import time
import hashlib
from typing import Optional
from config import settings

def verify_appid_token(appid: str, token: str) -> bool:
    """Verify token for appid"""
    if not appid or not token:
        return False
        
    current_minute = int(time.time() // 60)
    # Check current minute and previous minute
    for minute in [current_minute, current_minute - 1]:
        raw_str = f"{appid}{settings.FIXED_SECRET}{minute}"
        expected_token = hashlib.sha256(raw_str.encode()).hexdigest()[:10]
        if token == expected_token:
            return True
    return False

def generate_session_id(appid: str) -> str:
    """Generate a unique session ID for a connection"""
    timestamp = int(time.time())
    random_suffix = hashlib.md5(f"{timestamp}{appid}".encode()).hexdigest()[:6]
    return f"session-{appid}-{timestamp}-{random_suffix}" 