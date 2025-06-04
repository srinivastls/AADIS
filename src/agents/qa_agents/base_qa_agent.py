
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import logging
from src.agents.base_agent import BaseAgent

class BaseQAAgent(BaseAgent):
    """Base class for all QA agents"""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.capabilities = []
    
    @abstractmethod
    def can_handle(self, query: str, query_type: str) -> bool:
        """Determine if this agent can handle the given query"""
        pass
    
    @abstractmethod
    def process_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process the query and return results"""
        pass
    
    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent supports"""
        return self.capabilities