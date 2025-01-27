# MAGI System

MAGI System is a system for asynchronous discrimination and voting tasks. Its main objective is to evaluate and judge results generated by external agents (such as CodeGen, third-party platform content generation models) and provide voting results.

## System Architecture

The project adopts a front-end and back-end separated microservice architecture, including the following main components:

- Frontend (Next.js)
- Business Backend (Django)
- WebSocket Gateway (FastAPI)
- Message Queue (Redis)
- Database (PostgreSQL)

For detailed architecture design, please refer to [Docs](https://magisystem.gitbook.io/magi-system)

## Development Environment Requirements

- Docker & Docker Compose
- Node.js 20+
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

## Quick Start

1. Clone repository
```bash
git clone <repository-url>
cd magisys
```

2. Start development environment
```bash
docker-compose up -d
```

3. Access services
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001
- WebSocket Gateway: ws://localhost:8000

## Project Structure
```
magisys/
├── frontend/           # Next.js Frontend
├── backend/           # Django Business Backend
├── gateway/           # FastAPI WebSocket Gateway
├── docker-compose.yml # Container Orchestration Configuration
├── README.md          # Project Documentation
└── RFC.md            # Design Documentation
```

## Development Guide

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Gateway Development
```bash
cd gateway
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## Testing

Each component contains its own test suite:

- Frontend: `npm test`
- Backend: `python manage.py test`
- Gateway: `pytest`

## Deployment

The project uses Docker for deployment. Please refer to the deployment documentation in each component directory for detailed deployment guides.

## Contribution Guidelines

1. Fork the project
2. Create a feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## License

[MIT License](LICENSE)
