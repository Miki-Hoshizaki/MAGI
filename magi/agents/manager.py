from typing import List, Dict, Any, TypedDict, Optional
from . import BaseAgent, FeedbackResult
from .builtin import MelchiorAgent, BalthasarAgent, CasperAgent
from ..magi.client import LLMClient, Colors

APPROVAL_BANNER = f"""
{Colors.GREEN}
⭐️⭐️⭐️ CODE APPROVED ⭐️⭐️⭐️

     ____________________
    |                    |
    |    MAGI SYSTEM    |
    |     APPROVED      |
    |____________________|
    (\__/) ||
    (•ㅅ•) ||
    / 　 づ

All agents have reached consensus! 
{Colors.ENDC}"""

CODE_BLOCK_START = f"""
{Colors.CYAN}{'='*46}
▶️ {Colors.BOLD}APPROVED CODE START{Colors.ENDC} {Colors.CYAN}▶️
{'='*46}{Colors.ENDC}
"""

CODE_BLOCK_END = f"""
{Colors.CYAN}{'='*46}
⏹️ {Colors.BOLD}APPROVED CODE END{Colors.ENDC} {Colors.CYAN}⏹️
{'='*46}{Colors.ENDC}
"""

class ReviewResult(TypedDict):
    approved: bool
    feedbacks: List[FeedbackResult]
    final_code: str

class AgentManager:
    """Manages multiple agents and coordinates their decisions."""
    
    def __init__(self, agents: List[BaseAgent] = None, max_iterations: int = 3):
        """Initialize with a list of agents or use default built-in agents."""
        if agents is None:
            self.agents = [
                MelchiorAgent(),
                BalthasarAgent(),
                CasperAgent()
            ]
        else:
            self.agents = agents
        
        self.max_iterations = max_iterations
        self.llm_client = LLMClient()
    
    def review_code(self, original_request: str, generated_code: str, context: Dict[str, Any] = None) -> ReviewResult:
        """Review code with all agents and return the result."""
        iteration = 0
        while iteration < self.max_iterations:
            print(f"\n{Colors.BOLD}🔄 Iteration {iteration + 1}/{self.max_iterations}{Colors.ENDC}")
            
            # Collect feedback from all agents
            feedbacks = []
            negative_count = 0
            
            for agent in self.agents:
                feedback = agent.review(original_request, generated_code, context)
                feedbacks.append(feedback)
                if feedback["decision"].upper() == "NEGATIVE":
                    negative_count += 1
            
            # If less than 2 agents give negative feedback, code is approved
            if negative_count < 2:
                print(APPROVAL_BANNER)
                print(CODE_BLOCK_START)
                print(generated_code)
                print(CODE_BLOCK_END)
                return {
                    "approved": True,
                    "feedbacks": feedbacks,
                    "final_code": generated_code
                }
            
            print(f"\n{Colors.RED}❌ Code rejected by {negative_count} agents. Regenerating...{Colors.ENDC}")
            
            # Regenerate code based on feedback
            generated_code = self.llm_client.generate_code(
                original_request,
                previous_code=generated_code,
                agent_feedback=feedbacks
            )
            
            iteration += 1
        
        print(f"\n{Colors.YELLOW}⚠️ Maximum iterations reached without approval{Colors.ENDC}")
        return {
            "approved": False,
            "feedbacks": feedbacks,
            "final_code": generated_code
        }
