# Gateway Communication Protocol

This document describes the communication protocols used in the Gateway service for both client-gateway WebSocket communication and backend-gateway Redis-based communication.

## Client-Gateway WebSocket Protocol

### Connection Establishment

1. Clients connect to the WebSocket endpoint with a session ID
2. Gateway accepts the connection and maintains the session

### Message Format

All messages are JSON objects with the following base structure:

```json
{
    "type": "message_type",
    "session_id": "unique_session_id",
    // Additional fields based on message type
}
```

### Client to Gateway Messages

#### Agent Judgement Request
```json
{
    "type": "agent_judgement",
    "agent_ids": ["agent_id1", "agent_id2", ...],
    "session_id": "unique_session_id"
}
```

#### Unregister Request (Reserved)
```json
{
    "type": "unregister",
    "session_id": "unique_session_id"
}
```

### Gateway to Client Messages

#### Error Response
```json
{
    "error": "error_message"
}
```

#### Agent Judgement Response
```json
{
    "type": "agent_judgement_stream",
    // Additional fields from backend
}
```

```json
{
    "type": "agent_judgement_final",
    // Final result fields from backend
}
```

### Error Handling

1. Missing message type
2. Missing required fields
3. Unsupported message type
4. Internal server errors

## Backend-Gateway Redis Protocol

### Queue Structure

The Gateway service uses Redis queues for communication with backend services:

- `queue_agent_judgement_stream`: For streaming updates
- `queue_agent_judgement_final`: For final results

### Message Format

Messages in Redis queues follow the same JSON structure as WebSocket messages:

```json
{
    "type": "message_type",
    "session_id": "unique_session_id",
    // Additional fields based on message type
}
```

### Message Flow

1. Client sends request via WebSocket
2. Gateway forwards request to appropriate Redis queue
3. Backend processes request and sends responses to Redis queues
4. Gateway consumes messages from Redis queues and forwards to appropriate client

### Error Handling

1. Invalid JSON messages
2. Missing session ID
3. Redis connection issues
4. Message processing errors

## Implementation Notes

- All messages are JSON encoded
- Redis connections use UTF-8 encoding with decoded responses
- WebSocket connections are managed per session
- Redis consumer runs in background, monitoring multiple queues
- Automatic reconnection and error recovery mechanisms are in place 