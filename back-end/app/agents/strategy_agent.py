"""
Strategy Agent - Code Analysis & Improvement Suggestions

Analyzes architecture, detects code smells, creates Change Proposals (never modifies code directly).
"""
import os
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional
from pathlib import Path
import ast
import re

from app.services.event_bus import get_event_bus
from app.models.proposal import (
    ChangeProposal,
    FileChange,
    ImpactAnalysis,
    ChangeAction,
    ProposalType
)

logger = logging.getLogger(__name__)


class StrategyAgent:
    """
    Strategy Agent analyzes code and suggests improvements.
    
    Core Principle: NEVER modifies code directly. Only creates Change Proposals.
    
    Responsibilities:
    - Detect code duplication
    - Identify architectural smells
    - Suggest refactorings
    - Find security issues
    - Calculate blast radius
    """
    
    def __init__(self, workspace_path: str, project_id: str):
        """
        Initialize Strategy Agent.
        
        Args:
            workspace_path: Path to workspace/repo root
            project_id: GCP project ID for Pub/Sub
        """
        self.workspace_path = Path(workspace_path)
        self.event_bus = get_event_bus(project_id)
        
        logger.info(f"Strategy Agent initialized for workspace: {workspace_path}")
    
    async def handle_context_update(self, event: Dict):
        """
        Handle context.update.v1 event.
        
        When code changes, analyze for improvement opportunities.
        """
        logger.info(f"Strategy Agent received context update: {event['event_id']}")
        
        data = event["data"]
        files_changed = data.get("files_changed", [])
        impact_score = data.get("impact_score", 0)
        
        # Only analyze significant changes
        if impact_score < 5.0:
            logger.info(f"Impact score too low ({impact_score}), skipping analysis")
            return
        
        # Analyze changed files
        for file_path in files_changed:
            if file_path.endswith(".py"):
                await self._analyze_python_file(file_path, event)
    
    async def _analyze_python_file(self, file_path: str, event: Dict):
        """Analyze a Python file for issues."""
        
        full_path = self.workspace_path / file_path
        
        if not full_path.exists():
            return
        
        try:
            with open(full_path, 'r') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content)
            
            # Run analysis
            issues = []
            
            # Check 1: Long functions (>50 lines)
            issues.extend(self._check_function_length(tree, file_path))
            
            # Check 2: Too many parameters (>5)
            issues.extend(self._check_parameter_count(tree, file_path))
            
            # Check 3: Missing docstrings
            issues.extend(self._check_docstrings(tree, file_path))
            
            # If issues found, create proposals
            for issue in issues:
                await self._create_proposal_from_issue(issue, file_path, event)
                
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
    
    def _check_function_length(self, tree: ast.AST, file_path: str) -> List[Dict]:
        """Check for overly long functions."""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Count lines
                if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                    length = node.end_lineno - node.lineno
                    
                    if length > 50:
                        issues.append({
                            "type": "long_function",
                            "function": node.name,
                            "lines": length,
                            "file": file_path,
                            "severity": "medium",
                            "suggestion": f"Consider breaking {node.name} into smaller functions"
                        })
        
        return issues
    
    def _check_parameter_count(self, tree: ast.AST, file_path: str) -> List[Dict]:
        """Check for functions with too many parameters."""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                param_count = len(node.args.args)
                
                if param_count > 5:
                    issues.append({
                        "type": "too_many_params",
                        "function": node.name,
                        "param_count": param_count,
                        "file": file_path,
                        "severity": "low",
                        "suggestion": f"Consider using a config object for {node.name}"
                    })
        
        return issues
    
    def _check_docstrings(self, tree: ast.AST, file_path: str) -> List[Dict]:
        """Check for missing docstrings."""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                # Check if has docstring
                has_docstring = (
                    ast.get_docstring(node) is not None
                )
                
                if not has_docstring and not node.name.startswith("_"):
                    issues.append({
                        "type": "missing_docstring",
                        "name": node.name,
                        "node_type": "class" if isinstance(node, ast.ClassDef) else "function",
                        "file": file_path,
                        "severity": "low",
                        "suggestion": f"Add docstring to {node.name}"
                    })
        
        return issues
    
    async def _create_proposal_from_issue(
        self,
        issue: Dict,
        file_path: str,
        context_event: Dict
    ):
        """Create a Change Proposal from an identified issue."""
        
        # For now, just emit an insight event
        # Full proposal generation would use Gemini to create actual code fixes
        
        logger.info(f"Issue detected: {issue['type']} in {file_path}")
        
        # Emit insight event
        self.event_bus.publish(
            topic="strategy-insights",
            event_type="strategy.insight.v1",
            source="strategy-agent",
            data={
                "insight_type": issue["type"],
                "file": file_path,
                "severity": issue["severity"],
                "suggestion": issue["suggestion"],
                "details": issue,
                "related_event": context_event["event_id"]
            }
        )
    
    async def analyze_codebase(self) -> List[Dict]:
        """
        Full codebase analysis (for scheduled jobs).
        
        Returns:
            List of insights generated
        """
        logger.info("Running full codebase analysis")
        
        insights = []
        
        # Find all Python files
        python_files = list(self.workspace_path.rglob("*.py"))
        
        logger.info(f"Found {len(python_files)} Python files to analyze")
        
        for file_path in python_files:
            # Skip venv, node_modules, etc
            if any(skip in str(file_path) for skip in [".venv", "node_modules", "__pycache__"]):
                continue
            
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                # Run all checks
                issues = []
                issues.extend(self._check_function_length(tree, str(file_path.relative_to(self.workspace_path))))
                issues.extend(self._check_parameter_count(tree, str(file_path.relative_to(self.workspace_path))))
                issues.extend(self._check_docstrings(tree, str(file_path.relative_to(self.workspace_path))))
                
                insights.extend(issues)
                
            except Exception as e:
                logger.error(f"Error analyzing {file_path}: {e}")
        
        logger.info(f"✅ Analysis complete: {len(insights)} insights generated")
        
        # Emit summary event
        if insights:
            self.event_bus.publish(
                topic="strategy-insights",
                event_type="strategy.analysis.completed.v1",
                source="strategy-agent",
                data={
                    "insights_count": len(insights),
                    "files_analyzed": len(python_files),
                    "insights": insights[:10]  # Top 10
                }
            )
        
        return insights


# Event handlers

async def handle_context_update(event: Dict):
    """Handle context.update.v1 events."""
    logger.info(f"Strategy Agent processing: {event['event_id']}")


# For testing
if __name__ == "__main__":
    import asyncio
    
    async def test():
        agent = StrategyAgent(
            workspace_path="/home/fsegall/Desktop/New_Projects/google-context-pilot/back-end",
            project_id="test-project"
        )
        
        # Test full analysis
        insights = await agent.analyze_codebase()
        print(f"Found {len(insights)} insights")
        
        for insight in insights[:5]:
            print(f"  - {insight['type']}: {insight['suggestion']}")
    
    asyncio.run(test())

