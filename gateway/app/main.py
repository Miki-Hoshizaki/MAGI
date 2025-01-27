from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from typing import Dict, List
import jwt
import aioredis
import json
from datetime import datetime

app = FastAPI(title="Magi Gateway", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis connection
redis = aioredis.from_url("redis://redis:6379", encoding="utf-8", decode_responses=True)

# JWT configuration
JWT_SECRET = "your-secret-key"  # Move to environment variables
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await connection.send_text(message)

    async def broadcast(self, message: str):
        for connections in self.active_connections.values():
            for connection in connections:
                await connection.send_text(message)

manager = ConnectionManager()

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        return user_id
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    try:
        # Verify the token from the query parameters
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=4001, reason="Authentication required")
            return

        try:
            user_id = await get_current_user(token)
        except HTTPException:
            await websocket.close(code=4001, reason="Invalid token")
            return

        await manager.connect(websocket, user_id)
        
        try:
            while True:
                data = await websocket.receive_text()
                message = {
                    "client_id": client_id,
                    "user_id": user_id,
                    "message": data,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Store message in Redis
                await redis.lpush(
                    f"messages:{user_id}", 
                    json.dumps(message)
                )
                
                # Broadcast to all connected clients
                await manager.broadcast(json.dumps(message))
                
        except WebSocketDisconnect:
            manager.disconnect(websocket, user_id)
            message = {
                "client_id": client_id,
                "user_id": user_id,
                "message": "left the chat",
                "timestamp": datetime.utcnow().isoformat()
            }
            await manager.broadcast(json.dumps(message))
            
    except Exception as e:
        print(f"Error: {str(e)}")
        await websocket.close(code=1011, reason="Internal server error")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()} 