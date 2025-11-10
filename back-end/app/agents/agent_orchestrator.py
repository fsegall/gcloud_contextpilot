"""
Agent Orchestrator - Manages multi-agent system lifecycle and coordination
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates multiple agents in a workspace
    Manages initialization, coordination, and communication
    """

    def __init__(self, workspace_id: str, workspace_path: str):
        self.workspace_id = workspace_id
        self.workspace_path = Path(workspace_path)
        self.agents: Dict[str, Any] = {}
        self.agent_classes = {}

        # Import agent classes
        self._import_agent_classes()

    def _import_agent_classes(self):
        """Import all available agent classes"""
        self.agent_classes = {}

        # Try to import each agent individually
        agent_imports = [
            ("spec", "app.agents.spec_agent", "SpecAgent"),
            ("git", "app.agents.git_agent", "GitAgent"),
            ("development", "app.agents.development_agent", "DevelopmentAgent"),
            ("context", "app.agents.context_agent", "ContextAgent"),
            (
                "coach",
                "app.agents.coach_agent",
                "CoachAgent",
            ),  # Strategy Coach (unified)
            ("milestone", "app.agents.milestone_agent", "MilestoneAgent"),
        ]

        for agent_id, module_name, class_name in agent_imports:
            try:
                module = __import__(module_name, fromlist=[class_name])
                agent_class = getattr(module, class_name)
                self.agent_classes[agent_id] = agent_class
                logger.info(f"[Orchestrator] Loaded {agent_id} agent")
            except (ImportError, AttributeError) as e:
                logger.warning(f"[Orchestrator] Could not load {agent_id} agent: {e}")

        logger.info(
            f"[Orchestrator] Successfully loaded {len(self.agent_classes)} agent classes"
        )

    def initialize_agents(
        self, agent_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Initialize specified agents (or all available agents)

        Args:
            agent_ids: List of agent IDs to initialize, None for all

        Returns:
            Dict of initialized agents
        """
        if agent_ids is None:
            agent_ids = list(self.agent_classes.keys())

        initialized = {}

        for agent_id in agent_ids:
            if agent_id not in self.agent_classes:
                logger.warning(f"[Orchestrator] Unknown agent: {agent_id}")
                continue

            try:
                agent_class = self.agent_classes[agent_id]

                # Each agent has different constructor signatures
                if agent_id == "spec":
                    agent = agent_class(
                        workspace_path=str(self.workspace_path),
                        workspace_id=self.workspace_id,
                    )
                elif agent_id == "git":
                    agent = agent_class(workspace_id=self.workspace_id)
                elif agent_id == "development":
                    # Development agent needs workspace_path and workspace_id
                    agent = agent_class(
                        workspace_path=str(self.workspace_path),
                        workspace_id=self.workspace_id,
                    )
                elif agent_id == "context":
                    # ContextAgent only needs project_id
                    project_id = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
                    if project_id:
                        agent = agent_class(project_id=project_id)
                    else:
                        logger.warning(f"[Orchestrator] Cannot initialize {agent_id} agent: GCP_PROJECT_ID not set")
                        continue
                elif agent_id in ["coach", "milestone"]:
                    # These agents may need workspace_path and workspace_id
                    try:
                        agent = agent_class(
                            workspace_path=str(self.workspace_path),
                            workspace_id=self.workspace_id,
                        )
                    except TypeError:
                        # Try with just workspace_id if workspace_path not supported
                        logger.warning(f"[Orchestrator] {agent_id} agent doesn't support workspace_path, trying workspace_id only")
                        agent = agent_class(workspace_id=self.workspace_id)
                else:
                    # Default: try both parameters
                    agent = agent_class(
                        workspace_id=self.workspace_id,
                        workspace_path=str(self.workspace_path),
                    )

                self.agents[agent_id] = agent
                initialized[agent_id] = agent

                # Initialize agent metrics with baseline activity
                if hasattr(agent, "state") and "metrics" in agent.state:
                    # Agent already has metrics from state file
                    pass
                else:
                    # Set initial metrics for newly created agents
                    if hasattr(agent, "state"):
                        if "metrics" not in agent.state:
                            agent.state["metrics"] = {
                                "events_processed": 0,
                                "events_published": 0,
                                "errors": 0,
                                "initialized": True,
                            }

                logger.info(f"[Orchestrator] Initialized {agent_id} agent")
            except Exception as e:
                logger.error(f"[Orchestrator] Failed to initialize {agent_id}: {e}")

        return initialized

    def get_agent_perspectives(self, topic: str) -> List[Dict[str, str]]:
        """
        Collect perspectives from all initialized agents about a topic
        Uses parallel processing for faster responses

        Args:
            topic: Discussion topic

        Returns:
            List of agent perspectives with agent_id, role, and response
        """
        from concurrent.futures import (
            ThreadPoolExecutor,
            TimeoutError as FutureTimeoutError,
        )
        import time

        perspectives = []

        # Quick return if no agents
        if not self.agents:
            return perspectives

        # Agent role descriptions (only for existing agents)
        agent_roles = {
            "spec": {
                "emoji": "📋",
                "name": "Spec Agent",
                "expertise": "technical specifications, requirements, and validation",
            },
            "git": {
                "emoji": "🔧",
                "name": "Git Agent",
                "expertise": "version control, code changes, and automation",
            },
            "strategy": {
                "emoji": "🧠",
                "name": "Strategy Agent",
                "expertise": "planning, architecture, and long-term vision",
            },
            "development": {
                "emoji": "💻",
                "name": "Development Agent",
                "expertise": "code implementation, debugging, and technical problem-solving",
            },
            "context": {
                "emoji": "📚",
                "name": "Context Agent",
                "expertise": "codebase understanding, file indexing, and context management",
            },
            "coach": {
                "emoji": "🎯",
                "name": "Coach Agent",
                "expertise": "code quality, best practices, and technical guidance",
            },
            "milestone": {
                "emoji": "🏁",
                "name": "Milestone Agent",
                "expertise": "project tracking, progress monitoring, and goal management",
            },
        }

        def get_single_perspective(agent_id, agent):
            """Get perspective from a single agent"""
            role_info = agent_roles.get(
                agent_id,
                {
                    "emoji": "🤖",
                    "name": f"{agent_id.title()} Agent",
                    "expertise": "system operations",
                },
            )

            try:
                # Try to get agent's perspective (if method exists)
                if hasattr(agent, "get_perspective"):
                    response = agent.get_perspective(topic)
                else:
                    # Generate LLM-powered perspective based on agent role and context
                    response = self._generate_llm_perspective(
                        agent_id, topic, role_info, agent
                    )

                logger.info(f"[Orchestrator] Got perspective from {agent_id}")
                return {
                    "agent_id": agent_id,
                    "emoji": role_info["emoji"],
                    "name": role_info["name"],
                    "expertise": role_info["expertise"],
                    "response": response,
                }
            except Exception as e:
                logger.error(
                    f"[Orchestrator] Failed to get perspective from {agent_id}: {e}"
                )
                # Add fallback perspective even on error
                return {
                    "agent_id": agent_id,
                    "emoji": role_info["emoji"],
                    "name": role_info["name"],
                    "expertise": role_info["expertise"],
                    "response": f"[Currently analyzing '{topic}' from {role_info['expertise']} perspective...]",
                }

        # Process agents in parallel for faster execution
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(get_single_perspective, agent_id, agent): agent_id
                for agent_id, agent in self.agents.items()
            }

            for future in futures:
                try:
                    perspective = future.result(
                        timeout=25
                    )  # 25 second timeout per agent (to allow for 20s API call)
                    perspectives.append(perspective)
                except FutureTimeoutError:
                    agent_id = futures[future]
                    logger.warning(
                        f"[Orchestrator] Timeout getting perspective from {agent_id}"
                    )
                    perspectives.append(
                        {
                            "agent_id": agent_id,
                            "emoji": "⏱️",
                            "name": f"{agent_id.title()} Agent",
                            "expertise": "analysis in progress",
                            "response": f"[Timeout analyzing '{topic}']",
                        }
                    )
                except Exception as e:
                    logger.error(f"[Orchestrator] Error in parallel processing: {e}")

        return perspectives

    def _generate_llm_perspective(
        self, agent_id: str, topic: str, role_info: Dict, agent: Any
    ) -> str:
        """Generate LLM-powered perspective based on agent's role and context"""
        import os

        gemini_api_key = os.getenv("GOOGLE_API_KEY")
        if not gemini_api_key:
            logger.warning(
                f"[Orchestrator] No GOOGLE_API_KEY for {agent_id} perspective"
            )
            return self._generate_default_perspective(
                agent_id, topic, role_info["expertise"]
            )

        logger.info(f"[Orchestrator] Generating LLM perspective for {agent_id}...")

        try:
            import requests

            # Collect agent context
            agent_context = self._collect_agent_context(agent_id, agent)
            logger.debug(
                f"[Orchestrator] Agent context for {agent_id}: {agent_context[:100]}..."
            )

            # Build prompt with agent's role and context
            prompt = f"""You are {role_info['name']}, an expert in {role_info['expertise']}.

Context about this agent:
{agent_context}

Topic: "{topic}"

Give a brief (2-3 sentences), specific, actionable perspective from your role. Focus on what you would do or recommend based on your expertise. Be concrete and avoid generic statements."""

            # Use latest Gemini 2.5 Flash Preview for best speed
            url = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            headers = {"Content-Type": "application/json"}

            logger.info(f"[Orchestrator] Calling Gemini API for {agent_id}...")
            response = requests.post(
                f"{url}?key={gemini_api_key}",
                json=payload,
                headers=headers,
                timeout=20,  # Increased timeout for Gemini API
            )

            logger.info(
                f"[Orchestrator] Gemini API response for {agent_id}: {response.status_code}"
            )

            if response.status_code == 200:
                result = response.json()
                perspective = (
                    result.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                    .strip()
                )
                if perspective:
                    logger.info(
                        f"[Orchestrator] Got LLM perspective for {agent_id}: {perspective[:50]}..."
                    )
                    return perspective
                else:
                    logger.warning(
                        f"[Orchestrator] Empty perspective from LLM for {agent_id}"
                    )
            else:
                logger.warning(
                    f"[Orchestrator] Gemini API error for {agent_id}: {response.status_code} - {response.text[:200]}"
                )

        except Exception as e:
            logger.error(
                f"[Orchestrator] LLM perspective generation failed for {agent_id}: {str(e)}"
            )
            import traceback

            logger.error(f"[Orchestrator] Traceback: {traceback.format_exc()}")

        # Fallback to default
        logger.info(f"[Orchestrator] Using fallback perspective for {agent_id}")
        return self._generate_default_perspective(
            agent_id, topic, role_info["expertise"]
        )

    def _collect_agent_context(self, agent_id: str, agent: Any) -> str:
        """Collect relevant context from agent's state and workspace"""
        context_parts = []

        # Agent state info
        if hasattr(agent, "state"):
            state = agent.state

            # Metrics
            if "metrics" in state:
                metrics = state["metrics"]
                context_parts.append(
                    f"My metrics: {metrics.get('events_processed', 0)} events processed, {metrics.get('events_published', 0)} published, {metrics.get('errors', 0)} errors"
                )

            # Memory/learnings
            if "memory" in state:
                memory_items = list(state["memory"].keys())[:3]  # First 3 items
                if memory_items:
                    context_parts.append(f"Recent memory: {', '.join(memory_items)}")

        # Workspace info
        workspace_files = []
        try:
            import os

            workspace_path = str(self.workspace_path)
            if os.path.exists(workspace_path):
                # List some key files
                for root, dirs, files in os.walk(workspace_path):
                    # Only top level
                    workspace_files = [f for f in files[:5] if not f.startswith(".")]
                    break

                if workspace_files:
                    context_parts.append(
                        f"Workspace files: {', '.join(workspace_files)}"
                    )
        except Exception as e:
            logger.debug(f"[Orchestrator] Could not read workspace for {agent_id}: {e}")

        # Agent-specific context
        if agent_id == "spec":
            context_parts.append(
                "I maintain technical specifications and requirements documentation"
            )
        elif agent_id == "git":
            context_parts.append("I monitor version control, commits, and code changes")
        elif agent_id == "strategy":
            context_parts.append(
                "I focus on architectural decisions and long-term planning"
            )

        return (
            "\n".join(context_parts)
            if context_parts
            else "No specific context available"
        )

    def _generate_default_perspective(
        self, agent_id: str, topic: str, expertise: str
    ) -> str:
        """Generate a default perspective when LLM is unavailable"""
        templates = {
            "spec": f"For '{topic}', we need clear specifications defining requirements and validation criteria for successful implementation.",
            "git": f"About '{topic}', I suggest implementing automated detection via git hooks and workflow automation to streamline the process.",
            "strategy": f"Strategically addressing '{topic}' requires a systematic approach with clear long-term planning and architectural consideration.",
            "development": f"To address '{topic}', I would analyze the codebase, identify root causes, and implement targeted fixes with proper testing.",
            "context": f"For '{topic}', I would review relevant code files, understand dependencies, and ensure proper context is maintained across the system.",
            "coach": f"Regarding '{topic}', I recommend following best practices, ensuring code quality, and implementing proper error handling and testing.",
            "milestone": f"To tackle '{topic}', I would break it down into measurable milestones, track progress, and ensure timely completion.",
        }

        return templates.get(
            agent_id,
            f"From my {expertise} perspective, '{topic}' requires careful consideration and systematic implementation.",
        )

    def get_agent_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Collect current metrics from all initialized agents

        Returns:
            Dict mapping agent_id to their current metrics
        """
        metrics = {}

        for agent_id, agent in self.agents.items():
            try:
                # Get metrics from agent state
                if hasattr(agent, "state"):
                    metrics[agent_id] = agent.state.get("metrics", {})
                elif hasattr(agent, "get_metrics"):
                    metrics[agent_id] = agent.get_metrics()
                else:
                    # Default metrics structure
                    metrics[agent_id] = {
                        "events_processed": 0,
                        "events_published": 0,
                        "errors": 0,
                        "status": "active",
                    }

                logger.info(f"[Orchestrator] Retrieved metrics from {agent_id}")
            except Exception as e:
                logger.error(
                    f"[Orchestrator] Failed to get metrics from {agent_id}: {e}"
                )
                metrics[agent_id] = {"error": str(e)}

        return metrics

    def shutdown_agents(self):
        """Gracefully shutdown all agents"""
        for agent_id, agent in self.agents.items():
            try:
                if hasattr(agent, "shutdown"):
                    agent.shutdown()
                logger.info(f"[Orchestrator] Shutdown {agent_id}")
            except Exception as e:
                logger.error(f"[Orchestrator] Error shutting down {agent_id}: {e}")

        self.agents.clear()
