# Eliza Service

This is a web service that implements an OpenAI-compatible chat completions API endpoint with streaming results. It uses the Magi framework to process code generation requests and provides real-time updates through a web interface.

## Features

- OpenAI API compatible endpoint (`/v1/chat/completions`)
- Real-time streaming of code generation progress
- Beautiful web interface for viewing results
- Asynchronous task processing with Celery
- Server-Sent Events (SSE) for live updates

## Prerequisites

- Python 3.8+
- Redis server (for Celery)
- Magi framework installed

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start Redis server:
```bash
redis-server
```

3. Start Celery worker:
```bash
celery -A celery_app worker --loglevel=info
```

4. Start the FastAPI server:
```bash
python app.py
```

The service will be available at `http://localhost:8000`.

## API Usage

### Using curl

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {
        "role": "user",
        "content": "Create a Python function that implements bubble sort"
      }
    ]
  }'
```

### Using the test client

Run the provided test client:
```bash
python client_test.py
```

This will:
1. Send a sample code generation request
2. Open the result page in your default browser
3. Show real-time updates of the code generation process

## API Endpoints

- `POST /v1/chat/completions`: Submit a code generation request
- `GET /v1/results/{task_id}`: Stream results for a specific task
- `GET /v1/status/{task_id}`: Get task status

## Directory Structure

```
eliza_service/
├── app.py              # FastAPI application
├── celery_app.py       # Celery task definitions
├── templates/          # HTML templates
│   └── result.html     # Result page template
├── static/             # Static files
│   └── style.css       # CSS styles
├── results/            # Generated result files
├── requirements.txt    # Project dependencies
└── README.md          # This file
```

## Development

To modify the service:
1. Edit `app.py` for API endpoints and routing
2. Edit `celery_app.py` for task processing logic
3. Edit templates in `templates/` for UI changes
4. Edit `static/style.css` for styling changes

## Security Notes

- Uses UUID v4 for task IDs
- Implements rate limiting
- Cleans up old result files
- Validates input through Pydantic models
