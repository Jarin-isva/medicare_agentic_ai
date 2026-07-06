# MCP Servers Quick Reference Guide

## What Are MCP Servers?

MCP (Model Context Protocol) Servers are specialized services that agents can call to get specific information. Think of them as APIs that agents use to make better decisions.

## Running MCP Servers

### Quick Start

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\python.exe mcp_servers\medical_kb.py
```

### Manual Startup

**Medical Knowledge Base (Port 8002)**
```powershell
.\.venv\Scripts\python.exe mcp_servers\medical_kb.py
```

Health Check:
```powershell
curl.exe http://localhost:8002/health
```

---

## MCP Server 1: Medical Knowledge Base (PORT 8002)

**Status:** ✅ IMPLEMENTED & RUNNING
**Python Environment:** .venv
**Installed MCP Version:** 2.0.0b1

### Available Tools

#### 1. **find_diseases**
Find potential diseases based on symptoms.

**Request:**
```bash
curl.exe -X POST http://localhost:8002/tools/find_diseases `
  -H "Content-Type: application/json" \
  -d '{
    "symptoms": ["fever", "headache"],
    "age": 30,
    "gender": "M",
    "region": "Bangladesh"
  }'
```

**Response:**
```json
{
  "status": "success",
  "results": {
    "total_matches": 5,
    "diseases": [
      {
        "disease_name": "Malaria",
        "severity": "severe",
        "confidence": 0.98,
        "probability": 0.95
      }
    ]
  }
}
```

---

#### 2. **get_disease_details**
Get comprehensive details about a specific disease.

**Request:**
```bash
curl.exe -X POST http://localhost:8002/tools/get_disease_details `
  -H "Content-Type: application/json" \
  -d '{"disease_name": "Dengue Fever"}'
```

---

#### 3. **check_drug_interaction**
Check for drug-drug interactions.

**Request:**
```bash
curl.exe -X POST http://localhost:8002/tools/check_drug_interaction `
  -H "Content-Type: application/json" \
  -d '{"medications": ["Aspirin", "Ibuprofen"]}'
```

---

#### 4. **get_treatment_guidelines**
Get WHO/clinical treatment guidelines.

**Request:**
```bash
curl.exe -X POST http://localhost:8002/tools/get_treatment_guidelines `
  -H "Content-Type: application/json" \
  -d '{"disease_name": "Malaria"}'
```

---

#### 5. **search_symptoms_by_category**
Search symptoms by medical category.

**Request:**
```bash
curl.exe -X POST http://localhost:8002/tools/search_symptoms_by_category `
  -H "Content-Type: application/json" \
  -d '{"category": "respiratory"}'
```

---

## Testing

### Run Full Test Suite

```bash
.\.venv\Scripts\python.exe tests\test_mcp_medical_kb.py
```

### Test Individual Tools

```bash
# Health check
curl.exe http://localhost:8002/health

# List all endpoints
curl.exe http://localhost:8002/
```

---

## MCP Server 2 & 3 (Coming Soon)

### Server 2: Emergency Detection (Port 8002)
- Red flag detection
- Emergency risk assessment
- Critical condition identification

### Server 3: Care Network (Port 8003)
- Hospital location matching
- Facility availability checking
- Referral letter generation

---

## Architecture