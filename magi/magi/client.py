import os
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class LLMClient:
    def __init__(self, api_key: str = None, agent: str = "melchior"):
        """
        Initialize LLM client
        :param api_key: API key
        :param agent: agent type, available options: melchior, balthasar, casper, deconstructor, codegen
        """
        self.api_key = api_key or os.getenv("REDPILL_API_KEY")
        self.base_url = "https://api.red-pill.ai/v1"
        self.agent = agent.lower()
        
    def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "claude-3.5-sonnet",
        temperature: float = 1,
        max_tokens: int = 4096,
        **kwargs
    ) -> Dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # If it's deconstructor, use lower temperature
        if self.agent == "deconstructor":
            temperature = 0
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()

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

    def _create_codegen_prompt(self, question: str) -> str:
        return f"""You are an expert code generator AI. Your task is to generate high-quality, well-documented code based on the user's requirements.

Please follow these guidelines when generating code:
1. Write clean, efficient, and maintainable code
2. Include appropriate error handling
3. Add clear comments and documentation
4. Follow best practices and coding standards
5. Consider edge cases and potential issues

Here is the programming question you need to address:

<question>
{question}
</question>

Please structure your response as follows:

<analysis>
[Your analysis of the requirements and approach]
</analysis>

<code>
[Your generated code solution]
</code>

<explanation>
[Brief explanation of how your code works and any important considerations]
</explanation>"""

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
            "melchior": "MELCHIOR-1, you are a strict software architect with extremely high standards for code quality. You believe that good code must follow strict architectural design principles. When evaluating code, you will strictly review the following points with high standards:\n1. Whether the code strictly follows layered architecture design (clear separation of presentation, business, and data layers)\n2. Whether components are sufficiently decoupled (dependency injection, interface isolation)\n3. Adherence to SOLID principles and design patterns\n4. Code testability and unit test coverage\n5. Completeness of exception handling and system fault tolerance\n6. Whether the code has good extensibility and maintainability\n7. Performance optimization and reasonable resource usage\n\nYour evaluation standards are high, and you will only give a POSITIVE evaluation when the code meets most of the above requirements. For any code that violates architectural design principles, you will give a NEGATIVE evaluation and explain the problems in detail.",
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
