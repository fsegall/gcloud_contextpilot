"""
Event Bus service using Google Cloud Pub/Sub.

Provides a simple interface for agents to publish and subscribe to events.
"""
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, Callable
from google.cloud import pubsub_v1

logger = logging.getLogger(__name__)


class EventBus:
    """
    Event Bus wrapper for Google Cloud Pub/Sub.
    
    Provides:
    - Standard event envelope
    - Event publishing
    - Event routing to handlers
    - Error handling and retries
    """
    
    def __init__(self, project_id: str):
        """
        Initialize Event Bus.
        
        Args:
            project_id: GCP project ID
        """
        self.project_id = project_id
        self.publisher = pubsub_v1.PublisherClient()
        self.subscriber = pubsub_v1.SubscriberClient()
        
        logger.info(f"EventBus initialized for project: {project_id}")
    
    def publish(
        self,
        topic: str,
        event_type: str,
        data: Dict,
        source: str,
        attributes: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Publish event to Pub/Sub topic.
        
        Args:
            topic: Topic name (e.g., 'context-updates')
            event_type: Event type (e.g., 'context.update.v1')
            data: Event payload
            source: Agent that created event (e.g., 'context-agent')
            attributes: Optional message attributes for filtering
            
        Returns:
            Message ID from Pub/Sub
        """
        topic_path = self.publisher.topic_path(self.project_id, topic)
        
        # Create standard event envelope
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": source,
            "data": data
        }
        
        # Message attributes (for filtering)
        attrs = attributes or {}
        attrs["event_type"] = event_type
        attrs["source"] = source
        
        # Publish
        message_json = json.dumps(event)
        future = self.publisher.publish(
            topic_path,
            data=message_json.encode("utf-8"),
            **attrs
        )
        
        message_id = future.result(timeout=10)
        
        logger.info(
            f"Published {event_type} to {topic}: "
            f"message_id={message_id}, event_id={event['event_id']}"
        )
        
        return message_id
    
    def publish_batch(
        self,
        topic: str,
        events: list[Dict]
    ) -> list[str]:
        """
        Publish multiple events in batch (more efficient).
        
        Args:
            topic: Topic name
            events: List of events to publish (each with type, data, source)
            
        Returns:
            List of message IDs
        """
        topic_path = self.publisher.topic_path(self.project_id, topic)
        futures = []
        
        for event_info in events:
            event = {
                "event_id": str(uuid.uuid4()),
                "event_type": event_info["type"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": event_info["source"],
                "data": event_info["data"]
            }
            
            message_json = json.dumps(event)
            future = self.publisher.publish(
                topic_path,
                data=message_json.encode("utf-8"),
                event_type=event_info["type"],
                source=event_info["source"]
            )
            futures.append(future)
        
        # Wait for all
        message_ids = [f.result(timeout=10) for f in futures]
        
        logger.info(f"Published {len(message_ids)} events to {topic}")
        
        return message_ids
    
    def subscribe(
        self,
        subscription: str,
        callback: Callable[[Dict], None],
        max_messages: int = 10
    ):
        """
        Subscribe to messages (pull mode).
        
        Use this for batch processing or background jobs.
        
        Args:
            subscription: Subscription name
            callback: Function to call for each message
            max_messages: Max messages to pull at once
        """
        subscription_path = self.subscriber.subscription_path(
            self.project_id,
            subscription
        )
        
        def message_callback(message: pubsub_v1.subscriber.message.Message):
            try:
                # Decode event
                event = json.loads(message.data.decode("utf-8"))
                
                # Call handler
                callback(event)
                
                # Acknowledge
                message.ack()
                
                logger.debug(f"Processed event: {event['event_id']}")
                
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                # Nack to retry
                message.nack()
        
        # Start streaming pull
        streaming_pull_future = self.subscriber.subscribe(
            subscription_path,
            callback=message_callback
        )
        
        logger.info(f"Listening on subscription: {subscription}")
        
        try:
            # Block until shutdown
            streaming_pull_future.result()
        except KeyboardInterrupt:
            streaming_pull_future.cancel()
            streaming_pull_future.result()


# Singleton instance
_event_bus_instance: Optional[EventBus] = None


def get_event_bus(project_id: str = None) -> EventBus:
    """
    Get or create EventBus singleton.
    
    Args:
        project_id: GCP project ID (required on first call)
        
    Returns:
        EventBus instance
    """
    global _event_bus_instance
    
    if _event_bus_instance is None:
        if project_id is None:
            raise ValueError("project_id required on first call")
        _event_bus_instance = EventBus(project_id)
    
    return _event_bus_instance

