"""
Django management command to test all active LLM models.
"""
import time
import requests
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.llm_providers.models import LLMModel
from typing import Dict, Any
from termcolor import colored

class Command(BaseCommand):
    help = 'Test all active LLM models for availability'

    def make_test_request(self, model: LLMModel) -> Dict[str, Any]:
        """
        Make a test request to the LLM model.
        
        Args:
            model: The LLM model to test
            
        Returns:
            Dict containing test results
        """
        start_time = time.time()
        error = None
        response = None
        
        try:
            headers = {
                "Authorization": f"Bearer {model.provider.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": model.model_name,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Reply with 'OK' if you can receive this message."}
                ],
                "temperature": 0.7,
                "max_tokens": 10
            }
            
            response = requests.post(
                f"{model.provider.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30  # 30 seconds timeout
            )
            response.raise_for_status()
            response_data = response.json()
            
        except requests.exceptions.RequestException as e:
            error = str(e)
        except Exception as e:
            error = str(e)
            
        end_time = time.time()
        duration = end_time - start_time
        
        return {
            "duration": duration,
            "error": error,
            "status_code": response.status_code if response else None,
            "response": response_data if response and not error else None
        }

    def handle(self, *args, **kwargs):
        models = LLMModel.objects.filter(is_active=True).select_related('provider')
        
        if not models:
            self.stdout.write(self.style.WARNING("No active LLM models found"))
            return
            
        self.stdout.write(self.style.SUCCESS(f"Testing {len(models)} active LLM models...\n"))
        
        results = []
        for model in models:
            self.stdout.write(f"Testing {model.name} from {model.provider.name}...")
            
            test_result = self.make_test_request(model)
            
            if test_result["error"]:
                status = colored("FAILED", "red")
                details = f"Error: {test_result['error']}"
            else:
                status = colored("SUCCESS", "green")
                response_content = test_result["response"]["choices"][0]["message"]["content"]
                details = f"Response: {response_content}"
                
            self.stdout.write(f"  Status: {status}")
            self.stdout.write(f"  Duration: {test_result['duration']:.2f}s")
            self.stdout.write(f"  {details}\n")
            
            results.append({
                "model": model,
                "result": test_result
            })
            
        # Print summary
        self.stdout.write(self.style.SUCCESS("Test Summary:"))
        success_count = len([r for r in results if not r["result"]["error"]])
        fail_count = len(results) - success_count
        
        self.stdout.write(f"Total models tested: {len(results)}")
        self.stdout.write(colored(f"Successful: {success_count}", "green"))
        if fail_count > 0:
            self.stdout.write(colored(f"Failed: {fail_count}", "red"))
