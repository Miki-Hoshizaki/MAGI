from abc import ABC, abstractmethod
from typing import Optional, AsyncIterator, Dict, Any, Union

class BaseProvider(ABC):
    """Base class for all LLM providers."""
    
    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        self.kwargs = kwargs
        
    @abstractmethod
    async def generate(self, prompt: str, stream: bool = False, **kwargs) -> Union[str, AsyncIterator[str]]:
        """
        Generate response from the LLM.
        
        Args:
            prompt: Input text prompt
            stream: Whether to stream the response
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Either a complete response string or an async iterator of response chunks
        """
        pass
    
    @abstractmethod
    async def embeddings(self, text: str) -> list[float]:
        """
        Generate embeddings for the input text.
        
        Args:
            text: Input text to generate embeddings for
            
        Returns:
            List of embedding values
        """
        pass

class BaseAgent(ABC):
    """Base class for all agents that use LLM providers."""
    
    def __init__(self, provider: BaseProvider):
        self.provider = provider
        
    @abstractmethod
    async def run(self, input_data: Dict[str, Any], stream: bool = False) -> Union[Dict[str, Any], AsyncIterator[Dict[str, Any]]]:
        """
        Execute the agent's task.
        
        Args:
            input_data: Input data for the agent
            stream: Whether to stream the response
            
        Returns:
            Either a complete response or an async iterator of response chunks
        """
        pass
