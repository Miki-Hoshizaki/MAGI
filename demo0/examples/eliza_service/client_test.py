import requests
import json
import sys
import os

def test_code_generation():
    # API endpoint
    url = "http://localhost:8000/v1/chat/completions"
    
    # Sample request for code generation
    request_data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "user",
                "content": """
                ## Conversation Messages
                [2023-05-15 10:15:23] user: Create a Python script 
                that collect all Elon musk's tweets from Twitter and call GPT to analyze the sentiment of each tweet.
                """
            }
        ]
    }
    
    # Send request
    response = requests.post(url, json=request_data)
    
    if response.status_code == 200:
        result = response.json()
        result_url = result['choices'][0]['message']['content']
        print(result_url)
        
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_code_generation()