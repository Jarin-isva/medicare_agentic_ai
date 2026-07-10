# mcp_servers/care_network.py

import sys
import os
import logging
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# ✅ FIX: Add path configuration
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Care Network MCP Server",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)

# Security
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Care Network"}

# Find hospital
@app.post("/tools/find_nearest_hospital")
async def find_nearest_hospital(payload: dict):
    """Find nearest hospital"""
    try:
        location = payload.get("location", "Chittagong")
        specialty = payload.get("specialty", "General")
        
        # Mock hospital data
        hospitals = [
            {
                "id": 1,
                "name": "Chittagong Medical College Hospital",
                "address": "123 Hospital Road, Chittagong",
                "phone": "+88031-2504844",
                "specialty": specialty,
                "available_beds": 5,
                "distance": 5
            }
        ]
        
        return {
            "status": "success",
            "hospitals": hospitals
        }
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "error": str(e)}

# Check availability
@app.post("/tools/check_availability")
async def check_availability(payload: dict):
    """Check hospital availability"""
    try:
        return {
            "status": "success",
            "available": True,
            "beds_available": 5
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

# Generate referral
@app.post("/tools/generate_referral_letter")
async def generate_referral_letter(payload: dict):
    """Generate referral letter"""
    try:
        return {
            "status": "success",
            "referral_letter": "Official referral letter generated",
            "tracking_id": f"REF-{payload.get('hospital_id', 1)}"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

# Schedule follow-up
@app.post("/tools/schedule_follow_up")
async def schedule_follow_up(payload: dict):
    """Schedule follow-up"""
    try:
        return {
            "status": "success",
            "appointment_confirmed": True,
            "date": "2026-07-13"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("🏥 Care Network MCP Server Starting")
    logger.info("Port: 8003")
    logger.info("=" * 60)

if __name__ == "__main__":
    port = int(os.getenv("MCP_CARE_NETWORK_PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")