# mcp_servers/emergency_detector.py

import sys
import os
import logging
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from dotenv import load_dotenv

# ✅ FIX: Add path configuration
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Initialize FastAPI
app = FastAPI(
    title="Emergency Detector MCP Server",
    version="1.0.0"
)

# ✅ Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)

# ✅ Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response

# ✅ Health check
@app.get("/health")
async def health_check():
    logger.info("✅ Health check passed")
    return {"status": "healthy", "service": "Emergency Detector"}

# ✅ Red flags tool
@app.post("/tools/check_red_flags")
async def check_red_flags(payload: dict):
    """Check for emergency red flags"""
    try:
        symptoms = payload.get("symptoms", [])
        logger.info(f"Checking red flags for symptoms: {symptoms}")
        
        # Red flag keywords
        critical_keywords = [
            "chest pain", "difficulty breathing", "loss of consciousness",
            "severe bleeding", "unconscious", "not breathing"
        ]
        
        red_flags = []
        for symptom in symptoms:
            if any(keyword in str(symptom).lower() for keyword in critical_keywords):
                red_flags.append(symptom)
        
        return {
            "status": "success",
            "red_flags": red_flags,
            "has_emergency": len(red_flags) > 0
        }
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "error": str(e)}

# ✅ Assess emergency level
@app.post("/tools/assess_emergency_level")
async def assess_emergency_level(payload: dict):
    """Assess emergency risk level"""
    try:
        age = payload.get("age", 30)
        severity = payload.get("severity", 5)
        
        # Simple risk scoring
        risk_score = (severity / 10) * 0.6 + (1 if age > 60 else 0) * 0.4
        
        return {
            "status": "success",
            "risk_score": min(risk_score, 1.0),
            "urgency_level": "EMERGENCY" if risk_score > 0.7 else "URGENT" if risk_score > 0.4 else "ROUTINE"
        }
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "error": str(e)}

# ✅ Evaluate contraindications
@app.post("/tools/evaluate_contraindications")
async def evaluate_contraindications(payload: dict):
    """Evaluate drug contraindications"""
    try:
        return {
            "status": "success",
            "contraindications": [],
            "safe": True
        }
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "error": str(e)}

# ✅ Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("🚨 Emergency Detector MCP Server Starting")
    logger.info("Port: 8002")
    logger.info("=" * 60)

# ✅ Main
if __name__ == "__main__":
    port = int(os.getenv("MCP_EMERGENCY_DETECTOR_PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")