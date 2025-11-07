import logging
import os
import json
from typing import Dict, Any, Optional

from google.cloud import firestore
from google.cloud import pubsub_v1

# Configure logging for the agent
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DevelopmentAgent:
    """
    The DevelopmentAgent is responsible for implementing features, fixing bugs,
    and generating code based on specifications and context provided by other agents.
    It subscribes to development-related events and publishes updates on its progress.

    This agent's event subscriptions are defined by its INPUT_TOPIC_ID and SUBSCRIPTION_ID.
    If the agent is observed to be idle, these configurations should be reviewed
    to ensure messages are being correctly published to its input topic.
    """

    AGENT_NAME = "development"
    # Define Pub/Sub topics relevant to this agent.
    # These environment variables should be set in the Cloud Run service or local environment.
    INPUT_TOPIC_ID = os.getenv("PUBSUB_DEVELOPMENT_AGENT_INPUT_TOPIC", "contextpilot-development-tasks")
    OUTPUT_TOPIC_ID = os.getenv("PUBSUB_AGENT_OUTPUT_TOPIC", "contextpilot-agent-events")
    # Subscription ID for this agent to listen to its input topic.
    # This subscription should be created in GCP Pub/Sub for the INPUT_TOPIC_ID.
    SUBSCRIPTION_ID = os.getenv("PUBSUB_DEVELOPMENT_AGENT_SUBSCRIPTION", "contextpilot-development-tasks-sub")

    def __init__(
        self,
        firestore_client: firestore.Client,
        pubsub_publisher: pubsub_v1.PublisherClient,
        pubsub_subscriber: pubsub_v1.SubscriberClient,
        # Assuming a Gemini client might be passed for AI capabilities
        # gemini_client: Any = None,
        project_id: str = os.getenv("GCP_PROJECT_ID")
    ):
        """
        Initializes the DevelopmentAgent with necessary Google Cloud clients.

        Args:
            firestore_client: An initialized Google Cloud Firestore client.
            pubsub_publisher: An initialized Google Cloud Pub/Sub publisher client.
            pubsub_subscriber: An initialized Google Cloud Pub/Sub subscriber client.
            gemini_client: An optional client for interacting with the Gemini model.
            project_id: The Google Cloud project ID.
        """
        if not project_id:
            raise ValueError("GCP_PROJECT_ID environment variable or project_id argument must be set.")

        self.project_id = project_id
        self.firestore_client = firestore_client
        self.pubsub_publisher = pubsub_publisher
        self.pubsub_subscriber = pubsub_subscriber
        # self.gemini_client = gemini_client # Uncomment if using GeminiClient

        self.input_topic_path = pubsub_publisher.topic_path(self.project_id, self.INPUT_TOPIC_ID)
        self.output_topic_path = pubsub_publisher.topic_path(self.project_id, self.OUTPUT_TOPIC_ID)
        self.subscription_path = pubsub_subscriber.subscription_path(self.project_id, self.SUBSCRIPTION_ID)

        logger.info(f"DevelopmentAgent initialized. Agent Name: {self.AGENT_NAME}")
        logger.info(f"Listening for tasks on subscription: {self.subscription_path}")
        logger.info(f"Publishing events to topic: {self.output_topic_path}")

    def _publish_event(self, event_type: str, payload: Dict[str, Any], context: Optional[Dict[str, Any]] = None):
        """
        Publishes an event to the agent's output topic, making its actions visible
        to other agents or services.

        Args:
            event_type: The type of the event (e.g., "code_generated", "task_completed").
            payload: The main data payload of the event.
            context: Optional contextual information for the event, such as original message ID.
        """
        event_data = {
            "agent": self.AGENT_NAME,
            "event_type": event_type,
            "timestamp": firestore.SERVER_TIMESTAMP, # Use server timestamp for consistency
            "payload": payload,
            "context": context if context is not None else {}
        }
        data_str = json.dumps(event_data, default=str) # default=str handles non-serializable types like timestamps
        data_bytes = data_str.encode("utf-8")

        try:
            future = self.pubsub_publisher.publish(self.output_topic_path, data_bytes)
            message_id = future.result() # Blocks until the message is published
            logger.info(f"Published event '{event_type}' with message ID: {message_id}")
            return message_id
        except Exception as e:
            logger.error(f"Failed to publish event '{event_type}' to {self.output_topic_path}: {e}", exc_info=True)
            raise

    def _handle_task_assigned(self, message_data: Dict[str, Any], original_message_id: str):
        """
        Handles a 'task_assigned' event, which initiates a development task for this agent.
        This method simulates code generation based on provided specifications.
        """
        task_id = message_data.get("task_id")
        description = message_data.get("description")
        specifications = message_data.get("specifications")
        # Additional context from the original message, if any
        task_context = message_data.get("context", {})

        if not task_id or not description or not specifications:
            logger.error(f"Received malformed 'task_assigned' event: missing task_id, description, or specifications. "
                         f"Message ID: {original_message_id}")
            # Potentially publish an error event or nack the message
            return

        logger.info(f"DevelopmentAgent received task '{task_id}'. Description: '{description[:100]}...'")

        # 1. Update task status in Firestore to 'in_progress'
        task_ref = self.firestore_client.collection("tasks").document(task_id)
        task_ref.update({"status": "in_progress", "assigned_agent": self.AGENT_NAME, "updated_at": firestore.SERVER_TIMESTAMP})
        logger.info(f"Task '{task_id}' status updated to 'in_progress'.")

        # 2. Simulate interaction with Gemini or other code generation tools
        # In a real scenario, this would involve calling self.gemini_client.generate_code()
        # based on description and specifications.
        generated_code = (
            f"# Simulated code for task: {task_id}\n"
            f"# Description: {description}\n"
            f"# Specifications:\n{json.dumps(specifications, indent=2)}\n\n"
            f"def implement_feature_{task_id.replace('-', '_')}():\n"
            f"    # TODO: Implement actual logic based on specifications using AI/tools\n"
            f"    print('Feature {task_id} implemented successfully!')\n"
            f"    return True\n"
        )
        logger.info(f"Simulated code generation for task '{task_id}'.")

        # 3. Publish a 'code_generated' event
        self._publish_event(
            event_type="code_generated",
            payload={
                "task_id": task_id,
                "generated_code": generated_code,
                "status": "ready_for_review",
                "agent_notes": "Initial code generated based on specifications. Awaiting review."
            },
            context={"original_message_id": original_message_id, **task_context}
        )
        logger.info(f"Published 'code_generated' event for task '{task_id}'.")

        # 4. Update task status in Firestore to 'completed' or 'awaiting_review'
        task_ref.update({"status": "awaiting_review", "result": "code_generated", "updated_at": firestore.SERVER_TIMESTAMP})
        logger.info(f"Task '{task_id}' status updated to 'awaiting_review'.")

    def _process_message(self, message: pubsub_v1.subscriber.message.Message):
        """
        Callback function to process an incoming Pub/Sub message.
        This is where the agent's core logic for reacting to events resides.
        """
        try:
            data = json.loads(message.data.decode("utf-8"))
            event_type = data.get("event_type")
            payload = data.get("payload", {})
            original_message_id = message.message_id

            logger.info(f"DevelopmentAgent received event '{event_type}' (Message ID: {original_message_id})")

            if event_type == "task_assigned":
                self._handle_task_assigned(payload, original_message_id)
            elif event_type == "code_review_feedback":
                # This agent would handle feedback on previously generated code.
                # It would likely involve re-running Gemini or applying manual fixes.
                task_id = payload.get("task_id")
                feedback = payload.get("feedback")
                logger.info(f"Received code review feedback for task '{task_id}'. Feedback: '{feedback[:100]}...'")
                # TODO: Implement logic to refine code based on feedback
                self._publish_event(
                    event_type="code_refined",
                    payload={"task_id": task_id, "status": "re_reviewed", "notes": "Code refined based on feedback."},
                    context={"original_message_id": original_message_id}
                )
            elif event_type == "test_failed":
                # Handle events indicating failing tests, triggering debugging or fix attempts.
                task_id = payload.get("task_id")
                error_details = payload.get("error_details")
                logger.warning(f"Received 'test_failed' event for task '{task_id}'. Error: '{error_details[:100]}...'")
                # TODO: Implement logic to debug and fix failing tests
                self._publish_event(
                    event_type="bug_fix_attempt",
                    payload={"task_id": task_id, "status": "fixing_bug", "notes": "Attempting to fix failing tests."},
                    context={"original_message_id": original_message_id}
                )
            else:
                logger.warning(f"DevelopmentAgent received unhandled event type: {event_type}")

            message.ack()  # Acknowledge the message to remove it from the subscription
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from message {message.message_id}: {e}. Nacking message.", exc_info=True)
            message.nack()  # Negative acknowledge if message is malformed
        except Exception as e:
            logger.error(f"Error processing message {message.message_id}: {e}. Nacking message.", exc_info=True)
            message.nack() # Negative acknowledge for other processing errors

    def start_listening(self):
        """
        Starts the Development Agent listening for messages on its Pub/Sub subscription.
        This method is blocking and will run indefinitely, typically in a dedicated
        worker process or Cloud Run service configured for Pub/Sub pull subscriptions.
        """
        logger.info(f"DevelopmentAgent starting to listen on subscription: {self.subscription_path}")
        streaming_pull_future = self.pubsub_subscriber.subscribe(
            self.subscription_path, callback=self._process_message
        )
        logger.info(f"Listening for messages on {self.subscription_path}...")

        # The subscriber is non-blocking, so we must keep the main thread alive to
        # allow the callback to be invoked.
        try:
            streaming_pull_future.result()  # Blocks indefinitely
        except KeyboardInterrupt:
            streaming_pull_future.cancel()
            streaming_pull_future.result() # Wait for the pull future to complete
            logger.info("DevelopmentAgent stopped listening due to KeyboardInterrupt.")
        except Exception as e:
            logger.critical(f"DevelopmentAgent encountered a critical error while listening: {e}", exc_info=True)
            streaming_pull_future.cancel()
            streaming_pull_future.result()
            raise # Re-raise the exception to indicate a critical failure

# Example of how to run the agent (for local testing/demonstration)
# In a Cloud Run environment, this would typically be integrated into the main app.py
# or a separate worker service.
if __name__ == "__main__":
    # Set environment variables for local testing.
    # Replace "your-gcp-project-id" with your actual GCP project ID.
    os.environ.setdefault("GCP_PROJECT_ID", "your-gcp-project-id")
    os.environ.setdefault("PUBSUB_DEVELOPMENT_AGENT_INPUT_TOPIC", "contextpilot-development-tasks")
    os.environ.setdefault("PUBSUB_AGENT_OUTPUT_TOPIC", "contextpilot-agent-events")
    os.environ.setdefault("PUBSUB_DEVELOPMENT_AGENT_SUBSCRIPTION", "contextpilot-development-tasks-sub")

    if os.getenv("GCP_PROJECT_ID") == "your-gcp-project-id":
        logger.critical("GCP_PROJECT_ID environment variable is not set. "
                        "Please configure it with your actual project ID to run locally.")
        import sys
        sys.exit(1)

    try:
        # Initialize Google Cloud clients
        _firestore_client = firestore.Client()
        _pubsub_publisher = pubsub_v1.PublisherClient()
        _pubsub_subscriber = pubsub_v1.SubscriberClient()

        # Create the DevelopmentAgent instance
        dev_agent = DevelopmentAgent(
            firestore_client=_firestore_client,
            pubsub_publisher=_pubsub_publisher,
            pubsub_subscriber=_pubsub_subscriber,
            project_id=os.getenv("GCP_PROJECT_ID")
        )

        # Start the agent (this call is blocking)
        dev_agent.start_listening()

    except Exception as e:
        logger.critical(f"Failed to initialize or run DevelopmentAgent locally: {e}", exc_info=True)
        sys.exit(1)