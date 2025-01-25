
import os
import json
import aiohttp
import re
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

PROMPT = '''
You are tasked with extracting the user input from either a "Conversation Messages" section or a "Current Post" format in the given markdown text. Follow these steps carefully:

1. The markdown text will be provided to you within <markdown_text> tags.

<markdown_text>
{{MARKDOWN_TEXT}}
</markdown_text>

2. First, check if there is a "Current Post" section. If found, extract the text from the "Text" field, ignoring the ID and From fields.

Example Current Post format:
```
Current Post:
  ID: 1881188681874371040
  From: Miki (@MikiHoshizaki)
  Text: @magiintelligent Write me a bubble sort algorithm in Python
```

3. If no Current Post is found, look for the "Conversation Messages" section and:
   - Find the last message that is not from the AI (messages from the AI typically start with a timestamp and an alphanumeric code in square brackets)
   - Extract the content of this last user message, ignoring any timestamps or user identifiers

4. Output the extracted content within <latest_user_input> tags.

If neither format is found or no valid user input is present, output <latest_user_input>No valid user input found</latest_user_input>.

Remember to include only the actual content of the user's message, without any additional formatting or metadata. For Current Post format, exclude any @ mentions at the start of the Text field.
'''


async def extract_user_input(markdown_text: str) -> str:
    """
    Asynchronously extract the last user input from markdown text using redpill API.
    
    Args:
        markdown_text (str): The markdown text containing conversation messages
        
    Returns:
        str: The extracted user input or "No valid user input found" if none found
    """
    print(f'Extracting user input from markdown text: {markdown_text}')
    api_key = os.getenv("REDPILL_API_KEY")
    if not api_key:
        raise ValueError("REDPILL_API_KEY environment variable not set")
        
    base_url = "https://api.red-pill.ai/v1"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    messages = [
        {"role": "system", "content": PROMPT},
        {"role": "user", "content": markdown_text}
    ]
    
    payload = {
        "model": "claude-3.5-sonnet",
        "messages": messages,
        "temperature": 0
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"API request failed with status {response.status}: {error_text}")
                
            result = await response.json()
            
            # Extract content from response
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Extract user input from the response using regex
            match = re.search(r"<latest_user_input>(.*?)</latest_user_input>", content, re.DOTALL)
            if match:
                return match.group(1).strip()
            return "No valid user input found"