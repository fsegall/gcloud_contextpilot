# back-end/app/agents/context_agent.py

import os
import json
import logging
from concurrent.futures import TimeoutError

from google.cloud import pubsub_v1
from google.cloud import firestore

# Configure logging for the agent
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Environment variables for Google Cloud Project ID and Pub/Sub topics
# In a Cloud Run environment, GCP_PROJECT_ID is automatically available.
# For local development, ensure this environment variable is set.
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
if not PROJECT_ID:
    logger.warning("GCP_PROJECT_ID environment variable not set. Using 'your-gcp-project-id' as placeholder.")
    # This placeholder is primarily for local testing setup; in production, it must be set.
    PROJECT_ID = "your-gcp-project-id"

# Define Pub/Sub topic and subscription names
CONTEXT_REQUESTS_TOPIC_NAME = "contextpilot-context-requests"
CONTEXT_RESPONSES_TOPIC_NAME = "contextpilot-context-updates"
CONTEXT_SUBSCRIPTION_ID = "contextpilot-context-agent-subscription"

# Full Pub/Sub topic and subscription paths
CONTEXT_REQUESTS_TOPIC_PATH = f"projects/{PROJECT_ID}/topics/{CONTEXT_REQUESTS_TOPIC_NAME}"
CONTEXT_RESPONSES_TOPIC_PATH = f"projects/{PROJECT_ID}/topics/{CONTEXT_RESPONSES_TOPIC_NAME}"


class ContextAgent:
    """
    The ContextAgent is a core component of the ContextPilot multi-agent system.
    It is responsible for managing, retrieving, and providing relevant context
    to other agents. It listens for context requests via Pub/Sub, aggregates
    information from various sources (e.g., Firestore, project artifacts),
    and publishes the requested context back to the system.
    """

    def __init__(self):
        """
        Initializes the ContextAgent with Pub/Sub subscriber and publisher clients,
        and a Firestore client. It also ensures that necessary Pub/Sub resources
        (topics and subscription) exist.
        """
        self.subscriber = pubsub_v1.SubscriberClient()
        self.publisher = pubsub_v1.PublisherClient()
        self.firestore_db = firestore.Client()
        self.subscription_path = self.subscriber.subscription_path(
            PROJECT_ID, CONTEXT_SUBSCRIPTION_ID
        )
        logger.info(f"ContextAgent initialized for project: {PROJECT_ID}")

        # Ensure Pub/Sub topics and subscription exist upon initialization
        self._ensure_pubsub_resources()

    def _ensure_pubsub_resources(self):
        """
        Ensures that the necessary Pub/Sub topics and the agent's subscription
        exist. This makes the agent more robust to initial deployments or
        resource deletions.
        """
        # Ensure CONTEXT_REQUESTS_TOPIC exists
        try:
            self.publisher.get_topic(request={"topic": CONTEXT_REQUESTS_TOPIC_PATH})
            logger.info(f"Pub/Sub Topic '{CONTEXT_REQUESTS_TOPIC_NAME}' already exists.")
        except Exception:
            self.publisher.create_topic(request={"name": CONTEXT_REQUESTS_TOPIC_PATH})
            logger.info(f"Pub/Sub Topic '{CONTEXT_REQUESTS_TOPIC_NAME}' created.")

        # Ensure CONTEXT_RESPONSES_TOPIC exists
        try:
            self.publisher.get_topic(request={"topic": CONTEXT_RESPONSES_TOPIC_PATH})
            logger.info(f"Pub/Sub Topic '{CONTEXT_RESPONSES_TOPIC_NAME}' already exists.")
        except Exception:
            self.publisher.create_topic(request={"name": CONTEXT_RESPONSES_TOPIC_PATH})
            logger.info(f"Pub/Sub Topic '{CONTEXT_RESPONSES_TOPIC_NAME}' created.")

        # Ensure the ContextAgent's subscription exists for CONTEXT_REQUESTS_TOPIC
        try:
            self.subscriber.get_subscription(request={"subscription": self.subscription_path})
            logger.info(f"Pub/Sub Subscription '{CONTEXT_SUBSCRIPTION_ID}' already exists.")
        except Exception:
            self.subscriber.create_subscription(
                request={"name": self.subscription_path, "topic": CONTEXT_REQUESTS_TOPIC_PATH}
            )
            logger.info(f"Pub/Sub Subscription '{CONTEXT_SUBSCRIPTION_ID}' created for topic '{CONTEXT_REQUESTS_TOPIC_NAME}'.")

    def start_listening(self):
        """
        Starts listening for messages on the dedicated context requests subscription.
        This method is blocking and will keep the agent running to process incoming
        context requests.
        """
        streaming_pull_future = self.subscriber.subscribe(
            self.subscription_path, callback=self._callback
        )
        logger.info(f"ContextAgent is listening for messages on {self.subscription_path}...")

        try:
            # Keep the main thread alive to allow the callback to run in a separate thread.
            streaming_pull_future.result()
        except TimeoutError:
            streaming_pull_future.cancel()  # Trigger the shutdown.
            streaming_pull_future.result()  # Block until the shutdown is complete.
        except Exception as e:
            logger.error(f"ContextAgent encountered an error while listening: {e}", exc_info=True)
            streaming_pull_future.cancel()
            streaming_pull_future.result()
        finally:
            self.subscriber.close()
            logger.info("ContextAgent subscriber closed.")

    def _callback(self, message: pubsub_v1.subscriber.message.Message):
        """
        Callback function executed when a new message is received on the
        context requests subscription. It decodes the message, processes
        the context request, and publishes a response.
        """
        logger.info(f"Received message ID: {message.message_id}")
        try:
            # Decode message data from bytes to JSON
            data = json.loads(message.data.decode("utf-8"))
            logger.debug(f"Decoded message data: {data}")

            # Extract metadata from message attributes
            request_id = message.attributes.get("request_id", "no-request-id")
            agent_id = message.attributes.get("agent_id", "unknown-agent")
            context_type = data.get("context_type", "general")
            query = data.get("query", {})

            logger.info(
                f"Processing context request from agent '{agent_id}' "
                f"(request_id: {request_id}) for type '{context_type}' with query: {query}"
            )

            # Fetch the requested context
            context_data = self.get_context(context_type, query)

            # Publish the context response back to the system
            self.publish_context(agent_id, request_id, context_data)

            # Acknowledge the message to remove it from the subscription
            message.ack()
            logger.info(f"Message {message.message_id} acknowledged.")

        except json.JSONDecodeError:
            logger.error(f"Failed to decode message data as JSON: {message.data}", exc_info=True)
            message.nack()  # Negative acknowledge to retry if it's a transient issue
        except Exception as e:
            logger.error(f"Error processing message {message.message_id}: {e}", exc_info=True)
            message.nack()  # Negative acknowledge

    def get_context(self, context_type: str, query: dict) -> dict:
        """
        Retrieves context based on the specified `context_type` and `query`.
        This method is the core logic for context aggregation and retrieval,
        which can involve querying Firestore, reading project files, or
        interacting with other services (e.g., Gemini for synthesis).

        Args:
            context_type: A string indicating the type of context requested (e.g., "project_scope", "agent_status").
            query: A dictionary containing specific parameters for the context request.

        Returns:
            A dictionary containing the retrieved context and status.
        """
        logger.info(f"Attempting to fetch context for type: '{context_type}' with query: {query}")
        retrieved_context = {"status": "success", "context": {}, "message": "Context retrieved successfully."}

        if context_type == "project_scope":
            # Example: Fetch project scope from Firestore
            try:
                doc_ref = self.firestore_db.collection("project_artifacts").document("project_scope")
                doc = doc_ref.get()
                if doc.exists:
                    retrieved_context["context"] = doc.to_dict()
                    logger.info(f"Retrieved project scope from Firestore.")
                else:
                    retrieved_context["status"] = "not_found"
                    retrieved_context["message"] = "Project scope document not found in Firestore."
                    logger.warning(retrieved_context["message"])
            except Exception as e:
                retrieved_context["status"] = "error"
                retrieved_context["message"] = f"Error fetching project scope from Firestore: {e}"
                logger.error(retrieved_context["message"], exc_info=True)

        elif context_type == "agent_status":
            # This would typically involve querying a 'agent_status' collection in Firestore
            # or subscribing to an 'agent-status-updates' topic.
            # For now, providing a simulated response.
            target_agent_id = query.get("agent_id")
            if target_agent_id:
                # In a real system, query Firestore for agent status or a dedicated service
                # For demonstration, simulate a response
                simulated_status = {
                    "agent_id": target_agent_id,
                    "status": "active" if target_agent_id not in ["spec", "development", "context", "coach", "milestone"] else "idle",
                    "last_seen": "2025-11-07T17:30:00Z", # Placeholder
                    "current_task": "None" if target_agent_id in ["spec", "development", "context", "coach", "milestone"] else "Processing request"
                }
                retrieved_context["context"] = simulated_status
                logger.info(f"Simulated agent status for '{target_agent_id}': {simulated_status['status']}")
            else:
                retrieved_context["status"] = "bad_request"
                retrieved_context["message"] = "Agent ID required for 'agent_status' context type."
                logger.warning(retrieved_context["message"])

        elif context_type == "project_overview":
            # Example of combining multiple sources or providing general project info
            retrieved_context["context"] = {
                "project_name": "ContextPilot",
                "phase": "Hackathon + Product Launch",
                "goal": "AI-powered context management with multi-agent system",
                "stack": "Cloud Run + Firestore + Pub/Sub + Gemini + VSCode Extension",
                "general_notes": "This context is aggregated from various project artifacts."
            }
            logger.info("Provided general project overview context.")

        else:
            # Default response for unhandled context types
            retrieved_context["status"] = "unsupported_type"
            retrieved_context["message"] = f"Unsupported context type requested: '{context_type}'."
            retrieved_context["context"] = {
                "requested_type": context_type,
                "requested_query": query,
                "available_types": ["project_scope", "agent_status", "project_overview"]
            }
            logger.warning(retrieved_context["message"])

        return retrieved_context

    def publish_context(self, target_agent_id: str, request_id: str, context_data: dict):
        """
        Publishes the retrieved context as a response to the system.
        Other agents can subscribe to the CONTEXT_RESPONSES_TOPIC to receive
        these updates.

        Args:
            target_agent_id: The ID of the agent that originally requested the context.
            request_id: The unique ID of the original context request.
            context_data: A dictionary containing the context to be published.
        """
        try:
            message_data = json.dumps(context_data).encode("utf-8")
            future = self.publisher.publish(
                CONTEXT_RESPONSES_TOPIC_PATH,
                message_data,
                agent_id=target_agent_id,
                request_id=request_id,
                context_source="ContextAgent",
                context_type=context_data.get("context", {}).get("requested_type", "unknown")
            )
            message_id = future.result()
            logger.info(
                f"Published context response (ID: {message_id}) for request '{request_id}' "
                f"to agent '{target_agent_id}' on topic '{CONTEXT_RESPONSES_TOPIC_NAME}'."
            )
        except Exception as e:
            logger.error(f"Failed to publish context for request '{request_id}': {e}", exc_info=True)


# Entry point for running the ContextAgent
if __name__ == "__main__":
    # This block is for local testing and demonstration purposes.
    # In a Cloud Run environment, the agent would typically be started by the
    # application server (e.g., Flask/FastAPI) that hosts this agent.

    # --- Local Firestore Setup (for testing convenience) ---
    # This ensures a 'project_scope' document exists for testing the get_context method.
    try:
        db_client = firestore.Client()
        project_scope_doc_ref = db_client.collection("project_artifacts").document("project_scope")
        if not project_scope_doc_ref.get().exists:
            project_scope_doc_ref.set({
                "title": "ContextPilot Project Scope",
                "content": """The ContextPilot project aims to revolutionize developer productivity by providing an AI-powered context management system. It leverages a multi-agent architecture to understand, maintain, and provide relevant context across various development tasks. Key features include intelligent context retrieval, proactive context suggestions, and seamless integration with developer tools like VSCode. The project is currently in the hackathon and product launch phase, focusing on core functionality and fine-tuning.
                The system relies on Cloud Run for scalable execution, Firestore for state persistence, Pub/Sub for inter-agent communication, and Gemini for advanced AI capabilities. The VSCode Extension serves as the primary user interface.""",
                "last_updated": firestore.SERVER_TIMESTAMP
            })
            logger.info("Dummy 'project_scope' document created in Firestore for local testing.")
        else:
            logger.info("Firestore 'project_scope' document already exists.")
    except Exception as e:
        logger.error(f"Could not initialize or create dummy Firestore document: {e}")
        # If Firestore setup fails, the agent might still run but context retrieval will be limited.

    # --- Start the ContextAgent ---
    context_agent = ContextAgent()
    context_agent.start_listening()