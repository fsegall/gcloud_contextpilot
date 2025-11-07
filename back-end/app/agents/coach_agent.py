import logging
from typing import Dict, Any

from app.agents.base_agent import BaseAgent
from app.services.pubsub_manager import PubSubManager
from app.services.gemini_service import GeminiService
from app.services.firestore_service import FirestoreService
from app.config import AGENT_NAMES, PUBSUB_TOPICS, AGENT_EVENT_TYPES

logger = logging.getLogger(__name__)

class CoachAgent(BaseAgent):
    """
    The Coach Agent is responsible for monitoring the overall project health,
    agent activity, and providing guidance or feedback to other agents.
    It identifies bottlenecks, ensures alignment with project goals, and
    promotes efficient collaboration.

    This agent's primary role is to observe, analyze, and suggest improvements
    or interventions to keep the multi-agent system running smoothly and
    aligned with project objectives.
    """

    def __init__(
        self,
        pubsub_manager: PubSubManager,
        gemini_service: GeminiService,
        firestore_service: FirestoreService,
    ):
        """
        Initializes the Coach Agent with necessary services.

        Args:
            pubsub_manager: Manages Pub/Sub interactions for eventing.
            gemini_service: Provides AI capabilities for analysis and content generation.
            firestore_service: Manages persistent state and data storage.
        """
        super().__init__(
            agent_name=AGENT_NAMES.COACH,
            pubsub_manager=pubsub_manager,
            gemini_service=gemini_service,
            firestore_service=firestore_service,
        )
        logger.info(f"{self.agent_name} initialized.")

    async def subscribe_to_events(self):
        """
        Subscribes the Coach Agent to relevant Pub/Sub topics.
        The Coach Agent needs to be aware of agent activities, errors,
        and project progress to provide effective coaching.
        """
        # Listen for all general agent events (errors, idle status, etc.)
        await self.pubsub_manager.subscribe_to_topic(
            PUBSUB_TOPICS.AGENT_EVENTS, self.on_event, subscription_id=f"{self.agent_name}-agent-events-sub"
        )
        logger.info(f"{self.agent_name} subscribed to {PUBSUB_TOPICS.AGENT_EVENTS}.")

        # Specifically interested in retrospective summaries to identify areas for improvement
        await self.pubsub_manager.subscribe_to_topic(
            PUBSUB_TOPICS.RETROSPECTIVE_EVENTS, self.on_event, subscription_id=f"{self.agent_name}-retrospective-events-sub"
        )
        logger.info(f"{self.agent_name} subscribed to {PUBSUB_TOPICS.RETROSPECTIVE_EVENTS}.")

        # Subscribe to project-wide updates if a dedicated topic exists
        # For now, general AGENT_EVENTS and RETROSPECTIVE_EVENTS provide sufficient context.
        # If specific PROJECT_UPDATE events are published on a separate topic, add subscription here.

    async def on_event(self, event_data: Dict[str, Any]):
        """
        Processes incoming events relevant to the Coach Agent.

        Args:
            event_data: A dictionary containing event details, including 'event_type',
                        'source_agent', and 'payload'.
        """
        event_type = event_data.get("event_type")
        source_agent = event_data.get("source_agent")
        payload = event_data.get("payload", {})

        logger.info(
            f"{self.agent_name} received event: {event_type} from {source_agent}"
        )

        if event_type == AGENT_EVENT_TYPES.AGENT_ERROR:
            await self._handle_agent_error(source_agent, payload)
        elif event_type == AGENT_EVENT_TYPES.AGENT_IDLE:
            await self._handle_agent_idle(source_agent, payload)
        elif event_type == AGENT_EVENT_TYPES.RETROSPECTIVE_SUMMARY:
            await self._handle_retrospective_summary(payload)
        elif event_type == AGENT_EVENT_TYPES.PROJECT_UPDATE:
            await self._handle_project_update(payload)
        else:
            logger.debug(f"{self.agent_name} ignoring event type: {event_type}")

    async def _handle_agent_error(self, source_agent: str, error_details: Dict[str, Any]):
        """
        Handles agent error events.
        Analyzes the error and publishes a coaching suggestion or alert.
        """
        logger.warning(
            f"Coach Agent detected error from {source_agent}: {error_details.get('message', 'No message')}"
        )
        # Use Gemini to analyze the error and suggest corrective actions or notify relevant agents
        prompt = (
            f"An error occurred in agent '{source_agent}'. "
            f"Error details: {error_details.get('message', 'No specific error message provided')}. "
            f"Context: {error_details.get('context', 'No context provided')}. "
            "Suggest a coaching action or a next step for the system to address this error. "
            "Focus on guiding the responsible agent or identifying a new task."
        )
        try:
            analysis = await self.gemini_service.generate_content(prompt)
            coaching_message = f"Detected error in {source_agent}. Analysis and suggestion: {analysis}"
        except Exception as e:
            logger.error(f"Error analyzing agent error with Gemini: {e}")
            coaching_message = (
                f"Agent {source_agent} reported an error. "
                f"Details: {error_details.get('message', 'No details provided')}. "
                "Consider reviewing its recent actions and logs manually."
            )

        await self.publish_event(
            event_type=AGENT_EVENT_TYPES.COACHING_SUGGESTION,
            payload={"message": coaching_message, "target_agent": source_agent, "severity": "high"},
            topic=PUBSUB_TOPICS.COACH_EVENTS
        )

    async def _handle_agent_idle(self, source_agent: str, idle_details: Dict[str, Any]):
        """
        Handles agent idle events.
        This directly addresses the retrospective action item to review triggers for idle agents.
        The coach can prompt for action or suggest reviewing subscriptions.
        """
        logger.info(f"Coach Agent detected {source_agent} is idle. Details: {idle_details.get('reason', 'No reason provided')}")

        coaching_message = (
            f"Agent {source_agent} is currently idle. "
            f"Reason: {idle_details.get('reason', 'Unknown')}. "
            "Consider reviewing its event subscriptions or assigning a new task to reactivate it."
        )

        # Specific handling for the Spec Agent based on retrospective context
        if source_agent == AGENT_NAMES.SPEC:
            # Check if the idle context matches the "Seven unit test are failing" issue
            idle_context = idle_details.get("context", "")
            if "Seven unit test are failing" in idle_context:
                 logger.info(f"Coach prompting Spec Agent for failing tests specification.")
                 # Publish a SPEC_REQUESTED event to activate the Spec Agent
                 await self.publish_event(
                     event_type=AGENT_EVENT_TYPES.SPEC_REQUESTED,
                     payload={
                         "task_description": "Define clear specifications for fixing seven failing unit tests, "
                                             "including detailed requirements and validation criteria for successful implementation.",
                         "priority": "HIGH",
                         "related_issue": "retro-20251107-165558"
                     },
                     topic=PUBSUB_TOPICS.SPEC_EVENTS # Assuming a topic for spec agent inputs
                 )
                 coaching_message += " A specific task related to failing unit tests has been assigned to it."
            else:
                coaching_message += " No specific pending task identified for this idle agent."

        await self.publish_event(
            event_type=AGENT_EVENT_TYPES.COACHING_SUGGESTION,
            payload={"message": coaching_message, "target_agent": source_agent, "severity": "medium"},
            topic=PUBSUB_TOPICS.COACH_EVENTS
        )

    async def _handle_retrospective_summary(self, summary_data: Dict[str, Any]):
        """
        Handles retrospective summary events.
        Uses Gemini to analyze the summary and identify actionable insights for the system.
        """
        logger.info(f"Coach Agent received retrospective summary.")
        prompt = (
            f"Analyze the following retrospective summary and identify key action items "
            f"related to agent performance, project bottlenecks, or areas for improvement. "
            f"Suggest specific coaching actions or prompts for other agents to address these points. "
            f"Format suggestions clearly.\n\n"
            f"Summary: {summary_data.get('summary', 'No summary provided')}"
        )
        try:
            analysis = await self.gemini_service.generate_content(prompt)
            logger.info(f"Coach Agent retrospective analysis: {analysis}")
            # Publish coaching suggestions based on analysis
            await self.publish_event(
                event_type=AGENT_EVENT_TYPES.COACHING_SUGGESTION,
                payload={"message": f"Retrospective analysis: {analysis}", "source_summary": summary_data, "severity": "low"},
                topic=PUBSUB_TOPICS.COACH_EVENTS
            )
        except Exception as e:
            logger.error(f"Error analyzing retrospective summary with Gemini: {e}")
            await self.publish_event(
                event_type=AGENT_EVENT_TYPES.COACHING_SUGGESTION,
                payload={"message": f"Failed to analyze retrospective summary. Manual review recommended. Error: {e}", "source_summary": summary_data, "severity": "low"},
                topic=PUBSUB_TOPICS.COACH_EVENTS
            )

    async def _handle_project_update(self, update_data: Dict[str, Any]):
        """
        Handles general project update events.
        (Placeholder for future functionality)
        """
        logger.info(f"Coach Agent received project update: {update_data.get('status', 'No status')}")
        # TODO: Evaluate project status against defined goals, identify risks,
        # and potentially trigger other agents for corrective actions.
        pass

    async def run(self):
        """
        Starts the Coach Agent's event subscription setup.
        In a Cloud Run context, this method would typically be called once during
        deployment to configure Pub/Sub push subscriptions. The actual event
        processing (`on_event`) is then triggered by incoming Pub/Sub messages
        via an HTTP endpoint.
        """
        await self.subscribe_to_events()
        logger.info(f"{self.agent_name} is configured and ready to receive events.")