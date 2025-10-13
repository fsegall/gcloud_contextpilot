"""
Event handling endpoints for Pub/Sub push subscriptions.

Each agent has an /events endpoint that receives Pub/Sub messages.
"""
from fastapi import APIRouter, Request, HTTPException
import base64
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/")
async def receive_event(request: Request):
    """
    Receive Pub/Sub push message.
    
    Pub/Sub sends messages in this format:
    {
      "message": {
        "data": "base64-encoded-json",
        "attributes": {"event_type": "...", "source": "..."},
        "messageId": "...",
        "publishTime": "..."
      },
      "subscription": "projects/.../subscriptions/..."
    }
    """
    try:
        envelope = await request.json()
        
        # Extract Pub/Sub message
        pubsub_message = envelope.get("message")
        if not pubsub_message:
            raise HTTPException(status_code=400, detail="Invalid Pub/Sub message")
        
        # Decode data
        data_bytes = base64.b64decode(pubsub_message["data"])
        event = json.loads(data_bytes)
        
        # Get attributes
        attributes = pubsub_message.get("attributes", {})
        event_type = attributes.get("event_type")
        source = attributes.get("source")
        
        logger.info(
            f"Received event: type={event_type}, source={source}, "
            f"id={event.get('event_id')}"
        )
        
        # Route to appropriate handler
        await route_event(event_type, event)
        
        # Acknowledge (return 200)
        return {"status": "ok", "event_id": event.get("event_id")}
        
    except Exception as e:
        logger.error(f"Error processing event: {e}")
        # Return 200 to avoid retries for malformed messages
        return {"status": "error", "error": str(e)}


async def route_event(event_type: str, event: Dict):
    """
    Route event to appropriate handler based on event type.
    
    This is where agents react to events from other agents.
    """
    
    # Import handlers
    from app.agents.spec_agent import handle_context_update as spec_context_handler
    from app.agents.strategy_agent import handle_context_update as strategy_context_handler
    from app.agents.git_agent import GitAgent
    
    handlers = {
        # Context updates
        "context.update.v1": [
            spec_context_handler,
            strategy_context_handler
        ],
        
        # Proposal approved
        "proposal.approved.v1": [
            # Git Agent will handle this
        ],
        
        # Git commits
        "git.commit.v1": [
            # Spec Agent updates CHANGELOG
            # Rewards Engine tracks action
        ],
    }
    
    handler_list = handlers.get(event_type, [])
    
    if not handler_list:
        logger.warning(f"No handler registered for event type: {event_type}")
        return
    
    # Call all handlers
    for handler in handler_list:
        try:
            await handler(event)
        except Exception as e:
            logger.error(f"Handler error for {event_type}: {e}")


@router.get("/health")
async def health_check():
    """Health check for event handler service."""
    return {
        "status": "healthy",
        "service": "event-handler",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

