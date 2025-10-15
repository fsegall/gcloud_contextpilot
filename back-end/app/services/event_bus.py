"""
Event Bus Service - Pub/Sub Integration

Provides event-driven communication between agents.
Supports both GCP Pub/Sub (production) and in-memory (development).
"""

import os
import json
import logging
from typing import Dict, List, Callable, Optional, Any
from datetime import datetime
from abc import ABC, abstractmethod
import asyncio
from collections import defaultdict

logger = logging.getLogger(__name__)

# Event schema version
EVENT_SCHEMA_VERSION = "1.0.0"


class EventBusInterface(ABC):
    """Abstract interface for event bus implementations"""
    
    @abstractmethod
    async def publish(self, topic: str, event_type: str, source: str, data: Dict) -> str:
        """Publish event to topic"""
        pass
    
    @abstractmethod
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subscribe handler to event type"""
        pass
    
    @abstractmethod
    async def start_listening(self) -> None:
        """Start listening for events"""
        pass
    
    @abstractmethod
    async def stop_listening(self) -> None:
        """Stop listening for events"""
        pass


class InMemoryEventBus(EventBusInterface):
    """
    In-memory event bus for development/testing.
    Events are processed synchronously in the same process.
    """
    
    def __init__(self):
        self.subscriptions: Dict[str, List[Callable]] = defaultdict(list)
        self.event_log: List[Dict] = []
        self.listening = False
        logger.info("[InMemoryEventBus] Initialized (development mode)")
    
    async def publish(self, topic: str, event_type: str, source: str, data: Dict) -> str:
        """Publish event to in-memory subscribers"""
        event = {
            'event_id': f"evt-{len(self.event_log)}",
            'event_type': event_type,
            'source': source,
            'topic': topic,
            'data': data,
            'timestamp': datetime.utcnow().isoformat(),
            'schema_version': EVENT_SCHEMA_VERSION
        }
        
        # Log event
        self.event_log.append(event)
        logger.info(f"[EventBus] Published: {event_type} from {source} to {topic}")
        
        # Call subscribers immediately (in-memory)
        if event_type in self.subscriptions:
            for handler in self.subscriptions[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event_type, data)
                    else:
                        handler(event_type, data)
                except Exception as e:
                    logger.error(f"[EventBus] Handler error for {event_type}: {e}")
        
        return event['event_id']
    
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subscribe handler to event type"""
        self.subscriptions[event_type].append(handler)
        logger.info(f"[EventBus] Subscribed to {event_type} (total: {len(self.subscriptions[event_type])})")
    
    async def start_listening(self) -> None:
        """Start listening (no-op for in-memory)"""
        self.listening = True
        logger.info("[EventBus] Listening started (in-memory mode)")
    
    async def stop_listening(self) -> None:
        """Stop listening"""
        self.listening = False
        logger.info("[EventBus] Listening stopped")
    
    def get_event_log(self) -> List[Dict]:
        """Get all events (for debugging)"""
        return self.event_log
    
    def clear_log(self) -> None:
        """Clear event log"""
        self.event_log.clear()


class PubSubEventBus(EventBusInterface):
    """
    Google Cloud Pub/Sub event bus for production.
    Events are published to GCP Pub/Sub topics.
    """
    
    def __init__(self, project_id: str):
        try:
            from google.cloud import pubsub_v1
            self.publisher = pubsub_v1.PublisherClient()
            self.subscriber = pubsub_v1.SubscriberClient()
            self.project_id = project_id
            self.subscriptions: Dict[str, List[Callable]] = defaultdict(list)
            self.subscription_futures = []
            self.listening = False
            logger.info(f"[PubSubEventBus] Initialized for project: {project_id}")
        except ImportError:
            logger.error("[PubSubEventBus] google-cloud-pubsub not installed")
            raise
    
    async def publish(self, topic: str, event_type: str, source: str, data: Dict) -> str:
        """Publish event to Pub/Sub topic"""
        topic_path = self.publisher.topic_path(self.project_id, topic)
        
        event = {
            'event_type': event_type,
            'source': source,
            'data': data,
            'timestamp': datetime.utcnow().isoformat(),
            'schema_version': EVENT_SCHEMA_VERSION
        }
        
        # Publish to Pub/Sub
        message_bytes = json.dumps(event).encode('utf-8')
        future = self.publisher.publish(topic_path, message_bytes)
        message_id = future.result()  # Block until published
        
        logger.info(f"[PubSubEventBus] Published {event_type} to {topic} (msg_id: {message_id})")
        return message_id
    
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Register handler for event type (local registry)"""
        self.subscriptions[event_type].append(handler)
        logger.info(f"[PubSubEventBus] Registered handler for {event_type}")
    
    async def start_listening(self) -> None:
        """Start listening to Pub/Sub subscriptions"""
        self.listening = True
        
        # Create subscription for each topic we care about
        # For now, we'll use a single subscription per agent
        subscription_name = f"contextpilot-events-sub"
        subscription_path = self.subscriber.subscription_path(
            self.project_id, subscription_name
        )
        
        def callback(message):
            """Handle incoming Pub/Sub message"""
            try:
                event = json.loads(message.data.decode('utf-8'))
                event_type = event['event_type']
                data = event['data']
                
                logger.info(f"[PubSubEventBus] Received {event_type}")
                
                # Call registered handlers
                if event_type in self.subscriptions:
                    for handler in self.subscriptions[event_type]:
                        try:
                            if asyncio.iscoroutinefunction(handler):
                                asyncio.create_task(handler(event_type, data))
                            else:
                                handler(event_type, data)
                        except Exception as e:
                            logger.error(f"[PubSubEventBus] Handler error: {e}")
                
                message.ack()
            except Exception as e:
                logger.error(f"[PubSubEventBus] Message processing error: {e}")
                message.nack()
        
        # Start streaming pull
        future = self.subscriber.subscribe(subscription_path, callback)
        self.subscription_futures.append(future)
        
        logger.info(f"[PubSubEventBus] Listening on {subscription_path}")
    
    async def stop_listening(self) -> None:
        """Stop listening to Pub/Sub"""
        self.listening = False
        for future in self.subscription_futures:
            future.cancel()
        self.subscription_futures.clear()
        logger.info("[PubSubEventBus] Stopped listening")


# Global event bus instance
_event_bus: Optional[EventBusInterface] = None


def get_event_bus(project_id: Optional[str] = None, force_in_memory: bool = False) -> EventBusInterface:
    """
    Get or create event bus instance.
    
    Args:
        project_id: GCP project ID (for Pub/Sub)
        force_in_memory: Force in-memory bus even if GCP is available
    
    Returns:
        EventBus instance (Pub/Sub or in-memory)
    """
    global _event_bus
    
    if _event_bus is not None:
        return _event_bus
    
    # Determine which implementation to use
    use_pubsub = (
        not force_in_memory and
        project_id is not None and
        os.getenv('USE_PUBSUB', 'false').lower() == 'true'
    )
    
    if use_pubsub:
        try:
            _event_bus = PubSubEventBus(project_id)
            logger.info("[EventBus] Using Google Pub/Sub")
        except Exception as e:
            logger.warning(f"[EventBus] Pub/Sub init failed, falling back to in-memory: {e}")
            _event_bus = InMemoryEventBus()
    else:
        _event_bus = InMemoryEventBus()
        logger.info("[EventBus] Using in-memory event bus (development mode)")
    
    return _event_bus


def reset_event_bus():
    """Reset global event bus (for testing)"""
    global _event_bus
    _event_bus = None


# Event type constants (for type safety)
class EventTypes:
    """Standard event types used across the system"""
    
    # Git events
    GIT_COMMIT = "git.commit.v1"
    GIT_BRANCH_CREATED = "git.branch.created.v1"
    GIT_MERGE = "git.merge.v1"
    GIT_ROLLBACK = "git.rollback.v1"
    
    # Proposal events
    PROPOSAL_CREATED = "proposal.created.v1"
    PROPOSAL_APPROVED = "proposal.approved.v1"
    PROPOSAL_REJECTED = "proposal.rejected.v1"
    
    # Context events
    CONTEXT_UPDATE = "context.update.v1"
    CONTEXT_DELTA = "context.delta.v1"
    CONTEXT_CHECKPOINT = "context.checkpoint.v1"
    
    # Spec events
    SPEC_UPDATE = "spec.update.v1"
    SPEC_VALIDATION = "spec.validation.v1"
    SPEC_REQUEST = "spec.request.v1"
    
    # Strategy events
    STRATEGY_INSIGHT = "strategy.insight.v1"
    STRATEGY_OPTIONS = "strategy.options.v1"
    STRATEGY_UPDATED = "strategy.updated.v1"
    STRATEGY_ANALYZE = "strategy.analyze.v1"
    
    # Milestone events
    MILESTONE_CREATE = "milestone.create.v1"
    MILESTONE_COMPLETE = "milestone.complete.v1"
    MILESTONE_SAVED = "milestone.saved.v1"
    MILESTONE_ALERT = "milestone.alert.v1"
    MILESTONE_BLOCKED = "milestone.blocked.v1"
    
    # Coach events
    COACH_NUDGE = "coach.nudge.v1"
    COACH_UNBLOCK = "coach.unblock.v1"
    COACH_CHECKIN = "coach.checkin.v1"
    COACH_SUGGEST_DOC = "coach.suggest.doc.v1"
    
    # Retrospective events
    RETROSPECTIVE_TRIGGER = "retrospective.trigger.v1"
    RETROSPECTIVE_ACTION_ITEM = "retrospective.action_item.v1"
    
    # Artifact events
    ARTIFACT_CREATED = "artifact.created.v1"
    ARTIFACT_UPDATED = "artifact.updated.v1"
    
    # Reward events
    REWARDS_SPEC_COMMIT = "rewards.spec_commit.v1"


# Topic constants
class Topics:
    """Pub/Sub topic names"""
    
    GIT_EVENTS = "git-events"
    PROPOSAL_EVENTS = "proposal-events"
    CONTEXT_EVENTS = "context-events"
    SPEC_EVENTS = "spec-events"
    STRATEGY_EVENTS = "strategy-events"
    MILESTONE_EVENTS = "milestone-events"
    COACH_EVENTS = "coach-events"
    RETROSPECTIVE_EVENTS = "retrospective-events"
    ARTIFACT_EVENTS = "artifact-events"
    REWARD_EVENTS = "reward-events"


# Helper function for event validation
def validate_event_data(event_type: str, data: Dict) -> bool:
    """
    Validate event data structure.
    
    Args:
        event_type: Event type to validate
        data: Event data payload
    
    Returns:
        True if valid, False otherwise
    """
    # Basic validation - ensure data is a dict
    if not isinstance(data, dict):
        logger.error(f"[EventBus] Invalid event data for {event_type}: not a dict")
        return False
    
    # Event-specific validation can be added here
    # For now, just check for required fields based on event type
    
    if event_type == EventTypes.PROPOSAL_CREATED:
        required = ['proposal_id', 'workspace_id']
        if not all(k in data for k in required):
            logger.error(f"[EventBus] Missing required fields for {event_type}: {required}")
            return False
    
    elif event_type == EventTypes.GIT_COMMIT:
        required = ['commit_hash', 'workspace_id']
        if not all(k in data for k in required):
            logger.error(f"[EventBus] Missing required fields for {event_type}: {required}")
            return False
    
    # Add more validation as needed
    
    return True
