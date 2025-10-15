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

from app.agents.base_agent import BaseAgent
from app.services.event_bus import EventTypes, Topics
from app.agents.diff_generator import generate_unified_diff, read_file_safe

logger = logging.getLogger(__name__)


class SpecAgent(BaseAgent):
    """
    Spec Agent manages documentation artifacts as versioned code.
    
    Responsibilities:
    - Generate/update markdown docs
    - Validate docs vs code consistency
    - Manage templates
    - Create Change Proposals for doc updates
    """
    
    def __init__(self, workspace_path: str, workspace_id: str = "default", project_id: Optional[str] = None):
        """
        Initialize Spec Agent.
        
        Args:
            workspace_path: Path to workspace directory
            workspace_id: Workspace identifier
            project_id: GCP project ID for Pub/Sub
        """
        # Initialize base agent
        super().__init__(workspace_id=workspace_id, agent_id='spec', project_id=project_id)
        
        # Spec-specific paths (ensure Path objects)
        self.workspace_path = Path(self.workspace_path)  # Convert to Path if string
        self.docs_path = self.workspace_path / "docs"
        self.templates_path = Path(__file__).parent.parent / "templates"
        
        # Subscribe to events
        self.subscribe_to_event(EventTypes.GIT_COMMIT)
        self.subscribe_to_event(EventTypes.CONTEXT_DELTA)
        
        logger.info(f"Spec Agent initialized for workspace: {workspace_path}")
    
    async def handle_event(self, event_type: str, data: Dict) -> None:
        """
        Handle incoming events.
        
        Args:
            event_type: Type of event
            data: Event data payload
        """
        logger.info(f"[Spec Agent] Received event: {event_type}")
        
        try:
            if event_type == EventTypes.GIT_COMMIT:
                await self._handle_git_commit(data)
            elif event_type == EventTypes.CONTEXT_DELTA:
                await self._handle_context_delta(data)
            
            # Update metrics
            self.increment_metric('events_processed')
        except Exception as e:
            logger.error(f"[Spec Agent] Error handling {event_type}: {e}")
            self.increment_metric('errors')
    
    async def _handle_git_commit(self, data: Dict) -> None:
        """Handle git.commit.v1 event"""
        commit_hash = data.get('commit_hash')
        workspace_id = data.get('workspace_id')
        
        logger.info(f"[Spec Agent] Processing commit {commit_hash}")
        
        # Analyze documentation consistency
        issues = self.validate_documentation()
        
        if issues:
            logger.warning(f"[Spec Agent] Found {len(issues)} documentation issues")
            # Create proposals for issues
            for issue in issues:
                await self._create_proposal_for_issue(issue)
    
    async def _handle_context_delta(self, data: Dict) -> None:
        """Handle context.delta.v1 event"""
        delta_type = data.get('type')
        scope = data.get('scope', [])
        
        logger.info(f"[Spec Agent] Context delta: {delta_type} in {scope}")
        # Could trigger specific doc updates based on scope
    
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
    
    async def _create_proposal_for_issue(self, issue: Dict) -> Optional[str]:
        """
        Create a change proposal with actual diff for a documentation issue.
        
        Args:
            issue: Issue dictionary from validate_documentation()
        
        Returns:
            Proposal ID if created, None otherwise
        """
        proposal_id = f"spec-{issue['type']}-{int(datetime.now().timestamp())}"
        
        # 1. Read current content
        file_path = issue['file']
        current_content = read_file_safe(file_path, str(self.workspace_path))
        
        # 2. Generate proposed content
        # For now, use a simple template. In production, use Gemini to generate
        if issue['type'] == 'missing_doc':
            proposed_content = self._generate_doc_template(file_path)
        else:
            # For other types, just add a note (in production, use LLM)
            proposed_content = current_content + f"\n\n<!-- Updated by Spec Agent: {issue['message']} -->\n"
        
        # 3. Generate diff
        diff_content = generate_unified_diff(
            file_path=file_path,
            old_content=current_content,
            new_content=proposed_content
        )
        
        # 4. Create proposal with diff
        proposal = {
            'id': proposal_id,
            'agent_id': 'spec',
            'workspace_id': self.workspace_id,
            'title': f"Docs issue: {issue['file']}",
            'description': issue['message'],
            'diff': {
                'format': 'unified',
                'content': diff_content
            },
            'proposed_changes': [{
                'file_path': file_path,
                'change_type': 'update' if current_content else 'create',
                'description': issue['message'],
                'before': current_content,
                'after': proposed_content,
                'diff': diff_content
            }],
            'status': 'pending',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        # 5. Save proposal to workspace
        await self._save_proposal(proposal)
        
        # 6. Publish proposal.created event
        await self.publish_event(
            topic=Topics.PROPOSAL_EVENTS,
            event_type=EventTypes.PROPOSAL_CREATED,
            data={
                'proposal_id': proposal_id,
                'workspace_id': self.workspace_id,
                'issue_type': issue['type'],
                'file': issue['file']
            }
        )
        
        logger.info(f"[Spec Agent] Created proposal {proposal_id} with diff for {issue['file']}")
        
        # 7. Remember this proposal
        proposals = self.recall('proposals_created', [])
        proposals.append(proposal_id)
        self.remember('proposals_created', proposals)
        
        return proposal_id
    
    def _generate_doc_template(self, file_path: str) -> str:
        """Generate basic documentation template"""
        filename = Path(file_path).stem
        return f"""# {filename.replace('_', ' ').replace('-', ' ').title()}

## Overview

This document describes {filename}.

## Purpose

<!-- Add purpose here -->

## Usage

<!-- Add usage instructions here -->

## Examples

<!-- Add examples here -->

## References

<!-- Add references here -->
"""
    
    async def _save_proposal(self, proposal: Dict) -> None:
        """Save proposal to workspace"""
        proposals_dir = Path(self.workspace_path) / 'proposals'
        proposals_dir.mkdir(exist_ok=True)
        
        # Save as JSON
        json_path = proposals_dir / f"{proposal['id']}.json"
        with open(json_path, 'w') as f:
            json.dump(proposal, f, indent=2)
        
        # Save as Markdown
        md_path = proposals_dir / f"{proposal['id']}.md"
        md_content = f"""# {proposal['title']}

**ID:** {proposal['id']}  
**Agent:** {proposal['agent_id']}  
**Status:** {proposal['status']}  
**Created:** {proposal['created_at']}

## Description

{proposal['description']}

## Proposed Changes

"""
        for change in proposal['proposed_changes']:
            md_content += f"""
### {change['file_path']} ({change['change_type']})

{change['description']}

```diff
{change.get('diff', 'No diff available')}
```
"""
        
        with open(md_path, 'w') as f:
            f.write(md_content)
        
        logger.debug(f"[Spec Agent] Saved proposal to {json_path} and {md_path}")
    
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

