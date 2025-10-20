"""
Development Agent - Code Implementation Generator

Generates actual code implementations from:
- Retrospective action items
- Spec agent requirements
- Manual feature requests

Uses Gemini API to analyze existing code and generate production-ready implementations.
"""
import os
import logging
import requests
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from pathlib import Path
import json

from app.agents.base_agent import BaseAgent
from app.services.event_bus import EventTypes, Topics
from app.agents.diff_generator import generate_unified_diff, read_file_safe
from app.repositories.proposal_repository import get_proposal_repository

logger = logging.getLogger(__name__)


class DevelopmentAgent(BaseAgent):
    """
    Development Agent generates code implementations using AI.
    
    Responsibilities:
    - Analyze feature requests and action items
    - Generate actual code implementations
    - Create proposals with real code diffs
    - Consider existing codebase context
    - Follow project conventions and patterns
    """
    
    def __init__(self, workspace_path: str, workspace_id: str = "default", project_id: Optional[str] = None):
        """
        Initialize Development Agent.
        
        Args:
            workspace_path: Path to workspace directory
            workspace_id: Workspace identifier
            project_id: GCP project ID for Pub/Sub
        """
        # Initialize base agent
        super().__init__(workspace_id=workspace_id, agent_id='development', project_id=project_id)
        
        # Development-specific paths
        self.workspace_path = Path(workspace_path)
        
        # Get Gemini API key
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not self.gemini_api_key:
            logger.warning("[DevelopmentAgent] GEMINI_API_KEY not set - agent will have limited functionality")
        
        # Subscribe to events
        self.subscribe_to_event(EventTypes.RETROSPECTIVE_SUMMARY)
        self.subscribe_to_event("spec.requirement.created")
        
        logger.info(f"[DevelopmentAgent] Initialized for workspace: {workspace_id}")
        logger.info(f"[DevelopmentAgent] Workspace path: {self.workspace_path}")
    
    async def handle_event(self, event_type: str, data: Dict) -> None:
        """
        Handle incoming events.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        try:
            logger.info(f"[DevelopmentAgent] Received event: {event_type}")
            
            if event_type == EventTypes.RETROSPECTIVE_SUMMARY:
                await self._handle_retrospective(data)
            elif event_type == "spec.requirement.created":
                await self._handle_spec_requirement(data)
            
            self.increment_metric("events_processed")
        except Exception as e:
            logger.error(f"[DevelopmentAgent] Error handling {event_type}: {e}")
            self.increment_metric("errors")
    
    async def _handle_retrospective(self, data: Dict) -> None:
        """
        Process retrospective summary and generate code implementations.
        
        Args:
            data: Retrospective event data
        """
        logger.info(f"[DevelopmentAgent] Processing retrospective: {data.get('retrospective_id')}")
        
        # For now, just log - actual implementation will be triggered manually
        # to avoid auto-generating code without user review
        logger.info("[DevelopmentAgent] Retrospective received - awaiting manual implementation request")
    
    async def _handle_spec_requirement(self, data: Dict) -> None:
        """
        Process spec requirement and generate implementation.
        
        Args:
            data: Spec requirement event data
        """
        logger.info(f"[DevelopmentAgent] Processing spec requirement: {data.get('requirement_id')}")
    
    async def implement_feature(
        self,
        description: str,
        target_files: Optional[List[str]] = None,
        context: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Generate code implementation for a feature.
        
        Args:
            description: Feature description or action item
            target_files: List of files to modify (optional - will be inferred if not provided)
            context: Additional context (existing code, specs, etc)
        
        Returns:
            Proposal ID if created, None otherwise
        """
        if not self.gemini_api_key:
            logger.error("[DevelopmentAgent] Cannot implement feature - GEMINI_API_KEY not set")
            return None
        
        logger.info(f"[DevelopmentAgent] Implementing feature: {description[:100]}...")
        
        try:
            # Step 1: Analyze the request and determine affected files
            if not target_files:
                target_files = await self._infer_target_files(description, context)
            
            if not target_files:
                logger.warning("[DevelopmentAgent] Could not determine target files")
                return None
            
            logger.info(f"[DevelopmentAgent] Target files: {target_files}")
            
            # Step 2: Read existing code for context
            file_contents = {}
            for file_path in target_files:
                full_path = self.workspace_path / file_path
                if full_path.exists():
                    file_contents[file_path] = read_file_safe(str(file_path), str(self.workspace_path))
                else:
                    file_contents[file_path] = None  # New file
            
            # Step 3: Generate implementation with Gemini
            implementations = await self._generate_code_with_ai(
                description=description,
                file_contents=file_contents,
                context=context
            )
            
            if not implementations:
                logger.warning("[DevelopmentAgent] No implementations generated")
                return None
            
            # Step 4: Create proposal with diffs
            proposal_id = await self._create_implementation_proposal(
                description=description,
                implementations=implementations,
                file_contents=file_contents
            )
            
            if proposal_id:
                logger.info(f"[DevelopmentAgent] Created proposal: {proposal_id}")
                
                # Publish event
                await self.publish_event(
                    topic=Topics.PROPOSAL_EVENTS,
                    event_type="proposal.created.v1",
                    data={
                        "proposal_id": proposal_id,
                        "agent_id": "development",
                        "workspace_id": self.workspace_id,
                        "files_modified": len(implementations)
                    }
                )
            
            return proposal_id
            
        except Exception as e:
            logger.error(f"[DevelopmentAgent] Error implementing feature: {e}", exc_info=True)
            self.increment_metric("errors")
            return None
    
    async def _infer_target_files(self, description: str, context: Optional[Dict]) -> List[str]:
        """
        Use AI to infer which files should be modified.
        
        Args:
            description: Feature description
            context: Additional context
        
        Returns:
            List of file paths
        """
        # Get workspace structure
        workspace_structure = self._get_workspace_structure()
        
        prompt = f"""Based on this feature request:

"{description}"

And this workspace structure:
{json.dumps(workspace_structure, indent=2)}

Identify the files that need to be created or modified. Return ONLY a JSON array of file paths.
Format: ["path/to/file1.py", "path/to/file2.ts"]

Consider:
- Backend files are in back-end/app/
- Frontend/extension files are in extension/src/
- Keep paths relative to workspace root
"""

        try:
            url = "https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash-exp:generateContent"
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 1024
                }
            }
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(
                f"{url}?key={self.gemini_api_key}",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                
                # Extract JSON array from response
                if "[" in text and "]" in text:
                    start = text.index("[")
                    end = text.rindex("]") + 1
                    file_list = json.loads(text[start:end])
                    return file_list
            
            logger.warning("[DevelopmentAgent] Could not infer target files from AI")
            return []
            
        except Exception as e:
            logger.error(f"[DevelopmentAgent] Error inferring files: {e}")
            return []
    
    def _get_workspace_structure(self) -> Dict:
        """Get a simplified workspace structure for AI context."""
        structure = {
            "backend": [],
            "extension": [],
            "docs": []
        }
        
        # Scan key directories
        for key, pattern in [
            ("backend", "back-end/app/**/*.py"),
            ("extension", "extension/src/**/*.ts"),
            ("docs", "docs/**/*.md")
        ]:
            try:
                files = list(self.workspace_path.glob(pattern))
                structure[key] = [str(f.relative_to(self.workspace_path)) for f in files[:50]]  # Limit to 50 files
            except Exception as e:
                logger.debug(f"Error scanning {pattern}: {e}")
        
        return structure
    
    async def _generate_code_with_ai(
        self,
        description: str,
        file_contents: Dict[str, Optional[str]],
        context: Optional[Dict]
    ) -> Dict[str, str]:
        """
        Generate code implementations using Gemini.
        
        Args:
            description: Feature description
            file_contents: Current file contents (or None for new files)
            context: Additional context
        
        Returns:
            Dict mapping file paths to new content
        """
        implementations = {}
        
        for file_path, current_content in file_contents.items():
            logger.info(f"[DevelopmentAgent] Generating code for: {file_path}")
            
            # Determine file type and language
            ext = Path(file_path).suffix
            language_map = {
                ".py": "Python",
                ".ts": "TypeScript",
                ".js": "JavaScript",
                ".tsx": "TypeScript React",
                ".md": "Markdown"
            }
            language = language_map.get(ext, "code")
            
            # Build prompt
            if current_content:
                prompt = f"""You are an expert {language} developer. Modify this file to implement the following feature:

**Feature Request:**
{description}

**Current File ({file_path}):**
```{language.lower()}
{current_content}
```

**Instructions:**
1. Implement the feature while preserving existing functionality
2. Follow the existing code style and patterns
3. Add comments for complex logic
4. Ensure the code is production-ready
5. Return ONLY the complete modified file content, no explanations

**Modified File:**"""
            else:
                prompt = f"""You are an expert {language} developer. Create a new file to implement the following feature:

**Feature Request:**
{description}

**New File ({file_path}):**

**Instructions:**
1. Create a complete, production-ready implementation
2. Follow best practices for {language}
3. Add appropriate imports and dependencies
4. Include comments for clarity
5. Return ONLY the complete file content, no explanations

**File Content:**"""
            
            try:
                url = "https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash-exp:generateContent"
                payload = {
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }],
                    "generationConfig": {
                        "temperature": 0.4,
                        "maxOutputTokens": 8192
                    }
                }
                headers = {"Content-Type": "application/json"}
                
                response = requests.post(
                    f"{url}?key={self.gemini_api_key}",
                    json=payload,
                    headers=headers,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    generated_code = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                    
                    # Clean up markdown code blocks if present
                    if "```" in generated_code:
                        lines = generated_code.split("\n")
                        code_lines = []
                        in_code_block = False
                        for line in lines:
                            if line.startswith("```"):
                                in_code_block = not in_code_block
                                continue
                            if in_code_block or not generated_code.startswith("```"):
                                code_lines.append(line)
                        generated_code = "\n".join(code_lines).strip()
                    
                    implementations[file_path] = generated_code
                    logger.info(f"[DevelopmentAgent] Generated {len(generated_code)} chars for {file_path}")
                else:
                    logger.error(f"[DevelopmentAgent] Gemini API error: {response.status_code} - {response.text[:200]}")
                
            except Exception as e:
                logger.error(f"[DevelopmentAgent] Error generating code for {file_path}: {e}")
        
        return implementations
    
    async def _create_implementation_proposal(
        self,
        description: str,
        implementations: Dict[str, str],
        file_contents: Dict[str, Optional[str]]
    ) -> Optional[str]:
        """
        Create a proposal with implementation diffs.
        
        Args:
            description: Feature description
            implementations: Generated code for each file
            file_contents: Original file contents
        
        Returns:
            Proposal ID if created
        """
        from app.models.proposal import ChangeProposal, ProposedChange
        
        proposal_id = f"dev-{int(datetime.now(timezone.utc).timestamp())}"
        
        # Build proposed changes with diffs
        proposed_changes = []
        for file_path, new_content in implementations.items():
            old_content = file_contents.get(file_path)
            
            change_type = "create" if old_content is None else "modify"
            
            # Generate diff
            diff = generate_unified_diff(
                file_path=file_path,
                old_content=old_content or "",
                new_content=new_content
            )
            
            proposed_changes.append(
                ProposedChange(
                    file_path=file_path,
                    change_type=change_type,
                    description=f"{'Create' if change_type == 'create' else 'Modify'} {file_path}",
                    before=old_content or "",
                    after=new_content,
                    diff=diff
                )
            )
        
        # Create proposal
        proposal = ChangeProposal(
            id=proposal_id,
            workspace_id=self.workspace_id,
            user_id="system",
            agent_id="development",
            is_system_proposal=True,
            title=f"💻 {description[:80]}" if len(description) > 80 else f"💻 {description}",
            description=f"""# Implementation Proposal

**Generated by:** Development Agent
**Date:** {datetime.now(timezone.utc).isoformat()}

## Feature Request

{description}

## Implementation

This proposal implements the requested feature with the following changes:

{chr(10).join(f"- {change.change_type.upper()}: `{change.file_path}`" for change in proposed_changes)}

## Next Steps

1. Review the proposed implementation
2. Test the changes if needed
3. Approve to apply the changes automatically
""",
            status="pending",
            proposed_changes=proposed_changes,
            created_at=datetime.now(timezone.utc),
            agent_metadata={
                "implementation_approach": "ai_generated",
                "model": "gemini-2.0-flash-exp"
            }
        )
        
        # Save to Firestore
        try:
            if os.getenv("FIRESTORE_ENABLED", "false").lower() == "true":
                repo = get_proposal_repository()
                repo.save(proposal)
                logger.info(f"[DevelopmentAgent] Saved proposal to Firestore: {proposal_id}")
                return proposal_id
            else:
                logger.warning("[DevelopmentAgent] Firestore not enabled - proposal not saved")
                return None
        except Exception as e:
            logger.error(f"[DevelopmentAgent] Error saving proposal: {e}")
            return None


# Utility function for CLI/API
async def implement_from_retrospective(
    workspace_id: str,
    retrospective_id: str,
    action_items: List[Dict],
    workspace_path: str,
    project_id: Optional[str] = None
) -> List[str]:
    """
    Generate implementations from retrospective action items.
    
    Args:
        workspace_id: Workspace identifier
        retrospective_id: Retrospective identifier
        action_items: List of action item dicts
        workspace_path: Path to workspace
        project_id: GCP project ID
    
    Returns:
        List of proposal IDs created
    """
    agent = DevelopmentAgent(
        workspace_path=workspace_path,
        workspace_id=workspace_id,
        project_id=project_id
    )
    
    proposal_ids = []
    
    for item in action_items:
        action = item.get("action", "")
        if not action:
            continue
        
        logger.info(f"[implement_from_retrospective] Processing: {action}")
        
        proposal_id = await agent.implement_feature(
            description=f"From retrospective {retrospective_id}: {action}",
            context={
                "retrospective_id": retrospective_id,
                "priority": item.get("priority"),
                "assigned_to": item.get("assigned_to")
            }
        )
        
        if proposal_id:
            proposal_ids.append(proposal_id)
    
    return proposal_ids

