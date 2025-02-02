import openai
from typing import Union, AsyncIterator
from ..base import BaseProvider

class OpenAIProvider(BaseProvider):
    """OpenAI API provider implementation."""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", base_url: str = None, **kwargs):
        super().__init__(api_key, **kwargs)
        self.model = model
        self.client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=base_url if base_url else None
        )
        
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
                async for chunk in await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=True,
                    **kwargs
                ):
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            return response_stream()
        else:
            response = await self.client.chat.completions.create(
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
        response = await self.client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding

    async def stream_chat(self, system_prompt: str, user_prompt: str, **kwargs) -> AsyncIterator[str]:
        """
        Stream chat response using OpenAI API.
        
        Args:
            system_prompt: System prompt that defines the context
            user_prompt: User's input prompt
            **kwargs: Additional OpenAI-specific parameters
            
        Returns:
            An async iterator of response chunks
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        async for chunk in await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            **kwargs
        ):
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
