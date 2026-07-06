# Intake Agent - Using Hugging Face Inference API (OpenAI-compatible router)
# agents/intake_agent.py

import os
import json
import logging
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv(override=True)

from openai import OpenAI
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class IntakeAgent(BaseAgent):
    """
    Intake Specialist Agent
    """

    def __init__(self):
        super().__init__(
            agent_name="IntakeAgent",
            mcp_server_url=None
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
        self.conversation_complete = False

        logger.info(f"✅ Intake Agent initialized with Hugging Face API ({self.model})")

    async def process(self, user_input: str) -> Dict[str, Any]:
        self.log_action("process_intake", f"User input: {user_input[:50]}...")

        self.add_to_history("user", user_input)

        response = await self._get_agent_response()

        self.add_to_history("assistant", response)

        extracted_data = await self._extract_structured_data()

        return {
            "status": "success",
            "agent_response": response,
            "extracted_data": extracted_data,
            "conversation_complete": self.conversation_complete,
            "patient_data": self.patient_data
        }

    async def start_intake(self) -> Dict[str, Any]:
        self.log_action("start_intake", "Beginning patient intake")

        system_prompt = """You are a professional healthcare intake specialist for MediGuide.

Your role:
1. Greet the patient warmly and professionally
2. Ask about their chief complaint (main health concern)
3. Gradually gather information in a conversational manner:
   - Age and gender (if not provided)
   - Duration and severity of symptoms (1-10 scale)
   - Current medications
   - Allergies
   - Medical history
   - Recent travel or exposures
4. Be empathetic and non-judgmental
5. Validate information back to the patient

Guidelines:
- Ask ONE question at a time
- Use simple, non-medical language when possible
- Show you're listening with brief acknowledgments
- When you have enough information, summarize and ask for confirmation
- Avoid diagnostic language (this is intake, not diagnosis)

Start by introducing yourself and asking what brings them in today."""

        user_message = "Hello, I need medical assistance."
        self.add_to_history("user", user_message)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=500,
                temperature=0.7,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            )

            agent_response = response.choices[0].message.content
            self.add_to_history("assistant", agent_response)

            self.log_action("start_intake", "Initial greeting sent")

            return {
                "status": "intake_started",
                "agent_greeting": agent_response,
                "agent": self.agent_name
            }
        except Exception as e:
            logger.error(f"Error in start_intake: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "agent_greeting": "I encountered an error. Please check your Hugging Face API token.",
                "agent": self.agent_name
            }

    async def _get_agent_response(self) -> str:
        system_prompt = """You are a professional healthcare intake specialist for MediGuide.

Your role:
1. Engage in natural conversation to gather patient information
2. Ask clarifying questions when needed
3. Acknowledge and validate responses
4. Gradually build a complete patient profile
5. When you have sufficient information (at least: age, chief complaint, symptom duration, severity, medications, allergies), offer to summarize

Guidelines:
- Ask ONE question at a time
- Use conversational language
- Show empathy and active listening
- After each response, ask a follow-up or move to the next information area
- If patient seems reluctant about a topic, acknowledge and move forward
- When ready, summarize: "Let me confirm what I've gathered..." then list key information

Do NOT provide medical advice or diagnoses during intake."""

        try:
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend([
                {"role": msg["role"], "content": msg["content"]}
                for msg in self.conversation_history
            ])

            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=500,
                temperature=0.7,
                messages=messages
            )

            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in _get_agent_response: {str(e)}")
            return f"I encountered an error processing your response: {str(e)}"

    async def _extract_structured_data(self) -> Dict[str, Any]:
        extraction_prompt = f"""Based on this conversation history, extract ALL patient information available.

Conversation:
{json.dumps(self.conversation_history, indent=2)}

Return ONLY a JSON object with this structure (use null for missing fields):
{{
    "age": <int or null>,
    "gender": "<M/F/Other or null>",
    "chief_complaint": "<main symptom>",
    "symptom_duration": "<e.g., '3 days', '2 weeks'>",
    "symptom_severity": <1-10 or null>,
    "current_medications": [<list of medications>],
    "allergies": [<list of allergies>],
    "medical_history": [<list of past conditions>],
    "recent_travel": "<location or null>",
    "exposure_history": "<contacts or environmental>",
    "pregnancy_status": "<if applicable>"
}}

STRICT: Return ONLY valid JSON, no other text, no markdown code fences."""

        try:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=500,
                    temperature=0.3,
                    messages=[{"role": "user", "content": extraction_prompt}],
                    response_format={"type": "json_object"}
                )
            except Exception as fmt_error:
                # Some HF-served models reject response_format outright.
                logger.warning(f"response_format not supported, retrying without it: {fmt_error}")
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=500,
                    temperature=0.3,
                    messages=[{"role": "user", "content": extraction_prompt}]
                )

            response_text = response.choices[0].message.content

            extracted_data = self.safe_json_parse(response_text)
            if not extracted_data:
                logger.warning("Failed to extract JSON from response")
                return {}

            self.update_patient_data(extracted_data)
            return extracted_data
        except Exception as e:
            logger.error(f"Error in _extract_structured_data: {str(e)}")
            return {}

    def is_intake_complete(self) -> bool:
        required_fields = ["age", "chief_complaint", "symptom_severity"]

        for field in required_fields:
            if field not in self.patient_data or self.patient_data[field] is None:
                return False

        self.conversation_complete = True
        return True