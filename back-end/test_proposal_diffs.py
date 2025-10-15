"""
Test Proposal Diff Generation

Tests that Spec Agent generates proposals with actual diffs.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add back-end to path
sys.path.insert(0, str(Path(__file__).parent))

from app.agents.spec_agent import SpecAgent
from app.utils.workspace_manager import get_workspace_path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_proposal_with_diff():
    """Test that proposals include diffs"""
    
    logger.info("="*80)
    logger.info("🧪 Testing Proposal Diff Generation")
    logger.info("="*80)
    
    # Use contextpilot workspace
    workspace_id = "contextpilot"
    workspace_path = str(Path(__file__).parent / ".contextpilot" / "workspaces" / workspace_id)
    
    logger.info(f"\n📁 Workspace: {workspace_path}")
    
    # Initialize Spec Agent
    logger.info("\n1️⃣ Initializing Spec Agent...")
    spec_agent = SpecAgent(
        workspace_path=workspace_path,
        workspace_id=workspace_id,
        project_id=None
    )
    
    # Detect issues
    logger.info("\n2️⃣ Detecting documentation issues...")
    issues = await spec_agent.validate_docs()
    
    if issues:
        logger.info(f"   Found {len(issues)} issues")
        
        # Create proposal for first issue
        issue = issues[0]
        logger.info(f"\n3️⃣ Creating proposal for: {issue['file']}")
        logger.info(f"   Issue type: {issue['type']}")
        logger.info(f"   Message: {issue['message']}")
        
        proposal_id = await spec_agent._create_proposal_for_issue(issue)
        logger.info(f"   ✅ Created proposal: {proposal_id}")
        
        # Check if proposal file exists
        proposals_dir = Path(workspace_path) / 'proposals'
        json_file = proposals_dir / f"{proposal_id}.json"
        md_file = proposals_dir / f"{proposal_id}.md"
        
        logger.info(f"\n4️⃣ Checking proposal files...")
        logger.info(f"   JSON: {json_file.exists()} - {json_file}")
        logger.info(f"   MD:   {md_file.exists()} - {md_file}")
        
        if json_file.exists():
            import json
            with open(json_file, 'r') as f:
                proposal = json.load(f)
            
            logger.info(f"\n5️⃣ Proposal Structure:")
            logger.info(f"   ID: {proposal['id']}")
            logger.info(f"   Title: {proposal['title']}")
            logger.info(f"   Has diff: {'diff' in proposal}")
            
            if 'diff' in proposal:
                diff_content = proposal['diff']['content']
                logger.info(f"   Diff format: {proposal['diff']['format']}")
                logger.info(f"   Diff length: {len(diff_content)} chars")
                logger.info(f"\n6️⃣ Diff Preview (first 500 chars):")
                logger.info("   " + "-"*70)
                for line in diff_content[:500].split('\n'):
                    logger.info(f"   {line}")
                logger.info("   " + "-"*70)
            
            if 'proposed_changes' in proposal and proposal['proposed_changes']:
                change = proposal['proposed_changes'][0]
                logger.info(f"\n7️⃣ Proposed Change:")
                logger.info(f"   File: {change['file_path']}")
                logger.info(f"   Type: {change['change_type']}")
                logger.info(f"   Has before: {'before' in change}")
                logger.info(f"   Has after: {'after' in change}")
                logger.info(f"   Has diff: {'diff' in change}")
        
        logger.info("\n" + "="*80)
        logger.info("✅ Proposal diff generation test completed!")
        logger.info("="*80)
    else:
        logger.warning("No issues found to test with")


if __name__ == "__main__":
    asyncio.run(test_proposal_with_diff())

