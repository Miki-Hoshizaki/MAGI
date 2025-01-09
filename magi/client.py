from typing import Dict, Any, Optional, List
import os
import requests
import json
import re

# ANSI color codes
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def format_section(title: str, content: str, color: str = Colors.HEADER) -> str:
    separator = "=" * 50
    return f"""
{color}{separator}
{Colors.BOLD}【{title}】{Colors.ENDC}
{color}{separator}{Colors.ENDC}
{content}
"""

def format_decision(decision: str) -> str:
    color = Colors.GREEN if decision.upper() == "POSITIVE" else Colors.RED
    return f"{color}{decision}{Colors.ENDC}"

class LLMClient:
    """Client for interacting with LLM APIs."""
    
    def __init__(self):
        """Initialize the LLM client with API configuration."""
        self.api_key = os.getenv("REDPILL_API_KEY")
        if not self.api_key:
            raise ValueError("REDPILL_API_KEY environment variable not set")
        self.api_endpoint = "https://api.red-pill.ai/v1/chat/completions"

    def _call_api(self, messages: List[Dict[str, str]], description: str, is_review: bool = False) -> Dict:
        """Make an API call and print request/response details."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "claude-3.5-sonnet",
            "messages": messages,
            "temperature": 0.7
        }
        
        # Print request
        agent_type = ""
        if "melchior" in description.lower():
            agent_type = f"{Colors.CYAN}MELCHIOR-1{Colors.ENDC}"
        elif "balthasar" in description.lower():
            agent_type = f"{Colors.YELLOW}BALTHASAR-2{Colors.ENDC}"
        elif "casper" in description.lower():
            agent_type = f"{Colors.BLUE}CASPER-3{Colors.ENDC}"
        
        print(format_section(
            f"REQUEST: {agent_type}" if agent_type else "REQUEST",
            messages[-1]["content"],
            Colors.CYAN
        ))
        
        response = requests.post(self.api_endpoint, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # Print response
        if is_review:
            # Extract decision for review responses
            decision = "NEGATIVE"  # Default
            
            # Try to find decision in XML format first
            decision_match = re.search(r"<decision>\s*(POSITIVE|NEGATIVE)\s*</decision>", content, re.IGNORECASE)
            if decision_match:
                decision = decision_match.group(1).upper()
            else:
                # Fall back to looking for "DECISION:" format
                lines = content.strip().split("\n")
                for line in lines:
                    if "DECISION:" in line.upper():
                        parts = line.split(":", 1)
                        if len(parts) > 1:
                            decision_text = parts[1].strip()
                            # Extract POSITIVE/NEGATIVE, ignoring any brackets or extra text
                            if "POSITIVE" in decision_text.upper():
                                decision = "POSITIVE"
                            elif "NEGATIVE" in decision_text.upper():
                                decision = "NEGATIVE"
                            break
            
            print(format_section(
                f"RESPONSE: {agent_type} → {format_decision(decision)}",
                content,
                Colors.YELLOW
            ))
        else:
            print(format_section(
                "RESPONSE",
                content,
                Colors.GREEN
            ))
        
        return result
        
    def _create_agent_prompt(self, personality: str, original_request: str, generated_code: str) -> str:
        """Create a prompt for agent review based on personality."""
        role_descriptions = {
            "melchior": "MELCHIOR-1, a strict software architect with extremely high standards for code quality, who believes that good code must follow strict architectural design principles",
            "balthasar": "BALTHASAR-2, a security engineer with a deep focus on security and stability, who always prioritizes the safety and reliability of systems",
            "casper": "CASPER-3, a pragmatic full-stack developer who values practical solutions and excellent user experience above all"
        }
        
        evaluation_criteria = {
            "melchior": """1. Layered architecture design (separation of presentation, business, and data layers)
2. Component decoupling (dependency injection, interface isolation)
3. SOLID principles and design patterns adherence
4. Code testability and unit test coverage
5. Exception handling and system fault tolerance
6. Code extensibility and maintainability
7. Performance optimization and resource usage""",
            
            "balthasar": """1. Security vulnerabilities and potential risks
2. Data validation and sanitization practices
3. Error handling and exception mechanisms
4. Protection of sensitive information
5. System robustness and fault tolerance
6. Input validation and security best practices
7. Access control and authorization checks""",
            
            "casper": """1. Code readability and maintainability
2. Completeness of functionality implementation
3. User experience and interaction design
4. Code reuse and modularity
5. Development efficiency and implementation cost
6. API design and usability
7. Documentation and code comments"""
        }
        
        prompt_template = """You are now embodying the role of {role_description}.
Your task is to review the following code and decide if it meets your high standards (POSITIVE) or needs improvement (NEGATIVE).

<evaluation_criteria>
When reviewing this code, you must evaluate these specific points:
{criteria}
</evaluation_criteria>

<review_context>
Original Request:
{request}

Generated Code:
{code}
</review_context>

Before making your final decision, analyze the code thoroughly from your unique perspective. Consider each evaluation criterion and how well the code meets your standards.

<inner_monologue>
[Think through each evaluation criterion. Consider the strengths and weaknesses of the code from your perspective.]
</inner_monologue>

<decision>POSITIVE or NEGATIVE</decision>

<reasoning>
[Provide a detailed explanation of your decision, referencing specific aspects of the code and how they relate to your evaluation criteria.]
</reasoning>

Remember: As {role_description}, you must maintain your high standards and unique perspective in this evaluation."""

        return prompt_template.format(
            role_description=role_descriptions[personality],
            criteria=evaluation_criteria[personality],
            request=original_request,
            code=generated_code
        )

    def _create_codegen_prompt(self, original_request: str, previous_code: str = None, agent_feedback: List[Dict[str, str]] = None) -> str:
        """Create a prompt for code generation."""
        if previous_code and agent_feedback:
            return f"""Please generate code based on the following request and previous feedback:

Original Request:
{original_request}

Previous Implementation:
{previous_code}

Agent Feedback:
{self._format_agent_feedback(agent_feedback)}

Please provide improved code that addresses the feedback above. Format your response as follows:
<code>
[Your code here]
</code>"""
        else:
            return f"""Please generate code for the following request:

{original_request}

Format your response as follows:
<code>
[Your code here]
</code>"""

    def _format_agent_feedback(self, feedback: List[Dict[str, str]]) -> str:
        """Format agent feedback into a readable string."""
        result = []
        for i, f in enumerate(feedback, 1):
            result.append(f"Agent {i}:")
            result.append(f"Decision: {f['decision']}")
            result.append(f"Feedback: {f['reason']}")
            result.append("")
        return "\n".join(result)

    def generate_code(self, request: str, previous_code: str = None, agent_feedback: List[Dict[str, str]] = None) -> str:
        """Generate code using the LLM."""
        prompt = self._create_codegen_prompt(request, previous_code, agent_feedback)
        
        messages = [
            {"role": "system", "content": "You are an expert programmer. Generate clean, efficient, and secure code."},
            {"role": "user", "content": prompt}
        ]
        
        description = "Code Generation Request" if not previous_code else "Code Regeneration Request"
        result = self._call_api(messages, description)
        content = result["choices"][0]["message"]["content"]
        
        # Extract code between <code> tags
        code_match = re.search(r"<code>(.*?)</code>", content, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        return content  # Return full content if no code tags found
        
    def get_agent_review(self, personality: str, original_request: str, generated_code: str) -> Dict[str, str]:
        """Get code review from LLM based on agent personality."""
        prompt = self._create_agent_prompt(personality, original_request, generated_code)
        
        messages = [
            {"role": "system", "content": "You are an expert code reviewer with specific personality traits."},
            {"role": "user", "content": prompt}
        ]
        
        description = f"{personality.capitalize()} Agent Review"
        result = self._call_api(messages, description, is_review=True)
        review_text = result["choices"][0]["message"]["content"]
        
        # More robust parsing of the review text
        decision = "NEGATIVE"  # Default
        reason = review_text.strip()
        
        # Try to find decision in XML format first
        decision_match = re.search(r"<decision>\s*(POSITIVE|NEGATIVE)\s*</decision>", review_text, re.IGNORECASE)
        if decision_match:
            decision = decision_match.group(1).upper()
            # Remove the decision tag from reason
            reason = re.sub(r"<decision>.*?</decision>", "", reason, flags=re.IGNORECASE | re.DOTALL).strip()
        else:
            # Fall back to looking for "DECISION:" format
            lines = review_text.strip().split("\n")
            for line in lines:
                if "DECISION:" in line.upper():
                    parts = line.split(":", 1)
                    if len(parts) > 1:
                        decision_text = parts[1].strip()
                        # Extract POSITIVE/NEGATIVE, ignoring any brackets or extra text
                        if "POSITIVE" in decision_text.upper():
                            decision = "POSITIVE"
                        elif "NEGATIVE" in decision_text.upper():
                            decision = "NEGATIVE"
                        # Remove the decision line from reason
                        reason = "\n".join(l for l in lines if "DECISION:" not in l.upper()).strip()
                        break
        
        return {
            "decision": decision,
            "reason": reason
        }
