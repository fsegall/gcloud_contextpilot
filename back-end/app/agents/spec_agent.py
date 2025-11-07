import os
import json
import logging
import asyncio
import datetime
from concurrent.futures import TimeoutError

# Google Cloud Clients
from google.cloud import pubsub_v1
from google.cloud import firestore
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SpecAgent:
    """
    The SpecAgent is responsible for generating detailed specifications based on
    incoming requests, typically related to development tasks, bug fixes, or
    feature enhancements. It leverages Gemini for AI-powered specification generation
    and interacts with Pub/Sub for event communication and Firestore for state persistence.

    This agent listens for 'specification_request' events and, upon receiving one,
    generates a comprehensive specification document and publishes a 'specs_generated' event.
    """

    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID environment variable not set.")

        self.incoming_subscription_id = os.getenv("SPEC_AGENT_INCOMING_SUBSCRIPTION_ID")
        self.outgoing_topic_id = os.getenv("SPEC_AGENT_OUTGOING_TOPIC_ID")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

        if not self.incoming_subscription_id:
            raise ValueError("SPEC_AGENT_INCOMING_SUBSCRIPTION_ID environment variable not set.")
        if not self.outgoing_topic_id:
            raise ValueError("SPEC_AGENT_OUTGOING_TOPIC_ID environment variable not set.")
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")

        self.pubsub_subscriber_client = pubsub_v1.SubscriberClient()
        self.pubsub_publisher_client = pubsub_v1.PublisherClient()
        self.firestore_client = firestore.Client(project=self.project_id)

        self.incoming_subscription_path = self.pubsub_subscriber_client.subscription_path(
            self.project_id, self.incoming_subscription_id
        )
        self.outgoing_topic_path = self.pubsub_publisher_client.topic_path(
            self.project_id, self.outgoing_topic_id
        )

        self._configure_gemini()
        logger.info(f"SpecAgent initialized for project: {self.project_id}")
        logger.info(f"Listening on subscription: {self.incoming_subscription_path}")
        logger.info(f"Publishing to topic: {self.outgoing_topic_path}")

    def _configure_gemini(self):
        """Configures the Gemini API client."""
        genai.configure(api_key=self.gemini_api_key)
        self.gemini_model = genai.GenerativeModel('gemini-pro')
        logger.info("Gemini API configured.")

    def _generate_specifications(self, event_data: dict) -> dict:
        """
        Generates specifications using the Gemini model based on the provided event data.
        """
        problem_description = event_data.get("description", "No description provided.")
        context = event_data.get("context", "General project context.")
        request_id = event_data.get("request_id", "unknown")

        prompt = (
            f"You are an expert software architect and technical writer. "
            f"Your task is to create clear, concise, and actionable technical specifications "
            f"for a development task within the ContextPilot project. "
            f"The project is an AI-powered context management system. "
            f"Focus on defining requirements, acceptance criteria, and potential implementation notes. "
            f"The output should be in Markdown format.\n\n"
            f"**Problem/Request:** {problem_description}\n\n"
            f"**Context:** {context}\n\n"
            f"**Task:** Generate detailed specifications for this problem. "
            f"Include:\n"
            f"1.  **High-Level Goal:** What is the main objective?\n"
            f"2.  **Functional Requirements:** What should the system do?\n"
            f"3.  **Non-Functional Requirements:** Performance, security, reliability, etc.\n"
            f"4.  **Acceptance Criteria:** How will we know it's done correctly? (SMART criteria)\n"
            f"5.  **Potential Implementation Notes/Considerations:** (Optional, brief suggestions)\n"
            f"6.  **Affected Components/Agents:** Which parts of ContextPilot are involved?\n"
            f"7.  **Example Scenario/Input-Output:** (If applicable)\n\n"
            f"Ensure the specifications are suitable for a developer to implement."
        )

        logger.info(f"Generating specifications for request_id: {request_id}")
        try:
            response = self.gemini_model.generate_content(prompt)
            spec_content = response.text
            logger.info(f"Specifications generated for request_id: {request_id}")
            return {
                "request_id": request_id,
                "status": "generated",
                "spec_content": spec_content,
                "timestamp": firestore.SERVER_TIMESTAMP, # Firestore will set the server timestamp
                "source_event": event_data,
            }
        except Exception as e:
            logger.error(f"Error generating specifications for request_id {request_id}: {e}")
            return {
                "request_id": request_id,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.datetime.utcnow().isoformat(), # Use current UTC time for failed events
                "source_event": event_data,
            }

    def _store_specification(self, specification_data: dict):
        """Stores the generated specification in Firestore."""
        request_id = specification_data.get("request_id")
        if not request_id:
            logger.error("Cannot store specification: 'request_id' missing.")
            return

        try:
            doc_ref = self.firestore_client.collection("specifications").document(request_id)
            doc_ref.set(specification_data)
            logger.info(f"Specification for request_id '{request_id}' stored in Firestore.")
        except Exception as e:
            logger.error(f"Error storing specification for request_id '{request_id}': {e}")

    def _publish_event(self, event_type: str, payload: dict):
        """Publishes an event to the outgoing Pub/Sub topic."""
        try:
            payload["event_type"] = event_type
            data = json.dumps(payload).encode("utf-8")
            future = self.pubsub_publisher_client.publish(self.outgoing_topic_path, data)
            message_id = future.result()
            logger.info(f"Published '{event_type}' event with message ID: {message_id}")
        except Exception as e:
            logger.error(f"Error publishing event '{event_type}': {e}")

    def _callback(self, message: pubsub_v1.subscriber.message.Message):
        """
        Callback function executed for each message received from Pub/Sub.
        This is the core logic for processing incoming requests.
        """
        logger.info(f"Received message: {message.message_id}")
        try:
            event_data = json.loads(message.data.decode("utf-8"))
            event_type = event_data.get("event_type")
            request_id = event_data.get("request_id", message.message_id) # Use message_id as fallback

            logger.info(f"Processing event_type: {event_type} for request_id: {request_id}")

            if event_type == "specification_request":
                # This handles scenarios like "Seven unit test are failing. Can we fix it?"
                # where a clear specification is needed.
                generated_spec = self._generate_specifications(event_data)
                self._store_specification(generated_spec)

                if generated_spec["status"] == "generated":
                    # Notify other agents (e.g., Development Agent) that specs are ready
                    self._publish_event(
                        "specs_generated",
                        {
                            "request_id": request_id,
                            "spec_id": request_id, # Assuming spec_id is same as request_id for now
                            "status": "ready_for_development",
                            "description": event_data.get("description"),
                            "timestamp": datetime.datetime.utcnow().isoformat(), # Use current UTC time for the outgoing event
                        }
                    )
                else:
                    logger.warning(f"Specification generation failed for request_id: {request_id}. Not publishing 'specs_generated' event.")
            else:
                logger.info(f"Unhandled event type: {event_type}. Message {message.message_id} acknowledged.")

            message.ack()
            logger.info(f"Message {message.message_id} acknowledged.")

        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from message {message.message_id}: {e}")
            message.nack() # Negative acknowledge to retry later
        except Exception as e:
            logger.error(f"Error processing message {message.message_id}: {e}")
            message.nack() # Negative acknowledge to retry later

    def start_listening(self, timeout: int = None):
        """
        Starts the Pub/Sub subscriber to listen for incoming specification requests.
        This method blocks indefinitely unless a timeout is provided.
        """
        streaming_pull_future = self.pubsub_subscriber_client.subscribe(
            self.incoming_subscription_path, callback=self._callback
        )
        logger.info(f"SpecAgent is listening for messages on {self.incoming_subscription_path}...")

        try:
            # The result() method will block indefinitely if timeout is None.
            # In a Cloud Run service, this is typically desired.
            streaming_pull_future.result(timeout=timeout)
        except TimeoutError:
            logger.warning("Pub/Sub listener timed out. Shutting down SpecAgent.")
            streaming_pull_future.cancel()
            self.pubsub_subscriber_client.close()
            # Wait for the future to complete to ensure all callbacks are finished
            streaming_pull_future.result()
        except Exception as e:
            logger.error(f"SpecAgent listener encountered an error: {e}")
            streaming_pull_future.cancel()
            self.pubsub_subscriber_client.close()
            streaming_pull_future.result()
        finally:
            self.pubsub_subscriber_client.close()
            self.pubsub_publisher_client.close()
            logger.info("SpecAgent Pub/Sub clients closed.")

# Entry point for the agent (e.g., if run as a standalone service or in Cloud Run)
if __name__ == "__main__":
    # Ensure all required environment variables are set before starting the agent.
    required_env_vars = [
        "GCP_PROJECT_ID",
        "SPEC_AGENT_INCOMING_SUBSCRIPTION_ID",
        "SPEC_AGENT_OUTGOING_TOPIC_ID",
        "GEMINI