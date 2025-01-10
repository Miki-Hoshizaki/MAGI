from typing import Dict, Any
from . import BaseAgent, FeedbackResult
from ..client import LLMClient

class MelchiorAgent(BaseAgent):
    """MELCHIOR-1: A strict software architect focused on architectural design principles."""
    
    def __init__(self):
        self.llm_client = LLMClient()
    
    def review(self, original_request: str, generated_code: str, context: Dict[str, Any] = None) -> FeedbackResult:
        return self.llm_client.get_agent_review("melchior", original_request, generated_code)

class BalthasarAgent(BaseAgent):
    """BALTHASAR-2: A security engineer focused on security and stability."""
    
    def __init__(self):
        self.llm_client = LLMClient()
    
    def review(self, original_request: str, generated_code: str, context: Dict[str, Any] = None) -> FeedbackResult:
        return self.llm_client.get_agent_review("balthasar", original_request, generated_code)

class CasperAgent(BaseAgent):
    """CASPER-3: A full-stack developer focused on practicality and user experience."""
    
    def __init__(self):
        self.llm_client = LLMClient()
    
    def review(self, original_request: str, generated_code: str, context: Dict[str, Any] = None) -> FeedbackResult:
        return self.llm_client.get_agent_review("casper", original_request, generated_code)
