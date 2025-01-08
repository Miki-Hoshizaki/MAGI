import json
import re
from typing import List, Dict, Any, Tuple
from llm_client import LLMClient

def extract_code_generation_result(response: Dict[str, Any]) -> Tuple[str, str, str]:
    """Extract analysis, code and explanation from code generation result"""
    content = response["choices"][0]["message"]["content"]
    
    # Extract analysis part
    analysis_pattern = r"<analysis>(.*?)</analysis>"
    analysis_match = re.search(analysis_pattern, content, re.DOTALL)
    analysis = analysis_match.group(1).strip() if analysis_match else ""
    
    # Extract code part
    code_pattern = r"<code>(.*?)</code>"
    code_match = re.search(code_pattern, content, re.DOTALL)
    code = code_match.group(1).strip() if code_match else ""
    
    # Extract explanation part
    explanation_pattern = r"<explanation>(.*?)</explanation>"
    explanation_match = re.search(explanation_pattern, content, re.DOTALL)
    explanation = explanation_match.group(1).strip() if explanation_match else ""
    
    return analysis, code, explanation

def evaluate_code(magi: LLMClient, code_info: Tuple[str, str, str], original_question: str) -> str:
    """Use MAGI to evaluate code generation result
    :param magi: MAGI instance
    :param code_info: Tuple of (analysis, code, explanation)
    :param original_question: Original programming question
    """
    analysis, code, explanation = code_info
    messages = [
        {"role": "system", "content": magi.create_system_prompt(original_question)},
        {"role": "user", "content": f"""Original programming question: {original_question}

Please evaluate the following code generation result from your perspective:

Code generator's analysis:
{analysis}

Generated code:
{code}

Code explanation:
{explanation}

Please evaluate if this code generation result meets the requirements and give a POSITIVE or NEGATIVE judgment."""}
    ]
    
    try:
        print(f"\n{'-'*20} {magi.agent.upper()} Evaluation {'-'*20}")
        response = magi.create_chat_completion(messages)
        content = response["choices"][0]["message"]["content"]
        print(f"Complete evaluation:\n{content}\n")
        
        pattern = r"<answer>\s*(POSITIVE|NEGATIVE)\s*</answer>"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            result = match.group(1)
            print(f"Evaluation result: {result}")
            return result
        print("No explicit answer found, defaulting to NEGATIVE")
        return "NEGATIVE"
    except Exception as e:
        print(f"Error in MAGI evaluation: {e}")
        return "NEGATIVE"

def combine_magi_results(magi_results: List[str]) -> bool:
    """Combine results from three MAGIs, return True if two or more are POSITIVE"""
    positive_count = sum(1 for result in magi_results if result == "POSITIVE")
    return positive_count >= 2

def extract_feedback(response: Dict[str, Any]) -> str:
    """Extract feedback information from MAGI's evaluation"""
    content = response["choices"][0]["message"]["content"]
    inner_monologue_pattern = r"<inner_monologue>(.*?)</inner_monologue>"
    match = re.search(inner_monologue_pattern, content, re.DOTALL)
    return match.group(1).strip() if match else ""

def main():
    # Create codegen agent and three MAGI instances
    codegen = LLMClient(agent="codegen")
    magis = [
        LLMClient(agent="melchior"),
        LLMClient(agent="balthasar"),
        LLMClient(agent="casper")
    ]
    
    # Example programming question
    question = input("Please enter your programming question: ")
    
    max_attempts = 3
    attempt = 1
    
    while attempt <= max_attempts:
        print(f"\n=== Attempt #{attempt} ===")
        
        # Generate code
        print("\n=== Code Generation ===")
        messages = [
            {"role": "system", "content": codegen.create_system_prompt(question)},
            {"role": "user", "content": question}
        ]
        
        try:
            generation_result = codegen.create_chat_completion(messages)
            print(json.dumps(generation_result, ensure_ascii=False, indent=2))
            
            # Extract code generation result
            code_info = extract_code_generation_result(generation_result)
            analysis, code, explanation = code_info
            
            print("\n=== Generated Code ===")
            print(code)
            
            # Collect MAGI evaluations
            print("\n=== MAGI Evaluation ===")
            magi_results = []
            magi_feedback = []
            
            for magi in magis:
                result = evaluate_code(magi, code_info, question)
                magi_results.append(result)
                
                # If NEGATIVE, collect feedback
                if result == "NEGATIVE":
                    feedback = extract_feedback(generation_result)
                    if feedback:
                        magi_feedback.append(f"{magi.agent}: {feedback}")
            
            # Check if passed
            if combine_magi_results(magi_results):
                print("\n=== Final Result: PASSED ===")
                print("Generated code meets the requirements of at least two MAGIs")
                return
            
            # If not passed, prepare for next attempt
            if attempt < max_attempts:
                print("\n=== Preparing for Regeneration ===")
                print("MAGI Feedback:")
                for feedback in magi_feedback:
                    print(f"- {feedback}")
                
                # Update question with feedback
                question = f"""Original question: {question}

Previously generated code:
{code}

MAGI feedback:
{chr(10).join(magi_feedback)}

Please regenerate the code based on the above feedback."""
            
            attempt += 1
            
        except Exception as e:
            print(f"Error: {e}")
            print(f"Error type: {type(e)}")
            print(f"Error args: {e.args}")
            return
    
    print("\n=== Final Result: FAILED ===")
    print(f"After {max_attempts} attempts, still unable to generate code that meets requirements")

if __name__ == "__main__":
    main()
