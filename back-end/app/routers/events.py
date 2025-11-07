"""
Event handling endpoints for Pub/Sub push subscriptions.

Each agent has an /events endpoint that receives Pub/Sub messages.
"""
from fastapi import APIRouter, Request, HTTPException
import base64
import json
import logging
from typing import Dict
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["events"])


@router.post("")
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
        
        # Get attributes (fallback to payload if attributes missing)
        attributes = pubsub_message.get("attributes", {}) if isinstance(pubsub_message, dict) else {}
        event_type = attributes.get("event_type") if attributes else None
        source = attributes.get("source") if attributes else None

        if not event_type:
            event_type = event.get("event_type") or event.get("type")

        if not source:
            source = event.get("source")
        
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
    Route event to appropriate agents based on event type.
    
    This initializes agents and calls their handle_event methods
    for agents that have subscribed to this event type.
    """
    from app.agents.agent_orchestrator import AgentOrchestrator
    from app.utils.workspace_manager import get_workspace_path
    
    # Extract workspace_id from event data
    workspace_id = event.get("data", {}).get("workspace_id", "default")
    if not workspace_id:
        workspace_id = "default"
    
    logger.info(f"[route_event] Routing {event_type} to agents in workspace: {workspace_id}")
    
    try:
        # Get workspace path
        workspace_path = get_workspace_path(workspace_id)
        
        # Initialize orchestrator
        orchestrator = AgentOrchestrator(
            workspace_id=workspace_id,
            workspace_path=str(workspace_path)
        )
        
        # Initialize all agents
        orchestrator.initialize_agents()
        
        # Route event to all agents that have subscribed to this event type
        event_data = event.get("data", {})
        
        processed_count = 0
        for agent_id, agent in orchestrator.agents.items():
            try:
                # Check if agent has explicitly subscribed to this event type
                if hasattr(agent, "subscribed_events"):
                    if not event_type or event_type not in agent.subscribed_events:
                        logger.debug(
                            f"[route_event] Agent {agent_id} not subscribed to {event_type}, skipping"
                        )
                        continue
                    logger.info(
                        f"[route_event] Agent {agent_id} subscribed to {event_type}, routing event"
                    )
                elif not hasattr(agent, "handle_event"):
                    logger.warning(
                        f"[route_event] Agent {agent_id} does not have handle_event method"
                    )
                    continue
                
                # Call handle_event on the agent
                if hasattr(agent, "handle_event"):
                    logger.info(f"[route_event] Calling handle_event on {agent_id} for {event_type}")
                    await agent.handle_event(event_type, event_data)
                    processed_count += 1
            except Exception as e:
                logger.error(f"[route_event] Error routing {event_type} to {agent_id}: {e}", exc_info=True)
                # Continue processing other agents even if one fails
        
        logger.info(f"[route_event] Routed {event_type} to {processed_count} agent(s)")
        
        # Cleanup
        orchestrator.shutdown_agents()
        
    except Exception as e:
        logger.error(f"[route_event] Error routing event {event_type}: {e}", exc_info=True)
        # Don't raise - we want to acknowledge the message even if routing fails


@router.get("/health")
async def health_check():
    """Health check for event handler service."""
    return {
        "status": "healthy",
        "service": "event-handler",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

