import os
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
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

load_dotenv()

class LLMClient:
    def __init__(self, api_key: str = None, agent: str = "melchior"):
        """
        Initialize LLM client
        :param api_key: API key
        :param agent: agent type, available options: melchior, balthasar, casper, deconstructor, codegen
        """
        self.api_key = api_key or os.getenv("REDPILL_API_KEY")
        if not self.api_key:
            raise ValueError("REDPILL_API_KEY environment variable not set")
        self.base_url = "https://api.red-pill.ai/v1"
        self.agent = agent.lower()
        
    def create_chat_completion(self, messages: List[Dict[str, str]], model: str = "claude-3.5-sonnet", temperature: float = 0.7) -> Dict:
        """Make an API call and print request/response details."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        
        # Print request
        agent_type = ""
        # Extract agent type from the message content
        content = messages[-1]["content"]
        if "MELCHIOR-1" in content:
            agent_type = f"{Colors.CYAN}MELCHIOR-1{Colors.ENDC}"
        elif "BALTHASAR-2" in content:
            agent_type = f"{Colors.YELLOW}BALTHASAR-2{Colors.ENDC}"
        elif "CASPER-3" in content:
            agent_type = f"{Colors.BLUE}CASPER-3{Colors.ENDC}"
        
        print(format_section(
            f"REQUEST: {agent_type}" if agent_type else "REQUEST",
            messages[-1]["content"],
            Colors.CYAN
        ))
        
        response = requests.post(self.base_url + "/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # Print response
        # Extract decision for review responses
        decision = "NEGATIVE"  # Default
        
        # Try to find decision in XML format first
        decision_match = re.search(r"<decision>\s*(POSITIVE|NEGATIVE)\s*</decision>", content, re.IGNORECASE)
        if decision_match:
            decision = decision_match.group(1).upper()
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

    def create_system_prompt(self, question: str) -> str:
        if self.agent == "deconstructor":
            return self._create_deconstructor_prompt(question)
        elif self.agent == "concluder":
            return self._create_concluder_prompt(question)
        elif self.agent == "codegen":
            return self._create_codegen_prompt(question)
        return self._create_magi_prompt(question)
    
    def _create_concluder_prompt(self, question: str) -> str:
        return f"""You are the Final Decision Maker AI, tasked with analyzing the results from question deconstruction and MAGI evaluations to make a final POSITIVE or NEGATIVE decision.

Here is the original question and its analysis:

<original_question>
{question}
</original_question>

Your task is to:
1. Review the question deconstruction analysis
2. Examine the MAGI evaluations for each sub-question
3. Consider how the logical relationships and MAGI responses combine
4. Make a final decision based on all available information

Please structure your response as follows:

<analysis>
[Your detailed analysis of how the sub-questions, their MAGI evaluations, and their relationships lead to the final decision]
</analysis>

<final_decision>
[Your final decision: either POSITIVE or NEGATIVE]
</final_decision>"""

    def _create_deconstructor_prompt(self, question: str) -> str:
        examples = """<examples>
<example>
<ORIGINAL_QUESTION>
Should I buy a new car?
</ORIGINAL_QUESTION>
<ideal_output>
<question_analysis>
First, I'll determine if this is a decision-making question. "Should I buy a new car?" is indeed a decision-making question as it involves choosing between two options (buying a new car or not) and determining a course of action that leads to a specific outcome.

Now, I'll identify potential sub-questions that could help in making this decision:
1. Is my current car unreliable or frequently breaking down?
2. Can I afford the monthly payments for a new car?
3. Would a new car significantly improve my quality of life or work efficiency?
4. Are there good deals or incentives available for new cars right now?
5. Is my current car old or high-mileage?
6. Do I need features that my current car doesn't have?
7. Are there environmental considerations that make a new, more efficient car desirable?

I'll refine these to the most relevant questions:
- Questions 1 and 5 are related to the condition of the current car. I'll keep question 1 as it's more directly related to the need for a new car.
- Question 2 is crucial for financial considerations, so I'll keep it.
- Question 3 addresses the potential benefits of a new car, which is important for decision-making.
- Question 4 is relevant as it could influence the timing of the purchase.
- Questions 6 and 7 are more specific and can be considered part of question 3, so I'll omit them for simplicity.

Now, I'll determine the logical relationships between these questions:
- Either the current car being unreliable (1) OR a significant improvement in life/work (3) would be a reason to consider buying a new car. This forms an OR relationship.
- However, even if one of these is true, the person must be able to afford the car (2), forming an AND relationship with the previous OR condition.
- Finally, the availability of good deals (4) could be the deciding factor, so it forms another AND relationship.

This leads to the final structure of sub-questions and relationships.
</question_analysis>

<sub_questions>
<sub_question_1>Is my current car unreliable or frequently breaking down?</sub_question_1>
<sub_question_2>Can I afford the monthly payments for a new car?</sub_question_2>
<sub_question_3>Would a new car significantly improve my quality of life or work efficiency?</sub_question_3>
<sub_question_4>Are there good deals or incentives available for new cars right now?</sub_question_4>
</sub_questions>

<relationships>
(<sub_question_1> OR <sub_question_3>) AND <sub_question_2> AND <sub_question_4>
</relationships>
</ideal_output>
</example>
</examples>

"""
        return examples + f"""You are an advanced Question Deconstruction AI designed to break down complex decision-making questions into a set of binary (yes/no) sub-questions and establish relationships between them. This deconstruction process aids in making the final decision for the original question.

Here is the original question you need to analyze and deconstruct:

<original_question>
{question}
</original_question>

Please follow these steps to deconstruct the question:

1. Determine if the given question is a decision-making question. A decision-making question typically involves choosing between options, determining a course of action, or making a judgment that leads to a specific outcome.

2. If the question is not a decision-making question, respond with "N/A" and end your analysis.

3. If it is a decision-making question, proceed with the following steps:

   a. Break down the original question into a set of binary sub-questions. Each sub-question should:
      - Be answerable with either POSITIVE or NEGATIVE
      - Contribute to making the final decision
      - Be as simple and specific as possible

   b. Establish relationships between the sub-questions. These relationships can be:
      - AND: Both sub-questions need to be POSITIVE for the original question to be affirmative
      - OR: At least one sub-question needs to be POSITIVE for the original question to be affirmative
      - NOT: The inverse of a sub-question is required

   c. Format your output as follows:
      <sub_questions>
      <sub_question_1>[First sub-question]</sub_question_1>
      <sub_question_2>[Second sub-question]</sub_question_2>
      ...
      </sub_questions>

      <relationships>
      [Describe the relationships between sub-questions using <sub_question_N> notation and logical operators (AND, OR, NOT)]
      </relationships>

Before providing your final output, please show your thought process in <question_analysis> tags. This should include:
- Your explicit determination of whether the question is decision-making or not, with explanation
- A list of potential sub-questions you've identified, explaining why each is relevant
- Your process of refining and selecting the most relevant sub-questions
- Your reasoning for determining the logical relationships between sub-questions

It's okay for this section to be quite long to ensure a thorough analysis.

Now, please proceed with deconstructing the given question, starting with your thought process."""

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
        result = self.create_chat_completion(messages, model="claude-3.5-sonnet", temperature=0.7)
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
        result = self.create_chat_completion(messages, model="claude-3.5-sonnet", temperature=0.7)
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

    def _create_magi_prompt(self, question: str) -> str:
        examples = """<examples>
<example>
<QUESTION>
Is Earth a perfect sphere?
</QUESTION>
<ideal_output>
NEGATIVE
</ideal_output>
</example>
<example>
<QUESTION>
Does a year always have four seasons?
</QUESTION>
<ideal_output>
POSITIVE
</ideal_output>
</example>
</examples>

"""
        agent_roles = {
            "melchior": "MELCHIOR-1, you are a strict software architect with extremely high standards for code quality. You believe that good code must follow strict architectural design principles. When evaluating code, you will strictly review the following points with high standards:\n1. Whether the code strictly follows layered architecture design (clear separation of presentation, business, and data layers)\n2. Whether components are sufficiently decoupled (dependency injection, interface isolation)\n3. Adherence to SOLID principles and design patterns\n4. Code testability and unit test coverage\n5. Exception handling and system fault tolerance\n6. Code extensibility and maintainability\n7. Performance optimization and reasonable resource usage\n\nYour evaluation standards are high, and you will only give a POSITIVE evaluation when the code meets most of the above requirements. For any code that violates architectural design principles, you will give a NEGATIVE evaluation and explain the problems in detail.",
            "balthasar": "BALTHASAR-2, you represent the perspective of a security engineer, focusing on security and stability thinking. When evaluating code, you will consider:\n1. Security vulnerabilities and risks in the code\n2. Data validation and sanitization\n3. Error handling and exception mechanisms\n4. Protection of sensitive information\n5. System robustness and fault tolerance",
            "casper": "CASPER-3, you represent the perspective of a full-stack developer, focusing on practicality and user experience thinking. When evaluating code, you will focus on:\n1. Code readability and maintainability\n2. Completeness of functionality implementation\n3. User experience and interaction design\n4. Code reuse and modularity\n5. Development efficiency and implementation cost"
        }
        
        role_description = agent_roles.get(self.agent, agent_roles["melchior"])
        
        return examples + f"""You are now embodying the role of {role_description}

Your task is to answer a binary question with either POSITIVE or NEGATIVE. This answer should reflect your unique perspective and role.

When considering the question, apply the following guidelines:
1. Stay true to your character's perspective
2. Consider the implications from your unique viewpoint
3. Evaluate based on your designated thought process
4. Assess the situation holistically
5. Provide reasoning that aligns with your character

Here is the question you need to evaluate:

<question>
{question}
</question>

Before providing your final answer, use an inner monologue to reason through the question from your perspective. Consider the implications and consequences based on your character's viewpoint.

<inner_monologue>
[Your reasoning goes here]
</inner_monologue>

<answer>
[Your final answer: either POSITIVE or NEGATIVE]
</answer>"""
