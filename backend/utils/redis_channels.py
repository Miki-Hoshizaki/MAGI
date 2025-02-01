"""
Redis channel definitions for communication between gateway and backend.
"""
from typing import Dict, Any

class RedisChannels:
    """
    Redis channel definitions for the MAGI system.
    All channels are defined as class attributes for consistency across the system.
    """
    # Gateway request queue for incoming user requests
    GATEWAY_REQUESTS = "gateway:requests"
    
    # Agent task streams template, will be formatted with session_id
    AGENT_TASKS_STREAM = "session:agents:tasks:{session_id}"
    
    # Results stream template, will be formatted with session_id
    RESULTS_STREAM = "session:results:{session_id}"
    
    @classmethod
    def agent_task_stream(cls, session_id: str) -> str:
        """
        Get the agent task stream name for a specific session.
        
        Args:
            session_id: The unique session identifier
            
        Returns:
            str: The formatted stream name
        """
        return cls.AGENT_TASKS_STREAM.format(session_id=session_id)
    
    @classmethod
    def result_stream(cls, session_id: str) -> str:
        """
        Get the result stream name for a specific session.
        
        Args:
            session_id: The unique session identifier
            
        Returns:
            str: The formatted stream name
        """
        return cls.RESULTS_STREAM.format(session_id=session_id)
