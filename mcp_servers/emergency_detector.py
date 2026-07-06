# MCP Server 2: Emergency Detector
# mcp_servers/emergency_detector.py

import asyncio
import json
import logging
import os
import sqlite3
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

from pydantic import BaseModel

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
DB_PATH = str(ROOT_DIR / "data" / "mediguide.db")

# ============================================
# RED FLAG DEFINITIONS (Conservative bias)
# ============================================

RED_FLAG_RULES = {
    "chest_pain": {
        "severity": 9,
        "requires_escalation": True,
        "keywords": ["chest pain", "chest discomfort", "cardiac", "heart pain"]
    },
    "difficulty_breathing": {
        "severity": 9,
        "requires_escalation": True,
        "keywords": ["difficulty breathing", "shortness of breath", "dyspnea", "cant breathe"]
    },
    "altered_consciousness": {
        "severity": 10,
        "requires_escalation": True,
        "keywords": ["unconscious", "unresponsive", "coma", "confusion", "disoriented"]
    },
    "severe_bleeding": {
        "severity": 9,
        "requires_escalation": True,
        "keywords": ["severe bleeding", "hemorrhage", "bleeding", "uncontrollable"]
    },
    "severe_allergic_reaction": {
        "severity": 9,
        "requires_escalation": True,
        "keywords": ["anaphylaxis", "allergy", "throat tightness", "swelling"]
    },
    "stroke_symptoms": {
        "severity": 9,
        "requires_escalation": True,
        "keywords": ["facial drooping", "arm weakness", "speech difficulty", "slurred speech"]
    },
    "severe_abdominal_pain": {
        "severity": 8,
        "requires_escalation": True,
        "keywords": ["severe abdominal pain", "acute abdomen", "severe stomach pain"]
    },
    "poisoning": {
        "severity": 10,
        "requires_escalation": True,
        "keywords": ["poisoning", "overdose", "toxic", "poison"]
    }
}

# ============================================
# PYDANTIC MODELS
# ============================================

class PatientData(BaseModel):
    symptoms: List[str]
    age: Optional[int] = None
    vital_signs: Dict[str, float] = {}
    medical_history: List[str] = []

class RedFlagResponse(BaseModel):
    has_emergency: bool
    red_flags: List[str]
    severity_score: int
    confidence: float
    immediate_action: str
    escalation_required: bool

class EmergencyAssessmentResponse(BaseModel):
    urgency_level: str  # EMERGENCY / URGENT / ROUTINE
    risk_score: float
    confidence: float
    contributing_factors: Dict[str, float]
    recommendation: str

# ============================================
# UTILITY FUNCTIONS
# ============================================

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ============================================
# MCP TOOL 1: Check Red Flags
# ============================================

async def check_red_flags(patient_data: PatientData) -> Dict[str, Any]:
    """
    Check for life-threatening red flags
    Conservative approach: when in doubt, escalate.
    IMPORTANT: vital sign checks only fire when that vital was actually
    provided. Missing data must never be treated as an abnormal reading.
    """

    logger.info(f"Checking red flags for symptoms: {patient_data.symptoms}")

    detected_flags = []
    highest_severity = 0

    symptoms_text = " ".join(patient_data.symptoms).lower()

    # Rule-based red flag detection (keyword match on symptom text)
    for flag_name, config in RED_FLAG_RULES.items():
        for keyword in config["keywords"]:
            if keyword.lower() in symptoms_text:
                detected_flags.append(flag_name)
                highest_severity = max(highest_severity, config["severity"])
                break

    # Check vital signs ONLY if they were actually supplied.
    # An empty/missing vital_signs dict must never be interpreted as an
    # abnormal reading — that previously caused every patient with no
    # recorded vitals to be flagged as hypotensive.
    vitals = patient_data.vital_signs or {}

    if "systolic" in vitals or "diastolic" in vitals:
        systolic = vitals.get("systolic")
        diastolic = vitals.get("diastolic")
        systolic_low = systolic is not None and systolic < 90
        diastolic_low = diastolic is not None and diastolic < 60
        if systolic_low or diastolic_low:
            detected_flags.append("hypotension")
            highest_severity = max(highest_severity, 8)

    if "heart_rate" in vitals and vitals["heart_rate"] is not None:
        if vitals["heart_rate"] > 120:
            detected_flags.append("tachycardia")
            highest_severity = max(highest_severity, 7)

    if "respiratory_rate" in vitals and vitals["respiratory_rate"] is not None:
        if vitals["respiratory_rate"] > 30:
            detected_flags.append("tachypnea")
            highest_severity = max(highest_severity, 8)

    if "oxygen_saturation" in vitals and vitals["oxygen_saturation"] is not None:
        if vitals["oxygen_saturation"] < 90:
            detected_flags.append("hypoxemia")
            highest_severity = max(highest_severity, 9)

    logger.info(f"Detected {len(detected_flags)} red flags")

    response = {
        "status": "success",
        "has_emergency": len(detected_flags) > 0,
        "red_flags": list(set(detected_flags)),  # Remove duplicates
        "severity_score": highest_severity,
        "confidence": 0.95 if detected_flags else 1.0,
        "immediate_action": "Call emergency services immediately" if detected_flags else "Safe for non-emergency evaluation",
        "escalation_required": highest_severity >= 8,
        "timestamp": "2026-07-04T10:00:00Z"
    }

    return response

# ============================================
# MCP TOOL 2: Assess Emergency Level
# ============================================

async def assess_emergency_level(patient_data: PatientData) -> Dict[str, Any]:
    """
    Comprehensive emergency risk assessment
    """

    logger.info("Assessing emergency level...")

    symptoms = patient_data.symptoms
    age = patient_data.age or 50
    vital_signs = patient_data.vital_signs or {}
    history = patient_data.medical_history or []

    # Step 1: Check absolute red flags
    red_flag_check = await check_red_flags(patient_data)

    if red_flag_check["has_emergency"]:
        return {
            "status": "success",
            "urgency_level": "EMERGENCY",
            "risk_score": 0.95,
            "confidence": 0.99,
            "contributing_factors": {
                "red_flags": 0.95,
                "age_risk": 0.0,
                "comorbidity_risk": 0.0,
                "vital_risk": 0.0
            },
            "recommendation": "IMMEDIATE hospital transfer required - Life-threatening condition detected",
            "action_code": "CALL_911"
        }

    # Step 2: Age-based risk (elderly higher risk)
    age_risk = 0.1 if age < 65 else 0.3

    # Step 3: Comorbidity risk
    high_risk_conditions = [
        "diabetes", "hypertension", "heart disease", "cardiac",
        "cancer", "stroke", "kidney", "lung disease"
    ]
    history_text = " ".join(history).lower()
    comorbidity_risk = 0.2 if any(c in history_text for c in high_risk_conditions) else 0.1

    # Step 4: Vital sign risk (only counts vitals that were actually provided)
    vital_risk = 0.0
    if "heart_rate" in vital_signs and vital_signs["heart_rate"] is not None:
        if vital_signs["heart_rate"] > 100:
            vital_risk += 0.1
    if "respiratory_rate" in vital_signs and vital_signs["respiratory_rate"] is not None:
        if vital_signs["respiratory_rate"] > 20:
            vital_risk += 0.1
    if "oxygen_saturation" in vital_signs and vital_signs["oxygen_saturation"] is not None:
        if vital_signs["oxygen_saturation"] < 95:
            vital_risk += 0.15
    if "systolic" in vital_signs and vital_signs["systolic"] is not None:
        if vital_signs["systolic"] > 180:
            vital_risk += 0.1

    # Step 5: Symptom severity risk
    severity_keywords = ["severe", "acute", "sudden", "critical", "worst"]
    symptoms_text = " ".join(symptoms).lower()
    symptom_risk = 0.15 if any(k in symptoms_text for k in severity_keywords) else 0.05

    # Calculate total risk
    total_risk = age_risk + comorbidity_risk + vital_risk + symptom_risk

    # Determine urgency level
    if total_risk > 0.6:
        urgency = "EMERGENCY"
    elif total_risk > 0.35:
        urgency = "URGENT"
    else:
        urgency = "ROUTINE"

    logger.info(f"Emergency level: {urgency}, Risk score: {total_risk:.2f}")

    response = {
        "status": "success",
        "urgency_level": urgency,
        "risk_score": min(total_risk, 1.0),
        "confidence": 0.85,
        "contributing_factors": {
            "age_risk": round(age_risk, 2),
            "comorbidity_risk": round(comorbidity_risk, 2),
            "vital_sign_risk": round(vital_risk, 2),
            "symptom_severity_risk": round(symptom_risk, 2)
        },
        "recommendation": {
            "EMERGENCY": "Immediate hospitalization required",
            "URGENT": "Same-day medical evaluation needed",
            "ROUTINE": "Can be managed in clinic setting"
        }[urgency],
        "action_code": {
            "EMERGENCY": "CALL_911",
            "URGENT": "URGENT_CLINIC",
            "ROUTINE": "ROUTINE_CLINIC"
        }[urgency]
    }

    return response

# ============================================
# MCP TOOL 3: Evaluate Contraindications
# ============================================

async def evaluate_contraindications(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check medication contraindications
    """

    medication = request.get("medication", "")
    patient_data = PatientData(**request.get("patient_data", {}))

    logger.info(f"Evaluating contraindications for {medication}")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get medication info
        med = cursor.execute(
            "SELECT contraindications FROM medications WHERE medication_name = ?",
            (medication,)
        ).fetchone()

        if not med:
            conn.close()
            return {
                "status": "not_found",
                "medication": medication,
                "contraindicated": False,
                "message": "Medication not found in database"
            }

        contraindications = med[0] or ""

        # Check patient factors
        contraindicated = False
        reasons = []

        # Age-based contraindications
        if patient_data.age and patient_data.age < 18:
            if "pediatric" in contraindications.lower() or "children" in contraindications.lower():
                contraindicated = True
                reasons.append("Not recommended for pediatric patients")

        if patient_data.age and patient_data.age > 65:
            if "elderly" in contraindications.lower() or "geriatric" in contraindications.lower():
                contraindicated = True
                reasons.append("Caution in elderly patients")

        # Check medical history contraindications
        history_text = " ".join(patient_data.medical_history).lower()
        contra_text = contraindications.lower()

        if "kidney" in history_text and ("renal" in contra_text or "kidney" in contra_text):
            contraindicated = True
            reasons.append("Contraindicated in renal disease")

        if "liver" in history_text and ("hepatic" in contra_text or "liver" in contra_text):
            contraindicated = True
            reasons.append("Contraindicated in liver disease")

        conn.close()

        logger.info(f"Contraindication check complete for {medication}")

        return {
            "status": "success",
            "medication": medication,
            "contraindicated": contraindicated,
            "reasons": reasons,
            "contraindications_info": contraindications,
            "safe_to_use": not contraindicated
        }

    except Exception as e:
        logger.error(f"Error evaluating contraindications: {e}")
        return {
            "status": "error",
            "error": str(e),
            "safe_to_use": False  # Conservative: assume unsafe on error
        }

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
            "service": "Emergency Detection MCP Server"
        }
    except:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "service": "Emergency Detection MCP Server"
        }

async def root():
    """Server information"""
    return {
        "name": "Emergency Detection MCP Server",
        "version": "1.0.0",
        "status": "running",
        "port": 8002,
        "endpoints": [
            "/health",
            "/tools/check_red_flags",
            "/tools/assess_emergency_level",
            "/tools/evaluate_contraindications"
        ]
    }

if __name__ == "__main__":
    class EmergencyHandler(BaseHTTPRequestHandler):
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

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path == "/health":
                self._send_json(200, asyncio.run(health_check()))
                return
            if parsed.path == "/":
                self._send_json(200, asyncio.run(root()))
                return
            self._send_json(404, {"error": "Not found"})

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            payload = self._read_json()
            if parsed.path == "/tools/check_red_flags":
                patient_data = PatientData(**payload)
                self._send_json(200, asyncio.run(check_red_flags(patient_data)))
                return
            if parsed.path == "/tools/assess_emergency_level":
                patient_data = PatientData(**payload)
                self._send_json(200, asyncio.run(assess_emergency_level(patient_data)))
                return
            if parsed.path == "/tools/evaluate_contraindications":
                self._send_json(200, asyncio.run(evaluate_contraindications(payload)))
                return
            self._send_json(404, {"error": "Not found"})

    print("\n" + "=" * 60)
    print("[EMERGENCY] Emergency Detection MCP Server")
    print("=" * 60)
    print("Starting server on http://0.0.0.0:8002")
    print("=" * 60 + "\n")

    server = ThreadingHTTPServer(("0.0.0.0", 8002), EmergencyHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()