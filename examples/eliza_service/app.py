from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
import json
import os
from pathlib import Path
import aiofiles
from celery_app import celery_app, process_code_generation
import asyncio
from extract_user_input import extract_user_input
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Ensure results directory exists
Path("results").mkdir(exist_ok=True)

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[List[str]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = 0
    frequency_penalty: Optional[float] = 0
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None

class Choice(BaseModel):
    index: int = 0
    message: Message
    finish_reason: str = "stop"

class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class ChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4()}")
    object: str = "chat.completion"
    created: int = 1677652288
    model: str
    choices: List[Choice]
    usage: Usage

async def generate_events(task_id: str):
    """Generate SSE events by reading the result file."""
    result_file = Path(f'results/{task_id}.html')
    last_content = ""
    
    while True:
        try:
            if not result_file.exists():
                yield 'data: File not found\n\n'
                break
                
            async with aiofiles.open(result_file, mode='r') as f:
                content = await f.read()
                
            if content != last_content:
                # Only send the new content
                new_content = content[len(last_content):]
                if new_content:
                    yield f'{new_content}\n\n'
                last_content = content
                
            # If content contains "COMPLETED" or "ERROR", stop streaming
            if 'COMPLETED' in content or 'ERROR' in content:
                break
                
            await asyncio.sleep(1)  # Wait before next update
            
        except Exception as e:
            yield f'data: Error: {str(e)}\n\n'
            break

@app.post("/v1/chat/completions")
async def create_chat_completion(request: ChatCompletionRequest) -> ChatCompletionResponse:
    
    # Extract the last message content for processing
    last_message = request.messages[-1] if request.messages else None
    if not last_message or last_message.role != "user":
        raise HTTPException(status_code=400, detail="Last message must be from user")
        
    # Extract user input from the message content
    extracted_input = await extract_user_input(last_message.content)
    if extracted_input == "No valid user input found":
        raise HTTPException(status_code=400, detail="No valid user input found in the message")
    
    print(extracted_input)
    
    # Update the last message with extracted input
    request.messages[-1].content = extracted_input
    
    task_id = str(uuid.uuid4())
    result_file = Path(f'results/{task_id}.html')
    
    # Create initial result file
    async with aiofiles.open(result_file, mode='w') as f:
        await f.write('<div class="status running">Initializing...</div>')
    
    # Start Celery task with the processed request
    process_code_generation.delay(task_id, request.model_dump())
    
    base_url = os.getenv('BASE_URL', "")
    # Generate response URL
    result_url = f"{base_url}/v1/results/{task_id}"
    
    eliza_expected_response = { "user": "magi", "text": f"You request accepted, please check here for your result: {result_url}", "action": "" }
    
    response_message = Message(
        role="assistant",
        content=json.dumps(eliza_expected_response)
    )
    
    return ChatCompletionResponse(
        model=request.model,
        choices=[
            Choice(
                message=response_message,
                finish_reason="stop"
            )
        ],
        usage=Usage()
    )

@app.get("/v1/results/{task_id}")
async def get_results(task_id: str):
    """Stream results as HTML."""
    return StreamingResponse(
        generate_events(task_id),
        media_type="text/html",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@app.get("/v1/status/{task_id}")
async def get_status(task_id: str):
    """Get task status."""
    result = celery_app.AsyncResult(task_id)
    return {"status": result.status}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
