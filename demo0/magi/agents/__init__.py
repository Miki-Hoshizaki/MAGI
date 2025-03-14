from abc import ABC, abstractmethod
from typing import Dict, Any, Literal, TypedDict

class FeedbackResult(TypedDict):
    decision: Literal["POSITIVE", "NEGATIVE"]
    reason: str

class BaseAgent(ABC):
    """Base class for all code review agents."""
    
    @abstractmethod
    def review(self, 
              original_request: str,
              generated_code: str,
              context: Dict[str, Any] = None) -> FeedbackResult:
        """Review the generated code and provide feedback.
        
        Args:
            original_request: The original user request that led to code generation
            generated_code: The code generated by the system
            context: Additional context information (optional)
            
        Returns:
            FeedbackResult containing the decision and reasoning
        """
        pass
