"""
Git Context Manager - Core Git Operations

This module provides low-level git operations and workspace management.
It is actively used by:
- GitAgent (back-end/app/agents/git_agent.py) - Wraps commit operations
- Server endpoints (back-end/app/server.py) - Legacy endpoints for compatibility

Key responsibilities:
- Git repository initialization and management
- Commit operations with metadata tracking
- Workspace context file management (checkpoint.yaml, history.json)
- Markdown template initialization (context.md, milestones.md, timeline.md)
- Push operations to remote repositories

See GIT_ARCHITECTURE.md for complete documentation.
"""

import os
import git
import yaml
import json
import logging
from datetime import datetime
from openai import OpenAI
from app.utils.workspace_manager import get_workspace_path, ensure_workspace_exists
import shutil
from datetime import datetime, timezone
from typing import Optional
import httpx

# Use existing logger configuration (don't reconfigure)
logger = logging.getLogger(__name__)

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")


class Git_Context_Manager:

    def __init__(self, workspace_id: str = "default", user_id: Optional[str] = None):
        logger.info(
            f"Initializing Git_Context_Manager with workspace_id: {workspace_id}"
        )

        self.workspace_id = workspace_id
        self.user_id = user_id or workspace_id  # Default to workspace_id if no user
        self.api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")

        self.openai_key = os.getenv("OPENAI_API_KEY")
        if self.openai_key:
            logger.info("OpenAI API key found")
            self.client = OpenAI(api_key=self.openai_key)
        else:
            logger.warning("OpenAI API key not found in environment variables")
            self.client = None

        logger.info(f"Calling ensure_workspace_exists for workspace_id: {workspace_id}")
        ensure_workspace_exists(workspace_id)

        self.context_dir = get_workspace_path(workspace_id)
        logger.info(f"Context directory path: {self.context_dir}")

        self.checkpoint_path = os.path.join(self.context_dir, "checkpoint.yaml")
        self.history_path = os.path.join(self.context_dir, "history.json")
        logger.info(f"Checkpoint path: {self.checkpoint_path}")
        logger.info(f"History path: {self.history_path}")

        logger.info("Finding git root...")
        git_root = self.find_git_root()
        logger.info(f"Git root found: {git_root}")

        # Try to initialize git repo, but handle gracefully if git is not available
        try:
            # Check if .git directory exists before trying to create Repo
            git_dir = os.path.join(git_root, ".git")
            if os.path.isdir(git_dir) or os.path.isfile(git_dir):  # .git can be a file (worktree) or dir
                self.repo = git.Repo(git_root, search_parent_directories=True)
                self.project_root = self.repo.working_tree_dir
                logger.info(f"Git repository initialized. Project root: {self.project_root}")
            else:
                # No .git found - this is OK in Cloud Run mode
                environment = os.getenv("ENVIRONMENT", "local")
                if environment == "production" or os.getenv("USE_PUBSUB") == "true":
                    logger.info("No .git directory found - operating in API-only mode (Cloud Run)")
                    self.repo = None
                    self.project_root = git_root
                    logger.info(f"Using workspace path as project root: {self.project_root}")
                else:
                    # In local mode, try anyway (might be a bare repo or submodule)
                    try:
                        self.repo = git.Repo(git_root, search_parent_directories=True)
                        self.project_root = self.repo.working_tree_dir if self.repo.working_tree_dir else git_root
                        logger.info(f"Git repository initialized (bare or submodule). Project root: {self.project_root}")
                    except Exception as e:
                        logger.warning(f"Could not initialize git repo: {e}. Operating in API-only mode.")
                        self.repo = None
                        self.project_root = git_root
        except Exception as e:
            # Git not available or error initializing - this is OK in Cloud Run
            environment = os.getenv("ENVIRONMENT", "local")
            if environment == "production" or os.getenv("USE_PUBSUB") == "true":
                logger.info(f"Git repository not available - operating in API-only mode (Cloud Run): {e}")
                self.repo = None
                self.project_root = git_root
            else:
                logger.warning(f"Git repository initialization failed: {e}")
                # Still set repo to None to avoid crashes, but log warning
                self.repo = None
                self.project_root = git_root

        logger.info(f"Creating context directory: {self.context_dir}")
        os.makedirs(self.context_dir, exist_ok=True)

        if not os.path.exists(self.history_path):
            logger.info(f"Creating new history file: {self.history_path}")
            with open(self.history_path, "w") as f:
                json.dump([], f)
        else:
            logger.info(f"History file already exists: {self.history_path}")

        # Initialize markdown files from templates (always check)
        logger.info("Checking and initializing markdown files from templates...")
        self.initialize_markdown_files()

        logger.info("Git_Context_Manager initialization completed")

    def find_git_root(self):
        """Find git root directory, or return workspace path if git is not available (Cloud Run mode)."""
        logger.info("Starting git root search...")
        path = os.getcwd()
        logger.info(f"Starting from current directory: {path}")

        # In Cloud Run, git may not be available - check environment
        environment = os.getenv("ENVIRONMENT", "local")
        if environment == "production" or os.getenv("USE_PUBSUB") == "true":
            # Cloud Run mode - git operations are handled via GitHub API, not local git
            logger.info("Cloud Run mode detected - git operations will use GitHub API")
            # Return workspace path as fallback (git operations will be API-based)
            workspace_path = get_workspace_path(self.workspace_id)
            logger.info(f"Using workspace path as git root fallback: {workspace_path}")
            return str(workspace_path)

        # Local mode - try to find actual git repository
        while path != os.path.dirname(path):
            git_dir = os.path.join(path, ".git")
            logger.debug(f"Checking for .git directory at: {git_dir}")

            if os.path.isdir(git_dir):
                logger.info(f"Found git root at: {path}")
                return path
            path = os.path.dirname(path)
            logger.debug(f"Moving up to parent directory: {path}")

        # Git not found - use workspace path as fallback
        logger.warning("Git directory not found in any parent directory - using workspace path as fallback")
        workspace_path = get_workspace_path(self.workspace_id)
        logger.info(f"Using workspace path as git root fallback: {workspace_path}")
        return str(workspace_path)

    def initialize_markdown_files(self):
        logger.info(
            f"Initializing markdown files from templates directory: {TEMPLATES_DIR}"
        )

        try:
            # Get current context to personalize templates
            context = self.get_project_context()
            checkpoint = context.get("checkpoint", {})
            project_name = checkpoint.get("project_name", "Unknown Project")
            goal = checkpoint.get("goal", "No goal defined")
            current_status = checkpoint.get("current_status", "No status")

            for filename in os.listdir(TEMPLATES_DIR):
                if filename.endswith(".md"):
                    template_file = os.path.join(TEMPLATES_DIR, filename)
                    workspace_file = os.path.join(self.context_dir, filename)

                    logger.info(f"Processing template: {filename}")
                    logger.debug(f"Template file: {template_file}")
                    logger.debug(f"Workspace file: {workspace_file}")

                    if not os.path.exists(workspace_file):
                        logger.info(f"Creating personalized template: {workspace_file}")

                        # Read template content
                        with open(template_file, "r", encoding="utf-8") as f:
                            template_content = f.read()

                        # Personalize content based on project context
                        personalized_content = self._personalize_template(
                            template_content,
                            project_name,
                            goal,
                            current_status,
                            filename,
                        )

                        # Write personalized content
                        with open(workspace_file, "w", encoding="utf-8") as f:
                            f.write(personalized_content)

                        logger.info(f"✅ Successfully created: {workspace_file}")
                    else:
                        logger.info(f"ℹ️ File already exists: {workspace_file}")
        except Exception as e:
            logger.error(f"Error initializing markdown files: {str(e)}")
            raise

    def _personalize_template(
        self,
        content: str,
        project_name: str,
        goal: str,
        current_status: str,
        filename: str,
    ) -> str:
        """Personalize template content with project-specific information."""
        logger.info(f"Personalizing template: {filename}")

        # Replace placeholders with actual project data
        personalized = content.replace("ContextPilot", project_name)
        personalized = personalized.replace(
            "(framework de gerenciamento de escopo e contexto com LLMs)", f"({goal})"
        )
        personalized = personalized.replace(
            "Status: Ativo, preparado para hackathon", f"Status: {current_status}"
        )

        # Add project-specific header if not present
        if filename == "context.md":
            header = f"""# 📄 {project_name} — Contexto Atual

## 🎯 Visão geral
- Projeto: {project_name}
- Status: {current_status}
- Objetivo: {goal}

"""
            if not personalized.startswith(f"# 📄 {project_name}"):
                personalized = header + personalized

        elif filename == "milestones.md":
            header = f"""# 🏁 {project_name} — Milestones

## ✅ Concluídos
- 🟢 Projeto inicializado
- 🟢 Workspace configurado

## 🔜 Próximos
- 🌟 Definir milestones específicos do projeto
- 📄 Documentar progresso
- 🎯 Alcançar objetivo: {goal}

"""
            if not personalized.startswith(f"# 🏁 {project_name}"):
                personalized = header + personalized

        elif filename == "timeline.md":
            header = f"""# 🕒 {project_name} — Timeline de contexto

## {datetime.now().strftime('%Y-%m-%d')}
- Projeto inicializado
- Workspace criado
- Status atual: {current_status}

## Próximos dias
- Desenvolver milestones específicos
- Documentar progresso
- Trabalhar no objetivo: {goal}

"""
            if not personalized.startswith(f"# 🕒 {project_name}"):
                personalized = header + personalized

        logger.info(f"Template {filename} personalized successfully")
        return personalized

    def _update_context_file(self, context_path: str, entry: dict):
        """Update context.md with latest status and recent activity."""
        try:
            # Read current content
            with open(context_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Add recent activity section if not present
            if "## 🚀 Atividade Recente" not in content:
                content += "\n\n## 🚀 Atividade Recente\n"

            # Add new entry to recent activity
            activity_entry = f"\n### {entry['timestamp'][:10]}\n"
            activity_entry += f"- **{entry['agent']}**: {entry['message']}\n"

            # Insert at the end of recent activity section
            if "## 🚀 Atividade Recente" in content:
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if line.strip() == "## 🚀 Atividade Recente":
                        # Find the end of this section
                        j = i + 1
                        while j < len(lines) and not lines[j].startswith("## "):
                            j += 1
                        lines.insert(j, activity_entry)
                        break
                content = "\n".join(lines)

            # Write updated content
            with open(context_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info("Context.md updated successfully")
        except Exception as e:
            logger.error(f"Error updating context.md: {str(e)}")

    def _update_timeline_file(self, timeline_path: str, entry: dict):
        """Update timeline.md with new timeline entry."""
        try:
            # Read current content
            with open(timeline_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract date from timestamp
            date = entry["timestamp"][:10]

            # Check if date section already exists
            if f"## {date}" in content:
                # Add to existing date section
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if line.strip() == f"## {date}":
                        # Find the end of this section
                        j = i + 1
                        while j < len(lines) and not lines[j].startswith("## "):
                            j += 1
                        lines.insert(j, f"- {entry['agent']}: {entry['message']}")
                        break
                content = "\n".join(lines)
            else:
                # Add new date section
                content += f"\n\n## {date}\n"
                content += f"- {entry['agent']}: {entry['message']}\n"

            # Write updated content
            with open(timeline_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info("Timeline.md updated successfully")
        except Exception as e:
            logger.error(f"Error updating timeline.md: {str(e)}")

    def query_llm(self, prompt: str, context: dict) -> str:
        """Query OpenAI LLM with project context for coaching insights."""
        if not self.client:
            return "OpenAI API not configured. Set OPENAI_API_KEY in .env file"
        try:
            context_summary = json.dumps(context, indent=2)
            messages = [
                {
                    "role": "system",
                    "content": "You are an experienced coach helping developers stay focused and make progress.",
                },
                {
                    "role": "user",
                    "content": f"Here is the current project context:\n{context_summary}\n\n{prompt}",
                },
            ]
            response = self.client.chat.completions.create(
                model="gpt-4", messages=messages, temperature=0.7, max_tokens=500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error querying LLM: {str(e)}"

    def get_project_context(self, include_temporal: bool = False):
        """
        Load project context from checkpoint.yaml and history.json.
        
        Args:
            include_temporal: If True, include Git log temporal context
            
        Returns:
            dict with checkpoint, history, and optionally temporal data
        """
        context = {}
        if os.path.exists(self.checkpoint_path):
            with open(self.checkpoint_path) as f:
                context["checkpoint"] = yaml.safe_load(f)
        if os.path.exists(self.history_path):
            with open(self.history_path) as f:
                context["history"] = json.load(f)
        
        # Add temporal context from Git if requested
        if include_temporal:
            context["temporal"] = self.get_temporal_context(since_days=30)
        
        return context

    async def _track_reward_action(self, action_type: str, metadata: dict):
        """Track reward action via API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/rewards/track",
                    json={
                        "user_id": self.user_id,
                        "action_type": action_type,
                        "metadata": metadata,
                    },
                    timeout=5.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    logger.info(
                        f"✅ Reward tracked: +{data.get('points_earned', 0)} CPT"
                    )
                else:
                    logger.warning(f"Reward tracking failed: {response.status_code}")

        except Exception as e:
            logger.error(f"Error tracking reward: {e}")

    def commit_changes(self, message: str, agent: str = "manual", allow_empty: bool = False):
        """
        Create git commit with metadata tracking and reward integration.

        Args:
            message: Commit message
            agent: Agent name for tracking
            allow_empty: If True, allow commit even with no changes (for temporal markers)

        Returns:
            Commit hash or "SKIPPED_NO_CHANGES" if nothing to commit (unless allow_empty=True)
        """
        # In Cloud Run mode, git operations are done via GitHub API, not local git
        if self.repo is None:
            logger.info("Git repository not available (Cloud Run mode) - commit operations use GitHub API")
            logger.info(f"Would commit with message: '{message}' from agent: {agent}")
            # Return a placeholder - actual commits happen via GitHub API in Cloud Run
            return "CLOUD_RUN_MODE"  # Indicates commit should be done via API
        
        logger.info(f"Starting commit with message: '{message}' from agent: {agent} (allow_empty={allow_empty})")
        try:
            logger.info("Adding all files to git...")

            # For temporal markers, add a small timestamp to context.md to ensure there's something to commit
            if allow_empty:
                context_md_path = os.path.join(self.context_dir, "context.md")
                logger.info(f"Checking if context.md exists at: {context_md_path}")
                if os.path.exists(context_md_path):
                    comment = f"\n<!-- Auto-update by agent '{agent}' at {datetime.now(timezone.utc).isoformat()} -->\n"
                    with open(context_md_path, "a", encoding="utf-8") as f:
                        f.write(comment)
                    logger.info(f"🚨 Temporal marker comment added to {context_md_path}")
                else:
                    # If context.md doesn't exist, create a minimal one for the temporal marker
                    os.makedirs(self.context_dir, exist_ok=True)
                    with open(context_md_path, "w", encoding="utf-8") as f:
                        f.write(f"# Project Context\n\n<!-- Temporal marker: {datetime.now(timezone.utc).isoformat()} -->\n")
                    logger.info(f"Created context.md for temporal marker")

            self.repo.git.add(A=True)
            logger.info("Files added successfully.")

            # Check if there's anything to commit
            if not self.repo.is_dirty(untracked_files=True):
                if allow_empty:
                    logger.info("No changes detected, but allow_empty=True - creating empty commit for temporal marker")
                    # Create empty commit using --allow-empty
                    commit = self.repo.index.commit(message, allow_empty=True)
                    logger.info(f"✅ Empty commit created with hash: {commit.hexsha}")
                else:
                    logger.warning("No changes detected after first add. Skipping commit.")
                    return "SKIPPED_NO_CHANGES"
            else:
                logger.info("Creating commit with changes...")
                commit = self.repo.index.commit(message)
                logger.info(f"✅ Commit created with hash: {commit.hexsha}")

            # Commit creation is now handled above (either empty or with changes)

            # Track reward (async, fire-and-forget)
            import asyncio

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            if loop.is_running():
                # Already in async context, schedule task
                asyncio.create_task(
                    self._track_reward_action(
                        action_type="cli_action",
                        metadata={
                            "agent": agent,
                            "commit": commit.hexsha,
                            "message": message[:100],
                        },
                    )
                )
            else:
                # Run in new event loop
                loop.run_until_complete(
                    self._track_reward_action(
                        action_type="cli_action",
                        metadata={
                            "agent": agent,
                            "commit": commit.hexsha,
                            "message": message[:100],
                        },
                    )
                )

            # Log to history
            self.log_history(message=message, agent=agent, commit=commit.hexsha)

            # Check for new changes after first commit (safety check)
            if self.repo is not None and self.repo.is_dirty(untracked_files=True):
                logger.info(
                    "Detected new changes after first commit. Adding and committing final changes before push..."
                )
                self.repo.git.add(A=True)
                final_message = f"Final auto-commit before push by {agent}"
                final_commit = self.repo.index.commit(final_message)
                logger.info(f"✅ Extra commit created with hash: {final_commit.hexsha}")

                # Log to history as well
                self.log_history(
                    message=final_message, agent=agent, commit=final_commit.hexsha
                )
                return final_commit.hexsha

            return commit.hexsha

        except Exception as e:
            logger.error(f"Error during commit: {str(e)}")
            raise

    def log_history(self, message: str, agent: str, commit: str = "???????"):
        """
        Log commit to history.json and update markdown documentation files.

        Updates:
        - history.json: Structured commit log
        - task_history.md: Full task history
        - context.md: Recent activity section
        - timeline.md: Timeline by date

        Args:
            message: Commit message
            agent: Agent name
            commit: Commit hash
        """
        logger.info(
            f"Logging history entry - Agent: {agent}, Message: {message[:50]}..."
        )

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": message,
            "agent": agent,
            "commit": commit,
            "summary": self._summarize_message(message),
        }
        logger.debug(f"History entry: {entry}")

        try:
            if os.path.exists(self.history_path):
                logger.info(f"Reading existing history from: {self.history_path}")
                with open(self.history_path) as f:
                    history = json.load(f)
                logger.info(f"Loaded {len(history)} existing history entries")
            else:
                logger.info("No existing history file found, creating new history")
                history = []

            history.append(entry)
            logger.info(
                f"Writing {len(history)} history entries to: {self.history_path}"
            )
            with open(self.history_path, "w") as f:
                json.dump(history, f, indent=2)
            logger.info("History file updated successfully")

            # Update task_history.md with new entry
            task_history_path = os.path.join(self.context_dir, "task_history.md")
            logger.info(f"Appending to task history: {task_history_path}")

            # Get checkpoint for project name
            checkpoint = self.get_project_context().get("checkpoint", {})

            if not os.path.exists(task_history_path):
                logger.info("Creating new task_history.md file")
                with open(task_history_path, "w", encoding="utf-8") as f:
                    f.write(
                        f"# 📝 {checkpoint.get('project_name', 'Project')} — Task History\n\n"
                    )

            with open(task_history_path, "a", encoding="utf-8") as f:
                f.write(f"\n### {entry['timestamp']}\n")
                f.write(f"- **Agent**: {entry['agent']}\n")
                f.write(f"- **Message**: {entry['message']}\n")
                f.write(f"- **Commit**: {entry['commit']}\n")
            logger.info("Task history updated successfully")

            context_path = os.path.join(self.context_dir, "context.md")
            if os.path.exists(context_path):
                logger.info(f"Updating context.md with latest status")
                self._update_context_file(context_path, entry)

            timeline_path = os.path.join(self.context_dir, "timeline.md")
            if os.path.exists(timeline_path):
                logger.info(f"Updating timeline.md with new entry")
                self._update_timeline_file(timeline_path, entry)

        except Exception as e:
            logger.error(f"Error logging history: {str(e)}")
            raise

    def _summarize_message(self, msg: str) -> str:
        """Summarize long commit messages to first line."""
        if msg.startswith("Error") or msg.startswith("You tried"):
            return "Error calling OpenAI"
        elif len(msg.splitlines()) > 1:
            return msg.splitlines()[0]
        return msg

    def get_git_log(self, since_days: Optional[int] = None, max_commits: int = 50) -> list:
        """
        Get Git commit history to situate agents in time.
        
        Returns structured commit history with:
        - timestamp (ISO format)
        - commit hash
        - author
        - message
        - date (formatted)
        
        Args:
            since_days: Only get commits from last N days (None = all)
            max_commits: Maximum number of commits to return
            
        Returns:
            List of commit dicts with temporal context
        """
        if self.repo is None:
            logger.warning("Git repository not available (Cloud Run mode) - cannot get git log")
            return []
        
        try:
            # Build git log command
            log_format = "--pretty=format:%H|%an|%ae|%ad|%s"
            date_format = "--date=iso-strict"
            cmd = ["log", log_format, date_format]
            
            if since_days:
                cmd.append(f"--since={since_days} days ago")
            
            if max_commits:
                cmd.append(f"-{max_commits}")
            
            # Execute git log
            log_output = self.repo.git.execute(cmd)
            
            if not log_output:
                logger.info("No commits found in git log")
                return []
            
            commits = []
            for line in log_output.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split('|', 4)
                if len(parts) < 5:
                    continue
                
                commit_hash, author_name, author_email, commit_date, message = parts
                
                # Parse date
                # Git date format: "2025-11-10 15:15:03 -0300"
                dt = None
                try:
                    # Git log with --date=iso-strict gives: "2025-11-10T15:15:03-03:00"
                    # But sometimes it's: "2025-11-10 15:15:03 -0300"
                    if 'T' in commit_date:
                        # ISO format with T separator
                        dt = datetime.fromisoformat(commit_date)
                    elif ' ' in commit_date:
                        # Space-separated format: "2025-11-10 15:15:03 -0300"
                        parts = commit_date.split(' ')
                        if len(parts) >= 3:
                            date_part = parts[0]
                            time_part = parts[1]
                            tz_part = parts[2]
                            # Format timezone: "-0300" -> "-03:00"
                            if len(tz_part) == 5 and tz_part[0] in ['+', '-']:
                                tz_formatted = f"{tz_part[:3]}:{tz_part[3:]}"
                            else:
                                tz_formatted = tz_part
                            dt_str = f"{date_part}T{time_part}{tz_formatted}"
                            dt = datetime.fromisoformat(dt_str)
                        else:
                            # Just date and time, no timezone
                            dt_str = commit_date.replace(' ', 'T')
                            dt = datetime.fromisoformat(dt_str)
                    else:
                        # Try direct ISO format
                        dt = datetime.fromisoformat(commit_date)
                    
                    date_str = dt.strftime('%Y-%m-%d')
                    time_str = dt.strftime('%H:%M:%S')
                except Exception as e:
                    logger.warning(f"Failed to parse commit date: {commit_date}, error: {e}")
                    date_str = commit_date.split(' ')[0] if ' ' in commit_date else commit_date.split('T')[0] if 'T' in commit_date else commit_date
                    time_str = ""
                
                commits.append({
                    "commit": commit_hash,
                    "author": author_name,
                    "email": author_email,
                    "date": commit_date,
                    "date_formatted": date_str,
                    "time": time_str,
                    "message": message,
                    "timestamp": dt.isoformat() if dt else commit_date
                })
            
            logger.info(f"Retrieved {len(commits)} commits from git log")
            return commits
            
        except Exception as e:
            logger.error(f"Error getting git log: {str(e)}")
            return []
    
    def get_temporal_context(self, since_days: Optional[int] = 30) -> dict:
        """
        Get temporal context from Git history for agents.
        
        Provides:
        - Recent commits (last N days)
        - Commit frequency
        - Activity timeline
        - Recent changes summary
        
        Args:
            since_days: How many days back to look (default: 30)
            
        Returns:
            Dict with temporal context information
        """
        commits = self.get_git_log(since_days=since_days, max_commits=100)
        
        if not commits:
            return {
                "has_git_history": False,
                "message": "No git history available (Cloud Run mode or new repository)"
            }
        
        # Group commits by date
        commits_by_date = {}
        for commit in commits:
            date = commit.get("date_formatted", "unknown")
            if date not in commits_by_date:
                commits_by_date[date] = []
            commits_by_date[date].append(commit)
        
        # Calculate stats
        total_commits = len(commits)
        unique_days = len(commits_by_date)
        avg_commits_per_day = total_commits / unique_days if unique_days > 0 else 0
        
        # Get most recent commit
        most_recent = commits[0] if commits else None
        
        # Get commits by author
        authors = {}
        for commit in commits:
            author = commit.get("author", "unknown")
            if author not in authors:
                authors[author] = 0
            authors[author] += 1
        
        return {
            "has_git_history": True,
            "total_commits": total_commits,
            "period_days": since_days,
            "unique_days_with_commits": unique_days,
            "avg_commits_per_day": round(avg_commits_per_day, 2),
            "most_recent_commit": most_recent,
            "commits_by_author": authors,
            "commits_by_date": {
                date: len(commits_list) 
                for date, commits_list in commits_by_date.items()
            },
            "recent_commits": commits[:10],  # Last 10 commits
            "timeline": [
                {
                    "date": date,
                    "commits": len(commits_list),
                    "messages": [c["message"] for c in commits_list[:3]]  # Sample messages
                }
                for date, commits_list in sorted(commits_by_date.items(), reverse=True)[:7]  # Last 7 days
            ]
        }
    
    def show_diff(self):
        """Get current git diff."""
        if self.repo is None:
            logger.warning("Git repository not available (Cloud Run mode) - cannot generate diff")
            return ""  # Return empty diff in Cloud Run mode
        return self.repo.git.diff(None)

    def summarize_diff_for_commit(self, diff: str) -> str:
        """
        Generate commit message from git diff using OpenAI LLM.

        Args:
            diff: Git diff string

        Returns:
            Summarized commit message or error message
        """
        if not self.client:
            return "Manual commit - OpenAI API not configured"
        try:
            if not diff.strip():
                return "No changes detected for automatic commit."

            prompt = (
                "You are an assistant that summarizes code changes into commit messages.\n"
                "Summarize the following Git diff into a commit message:\n\n"
                f"{diff}\n\nCommit message:"
            )

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=100,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            return f"Error calling OpenAI: {str(e)}"

    def write_context(self, state: dict):
        logger.info(f"Writing context to: {self.checkpoint_path}")
        logger.debug(f"Context state: {state}")

        checkpoint = state.get("checkpoint", {})
        logger.info(f"Checkpoint data: {checkpoint}")

        try:
            with open(self.checkpoint_path, "w") as f:
                yaml.dump(checkpoint, f)
            logger.info(f"Successfully wrote checkpoint to: {self.checkpoint_path}")
            return True
        except Exception as e:
            logger.error(f"Error writing checkpoint: {str(e)}")
            raise

    def push_to_llm(self, question: str = "What should I do next?") -> str:
        if not self.client:
            return (
                "OpenAI API não configurada. Configure OPENAI_API_KEY no arquivo .env"
            )

        state = self.get_project_context()
        prompt = (
            "You are a helpful assistant for managing software development projects. "
            "Based on the following checkpoint and history, respond concisely to the user:\n\n"
            f"Checkpoint:\n{yaml.dump(state.get('checkpoint', {}))}\n"
            f"History:\n{json.dumps(state.get('history', []), indent=2)}\n\n"
            f"Question: {question}"
        )

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()

    def push_changes(self, remote_name: str = "origin", branch: str = "main"):
        # In Cloud Run mode, git operations are done via GitHub API, not local git
        if self.repo is None:
            logger.info("Git repository not available (Cloud Run mode) - push operations use GitHub API")
            logger.info(f"Would push to remote '{remote_name}' on branch '{branch}'")
            return {"status": "cloud_run_mode", "message": "Push operations use GitHub API in Cloud Run mode"}
        
        logger.info(
            f"Pushing changes to remote '{remote_name}' on branch '{branch}'..."
        )
        try:
            remote = self.repo.remote(remote_name)
            push_info = remote.push(branch)
            logger.info("✅ Push completed successfully.")
            return {"status": "success", "details": str(push_info)}
        except Exception as e:
            logger.error(f"❌ Error pushing changes: {str(e)}")
            return {"status": "error", "message": str(e)}

    def commit_and_push(
        self,
        message: str,
        agent: str,
        remote_name: str = "origin",
        branch: str = "main",
    ):
        """
        Commits the current changes and pushes to the remote in one single step.
        """
        logger.info("Starting combined commit and push...")

        # Commit
        commit_result = self.commit_changes(message=message, agent=agent)
        if not commit_result:
            logger.warning("No changes to commit. Skipping push.")
            return {
                "status": "error",
                "message": "No changes to commit, skipping push.",
            }

        # Push
        push_result = self.push_changes(remote_name=remote_name, branch=branch)
        if push_result["status"] == "success":
            logger.info("✅ Commit and push completed successfully.")
            return {
                "status": "success",
                "commit": commit_result,
                "push_details": push_result["details"],
            }
        else:
            logger.error(f"❌ Push failed: {push_result['message']}")
            return {"status": "error", "message": push_result["message"]}

    def close_cycle(self):
        logger.info("Closing current cycle...")
        cycle_path = os.path.join(self.context_dir, "cycle.yaml")
        cycle_state = {
            "status": "closed",
            "closed_at": datetime.now(timezone.utc).isoformat(),
        }
        with open(cycle_path, "w") as f:
            yaml.dump(cycle_state, f)
        logger.info("✅ Cycle closed successfully.")
        return True
