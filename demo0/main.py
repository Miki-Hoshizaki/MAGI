from magi.agents.manager import AgentManager
from magi.client import LLMClient
import os
from dotenv import load_dotenv

def evaluate_code(original_request: str, initial_code: str = None) -> None:
    """Test the code review system with sample code."""
    manager = AgentManager(max_iterations=3)
    llm_client = LLMClient()
    
    # Generate initial code if not provided
    if initial_code is None:
        print("\n=== Generating Initial Code ===")
        initial_code = llm_client.generate_code(original_request)
        print(f"Initial Code:\n{initial_code}\n")
    
    # Review and potentially regenerate code
    result = manager.review_code(original_request, initial_code)
    
    # Print final results
    print("\n=== Final Results ===")
    print(f"Final Decision: {'APPROVED' if result['approved'] else 'REJECTED'}")
    print(f"\nFinal Code:\n{result['final_code']}")
    
    print("\nFinal Agent Reviews:")
    for i, feedback in enumerate(result['feedbacks'], 1):
        print(f"\nAgent {i} Review:")
        print(f"Decision: {feedback['decision']}")
        print(f"Reason: {feedback['reason']}")

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Test case 1: Simple request
    print("\n=== Test Case 1: Simple Request ===")
    original_request = """
    Create a function that calculates the factorial of a number recursively.
    The function should handle negative numbers and include proper input validation.
    """
    
    evaluate_code(original_request)
    
    # Test case 2: More complex request
    print("\n=== Test Case 2: Complex Request ===")
    original_request = """
    Create a secure password validation function that checks:
    - Minimum length of 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    Return True if valid, False otherwise.
    """
    
    evaluate_code(original_request)

    # Test case 3: More complex request - Twitter Analysis
    print("\n=== Test Case 3: Twitter Analysis Request ===")
    original_request = """
    Create a Python script that:
    1. Uses the Twitter API to fetch Elon Musk's recent tweets (last 100 tweets)
    2. For each tweet:
       - Use OpenAI's GPT model to analyze the sentiment regarding stock market impact
       - Assign a score from -5 to +5 where:
         * -5 means extremely negative impact on US stocks
         * +5 means extremely positive impact on US stocks
         * 0 means neutral or no impact
    3. Calculate:
       - Average sentiment score
       - Total number of positive and negative tweets
       - Most impactful tweets (highest absolute scores)
    4. Generate a final conclusion about Elon's overall Twitter sentiment impact on US stocks
    
    Requirements:
    - Use Twitter API v2
    - Include proper error handling for API rate limits
    - Format the output in a clear, readable way
    - Cache results to avoid unnecessary API calls
    - Use asyncio for efficient API requests
    """
    
    evaluate_code(original_request)

if __name__ == "__main__":
    main()
