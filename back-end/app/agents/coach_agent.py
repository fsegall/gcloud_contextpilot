import logging
from typing import Dict, Any

# Assuming these modules exist based on project context (multi-agent, Cloud Run, Pub/Sub, Firestore, Gemini)
# and common patterns for a Python project structure.
from contextpilot.core.base_agent import BaseAgent
from contextpilot.utils.pubsub_manager import PubSubManager
from contextpilot.utils.firestore_manager import FirestoreManager
from contextpilot.utils.gemini_client import GeminiClient

# Assuming a central module for defining event types and agent names for consistency
from contextpilot.core.event_types import (
    AGENT_ERROR_EVENT,
    AGENT_IDLE_EVENT,
    AGENT_STATUS_UPDATE_EVENT,
    RETROSPECTIVE_SUMMARY_EVENT,
    AGENT_ACTION_REQUEST_EVENT,  # Event for one agent to request action from another
    AGENT_FEEDBACK_EVENT,        # Event for one agent to provide feedback to another
)
from contextpilot.core.agent_names import (
    COACH_AGENT_NAME,
    SPEC_AGENT_NAME,
    DEVELOPMENT_AGENT_NAME,
    CONTEXT_AGENT_NAME,
    MILESTONE_AGENT_NAME,
)

logger = logging.getLogger(__name__)

class CoachAgent(BaseAgent):
    """
    The Coach Agent is responsible for monitoring the overall system,
    identifying issues like idle agents or errors, and providing guidance
    or suggestions to other agents or the system. It leverages AI (Gemini)
    to analyze agent behavior and provide actionable insights.

    This agent's event subscriptions are crucial for its role in system oversight,
    especially in addressing idle agents and errors as highlighted in the retrospective.
    """

    def __init__(self,
                 pubsub_manager: PubSubManager,
                 firestore_manager: FirestoreManager,
                 gemini_client: GeminiClient):
        """
        Initializes the CoachAgent.

        Args:
            pubsub_manager: An instance of PubSubManager for event communication.
            firestore_manager: An instance of FirestoreManager for state persistence
                               or historical data (though not directly used in this snippet).
            gemini_client: An instance of GeminiClient for AI capabilities.
        """
        super().__init__(
            agent_name=COACH_AGENT_NAME,
            pubsub_manager=pubsub_manager,
            firestore_manager=firestore_manager,
            gemini_client=gemini_client
        )
        logger.info(f"{self.agent_name} initialized.")

    def subscribe_to_events(self):
        """
        Defines the events the Coach Agent subscribes to.
        This agent is interested in monitoring agent status, errors, and overall system health
        to provide timely coaching and interventions.
        """
        # Subscribing to events directly related to the retrospective's action items
        self.pubsub_manager.subscribe(AGENT_ERROR_EVENT, self.handle_event)
        self.pubsub_manager.subscribe(AGENT_IDLE_EVENT, self.handle_event)

        # Subscribing to general status updates for broader oversight
        self.pubsub_manager.subscribe(AGENT_STATUS_UPDATE_EVENT, self.handle_event)
        self.pubsub_manager.subscribe(RETROSPECTIVE_SUMMARY_EVENT, self.handle_event)
        logger.info(f"{self.agent_name} subscribed to coaching-relevant events.")

    async def handle_event(self, event_type: str, payload: Dict[str, Any]):
        """
        Handles incoming events relevant to the Coach Agent.
        Dispatches events to specific handler methods based on their type.

        Args:
            event_type: The type of the event (e.g., AGENT_ERROR_EVENT).
            payload: The data associated with the event.
        """
        logger.info(f"{self.agent_name} received event: {event_type} with payload: {payload}")

        try:
            if event_type == AGENT_ERROR_EVENT:
                await self._handle_agent_error(payload)
            elif event_type == AGENT_IDLE_EVENT:
                await self._handle_agent_idle(payload)
            elif event_type == AGENT_STATUS_UPDATE_EVENT:
                await self._handle_agent_status_update(payload)
            elif event_type == RETROSPECTIVE_SUMMARY_EVENT:
                await self._handle_retrospective_summary(payload)
            else:
                logger.warning(f"{self.agent_name} received unhandled event type: {event_type}")
        except Exception as e:
            logger.error(f"Error handling event {event_type} for {self.agent_name}: {e}", exc_info=True)
            # Publish an internal error event for the system to log/monitor this agent's failure
            await self.pubsub_manager.publish(
                AGENT_ERROR_EVENT,
                {"agent_name": self.agent_name, "error": str(e), "event_type": event_type, "original_payload": payload}
            )

    async def _handle_agent_error(self, payload: Dict[str, Any]):
        """
        Handles an AGENT_ERROR_EVENT.
        Analyzes the error using AI and potentially suggests corrective actions or
        notifies relevant agents (e.g., Spec Agent for clarification).
        """
        agent_name = payload.get("agent_name", "Unknown Agent")
        error_message = payload.get("error", "No error message provided.")
        context = payload.get("context", {})

        logger.warning(f"Coach Agent detected error from {agent_name}: {error_message}. Context: {context}")

        # Use Gemini to analyze the error and suggest a fix or next steps
        prompt = (f"An error occurred in agent '{agent_name}'. Error: '{error_message}'. "
                  f"Context: {context}. "
                  "As a system coach, analyze this error and provide a concise suggestion for resolution "
                  "or a recommendation for which agent should investigate (e.g., 'Spec Agent needs to clarify requirements').")

        try:
            ai_suggestion = await self.gemini_client.generate_content(prompt)
            logger.info(f"AI Coach suggestion for {agent_name} error: {ai_suggestion}")

            # Publish a feedback event or an action request to relevant agents
            await self.pubsub_manager.publish(
                AGENT_FEEDBACK_EVENT,
                {
                    "target_agent": agent_name,
                    "source_agent": self.agent_name,
                    "feedback_type": "error_resolution_suggestion",
                    "message": ai_suggestion,
                    "original_error_payload": payload
                }
            )
            # If the suggestion points to the Spec Agent (as per retrospective context),
            # publish a specific action request for requirements review.
            if SPEC_AGENT_NAME in ai_suggestion.lower(): # Simple heuristic for keyword detection
                 await self.pubsub_manager.publish(
                    AGENT_ACTION_REQUEST_EVENT,
                    {
                        "target_agent": SPEC_AGENT_NAME,
                        "source_agent": self.agent_name,
                        "action": "review_requirements_for_error",
                        "details": f"Review requirements related to the error in {agent_name}: {error_message}. Coach suggestion: {ai_suggestion}"
                    }
                )

        except Exception as e:
            logger.error(f"Failed to get AI suggestion for error from {agent_name}: {e}")

    async def _handle_agent_idle(self, payload: Dict[str, Any]):
        """
        Handles an AGENT_IDLE_EVENT.
        Investigates why an agent is idle using AI and suggests potential tasks or checks.
        This directly addresses the retrospective's concern about idle agents.
        """
        idle_agent_name = payload.get("agent_name", "Unknown Agent")
        last_activity_time = payload.get("last_activity_time")
        idle_duration_seconds = payload.get("idle_duration_seconds")

        logger.info(f"Coach Agent detected idle agent: {idle_agent_name}. "
                    f"Last activity: {last_activity_time}, Duration: {idle_duration_seconds}s")

        # Use Gemini to suggest potential tasks or investigate the reason for idleness
        prompt = (f"Agent '{idle_agent_name}' has been idle for {idle_duration_seconds} seconds. "
                  f"Last known activity was at {last_activity_time}. "
                  "As a system coach, suggest potential next steps or tasks for this agent, "
                  "or recommend an investigation into why it's idle. Be concise and actionable.")

        try:
            ai_suggestion = await self.gemini_client.generate_content(prompt)
            logger.info(f"AI Coach suggestion for idle agent {idle_agent_name}: {ai_suggestion}")

            # Publish a suggestion or action request to the idle agent
            await self.pubsub_manager.publish(
                AGENT_ACTION_REQUEST_EVENT,
                {
                    "target_agent": idle_agent_name,
                    "source_agent": self.agent_name,
                    "action": "suggest_task_or_investigate_idle",
                    "details": ai_suggestion,
                    "original_idle_payload": payload
                }
            )
        except Exception as e:
            logger.error(f"Failed to get AI suggestion for idle agent {idle_agent_name}: {e}")

    async def _handle_agent_status_update(self, payload: Dict[str, Any]):
        """
        Handles an AGENT_STATUS_UPDATE_EVENT.
        Monitors general agent progress and provides feedback or identifies bottlenecks.
        """
        agent_name = payload.get("agent_name", "Unknown Agent")
        status = payload.get("status", "unknown")
        progress = payload.get("progress", {})

        logger.debug(f"Coach Agent received status update from {agent_name}: Status={status}, Progress={progress}")

        # Example: If a critical agent is stuck or reporting slow progress, provide coaching.
        # This logic can be expanded based on specific project needs and agent roles.
        if status == "stuck" or (progress.get("percentage") is not None and progress["percentage"] < 10 and progress.get("duration_minutes", 0) > 30):
            prompt = (f"Agent '{agent_name}' is reporting status '{status}' with progress: {progress}. "
                      "As a system coach, analyze this status and provide guidance or suggest an intervention. "
                      "Be concise and actionable.")
            try:
                ai_suggestion = await self.gemini_client.generate_content(prompt)
                logger.info(f"AI Coach suggestion for agent {agent_name} status update: {ai_suggestion}")
                await self.pubsub_manager.publish(
                    AGENT_FEEDBACK_EVENT,
                    {
                        "target_agent": agent_name,
                        "source_agent": self.agent_name,
                        "feedback_type": "status_guidance",
                        "message":