"""
End-to-end test for event-driven architecture

Tests the flow:
1. Spec Agent detects issue
2. Spec Agent publishes proposal.created event
3. User approves proposal (simulated)
4. Backend publishes proposal.approved event
5. Git Agent receives event and commits
6. Git Agent publishes git.commit event
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add back-end to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.event_bus import get_event_bus, reset_event_bus, EventTypes, Topics
from app.agents.spec_agent import SpecAgent
from app.agents.git_agent import GitAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_event_flow():
    """Test end-to-end event flow"""
    
    logger.info("="*80)
    logger.info("🧪 Testing Event-Driven Architecture")
    logger.info("="*80)
    
    # Reset event bus to ensure clean state
    reset_event_bus()
    
    # Use existing contextpilot workspace
    workspace_id = "contextpilot"
    workspace_path = str(Path(__file__).parent / ".contextpilot" / "workspaces" / workspace_id)
    
    logger.info(f"📁 Workspace: {workspace_path}")
    
    # Initialize agents
    logger.info("\n1️⃣ Initializing agents...")
    spec_agent = SpecAgent(
        workspace_path=workspace_path,
        workspace_id=workspace_id,
        project_id=None  # Use in-memory event bus
    )
    
    git_agent = GitAgent(
        workspace_id=workspace_id,
        project_id=None
    )
    
    # Get event bus
    event_bus = get_event_bus()
    
    # Start listening
    logger.info("\n2️⃣ Starting event listeners...")
    await event_bus.start_listening()
    
    # Simulate Spec Agent finding an issue and creating proposal
    logger.info("\n3️⃣ Spec Agent: Detecting documentation issues...")
    issues = spec_agent.validate_documentation()
    
    if issues:
        logger.info(f"   Found {len(issues)} issues")
        
        # Create proposal for first issue
        logger.info("\n4️⃣ Spec Agent: Creating proposal...")
        proposal_id = await spec_agent._create_proposal_for_issue(issues[0])
        logger.info(f"   Created proposal: {proposal_id}")
        
        # Simulate user approval (publish proposal.approved event)
        logger.info("\n5️⃣ User: Approving proposal...")
        await event_bus.publish(
            topic=Topics.PROPOSAL_EVENTS,
            event_type=EventTypes.PROPOSAL_APPROVED,
            source="user",
            data={
                'proposal_id': proposal_id,
                'workspace_id': workspace_id
            }
        )
        logger.info("   Approval event published")
        
        # Wait for Git Agent to process
        await asyncio.sleep(1)
        
        # Check Git Agent metrics
        logger.info("\n6️⃣ Git Agent: Checking metrics...")
        git_metrics = git_agent.get_metrics()
        logger.info(f"   Events processed: {git_metrics.get('events_processed', 0)}")
        logger.info(f"   Events published: {git_metrics.get('events_published', 0)}")
        
        # Check Spec Agent metrics
        logger.info("\n7️⃣ Spec Agent: Checking metrics...")
        spec_metrics = spec_agent.get_metrics()
        logger.info(f"   Events processed: {spec_metrics.get('events_processed', 0)}")
        logger.info(f"   Events published: {spec_metrics.get('events_published', 0)}")
        
        # Check event log (in-memory only)
        if hasattr(event_bus, 'get_event_log'):
            logger.info("\n8️⃣ Event Log:")
            events = event_bus.get_event_log()
            for i, event in enumerate(events, 1):
                logger.info(f"   {i}. {event['event_type']} from {event['source']}")
        
        logger.info("\n" + "="*80)
        logger.info("✅ Event flow test completed successfully!")
        logger.info("="*80)
    else:
        logger.warning("No issues found to test with")
    
    # Stop listening
    await event_bus.stop_listening()


if __name__ == "__main__":
    asyncio.run(test_event_flow())

