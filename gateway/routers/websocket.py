from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional
import json
import jwt
from ..config import settings
from ..services.websocket_manager import WebSocketManager

router = APIRouter()
manager = WebSocketManager()

async def get_token_data(token: str = Query(...)) -> dict:
    """Get and verify token from query parameters"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token_data: Optional[dict] = Depends(get_token_data)
):
    if not token_data:
        await websocket.close(code=1008)  # Policy Violation
        return
    
    # Use user ID as client identifier
    client_id = token_data.get("sub")
    
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                # Handle message
                await manager.handle_message(client_id, message)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "error": "Invalid JSON format"
                }))
    except WebSocketDisconnect:
        await manager.disconnect(client_id)
