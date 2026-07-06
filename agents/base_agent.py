# Base Agent Class
# agents/base_agent.py

import json
import logging
import os
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from datetime import datetime
import requests

from dotenv import load_dotenv
load_dotenv(override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all specialized agents
    Handles common functionality like MCP communication
    """

    def __init__(self, agent_name: str, mcp_server_url: Optional[str] = None):
        self.agent_name = agent_name
        self.mcp_server_url = mcp_server_url
        self.conversation_history = []
        self.patient_data = {}
        self.created_at = datetime.now()

        logger.info(f"✅ Agent initialized: {agent_name}")

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    def call_mcp_tool(self, tool_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.mcp_server_url:
            logger.warning(f"{self.agent_name}: No MCP server configured")
            return {"error": "MCP server not configured"}

        try:
            url = f"{self.mcp_server_url}/tools/{tool_name}"
            logger.info(f"{self.agent_name}: Calling {tool_name}")

            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"{self.agent_name}: {tool_name} succeeded")
                return data
            else:
                logger.error(f"{self.agent_name}: {tool_name} failed with status {response.status_code}")
                return {"error": f"MCP tool failed: {response.status_code}"}

        except requests.exceptions.Timeout:
            logger.error(f"{self.agent_name}: MCP request timeout")
            return {"error": "MCP server timeout"}
        except Exception as e:
            logger.error(f"{self.agent_name}: MCP error: {e}")
            return {"error": str(e)}

    def add_to_history(self, role: str, content: str):
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

    def get_history(self) -> List[Dict[str, Any]]:
        return self.conversation_history

    def clear_history(self):
        self.conversation_history = []

    def update_patient_data(self, data: Dict[str, Any]):
        self.patient_data.update(data)

    def get_patient_data(self) -> Dict[str, Any]:
        return self.patient_data

    def log_action(self, action: str, details: str = ""):
        log_entry = {
            "agent": self.agent_name,
            "action": action,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        logger.info(json.dumps(log_entry))

    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return True

    def __str__(self) -> str:
        return f"{self.agent_name} (created: {self.created_at.isoformat()})"

    def get_status(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "created_at": self.created_at.isoformat(),
            "history_length": len(self.conversation_history),
            "patient_data_keys": list(self.patient_data.keys()),
            "mcp_server": self.mcp_server_url
        }

    @staticmethod
    def safe_json_parse(text: str) -> dict:
        """
        Try a direct JSON parse first. If that fails (common with some
        Hugging Face-served models that wrap JSON in prose or markdown
        fences), fall back to extracting the first {...} block.
        """
        if not text:
            return {}

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Strip markdown code fences if present
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                pass

        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass

        return {}