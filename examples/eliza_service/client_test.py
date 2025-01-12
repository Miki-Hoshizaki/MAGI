import requests
import json
import webbrowser
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
                Create a Python function that implements a binary search algorithm.
                The function should:
                1. Take a sorted list and a target value as input
                2. Return the index if found, or -1 if not found
                3. Include proper type hints
                4. Include docstring with examples
                """
            }
        ]
    }
    
    # Send request
    response = requests.post(url, json=request_data)
    
    if response.status_code == 200:
        result = response.json()
        result_url = result['choices'][0]['message']['content']
        
        # Extract the URL from the response
        result_url = result_url.split(": ")[-1]
        
        # Construct full URL
        full_url = f"http://localhost:8000{result_url}"
        print(f"Opening result page in browser: {full_url}")
        
        # Open the result page in the default browser
        webbrowser.open(full_url)
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_code_generation()