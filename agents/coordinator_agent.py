# Care Coordinator Agent - Using Hugging Face API
# agents/coordinator_agent.py

import os
import json
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

from openai import OpenAI
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class CareCoordinatorAgent(BaseAgent):
    """
    Care Coordinator Agent using Hugging Face API
    
    Responsibilities:
    - Generate referrals to appropriate specialists
    - Match patients to care facilities
    - Schedule follow-ups
    """
    
    def __init__(self):
        """Initialize with Hugging Face API"""
        super().__init__(
            agent_name="CareCoordinatorAgent",
            mcp_server_url="http://localhost:8003"
        )
        
        api_key = os.getenv("HF_TOKEN")
        base_url = os.getenv("HF_BASE_URL", "https://api-inference.huggingface.co/v1")
        
        if not api_key or api_key.startswith("hf_your"):
            raise ValueError("❌ HF_TOKEN not configured")
        
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = os.getenv("HF_MODEL", "meta-llama/Llama-3.3-70B-Instruct")
        self.referral = {}
        
        logger.info(f"✅ Care Coordinator Agent initialized with Hugging Face API")
    
    async def process(
        self, 
        patient_data: Dict[str, Any],
        diagnosis: str,
        urgency_level: str
    ) -> Dict[str, Any]:
        """
        Generate care plan and referrals
        """
        
        self.log_action("generate_care_plan", f"Creating plan for {diagnosis}")
        
        self.update_patient_data(patient_data)
        
        # Step 1: Determine required specialty
        specialty = await self._determine_specialty(diagnosis)
        
        # Step 2: Find nearest hospital
        hospitals = await self._find_hospitals(specialty, patient_data, urgency_level)
        
        # Step 3: Generate referral
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
        """
        Determine required medical specialty
        """
        
        prompt = f"""Determine specialty for: {diagnosis}
        Return ONLY the specialty name (e.g., Cardiology, Internal Medicine).
        Specialty:"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=50
            )
            
            specialty = response.choices[0].message.content.strip()
            logger.info(f"{self.agent_name}: Specialty: {specialty}")
            
            return specialty
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return "General"
    
    async def _find_hospitals(
        self,
        specialty: str,
        patient_data: Dict[str, Any],
        urgency_level: str
    ) -> List[Dict[str, Any]]:
        """
        Find hospitals matching specialty
        """
        
        location = patient_data.get("location", "Chittagong")
        
        payload = {
            "specialty": specialty,
            "location": location,
            "urgency_level": urgency_level
        }
        
        logger.info(f"{self.agent_name}: Finding hospitals in {location}")
        
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
        """
        Generate referral letter
        """
        
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
        """Get immediate action based on urgency"""
        actions = {
            "EMERGENCY": "🚨 Call emergency services immediately",
            "URGENT": "📞 Contact hospital immediately",
            "ROUTINE": "📅 Schedule appointment within 1 week"
        }
        return actions.get(urgency_level, "Standard follow-up")
    
    def _get_follow_up_schedule(self, urgency_level: str) -> str:
        """Get follow-up schedule"""
        schedules = {
            "EMERGENCY": "24-72 hours for assessment",
            "URGENT": "3-7 days for evaluation",
            "ROUTINE": "7-14 days for appointment"
        }
        return schedules.get(urgency_level, "As arranged")
    
    def _get_patient_instructions(self, diagnosis: str) -> List[str]:
        """Get patient instructions"""
        return [
            "Bring all medical documents",
            "Bring list of current medications",
            "Inform hospital of any allergies",
            "Arrange transport if needed",
            "Contact your primary care provider for follow-up"
        ]
    
    def get_referral(self) -> Dict[str, Any]:
        """Get current referral"""
        return self.referral