from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import json
import logging
from utils.auth import verify_appid_token, generate_session_id
from app_state import manager
from redis_handlers.producer import send_to_redis

logger = logging.getLogger(__name__)
router = APIRouter()

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
        await websocket.close(code=4001, reason="Invalid credentials")
        return
    
    # Generate session ID for this connection
    session_id = generate_session_id(appid)
    
    try:
        # Accept connection
        await manager.connect(session_id, websocket)
        logger.info(f"New WebSocket connection: {session_id}")
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "session_id": session_id
        })

        while True:
            try:
                # Receive message
                raw_data = await websocket.receive_text()
                
                try:
                    data = json.loads(raw_data)
                except json.JSONDecodeError:
                    await websocket.send_json({
                        "error": "Invalid JSON format"
                    })
                    continue

                # Handle ping message
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    continue

                # Handle other message types
                message_type = data.get("type")
                if message_type not in ("get_voters", "agent_judgement"):
                    await websocket.send_json({
                        "error": "Unsupported message type"
                    })
                    continue

                # Add session_id to message
                data["session_id"] = session_id
                
                # Send to Redis for processing
                await send_to_redis(data)
                await websocket.send_json({
                    "type": "message_received",
                    "message_type": message_type
                })

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: {session_id}")
                break
            except Exception as e:
                logger.error(f"Error processing message from {session_id}: {str(e)}")
                await websocket.send_json({
                    "error": f"Error processing message: {str(e)}"
                })

    except Exception as e:
        logger.error(f"WebSocket error for {session_id}: {str(e)}")
    finally:
        await manager.disconnect(session_id)
