"""
Strategy Coach Agent - Unified Strategic & Technical Coaching

Provides comprehensive guidance combining:
- Strategic direction and architectural planning (proactive)
- Technical code analysis and refactoring suggestions (reactive)
- Motivational coaching based on progress and milestones
- Best practices and design patterns

This agent unifies strategic thinking, technical analysis, and team motivation.
"""

import logging
import ast
from datetime import datetime, timezone
from typing import Dict, Optional, List
from pathlib import Path
import json

from app.agents.base_agent import BaseAgent
from app.services.event_bus import EventTypes, Topics

logger = logging.getLogger(__name__)


class CoachAgent(BaseAgent):
    """
    Strategy Coach Agent - Unified strategic and technical coaching.

    Three core functions:

    1. STRATEGIC (Proactive):
       - Architectural direction and planning
       - Long-term technical vision
       - Design pattern recommendations
       - Technology stack decisions

    2. TECHNICAL (Reactive):
       - Code quality analysis (code smells, complexity)
       - Refactoring suggestions
       - Security and performance review
       - Best practice enforcement

    3. MOTIVATIONAL (Progress-based):
       - Milestone tracking and celebration
       - Progress encouragement
       - Blocker identification and support
       - Team collaboration facilitation
    """

    def __init__(
        self,
        workspace_path: str,
        workspace_id: str = "default",
        project_id: Optional[str] = None,
    ):
        """
        Initialize Coach Agent.

        Args:
            workspace_path: Path to workspace directory
            workspace_id: Workspace identifier
            project_id: GCP project ID for Pub/Sub
        """
        # Initialize base agent
        super().__init__(
            workspace_id=workspace_id, agent_id="coach", project_id=project_id
        )

        # Coach-specific paths
        self.workspace_path = Path(workspace_path)
        self.coaching_path = self.workspace_path / ".coaching"
        self.coaching_path.mkdir(exist_ok=True)

        # Subscribe to events
        self.subscribe_to_event(EventTypes.PROPOSAL_CREATED)
        self.subscribe_to_event(EventTypes.PROPOSAL_REJECTED)
        self.subscribe_to_event(EventTypes.GIT_COMMIT)

        logger.info(
            f"[Strategy Coach Agent] Initialized for workspace: {workspace_path}"
        )

    async def handle_event(self, event_type: str, data: Dict) -> None:
        """
        Handle incoming events.

        Args:
            event_type: Type of event
            data: Event data payload
        """
        logger.info(f"[Coach Agent] Received event: {event_type}")

        try:
            if event_type == EventTypes.PROPOSAL_CREATED:
                await self._handle_proposal_created(data)
            elif event_type == EventTypes.PROPOSAL_REJECTED:
                await self._handle_proposal_rejected(data)
            elif event_type == EventTypes.GIT_COMMIT:
                await self._handle_git_commit(data)

            # Update metrics
            self.increment_metric("events_processed")
        except Exception as e:
            logger.error(f"[Coach Agent] Error handling {event_type}: {e}")
            self.increment_metric("errors")

    async def _handle_proposal_created(self, data: Dict) -> None:
        """Handle proposal.created.v1 event - provide guidance"""
        proposal_id = data.get("proposal_id")
        agent_id = data.get("agent_id", "unknown")

        logger.info(f"[Coach Agent] New proposal created: {proposal_id} by {agent_id}")

        # Track proposal patterns
        await self._track_proposal_pattern(proposal_id, agent_id, "created")

        # Publish coaching insight event
        await self.publish_event(
            topic=Topics.COACH_EVENTS,
            event_type="coach.insight.v1",
            data={
                "type": "proposal_created",
                "proposal_id": proposal_id,
                "agent_id": agent_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def _handle_proposal_rejected(self, data: Dict) -> None:
        """Handle proposal.rejected.v1 event - analyze for learning"""
        proposal_id = data.get("proposal_id")
        reason = data.get("reason", "No reason provided")

        logger.info(f"[Coach Agent] Proposal rejected: {proposal_id}")

        # Analyze rejection patterns for coaching insights
        await self._analyze_rejection(proposal_id, reason)

        # Track for learning
        await self._track_proposal_pattern(proposal_id, "unknown", "rejected")

    async def _handle_git_commit(self, data: Dict) -> None:
        """Handle git.commit.v1 event - track development patterns AND analyze code"""
        commit_hash = data.get("commit_hash")
        message = data.get("message", "")
        files_changed = data.get("files_changed", [])

        logger.info(f"[Strategy Coach Agent] Analyzing commit: {commit_hash}")

        # 1. Check commit message quality (motivational)
        quality_score = self._assess_commit_message_quality(message)

        if quality_score < 0.5:
            logger.info(
                f"[Strategy Coach Agent] Low quality commit message detected (score: {quality_score})"
            )
            # Could publish coaching suggestion event

        # 2. Analyze changed Python files for code quality (technical)
        for file_path in files_changed:
            if file_path.endswith(".py"):
                await self._analyze_python_file(file_path)

    async def _track_proposal_pattern(
        self, proposal_id: str, agent_id: str, status: str
    ) -> None:
        """Track proposal patterns for coaching insights"""
        patterns_file = self.coaching_path / "proposal_patterns.json"

        try:
            if patterns_file.exists():
                with open(patterns_file, "r") as f:
                    patterns = json.load(f)
            else:
                patterns = {"proposals": [], "stats": {}}

            # Add proposal
            patterns["proposals"].append(
                {
                    "proposal_id": proposal_id,
                    "agent_id": agent_id,
                    "status": status,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

            # Update stats
            agent_stats = patterns["stats"].get(agent_id, {"created": 0, "rejected": 0})
            if status == "created":
                agent_stats["created"] += 1
            elif status == "rejected":
                agent_stats["rejected"] += 1
            patterns["stats"][agent_id] = agent_stats

            # Save
            with open(patterns_file, "w") as f:
                json.dump(patterns, f, indent=2)

            logger.info(f"[Coach Agent] Tracked proposal pattern for {agent_id}")

        except Exception as e:
            logger.error(f"[Coach Agent] Failed to track proposal pattern: {e}")

    async def _analyze_rejection(self, proposal_id: str, reason: str) -> None:
        """Analyze rejection for learning opportunities"""
        logger.info(
            f"[Coach Agent] Analyzing rejection of {proposal_id}: {reason[:100]}"
        )

        # In production, this would:
        # 1. Extract key themes from rejection reason
        # 2. Identify common patterns
        # 3. Generate coaching suggestions
        # 4. Update learning resources

    def _assess_commit_message_quality(self, message: str) -> float:
        """
        Assess commit message quality (0-1 score).

        Args:
            message: Commit message

        Returns:
            Quality score between 0 and 1
        """
        if not message:
            return 0.0

        score = 0.5  # Base score

        # Good: Has conventional commit prefix
        if any(
            message.lower().startswith(prefix)
            for prefix in ["feat:", "fix:", "docs:", "refactor:", "test:", "chore:"]
        ):
            score += 0.2

        # Good: Reasonable length (10-72 chars for first line)
        first_line = message.split("\n")[0]
        if 10 <= len(first_line) <= 72:
            score += 0.2

        # Bad: Too short
        if len(first_line) < 10:
            score -= 0.3

        # Good: Has description (multiple lines)
        if "\n" in message:
            score += 0.1

        return max(0.0, min(1.0, score))

    async def get_coaching_summary(self) -> Dict:
        """
        Get summary of coaching insights.

        Returns:
            Dictionary with coaching metrics
        """
        patterns_file = self.coaching_path / "proposal_patterns.json"

        try:
            if patterns_file.exists():
                with open(patterns_file, "r") as f:
                    patterns = json.load(f)

                return {
                    "total_proposals_tracked": len(patterns.get("proposals", [])),
                    "agent_stats": patterns.get("stats", {}),
                    "status": "active",
                }
            else:
                return {"total_proposals_tracked": 0, "status": "uninitialized"}
        except Exception as e:
            logger.error(f"[Coach Agent] Failed to get coaching summary: {e}")
            return {"status": "error", "error": str(e)}

    def provide_perspective(self, topic: str) -> str:
        """
        Provide agent perspective on a topic.

        Args:
            topic: Discussion topic

        Returns:
            Agent's perspective as a string
        """
        # Strategy Coach Agent focuses on strategic direction and best practices
        return f"Let's align '{topic}' with our long-term technical vision and architectural principles. I recommend identifying optimal design patterns, considering scalability implications, and ensuring team knowledge transfer throughout implementation."

    # ========================================
    # TECHNICAL ANALYSIS METHODS (from old Strategy Agent)
    # ========================================

    async def _analyze_python_file(self, file_path: str) -> None:
        """
        Analyze a Python file for code quality issues.

        Args:
            file_path: Relative path to Python file
        """
        # Get project root (up from workspace_path)
        project_root = self.workspace_path.parent.parent.parent
        full_path = project_root / file_path

        if not full_path.exists():
            logger.debug(f"[Strategy Coach Agent] File not found: {full_path}")
            return

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse AST
            tree = ast.parse(content)

            # Run analysis checks
            issues = []
            issues.extend(self._check_function_length(tree, file_path))
            issues.extend(self._check_parameter_count(tree, file_path))
            issues.extend(self._check_docstrings(tree, file_path))

            if issues:
                logger.info(
                    f"[Strategy Coach Agent] Found {len(issues)} code quality issues in {file_path}"
                )
                # In production: create proposals for significant issues
                # For now: just log and track
                await self._track_code_issues(file_path, issues)
            else:
                logger.debug(
                    f"[Strategy Coach Agent] No issues found in {file_path} ✅"
                )

        except Exception as e:
            logger.error(f"[Strategy Coach Agent] Error analyzing {file_path}: {e}")

    def _check_function_length(self, tree: ast.AST, file_path: str) -> List[Dict]:
        """Check for overly long functions (>50 lines)."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if hasattr(node, "end_lineno") and hasattr(node, "lineno"):
                    length = node.end_lineno - node.lineno

                    if length > 50:
                        issues.append(
                            {
                                "type": "long_function",
                                "function": node.name,
                                "lines": length,
                                "file": file_path,
                                "severity": "medium",
                                "suggestion": f"Consider breaking {node.name} ({length} lines) into smaller functions",
                            }
                        )

        return issues

    def _check_parameter_count(self, tree: ast.AST, file_path: str) -> List[Dict]:
        """Check for functions with too many parameters (>5)."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                param_count = len(node.args.args)

                if param_count > 5:
                    issues.append(
                        {
                            "type": "too_many_params",
                            "function": node.name,
                            "param_count": param_count,
                            "file": file_path,
                            "severity": "low",
                            "suggestion": f"Consider using a config object for {node.name} ({param_count} params)",
                        }
                    )

        return issues

    def _check_docstrings(self, tree: ast.AST, file_path: str) -> List[Dict]:
        """Check for missing docstrings in public functions/classes."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                has_docstring = ast.get_docstring(node) is not None

                # Only flag public functions/classes (not starting with _)
                if not has_docstring and not node.name.startswith("_"):
                    node_type = (
                        "class" if isinstance(node, ast.ClassDef) else "function"
                    )
                    issues.append(
                        {
                            "type": "missing_docstring",
                            "name": node.name,
                            "node_type": node_type,
                            "file": file_path,
                            "severity": "low",
                            "suggestion": f"Add docstring to public {node_type} {node.name}",
                        }
                    )

        return issues

    async def _track_code_issues(self, file_path: str, issues: List[Dict]) -> None:
        """Track code quality issues for trending analysis."""
        issues_file = self.coaching_path / "code_quality_issues.json"

        try:
            if issues_file.exists():
                with open(issues_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {"files": {}, "summary": {}}

            # Track issues by file
            data["files"][file_path] = {
                "issues": issues,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "issue_count": len(issues),
            }

            # Update summary by type
            for issue in issues:
                issue_type = issue["type"]
                data["summary"][issue_type] = data["summary"].get(issue_type, 0) + 1

            # Save
            with open(issues_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            logger.debug(
                f"[Strategy Coach Agent] Tracked {len(issues)} issues for {file_path}"
            )

        except Exception as e:
            logger.error(f"[Strategy Coach Agent] Failed to track code issues: {e}")
