import openai
from typing import Union, AsyncIterator
from ..base import BaseProvider

class OpenAIProvider(BaseProvider):
    """OpenAI API provider implementation."""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", **kwargs):
        super().__init__(api_key, **kwargs)
        self.model = model
        openai.api_key = api_key
        
    async def generate(self, prompt: str, stream: bool = False, **kwargs) -> Union[str, AsyncIterator[str]]:
        """
        Generate response using OpenAI API.
        
        Args:
            prompt: Input text prompt
            stream: Whether to stream the response
            **kwargs: Additional OpenAI-specific parameters
            
        Returns:
            Either a complete response string or an async iterator of response chunks
        """
        messages = [{"role": "user", "content": prompt}]
        
        if stream:
            async def response_stream():
                async for chunk in await openai.ChatCompletion.acreate(
                    model=self.model,
                    messages=messages,
                    stream=True,
                    **kwargs
                ):
                    if chunk and chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            return response_stream()
        else:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=messages,
                stream=False,
                **kwargs
            )
            return response.choices[0].message.content
            
    async def embeddings(self, text: str) -> list[float]:
        """
        Generate embeddings using OpenAI API.
        
        Args:
            text: Input text to generate embeddings for
            
        Returns:
            List of embedding values
        """
        response = await openai.Embedding.acreate(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding
