import asyncio
import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol

# Configure logger for this module
logger = logging.getLogger(__name__)


class EventTypes(str, Enum):
    """Canonical event type identifiers used across agents."""

    PROPOSAL_CREATED = "proposal.created.v1"
    PROPOSAL_APPROVED = "proposal.approved.v1"
    PROPOSAL_REJECTED = "proposal.rejected.v1"
    RETROSPECTIVE_SUMMARY = "retrospective.summary.v1"
    MILESTONE_COMPLETE = "milestone.complete.v1"
    GIT_COMMIT = "git.commit.v1"
    AGENT_METRICS_RESET = "agents.metrics.reset"

    # Examples / backwards-compatible aliases
    MY_EVENT = "custom.my_event"
    MY_RESPONSE = "custom.my_response"


class Topics(str, Enum):
    """Pub/Sub style topics used by the event bus."""

    PROPOSAL_EVENTS = "proposals-events"
    PROPOSALS_EVENTS = PROPOSAL_EVENTS  # alias used in docs/tests
    RETROSPECTIVE_EVENTS = "retrospective-events"
    GIT_EVENTS = "git-events"
    AGENT_EVENTS = "agent-events"
    METRICS_EVENTS = "metrics-events"
    MY_TOPIC = "custom.my_topic"


class EventBusInterface(Protocol):
    def subscribe(self, event_type: str, handler: Callable[[str, Dict[str, Any]], Any]) -> None:
        ...

    def unsubscribe(self, event_type: str, handler: Callable[[str, Dict[str, Any]], Any]) -> None:
        ...

    async def publish(
        self,
        *,
        topic: str,
        event_type: str,
        source: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        ...

    def get_event_log(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        ...

    def reset(self) -> None:
        ...


class InMemoryEventBus(EventBusInterface):
    """Simple in-memory event bus for development and local testing."""

    def __init__(self, max_log_size: int = 500) -> None:
        self._subscribers: Dict[str, List[Callable[[str, Dict[str, Any]], Any]]] = defaultdict(list)
        self._event_log: List[Dict[str, Any]] = []
        self._max_log_size = max_log_size
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Subscription management
    # ------------------------------------------------------------------
    def subscribe(self, event_type: str, handler: Callable[[str, Dict[str, Any]], Any]) -> None:
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)
            logger.debug("Subscribed handler %s to %s", getattr(handler, "__name__", handler), event_type)

    def unsubscribe(self, event_type: str, handler: Callable[[str, Dict[str, Any]], Any]) -> None:
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)
            logger.debug("Unsubscribed handler %s from %s", getattr(handler, "__name__", handler), event_type)

    # ------------------------------------------------------------------
    # Publish
    # ------------------------------------------------------------------
    async def publish(
        self,
        *,
        topic: str,
        event_type: str,
        source: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        event_id = f"evt-{uuid.uuid4().hex}"
        event_payload = {
            "event_id": event_id,
            "topic": topic,
            "event_type": event_type,
            "source": source,
            "data": data,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        async with self._lock:
            self._event_log.append(event_payload)
            if len(self._event_log) > self._max_log_size:
                self._event_log = self._event_log[-self._max_log_size :]

        handlers = list(self._subscribers.get(event_type, []))
        if not handlers:
            logger.debug("No subscribers for event %s", event_type)
            return event_id

        async def _execute_handler(handler: Callable[[str, Dict[str, Any]], Any]) -> None:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_type, data)
                else:
                    await asyncio.to_thread(handler, event_type, data)
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.error(
                    "Error delivering event %s to handler %s: %s",
                    event_type,
                    getattr(handler, "__name__", handler),
                    exc,
                    exc_info=True,
                )

        await asyncio.gather(*[_execute_handler(handler) for handler in handlers], return_exceptions=True)
        return event_id

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def get_event_log(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        if limit is None or limit >= len(self._event_log):
            return list(self._event_log)
        return self._event_log[-limit:]

    def reset(self) -> None:
        self._subscribers.clear()
        self._event_log.clear()


_event_bus_instance: Optional[InMemoryEventBus] = None


def get_event_bus(
    project_id: Optional[str] = None,
    force_in_memory: bool = False,
    agent_id: Optional[str] = None,
    **_: Any,
) -> EventBusInterface:
    """Return the singleton event bus instance."""

    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = InMemoryEventBus()
        logger.info("In-memory EventBus initialized (project_id=%s, in_memory=%s)", project_id, force_in_memory)

    if agent_id:
        logger.debug("EventBus requested by %s", agent_id)

    return _event_bus_instance


def reset_event_bus() -> None:
    global _event_bus_instance
    if _event_bus_instance is not None:
        _event_bus_instance.reset()
        _event_bus_instance = None
        logger.info("EventBus reset")
