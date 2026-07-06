# MCP Server 1: Medical Knowledge Base
# mcp_servers/medical_kb.py

import asyncio
import json
import os
import sqlite3
import logging
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

ROOT_DIR = Path(__file__).resolve().parent.parent
VENV_PYTHON = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
VENV_SITE_PACKAGES = ROOT_DIR / ".venv" / "Lib" / "site-packages"

if VENV_PYTHON.exists() and not os.environ.get("VIRTUAL_ENV"):
    try:
        current_exe = Path(sys.executable).resolve()
        venv_exe = VENV_PYTHON.resolve()
    except OSError:
        current_exe = None
        venv_exe = VENV_PYTHON

    if current_exe != venv_exe:
        os.execv(str(venv_exe), [str(venv_exe), str(Path(__file__).resolve()), *sys.argv[1:]])

if VENV_SITE_PACKAGES.exists():
    sys.path.insert(0, str(VENV_SITE_PACKAGES))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
BASE_DIR = ROOT_DIR
DB_PATH = str(BASE_DIR / "data" / "mediguide.db")

# ============================================
# UTILITY FUNCTIONS
# ============================================

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def serialize_rows(rows: List[sqlite3.Row]) -> List[Dict]:
    """Convert sqlite3.Row objects to dictionaries"""
    return [dict(row) for row in rows]

# ============================================
# MCP TOOL 1: Find Diseases by Symptoms
# ============================================

async def find_diseases(
    symptoms: List[str],
    age: Optional[int] = None,
    gender: Optional[str] = None,
    region: str = "Bangladesh"
):
    """Find potential diseases based on symptoms."""
    
    logger.info(f"Finding diseases for symptoms: {symptoms}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if not symptoms:
            return {"error": "No symptoms provided"}
        
        # Convert symptom names to lowercase for matching
        symptoms_lower = [s.lower() for s in symptoms]
        
        # SQL Query: Find diseases matching symptoms
        query = """
        SELECT DISTINCT
            d.id,
            d.disease_name,
            d.icd11_code,
            d.severity_level,
            d.is_emergency,
            d.description,
            d.typical_duration,
            COUNT(ds.symptom_id) as symptom_matches,
            AVG(ds.association_strength) as avg_strength,
            MAX(ds.association_strength) as max_strength
        FROM diseases d
        LEFT JOIN disease_symptoms ds ON d.id = ds.disease_id
        LEFT JOIN symptoms s ON ds.symptom_id = s.id
        WHERE LOWER(s.symptom_name) IN ({})
        GROUP BY d.id
        ORDER BY 
            symptom_matches DESC,
            avg_strength DESC,
            d.severity_level DESC
        LIMIT 10
        """.format(','.join(['?' for _ in symptoms_lower]))
        
        results = cursor.execute(query, symptoms_lower).fetchall()
        conn.close()
        
        # Format response
        diseases = []
        for row in results:
            disease = {
                "id": row["id"],
                "disease_name": row["disease_name"],
                "icd11_code": row["icd11_code"],
                "severity": row["severity_level"],
                "is_emergency": bool(row["is_emergency"]),
                "description": row["description"],
                "typical_duration": row["typical_duration"],
                "symptom_matches": row["symptom_matches"],
                "confidence": min(row["avg_strength"] or 0.5, 1.0),
                "probability": min((row["symptom_matches"] / len(symptoms)) * (row["avg_strength"] or 0.5), 1.0)
            }
            diseases.append(disease)
        
        response = {
            "status": "success",
            "query": {
                "symptoms": symptoms,
                "age": age,
                "gender": gender,
                "region": region
            },
            "results": {
                "total_matches": len(diseases),
                "diseases": diseases
            },
            "timestamp": "2026-07-04T10:00:00Z"
        }
        
        logger.info(f"Found {len(diseases)} diseases")
        
        return response
        
    except Exception as e:
        logger.error(f"Error finding diseases: {e}")
        return {"error": str(e)}

# ============================================
# MCP TOOL 2: Get Disease Details
# ============================================

async def get_disease_details(disease_name: str):
    """Get comprehensive details about a specific disease."""
    
    logger.info(f"Getting details for disease: {disease_name}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get disease info
        disease = cursor.execute("""
            SELECT * FROM diseases WHERE disease_name = ?
        """, (disease_name,)).fetchone()
        
        if not disease:
            conn.close()
            return {"error": f"Disease not found: {disease_name}"}
        
        # Get associated symptoms
        symptoms = cursor.execute("""
            SELECT 
                s.symptom_name,
                s.medical_term,
                ds.association_strength,
                ds.is_primary_symptom,
                ds.typical_onset_days,
                ds.prevalence_percentage
            FROM disease_symptoms ds
            JOIN symptoms s ON ds.symptom_id = s.id
            WHERE ds.disease_id = ?
            ORDER BY ds.association_strength DESC
        """, (disease["id"],)).fetchall()
        
        conn.close()
        
        response = {
            "status": "success",
            "disease": {
                "name": disease["disease_name"],
                "code": disease["icd11_code"],
                "severity": disease["severity_level"],
                "is_emergency": bool(disease["is_emergency"]),
                "description": disease["description"],
                "typical_duration": disease["typical_duration"],
                "treatment_class": disease["treatment_class"]
            },
            "symptoms": [
                {
                    "name": s["symptom_name"],
                    "medical_term": s["medical_term"],
                    "confidence": s["association_strength"],
                    "is_primary": bool(s["is_primary_symptom"]),
                    "onset_days": s["typical_onset_days"],
                    "prevalence": f"{s['prevalence_percentage']:.0f}%"
                }
                for s in symptoms
            ],
            "symptom_count": len(symptoms)
        }
        
        logger.info(f"Retrieved details for {disease_name}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting disease details: {e}")
        return {"error": str(e)}

# ============================================
# MCP TOOL 3: Check Drug Interactions
# ============================================

async def check_drug_interaction(medications: List[str]):
    """Check for drug-drug interactions."""
    
    logger.info(f"Checking interactions for medications: {medications}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if len(medications) < 2:
            return {
                "status": "success",
                "medications": medications,
                "interactions": [],
                "safe_to_combine": True
            }
        
        # Check all medication pairs
        interactions_found = []
        
        for i, med1 in enumerate(medications):
            for med2 in medications[i+1:]:
                # Get medication IDs
                med1_id = cursor.execute(
                    "SELECT id FROM medications WHERE medication_name = ?",
                    (med1,)
                ).fetchone()
                
                med2_id = cursor.execute(
                    "SELECT id FROM medications WHERE medication_name = ?",
                    (med2,)
                ).fetchone()
                
                if med1_id and med2_id:
                    # Check interaction
                    interaction = cursor.execute("""
                        SELECT severity, description FROM drug_interactions
                        WHERE (medication_1_id = ? AND medication_2_id = ?)
                           OR (medication_1_id = ? AND medication_2_id = ?)
                    """, (med1_id[0], med2_id[0], med2_id[0], med1_id[0])).fetchone()
                    
                    if interaction:
                        interactions_found.append({
                            "drug_1": med1,
                            "drug_2": med2,
                            "severity": interaction["severity"],
                            "description": interaction["description"]
                        })
        
        conn.close()
        
        response = {
            "status": "success",
            "medications": medications,
            "interactions": interactions_found,
            "safe_to_combine": len(interactions_found) == 0,
            "warning_count": len(interactions_found)
        }
        
        if interactions_found:
            logger.warning(f"Found {len(interactions_found)} interactions")
        else:
            logger.info("No interactions found")
        
        return response
        
    except Exception as e:
        logger.error(f"Error checking interactions: {e}")
        return {"error": str(e)}

# ============================================
# MCP TOOL 4: Get Treatment Guidelines
# ============================================

async def get_treatment_guidelines(disease_name: str):
    """Get WHO/clinical treatment guidelines for a disease."""
    
    logger.info(f"Getting guidelines for: {disease_name}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        disease = cursor.execute("""
            SELECT * FROM diseases WHERE disease_name = ?
        """, (disease_name,)).fetchone()
        
        conn.close()
        
        if not disease:
            return {"error": f"Disease not found: {disease_name}"}
        
        # Clinical guidelines (evidence-based)
        guidelines = {
            "Dengue Fever": {
                "first_line": "Supportive care, fluid replacement",
                "monitoring": "Daily platelet count, vital signs",
                "hospitalization": "If warning signs present",
                "critical_management": "Balanced fluid resuscitation, monitoring for severe dengue",
                "evidence_level": "WHO Guidelines 2009-2020",
                "contraindicated": "NSAIDs (use acetaminophen), aspirin"
            },
            "Malaria": {
                "first_line": "Artemisinin-based combination therapy (ACT)",
                "monitoring": "Parasitemia clearance, clinical response",
                "hospitalization": "Severe malaria cases",
                "critical_management": "IV artesunate, manage complications",
                "evidence_level": "WHO Guidelines 2021",
                "contraindicated": "Chloroquine-resistant strains in P. falciparum"
            },
            "Typhoid Fever": {
                "first_line": "Fluoroquinolone (Ciprofloxacin) or 3rd gen cephalosporin",
                "monitoring": "Clinical response, 48-72 hours",
                "hospitalization": "Complicated cases",
                "critical_management": "Surgical intervention if perforation",
                "evidence_level": "WHO Guidelines 2018",
                "contraindicated": "Chloramphenicol (resistance)"
            },
            "Cholera": {
                "first_line": "Aggressive IV fluid replacement + antibiotics",
                "monitoring": "Hourly fluid balance, electrolytes",
                "hospitalization": "All cases require hospitalization",
                "critical_management": "Intensive monitoring, replacement of ongoing losses",
                "evidence_level": "WHO Guidelines 2004-2017",
                "contraindicated": "Inadequate fluid therapy"
            },
            "Pneumonia": {
                "first_line": "Antibiotics based on severity/age",
                "monitoring": "Oxygen saturation, respiratory status",
                "hospitalization": "Severe/hypoxemic cases",
                "critical_management": "Supplemental oxygen, ICU if respiratory failure",
                "evidence_level": "IDSA Guidelines 2019",
                "contraindicated": "Monotherapy for severe cases"
            }
        }
        
        # Get specific guidelines or use default
        guide = guidelines.get(disease_name, {
            "first_line": "Symptomatic and supportive care",
            "monitoring": "Clinical assessment",
            "hospitalization": "Based on severity",
            "evidence_level": "Standard practice"
        })
        
        response = {
            "status": "success",
            "disease": disease_name,
            "guidelines": guide,
            "source": "WHO/Clinical Evidence",
            "note": "These are guidelines. Follow local protocols and consult specialist for individual patient management."
        }
        
        logger.info(f"Retrieved guidelines for {disease_name}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting guidelines: {e}")
        return {"error": str(e)}

# ============================================
# MCP TOOL 5: Search Symptoms by Category
# ============================================

async def search_symptoms_by_category(category: str):
    """Search for symptoms by category."""
    
    logger.info(f"Searching symptoms in category: {category}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        symptoms = cursor.execute("""
            SELECT symptom_name, medical_term, category 
            FROM symptoms 
            WHERE category = ?
            ORDER BY symptom_name
        """, (category.lower(),)).fetchall()
        
        conn.close()
        
        response = {
            "status": "success",
            "category": category,
            "symptoms": [
                {
                    "name": s["symptom_name"],
                    "medical_term": s["medical_term"]
                }
                for s in symptoms
            ],
            "count": len(symptoms)
        }
        
        logger.info(f"Found {len(symptoms)} symptoms in category {category}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error searching symptoms: {e}")
        return {"error": str(e)}

# ============================================
# SERVER ENDPOINTS
# ============================================

async def health_check():
    """Health check endpoint"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("SELECT 1")
        conn.close()
        return {
            "status": "healthy",
            "database": "connected",
            "service": "Medical Knowledge Base MCP Server"
        }
    except:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "service": "Medical Knowledge Base MCP Server"
        }

async def root():
    """Server information"""
    return {
        "name": "Medical Knowledge Base MCP Server",
        "version": "1.0.0",
        "status": "running",
        "port": 8001,
        "endpoints": [
            "/health",
            "/tools/find_diseases",
            "/tools/get_disease_details",
            "/tools/check_drug_interaction",
            "/tools/get_treatment_guidelines",
            "/tools/search_symptoms_by_category"
        ]
    }

# ============================================
# HTTP HANDLER
# ============================================

class MedicalKBHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Medical Knowledge Base MCP Server"""
    
    def _read_json(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        body = self.rfile.read(length).decode("utf-8")
        try:
            return json.loads(body) if body else {}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON body"}

    def _send_json(self, status: int, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            try:
                with sqlite3.connect(DB_PATH) as conn:
                    conn.execute("SELECT 1")
                self._send_json(200, {"status": "healthy", "database": "connected"})
            except Exception:
                self._send_json(200, {"status": "unhealthy", "database": "disconnected"})
            return

        if parsed.path == "/":
            self._send_json(200, {
                "name": "Medical Knowledge Base MCP Server",
                "version": "1.0.0",
                "status": "running",
                "endpoints": [
                    "/tools/find_diseases",
                    "/tools/get_disease_details",
                    "/tools/check_drug_interaction",
                    "/tools/get_treatment_guidelines",
                    "/tools/search_symptoms_by_category",
                    "/health",
                ],
            })
            return

        self._send_json(404, {"error": "Not found"})

    def do_POST(self):  # noqa: N802
        parsed = urlparse(self.path)
        payload = self._read_json()

        if parsed.path == "/tools/find_diseases":
            response = asyncio.run(
                find_diseases(
                    symptoms=payload.get("symptoms", []),
                    age=payload.get("age"),
                    gender=payload.get("gender"),
                    region=payload.get("region", "Bangladesh"),
                )
            )
            self._send_json(200, response)
            return

        if parsed.path == "/tools/get_disease_details":
            response = asyncio.run(get_disease_details(payload.get("disease_name", "")))
            self._send_json(200, response)
            return

        if parsed.path == "/tools/check_drug_interaction":
            response = asyncio.run(check_drug_interaction(payload.get("medications", [])))
            self._send_json(200, response)
            return

        if parsed.path == "/tools/get_treatment_guidelines":
            response = asyncio.run(get_treatment_guidelines(payload.get("disease_name", "")))
            self._send_json(200, response)
            return

        if parsed.path == "/tools/search_symptoms_by_category":
            response = asyncio.run(search_symptoms_by_category(payload.get("category", "")))
            self._send_json(200, response)
            return

        self._send_json(404, {"error": "Not found"})

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("[MEDICAL KB] Medical Knowledge Base MCP Server")
    print("=" * 60)
    print("Starting server on http://0.0.0.0:8001")
    print("=" * 60 + "\n")

    server = ThreadingHTTPServer(("0.0.0.0", 8001), MedicalKBHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()