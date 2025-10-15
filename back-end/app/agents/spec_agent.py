"""
Spec Agent - Documentation Curator

Manages markdown artifacts, validates consistency, generates docs from code.
"""
import os
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional
from pathlib import Path
import yaml
import json

# Lazy import of event bus in __init__ to avoid hard dependency during local tests
# from app.services.event_bus import get_event_bus

logger = logging.getLogger(__name__)


class SpecAgent:
    """
    Spec Agent manages documentation artifacts as versioned code.
    
    Responsibilities:
    - Generate/update markdown docs
    - Validate docs vs code consistency
    - Manage templates
    - Create Change Proposals for doc updates
    """
    
    def __init__(self, workspace_path: str, project_id: str):
        """
        Initialize Spec Agent.
        
        Args:
            workspace_path: Path to workspace directory
            project_id: GCP project ID for Pub/Sub
        """
        self.workspace_path = Path(workspace_path)
        self.docs_path = self.workspace_path / "docs"
        self.templates_path = Path(__file__).parent.parent / "templates"
        # Lazy/optional event bus initialization to avoid hanging when GCP is not configured
        self.event_bus = None
        try:
            if project_id and project_id not in ("local", "test"):
                self.event_bus = get_event_bus(project_id)
        except Exception as e:
            logger.warning(f"SpecAgent: Pub/Sub disabled (reason: {e})")
            self.event_bus = None
        
        logger.info(f"Spec Agent initialized for workspace: {workspace_path}")
    
    async def handle_context_update(self, event: Dict):
        """
        Handle context.update.v1 event.
        
        When code changes, check if docs need updating.
        """
        logger.info(f"Spec Agent received context update: {event['event_id']}")
        
        data = event["data"]
        files_changed = data.get("files_changed", [])
        
        # Check if API routes changed
        if any("routes" in f or "api" in f for f in files_changed):
            logger.info("API changes detected, checking if API.md needs update")
            await self._check_api_docs(event)
        
        # Check if architecture changed
        if any("services" in f or "agents" in f for f in files_changed):
            logger.info("Architecture changes detected")
            await self._check_architecture_docs(event)
    
    async def _check_api_docs(self, event: Dict):
        """Check if API.md needs updating based on code changes."""
        
        # TODO: Parse FastAPI routes from code
        # TODO: Compare with current API.md
        # TODO: Generate diff
        # TODO: Create Change Proposal
        
        logger.info("API doc validation not yet implemented")
    
    async def _check_architecture_docs(self, event: Dict):
        """Check if ARCHITECTURE.md needs updating."""
        
        logger.info("Architecture doc validation not yet implemented")
    
    async def generate_daily_checklist(self, user_id: str) -> str:
        """
        Generate daily checklist from template.
        
        Args:
            user_id: User to generate checklist for
            
        Returns:
            Path to generated checklist
        """
        logger.info(f"Generating daily checklist for user: {user_id}")
        
        # Load template
        template_path = self.templates_path / "daily_checklist.md"
        
        with open(template_path, 'r') as f:
            template = f.read()
        
        # Get today's date
        today = datetime.now(timezone.utc)
        day_of_week = today.strftime("%A")
        date = today.strftime("%Y-%m-%d")
        
        # Simple substitution (in production, use proper templating)
        content = template.replace("{{day_of_week}}", day_of_week)
        content = content.replace("{{date}}", date)
        content = content.replace("{{generation_time}}", today.isoformat())
        
        # TODO: Fetch coach nudges and populate
        content = content.replace("{{#if coach_nudges}}", "")
        content = content.replace("{{else}}", "")
        content = content.replace("{{/if}}", "")
        content = content.replace("{{#each coach_nudges}}", "")
        content = content.replace("{{/each}}", "")
        
        # Save to workspace
        output_path = self.workspace_path / f"daily_checklist_{date}.md"
        
        with open(output_path, 'w') as f:
            f.write(content)
        
        logger.info(f"✅ Daily checklist generated: {output_path}")
        
        # Emit event
        if self.event_bus:
            self.event_bus.publish(
                topic="spec-updates",
                event_type="spec.update.v1",
                source="spec-agent",
                data={
                    "file": str(output_path),
                    "action": "created",
                    "type": "daily_checklist"
                }
            )
        
        return str(output_path)
    
    async def validate_docs(self) -> List[Dict]:
        """
        Validate all documentation for consistency.
        
        Returns:
            List of validation issues
        """
        logger.info("Validating documentation consistency")
        
        issues = []
        
        # Check if standard docs exist
        required_docs = ["README.md", "ARCHITECTURE.md"]
        
        for doc in required_docs:
            doc_path = self.workspace_path / doc
            if not doc_path.exists():
                issues.append({
                    "type": "missing_doc",
                    "file": doc,
                    "severity": "high",
                    "message": f"{doc} not found"
                })
        
        # TODO: Check API endpoints vs API.md
        # TODO: Check architecture diagram vs actual structure
        # TODO: Check for stale docs (>7 days since related code changed)
        
        if issues:
            logger.warning(f"Found {len(issues)} documentation issues")
            
            # Emit validation event
            if self.event_bus:
                self.event_bus.publish(
                    topic="spec-updates",
                    event_type="spec.validation.v1",
                    source="spec-agent",
                    data={
                        "issues": issues,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )
        else:
            logger.info("✅ All docs valid")
        
        return issues
    
    async def create_template(
        self,
        name: str,
        sections: List[str],
        frequency: Optional[str] = None
    ) -> str:
        """
        Create a new custom template.
        
        Args:
            name: Template name (e.g., "retrospective.md")
            sections: List of section names
            frequency: Optional frequency (daily, weekly, sprint)
            
        Returns:
            Path to created template
        """
        logger.info(f"Creating custom template: {name}")
        
        # Generate template structure
        frontmatter = {
            "managed_by": "spec-agent",
            "template": name.replace(".md", ""),
            "version": "1.0.0",
            "created": datetime.now(timezone.utc).isoformat(),
            "auto_update": False,
            "frequency": frequency
        }
        
        content = "---\n"
        content += yaml.dump(frontmatter)
        content += "---\n\n"
        content += f"# {name.replace('.md', '').replace('_', ' ').title()}\n\n"
        
        for section in sections:
            content += f"## {section}\n\n"
            content += "<!-- Add content here -->\n\n"
        
        content += "---\n\n"
        content += f"*Generated by Spec Agent on {datetime.now(timezone.utc).strftime('%Y-%m-%d')}*\n"
        
        # Save template
        template_path = self.docs_path / "templates" / name
        template_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(template_path, 'w') as f:
            f.write(content)
        
        logger.info(f"✅ Template created: {template_path}")
        
        # Emit event
        if self.event_bus:
            self.event_bus.publish(
                topic="spec-updates",
                event_type="spec.template.created.v1",
                source="spec-agent",
                data={
                    "template_name": name,
                    "path": str(template_path),
                    "sections": sections
                }
            )
        
        return str(template_path)


# Event handlers (will be called by Cloud Run endpoint)

async def handle_context_update(event: Dict):
    """Handle context.update.v1 events."""
    # This will be called by /events endpoint
    # For now, just log
    logger.info(f"Received context update: {event['event_id']}")


async def handle_git_commit(event: Dict):
    """Handle git.commit.v1 events."""
    logger.info(f"Received git commit: {event['event_id']}")
    
    # TODO: Update CHANGELOG.md
    # TODO: Check if docs need updating


# For testing
if __name__ == "__main__":
    import asyncio
    
    async def test():
        agent = SpecAgent(
            workspace_path="/tmp/test-workspace",
            project_id="test-project"
        )
        
        # Test daily checklist generation
        checklist_path = await agent.generate_daily_checklist("test_user")
        print(f"Generated: {checklist_path}")
        
        # Test template creation
        template_path = await agent.create_template(
            name="retrospective.md",
            sections=["What Went Well", "What To Improve", "Action Items"],
            frequency="sprint"
        )
        print(f"Template: {template_path}")
    
    asyncio.run(test())

