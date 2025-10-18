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
        self, trigger: str = "manual", gemini_api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Conduct a retrospective meeting between agents.

        Args:
            trigger: What triggered the retrospective (e.g., "manual", "milestone_complete", "cycle_end")
            gemini_api_key: Optional Gemini API key for LLM synthesis

        Returns:
            Retrospective summary with agent insights and action items
        """
        logger.info(f"[RetrospectiveAgent] Starting retrospective (trigger: {trigger})")

        # 1. Gather agent metrics
        agent_metrics = self._collect_agent_metrics()

        # 2. Gather agent learnings (from state files)
        agent_learnings = self._collect_agent_learnings()

        # 3. Analyze event history
        event_summary = self._analyze_event_history()

        # 4. Generate insights
        insights = self._generate_insights(
            agent_metrics, agent_learnings, event_summary
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
            "agent_metrics": agent_metrics,
            "agent_learnings": agent_learnings,
            "event_summary": event_summary,
            "insights": insights,
            "action_items": action_items,
            "llm_summary": llm_summary,
        }

        # 8. Save retrospective to workspace
        self._save_retrospective(retrospective)

        # 9. Publish retrospective event
        await self.publish_event(
            topic=Topics.RETROSPECTIVE_EVENTS,
            event_type="retrospective.summary.v1",
            data={
                "retrospective_id": retrospective["retrospective_id"],
                "workspace_id": self.workspace_id,
                "insights_count": len(insights),
                "action_items_count": len(action_items),
            },
        )

        logger.info(
            f"[RetrospectiveAgent] Retrospective completed: {retrospective['retrospective_id']}"
        )
        return retrospective

    def _collect_agent_metrics(self) -> Dict[str, Dict]:
        """Collect metrics from all agent state files"""
        metrics = {}
        state_dir = Path(self.workspace_path) / ".agent_state"

        if not state_dir.exists():
            logger.warning("[RetrospectiveAgent] No agent state directory found")
            return metrics

        for state_file in state_dir.glob("*_state.json"):
            agent_id = state_file.stem.replace("_state", "")
            try:
                with open(state_file, "r") as f:
                    state = json.load(f)
                    metrics[agent_id] = state.get("metrics", {})
            except Exception as e:
                logger.error(
                    f"[RetrospectiveAgent] Error reading {agent_id} state: {e}"
                )

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
        self, agent_metrics: Dict, agent_learnings: Dict, event_summary: Dict
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

        return insights

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
            import google.generativeai as genai

            genai.configure(api_key=gemini_api_key)

            model = genai.GenerativeModel("gemini-1.5-flash")

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

            response = model.generate_content(prompt)
            return response.text

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


# Standalone helper function for API endpoint
async def trigger_retrospective(
    workspace_id: str = "default",
    trigger: str = "manual",
    gemini_api_key: Optional[str] = None,
) -> Dict:
    """
    Trigger a retrospective (used by API endpoint).

    Args:
        workspace_id: Workspace identifier
        trigger: What triggered the retrospective
        gemini_api_key: Optional Gemini API key

    Returns:
        Retrospective summary
    """
    project_id = os.getenv(
        "GCP_PROJECT_ID",
        os.getenv("GOOGLE_CLOUD_PROJECT", os.getenv("GCP_PROJECT", "local")),
    )

    agent = RetrospectiveAgent(workspace_id=workspace_id, project_id=project_id)
    retrospective = await agent.conduct_retrospective(
        trigger=trigger, gemini_api_key=gemini_api_key
    )

    return retrospective
