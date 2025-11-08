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

        self.repo = git.Repo(git_root, search_parent_directories=True)
        self.project_root = self.repo.working_tree_dir
        logger.info(f"Project root: {self.project_root}")

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
        logger.info("Starting git root search...")
        path = os.getcwd()
        logger.info(f"Starting from current directory: {path}")

        while path != os.path.dirname(path):
            git_dir = os.path.join(path, ".git")
            logger.debug(f"Checking for .git directory at: {git_dir}")

            if os.path.isdir(git_dir):
                logger.info(f"Found git root at: {path}")
                return path
            path = os.path.dirname(path)
            logger.debug(f"Moving up to parent directory: {path}")

        logger.error("Git directory not found in any parent directory")
        raise git.exc.InvalidGitRepositoryError("❌ Git directory not found.")

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

    def get_project_context(self):
        """Load project context from checkpoint.yaml and history.json."""
        context = {}
        if os.path.exists(self.checkpoint_path):
            with open(self.checkpoint_path) as f:
                context["checkpoint"] = yaml.safe_load(f)
        if os.path.exists(self.history_path):
            with open(self.history_path) as f:
                context["history"] = json.load(f)
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

    def commit_changes(self, message: str, agent: str = "manual"):
        """
        Create git commit with metadata tracking and reward integration.

        Args:
            message: Commit message
            agent: Agent name for tracking

        Returns:
            Commit hash or "SKIPPED_NO_CHANGES" if nothing to commit
        """
        logger.info(f"Starting commit with message: '{message}' from agent: {agent}")
        try:
            logger.info("Adding all files to git...")

            context_md_path = os.path.join(self.context_dir, "context.md")
            logger.info(f"Checking if context.md exists at: {context_md_path}")
            if os.path.exists(context_md_path):
                comment = f"\n<!-- Auto-update by agent '{agent}' at {datetime.now(timezone.utc).isoformat()} -->\n"
                with open(context_md_path, "a", encoding="utf-8") as f:
                    f.write(comment)
                logger.info(f"🚨 Forced update comment added to {context_md_path}")

            self.repo.git.add(A=True)
            logger.info("Files added successfully.")

            # Check if there's anything to commit
            if not self.repo.is_dirty(untracked_files=True):
                logger.warning("No changes detected after first add. Skipping commit.")
                return "SKIPPED_NO_CHANGES"

            logger.info("Creating initial commit...")
            commit = self.repo.index.commit(message)
            logger.info(f"✅ Commit created with hash: {commit.hexsha}")

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
            if self.repo.is_dirty(untracked_files=True):
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

    def show_diff(self):
        """Get current git diff."""
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
