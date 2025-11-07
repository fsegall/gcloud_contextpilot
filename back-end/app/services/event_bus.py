import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Callable, Any, Dict, List
from dataclasses import dataclass, field

# Configure logger for this module
logger = logging.getLogger(__name__)


@dataclass
class Event:
    """
    Base class for all events in the system.

    Events are immutable data structures that represent something that has
    occurred in the system. They are dispatched via the EventBus to interested
    subscribers.

    Attributes:
        event_type (str): A string identifying the type of event (e.g., "AGENT_STATUS_UPDATE", "TASK_COMPLETED").
        payload (Dict[str, Any]): A dictionary containing event-specific data.
        timestamp (str): ISO formatted UTC timestamp when the event was created.
    """
    event_type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        """Ensures event_type is not empty after initialization."""
        if not self.event_type:
            raise ValueError("Event type cannot be empty.")

    def __str__(self):
        """Provides a human-readable representation of the event."""
        return f"Event(type='{self.event_type}', timestamp='{self.timestamp}', payload={self.payload})"


class EventBus:
    """
    An asynchronous in-memory event bus for dispatching events to subscribed handlers.

    This bus facilitates communication between different components (e.g., agents, services)
    by allowing them to publish and subscribe to specific event types. Handlers are
    executed asynchronously to prevent blocking the publisher.

    It is implemented as an async singleton to ensure a single, globally accessible
    instance across the application that can be initialized asynchronously.
    """
    _instance = None
    _lock = asyncio.Lock()  # Protects _instance creation and shared state

    def __new__(cls):
        """
        Ensures only one instance of EventBus is created (singleton pattern).
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False  # Flag to track async initialization status
        return cls._instance

    async def initialize(self):
        """
        Initializes the event bus's internal state. This method should be awaited
        once at application startup to set up the bus properly.
        """
        async with self._lock:
            if not self._initialized:
                self._subscribers: Dict[str, List[Callable[[Event], Any]]] = defaultdict(list)
                self._initialized = True
                logger.info("EventBus initialized successfully.")

    async def subscribe(self, event_type: str, handler: Callable[[Event], Any]):
        """
        Subscribes a handler function to a specific event type.

        The handler function will be called with an `Event` object when an event
        of the specified type is published. It can be a regular synchronous function
        or an asynchronous coroutine function.

        Args:
            event_type (str): The type of event to subscribe to.
            handler (Callable[[Event], Any]): The function to call when the event occurs.
        """
        if not self._initialized:
            logger.warning(
                f"EventBus not initialized. Attempting to initialize before subscribing "
                f"handler '{handler.__name__}' to '{event_type}'."
            )
            await self.initialize()  # Attempt to initialize if not already

        async with self._lock:
            if handler not in self._subscribers[event_type]:
                self._subscribers[event_type].append(handler)
                logger.debug(f"Handler '{handler.__name__}' subscribed to event type '{event_type}'.")
            else:
                logger.warning(f"Handler '{handler.__name__}' is already subscribed to event type '{event_type}'.")

    async def unsubscribe(self, event_type: str, handler: Callable[[Event], Any]):
        """
        Unsubscribes a handler function from a specific event type.

        Args:
            event_type (str): The type of event to unsubscribe from.
            handler (Callable[[Event], Any]): The handler function to remove.
        """
        if not self._initialized:
            logger.warning("Attempted to unsubscribe from an uninitialized EventBus. No action taken.")
            return

        async with self._lock:
            if handler in self._subscribers[event_type]:
                self._subscribers[event_type].remove(handler)
                logger.debug(f"Handler '{handler.__name__}' unsubscribed from event type '{event_type}'.")
            else:
                logger.warning(
                    f"Handler '{handler.__name__}' not found for event type '{event_type}'. "
                    f"No action taken during unsubscribe."
                )

    async def publish(self, event: Event):
        """
        Publishes an event to the bus.

        This method dispatches the event to all currently subscribed handlers for
        its `event_type`. Each handler is executed as a separate `asyncio.Task`,
        ensuring that the publishing operation is non-blocking.

        Args:
            event (Event): The event object to publish.
        """
        if not self._initialized:
            logger.error(f"Attempted to publish event '{event.event_type}' to an uninitialized EventBus. Event dropped.")
            return

        logger.info(f"Publishing event: {event}")
        handlers_to_dispatch = []
        async with self._lock:
            # Get a copy of the handlers list to prevent issues if subscribers modify it
            # during iteration (e.g., unsubscribe themselves).
            handlers_to_dispatch = list(self._subscribers[event.event_type])

        if not handlers_to_dispatch:
            logger.debug(f"No handlers subscribed for event type '{event.event_type}'. Event not dispatched.")
            return

        for handler in handlers_to_dispatch:
            # Create a task for each handler to run concurrently without blocking the publisher
            asyncio.create_task(self._dispatch_event_to_handler(event, handler))

    async def _dispatch_event_to_handler(self, event: Event, handler: Callable[[Event], Any]):
        """
        Internal method to safely call a single handler with an event.

        This method handles both synchronous and asynchronous handler functions
        and catches any exceptions raised by the handler to prevent them from
        crashing the event bus or other handlers.

        Args:
            event (Event): The event object to pass to the handler.
            handler (Callable[[Event], Any]): The handler function to execute.
        """
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                # Run synchronous handlers in a thread pool to avoid blocking the event loop.
                # This is crucial for long-running synchronous operations in an async application.
                await asyncio.to_thread(handler, event)
            logger.debug(f"Event '{event.event_type}' successfully dispatched to handler '{handler.__name__}'.")
        except Exception as e:
            logger.error(
                f"Error dispatching event '{event.event_type}' to handler '{handler.__name__}': {e}",
                exc_info=True  # Log full traceback for debugging
            )


# Global instance for easy access throughout the application.
# Components can import `event_bus` and use it directly after it has been initialized
# at the application's startup.
event_bus = EventBus()