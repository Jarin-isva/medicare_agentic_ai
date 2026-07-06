# Agent Orchestrator
# agents/agent_orchestrator.py

import os
import json
import logging
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv(override=True)

from agents.intake_agent import IntakeAgent
from agents.symptom_agent import SymptomAnalysisAgent
from agents.triage_agent import TriageAgent
from agents.coordinator_agent import CareCoordinatorAgent

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    def __init__(self):
        try:
            self.intake_agent = IntakeAgent()
            self.analysis_agent = SymptomAnalysisAgent()
            self.triage_agent = TriageAgent()
            self.coordinator_agent = CareCoordinatorAgent()

            self.workflow_state = "IDLE"
            self.patient_session = {}

            logger.info("✅ Agent Orchestrator initialized with 4 agents")
        except ValueError as e:
            logger.error(f"❌ Error initializing agents: {e}")
            raise

    async def start_patient_workflow(self, patient_id: str = "NEW") -> Dict[str, Any]:
        logger.info(f"Starting workflow for patient: {patient_id}")

        self.workflow_state = "INTAKE"
        self.patient_session = {
            "patient_id": patient_id,
            "workflow_stages": {
                "intake": False,
                "analysis": False,
                "triage": False,
                "coordination": False
            }
        }

        intake_result = await self.intake_agent.start_intake()

        return {
            "status": "workflow_started",
            "stage": "INTAKE",
            "patient_id": patient_id,
            "message": intake_result.get("agent_greeting", "Error starting intake"),
            "next_action": "Respond to intake questions"
        }

    async def process_intake_response(self, user_input: str) -> Dict[str, Any]:
        if self.workflow_state != "INTAKE":
            return {"error": "Not in intake stage"}

        logger.info("Processing intake response")

        result = await self.intake_agent.process(user_input)

        if self.intake_agent.is_intake_complete():
            logger.info("Intake complete, moving to analysis")
            self.workflow_state = "ANALYSIS"
            self.patient_session["workflow_stages"]["intake"] = True

            return {
                "status": "intake_complete",
                "agent_response": result["agent_response"],
                "patient_data": self.intake_agent.get_patient_data(),
                "next_stage": "ANALYSIS",
                "message": "Thank you. Let me analyze your symptoms..."
            }

        return {
            "status": "intake_continues",
            "agent_response": result["agent_response"],
            "extracted_data": result["extracted_data"]
        }

    async def run_analysis(self) -> Dict[str, Any]:
        if self.workflow_state != "ANALYSIS":
            return {"error": "Not in analysis stage"}

        logger.info("Running symptom analysis")

        patient_data = self.intake_agent.get_patient_data()

        result = await self.analysis_agent.process(patient_data)

        self.workflow_state = "TRIAGE"
        self.patient_session["workflow_stages"]["analysis"] = True

        return {
            "status": "analysis_complete",
            "differential_diagnosis": result["differential_diagnosis"],
            "clinical_reasoning": result["clinical_reasoning"],
            "next_stage": "TRIAGE"
        }

    async def run_triage(self) -> Dict[str, Any]:
        if self.workflow_state != "TRIAGE":
            return {"error": "Not in triage stage"}

        logger.info("Running emergency triage")

        patient_data = self.intake_agent.get_patient_data()

        result = await self.triage_agent.process(patient_data)

        self.workflow_state = "COORDINATION"
        self.patient_session["workflow_stages"]["triage"] = True

        return {
            "status": "triage_complete",
            "urgency_level": result["urgency_level"],
            "risk_score": result["risk_score"],
            "recommendation": result.get("recommendation", ""),
            "immediate_action": result.get("immediate_action", ""),
            "next_stage": "COORDINATION"
        }

    async def run_coordination(self) -> Dict[str, Any]:
        if self.workflow_state != "COORDINATION":
            return {"error": "Not in coordination stage"}

        logger.info("Running care coordination")

        patient_data = self.intake_agent.get_patient_data()
        diagnosis = self.analysis_agent.get_top_diagnosis()
        urgency_level = self.triage_agent.get_urgency_level()

        diagnosis_name = diagnosis.get("disease", "Unknown Condition")

        result = await self.coordinator_agent.process(
            patient_data,
            diagnosis_name,
            urgency_level
        )

        self.workflow_state = "COMPLETE"
        self.patient_session["workflow_stages"]["coordination"] = True

        return {
            "status": "workflow_complete",
            "referral": result["primary_referral"],
            "alternatives": result.get("alternative_hospitals", []),
            "care_plan": result["care_plan"],
            "message": "Your care plan has been prepared"
        }

    async def run_complete_workflow(self, initial_input: str) -> Dict[str, Any]:
        logger.info("Running complete workflow")

        await self.start_patient_workflow()
        intake_response = await self.process_intake_response(initial_input)

        if intake_response["status"] != "intake_complete":
            return {
                "status": "intake_in_progress",
                "message": "Please provide more information"
            }

        analysis_result = await self.run_analysis()
        triage_result = await self.run_triage()
        coordination_result = await self.run_coordination()

        return {
            "status": "complete",
            "workflow_completed": True,
            "intake": intake_response,
            "analysis": analysis_result,
            "triage": triage_result,
            "coordination": coordination_result
        }

    def get_workflow_status(self) -> Dict[str, Any]:
        return {
            "current_stage": self.workflow_state,
            "patient_session": self.patient_session,
            "agents_status": {
                "intake": self.intake_agent.get_status(),
                "analysis": self.analysis_agent.get_status(),
                "triage": self.triage_agent.get_status(),
                "coordinator": self.coordinator_agent.get_status()
            }
        }

    def reset_workflow(self):
        self.workflow_state = "IDLE"
        self.patient_session = {}
        self.intake_agent.clear_history()
        logger.info("Workflow reset for new patient")