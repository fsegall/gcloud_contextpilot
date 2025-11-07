# back-end/app/agents/milestone_agent.py

import os
import json
import logging

from google.cloud import pubsub_v1

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration ---
# Assuming GCP_PROJECT_ID is available as an environment variable in Cloud Run
# For local testing, ensure this is set or provide a default.
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
AGENT_ID = "milestone" # Unique identifier for this agent

# Define Pub/Sub topics this agent is interested in.
# These topics should be consistent with other agents publishing events
# within the ContextPilot multi-agent system.
TOPICS_OF_INTEREST = [
    "contextpilot.project.update",      # General updates about the project state.
    "contextpilot.task.status_change",  # When a development task's status changes (e.g., 'completed', 'blocked').
    "contextpilot.goal.achieved",       # When a specific project goal is met.
    "contextpilot.proposal.accepted",   # When a proposal (e.g., for a new feature or task) is accepted.
    "contextpilot.retrospective.summary", # Summaries from retrospectives, indicating progress, issues, or new insights.
]

# --- MilestoneAgent Class ---
class MilestoneAgent:
    """
    The MilestoneAgent is responsible for tracking project progress against defined milestones.
    It subscribes to various project events to update milestone status, identify new milestones,
    and report on overall project advancement.

    This agent is designed to be "always on" and react to events, making it active rather than idle.
    """

    def __init__(self, project_id: str, agent_id: str):
        """
        Initializes the MilestoneAgent with a project ID and its unique agent ID.
        Sets up the Pub/Sub subscriber client.
        """
        if not project_id:
            raise ValueError("PROJECT_ID must be set for the MilestoneAgent.")
        self.project_id = project_id
        self.agent_id = agent_id
        self.subscriber = pubsub_v1.SubscriberClient()
        self.subscriptions = {} # Stores topic_name -> subscription_path mapping

        logger.info(f"MilestoneAgent '{self.agent_id}' initialized for project '{self.project_id}'.")

    def _get_topic_path(self, topic_name: str) -> str:
        """Constructs the full Pub/Sub topic path."""
        return self.subscriber.topic_path(self.project_id, topic_name)

    def _get_subscription_path(self, topic_name: str) -> str:
        """
        Constructs a unique subscription path for this agent and a given topic.
        Uses a consistent naming convention: contextpilot-{agent_id}-sub-{topic_name_slug}.
        """
        # Replace dots with hyphens for a cleaner slug in the subscription name
        topic_slug = topic_name.replace('.', '-')
        return self.subscriber.subscription_path(self.project_id, f"contextpilot-{self.agent_id}-sub-{topic_slug}")

    def subscribe_to_events(self):
        """
        Subscribes the MilestoneAgent to all defined topics of interest.
        It checks if a subscription already exists; if not, it creates a new pull subscription.
        """
        logger.info(f"MilestoneAgent '{self.agent_id}' is setting up subscriptions for {len(TOPICS_OF_INTEREST)} topics...")
        for topic_name in TOPICS_OF_INTEREST:
            topic_path = self._get_topic_path(topic_name)
            subscription_path = self._get_subscription_path(topic_name)

            try:
                # Attempt to get the subscription to check for its existence
                self.subscriber.get_subscription(request={"subscription": subscription_path})
                logger.info(f"Subscription '{subscription_path}' already exists for topic '{topic_name}'. Reusing.")
            except Exception as e:
                # If the subscription does not exist (e.g., NotFound exception), create it.
                logger.warning(f"Subscription '{subscription_path}' not found for topic '{topic_name}'. Attempting to create.")
                try:
                    # Create a pull subscription. Pull subscriptions are generally well-suited
                    # for agents running in environments like Cloud Run that might scale down.
                    self.subscriber.create_subscription(
                        request={
                            "name": subscription_path,
                            "topic": topic_path,
                            "ack_deadline_seconds": 60, # Time given to acknowledge a message
                        }
                    )
                    logger.info(f"Created subscription '{subscription_path}' for topic '{topic_name}'.")
                except Exception as create_e:
                    logger.error(f"Failed to create subscription '{subscription_path}' for topic '{topic_name}': {create_e}")
                    continue # Continue to the next topic if creation fails

            self.subscriptions[topic_name] = subscription_path
        logger.info(f"MilestoneAgent '{self.agent_id}' finished setting up subscriptions.")

    def _callback(self, message: pubsub_v1.subscriber.message.Message):
        """
        Callback function invoked when a new message is received on a subscribed topic.
        It decodes, logs, processes, and acknowledges/nacks the message.
        """
        logger.info(f"Received message: ID={message.message_id}, Attributes={message.attributes}")
        try:
            # Decode message data from bytes to JSON
            data = json.loads(message.data.decode('utf-8'))
            # Assuming publishers add a 'topic_name' attribute for easier routing
            topic_name = message.attributes.get('topic_name', 'unknown_topic')
            logger.info(f"Processing message from topic '{topic_name}': {data}")

            # Delegate message processing to a dedicated method
            self.process_message(topic_name, data, message.attributes)

            message.ack() # Acknowledge the message after successful processing
            logger.debug(f"Message ID {message.message_id} acknowledged.")
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON from message ID {message.message_id}. Data: {message.data.decode('utf-8')}")
            message.nack() # Negative acknowledge if message is malformed, so it can be redelivered or moved to DLQ
        except Exception as e:
            logger.error(f"Error processing message ID {message.message_id}: {e}", exc_info=True)
            message.nack() # Negative acknowledge on other processing errors

    def process_message(self, topic_name: str, data: dict, attributes: dict):
        """
        Dispatches incoming messages to specific handlers based on the topic name.
        This method contains the core logic for the MilestoneAgent to react to events.
        """
        logger.info(f"MilestoneAgent '{self.agent_id}' received event on '{topic_name}'.")

        # In a real implementation, this would involve:
        # 1. Querying Firestore for current project milestones and related data.
        # 2. Analyzing the event data (e.g., task completed, goal achieved).
        # 3. Updating milestone progress or status in Firestore.
        # 4. Potentially publishing new events (e.g., "milestone.updated", "milestone.achieved")
        #    to notify other agents or the VSCode extension.
        # 5. Interacting with Gemini for AI-driven insights or suggestions regarding milestones.

        if topic_name == "contextpilot.task.status_change":
            self._handle_task_status_change(data, attributes)
        elif topic_name == "contextpilot.project.update":
            self._handle_project_update(data, attributes)
        elif topic_name == "contextpilot.goal.achieved":
            self._handle_goal_achieved(data, attributes)
        elif topic_name == "contextpilot.proposal.accepted":
            self._handle_proposal_accepted(data, attributes)
        elif topic_name == "contextpilot.retrospective.summary":
            self._handle_retrospective_summary(data, attributes)
        else:
            logger.warning(f"No specific handler defined for topic '{topic_name}'. Message data: {data}")

    def _handle_task_status_change(self, data: dict, attributes: dict):
        """Handles events related to task status changes."""
        task_id = data.get('task_id')
        new_status = data.get('new_status')
        logger.info(f"Task '{task_id}' status changed to '{new_status}'. Assessing impact on project milestones.")
        # Example: If new_status is 'completed', check if this task is part of a milestone
        # and update the milestone's progress.

    def _handle_project_update(self, data: dict, attributes: dict):
        """Handles general project update events."""
        update_type = data.get('update_type')
        logger.info(f"Project update of type '{update_type}' received. Re-evaluating overall project state for milestones.")
        # Example: A major project update might require reviewing all active milestones.

    def _handle_goal_achieved(self, data: dict, attributes: dict):
        """Handles events where a specific project goal is achieved."""
        goal_id = data.get('goal_id')
        logger.info(f"Goal '{goal_id}' achieved! Updating relevant milestones and reporting progress.")
        # Example: Mark any milestones directly associated with this goal as complete.

    def _handle_proposal_accepted(self, data: dict, attributes: dict):
        """Handles events where a new proposal (e.g., feature, task) is accepted."""
        proposal_id = data.get('proposal_id')
        logger.info(f"Proposal '{proposal_id}' accepted. Considering new milestones or adjustments to existing ones.")
        # Example: A new accepted feature might necessitate creating a new milestone or
        # adding tasks to an existing one.

    def _handle_retrospective_summary(self, data: dict, attributes: dict):
        """Handles events providing a summary from a retrospective session."""
        summary = data.get('summary', 'No summary provided.')
        logger.info(f"Retrospective summary received. Analyzing for milestone risks, opportunities, or adjustments: {summary[:150]}...")
        # Example: Identify if any issues reported in the retro impact milestone timelines,
        # or if new insights suggest new milestones.

    def start_listening(self):
        """
        Starts listening for messages on all configured subscriptions using a streaming pull.
        This method will block indefinitely, keeping the agent active to process messages.
        """
        if not self.subscriptions:
            logger.warning("No subscriptions found. Call subscribe_to_events() before starting to listen.")
            return

        logger.info(f"MilestoneAgent '{self.agent_id}' starting to listen for messages on {len(self.subscriptions)} subscriptions...")
        
        # Create a Future for each subscription, allowing concurrent listening
        futures = []
        for topic_name, sub_path in self.subscriptions.items():
            logger.info(f"Actively listening on subscription: {sub_path} for topic: {topic_name}")
            # The `subscribe` method is non-blocking and returns a Future object
            future = self.subscriber.subscribe(sub_path, callback=self._callback)
            futures.append(future)

        # Keep the main thread alive, waiting for messages to be processed by the callbacks.
        # In a Cloud Run context, this means the instance will stay active.
        try:
            # Wait for all futures to complete. Since these are streaming pulls, they won't
            # complete unless cancelled or an error occurs. This effectively keeps the agent running.
            for future in futures:
                future.result()
        except KeyboardInterrupt:
            logger.info("MilestoneAgent received shutdown signal (KeyboardInterrupt).")
        except Exception as e:
            logger.error(f"MilestoneAgent encountered an error during listening: {e}", exc_info=True)
        finally:
            # Cancel all subscription futures to gracefully stop listening
            for future in futures:
                future.cancel()
            self.subscriber.close() # Close the Pub/Sub client
            logger.info("MilestoneAgent shut down gracefully.")

# --- Main Execution Block ---
if __name__ == "__main__":
    # For local development/testing, ensure GCP_PROJECT_ID is set in your environment.
    # In a Cloud Run environment, this will be automatically provided by GCP.
    if not PROJECT_ID or PROJECT_ID == "your-gcp-project-id":
        logger.warning("GCP_PROJECT_ID environment variable not set. Using 'contextpilot-dev' for local testing. Please set it for production.")
        PROJECT_ID = os.getenv("GCP_PROJECT_ID", "contextpilot-dev") # Fallback for local testing

    milestone_agent = MilestoneAgent(project_id=PROJECT_ID, agent_id=AGENT_ID)

    # 1. Ensure all necessary Pub/Sub subscriptions are created or exist.
    milestone_agent.subscribe_to_events()

    # 2. Start the agent's listening loop. This