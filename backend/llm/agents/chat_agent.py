from typing import Dict, Any, Union, AsyncIterator
from ..base import BaseAgent, BaseProvider

class ChatAgent(BaseAgent):
    """Simple chat agent implementation."""
    
    async def run(
        self, 
        input_data: Dict[str, Any], 
        stream: bool = False
    ) -> Union[Dict[str, Any], AsyncIterator[Dict[str, Any]]]:
        """
        Process chat input and generate response.
        
        Args:
            input_data: Dictionary containing 'message' key with user input
            stream: Whether to stream the response
            
        Returns:
            Dictionary containing 'response' key with agent's response
        """
        message = input_data.get('message', '')
        if not message:
            raise ValueError("Input message is required")
            
        if stream:
            async def response_stream():
                async for chunk in await self.provider.generate(message, stream=True):
                    yield {"response": chunk}
            return response_stream()
        else:
            response = await self.provider.generate(message, stream=False)
            return {"response": response}
