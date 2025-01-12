import os
import sys
from celery import Celery
from magi.agents.manager import AgentManager
from magi.client import LLMClient
import aiofiles
import asyncio
from pathlib import Path
from datetime import datetime
import json
import html
import re

# Initialize Celery
celery_app = Celery('eliza_service',
                    broker='redis://localhost:6379/0',
                    backend='redis://localhost:6379/0')

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
)

class HTMLFormatter:
    # HTML 标签的正则表达式
    HTML_TAG_PATTERN = re.compile(r'</?(?:div|span|p|h[1-6]|pre|code|br|hr|b|i|strong|em)(?:\s+[^>]*)?>', re.IGNORECASE)
    
    @staticmethod
    def escape_xml_tags(text: str) -> str:
        """Escape XML tags but preserve HTML tags."""
        if not isinstance(text, str):
            return str(text)
            
        # 保存所有合法的 HTML 标签
        preserved_tags = []
        def save_tag(match):
            preserved_tags.append(match.group(0))
            return f"___TAG_{len(preserved_tags)-1}___"
        
        # 替换并保存合法的 HTML 标签
        text = HTMLFormatter.HTML_TAG_PATTERN.sub(save_tag, text)
        
        # 转义所有剩余的 < 和 >
        text = html.escape(text)
        
        # 恢复保存的 HTML 标签
        for i, tag in enumerate(preserved_tags):
            text = text.replace(f"___TAG_{i}___", tag)
            
        return text

    @staticmethod
    def get_html_header():
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Magi Code Generation Result</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        h1, h2, h3 { color: #333; }
        .content {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 4px;
            border: 1px solid #dee2e6;
        }
        .code-block {
            background-color: #f1f3f5;
            padding: 15px;
            border-radius: 4px;
            margin: 10px 0;
            white-space: pre-wrap;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace;
        }
        .positive { color: #28a745; }
        .negative { color: #dc3545; }
        .agent-feedback {
            margin: 15px 0;
            padding: 10px;
            border-left: 4px solid #007bff;
            background-color: #f8f9fa;
        }
        .status {
            text-align: center;
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
        }
        .status.running { background-color: #cce5ff; color: #004085; }
        .status.completed { background-color: #d4edda; color: #155724; }
        .status.error { background-color: #f8d7da; color: #721c24; }
        
        /* 添加自定义标签的样式 */
        .xml-tag {
            display: block;
            margin: 10px 0;
            padding: 10px;
            background-color: #f8f9fa;
            border-left: 4px solid #6c757d;
            font-family: monospace;
            word-wrap: break-word;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Code Generation Progress</h1>
        <div class="content">'''

    @staticmethod
    def get_html_footer():
        return '''
        </div>
    </div>
</body>
</html>'''

    @staticmethod
    def format_code(code: str) -> str:
        escaped_code = HTMLFormatter.escape_xml_tags(code)
        return f'<div class="code-block"><pre><code>{escaped_code}</code></pre></div>'

    @staticmethod
    def format_agent_feedback(agent_num: int, feedback: dict) -> str:
        decision_class = 'positive' if feedback['decision'] == 'APPROVED' else 'negative'
        escaped_reason = HTMLFormatter.escape_xml_tags(feedback['reason'])
        return f'''
        <div class="agent-feedback">
            <h3>Agent {agent_num} Review:</h3>
            <p class="{decision_class}">Decision: {feedback['decision']}</p>
            <div class="xml-tag" style="white-space: pre-wrap;">{escaped_reason}</div>
        </div>
        '''

    @staticmethod
    def format_status(status: str) -> str:
        escaped_status = HTMLFormatter.escape_xml_tags(status)
        return f'<div class="status {escaped_status.lower()}">{escaped_status}</div>'

async def update_result_file(task_id: str, content: str, is_first: bool = False):
    result_file = Path(f'results/{task_id}.html')
    formatter = HTMLFormatter()
    
    if is_first:
        content = formatter.get_html_header() + content
    
    async with aiofiles.open(result_file, mode='w') as f:
        await f.write(content)

@celery_app.task(bind=True)
def process_code_generation(self, task_id: str, request_data: dict):
    try:
        # Initialize components
        manager = AgentManager(max_iterations=3)
        llm_client = LLMClient()
        formatter = HTMLFormatter()
        
        # Extract the programming request from messages
        programming_request = next(
            msg['content'] for msg in request_data['messages'] 
            if msg['role'] == 'user'
        )

        # Update status - Starting
        content = formatter.format_status("RUNNING")
        asyncio.run(update_result_file(task_id, content, is_first=True))

        # Generate initial code
        content += "<h2>Generating Initial Code</h2>"
        asyncio.run(update_result_file(task_id, content))
        
        initial_code = llm_client.generate_code(programming_request)
        content += formatter.format_code(initial_code)
        asyncio.run(update_result_file(task_id, content))

        # Review code
        content += "<h2>Reviewing Code</h2>"
        asyncio.run(update_result_file(task_id, content))
        
        result = manager.review_code(programming_request, initial_code)

        # Add agent feedback
        content += "<h2>Agent Reviews</h2>"
        for i, feedback in enumerate(result['feedbacks'], 1):
            content += formatter.format_agent_feedback(i, feedback)
        asyncio.run(update_result_file(task_id, content))

        # Add final results
        content += "<h2>Final Results</h2>"
        content += f"<p>Final Decision: <span class='{'positive' if result['approved'] else 'negative'}'>"
        content += f"{'APPROVED' if result['approved'] else 'REJECTED'}</span></p>"
        
        if result['approved']:
            content += "<h3>Final Code:</h3>"
            content += formatter.format_code(result['final_code'])
        
        # Update status - Completed
        content += formatter.format_status("COMPLETED")
        content += formatter.get_html_footer()
        asyncio.run(update_result_file(task_id, content))

        return {"status": "completed"}
        
    except Exception as e:
        # Update status - Error
        content = formatter.format_status(f"ERROR: {str(e)}")
        content += formatter.get_html_footer()
        asyncio.run(update_result_file(task_id, content))
        raise
