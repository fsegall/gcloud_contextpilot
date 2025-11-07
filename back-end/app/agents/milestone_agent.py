import logging
import os
from typing import Dict, Any, Optional

# Assuming these services and base agent exist in the project structure
from app.services.pubsub_service import PubSubService
from app.services.firestore_service import FirestoreService
from app.services.gemini_service import GeminiService
from app.agents.base_agent import BaseAgent

# Configure logging for the agent
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())

class MilestoneAgent(BaseAgent):
    """
    The Milestone Agent is responsible for tracking project milestones, progress,
    and generating updates or reports related to project timelines.
    It subscribes to events that indicate progress, task completion, or
    changes in project scope that might affect milestones.

    This agent plays a crucial role in providing an overview of project health
    and ensuring that the project stays on track towards its defined goals.
    """

    AGENT_NAME = "milestone"
    # Define the Pub/Sub topics this agent should subscribe to.
    # These topics represent events that are relevant for milestone tracking.
    SUBSCRIPTION_TOPICS = [
        "project_updates",      # General project status updates
        "task_completion",      # When individual tasks are completed
        "scope_changes",        # Changes in project scope or requirements
        "agent_status_updates", # Status updates from other agents (e.g., Spec, Dev)
        "error_notifications"   # To be aware of critical errors affecting progress
    ]

    def __init__(
        self,
        pubsub_service: PubSubService,
        firestore_service: FirestoreService,
        gemini_service: GeminiService,
        agent_name: str = AGENT_NAME
    ):
        """
        Initializes the MilestoneAgent with necessary services.

        Args:
            pubsub_service: An instance of PubSubService for event handling.
            firestore_service: An instance of FirestoreService for data persistence.
            gemini_service: An instance of GeminiService for AI capabilities.
            agent_name: The name of this agent. Defaults to AGENT_NAME.
        """
        super().__init__(agent_name, pubsub_service, firestore_service, gemini_service)
        logger.info(f"MilestoneAgent '{self.agent_name}' initialized.")

        # Internal state to track current project milestones and their status
        self.current_milestones: Dict[str, Any] = {}

    def subscribe_to_events(self) -> None:
        """
        Subscribes the Milestone Agent to its defined Pub/Sub topics.
        This method ensures the agent is configured to receive relevant events
        that trigger its milestone tracking and reporting logic.
        """
        logger.info(f"MilestoneAgent '{self.agent_name}' is subscribing to events...")
        for topic in self.SUBSCRIPTION_TOPICS:
            try:
                # The PubSubService is expected to handle the actual subscription
                # mechanism, linking the topic to this agent's message handler.
                self.pubsub_service.subscribe_agent_to_topic(
                    topic=topic,
                    agent_name=self.agent_name,
                    callback=self.handle_message
                )
                logger.info(f"MilestoneAgent subscribed to topic: '{topic}'.")
            except Exception as e:
                logger.error(f"Failed to subscribe MilestoneAgent to topic '{topic}': {e}", exc_info=True)

    async def handle_message(self, message_data: Dict[str, Any], message_id: str) -> None:
        """
        Processes incoming messages from subscribed Pub/Sub topics.
        This is the main entry point for event-driven processing for this agent.

        Args:
            message_data: The deserialized message payload containing event details.
            message_id: The unique ID of the Pub/Sub message.
        """
        logger.info(f"MilestoneAgent '{self.agent_name}' received message (ID: {message_id}).")

        event_type = message_data.get("event_type")
        payload = message_data.get("payload", {})
        source_agent = message_data.get("source_agent", "unknown")

        if not event_type:
            logger.warning(f"Message {message_id} from '{source_agent}' missing 'event_type'. Skipping.")
            return

        logger.debug(f"Processing event_type: '{event_type}' from '{source_agent}' with payload: {payload}")

        try:
            if event_type == "project_update":
                await self._process_project_update(payload)
            elif event_type == "task_completion":
                await self._process_task_completion(payload)
            elif event_type == "scope_change":
                await self._process_scope_change(payload)
            elif event_type == "agent_status_update":
                await self._process_agent_status_update(payload)
            elif event_type == "error_notification":
                await self._process_error_notification(payload)
            else:
                logger.info(f"MilestoneAgent received unhandled event type: '{event_type}'.")

            # After processing, potentially re-evaluate milestones and publish updates
            await self._evaluate_and_update_milestones()

        except Exception as e:
            logger.error(f"Error processing message {message_id} for event type '{event_type}': {e}", exc_info=True)
            # Potentially publish an error event or notify a monitoring agent

    async def _process_project_update(self, payload: Dict[str, Any]) -> None:
        """
        Handles project update events.
        Analyzes general project status changes and their impact on milestones.
        """
        project_id = payload.get("project_id")
        update_details = payload.get("details")
        timestamp = payload.get("timestamp")
        logger.info(f"Project update for '{project_id}' at {timestamp}: {update_details[:100]}...")

        # Example: Use Gemini to summarize the update and assess milestone impact
        prompt = (
            f"Analyze the following project update for project '{project_id}': '{update_details}'. "
            "Identify any direct or indirect impacts on project milestones, timelines, or risks. "
            "Provide a concise summary of the impact."
        )
        ai_analysis = await self.gemini_service.generate_content(prompt)
        logger.debug(f"AI analysis of project update: {ai_analysis}")

        # Store or update relevant project status in Firestore
        await self.firestore_service.update_document(
            collection_name="projects",
            doc_id=project_id,
            data={"last_update": timestamp, "status_summary": ai_analysis}
        )

    async def _process_task_completion(self, payload: Dict[str, Any]) -> None:
        """
        Handles task completion events.
        Checks if completed tasks contribute to achieving any defined milestones.
        """
        task_id = payload.get("task_id")
        status = payload.get("status")
        assigned_to = payload.get("assigned_to")
        milestone_id = payload.get("milestone_id") # Task might be directly linked to a milestone
        logger.info(f"Task '{task_id}' by '{assigned_to}' completed with status: '{status}'.")

        # If task is linked to a milestone, update its progress
        if milestone_id:
            # Fetch milestone, update progress, save back
            milestone_doc = await self.firestore_service.get_document("milestones", milestone_id)
            if milestone_doc:
                # Logic to update milestone progress based on task completion
                logger.debug(f"Updating progress for milestone '{milestone_id}' due to task '{task_id}'.")
                # Example: increment completed tasks count, recalculate percentage
                # await self.firestore_service.update_document("milestones", milestone_id, {"progress": new_progress})
            else:
                logger.warning(f"Milestone '{milestone_id}' linked to task '{task_id}' not found.")

    async def _process_scope_change(self, payload: Dict[str, Any]) -> None:
        """
        Handles scope change events.
        Assesses the impact of scope changes on existing milestones and timelines.
        """
        change_details = payload.get("details")
        change_id = payload.get("change_id")
        logger.warning(f"Scope change '{change_id}' detected: {change_details[:100]}... Re-evaluating milestones.")

        # Use Gemini to assess the impact on current milestones and timelines
        prompt = (
            f"A project scope change has occurred: '{change_details}'. "
            "Assess its potential impact on existing project milestones, deadlines, "
            "resource allocation, and overall project feasibility. "
            "Suggest necessary adjustments or risks to consider."
        )
        ai_assessment = await self.gemini_service.generate_content(prompt)
        logger.debug(f"AI assessment for scope change: {ai_assessment}")

        # Potentially publish a new event for the Development Agent or Spec Agent
        # to review and adjust plans based on the AI assessment.
        await self.pubsub_service.publish(
            topic="milestone_impact_assessment",
            data={
                "event_type": "scope_change_impact",
                "payload": {"change_id": change_id, "assessment": ai_assessment},
                "source_agent": self.agent_name
            }
        )

    async def _process_agent_status_update(self, payload: Dict[str, Any]) -> None:
        """
        Handles status updates from other agents.
        Monitors the progress and activity of other agents, which can be critical
        for milestone progression (e.g., Spec Agent completing specs for a feature).
        """
        agent_name = payload.get("agent_name")
        status = payload.get("status")
        progress = payload.get("progress")
        last_activity = payload.get("last_activity")
        logger.info(f"Received status update from '{agent_name}': Status='{status}', Progress='{progress}', Last Activity='{last_activity}'.")

        # Check for idle agents or agents blocking milestones
        if status == "idle" and agent_name in ["spec", "development", "context", "coach"]:
            logger.warning(f"Agent '{agent_name}' is idle. This might impact dependent milestones.")
            # Potentially publish an alert or create a task for a human or another agent
            # to investigate why the agent is idle.
            await self.pubsub_service.publish(
                topic="agent_alert",
                data={
                    "event_type": "idle_agent_alert",
                    "payload": {"agent_name": agent_name, "reason": "Idle status detected by Milestone Agent"},
                    "source_agent": self.agent_name
                }
            )
        # Example: If Spec Agent completes a critical specification, this might unblock a development milestone.
        # if agent_name == "spec" and status == "completed_specs" and progress == "100%":
        #     await self._check_for_milestone_unblock("spec_completion", payload)

    async def _process_error_notification(self, payload: Dict[str, Any]) -> None:
        """
        Handles error notifications from any part of the system.
        Critical errors can halt progress and impact milestones.
        """
        error_details = payload.get("details")
        severity = payload.get("severity", "medium")
        source = payload.get("source", "system")
        logger.error(f"Received error notification (Severity: {severity}) from '{source}': {error_details[:150]}...")

        # Use Gemini to assess the potential impact of the error on project milestones
        prompt = (
            f"An error occurred in the system: '{error_details}'. "
            f"Severity is '{severity}'. Source: '{source}'. "
            "Assess the potential impact of this error on project milestones, "
            "timelines, and overall project stability. Suggest immediate actions if critical."
        )
        ai_impact_assessment = await self.gemini_service.generate_content(prompt)
        logger.debug(f"AI impact assessment for error: {ai_impact_assessment}")

        # Store the error and its impact assessment in Firestore
        await self.firestore_service.add_document(
            collection_name="error_log",
            data={
                "timestamp": payload.get("timestamp", os.getenv("CURRENT_TIMESTAMP")),
                "error_details": error_details,
                "severity": severity,
                "source": source,
                "milestone_impact": ai_impact_assessment
            }
        )
        # Potentially publish an alert for human intervention or a remediation agent
        await self.pubsub_service.publish(
            topic="system_alert",
            data={
                "event_type": "critical_error_impact",
                "payload": {"error": error_details, "impact": ai_impact_assessment},
                "source_agent": self.agent_name
            }
        )


    async def _evaluate_and_update_milestones(self) -> None:
        """
        Periodically or after significant events, this method re-evaluates
        the status of all active milestones based on current project data.
        It can fetch data from Firestore, apply business logic, and use AI
        to predict completion dates or identify risks.
        """
        logger.debug("Evaluating and updating project milestones...")
        # Example: Fetch all active milestones from Firestore
        # active_milestones = await self.firestore_service.get_collection("milestones", query={"status": "active"})

        # For each milestone, assess its current status, progress, and risks
        # This might involve querying tasks, project updates, agent statuses, etc.
        # Use Gemini to generate a summary report or predict completion dates.
        # prompt = "Generate a summary report of current project milestones, their status, and potential risks."
        # milestone_report = await self.gemini_service.generate_content(prompt)
        # logger.info(f"Milestone Report: {milestone_report[:200]}...")

        # If a milestone is achieved, publish a "milestone_achieved" event
        # If a milestone is at risk, publish a "milestone_at_risk" event
        # await self.pubsub_service.publish("milestone_achieved", {"milestone_id": "M-Alpha", "date": "2025-12-01"})
        # await self.firestore_service.update_document("project_status", "overall", {"milestone_report": milestone_report})
        logger.debug("Milestone evaluation complete (placeholder logic).")

    async def run(self) -> None:
        """
        Starts the Milestone Agent.
        In a Cloud Run environment, this method might be called during
        application startup to ensure subscriptions are active, or the agent
        might be instantiated per event. The PubSubService is expected to
        handle the continuous listening mechanism.
        """
        logger.info(f"MilestoneAgent '{self.agent_name}' is starting...")
        self.subscribe_to_events()
        logger.info(f"MilestoneAgent '{self.agent_name}' is active and listening for events.")
        # In a typical Cloud Run setup, the process might exit after
        # handling an event, or a background thread might keep subscriptions alive.
        # The PubSubService should manage the actual message pulling/pushing.