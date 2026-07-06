# Care Coordinator Agent - Using Hugging Face Inference API
# agents/coordinator_agent.py

import os
import json
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv(override=True)

from openai import OpenAI
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class CareCoordinatorAgent(BaseAgent):
    """
    Care Coordinator Agent
    """

    def __init__(self):
        super().__init__(
            agent_name="CareCoordinatorAgent",
            mcp_server_url="http://localhost:8003"
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
        self.referral = {}

        logger.info(f"✅ Care Coordinator Agent initialized with Hugging Face API ({self.model})")

    async def process(
        self,
        patient_data: Dict[str, Any],
        diagnosis: str,
        urgency_level: str
    ) -> Dict[str, Any]:
        self.log_action("generate_care_plan", f"Creating plan for {diagnosis}")

        self.update_patient_data(patient_data)

        specialty = await self._determine_specialty(diagnosis)

        hospitals = await self._find_hospitals(specialty, patient_data, urgency_level)

        referral = await self._generate_referral(
            hospitals[0] if hospitals else {},
            diagnosis,
            patient_data,
            urgency_level
        )

        self.referral = referral

        return {
            "status": "success",
            "primary_referral": referral,
            "alternative_hospitals": hospitals[1:3] if len(hospitals) > 1 else [],
            "care_plan": {
                "immediate_action": self._get_immediate_action(urgency_level),
                "follow_up_schedule": self._get_follow_up_schedule(urgency_level),
                "patient_instructions": self._get_patient_instructions(diagnosis)
            }
        }

    async def _determine_specialty(self, diagnosis: str) -> str:
        prompt = f"""Determine the primary medical specialty for this diagnosis:
        Diagnosis: {diagnosis}

        Return ONLY the specialty name (e.g., Cardiology, Orthopedics, Internal Medicine).
        No punctuation, no explanation, just the specialty name.
        Specialty:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=20,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            specialty = response.choices[0].message.content.strip()
            # Some models echo extra text; keep just the first line/word group
            specialty = specialty.splitlines()[0].strip().strip(".")
            logger.info(f"{self.agent_name}: Determined specialty: {specialty}")

            return specialty
        except Exception as e:
            logger.error(f"Error in _determine_specialty: {str(e)}")
            return "General"

    async def _find_hospitals(
        self,
        specialty: str,
        patient_data: Dict[str, Any],
        urgency_level: str
    ) -> List[Dict[str, Any]]:
        location = patient_data.get("location", "Chittagong")

        payload = {
            "specialty": specialty,
            "location": location,
            "urgency_level": urgency_level
        }

        logger.info(f"{self.agent_name}: Searching for hospitals in {location}")

        response = self.call_mcp_tool("find_nearest_hospital", payload)

        hospitals = response.get("hospitals", [])
        logger.info(f"{self.agent_name}: Found {len(hospitals)} hospitals")

        return hospitals

    async def _generate_referral(
        self,
        hospital: Dict[str, Any],
        diagnosis: str,
        patient_data: Dict[str, Any],
        urgency_level: str
    ) -> Dict[str, Any]:
        if not hospital:
            return {
                "status": "no_hospital",
                "message": "No suitable hospital found"
            }

        payload = {
            "hospital_id": hospital.get("id", 1),
            "diagnosis": diagnosis,
            "urgency_level": urgency_level,
            "patient_info": {
                "age": patient_data.get("age"),
                "gender": patient_data.get("gender"),
                "patient_id": f"PAT-{patient_data.get('patient_id', 'UNKNOWN')}",
                "chief_complaint": patient_data.get("chief_complaint"),
                "medications": patient_data.get("current_medications", []),
                "allergies": patient_data.get("allergies", []),
                "medical_history": patient_data.get("medical_history", [])
            }
        }

        logger.info(f"{self.agent_name}: Generating referral for {hospital.get('name')}")

        response = self.call_mcp_tool("generate_referral_letter", payload)

        return {
            "hospital_id": hospital.get("id"),
            "hospital_name": hospital.get("name"),
            "address": hospital.get("address"),
            "phone": hospital.get("phone"),
            "referral_letter": response.get("referral_letter", ""),
            "tracking_id": response.get("tracking_id", ""),
            "urgent": urgency_level in ["EMERGENCY", "URGENT"]
        }

    def _get_immediate_action(self, urgency_level: str) -> str:
        actions = {
            "EMERGENCY": "🚨 Call emergency services immediately",
            "URGENT": "📞 Contact hospital immediately to arrange admission",
            "ROUTINE": "📅 Schedule appointment within 1 week"
        }
        return actions.get(urgency_level, "Standard follow-up")

    def _get_follow_up_schedule(self, urgency_level: str) -> str:
        schedules = {
            "EMERGENCY": "24-72 hours for initial assessment",
            "URGENT": "3-7 days for first evaluation",
            "ROUTINE": "7-14 days for appointment"
        }
        return schedules.get(urgency_level, "As arranged")

    def _get_patient_instructions(self, diagnosis: str) -> List[str]:
        return [
            "Bring all medical documents to the hospital",
            "Bring list of current medications",
            "Do not eat or drink if anesthesia may be needed",
            "Inform hospital of any medication allergies",
            "Arrange transport if needed",
            "Contact your primary care provider for follow-up"
        ]

    def get_referral(self) -> Dict[str, Any]:
        return self.referral