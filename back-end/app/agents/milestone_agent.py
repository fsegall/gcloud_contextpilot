import logging
from typing import Dict, Any
from datetime import datetime, timezone

# Assuming these imports exist based on project context and common patterns
# BaseAgent provides common functionality for all agents (e.g., agent_id, basic logging setup)
from app.agents.base_agent import BaseAgent
# PubSubManager handles interaction with Google Cloud Pub/Sub
from app.services.pubsub_manager import PubSubManager

# Configure logging for the agent
logger = logging.getLogger(__name__)

class MilestoneAgent(BaseAgent):
    """
    The MilestoneAgent is responsible for tracking project milestones, deadlines,
    and overall project progress within the ContextPilot system.
    It monitors various project-related events to assess current status, identify
    potential blockers, and ensure the project remains on schedule.

    This agent plays a crucial role in providing a high-level overview of project
    health and can trigger alerts or reports based on milestone statuses.
    """

    def __init__(self, agent_id: str = "milestone_agent", pubsub_manager: PubSubManager = None):
        """
        Initializes the MilestoneAgent.

        Args:
            agent_id (str): The unique identifier for this agent. Defaults to "milestone_agent".
            pubsub_manager (PubSubManager, optional): An instance of the PubSubManager.
                                                      If not provided, a new one will be created.
        """
        super().__init__(agent_id)
        # Initialize PubSubManager. This allows for dependency injection for testing.
        self.pubsub_manager = pubsub_manager if pubsub_manager else PubSubManager()
        logger.info(f"MilestoneAgent '{self.agent_id}' initialized and ready to subscribe.")
        # Immediately subscribe to events upon initialization
        self.subscribe_to_events()

    def subscribe_to_events(self):
        """
        Configures and registers the MilestoneAgent's subscriptions to relevant
        Google Cloud Pub/Sub topics.

        This method is critical for defining what events the MilestoneAgent listens to.
        The retrospective noted 'milestone' agent as idle, implying its triggers
        might need review. This implementation explicitly defines its intended
        event sources to ensure it's actively monitoring project progress.
        """
        logger.info(f"MilestoneAgent '{self.agent_id}' is setting up event subscriptions...")

        # 1. Subscribe to its own command topic for direct instructions
        #    e.g., "milestone_agent, generate a progress report."
        self.pubsub_manager.subscribe(
            topic_name=f"agent_commands_{self.agent_id}",
            callback=self.handle_event,
            subscription_id=f"{self.agent_id}_commands_sub"
        )
        logger.info(f"Subscribed to direct commands topic: 'agent_commands_{self.agent_id}'")

        # 2. Subscribe to general project update events
        #    These events might come from other agents (e.g., DevelopmentAgent, SpecAgent)
        #    indicating changes in project status, scope, or resource allocation.
        self.pubsub_manager.subscribe(
            topic_name="project_updates",
            callback=self.handle_event,
            subscription_id=f"{self.agent_id}_project_updates_sub"
        )
        logger.info(f"Subscribed to general project updates topic: 'project_updates'")

        # 3. Subscribe to task status changes
        #    Crucial for tracking progress against specific tasks that contribute to milestones.
        #    e.g., "task_completed", "task_failed", "task_started".
        self.pubsub_manager.subscribe(
            topic_name="task_status_changes",
            callback=self.handle_event,
            subscription_id=f"{self.agent_id}_task_status_sub"
        )
        logger.info(f"Subscribed to task status changes topic: 'task_status_