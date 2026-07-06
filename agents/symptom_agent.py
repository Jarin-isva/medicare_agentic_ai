# Symptom Analysis Agent - Using Hugging Face Inference API
# agents/symptom_agent.py

import os
import json
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv(override=True)

from openai import OpenAI
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class SymptomAnalysisAgent(BaseAgent):
    """
    Clinical Analyzer Agent
    """

    def __init__(self):
        super().__init__(
            agent_name="SymptomAnalysisAgent",
            mcp_server_url="http://localhost:8001"
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
        self.differential_diagnoses = []

        logger.info(f"✅ Symptom Analysis Agent initialized with Hugging Face API ({self.model})")

    async def process(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        self.log_action("analyze_symptoms", "Analyzing symptoms for patient")

        self.update_patient_data(patient_data)

        symptoms = self._extract_symptom_list(patient_data)

        mcp_response = await self._call_medical_kb(symptoms, patient_data)

        analysis = await self._clinical_analysis(mcp_response, patient_data)

        self.differential_diagnoses = analysis.get("differential_diagnosis", [])

        return {
            "status": "success",
            "differential_diagnosis": analysis.get("differential_diagnosis", []),
            "clinical_reasoning": analysis.get("clinical_reasoning", ""),
            "recommended_tests": analysis.get("recommended_tests", []),
            "urgency_indicators": analysis.get("urgency_indicators", [])
        }

    def _extract_symptom_list(self, patient_data: Dict[str, Any]) -> List[str]:
        """
        Build a list of DB-friendly symptom keywords (matching the
        underscore-separated naming convention used in the symptoms table,
        e.g. 'body_ache', 'difficulty_breathing') from either an explicit
        'symptoms' list or the free-text chief complaint.
        """
        symptoms = patient_data.get("symptoms", [])
        if symptoms:
            # Normalize explicit symptoms too, in case they come as free text
            return [self._normalize_symptom(s) for s in symptoms if s]

        chief_complaint = patient_data.get("chief_complaint")
        if not chief_complaint:
            return []

        raw = chief_complaint.lower()
        raw = raw.replace(" and ", ",")
        candidates = [s.strip() for s in raw.split(",") if s.strip()]

        qualifiers = ["severe ", "mild ", "moderate ", "acute ", "chronic ", "sudden ", "slight "]
        normalized = []
        for c in candidates:
            for q in qualifiers:
                if c.startswith(q):
                    c = c[len(q):]
            normalized.append(self._normalize_symptom(c))

        return normalized

    @staticmethod
    def _normalize_symptom(text: str) -> str:
        """Convert free-text symptom phrases to underscore_case to match DB rows."""
        text = text.strip().lower()
        for prefix in ["severe ", "mild ", "moderate ", "acute ", "chronic ", "sudden ", "slight "]:
            if text.startswith(prefix):
                text = text[len(prefix):]
        return text.strip().replace(" ", "_")

    async def _call_medical_kb(self, symptoms: List[str], patient_data: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "symptoms": symptoms,
            "age": patient_data.get("age"),
            "gender": patient_data.get("gender"),
            "region": "Bangladesh"
        }

        logger.info(f"{self.agent_name}: Calling Medical KB for {len(symptoms)} symptoms: {symptoms}")

        response = self.call_mcp_tool("find_diseases", payload)

        logger.info(f"{self.agent_name}: Received {len(response.get('results', {}).get('diseases', []))} disease matches")

        return response

    async def _clinical_analysis(self, mcp_response: Dict[str, Any], patient_data: Dict[str, Any]) -> Dict[str, Any]:
        diseases = mcp_response.get("results", {}).get("diseases", [])

        if not diseases:
            return {
                "differential_diagnosis": [],
                "clinical_reasoning": "No matching diseases found in knowledge base",
                "recommended_tests": [],
                "urgency_indicators": []
            }

        analysis_prompt = f"""As a clinical reasoning engine, analyze this patient case:

PATIENT PROFILE:
- Age: {patient_data.get('age')} years
- Gender: {patient_data.get('gender')}
- Chief Complaint: {patient_data.get('chief_complaint')}
- Symptom Duration: {patient_data.get('symptom_duration')}
- Severity: {patient_data.get('symptom_severity')}/10
- Medical History: {', '.join(patient_data.get('medical_history', ['None'])) if patient_data.get('medical_history') else 'None'}
- Current Medications: {', '.join(patient_data.get('current_medications', ['None'])) if patient_data.get('current_medications') else 'None'}

DATABASE MATCHES (from Medical Knowledge Base):
{json.dumps(diseases[:5], indent=2)}

Your task:
1. Rank the top 3-5 most likely diagnoses
2. Explain clinical reasoning for each
3. Identify key distinguishing features
4. Recommend diagnostic tests
5. Flag any urgent considerations

Return ONLY JSON, no markdown code fences, no other text:
{{
    "differential_diagnosis": [
        {{
            "disease": "<name>",
            "probability": <0-1>,
            "severity": "<mild/moderate/severe>",
            "confidence": <0-1>,
            "reasoning": "<clinical rationale>",
            "supporting_features": ["<feature1>", "<feature2>"],
            "distinguishing_tests": ["<test1>", "<test2>"]
        }}
    ],
    "clinical_reasoning": "<overall analysis>",
    "recommended_tests": ["<test1>", "<test2>"],
    "urgency_indicators": ["<indicator1>", "<indicator2>"]
}}"""

        try:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=2000,
                    temperature=0.5,
                    messages=[{"role": "user", "content": analysis_prompt}],
                    response_format={"type": "json_object"}
                )
            except Exception as fmt_error:
                logger.warning(f"response_format not supported, retrying without it: {fmt_error}")
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=2000,
                    temperature=0.5,
                    messages=[{"role": "user", "content": analysis_prompt}]
                )

            response_text = response.choices[0].message.content

            analysis = self.safe_json_parse(response_text)
            if not analysis:
                logger.warning("Failed to parse clinical analysis JSON")
                return {
                    "differential_diagnosis": [],
                    "clinical_reasoning": response_text,
                    "recommended_tests": [],
                    "urgency_indicators": []
                }
            return analysis
        except Exception as e:
            logger.error(f"Error in _clinical_analysis: {str(e)}")
            return {
                "differential_diagnosis": [],
                "clinical_reasoning": f"Error: {str(e)}",
                "recommended_tests": [],
                "urgency_indicators": []
            }

    def get_top_diagnosis(self) -> Dict[str, Any]:
        if self.differential_diagnoses:
            return self.differential_diagnoses[0]
        return {}

    def get_differential_diagnosis(self) -> List[Dict[str, Any]]:
        return self.differential_diagnoses