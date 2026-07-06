# MediGuide: AI-Powered Healthcare Triage Assistant

**A multi-agent AI system for conversational patient intake, symptom analysis, emergency triage, and hospital referral — built for the Kaggle AI Agents Capstone (Agents for Good track).**

---

## Problem

Access to timely clinical triage is limited in many regions, including rural Bangladesh, where patients often cannot easily determine whether a health concern requires emergency care, urgent evaluation, or routine follow-up. Delays or misjudged urgency can lead to poor outcomes or unnecessary strain on hospital resources. MediGuide is a prototype system exploring whether a coordinated set of AI agents can help structure this decision process — gathering patient information conversationally, cross-referencing it against medical knowledge, flagging red-flag emergencies, and pointing toward appropriate care.

## Solution Overview

MediGuide breaks the triage process into four distinct responsibilities, each handled by a specialized agent, coordinated by a central orchestrator:

1. **Intake Agent** — conversationally collects patient demographics, chief complaint, symptom duration/severity, medications, allergies, and medical history, then extracts this into structured data.
2. **Symptom Analysis Agent** — queries a Medical Knowledge Base MCP server for candidate diseases matching the reported symptoms, then uses an LLM to rank a differential diagnosis with clinical reasoning.
3. **Emergency Triage Agent** — checks for critical red-flag symptoms via a dedicated Emergency Detector MCP server, and separately produces a risk-scored urgency classification (EMERGENCY / URGENT / ROUTINE).
4. **Care Coordinator Agent** — determines the relevant medical specialty, queries a Care Network MCP server for matching hospitals, and generates a referral letter and care plan.

The `AgentOrchestrator` manages the workflow state machine (`INTAKE → ANALYSIS → TRIAGE → COORDINATION → COMPLETE`) and hands data between agents.

A Streamlit frontend provides a simple conversational + form-based interface for the full patient journey.

## Architecture
┌─────────────────────────┐
                 │     Streamlit UI         │
                 └────────────┬────────────┘
                              │
                 ┌────────────▼────────────┐
                 │   Agent Orchestrator     │
                 │  (workflow state machine)│
                 └─┬───────┬───────┬───────┬┘
                   │       │       │       │
            ┌──────▼─┐ ┌───▼────┐ ┌▼──────┐ ┌▼───────────┐
            │ Intake │ │Symptom │ │Triage │ │Coordinator │
            │ Agent  │ │ Agent  │ │ Agent │ │   Agent    │
            └────────┘ └───┬────┘ └───┬───┘ └─────┬──────┘
                            │           │          │
                  ┌─────────▼──┐ ┌──────▼───┐ ┌───▼─────────┐
                  │ Medical KB │ │Emergency │ │Care Network │
                  │MCP Server  │ │Detector  │ │MCP Server   │
                  │(port 8001) │ │MCP Server│ │(port 8003)  │
                  │            │ │(port 8002)│ │             │
                  └────────────┘ └──────────┘ └─────────────┘
                  Each agent calls a Hugging Face-hosted LLM (via `huggingface_hub.InferenceClient`) for reasoning and language tasks, and calls its corresponding MCP server over HTTP for structured domain data (disease matching, red-flag rules, hospital records).

## Course Concepts Demonstrated

| Concept | Where | Notes |
|---|---|---|
| **Multi-agent system** | `agents/` directory, `agent_orchestrator.py` | Four specialized agents coordinated through an explicit workflow state machine, each with a single clear responsibility. |
| **MCP Servers** | `mcp_servers/` directory | Three independent FastAPI-based MCP servers (`medical_kb.py`, `emergency_detector.py`, `care_network.py`) exposing domain-specific tools that agents call over HTTP. |
| **Security features** | `agents/*.py`, `.env.example` | API tokens are never hardcoded; all agents load credentials via `python-dotenv` from a `.env` file (excluded from version control via `.gitignore`). Agents validate that a real token is present before initializing and fail closed with a clear error if missing. |

## Technology Stack

- **Language model access**: Hugging Face Inference API (`huggingface_hub.InferenceClient`)
- **Backend / MCP servers**: FastAPI + Uvicorn
- **Database**: SQLite
- **Frontend**: Streamlit
- **Async orchestration**: Python `asyncio`

## Project Structure
mediguide-agent/
├── agents/
│   ├── base_agent.py          # Shared base class (history, MCP calls, logging)
│   ├── intake_agent.py        # Patient intake conversation + data extraction
│   ├── symptom_agent.py       # Differential diagnosis
│   ├── triage_agent.py        # Emergency risk assessment
│   ├── coordinator_agent.py   # Referral & care plan generation
│   └── agent_orchestrator.py  # Workflow coordination across all agents
├── mcp_servers/
│   ├── medical_kb.py          # Disease/symptom knowledge base server
│   ├── emergency_detector.py  # Red-flag detection server
│   └── care_network.py        # Hospital registry & referral server
├── data/
│   └── mediguide.db           # SQLite database (diseases, symptoms, hospitals)
├── streamlit_app.py           # Frontend
├── start_servers.py           # Launches/stops all 3 MCP servers with PID tracking
├── requirements.txt
├── .env.example                # Template — copy to .env and fill in your own token
└── README.md
## Setup Instructions

### Prerequisites
- Python 3.10+
- A Hugging Face account and API token (free tier): https://huggingface.co/settings/tokens

### Installation

```bash
git clone <YOUR_GITHUB_REPO_URL_HERE>
cd mediguide-agent

python -m venv .venv
# Windows
.venv\Scripts\activate
# Mac/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### Configuration

```bash
cp .env.example .env
```

Edit `.env` and add your Hugging Face token:

```dotenv
HF_API_TOKEN=hf_your_real_token_here
HF_MODEL=meta-llama/Llama-3.1-8B-Instruct
```

If the default model is gated or unavailable on your account, an ungated alternative is `mistralai/Mistral-7B-Instruct-v0.3`.

### Running the system

**Terminal 1 — start the three MCP servers:**
```bash
python start_servers.py
```

**Terminal 2 — launch the frontend:**
```bash
streamlit run streamlit_app.py
```

Open `http://localhost:8501` in your browser.

**To stop the MCP servers:**
```bash
python start_servers.py stop
```

## Known Limitations

This is a capstone prototype, not a certified clinical tool:
- The medical knowledge base contains a limited, illustrative set of conditions and is not a substitute for professional medical diagnosis.
- The Hugging Face free inference tier can be rate-limited and may return a `503` while a model cold-starts; retrying after a short delay resolves this.
- No patient data is persisted beyond the active session — this is intentional for privacy, but means case history does not survive an app restart.

## License

MIT