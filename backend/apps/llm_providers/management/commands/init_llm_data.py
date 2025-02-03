"""
Django management command to initialize LLM providers and agents.
"""
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from apps.llm_providers.models import LLMProvider, LLMModel
from apps.agents.models import Agent

User = get_user_model()

class Command(BaseCommand):
    help = 'Initialize LLM providers and agents'

    def handle(self, *args, **kwargs):
        try:
            with transaction.atomic():
                # Create superuser
                if not User.objects.filter(username='admin').exists():
                    User.objects.create_superuser(
                        username='admin',
                        password='admin',
                        email='admin@magisystem.ai'
                    )
                    self.stdout.write(self.style.SUCCESS('Created superuser: admin'))

                # Create RedPill provider
                redpill_provider = LLMProvider.objects.create(
                    name="RedPill AI",
                    provider_type="openai",  # Compatible with OpenAI API
                    base_url="https://api.red-pill.ai/v1",
                    api_key=os.getenv("REDPILL_API_KEY", ""),
                    is_active=True,
                    priority=1
                )
                self.stdout.write(self.style.SUCCESS(f"Created LLM provider: {redpill_provider.name}"))

                # Create Claude model
                claude_model = LLMModel.objects.create(
                    provider=redpill_provider,
                    name="Claude 3.5 Sonnet",
                    model_name="claude-3.5-sonnet",
                    description="Anthropic's Claude 3.5 Sonnet model via RedPill API",
                    features={
                        "supports_streaming": True,
                        "supports_functions": True,
                        "max_context_length": 100000
                    },
                    max_tokens=4096,
                    is_active=True
                )
                self.stdout.write(self.style.SUCCESS(f"Created LLM model: {claude_model.name}"))

                # Create the three code review agents
                agents_data = [
                    {
                        "id": "d37c1cc8-bcc4-4b73-9f49-a93a30971f2c",
                        "name": "MELCHIOR-1",
                        "description": "A strict software architect focused on architectural design principles.",
                        "system_prompt": """You are MELCHIOR-1, a strict software architect with expertise in architectural design principles.
Your role is to review code with a focus on:
1. Architectural patterns and design principles
2. Code organization and structure
3. Scalability and maintainability
4. Component interactions and dependencies

Evaluate the code based on these criteria and provide a detailed review.
Your response must include a <decision>POSITIVE</decision> or <decision>NEGATIVE</decision> tag.""",
                        "user_prompt_template": """Original Request:
{user_request}

Generated Code:
{code}

Please review the code focusing on architectural design principles and provide your feedback.""",
                        "temperature": 0.7,
                        "weight": 1.0
                    },
                    {
                        "id": "6634d0ec-d700-4a92-9066-4960a0f11927",
                        "name": "BALTHASAR-2",
                        "description": "A security engineer focused on security and stability.",
                        "system_prompt": """You are BALTHASAR-2, a security engineer with expertise in code security and stability.
Your role is to review code with a focus on:
1. Security vulnerabilities and best practices
2. Input validation and sanitization
3. Error handling and system stability
4. Data protection and privacy

Evaluate the code based on these criteria and provide a detailed review.
Your response must include a <decision>POSITIVE</decision> or <decision>NEGATIVE</decision> tag.""",
                        "user_prompt_template": """Original Request:
{user_request}

Generated Code:
{code}

Please review the code focusing on security and stability aspects and provide your feedback.""",
                        "temperature": 0.7,
                        "weight": 1.0
                    },
                    {
                        "id": "89cbe912-25d0-47b0-97da-b25622bfac0d",
                        "name": "CASPER-3",
                        "description": "A full-stack developer focused on practicality and user experience.",
                        "system_prompt": """You are CASPER-3, a full-stack developer with expertise in practical implementation and user experience.
Your role is to review code with a focus on:
1. Code functionality and completeness
2. User experience and interface design
3. Performance and efficiency
4. Implementation best practices

Evaluate the code based on these criteria and provide a detailed review.
Your response must include a <decision>POSITIVE</decision> or <decision>NEGATIVE</decision> tag.""",
                        "user_prompt_template": """Original Request:
{user_request}

Generated Code:
{code}

Please review the code focusing on practicality and user experience aspects and provide your feedback.""",
                        "temperature": 0.7,
                        "weight": 1.0
                    }
                ]

                for agent_data in agents_data:
                    agent = Agent.objects.create(
                        id=agent_data["id"],
                        name=agent_data["name"],
                        description=agent_data["description"],
                        llm_model=claude_model,
                        system_prompt=agent_data["system_prompt"],
                        user_prompt_template=agent_data["user_prompt_template"],
                        temperature=agent_data["temperature"],
                        weight=agent_data["weight"]
                    )
                    self.stdout.write(self.style.SUCCESS(f"Created agent: {agent.name}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error initializing data: {str(e)}"))
            raise
