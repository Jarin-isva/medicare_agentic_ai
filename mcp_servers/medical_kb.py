# Medical Knowledge Base MCP Server - WITH SECURITY
# mcp_servers/medical_kb.py

import os
import json
import logging
import sqlite3
import time
from typing import Dict, Any, List
from contextlib import contextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# FastAPI App Setup
# ============================================

app = FastAPI(
    title="Medical Knowledge Base MCP Server",
    description="Provides medical knowledge for MediGuide agents",
    version="1.0.0"
)

# ============================================
# SECURITY: CORS Middleware
# ============================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://localhost:3000",
        "http://127.0.0.1:8501",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=3600,  # Cache preflight for 1 hour
)

# ============================================
# SECURITY: Trusted Host Middleware
# ============================================

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "localhost",
        "127.0.0.1",
        "localhost:8501",
        "127.0.0.1:8501",
    ]
)

# ============================================
# SECURITY: Request/Response Middleware
# ============================================

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    Add security headers and log requests
    """
    start_time = time.time()
    
    # Log incoming request
    logger.info(f"🔵 {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        # Log response
        process_time = time.time() - start_time
        logger.info(f"✅ Response: {response.status_code} ({process_time:.3f}s)")
        
        return response
    
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(e)}
        )

# ============================================
# Database Connection
# ============================================

DB_PATH = os.getenv("DATABASE_PATH", "data/mediguide.db")

@contextmanager
def get_db_connection():
    """Get database connection with error handling"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        yield conn
        conn.close()
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise

# ============================================
# Input Validation
# ============================================

def validate_symptoms(symptoms: List[str]) -> bool:
    """Validate symptom input"""
    if not symptoms:
        raise ValueError("Symptoms list cannot be empty")
    
    if not isinstance(symptoms, list):
        raise ValueError("Symptoms must be a list")
    
    if len(symptoms) > 10:
        raise ValueError("Maximum 10 symptoms allowed")
    
    for symptom in symptoms:
        if not isinstance(symptom, str):
            raise ValueError("Each symptom must be a string")
        if len(symptom) > 100:
            raise ValueError("Symptom text too long")
    
    return True

def validate_age(age: int) -> bool:
    """Validate age input"""
    if not isinstance(age, int):
        raise ValueError("Age must be an integer")
    
    if age < 1 or age > 120:
        raise ValueError("Age must be between 1 and 120")
    
    return True

def validate_gender(gender: str) -> bool:
    """Validate gender input"""
    if gender not in ["M", "F", "Other"]:
        raise ValueError("Gender must be M, F, or Other")
    
    return True

# ============================================
# Health Check
# ============================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM diseases")
            disease_count = cursor.fetchone()[0]
        
        logger.info("✅ Health check passed")
        
        return {
            "status": "healthy",
            "service": "Medical Knowledge Base MCP",
            "port": 8001,
            "database": "connected",
            "diseases_in_db": disease_count
        }
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# ============================================
# Tool: Find Diseases
# ============================================

@app.post("/tools/find_diseases")
async def find_diseases(payload: Dict[str, Any]):
    """
    Find diseases matching symptoms
    
    Input:
    {
        "symptoms": ["fever", "headache"],
        "age": 35,
        "gender": "M",
        "region": "Bangladesh"
    }
    
    Output:
    {
        "results": {
            "diseases": [
                {
                    "id": 1,
                    "disease_name": "Dengue Fever",
                    "probability": 0.95,
                    "severity": "moderate"
                }
            ]
        }
    }
    """
    try:
        # Validate inputs
        symptoms = payload.get("symptoms", [])
        age = payload.get("age", 30)
        gender = payload.get("gender", "M")
        
        logger.info(f"find_diseases called: symptoms={symptoms}, age={age}")
        
        # Validate
        validate_symptoms(symptoms)
        validate_age(age)
        validate_gender(gender)
        
        # Query database
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Build query
            symptoms_placeholders = ",".join(["?"] * len(symptoms))
            
            query = f"""
            SELECT DISTINCT
                d.id,
                d.disease_name,
                d.severity_level,
                d.is_emergency,
                COUNT(ds.symptom_id) as matching_symptoms,
                CAST(COUNT(ds.symptom_id) AS FLOAT) / 
                    (SELECT COUNT(*) FROM disease_symptoms WHERE disease_id = d.id) as probability
            FROM diseases d
            LEFT JOIN disease_symptoms ds ON d.id = ds.disease_id
            LEFT JOIN symptoms s ON ds.symptom_id = s.id
            WHERE LOWER(s.symptom_name) IN ({symptoms_placeholders})
            GROUP BY d.id
            ORDER BY probability DESC
            LIMIT 10
            """
            
            lower_symptoms = [s.lower() for s in symptoms]
            cursor.execute(query, lower_symptoms)
            results = cursor.fetchall()
        
        # Format results
        diseases = [
            {
                "id": row["id"],
                "disease_name": row["disease_name"],
                "severity": row["severity_level"],
                "is_emergency": bool(row["is_emergency"]),
                "probability": min(row["probability"], 1.0),
            }
            for row in results
        ]
        
        logger.info(f"✅ Found {len(diseases)} diseases")
        
        return {
            "status": "success",
            "results": {
                "diseases": diseases,
                "symptom_count": len(symptoms),
                "matches_found": len(diseases)
            }
        }
    
    except ValueError as e:
        logger.warning(f"⚠️ Validation error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "code": 400
        }
    except Exception as e:
        logger.error(f"❌ Error in find_diseases: {e}")
        return {
            "status": "error",
            "error": str(e),
            "code": 500
        }

# ============================================
# Tool: Get Disease Details
# ============================================

@app.post("/tools/get_disease_details")
async def get_disease_details(payload: Dict[str, Any]):
    """Get detailed information about a disease"""
    try:
        disease_id = payload.get("disease_id")
        
        if not disease_id:
            return {"status": "error", "error": "disease_id required"}
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM diseases WHERE id = ?
            """, (disease_id,))
            
            result = cursor.fetchone()
        
        if not result:
            return {"status": "error", "error": "Disease not found"}
        
        logger.info(f"✅ Retrieved details for disease {disease_id}")
        
        return {
            "status": "success",
            "disease": {
                "id": result["id"],
                "disease_name": result["disease_name"],
                "icd11_code": result["icd11_code"],
                "severity_level": result["severity_level"],
                "is_emergency": bool(result["is_emergency"]),
                "treatment_class": result["treatment_class"]
            }
        }
    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {"status": "error", "error": str(e)}

# ============================================
# Tool: Check Drug Interaction
# ============================================

@app.post("/tools/check_drug_interaction")
async def check_drug_interaction(payload: Dict[str, Any]):
    """Check for drug interactions"""
    try:
        medications = payload.get("medications", [])
        
        logger.info(f"Checking interactions for: {medications}")
        
        # Placeholder implementation
        return {
            "status": "success",
            "interactions": [],
            "safe": True
        }
    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {"status": "error", "error": str(e)}

# ============================================
# Tool: Get Treatment Guidelines
# ============================================

@app.post("/tools/get_treatment_guidelines")
async def get_treatment_guidelines(payload: Dict[str, Any]):
    """Get WHO treatment guidelines for a disease"""
    try:
        disease_name = payload.get("disease_name")
        
        logger.info(f"Getting guidelines for: {disease_name}")
        
        # Placeholder implementation
        return {
            "status": "success",
            "guidelines": [
                "Supportive care",
                "Hydration",
                "Pain management",
                "Monitor vital signs"
            ]
        }
    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {"status": "error", "error": str(e)}

# ============================================
# Tool: Search Symptoms by Category
# ============================================

@app.post("/tools/search_symptoms_by_category")
async def search_symptoms_by_category(payload: Dict[str, Any]):
    """Search symptoms by category"""
    try:
        category = payload.get("category")
        
        if not category:
            return {"status": "error", "error": "category required"}
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM symptoms WHERE category = ?
            """, (category,))
            
            results = cursor.fetchall()
        
        symptoms = [
            {
                "id": row["id"],
                "symptom_name": row["symptom_name"],
                "medical_term": row["medical_term"],
                "category": row["category"]
            }
            for row in results
        ]
        
        logger.info(f"✅ Found {len(symptoms)} symptoms in category {category}")
        
        return {
            "status": "success",
            "symptoms": symptoms,
            "count": len(symptoms)
        }
    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {"status": "error", "error": str(e)}

# ============================================
# Error Handlers
# ============================================

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

# ============================================
# Startup Event
# ============================================

@app.on_event("startup")
async def startup_event():
    """Run on server startup"""
    logger.info("=" * 60)
    logger.info("🏥 Medical Knowledge Base MCP Server Starting")
    logger.info("=" * 60)
    logger.info(f"📊 Database: {DB_PATH}")
    logger.info(f"🔌 Port: 8001")
    logger.info(f"🔐 Security: CORS + Headers + Input Validation")
    logger.info("=" * 60)

@app.on_event("shutdown")
async def shutdown_event():
    """Run on server shutdown"""
    logger.info("🛑 Medical Knowledge Base MCP Server Shutting Down")

# ============================================
# Run Server
# ============================================

if __name__ == "__main__":
    port = int(os.getenv("MCP_MEDICAL_KB_PORT", 8001))
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )