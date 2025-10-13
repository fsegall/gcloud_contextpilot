"""
Git Agent - Git Operations Authority

Only agent authorized to perform Git operations. Implements git-flow, rollbacks, and semantic commits.
"""
import os
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional
from pathlib import Path
import git
import uuid

from app.services.event_bus import get_event_bus
from app.models.proposal import ChangeProposal, FileChange, ChangeAction
from google.cloud import firestore

logger = logging.getLogger(__name__)


class GitAgent:
    """
    Git Agent handles all Git operations.
    
    Core Principle: Single authority for Git operations - auditable and reversible.
    
    Responsibilities:
    - Apply approved Change Proposals
    - Create branches (git-flow)
    - Create semantic commits
    - Manage rollback points
    - Protect critical branches
    """
    
    def __init__(self, repo_path: str, project_id: str):
        """
        Initialize Git Agent.
        
        Args:
            repo_path: Path to Git repository
            project_id: GCP project ID for Pub/Sub
        """
        self.repo = git.Repo(repo_path, search_parent_directories=True)
        self.repo_path = Path(self.repo.working_tree_dir)
        self.event_bus = get_event_bus(project_id)
        self.db = firestore.AsyncClient()
        
        logger.info(f"Git Agent initialized for repo: {self.repo_path}")
    
    async def handle_proposal_approved(self, event: Dict):
        """
        Handle proposal.approved.v1 event.
        
        Apply the approved changes to a new branch.
        """
        logger.info(f"Git Agent received approval: {event['event_id']}")
        
        data = event["data"]
        proposal_id = data["proposal_id"]
        changes = [FileChange(**c) for c in data["changes"]]
        
        try:
            # Apply proposal
            result = await self.apply_proposal(proposal_id, changes, data.get("user_id"))
            
            # Publish success event
            self.event_bus.publish(
                topic="git-events",
                event_type="git.commit.v1",
                source="git-agent",
                data={
                    "proposal_id": proposal_id,
                    "branch": result["branch"],
                    "commit_hash": result["commit"],
                    "files_changed": result["files_changed"]
                }
            )
            
        except Exception as e:
            logger.error(f"Error applying proposal {proposal_id}: {e}")
            
            # Publish failure event
            self.event_bus.publish(
                topic="git-events",
                event_type="git.apply.failed.v1",
                source="git-agent",
                data={
                    "proposal_id": proposal_id,
                    "error": str(e)
                }
            )
    
    async def apply_proposal(
        self,
        proposal_id: str,
        changes: List[FileChange],
        user_id: str
    ) -> Dict:
        """
        Apply a Change Proposal to a new branch.
        
        Args:
            proposal_id: Proposal ID
            changes: List of file changes
            user_id: User who approved
            
        Returns:
            Dict with branch name, commit hash, etc
        """
        logger.info(f"Applying proposal: {proposal_id}")
        
        # 1. Create branch from develop
        branch_name = f"agent/proposal-{proposal_id}"
        
        try:
            # Ensure we're on develop
            self.repo.git.checkout("develop")
            self.repo.git.pull()
            
        except git.exc.GitCommandError:
            # develop doesn't exist, use main
            logger.warning("develop branch not found, using main")
            self.repo.git.checkout("main")
            self.repo.git.pull()
        
        # Create new branch
        self.repo.git.checkout("-b", branch_name)
        logger.info(f"Created branch: {branch_name}")
        
        # 2. Apply changes
        files_changed = []
        
        for change in changes:
            file_path = self.repo_path / change.file
            
            if change.action == ChangeAction.CREATE:
                # Create new file
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, 'w') as f:
                    f.write(change.content)
                logger.info(f"Created file: {change.file}")
                
            elif change.action == ChangeAction.MODIFY:
                # Apply diff (simplified - in production use proper patch)
                # For now, this is a placeholder
                logger.warning(f"MODIFY action not fully implemented for {change.file}")
                # TODO: Apply actual diff using patch library
                
            elif change.action == ChangeAction.DELETE:
                # Delete file
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Deleted file: {change.file}")
            
            files_changed.append(change.file)
        
        # 3. Stage changes
        self.repo.git.add(A=True)
        
        # 4. Create semantic commit
        commit_message = self._generate_commit_message(proposal_id, changes)
        commit = self.repo.index.commit(commit_message)
        
        logger.info(f"Created commit: {commit.hexsha}")
        
        # 5. Create rollback point
        rollback_id = await self._create_rollback_point(
            branch_name,
            commit.hexsha,
            proposal_id
        )
        
        logger.info(f"✅ Proposal applied: {proposal_id}")
        
        return {
            "branch": branch_name,
            "commit": commit.hexsha,
            "files_changed": files_changed,
            "rollback_id": rollback_id
        }
    
    def _generate_commit_message(
        self,
        proposal_id: str,
        changes: List[FileChange]
    ) -> str:
        """Generate semantic commit message."""
        
        # Determine type and scope
        if all(c.file.endswith(".md") for c in changes):
            commit_type = "docs"
            scope = "spec"
        else:
            commit_type = "agent"
            scope = "refactor"
        
        # Count changes
        lines_added = sum(c.lines_added for c in changes)
        lines_removed = sum(c.lines_removed for c in changes)
        
        # Build message
        message = f"{commit_type}({scope}): Apply proposal {proposal_id}\n\n"
        
        for change in changes:
            action = change.action.value
            message += f"- {action.capitalize()}: {change.file}\n"
        
        message += f"\nStats: +{lines_added} -{lines_removed} lines\n"
        message += f"Generated by: Git Agent\n"
        message += f"Proposal ID: {proposal_id}\n"
        
        return message
    
    async def _create_rollback_point(
        self,
        branch: str,
        commit_hash: str,
        proposal_id: str
    ) -> str:
        """Create a rollback point in Firestore."""
        
        rollback_id = f"rb_{uuid.uuid4().hex[:8]}"
        
        await self.db.collection("rollback_points").document(rollback_id).set({
            "rollback_id": rollback_id,
            "created_at": firestore.SERVER_TIMESTAMP,
            "branch": branch,
            "commit_hash": commit_hash,
            "proposal_id": proposal_id,
            "can_rollback": True,
            "rolled_back": False
        })
        
        logger.info(f"Created rollback point: {rollback_id}")
        
        return rollback_id
    
    async def rollback(self, rollback_id: str) -> Dict:
        """
        Rollback to a previous state.
        
        Args:
            rollback_id: Rollback point ID
            
        Returns:
            Dict with status and details
        """
        logger.info(f"Rolling back: {rollback_id}")
        
        # Get rollback point
        doc = await self.db.collection("rollback_points").document(rollback_id).get()
        
        if not doc.exists:
            raise ValueError(f"Rollback point not found: {rollback_id}")
        
        rollback_data = doc.to_dict()
        
        if not rollback_data["can_rollback"]:
            raise ValueError("Rollback not allowed (may be merged to main)")
        
        if rollback_data["rolled_back"]:
            raise ValueError("Already rolled back")
        
        # Checkout branch
        branch = rollback_data["branch"]
        self.repo.git.checkout(branch)
        
        # Reset to commit
        commit_hash = rollback_data["commit_hash"]
        self.repo.git.reset("--hard", commit_hash)
        
        logger.info(f"✅ Rolled back to {commit_hash}")
        
        # Mark as rolled back
        await doc.reference.update({
            "rolled_back": True,
            "rolled_back_at": firestore.SERVER_TIMESTAMP
        })
        
        # Emit event
        self.event_bus.publish(
            topic="git-events",
            event_type="git.rollback.v1",
            source="git-agent",
            data={
                "rollback_id": rollback_id,
                "branch": branch,
                "commit_hash": commit_hash,
                "proposal_id": rollback_data["proposal_id"]
            }
        )
        
        return {
            "status": "success",
            "rollback_id": rollback_id,
            "branch": branch,
            "commit": commit_hash
        }


# For testing
if __name__ == "__main__":
    import asyncio
    
    async def test():
        agent = GitAgent(
            repo_path="/home/fsegall/Desktop/New_Projects/google-context-pilot",
            project_id="test-project"
        )
        
        print(f"Current branch: {agent.repo.active_branch.name}")
        print(f"Repo path: {agent.repo_path}")
    
    asyncio.run(test())

