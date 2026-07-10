# Base Agent Class
# agents/base_agent.py

import json
import logging
import os
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from datetime import datetime
import requests

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# BASE AGENT CLASS
# ============================================

class BaseAgent(ABC):
    """
    Base class for all specialized agents
    Handles common functionality like MCP communication
    """
    
    def __init__(self, agent_name: str, mcp_server_url: Optional[str] = None):
        """
        Initialize base agent
        
        Args:
            agent_name: Name of the agent
            mcp_server_url: URL of MCP server to communicate with
        """
        self.agent_name = agent_name
        self.mcp_server_url = mcp_server_url
        self.conversation_history = []
        self.patient_data = {}
        self.created_at = datetime.now()
        
        logger.info(f"✅ Agent initialized: {agent_name}")
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input and return output
        Must be implemented by subclasses
        """
        pass
    
    def call_mcp_tool(self, tool_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool on the MCP server
        
        Args:
            tool_name: Name of the tool to call
            payload: Data to send to the tool
        
        Returns:
            Response from MCP server
        """
        
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
        """
        Add message to conversation history
        
        Args:
            role: "user" or "assistant"
            content: Message content
        """
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return self.conversation_history
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def update_patient_data(self, data: Dict[str, Any]):
        """Update patient data"""
        self.patient_data.update(data)
    
    def get_patient_data(self) -> Dict[str, Any]:
        """Get current patient data"""
        return self.patient_data
    
    def log_action(self, action: str, details: str = ""):
        """
        Log an action for audit trail
        
        Args:
            action: Action performed
            details: Additional details
        """
        log_entry = {
            "agent": self.agent_name,
            "action": action,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        logger.info(json.dumps(log_entry))
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data
        Override in subclasses for specific validation
        
        Args:
            input_data: Input to validate
        
        Returns:
            True if valid, False otherwise
        """
        return True
    
    def safe_json_parse(self, json_string: str) -> Dict[str, Any]:
        """
        Safely parse JSON string, handles various edge cases
        
        Args:
            json_string: JSON string to parse
        
        Returns:
            Parsed dict or empty dict if parsing fails
        """
        if not json_string:
            return {}
        
        try:
            # Try direct parsing
            return json.loads(json_string)
        except json.JSONDecodeError:
            pass
        
        try:
            # Try removing markdown code fences
            cleaned = json_string.strip()
            
            # Remove ```json and ``` markers
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            
            cleaned = cleaned.strip()
            
            # Try parsing cleaned version
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        
        try:
            # Try finding JSON object within text
            json_start = json_string.find('{')
            json_end = json_string.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_substr = json_string[json_start:json_end]
                return json.loads(json_substr)
        except json.JSONDecodeError:
            pass
        
        # If all parsing fails, log warning and return empty dict
        logger.warning(f"Failed to parse JSON: {json_string[:100]}...")
        return {}
    
    def __str__(self) -> str:
        """String representation of agent"""
        return f"{self.agent_name} (created: {self.created_at.isoformat()})"
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "agent_name": self.agent_name,
            "created_at": self.created_at.isoformat(),
            "history_length": len(self.conversation_history),
            "patient_data_keys": list(self.patient_data.keys()),
            "mcp_server": self.mcp_server_url
        }