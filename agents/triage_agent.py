# Emergency Triage Agent - Using Hugging Face API
# agents/triage_agent.py

import os
import json
import logging
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

from openai import OpenAI
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class TriageAgent(BaseAgent):
    """
    Emergency Triage Agent using Hugging Face API
    
    Responsibilities:
    - Detect life-threatening conditions
    - Assess emergency risk level
    - Classify urgency (EMERGENCY/URGENT/ROUTINE)
    """
    
    def __init__(self):
        """Initialize with Hugging Face API"""
        super().__init__(
            agent_name="TriageAgent",
            mcp_server_url="http://localhost:8002"
        )
        
        api_key = os.getenv("HF_TOKEN")
        base_url = os.getenv("HF_BASE_URL", "https://api-inference.huggingface.co/v1")
        
        if not api_key or api_key.startswith("hf_your"):
            raise ValueError("❌ HF_TOKEN not configured")
        
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = os.getenv("HF_MODEL", "meta-llama/Llama-3.3-70B-Instruct")
        self.urgency_level = "ROUTINE"
        self.red_flags = []
        self.confidence = 0.0
        
        logger.info(f"✅ Triage Agent initialized with Hugging Face API")
    
    async def process(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess patient urgency and emergency risk
        """
        
        self.log_action("assess_urgency", "Beginning triage")
        
        self.update_patient_data(patient_data)
        
        # Step 1: Check red flags
        red_flag_assessment = await self._check_red_flags(patient_data)
        
        # If emergency detected, escalate immediately
        if red_flag_assessment.get("has_emergency"):
            self.urgency_level = "EMERGENCY"
            self.red_flags = red_flag_assessment.get("red_flags", [])
            self.confidence = 0.99
            
            return {
                "status": "success",
                "urgency_level": "EMERGENCY",
                "risk_score": 0.95,
                "confidence": 0.99,
                "red_flags_detected": self.red_flags,
                "immediate_action": "🚨 CALL EMERGENCY SERVICES IMMEDIATELY",
                "action_code": "CALL_911",
                "reasoning": f"Life-threatening detected: {', '.join(self.red_flags)}"
            }
        
        # Step 2: Full assessment with Hugging Face
        assessment = await self._assess_emergency_level(patient_data)
        
        self.urgency_level = assessment.get("urgency_level", "ROUTINE")
        self.confidence = assessment.get("confidence", 0.5)
        
        return {
            "status": "success",
            "urgency_level": assessment.get("urgency_level"),
            "risk_score": assessment.get("risk_score"),
            "confidence": assessment.get("confidence"),
            "contributing_factors": assessment.get("contributing_factors", {}),
            "recommendation": assessment.get("recommendation"),
            "action_code": assessment.get("action_code")
        }
    
    async def _check_red_flags(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check for critical red flags using MCP Server
        """
        
        payload = {
            "symptoms": [patient_data.get("chief_complaint", "")],
            "age": patient_data.get("age"),
            "vital_signs": patient_data.get("vital_signs", {}),
            "medical_history": patient_data.get("medical_history", [])
        }
        
        logger.info(f"{self.agent_name}: Checking red flags")
        
        response = self.call_mcp_tool("check_red_flags", payload)
        
        return response
    
    async def _assess_emergency_level(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive emergency assessment with Hugging Face
        """
        
        assessment_prompt = f"""As an emergency medicine expert, assess this patient's urgency:

PATIENT PROFILE:
- Age: {patient_data.get('age')} years
- Chief Complaint: {patient_data.get('chief_complaint')}
- Severity: {patient_data.get('symptom_severity')}/10
- Duration: {patient_data.get('symptom_duration')}
- Medical History: {', '.join(patient_data.get('medical_history', ['None'])) if patient_data.get('medical_history') else 'None'}

Determine urgency: EMERGENCY / URGENT / ROUTINE

Return ONLY JSON:
{{
    "urgency_level": "<EMERGENCY|URGENT|ROUTINE>",
    "risk_score": <0-1>,
    "confidence": <0-1>,
    "contributing_factors": {{"age_risk": <0-1>}},
    "recommendation": "<action>",
    "action_code": "<CALL_911|URGENT_CLINIC|ROUTINE_CLINIC>"
}}"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": assessment_prompt}],
                temperature=0.5,
                max_tokens=1000
            )
            
            response_text = response.choices[0].message.content
            
            assessment = self.safe_json_parse(response_text)
            if assessment:
                return assessment
            else:
                return {
                    "urgency_level": "ROUTINE",
                    "risk_score": 0.3,
                    "confidence": 0.5,
                    "recommendation": "Standard evaluation",
                    "action_code": "ROUTINE_CLINIC"
                }
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return {
                "urgency_level": "ROUTINE",
                "risk_score": 0.3,
                "confidence": 0.5,
                "recommendation": "Standard evaluation",
                "action_code": "ROUTINE_CLINIC"
            }
    
    def get_urgency_level(self) -> str:
        """Get current urgency level"""
        return self.urgency_level
    
    def is_emergency(self) -> bool:
        """Check if emergency"""
        return self.urgency_level == "EMERGENCY"