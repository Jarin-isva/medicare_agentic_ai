# Symptom Analysis Agent - Using Hugging Face API
# agents/symptom_agent.py

import os
import json
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

from openai import OpenAI
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class SymptomAnalysisAgent(BaseAgent):
    """
    Clinical Analyzer Agent using Hugging Face API
    
    Responsibilities:
    - Analyze symptoms using Medical Knowledge Base MCP Server
    - Generate differential diagnosis
    - Provide clinical reasoning
    """
    
    def __init__(self):
        """Initialize with Hugging Face API"""
        super().__init__(
            agent_name="SymptomAnalysisAgent",
            mcp_server_url="http://localhost:8001"
        )
        
        api_key = os.getenv("HF_TOKEN")
        base_url = os.getenv("HF_BASE_URL", "https://api-inference.huggingface.co/v1")
        
        if not api_key or api_key.startswith("hf_your"):
            raise ValueError("❌ HF_TOKEN not configured")
        
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = os.getenv("HF_MODEL", "meta-llama/Llama-3.3-70B-Instruct")
        self.differential_diagnoses = []
        
        logger.info(f"✅ Symptom Analysis Agent initialized with Hugging Face API")
    
    async def process(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze patient symptoms and generate differential diagnosis
        
        Args:
            patient_data: Patient information from intake
        
        Returns:
            Differential diagnosis and analysis
        """
        
        self.log_action("analyze_symptoms", "Analyzing symptoms")
        
        self.update_patient_data(patient_data)
        
        # Step 1: Call Medical KB MCP Server
        symptoms = patient_data.get("symptoms", [])
        if not symptoms and patient_data.get("chief_complaint"):
            symptoms = [patient_data["chief_complaint"]]
        
        mcp_response = await self._call_medical_kb(symptoms, patient_data)
        
        # Step 2: Analyze with Hugging Face
        analysis = await self._clinical_analysis(mcp_response, patient_data)
        
        self.differential_diagnoses = analysis.get("differential_diagnosis", [])
        
        return {
            "status": "success",
            "differential_diagnosis": analysis.get("differential_diagnosis", []),
            "clinical_reasoning": analysis.get("clinical_reasoning", ""),
            "recommended_tests": analysis.get("recommended_tests", []),
            "urgency_indicators": analysis.get("urgency_indicators", [])
        }
    
    async def _call_medical_kb(self, symptoms: List[str], patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call Medical Knowledge Base MCP Server
        """
        
        payload = {
            "symptoms": symptoms,
            "age": patient_data.get("age"),
            "gender": patient_data.get("gender"),
            "region": "Bangladesh"
        }
        
        logger.info(f"{self.agent_name}: Calling Medical KB")
        
        response = self.call_mcp_tool("find_diseases", payload)
        
        return response
    
    async def _clinical_analysis(self, mcp_response: Dict[str, Any], patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform clinical analysis with Hugging Face
        """
        
        diseases = mcp_response.get("results", {}).get("diseases", [])
        
        if not diseases:
            return {
                "differential_diagnosis": [],
                "clinical_reasoning": "No matching diseases found",
                "recommended_tests": [],
                "urgency_indicators": []
            }
        
        analysis_prompt = f"""As a clinical reasoning engine, analyze this patient case:

PATIENT PROFILE:
- Age: {patient_data.get('age')} years
- Gender: {patient_data.get('gender')}
- Chief Complaint: {patient_data.get('chief_complaint')}
- Duration: {patient_data.get('symptom_duration')}
- Severity: {patient_data.get('symptom_severity')}/10

DATABASE MATCHES:
{json.dumps(diseases[:5], indent=2)}

Return ONLY JSON:
{{
    "differential_diagnosis": [
        {{
            "disease": "<name>",
            "probability": <0-1>,
            "severity": "<mild/moderate/severe>",
            "confidence": <0-1>,
            "reasoning": "<rationale>"
        }}
    ],
    "clinical_reasoning": "<analysis>",
    "recommended_tests": ["<test1>"],
    "urgency_indicators": ["<indicator>"]
}}"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.5,
                max_tokens=2000
            )
            
            response_text = response.choices[0].message.content
            
            analysis = self.safe_json_parse(response_text)
            if analysis:
                return analysis
            else:
                return {
                    "differential_diagnosis": [],
                    "clinical_reasoning": response_text,
                    "recommended_tests": [],
                    "urgency_indicators": []
                }
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return {
                "differential_diagnosis": [],
                "clinical_reasoning": f"Error: {str(e)}",
                "recommended_tests": [],
                "urgency_indicators": []
            }
    
    def get_top_diagnosis(self) -> Dict[str, Any]:
        """Get the most likely diagnosis"""
        if self.differential_diagnoses:
            return self.differential_diagnoses[0]
        return {}
    
    def get_differential_diagnosis(self) -> List[Dict[str, Any]]:
        """Get all differential diagnoses"""
        return self.differential_diagnoses