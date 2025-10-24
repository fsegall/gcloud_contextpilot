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
from app.models.proposal import ChangeProposal, ProposedChange, ProposalDiff

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

    def __init__(
        self,
        workspace_path: str,
        workspace_id: str = "default",
        project_id: Optional[str] = None,
    ):
        """
        Initialize Development Agent.

        Args:
            workspace_path: Path to workspace directory
            workspace_id: Workspace identifier
            project_id: GCP project ID for Pub/Sub
        """
        # Initialize base agent
        super().__init__(
            workspace_id=workspace_id, agent_id="development", project_id=project_id
        )

        # Development-specific paths
        self.workspace_path = Path(workspace_path)
        # Get project root (go up from .contextpilot/workspaces/contextpilot to project root)
        self.project_root = self.workspace_path.parent.parent.parent.parent

        # Get Gemini API key
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not self.gemini_api_key:
            logger.info(
                "[DevelopmentAgent] GEMINI_API_KEY not set - agent will have limited functionality (expected in local mode)"
            )

        # Sandbox mode configuration
        self.sandbox_enabled = os.getenv("SANDBOX_ENABLED", "false").lower() == "true"
        self.sandbox_repo_url = os.getenv("SANDBOX_REPO_URL", "https://github.com/fsegall/contextpilot-sandbox.git")
        self.github_token = os.getenv("GITHUB_TOKEN")
        
        if self.sandbox_enabled and not self.github_token:
            logger.warning("[DevelopmentAgent] SANDBOX_ENABLED=true but GITHUB_TOKEN not set")
        
        logger.info(f"[DevelopmentAgent] Sandbox mode: {'enabled' if self.sandbox_enabled else 'disabled'}")

        # Subscribe to events
        self.subscribe_to_event(EventTypes.RETROSPECTIVE_TRIGGER)
        self.subscribe_to_event("spec.requirement.created")

        logger.info(f"[DevelopmentAgent] Initialized for workspace: {workspace_id}")
        logger.info(f"[DevelopmentAgent] Workspace path: {self.workspace_path}")

    def _generate_overall_diff(
        self, proposed_changes: List[ProposedChange]
    ) -> ProposalDiff:
        """Generate overall diff from individual changes"""
        diff_content = ""

        for change in proposed_changes:
            if change.diff:
                diff_content += f"--- {change.file_path}\n"
                diff_content += f"+++ {change.file_path}\n"
                diff_content += change.diff + "\n\n"

        return ProposalDiff(format="unified", content=diff_content.strip())

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
        logger.info(
            f"[DevelopmentAgent] Processing retrospective: {data.get('retrospective_id')}"
        )

        # For now, just log - actual implementation will be triggered manually
        # to avoid auto-generating code without user review
        logger.info(
            "[DevelopmentAgent] Retrospective received - awaiting manual implementation request"
        )

    async def _handle_spec_requirement(self, data: Dict) -> None:
        """
        Process spec requirement and generate implementation.

        Args:
            data: Spec requirement event data
        """
        logger.info(
            f"[DevelopmentAgent] Processing spec requirement: {data.get('requirement_id')}"
        )

    async def _get_project_context(self) -> str:
        """
        Get comprehensive project context (same as "Ask Claude" feature).

        Uses Spec Agent's context generation to ensure Development Agent
        has full awareness of project structure, specs, and recent changes.

        Returns:
            Project context summary string
        """
        try:
            from app.agents.spec_agent import SpecAgent

            logger.info("[DevelopmentAgent] Loading project context via Spec Agent...")

            # Initialize Spec Agent for context retrieval
            spec_agent = SpecAgent(
                workspace_path=str(self.workspace_path),
                workspace_id=self.workspace_id,
                project_id=self.project_id,
            )

            # Generate comprehensive context (same as Claude gets)
            context = spec_agent.generate_context_summary(proposal_type="development")

            logger.info(
                f"[DevelopmentAgent] Loaded {len(context)} chars of project context"
            )
            return context

        except Exception as e:
            logger.error(f"[DevelopmentAgent] Error loading project context: {e}")
            # Fallback to basic context
            return self._get_basic_fallback_context()

    def _get_basic_fallback_context(self) -> str:
        """
        Get basic project context if Spec Agent fails.

        Returns:
            Minimal context string
        """
        try:
            readme_path = self.project_root / "README.md"
            readme_content = ""
            if readme_path.exists():
                readme_content = readme_path.read_text(encoding="utf-8")[:1000]

            return f"""# Project Context (Basic)

## README
{readme_content if readme_content else "README.md not found"}

## Workspace
- Path: {self.workspace_path}
- ID: {self.workspace_id}

**Note**: Full context unavailable. Using minimal fallback.
"""
        except Exception as e:
            logger.error(f"[DevelopmentAgent] Error in fallback context: {e}")
            return "# Project Context\n\nContext unavailable."

    async def implement_feature(
        self,
        description: str,
        target_files: Optional[List[str]] = None,
        context: Optional[Dict] = None,
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
        # Check if sandbox mode is enabled
        if self.sandbox_enabled:
            logger.info("[DevelopmentAgent] Sandbox mode enabled - implementing directly in sandbox")
            branch_name = await self._implement_in_sandbox(description, context)
            if branch_name:
                # Create a proposal to track the sandbox implementation
                return await self._create_sandbox_proposal(description, branch_name, context)
            else:
                logger.warning("[DevelopmentAgent] Sandbox implementation failed, falling back to proposal mode")
        
        # Original proposal-based implementation
        if not self.gemini_api_key:
            logger.error(
                "[DevelopmentAgent] Cannot implement feature - GEMINI_API_KEY not set"
            )
            return None

        logger.info(f"[DevelopmentAgent] Implementing feature: {description[:100]}...")

        try:
            # Step 0: Get project context (like Claude does)
            project_context = await self._get_project_context()
            logger.info(
                f"[DevelopmentAgent] Loaded project context ({len(project_context)} chars)"
            )

            # Merge with provided context
            if context:
                context["project_summary"] = project_context
            else:
                context = {"project_summary": project_context}

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
                full_path = self.project_root / file_path
                if full_path.exists():
                    file_contents[file_path] = read_file_safe(
                        str(file_path), str(self.project_root)
                    )
                else:
                    file_contents[file_path] = None  # New file

            # Step 3: Generate implementation with Gemini
            implementations = await self._generate_code_with_ai(
                description=description, file_contents=file_contents, context=context
            )

            if not implementations:
                logger.warning("[DevelopmentAgent] No implementations generated")
                return None

            # Step 4: Create proposal with diffs
            proposal_id = await self._create_implementation_proposal(
                description=description,
                implementations=implementations,
                file_contents=file_contents,
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
                        "files_modified": len(implementations),
                    },
                )

            return proposal_id

        except Exception as e:
            logger.error(
                f"[DevelopmentAgent] Error implementing feature: {e}", exc_info=True
            )
            self.increment_metric("errors")
            return None

    async def _infer_target_files(
        self, description: str, context: Optional[Dict]
    ) -> List[str]:
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
            url = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1024},
            }
            headers = {"Content-Type": "application/json"}

            response = requests.post(
                f"{url}?key={self.gemini_api_key}",
                json=payload,
                headers=headers,
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                text = (
                    result.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                    .strip()
                )

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
        # In Cloud Run, we don't have access to the full workspace
        # So we provide a static structure based on the actual project
        structure = {
            "backend": [
                "back-end/app/agents/base_agent.py",
                "back-end/app/agents/retrospective_agent.py", 
                "back-end/app/agents/development_agent.py",
                "back-end/app/agents/spec_agent.py",
                "back-end/app/agents/git_agent.py",
                "back-end/app/agents/context_agent.py",
                "back-end/app/agents/coach_agent.py",
                "back-end/app/agents/milestone_agent.py",
                "back-end/app/routers/proposals.py",
                "back-end/app/models/proposal.py",
                "back-end/app/services/event_bus.py",
                "back-end/app/server.py"
            ],
            "extension": [
                "extension/src/views/proposals.ts",
                "extension/src/commands/index.ts",
                "extension/src/services/contextpilot.ts",
                "extension/package.json"
            ],
            "docs": [
                "docs/agent_improvements_retro-20251022-012119.md",
                "GIT_ARCHITECTURE.md",
                "AGENT_INTERFACE_SPEC.md"
            ]
        }
        
        logger.info(f"[DevelopmentAgent] Using static workspace structure with {sum(len(files) for files in structure.values())} files")
        return structure

    async def _implement_in_sandbox(self, description: str, context: Optional[Dict] = None) -> Optional[str]:
        """
        Implement feature directly in sandbox repository.
        
        Args:
            description: Feature description
            context: Additional context
            
        Returns:
            Branch name if successful, None otherwise
        """
        if not self.sandbox_enabled:
            logger.info("[DevelopmentAgent] Sandbox mode disabled, falling back to proposal mode")
            return await self.implement_feature(description, context)
            
        if not self.github_token:
            logger.error("[DevelopmentAgent] GITHUB_TOKEN required for sandbox mode")
            return None
            
        try:
            # Generate branch name
            branch_name = f"dev-agent/{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            logger.info(f"[DevelopmentAgent] Starting sandbox implementation: {branch_name}")
            
            # Step 1: Clone sandbox repo
            sandbox_path = await self._clone_sandbox_repo()
            if not sandbox_path:
                return None
                
            # Step 2: Create branch
            await self._create_branch(sandbox_path, branch_name)
            
            # Step 3: Analyze and implement changes
            target_files = await self._infer_target_files_from_sandbox(description, sandbox_path)
            if not target_files:
                logger.warning("[DevelopmentAgent] Could not determine target files in sandbox")
                return None
                
            # Step 4: Generate and apply code changes
            changes_made = await self._apply_code_changes(sandbox_path, target_files, description, context)
            if not changes_made:
                logger.warning("[DevelopmentAgent] No changes were made in sandbox")
                return None
                
            # Step 5: Commit and push
            commit_message = await self._generate_commit_message(description, changes_made)
            await self._commit_and_push(sandbox_path, branch_name, commit_message)
            
            logger.info(f"[DevelopmentAgent] Sandbox implementation completed: {branch_name}")
            return branch_name
            
        except Exception as e:
            logger.error(f"[DevelopmentAgent] Error in sandbox implementation: {e}", exc_info=True)
            return None

    async def _clone_sandbox_repo(self) -> Optional[Path]:
        """Clone sandbox repository to temporary directory."""
        try:
            import tempfile
            import subprocess
            
            # Create temporary directory
            temp_dir = Path(tempfile.mkdtemp(prefix="contextpilot-sandbox-"))
            sandbox_path = temp_dir / "sandbox"
            
            # Clone with token authentication
            repo_url = self.sandbox_repo_url.replace("https://", f"https://{self.github_token}@")
            
            result = subprocess.run([
                "git", "clone", repo_url, str(sandbox_path)
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                logger.error(f"[DevelopmentAgent] Failed to clone sandbox: {result.stderr}")
                return None
                
            logger.info(f"[DevelopmentAgent] Cloned sandbox to: {sandbox_path}")
            return sandbox_path
            
        except Exception as e:
            logger.error(f"[DevelopmentAgent] Error cloning sandbox: {e}")
            return None

    async def _create_branch(self, sandbox_path: Path, branch_name: str) -> bool:
        """Create new branch in sandbox."""
        try:
            import subprocess
            
            result = subprocess.run([
                "git", "checkout", "-b", branch_name
            ], cwd=sandbox_path, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.error(f"[DevelopmentAgent] Failed to create branch: {result.stderr}")
                return False
                
            logger.info(f"[DevelopmentAgent] Created branch: {branch_name}")
            return True
            
        except Exception as e:
            logger.error(f"[DevelopmentAgent] Error creating branch: {e}")
            return False

    async def _infer_target_files_from_sandbox(self, description: str, sandbox_path: Path) -> List[str]:
        """Infer target files by scanning actual sandbox repository."""
        try:
            # Get actual file structure from sandbox
            structure = {"backend": [], "extension": [], "docs": []}
            
            for key, pattern in [
                ("backend", "back-end/app/**/*.py"),
                ("extension", "extension/src/**/*.ts"),
                ("docs", "docs/**/*.md"),
            ]:
                files = list(sandbox_path.glob(pattern))
                structure[key] = [str(f.relative_to(sandbox_path)) for f in files[:50]]
            
            # Use AI to infer files (same logic as before but with real structure)
            prompt = f"""Based on this feature request:

"{description}"

And this workspace structure:
{json.dumps(structure, indent=2)}

Identify the files that need to be created or modified. Return ONLY a JSON array of file paths.
Format: ["path/to/file1.py", "path/to/file2.ts"]

Consider:
- Backend files are in back-end/app/
- Frontend/extension files are in extension/src/
- Keep paths relative to workspace root
"""

            if not self.gemini_api_key:
                logger.warning("[DevelopmentAgent] No Gemini API key for file inference")
                return []
                
            url = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1024},
            }
            headers = {"Content-Type": "application/json"}

            response = requests.post(
                f"{url}?key={self.gemini_api_key}",
                json=payload,
                headers=headers,
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                text = (
                    result.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                    .strip()
                )

                if "[" in text and "]" in text:
                    start = text.index("[")
                    end = text.rindex("]") + 1
                    file_list = json.loads(text[start:end])
                    logger.info(f"[DevelopmentAgent] Inferred target files: {file_list}")
                    return file_list

            logger.warning("[DevelopmentAgent] Could not infer target files from AI")
            return []

        except Exception as e:
            logger.error(f"[DevelopmentAgent] Error inferring files from sandbox: {e}")
            return []

    async def _apply_code_changes(self, sandbox_path: Path, target_files: List[str], description: str, context: Optional[Dict]) -> List[str]:
        """Apply code changes to files in sandbox."""
        changes_made = []
        
        try:
            for file_path in target_files:
                full_path = sandbox_path / file_path
                
                # Read current content
                current_content = ""
                if full_path.exists():
                    current_content = full_path.read_text(encoding="utf-8")
                
                # Generate new content using AI
                new_content = await self._generate_code_with_ai(
                    description, 
                    {file_path: current_content}, 
                    context or {}
                )
                
                if new_content and file_path in new_content:
                    # Write new content
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    full_path.write_text(new_content[file_path], encoding="utf-8")
                    changes_made.append(file_path)
                    logger.info(f"[DevelopmentAgent] Modified file: {file_path}")
                    
        except Exception as e:
            logger.error(f"[DevelopmentAgent] Error applying changes: {e}")
            
        return changes_made

    async def _generate_commit_message(self, description: str, changes_made: List[str]) -> str:
        """Generate commit message for changes."""
        try:
            if self.gemini_api_key:
                # Use AI to generate commit message
                prompt = f"""Generate a conventional commit message for these changes:

Description: {description}
Files changed: {', '.join(changes_made)}

Format: type(scope): description

Examples:
- feat(agents): add error handling to base agent
- fix(api): resolve timeout issues in proposals endpoint
- docs(readme): update installation instructions
"""

                url = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.3, "maxOutputTokens": 200},
                }
                headers = {"Content-Type": "application/json"}

                response = requests.post(
                    f"{url}?key={self.gemini_api_key}",
                    json=payload,
                    headers=headers,
                    timeout=30,
                )

                if response.status_code == 200:
                    result = response.json()
                    message = (
                        result.get("candidates", [{}])[0]
                        .get("content", {})
                        .get("parts", [{}])[0]
                        .get("text", "")
                        .strip()
                    )
                    if message:
                        return message
                        
        except Exception as e:
            logger.debug(f"[DevelopmentAgent] Error generating AI commit message: {e}")
            
        # Fallback to simple message
        return f"feat: {description[:50]}"

    async def _commit_and_push(self, sandbox_path: Path, branch_name: str, commit_message: str) -> bool:
        """Commit changes and push to sandbox repository."""
        try:
            import subprocess
            
            # Add all changes
            result = subprocess.run([
                "git", "add", "."
            ], cwd=sandbox_path, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.error(f"[DevelopmentAgent] Failed to add changes: {result.stderr}")
                return False
                
            # Commit changes
            result = subprocess.run([
                "git", "commit", "-m", commit_message
            ], cwd=sandbox_path, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.error(f"[DevelopmentAgent] Failed to commit: {result.stderr}")
                return False
                
            # Push branch
            result = subprocess.run([
                "git", "push", "origin", branch_name
            ], cwd=sandbox_path, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                logger.error(f"[DevelopmentAgent] Failed to push: {result.stderr}")
                return False
                
            logger.info(f"[DevelopmentAgent] Successfully pushed branch: {branch_name}")
            return True
            
        except Exception as e:
            logger.error(f"[DevelopmentAgent] Error committing and pushing: {e}")
            return False

    async def _create_sandbox_proposal(self, description: str, branch_name: str, context: Optional[Dict]) -> Optional[str]:
        """Create a proposal to track sandbox implementation."""
        try:
            proposal_id = f"dev-sandbox-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            # Create proposal with sandbox info
            proposal_data = {
                "id": proposal_id,
                "workspace_id": self.workspace_id,
                "user_id": "system",
                "agent_id": "development",
                "is_system_proposal": True,
                "title": f"🤖 Sandbox Implementation: {description[:60]}",
                "description": f"""# Sandbox Implementation

**Generated by:** Development Agent (Sandbox Mode)
**Branch:** `{branch_name}`
**Date:** {datetime.now(timezone.utc).isoformat()}

## Feature Request

{description}

## Implementation Status

✅ **Code implemented** in sandbox repository
✅ **Branch created:** `{branch_name}`
✅ **Changes committed** and pushed
🔄 **PR will be created** automatically via GitHub Actions

## Next Steps

1. Review the changes in the [sandbox repository](https://github.com/fsegall/contextpilot-sandbox/tree/{branch_name})
2. GitHub Actions will automatically create a PR to the main repository
3. Review and merge the PR when ready

## Context

{context.get('retrospective_id', 'Manual request') if context else 'Manual request'}
""",
                "proposed_changes": [
                    {
                        "file_path": f"sandbox-branch-{branch_name}",
                        "change_type": "create",
                        "description": f"Sandbox implementation in branch {branch_name}",
                        "before": "",
                        "after": f"Branch {branch_name} with implemented changes",
                        "diff": f"Sandbox branch: {branch_name}\nRepository: https://github.com/fsegall/contextpilot-sandbox"
                    }
                ],
                "status": "pending",
                "created_at": datetime.now(timezone.utc),
                "metadata": {
                    "sandbox_branch": branch_name,
                    "implementation_type": "sandbox",
                    "retrospective_id": context.get("retrospective_id") if context else None
                }
            }

            # Save to repository
            repo = get_proposal_repository()
            await repo.create_proposal(ChangeProposal(**proposal_data))
            
            logger.info(f"[DevelopmentAgent] Created sandbox proposal: {proposal_id}")
            return proposal_id
            
        except Exception as e:
            logger.error(f"[DevelopmentAgent] Error creating sandbox proposal: {e}")
            return None

    async def _generate_code_with_ai(
        self,
        description: str,
        file_contents: Dict[str, Optional[str]],
        context: Optional[Dict],
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
                ".md": "Markdown",
            }
            language = language_map.get(ext, "code")

            # Get project context summary
            project_summary = context.get("project_summary", "") if context else ""

            # Build prompt
            if current_content:
                prompt = f"""You are an expert {language} developer working on the ContextPilot project.

**PROJECT CONTEXT:**
{project_summary[:2000] if project_summary else "No project context available"}

**Feature Request:**
{description}

**Current File ({file_path}):**
```{language.lower()}
{current_content}
```

**Instructions:**
1. Read and understand the project context before making changes
2. Implement the feature while preserving existing functionality
3. Follow the existing code style and patterns shown in the project
4. Ensure compatibility with the project's architecture
5. Add comments for complex logic
6. Ensure the code is production-ready
7. Return ONLY the complete modified file content, no explanations

**Modified File:**"""
            else:
                prompt = f"""You are an expert {language} developer working on the ContextPilot project.

**PROJECT CONTEXT:**
{project_summary[:2000] if project_summary else "No project context available"}

**Feature Request:**
{description}

**New File ({file_path}):**

**Instructions:**
1. Read and understand the project context before creating the file
2. Create a complete, production-ready implementation
3. Follow best practices for {language} and the project's conventions
4. Ensure compatibility with the existing project architecture
5. Add appropriate imports and dependencies
6. Include comments for clarity
7. Return ONLY the complete file content, no explanations

**File Content:**"""

            try:
                url = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.4, "maxOutputTokens": 8192},
                }
                headers = {"Content-Type": "application/json"}

                response = requests.post(
                    f"{url}?key={self.gemini_api_key}",
                    json=payload,
                    headers=headers,
                    timeout=60,
                )

                if response.status_code == 200:
                    result = response.json()
                    generated_code = (
                        result.get("candidates", [{}])[0]
                        .get("content", {})
                        .get("parts", [{}])[0]
                        .get("text", "")
                        .strip()
                    )

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
                    logger.info(
                        f"[DevelopmentAgent] Generated {len(generated_code)} chars for {file_path}"
                    )
                else:
                    logger.error(
                        f"[DevelopmentAgent] Gemini API error: {response.status_code} - {response.text[:200]}"
                    )

            except Exception as e:
                logger.error(
                    f"[DevelopmentAgent] Error generating code for {file_path}: {e}"
                )

        return implementations

    async def _create_implementation_proposal(
        self,
        description: str,
        implementations: Dict[str, str],
        file_contents: Dict[str, Optional[str]],
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
                new_content=new_content,
            )

            proposed_changes.append(
                ProposedChange(
                    file_path=file_path,
                    change_type=change_type,
                    description=f"{'Create' if change_type == 'create' else 'Modify'} {file_path}",
                    before=old_content or "",
                    after=new_content,
                    diff=diff,
                )
            )

        # Generate overall diff
        overall_diff = self._generate_overall_diff(proposed_changes)

        # Create proposal
        proposal = ChangeProposal(
            id=proposal_id,
            workspace_id=self.workspace_id,
            user_id="system",
            agent_id="development",
            is_system_proposal=True,
            title=(
                f"💻 {description[:80]}"
                if len(description) > 80
                else f"💻 {description}"
            ),
            diff=overall_diff,
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
                "model": "gemini-2.5-flash",
            },
        )

        # Save to Firestore
        try:
            if os.getenv("FIRESTORE_ENABLED", "false").lower() == "true":
                repo = get_proposal_repository()
                repo.create(proposal.model_dump())
                logger.info(
                    f"[DevelopmentAgent] Saved proposal to Firestore: {proposal_id}"
                )
                return proposal_id
            else:
                logger.warning(
                    "[DevelopmentAgent] Firestore not enabled - proposal not saved"
                )
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
    project_id: Optional[str] = None,
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
        workspace_path=workspace_path, workspace_id=workspace_id, project_id=project_id
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
                "assigned_to": item.get("assigned_to"),
            },
        )

        if proposal_id:
            proposal_ids.append(proposal_id)

    return proposal_ids
