import os
import logging
import json
from concurrent.futures import TimeoutError
import datetime

from google.cloud import pubsub_v1
from google.cloud import firestore

# --- Configuration ---
# These should ideally come from environment variables or a centralized config service
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
if not PROJECT_ID:
    raise ValueError("GCP_PROJECT_ID environment variable not set. Please set it to your Google Cloud Project ID.")

# Pub/Sub topics and subscriptions
# Agents request context on CONTEXT_REQUEST_TOPIC_ID
CONTEXT_REQUEST_TOPIC_ID = "contextpilot.request.context"
# ContextAgent publishes responses on CONTEXT_RESPONSE_TOPIC_ID
CONTEXT_RESPONSE_TOPIC_ID = "contextpilot.response.context"
# The subscription for ContextAgent to listen for context requests
CONTEXT_AGENT_SUBSCRIPTION_ID = "context_agent_request_sub"

# Firestore collection for storing project artifacts (e.g., README.md content)
PROJECT_ARTIFACTS_COLLECTION = "project_artifacts"

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ContextAgent:
    """
    The ContextAgent is responsible for providing project-specific context and
    current development state to other agents in the ContextPilot system.
    It listens for context requests via Google Cloud Pub/Sub and retrieves
    information from Firestore.
    """
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.pubsub_publisher = pubsub_v1.PublisherClient()
        self.pubsub_subscriber = pubsub_v1.SubscriberClient()
        self.firestore_db = firestore.Client(project=project_id)

        # Construct full Pub/Sub topic and subscription paths
        self.context_request_topic_path = self.pubsub_publisher.topic_path(project_id, CONTEXT_REQUEST_TOPIC_ID)
        self.context_response_topic_path = self.pubsub_publisher.topic_path(project_id, CONTEXT_RESPONSE_TOPIC_ID)
        self.context_agent_subscription_path = self.pubsub_subscriber.subscription_path(project_id, CONTEXT_AGENT_SUBSCRIPTION_ID)

        logger.info(f"ContextAgent initialized for project: {self.project_id}")
        logger.info(f"Listening for context requests on subscription: {self.context_agent_subscription_path}")
        logger.info(f"Publishing context responses to topic: {self.context_response_topic_path}")

    def _get_project_artifact(self, artifact_name: str) -> str | None:
        """
        Retrieves the content of a specific project artifact (e.g., 'README.md')
        from the Firestore 'project_artifacts' collection.
        """
        try:
            doc_ref = self.firestore_db.collection(PROJECT_ARTIFACTS_COLLECTION).document(artifact_name)
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict().get("content")
            else:
                logger.warning(f"Project artifact '{artifact_name}' not found in Firestore.")
                return None
        except Exception as e:
            logger.error(f"Error retrieving artifact '{artifact_name}' from Firestore: {e}", exc_info=True)
            return None

    def _get_all_project_artifacts(self) -> dict:
        """
        Retrieves the content of all predefined project markdown artifacts
        from Firestore and returns them in a dictionary.
        """
        artifacts = {}
        # List of key project markdown files to fetch
        artifact_names = [
            "README.md", "project_scope.md", "ARCHITECTURE.md",
            "project_checklist.md", "daily_checklist.md"
        ]
        for name in artifact_names:
            content = self._get_project_artifact(name)
            if content:
                # Store content with a key like 'readme_content'
                artifacts[name.replace(".md", "_content")] = content
        return artifacts

    def _get_dynamic_current_context(self) -> dict:
        """
        Constructs or fetches the dynamic 'Current Context' information.
        This information reflects the immediate state of the project or agent system.
        In a more advanced system, this might involve querying a state manager
        or listening to various system events.
        """
        # For this implementation, we'll provide a snapshot based on the project context.
        # The 'proposal_type' and 'agent' fields might be dynamic based on the active task
        # or the agent requesting context.
        return {
            "proposal_type": "development", # Example: could be 'bugfix', 'feature', etc.
            "agent": "Context Agent",       # The agent providing this context
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat() # Current UTC timestamp
        }

    def _handle_context_request(self, message: pubsub_v1.subscriber.message.Message):
        """
        Callback function executed when a new message is received on the
        ContextAgent's subscription. It processes the request and publishes a response.
        """
        logger.info(f"Received message {message.message_id} on subscription {self.context_agent_subscription_path}")
        try:
            data = json.loads(message.data.decode("utf-8"))
            request_type = data.get("type")
            request_payload = data.get("payload", {})
            # The 'agent_id' attribute helps identify which agent made the request
            requester_agent_id = message.attributes.get("agent_id", "unknown_agent")

            logger.info(f"Processing request from agent '{requester_agent_id}': Type='{request_type}', Payload={request_payload}")

            response_payload = {}
            response_type = "error_response" # Default to error

            if request_type == "get_project_context":
                # Request to get all general project context (artifacts + dynamic context)
                response_payload = self._get_all_project_artifacts()
                response_payload["current_context"] = self._get_dynamic_current_context()
                response_type = "project_context_response"
                logger.info(f"Prepared full project context response for agent '{requester_agent_id}'.")

            elif request_type == "get_artifact_content":
                # Request to get content of a specific artifact
                artifact_name = request_payload.get("artifact_name")
                if artifact_name:
                    content = self._get_project_artifact(artifact_name)
                    if content:
                        response_payload = {"artifact_name": artifact_name, "content": content}
                        response_type = "artifact_content_response"
                        logger.info(f"Prepared artifact content response for '{artifact_name}' for agent '{requester_agent_id}'.")
                    else:
                        response_payload = {"error": f"Artifact '{artifact_name}' not found."}
                        response_type = "artifact_not_found"
                        logger.warning(f"Artifact '{artifact_name}' not found for agent '{requester_agent_id}'.")
                else:
                    response_payload = {"error": "Missing 'artifact_name' in request payload."}
                    response_type = "invalid_request"
                    logger.warning(f"Missing 'artifact_name' in request payload from agent '{requester_agent_id}'.")
            else:
                response_payload = {"error": f"Unknown request type: {request_type}"}
                response_type = "unknown_request_type"
                logger.warning(f"Unknown request type '{request_type}' from agent '{requester_agent_id}'.")

            # Publish the response back to the system
            self._publish_response(requester_agent_id, response_type, response_payload, message.message_id)
            message.ack() # Acknowledge the message to remove it from the subscription

        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from message {message.message_id}: {e}", exc_info=True)
            message.nack() # Negatively acknowledge the message for redelivery
        except Exception as e:
            logger.error(f"Error processing message {message.message_id}: {e}", exc_info=True)
            message.nack() # Negatively acknowledge the message for redelivery

    def _publish_response(self, target_agent_id: str, response_type: str, payload: dict, correlation_id: str = None):
        """
        Publishes a response message to the designated response topic.
        Includes attributes for routing and correlation.
        """
        message_data = json.dumps({
            "type": response_type,
            "payload": payload
        }).encode("utf-8")

        attributes = {
            "target_agent_id": target_agent_id, # Allows other agents to filter responses
            "source_agent_id": "context_agent", # Identifies the sender
        }
        if correlation_id:
            attributes["correlation_id"] = correlation_id # Links response to original request

        future = self.pubsub_publisher.publish(self.context_response_topic_path, message_data, **attributes)
        future.add_done_callback(lambda f: logger.info(f"Published response with message ID: {f.result()} "
                                                        f"for target '{target_agent_id}' (correlation: {correlation_id})"))

    def run(self):
        """
        Starts the Pub/Sub subscriber to continuously listen for incoming messages
        on its designated subscription. This method blocks indefinitely.
        """
        logger.info(f"ContextAgent starting to listen for messages on {self.context_agent_subscription_path}...")
        streaming_pull_future = self.pubsub_subscriber.subscribe(
            self.context_agent_subscription_path, callback=self._handle_context_request
        )
        with self.pubsub_subscriber:
            try:
                # Keep the main thread alive, so the callback can be executed.
                # This will block until the subscription is cancelled or an error occurs.
                streaming_pull_future.result()
            except TimeoutError:
                streaming_pull_future.cancel()  # Trigger the shutdown.
                streaming_pull_future.result()  # Block until the shutdown is complete.
            except KeyboardInterrupt:
                logger.info("ContextAgent received shutdown signal (KeyboardInterrupt).")
                streaming_pull_future.cancel()
                streaming_pull_future.result()
            except Exception as e:
                logger.error(f"ContextAgent encountered an unexpected error: {e}", exc_info=True)
                streaming_pull_future.cancel()
                streaming_pull_future.result()

        logger.info("ContextAgent stopped.")

# --- Main execution ---
if __name__ == "__main__":
    # Ensure GCP_PROJECT_ID environment variable is set for local execution
    # or when deployed to Google Cloud environments like Cloud Run.
    if not PROJECT_ID:
        logger.error("GCP_PROJECT_ID environment variable not set. Please set it before running the agent.")
        exit(1)

    agent = ContextAgent(PROJECT_ID)
    agent.run()