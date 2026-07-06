# Emergency Triage Agent - Using Hugging Face Inference API
# agents/triage_agent.py

import os
import json
import logging
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv(override=True)

from openai import OpenAI
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class TriageAgent(BaseAgent):
    """
    Emergency Triage Agent
    """

    def __init__(self):
        super().__init__(
            agent_name="TriageAgent",
            mcp_server_url="http://localhost:8002"
        )

        api_key = os.getenv("HF_TOKEN")
        base_url = os.getenv("HF_BASE_URL", "https://router.huggingface.co/v1")

        if not api_key or api_key.startswith("hf_your"):
            raise ValueError(
                "❌ HF_TOKEN not configured in .env file. "
                "Get one from https://huggingface.co/settings/tokens"
            )

        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = os.getenv("HF_MODEL", "meta-llama/Llama-3.3-70B-Instruct")
        self.urgency_level = "ROUTINE"
        self.red_flags = []
        self.confidence = 0.0

        logger.info(f"✅ Triage Agent initialized with Hugging Face API ({self.model})")

    async def process(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        self.log_action("assess_urgency", "Beginning triage assessment")

        self.update_patient_data(patient_data)

        red_flag_assessment = await self._check_red_flags(patient_data)

        if red_flag_assessment.get("has_emergency"):
            self.urgency_level = "EMERGENCY"
            self.red_flags = red_flag_assessment.get("red_flags", [])
            self.confidence = red_flag_assessment.get("confidence", 0.99)

            return {
                "status": "success",
                "urgency_level": "EMERGENCY",
                "risk_score": 0.95,
                "confidence": 0.99,
                "red_flags_detected": self.red_flags,
                "immediate_action": "🚨 CALL EMERGENCY SERVICES IMMEDIATELY",
                "action_code": "CALL_911",
                "reasoning": f"Life-threatening condition detected: {', '.join(self.red_flags)}"
            }

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
        assessment_prompt = f"""As an emergency medicine expert, assess this patient's urgency:

PATIENT PROFILE:
- Age: {patient_data.get('age')} years
- Chief Complaint: {patient_data.get('chief_complaint')}
- Symptom Severity: {patient_data.get('symptom_severity')}/10
- Duration: {patient_data.get('symptom_duration')}
- Medical History: {', '.join(patient_data.get('medical_history', ['None'])) if patient_data.get('medical_history') else 'None'}
- Current Medications: {', '.join(patient_data.get('current_medications', [])) if patient_data.get('current_medications') else 'None'}
- Vital Signs: {patient_data.get('vital_signs', {})}

ASSESSMENT TASK:
1. Determine urgency level: EMERGENCY / URGENT / ROUTINE
2. Calculate risk score (0-1)
3. Identify contributing factors
4. Provide immediate recommendation
5. Specify action code

GUIDELINES:
- EMERGENCY: Immediate life-threat (CALL 911)
- URGENT: Same-day evaluation needed
- ROUTINE: Can wait for clinic appointment

Return ONLY JSON, no markdown code fences, no other text:
{{
    "urgency_level": "<EMERGENCY|URGENT|ROUTINE>",
    "risk_score": <0-1>,
    "confidence": <0-1>,
    "contributing_factors": {{
        "age_risk": <0-1>,
        "symptom_severity_risk": <0-1>,
        "medical_history_risk": <0-1>,
        "vital_sign_risk": <0-1>
    }},
    "recommendation": "<action needed>",
    "action_code": "<CALL_911|URGENT_CLINIC|ROUTINE_CLINIC>"
}}"""

        try:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=1000,
                    temperature=0.5,
                    messages=[{"role": "user", "content": assessment_prompt}],
                    response_format={"type": "json_object"}
                )
            except Exception as fmt_error:
                logger.warning(f"response_format not supported, retrying without it: {fmt_error}")
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=1000,
                    temperature=0.5,
                    messages=[{"role": "user", "content": assessment_prompt}]
                )

            response_text = response.choices[0].message.content

            assessment = self.safe_json_parse(response_text)
            if not assessment:
                logger.warning("Failed to parse triage assessment")
                return {
                    "urgency_level": "ROUTINE",
                    "risk_score": 0.3,
                    "confidence": 0.5,
                    "recommendation": "Standard evaluation needed",
                    "action_code": "ROUTINE_CLINIC"
                }
            return assessment
        except Exception as e:
            logger.error(f"Error in _assess_emergency_level: {str(e)}")
            return {
                "urgency_level": "ROUTINE",
                "risk_score": 0.3,
                "confidence": 0.5,
                "recommendation": "Standard evaluation needed",
                "action_code": "ROUTINE_CLINIC"
            }

    def get_urgency_level(self) -> str:
        return self.urgency_level

    def is_emergency(self) -> bool:
        return self.urgency_level == "EMERGENCY"