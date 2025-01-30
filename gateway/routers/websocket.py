from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import json
import logging
from ..utils.auth import verify_appid_token, generate_session_id
from ..websocket_manager import ConnectionManager

logger = logging.getLogger(__name__)
router = APIRouter()
manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    appid: str = Query(...),
    token: str = Query(...)
):
    """WebSocket endpoint with appid + token authentication"""
    
    # Verify appid and token
    if not verify_appid_token(appid, token):
        logger.warning(f"Authentication failed for appid: {appid}")
        await websocket.close(code=1008)  # Policy Violation
        return
    
    # Generate session ID for this connection
    session_id = generate_session_id(appid)
    
    # Accept connection
    await manager.connect(session_id, websocket)
    logger.info(f"New WebSocket connection: {session_id}")
    
    try:
        while True:
            try:
                # Receive and parse message
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle message
                await manager.handle_message(session_id, message)
            
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from {session_id}")
                await manager.send_message(session_id, {
                    "error": "Invalid JSON format"
                })
            
            except Exception as e:
                logger.error(f"Error processing message from {session_id}: {str(e)}")
                await manager.send_message(session_id, {
                    "error": "Internal server error"
                })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
        manager.disconnect(session_id)
    
    except Exception as e:
        logger.error(f"Unexpected error for {session_id}: {str(e)}")
        manager.disconnect(session_id)
