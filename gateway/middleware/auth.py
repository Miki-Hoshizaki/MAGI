from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from ..config import settings

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = None) -> dict:
    """Verify JWT token"""
    if not credentials:
        raise HTTPException(status_code=403, detail="Token Error")
    
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token Expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid Token")

async def auth_middleware(request: Request, call_next):
    """Authentication middleware"""
    if request.url.path in ["/ws"]:  # WebSocket uses standalone authentication
        return await call_next(request)
        
    try:
        auth = await security(request)
        token_data = await verify_token(auth)
        request.state.user = token_data
    except HTTPException as e:
        if request.url.path.startswith("/api/public"):  # Public api doesn't need to be authenticated
            pass
        else:
            raise e
    
    response = await call_next(request)
    return response
