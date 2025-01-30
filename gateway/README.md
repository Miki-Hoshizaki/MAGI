# Magi Gateway Service

Gateway service for the Magi system, providing WebSocket-based real-time communication between clients and backend services.

## Features

- WebSocket-based real-time communication
- Authentication with appid + token mechanism
- Redis-based message queue integration
- Support for agent judgement streaming
- Automatic reconnection and error handling

## Prerequisites

- Python 3.9+
- Docker and Docker Compose (for local development)
- Poetry (recommended) or pip

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd magi/gateway
```

2. Install dependencies:
```bash
# Using pip
pip install -r requirements.txt

# Or using Poetry
poetry install
```

## Local Development with Docker Compose

For local development, we provide a `docker-compose.dev.yml` file that sets up required services like Redis.

1. Start the development services:
```bash
docker compose -f docker-compose.dev.yml up -d
```

This will start:
- Redis server on port 6379 with data persistence

2. Check services status:
```bash
docker compose -f docker-compose.dev.yml ps
```

3. View logs:
```bash
docker compose -f docker-compose.dev.yml logs -f
```

4. Stop services:
```bash
docker compose -f docker-compose.dev.yml down
```

To remove all data volumes:
```bash
docker compose -f docker-compose.dev.yml down -v
```

## Configuration

Create a `.env` file in the gateway directory with the following settings:

```env
# Application settings
DEBUG=true
HOST=0.0.0.0
PORT=8000

# Redis settings
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Authentication
FIXED_SECRET=your-secret-key  # Change this in production!

# CORS settings
CORS_ORIGINS=*  # Use comma-separated values in production
```

## Running the Service

1. Start Redis server if not already running:
```bash
redis-server
```

2. Start the Gateway service:
```bash
# Development mode
python main.py

# Or using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Running Tests

The Gateway service includes comprehensive tests for all major components. Here's how to run them:

1. Install test dependencies:
```bash
pip install pytest pytest-asyncio pytest-cov
```

2. Run all tests:
```bash
# Run tests with verbose output
pytest tests/ -v

# Run tests with coverage report
pytest tests/ --cov=. -v

# Run specific test file
pytest tests/test_websocket.py -v
```

### Test Structure

- `tests/test_websocket.py`: WebSocket connection and message handling tests
- `tests/test_redis_handlers.py`: Redis integration tests
- `tests/test_auth.py`: Authentication mechanism tests
- `tests/conftest.py`: Test configuration and fixtures

### Running Individual Test Components

```bash
# Test WebSocket functionality
pytest tests/test_websocket.py -v

# Test Redis handlers
pytest tests/test_redis_handlers.py -v

# Test authentication
pytest tests/test_auth.py -v
```

## WebSocket Client Example

Here's a simple example of how to connect to the Gateway service:

```python
import websockets
import asyncio
import json
import hashlib
import time

async def connect_gateway():
    # Generate token
    appid = "your_app_id"
    current_minute = int(time.time() // 60)
    raw_str = f"{appid}your-secret-key{current_minute}"
    token = hashlib.sha256(raw_str.encode()).hexdigest()[:10]
    
    # Connect to WebSocket
    uri = f"ws://localhost:8000/ws?appid={appid}&token={token}"
    
    async with websockets.connect(uri) as websocket:
        # Send agent judgement request
        message = {
            "type": "agent_judgement",
            "agent_ids": ["agent1", "agent2"],
            "data": {
                "user_input": "Your input here"
            }
        }
        await websocket.send(json.dumps(message))
        
        # Receive streaming responses
        while True:
            response = await websocket.recv()
            print(json.loads(response))

# Run the client
asyncio.run(connect_gateway())
```

## API Documentation

### WebSocket Endpoint

- URL: `/ws`
- Query Parameters:
  - `appid`: Application ID
  - `token`: Authentication token

### Message Types

1. Agent Judgement Request:
```json
{
    "type": "agent_judgement",
    "agent_ids": ["agent1", "agent2"],
    "data": {
        "user_input": "..."
    }
}
```

2. Stream Response:
```json
{
    "type": "agent_judgement_stream",
    "session_id": "...",
    "data": {
        "thinking": "..."
    }
}
```

3. Final Response:
```json
{
    "type": "agent_judgement_final",
    "session_id": "...",
    "result_code": 0,
    "data": {
        "judgement": "..."
    }
}
```

## Error Handling

The service will return error messages in the following format:

```json
{
    "error": "Error message description"
}
```

Common error scenarios:
- Authentication failure
- Invalid message format
- Unsupported message type
- Internal server error

## Development

When developing new features or fixing bugs:

1. Write tests first in the appropriate test file
2. Implement the feature/fix
3. Run the test suite to ensure everything works
4. Update documentation if needed

## Production Deployment

For production deployment:

1. Update the `.env` file with production settings
2. Use proper CORS_ORIGINS values
3. Change FIXED_SECRET to a secure value
4. Consider using a process manager like supervisord
5. Set up proper logging
6. Use HTTPS/WSS for secure communication 