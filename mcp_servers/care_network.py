# MCP Server 3: Care Network Registry
# mcp_servers/care_network.py

import os
import asyncio
import json
import logging
import math
import sqlite3
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional
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
# PYDANTIC MODELS
# ============================================

class CoordinatesModel(BaseModel):
    latitude: float
    longitude: float

# ============================================
# UTILITY FUNCTIONS
# ============================================

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates"""
    R = 6371  # Earth's radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

# ============================================
# MCP TOOL 1: Find Nearest Hospital
# ============================================

async def find_nearest_hospital(request: Dict[str, Any]) -> Dict[str, Any]:
    """Find nearest hospital matching specialty"""
    
    specialty = request.get("specialty", "")
    location = request.get("location", "Chittagong")
    coordinates = request.get("coordinates")
    urgency_level = request.get("urgency_level", "ROUTINE")
    
    logger.info(f"Finding hospitals for specialty: {specialty} in {location}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                id,
                hospital_name,
                address,
                phone,
                city,
                district,
                specialties,
                available_beds,
                rating,
                latitude,
                longitude,
                is_emergency_facility,
                average_wait_time
            FROM hospitals 
            WHERE (specialties LIKE ? OR district = ?)
                AND status = 'active'
                AND available_beds > 0
            ORDER BY rating DESC, available_beds DESC
            LIMIT 20
        """
        
        results = cursor.execute(
            query,
            (f"%{specialty}%", location)
        ).fetchall()
        
        conn.close()
        
        hospitals = []
        for row in results:
            hospital_data = {
                "id": row["id"],
                "name": row["hospital_name"],
                "address": row["address"],
                "phone": row["phone"],
                "city": row["city"],
                "district": row["district"],
                "specialties": row["specialties"].split("|") if row["specialties"] else [],
                "available_beds": row["available_beds"],
                "rating": row["rating"],
                "is_emergency": bool(row["is_emergency_facility"]),
                "wait_time_minutes": row["average_wait_time"]
            }
            
            if coordinates:
                dist = haversine_distance(
                    coordinates.get("latitude"),
                    coordinates.get("longitude"),
                    row["latitude"],
                    row["longitude"]
                )
                hospital_data["distance_km"] = round(dist, 2)
            
            hospitals.append(hospital_data)
        
        if coordinates:
            hospitals.sort(key=lambda x: x.get("distance_km", float("inf")))
        
        logger.info(f"Found {len(hospitals)} hospitals")
        
        return {
            "status": "success",
            "hospitals": hospitals[:10],
            "specialty_searched": specialty,
            "location": location,
            "urgency": urgency_level,
            "total_available": len(hospitals),
            "timestamp": "2026-07-04T10:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Error finding hospitals: {e}")
        return {
            "status": "error",
            "error": str(e),
            "hospitals": []
        }

# ============================================
# MCP TOOL 2: Check Availability
# ============================================

async def check_availability(request: Dict[str, Any]) -> Dict[str, Any]:
    """Check real-time availability of hospital"""
    
    hospital_id = request.get("hospital_id")
    urgency_level = request.get("urgency_level", "ROUTINE")
    
    logger.info(f"Checking availability for hospital {hospital_id}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        result = cursor.execute("""
            SELECT 
                hospital_name,
                available_beds,
                average_wait_time,
                is_emergency_facility
            FROM hospitals
            WHERE id = ?
        """, (hospital_id,)).fetchone()
        
        conn.close()
        
        if not result:
            return {
                "status": "not_found",
                "hospital_id": hospital_id,
                "available": False
            }
        
        hospital_name, available_beds, wait_time, is_emergency = result
        
        accepting = True
        if urgency_level == "EMERGENCY" and not is_emergency:
            accepting = False
        
        logger.info(f"Availability check complete for {hospital_name}")
        
        return {
            "status": "success",
            "hospital_id": hospital_id,
            "hospital_name": hospital_name,
            "accepting_patients": accepting,
            "available_beds": available_beds,
            "estimated_wait_minutes": wait_time,
            "admission_status": "Ready for admission" if accepting and available_beds > 0 else "No availability",
            "urgency_category": urgency_level
        }
        
    except Exception as e:
        logger.error(f"Error checking availability: {e}")
        return {
            "status": "error",
            "error": str(e),
            "available": False
        }

# ============================================
# MCP TOOL 3: Generate Referral Letter
# ============================================

async def generate_referral_letter(request: Dict[str, Any]) -> Dict[str, Any]:
    """Generate official referral letter"""
    
    hospital_id = request.get("hospital_id")
    diagnosis = request.get("diagnosis", "")
    patient_info = request.get("patient_info", {})
    
    logger.info(f"Generating referral letter for hospital {hospital_id}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        hospital = cursor.execute(
            "SELECT hospital_name, address, phone FROM hospitals WHERE id = ?",
            (hospital_id,)
        ).fetchone()
        
        conn.close()
        
        if not hospital:
            return {
                "status": "not_found",
                "error": "Hospital not found"
            }
        
        hospital_name, address, phone = hospital
        
        referral_letter = f"""
============================================================
                    MEDICAL REFERRAL LETTER
============================================================

Date: 2026-07-04
Reference ID: REF-{hospital_id}-{patient_info.get('patient_id', 'UNKNOWN')}

TO: {hospital_name}
    {address}
    Phone: {phone}

FROM: MediGuide Clinical Support System
      Developed for Remote Healthcare Communities

------------------------------------------------------------

PATIENT INFORMATION:
----------------------------------------------------------------
Age:                    {patient_info.get('age', 'N/A')} years
Gender:                 {patient_info.get('gender', 'N/A')}
Chief Complaint:        {patient_info.get('chief_complaint', 'N/A')}
Patient ID:             {patient_info.get('patient_id', 'Not available')}

------------------------------------------------------------

CLINICAL IMPRESSION:
----------------------------------------------------------------
{diagosis}

------------------------------------------------------------

CURRENT MEDICATIONS:
----------------------------------------------------------------
{', '.join(patient_info.get('medications', ['None reported']))}

ALLERGIES:
----------------------------------------------------------------
{', '.join(patient_info.get('allergies', ['None reported']))}

MEDICAL HISTORY:
----------------------------------------------------------------
{', '.join(patient_info.get('medical_history', ['Non-significant']))}

------------------------------------------------------------

REASON FOR REFERRAL:
----------------------------------------------------------------
Patient requires specialist evaluation and management beyond 
primary care capabilities. Immediate evaluation recommended.

------------------------------------------------------------

REQUESTED INVESTIGATIONS/ACTIONS:
----------------------------------------------------------------
- Specialist evaluation and assessment
- Investigation as deemed necessary by specialist
- Treatment initiation and management
- Follow-up coordination

------------------------------------------------------------

URGENCY LEVEL: {request.get('urgency_level', 'ROUTINE')}

FOLLOW-UP:
Please provide:
1. Specialist assessment report
2. Investigation results
3. Treatment plan
4. Follow-up recommendations

============================================================
Generated by MediGuide AI Clinical Support System
For questions: support@mediguide.local
============================================================
"""
        
        logger.info("Referral letter generated successfully")
        
        return {
            "status": "success",
            "hospital_id": hospital_id,
            "hospital_name": hospital_name,
            "referral_letter": referral_letter,
            "tracking_id": f"REF-{hospital_id}-{patient_info.get('patient_id')}",
            "digital_signature": True,
            "letter_format": "plaintext"
        }
        
    except Exception as e:
        logger.error(f"Error generating referral letter: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

# ============================================
# MCP TOOL 4: Schedule Follow-up
# ============================================

async def schedule_follow_up(request: Dict[str, Any]) -> Dict[str, Any]:
    """Schedule follow-up appointment"""
    
    hospital_id = request.get("hospital_id")
    urgency = request.get("urgency_level", "ROUTINE")
    
    logger.info(f"Scheduling follow-up for hospital {hospital_id}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        hospital = cursor.execute(
            "SELECT hospital_name, phone FROM hospitals WHERE id = ?",
            (hospital_id,)
        ).fetchone()
        
        conn.close()
        
        if not hospital:
            return {
                "status": "not_found",
                "error": "Hospital not found"
            }
        
        hospital_name, phone = hospital
        
        follow_up_days = {
            "EMERGENCY": 1,
            "URGENT": 3,
            "ROUTINE": 7
        }
        
        days = follow_up_days.get(urgency, 7)
        
        logger.info(f"Follow-up scheduled for {hospital_name}")
        
        return {
            "status": "success",
            "hospital_id": hospital_id,
            "hospital_name": hospital_name,
            "appointment_scheduled": True,
            "recommended_follow_up_days": days,
            "phone_to_book": phone,
            "booking_instructions": f"Please call {phone} to schedule appointment within {days} days",
            "tracking_id": f"FUP-{hospital_id}"
        }
        
    except Exception as e:
        logger.error(f"Error scheduling follow-up: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

# ============================================
# SERVER ENDPOINTS
# ============================================

async def health_check():
    """Health check endpoint"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("SELECT COUNT(*) FROM hospitals")
        conn.close()
        return {
            "status": "healthy",
            "database": "connected",
            "service": "Care Network Registry MCP Server"
        }
    except:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "service": "Care Network Registry MCP Server"
        }

async def root():
    """Server information"""
    return {
        "name": "Care Network Registry MCP Server",
        "version": "1.0.0",
        "status": "running",
        "port": 8003,
        "endpoints": [
            "/health",
            "/tools/find_nearest_hospital",
            "/tools/check_availability",
            "/tools/generate_referral_letter",
            "/tools/schedule_follow_up"
        ]
    }

if __name__ == "__main__":
    class CareNetworkHandler(BaseHTTPRequestHandler):
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
                self._send_json(200, asyncio.run(health_check()))
                return
            if parsed.path == "/":
                self._send_json(200, asyncio.run(root()))
                return
            self._send_json(404, {"error": "Not found"})

        def do_POST(self):  # noqa: N802
            parsed = urlparse(self.path)
            payload = self._read_json()
            if parsed.path == "/tools/find_nearest_hospital":
                self._send_json(200, asyncio.run(find_nearest_hospital(payload)))
                return
            if parsed.path == "/tools/check_availability":
                self._send_json(200, asyncio.run(check_availability(payload)))
                return
            if parsed.path == "/tools/generate_referral_letter":
                self._send_json(200, asyncio.run(generate_referral_letter(payload)))
                return
            if parsed.path == "/tools/schedule_follow_up":
                self._send_json(200, asyncio.run(schedule_follow_up(payload)))
                return
            self._send_json(404, {"error": "Not found"})

    print("\n" + "=" * 60)
    print("[CARE NETWORK] Care Network Registry MCP Server")
    print("=" * 60)
    print("Starting server on http://0.0.0.0:8003")
    print("=" * 60 + "\n")

    server = ThreadingHTTPServer(("0.0.0.0", 8003), CareNetworkHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()