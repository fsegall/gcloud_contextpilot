"""
Retrospective Agent - Agent Meetings & Cross-Agent Learning

Facilitates periodic retrospectives where agents:
- Share learnings from their work
- Identify coordination bottlenecks
- Propose process improvements
- Generate actionable insights

Triggered at cycle boundaries (e.g., end of milestone, manual trigger).
"""

import os
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

from app.agents.base_agent import BaseAgent
from app.services.event_bus import EventTypes, Topics, get_event_bus
from app.utils.workspace_manager import get_workspace_path
from app.agents.diff_generator import generate_unified_diff

logger = logging.getLogger(__name__)


class RetrospectiveAgent(BaseAgent):
    """
    Retrospective Agent - Facilitates cross-agent learning and reflection.

    Core responsibilities:
    - Collect agent metrics and learnings
    - Synthesize insights from multiple agents
    - Identify workflow improvements
    - Generate retrospective summaries
    - Propose action items
    """

    def __init__(self, workspace_id: str = "default", project_id: Optional[str] = None):
        super().__init__(
            workspace_id=workspace_id, agent_id="retrospective", project_id=project_id
        )

        # Subscribe to cycle completion events
        self.subscribe_to_event(EventTypes.MILESTONE_COMPLETE)

        logger.info(f"[RetrospectiveAgent] Initialized for workspace: {workspace_id}")

    async def handle_event(self, event_type: str, data: Dict) -> None:
        """Handle incoming events"""
        logger.info(f"[RetrospectiveAgent] Received event: {event_type}")

        try:
            if event_type == EventTypes.MILESTONE_COMPLETE:
                # Trigger retrospective on milestone completion
                await self.conduct_retrospective(trigger="milestone_complete")

            self.increment_metric("events_processed")
        except Exception as e:
            logger.error(f"[RetrospectiveAgent] Error handling {event_type}: {e}")
            self.increment_metric("errors")

    async def conduct_retrospective(
        self,
        trigger: str = "manual",
        gemini_api_key: Optional[str] = None,
        trigger_topic: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Conduct a retrospective meeting between agents.

        Args:
            trigger: What triggered the retrospective (e.g., "manual", "milestone_complete", "cycle_end")
            gemini_api_key: Optional Gemini API key for LLM synthesis
            trigger_topic: Optional topic for agent discussion

        Returns:
            Retrospective summary with agent insights and action items
        """
        logger.info(
            f"[RetrospectiveAgent] Starting retrospective (trigger: {trigger}, topic: {trigger_topic})"
        )

        # 1. Gather agent metrics
        agent_metrics = self._collect_agent_metrics()

        # 2. Gather agent learnings (from state files)
        agent_learnings = self._collect_agent_learnings()

        # 3. Analyze event history
        event_summary = self._analyze_event_history()

        # 4. Generate insights
        insights = self._generate_insights(
            agent_metrics, agent_learnings, event_summary, trigger, trigger_topic
        )

        # 5. Propose action items
        action_items = self._propose_action_items(insights)

        # 6. (Optional) Use LLM to synthesize a narrative
        llm_summary = None
        if gemini_api_key:
            llm_summary = await self._synthesize_with_llm(
                agent_metrics, agent_learnings, insights, action_items, gemini_api_key
            )

        # 7. Create retrospective report
        retrospective = {
            "retrospective_id": f"retro-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trigger": trigger,
            "topic": trigger_topic,  # Add discussion topic
            "agent_metrics": agent_metrics,
            "agent_learnings": agent_learnings,
            "event_summary": event_summary,
            "insights": insights,
            "action_items": action_items,
            "llm_summary": llm_summary,
        }

        # 8. Save retrospective to workspace
        self._save_retrospective(retrospective)

        # 9. Create improvement proposal from action items
        # Note: If code actions are implemented via Codespaces/Sandbox, those will create
        # their own proposals. We only create a "Recommendations" proposal for non-code actions.
        proposal_id = await self._create_improvement_proposal(retrospective)
        if proposal_id:
            retrospective["proposal_id"] = proposal_id
            logger.info(
                f"[RetrospectiveAgent] Created improvement proposal: {proposal_id}"
            )

        # 10. Publish retrospective event
        await self.publish_event(
            topic=Topics.RETROSPECTIVE_EVENTS,
            event_type="retrospective.summary.v1",
            data={
                "retrospective_id": retrospective["retrospective_id"],
                "workspace_id": self.workspace_id,
                "insights_count": len(insights),
                "action_items_count": len(action_items),
                "proposal_id": proposal_id,
            },
        )

        logger.info(
            f"[RetrospectiveAgent] Retrospective completed: {retrospective['retrospective_id']}"
        )
        return retrospective

    def _collect_agent_metrics(self) -> Dict[str, Dict]:
        """Collect metrics from all agents (live or from state files)"""
        metrics = {}

        # Try to use orchestrator for real-time metrics from live agents
        try:
            from app.agents.agent_orchestrator import AgentOrchestrator

            logger.info(f"[RetrospectiveAgent] Collecting metrics from workspace: {self.workspace_id}, path: {self.workspace_path}")
            
            orchestrator = AgentOrchestrator(
                workspace_id=self.workspace_id, workspace_path=self.workspace_path
            )

            # Initialize agents to get current state
            orchestrator.initialize_agents()

            # Get real-time metrics
            metrics = orchestrator.get_agent_metrics()

            logger.info(
                f"[RetrospectiveAgent] Collected live metrics from {len(metrics)} agents: {metrics}"
            )

            # Shutdown agents
            orchestrator.shutdown_agents()

            if metrics:
                return metrics
        except Exception as e:
            logger.warning(f"[RetrospectiveAgent] Could not get live metrics: {e}", exc_info=True)

        # Fallback to reading state files
        state_dir = Path(self.workspace_path) / ".agent_state"

        if not state_dir.exists():
            logger.warning(f"[RetrospectiveAgent] No agent state directory found at {state_dir}")
            return metrics

        logger.info(f"[RetrospectiveAgent] Reading metrics from state files in {state_dir}")
        for state_file in state_dir.glob("*_state.json"):
            agent_id = state_file.stem.replace("_state", "")
            try:
                with open(state_file, "r") as f:
                    state = json.load(f)
                    agent_metrics = state.get("metrics", {})
                    metrics[agent_id] = agent_metrics
                    logger.info(f"[RetrospectiveAgent] Loaded metrics for {agent_id}: {agent_metrics}")
            except Exception as e:
                logger.error(
                    f"[RetrospectiveAgent] Error reading {agent_id} state: {e}", exc_info=True
                )

        logger.info(f"[RetrospectiveAgent] Final collected metrics: {metrics}")
        return metrics

    def _collect_agent_learnings(self) -> Dict[str, Any]:
        """Collect learnings from agent memory"""
        learnings = {}
        state_dir = Path(self.workspace_path) / ".agent_state"

        if not state_dir.exists():
            return learnings

        for state_file in state_dir.glob("*_state.json"):
            agent_id = state_file.stem.replace("_state", "")
            try:
                with open(state_file, "r") as f:
                    state = json.load(f)
                    memory = state.get("memory", {})

                    # Extract learnings-related memory keys
                    agent_learnings = {
                        k: v
                        for k, v in memory.items()
                        if "learning" in k.lower() or "insight" in k.lower()
                    }

                    if agent_learnings:
                        learnings[agent_id] = agent_learnings
            except Exception as e:
                logger.error(
                    f"[RetrospectiveAgent] Error reading {agent_id} learnings: {e}"
                )

        return learnings

    def _analyze_event_history(self) -> Dict[str, Any]:
        """Analyze recent event bus activity"""
        try:
            event_bus = get_event_bus(
                project_id=self.project_id,
                force_in_memory=os.getenv("USE_PUBSUB", "false").lower() != "true",
            )

            # Only works with InMemoryEventBus (has get_event_log)
            if hasattr(event_bus, "get_event_log"):
                events = event_bus.get_event_log()

                # Analyze event patterns
                event_types = {}
                for event in events:
                    event_type = event.get("event_type", "unknown")
                    event_types[event_type] = event_types.get(event_type, 0) + 1

                return {
                    "total_events": len(events),
                    "event_types": event_types,
                    "most_active_agent": self._find_most_active_agent(events),
                }
            else:
                return {"note": "Event history only available in development mode"}
        except Exception as e:
            logger.error(f"[RetrospectiveAgent] Error analyzing events: {e}")
            return {}

    def _find_most_active_agent(self, events: List[Dict]) -> str:
        """Find which agent published the most events"""
        agent_counts = {}
        for event in events:
            source = event.get("source", "unknown")
            agent_counts[source] = agent_counts.get(source, 0) + 1

        if agent_counts:
            return max(agent_counts, key=agent_counts.get)
        return "none"

    def _generate_insights(
        self,
        agent_metrics: Dict,
        agent_learnings: Dict,
        event_summary: Dict,
        trigger: str = "manual",
        trigger_topic: str = None,
    ) -> List[str]:
        """Generate insights from collected data"""
        insights = []

        # Insight 1: Agent activity levels
        total_events_processed = sum(
            m.get("events_processed", 0) for m in agent_metrics.values()
        )
        if total_events_processed > 0:
            insights.append(
                f"Agents processed {total_events_processed} events in this cycle."
            )

        # Insight 2: Error rates
        total_errors = sum(m.get("errors", 0) for m in agent_metrics.values())
        if total_errors > 0:
            insights.append(
                f"⚠️ {total_errors} errors occurred across all agents. Review error logs."
            )

        # Insight 3: Agent collaboration
        if event_summary.get("total_events", 0) > 0:
            most_active = event_summary.get("most_active_agent", "unknown")
            insights.append(
                f"Most active agent: {most_active}. Strong cross-agent communication observed."
            )

        # Insight 4: Learnings present
        if agent_learnings:
            agents_with_learnings = list(agent_learnings.keys())
            insights.append(
                f"Agents {', '.join(agents_with_learnings)} recorded learnings for future reference."
            )

        # Insight 5: Idle agents (no events processed)
        idle_agents = [
            agent_id
            for agent_id, metrics in agent_metrics.items()
            if metrics.get("events_processed", 0) == 0
        ]
        if idle_agents:
            insights.append(
                f"⏸️ Idle agents: {', '.join(idle_agents)}. Consider reviewing their triggers."
            )

        # NEW: Agent Discussion about the Topic
        if trigger_topic:
            insights.extend(
                self._simulate_agent_discussion(trigger_topic, agent_metrics)
            )

        return insights

    def _simulate_agent_discussion(self, topic: str, agent_metrics: Dict) -> List[str]:
        """Generate agent perspectives using real agent instances or LLM"""
        discussion_insights = []

        # Try to use AgentOrchestrator for real agent perspectives
        try:
            from app.agents.agent_orchestrator import AgentOrchestrator

            logger.info("[RetrospectiveAgent] Initializing agents for discussion...")
            orchestrator = AgentOrchestrator(
                workspace_id=self.workspace_id, workspace_path=self.workspace_path
            )

            # Initialize all available agents
            orchestrator.initialize_agents()

            # Get perspectives from real agents
            perspectives = orchestrator.get_agent_perspectives(topic)

            # Require at least 3 agents for a proper discussion
            # If we have fewer, fall back to LLM-generated discussion
            if perspectives and len(perspectives) >= 3:
                logger.info(
                    f"[RetrospectiveAgent] Got {len(perspectives)} real agent perspectives"
                )
                for p in perspectives:
                    discussion_insights.append(
                        f"{p['emoji']} {p['name']}: {p['response']}"
                    )

                # Shutdown agents after discussion
                orchestrator.shutdown_agents()
                return discussion_insights
            else:
                logger.warning(
                    f"[RetrospectiveAgent] Only got {len(perspectives) if perspectives else 0} perspectives, need at least 3. Falling back to LLM"
                )
                # Shutdown any initialized agents
                orchestrator.shutdown_agents()
        except Exception as e:
            logger.warning(f"[RetrospectiveAgent] Orchestrator failed: {e}, trying LLM")

        # Fallback to LLM-generated perspectives
        return self._llm_agent_discussion(topic)

    def _llm_agent_discussion(self, topic: str) -> List[str]:
        """Generate agent perspectives using LLM - single call for all agents"""
        # Get API key
        gemini_api_key = os.getenv("GOOGLE_API_KEY")
        if not gemini_api_key:
            logger.warning(
                "[RetrospectiveAgent] No GOOGLE_API_KEY for agent discussion"
            )
            return self._fallback_agent_discussion(topic)

        try:
            import requests

            # Define agent roles and their expertise (matching actual registered agents)
            agents = [
                (
                    "📋 Spec Agent",
                    "technical specifications, requirements, and validation criteria",
                ),
                (
                    "🔧 Git Agent",
                    "version control, code changes, and commit automation",
                ),
                (
                    "💻 Development Agent",
                    "code implementation, proposal generation with AI",
                ),
                (
                    "📦 Context Agent",
                    "context management, knowledge indexing, and semantic retrieval",
                ),
                (
                    "🎯 Strategy Coach Agent",
                    "strategic direction, code quality analysis, and motivational progress tracking",
                ),
                (
                    "🏁 Milestone Agent",
                    "project progress tracking, deliverables, and completion criteria",
                ),
            ]

            # Build a comprehensive prompt for all agents at once
            prompt = f"""You are simulating a multi-agent development team discussing a topic.

Topic: "{topic}"

Generate a brief (1-2 sentence) perspective from EACH of the following agents:

{chr(10).join(f"{i+1}. {name} - Expertise: {expertise}" for i, (name, expertise) in enumerate(agents))}

Format your response as exactly 6 lines, one per agent, like:
📋 Spec Agent: [perspective]
🔧 Git Agent: [perspective]
💻 Development Agent: [perspective]
📦 Context Agent: [perspective]
🎯 Strategy Coach Agent: [perspective]
🏁 Milestone Agent: [perspective]

Make each perspective specific, actionable, and focused on that agent's role.
NO preamble, just the 6 lines."""

            # Single API call for all perspectives
            url = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            headers = {"Content-Type": "application/json"}

            logger.info("[RetrospectiveAgent] Calling Gemini for agent discussion...")
            logger.debug(
                f"[RetrospectiveAgent] API Key present: {bool(gemini_api_key)}"
            )

            response = requests.post(
                f"{url}?key={gemini_api_key}",
                json=payload,
                headers=headers,
                timeout=15,
            )

            logger.info(
                f"[RetrospectiveAgent] Gemini response status: {response.status_code}"
            )
            if response.status_code != 200:
                logger.error(
                    f"[RetrospectiveAgent] Gemini error response: {response.text[:500]}"
                )

            if response.status_code == 200:
                result = response.json()
                full_response = (
                    result.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                    .strip()
                )

                if full_response:
                    # Split into lines and clean up
                    perspectives = [
                        line.strip()
                        for line in full_response.split("\n")
                        if line.strip()
                    ]
                    logger.info(
                        f"[RetrospectiveAgent] Got {len(perspectives)} perspectives from LLM"
                    )
                    return (
                        perspectives
                        if len(perspectives) >= 3
                        else self._fallback_agent_discussion(topic)
                    )
                else:
                    logger.warning("[RetrospectiveAgent] Empty LLM response")
                    return self._fallback_agent_discussion(topic)
            else:
                logger.error(
                    f"[RetrospectiveAgent] LLM API error: {response.status_code}"
                )
                return self._fallback_agent_discussion(topic)

        except Exception as e:
            logger.error(f"[RetrospectiveAgent] LLM discussion generation failed: {e}")
            return self._fallback_agent_discussion(topic)

    def _fallback_agent_discussion(self, topic: str) -> List[str]:
        """Fallback hardcoded discussion when LLM is unavailable"""
        return [
            f"📋 Spec Agent: Regarding '{topic}', we need clear specifications for "
            "content inclusion criteria and validation rules.",
            f"🔧 Git Agent: For '{topic}', we should implement automated detection "
            "of new files and trigger updates on commits.",
            f"💻 Development Agent: I can generate implementation code for '{topic}' "
            "using AI analysis of existing patterns.",
            f"📦 Context Agent: '{topic}' relates to our context management strategy. "
            "We should ensure new content is properly indexed and tagged for retrieval.",
            f"🎯 Strategy Coach Agent: Let's align '{topic}' with our technical vision, "
            "analyze code quality implications, and track progress towards milestones.",
            f"🏁 Milestone Agent: '{topic}' indicates we should track completion "
            "as part of our milestone criteria and measure velocity impact.",
        ]

    def _propose_action_items(self, insights: List[str]) -> List[Dict[str, str]]:
        """Propose action items based on insights"""
        action_items = []

        # Parse insights for actionable items
        for insight in insights:
            if "errors" in insight.lower():
                action_items.append(
                    {
                        "priority": "high",
                        "action": "Review error logs and fix agent error handling",
                        "assigned_to": "developer",
                    }
                )

            if "idle agents" in insight.lower():
                action_items.append(
                    {
                        "priority": "medium",
                        "action": "Review event subscriptions for idle agents",
                        "assigned_to": "developer",
                    }
                )

            if "learnings" in insight.lower():
                action_items.append(
                    {
                        "priority": "low",
                        "action": "Document agent learnings in project retrospective notes",
                        "assigned_to": "team",
                    }
                )

        # Default action: continue with good performance
        if not action_items:
            action_items.append(
                {
                    "priority": "low",
                    "action": "Continue current workflow - agents performing well",
                    "assigned_to": "team",
                }
            )

        return action_items

    async def _synthesize_with_llm(
        self,
        agent_metrics: Dict,
        agent_learnings: Dict,
        insights: List[str],
        action_items: List[Dict],
        gemini_api_key: str,
    ) -> str:
        """Use Gemini to create a narrative retrospective summary"""
        try:
            import requests

            # Use Gemini REST API v1 (stable version)
            url = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-pro:generateContent"

            prompt = f"""
You are a retrospective facilitator for a multi-agent development system.

**Agent Metrics:**
{json.dumps(agent_metrics, indent=2)}

**Agent Learnings:**
{json.dumps(agent_learnings, indent=2)}

**Insights:**
{chr(10).join(f"- {i}" for i in insights)}

**Action Items:**
{json.dumps(action_items, indent=2)}

Please synthesize a concise retrospective summary in the following format:

## Retrospective Summary

**What went well:**
- [List 2-3 positive observations]

**What could be improved:**
- [List 2-3 areas for improvement]

**Key learnings:**
- [List 2-3 key insights]

**Next cycle focus:**
- [List 1-2 priorities for next cycle]

Keep the tone encouraging and constructive. Maximum 200 words.
"""

            # Call Gemini API
            payload = {"contents": [{"parts": [{"text": prompt}]}]}

            headers = {"Content-Type": "application/json"}

            response = requests.post(
                f"{url}?key={gemini_api_key}", json=payload, headers=headers, timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                text = (
                    result.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                )
                return text if text else "LLM synthesis unavailable."
            else:
                logger.error(
                    f"[RetrospectiveAgent] Gemini API error: {response.status_code} - {response.text}"
                )
                return "LLM synthesis unavailable. See raw insights above."

        except Exception as e:
            logger.error(f"[RetrospectiveAgent] LLM synthesis failed: {e}")
            return "LLM synthesis unavailable. See raw insights above."

    def _save_retrospective(self, retrospective: Dict) -> None:
        """Save retrospective report to workspace"""
        retro_dir = Path(self.workspace_path) / "retrospectives"
        retro_dir.mkdir(exist_ok=True)

        retro_id = retrospective["retrospective_id"]

        # Save JSON
        json_path = retro_dir / f"{retro_id}.json"
        with open(json_path, "w") as f:
            json.dump(retrospective, f, indent=2)

        # Save Markdown summary
        md_path = retro_dir / f"{retro_id}.md"
        md_content = self._format_retrospective_md(retrospective)
        with open(md_path, "w") as f:
            f.write(md_content)

        logger.info(f"[RetrospectiveAgent] Saved retrospective to {retro_dir}")

    def _format_retrospective_md(self, retrospective: Dict) -> str:
        """Format retrospective as Markdown"""
        md = f"""# Agent Retrospective
**ID:** {retrospective['retrospective_id']}  
**Date:** {retrospective['timestamp']}  
**Trigger:** {retrospective['trigger']}

---

## Agent Metrics

"""
        for agent_id, metrics in retrospective["agent_metrics"].items():
            md += f"### {agent_id.upper()}\n"
            for key, value in metrics.items():
                md += f"- **{key}:** {value}\n"
            md += "\n"

        md += f"""---

## Insights

"""
        for insight in retrospective["insights"]:
            md += f"- {insight}\n"

        md += f"""
---

## Action Items

"""
        for item in retrospective["action_items"]:
            md += f"- [{item['priority'].upper()}] {item['action']} (Assigned: {item['assigned_to']})\n"

        if retrospective.get("llm_summary"):
            md += f"""
---

## LLM Summary

{retrospective['llm_summary']}
"""

        md += f"""
---

*Generated by RetrospectiveAgent*
"""

        return md

    async def _create_improvement_proposal(self, retrospective: Dict) -> Optional[str]:
        """
        Create a change proposal from retrospective action items.

        This closes the feedback loop: retrospective → insights → proposal → code changes
        
        NEW: If action items require code changes, triggers DevelopmentAgent for implementation
        """
        action_items = retrospective.get("action_items", [])

        if not action_items:
            logger.info(
                "[RetrospectiveAgent] No action items, skipping proposal creation"
            )
            return None
        
        # Check if any action items need code implementation
        code_action_items = self._identify_code_actions(action_items)
        code_proposals_created = []
        if code_action_items:
            logger.info(
                f"[RetrospectiveAgent] Found {len(code_action_items)} action items requiring code implementation"
            )
            # Trigger Development Agent for code generation (creates Codespaces/Sandbox proposals)
            code_proposals_created = await self._trigger_development_agent(retrospective, code_action_items)
            if code_proposals_created:
                logger.info(
                    f"[RetrospectiveAgent] DevelopmentAgent created {len(code_proposals_created)} code proposals"
                )

        # Filter out code action items from the recommendations proposal
        # Only create "Recommendations" proposal for non-code actions
        code_action_texts = {item.get("action", "") for item in code_action_items}
        non_code_action_items = [
            item for item in action_items
            if item.get("action", "") not in code_action_texts
        ]
        
        # If all actions are code actions and proposals were created, skip recommendations proposal
        if not non_code_action_items and code_proposals_created:
            logger.info(
                "[RetrospectiveAgent] All actions are code actions with proposals - skipping Recommendations proposal"
            )
            return code_proposals_created[0] if code_proposals_created else None

        # Get high and medium priority actions (from non-code actions only)
        high_priority_actions = [
            item for item in non_code_action_items if item.get("priority") == "high"
        ]
        medium_priority_actions = [
            item for item in non_code_action_items if item.get("priority") == "medium"
        ]

        # Prioritize high, then include medium if needed, or all non-code actions
        if high_priority_actions:
            actions_to_propose = high_priority_actions
        elif medium_priority_actions:
            actions_to_propose = medium_priority_actions[:3]
        else:
            actions_to_propose = non_code_action_items[:3]

        if not actions_to_propose:
            return None

        # Build proposal content
        topic = retrospective.get("topic")
        if topic:
            proposal_title = f"{topic} - Recommendations"
            background_context = f"During the retrospective discussion on '{topic}', the following improvements were identified:"
        else:
            proposal_title = "Agent System Improvements (from Retrospective)"
            background_context = "After analyzing agent performance and collaboration patterns, the following improvements have been identified:"

        proposal_description = f"""# {proposal_title.replace(' - Recommendations', '')}

**Generated from Retrospective:** {retrospective['retrospective_id']}
**Date:** {retrospective['timestamp']}
{f"**Discussion Topic:** {topic}" if topic else ""}

## Background

{background_context}

"""

        # Add insights
        for insight in retrospective.get("insights", [])[:3]:
            proposal_description += f"- {insight}\n"

        proposal_description += "\n## Proposed Changes\n\n"

        # Add action items
        for i, item in enumerate(actions_to_propose, 1):
            proposal_description += f"### {i}. {item['action']}\n\n"
            proposal_description += f"**Priority:** {item['priority'].upper()}\n"
            proposal_description += f"**Assigned to:** {item['assigned_to']}\n\n"

            # Add implementation guidance
            if "error" in item["action"].lower():
                proposal_description += "**Implementation:**\n"
                proposal_description += "- Review error logs in `.agent_state/` files\n"
                proposal_description += (
                    "- Add try-catch blocks around agent operations\n"
                )
                proposal_description += "- Improve error reporting to event bus\n\n"
            elif (
                "subscribe" in item["action"].lower()
                or "event" in item["action"].lower()
            ):
                proposal_description += "**Implementation:**\n"
                proposal_description += (
                    "- Update agent `__init__` to subscribe to new events\n"
                )
                proposal_description += "- Add handler method for new event type\n"
                proposal_description += "- Test event flow with demo script\n\n"
            elif "document" in item["action"].lower():
                proposal_description += "**Implementation:**\n"
                proposal_description += "- Update relevant README or docs files\n"
                proposal_description += "- Add code comments\n"
                proposal_description += "- Create examples if needed\n\n"
            else:
                proposal_description += "**Implementation:**\n"
                proposal_description += "- Review relevant agent code\n"
                proposal_description += "- Make incremental changes\n"
                proposal_description += "- Test with existing workflows\n\n"

        proposal_description += """
## Benefits

Implementing these changes will:
- Improve agent coordination and collaboration
- Reduce errors and edge cases
- Enhance system reliability
- Better developer experience

## Next Steps

1. Review this proposal
2. Approve to implement changes
3. Test with existing workflows
4. Monitor agent metrics in next retrospective

---

*This proposal was automatically generated by the Retrospective Agent based on agent performance analysis.*
"""

        # Create the proposal using the proposal repository
        try:
            from app.repositories.proposal_repository import get_proposal_repository
            from app.config import get_config, StorageMode

            # Check if we're in cloud mode (Firestore enabled)
            config = get_config()
            if config.storage_mode == StorageMode.CLOUD:
                repo = get_proposal_repository()

                # Generate proposal ID
                proposal_id = f"retro-proposal-{retrospective['retrospective_id']}"
                
                # Generate diff for the new file
                file_path = f"docs/agent_improvements_{retrospective['retrospective_id']}.md"
                diff_content = generate_unified_diff(
                    file_path=file_path,
                    old_content="",  # New file - no old content
                    new_content=proposal_description
                )

                proposal_data = {
                    "id": proposal_id,
                    "workspace_id": self.workspace_id,
                    "user_id": "system",  # Agent-generated proposals use "system" user_id
                    "agent_id": "retrospective",
                    "title": proposal_title,
                    "description": proposal_description,
                    "diff": {
                        "format": "unified",
                        "content": diff_content
                    },
                    "proposed_changes": [
                        {
                            "file_path": file_path,
                            "change_type": "create",
                            "description": "Agent improvement action plan",
                            "after": proposal_description,
                            "diff": diff_content,
                        }
                    ],
                    "status": "pending",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "metadata": {
                        "retrospective_id": retrospective["retrospective_id"],
                        "action_items_count": len(actions_to_propose),
                    },
                }

                repo.create(proposal_data)
                logger.info(
                    f"[RetrospectiveAgent] Proposal created in Firestore: {proposal_id}"
                )
                return proposal_id
            else:
                # Fallback: save to local file
                proposal_id = f"retro-proposal-{retrospective['retrospective_id']}"
                proposals_dir = Path(self.workspace_path) / "proposals"
                proposals_dir.mkdir(exist_ok=True)
                
                # Generate diff for the new file
                file_path = f"docs/agent_improvements_{retrospective['retrospective_id']}.md"
                diff_content = generate_unified_diff(
                    file_path=file_path,
                    old_content="",  # New file - no old content
                    new_content=proposal_description
                )

                proposal_data = {
                    "id": proposal_id,
                    "workspace_id": self.workspace_id,
                    "user_id": "system",  # Agent-generated proposals use "system" user_id
                    "agent_id": "retrospective",
                    "title": proposal_title,
                    "description": proposal_description,
                    "diff": {
                        "format": "unified",
                        "content": diff_content
                    },
                    "proposed_changes": [
                        {
                            "file_path": file_path,
                            "change_type": "create",
                            "description": "Agent improvement action plan",
                            "after": proposal_description,
                            "diff": diff_content,
                        }
                    ],
                    "status": "pending",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "metadata": {
                        "retrospective_id": retrospective["retrospective_id"],
                        "action_items_count": len(actions_to_propose),
                    },
                }

                # Save JSON
                with open(proposals_dir / f"{proposal_id}.json", "w") as f:
                    json.dump(proposal_data, f, indent=2)

                # Save MD
                with open(proposals_dir / f"{proposal_id}.md", "w") as f:
                    f.write(f"# {proposal_title}\n\n{proposal_description}")

                logger.info(
                    f"[RetrospectiveAgent] Proposal saved locally: {proposal_id}"
                )
                return proposal_id

        except Exception as e:
            logger.error(f"[RetrospectiveAgent] Failed to create proposal: {e}")
            return None

    def _identify_code_actions(self, action_items: List[Dict]) -> List[Dict]:
        """
        Identify action items that require code implementation.
        
        Returns action items that contain keywords indicating code work is needed.
        
        Args:
            action_items: List of action item dictionaries
            
        Returns:
            Filtered list of action items requiring code changes
        """
        code_keywords = [
            "implement", "add", "create", "fix", "refactor", "update", 
            "error handling", "validation", "endpoint", "api", "function",
            "method", "class", "component", "service", "agent code",
            "schema", "protocol", "message", "event handler"
        ]
        
        code_actions = []
        for item in action_items:
            action = item.get("action", "").lower()
            # Check if action contains code-related keywords
            if any(keyword in action for keyword in code_keywords):
                # Exclude purely documentation tasks
                if not any(doc_word in action for doc_word in ["document", "readme", "guide", "manual"]):
                    code_actions.append(item)
                    logger.info(f"[RetrospectiveAgent] Identified code action: {item.get('action')[:80]}")
        
        return code_actions

    async def _trigger_development_agent(self, retrospective: Dict, code_actions: List[Dict]) -> None:
        """
        Trigger Development Agent to generate code implementations.
        
        Creates a detailed implementation request and lets DevelopmentAgent
        generate actual code proposals with diffs.
        
        Args:
            retrospective: Full retrospective data for context
            code_actions: Action items that need code implementation
        """
        try:
            from app.agents.development_agent import DevelopmentAgent
            
            logger.info(
                f"[RetrospectiveAgent] Triggering DevelopmentAgent for {len(code_actions)} code actions"
            )
            
            # Initialize Development Agent
            dev_agent = DevelopmentAgent(
                workspace_path=str(self.workspace_path),
                workspace_id=self.workspace_id,
                project_id=self.project_id,
            )
            
            # Process each code action
            for action_item in code_actions:
                action = action_item.get("action", "")
                priority = action_item.get("priority", "medium")
                
                # Build comprehensive description
                description = f"""From Retrospective: {retrospective['retrospective_id']}
Priority: {priority.upper()}

Action Item: {action}

Context from Retrospective:
"""
                # Add relevant insights
                for insight in retrospective.get("insights", [])[:3]:
                    if any(keyword in insight.lower() for keyword in action.lower().split()):
                        description += f"- {insight}\n"
                
                description += f"\n**Implementation Goal:**\n{action}"
                
                # Call Development Agent to generate code
                logger.info(f"[RetrospectiveAgent] Requesting implementation: {action[:80]}")
                proposal_id = await dev_agent.implement_feature(
                    description=description,
                    context={
                        "retrospective_id": retrospective["retrospective_id"],
                        "priority": priority,
                        "topic": retrospective.get("topic"),
                        "trigger": "retrospective_analysis",
                    },
                )
                
                if proposal_id:
                    logger.info(
                        f"[RetrospectiveAgent] ✅ DevelopmentAgent created code proposal: {proposal_id}"
                    )
                else:
                    logger.warning(
                        f"[RetrospectiveAgent] ⚠️ DevelopmentAgent could not generate proposal for: {action[:80]}"
                    )
                    
        except Exception as e:
            logger.error(
                f"[RetrospectiveAgent] Error triggering DevelopmentAgent: {e}",
                exc_info=True,
            )


# Standalone helper function for API endpoint
async def trigger_retrospective(
    workspace_id: str = "default",
    trigger: str = "manual",
    gemini_api_key: Optional[str] = None,
    trigger_topic: Optional[str] = None,
) -> Dict:
    """
    Trigger a retrospective (used by API endpoint).

    Args:
        workspace_id: Workspace identifier
        trigger: What triggered the retrospective
        gemini_api_key: Optional Gemini API key
        trigger_topic: Optional topic for agent discussion

    Returns:
        Retrospective summary
    """
    project_id = os.getenv(
        "GCP_PROJECT_ID",
        os.getenv("GOOGLE_CLOUD_PROJECT", os.getenv("GCP_PROJECT", "local")),
    )

    agent = RetrospectiveAgent(workspace_id=workspace_id, project_id=project_id)
    retrospective = await agent.conduct_retrospective(
        trigger=trigger, gemini_api_key=gemini_api_key, trigger_topic=trigger_topic
    )

    return retrospective
