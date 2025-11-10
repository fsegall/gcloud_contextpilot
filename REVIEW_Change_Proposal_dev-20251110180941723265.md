# Review: Change Proposal #dev-20251110180941723265

## Summary

**Status:** ❌ **REJECT - Files Already Exist, Implementation Doesn't Match Architecture**

This proposal attempts to create `development_agent.py` and `spec_agent.py`, but **both files already exist** and are properly implemented. The proposed implementation doesn't follow the existing architecture patterns and would overwrite working code.

---

## Issues Found

### 1. ❌ Files Already Exist
- `back-end/app/agents/development_agent.py` - **Already exists** (2,277 lines, fully functional)
- `back-end/app/agents/spec_agent.py` - **Already exists** (299 lines, partially functional)

**Impact:** Creating these files would overwrite existing, working implementations.

### 2. ❌ Architecture Mismatch

The proposed implementation doesn't follow the existing patterns:

#### Proposed Code Issues:
- ❌ Doesn't extend `BaseAgent` (uses standalone class)
- ❌ Uses non-existent event classes (`ProposalApprovedEvent`, `UserRequestEvent`)
- ❌ Uses incorrect event subscription pattern (`event_bus.subscribe(EventClass, handler)`)
- ❌ Event bus uses string event types, not classes

#### Existing Pattern (Correct):
```python
class DevelopmentAgent(BaseAgent):
    def __init__(self, workspace_path: str, workspace_id: str = "default", project_id: Optional[str] = None):
        super().__init__(workspace_id=workspace_id, agent_id="development", project_id=project_id)
        
        # Subscribe to events using string event types
        self.subscribe_to_event("retrospective.summary.v1")
        self.subscribe_to_event("spec.requirement.created")
    
    async def handle_event(self, event_type: str, data: Dict) -> None:
        if event_type == "retrospective.summary.v1":
            await self._handle_retrospective(data)
```

### 3. ❌ Event Types Don't Match

**Proposed code uses:**
- `ProposalApprovedEvent` (class) - ❌ Doesn't exist
- `UserRequestEvent` (class) - ❌ Doesn't exist

**Actual event system uses:**
- `EventTypes.PROPOSAL_APPROVED` = `"proposal.approved.v1"` (string)
- `EventTypes.PROPOSAL_CREATED` = `"proposal.created.v1"` (string)
- `EventTypes.GIT_COMMIT` = `"git.commit.v1"` (string)
- `EventTypes.RETROSPECTIVE_SUMMARY` = `"retrospective.summary.v1"` (string)

### 4. ✅ Actual Root Cause Identified

The retrospective mentions: **"Idle agents: spec, development. Consider reviewing their triggers."**

**Analysis:**
- ✅ **DevelopmentAgent** already subscribes to events:
  - `"retrospective.summary.v1"` 
  - `"spec.requirement.created"`
  - **Status:** Should be active (unless events aren't being published)

- ❌ **SpecAgent** does NOT subscribe to any events:
  - `handle_event` method exists but is a no-op
  - No `subscribe_to_event` calls in `__init__`
  - **Status:** Correctly identified as idle

---

## Recommended Solution

### Option 1: Add Event Subscriptions to SpecAgent (Recommended)

**File:** `back-end/app/agents/spec_agent.py`

**Changes needed:**

1. **Add event subscriptions in `__init__`:**
```python
def __init__(self, workspace_path: Optional[str] = None, workspace_id: str = "default", project_id: Optional[str] = None) -> None:
    # ... existing initialization code ...
    
    # Subscribe to events that trigger documentation updates
    from app.services.event_bus import EventTypes
    self.subscribe_to_event(EventTypes.GIT_COMMIT)  # Update docs when code changes
    self.subscribe_to_event(EventTypes.PROPOSAL_APPROVED)  # Update docs when proposals approved
    self.subscribe_to_event(EventTypes.PROPOSAL_CREATED)  # Track new proposals
```

2. **Implement event handling:**
```python
async def handle_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
    """Handle incoming events and trigger documentation validation/updates."""
    try:
        if event_type == EventTypes.GIT_COMMIT:
            await self._handle_git_commit(event_data)
        elif event_type == EventTypes.PROPOSAL_APPROVED:
            await self._handle_proposal_approved(event_data)
        elif event_type == EventTypes.PROPOSAL_CREATED:
            await self._handle_proposal_created(event_data)
        
        self.increment_metric("events_processed")
    except Exception as e:
        logger.error(f"[SpecAgent] Error handling {event_type}: {e}", exc_info=True)
        self.increment_metric("errors")

async def _handle_git_commit(self, data: Dict[str, Any]) -> None:
    """Update documentation when code changes are committed."""
    files_changed = data.get("files_changed", [])
    commit_hash = data.get("commit_hash")
    
    logger.info(f"[SpecAgent] Git commit detected: {commit_hash}, files: {files_changed}")
    
    # Validate docs after code changes
    issues = await self.validate_docs()
    if issues:
        logger.info(f"[SpecAgent] Found {len(issues)} documentation issues after commit")
        # Optionally create proposals for critical issues
        for issue in issues:
            if issue.get("severity") == "high":
                await self._create_proposal_for_issue(issue)

async def _handle_proposal_approved(self, data: Dict[str, Any]) -> None:
    """Update documentation when proposals are approved."""
    proposal_id = data.get("proposal_id")
    logger.info(f"[SpecAgent] Proposal approved: {proposal_id}")
    
    # Validate docs after proposal approval
    issues = await self.validate_docs()

async def _handle_proposal_created(self, data: Dict[str, Any]) -> None:
    """Track new proposals for documentation updates."""
    proposal_id = data.get("proposal_id")
    agent_id = data.get("agent_id")
    logger.debug(f"[SpecAgent] Proposal created: {proposal_id} by {agent_id}")
```

### Option 2: Verify DevelopmentAgent is Receiving Events

**Investigation needed:**
- Check if `retrospective.summary.v1` events are being published
- Check if `spec.requirement.created` events are being published
- Verify event bus is working correctly
- Check agent initialization in orchestrator

---

## Action Items

1. ✅ **DO NOT** apply the proposed changes (would break existing code)
2. ✅ **DO** add event subscriptions to SpecAgent (see Option 1 above)
3. ✅ **DO** verify DevelopmentAgent is receiving events (investigation)
4. ✅ **DO** test event flow: Git commit → SpecAgent validation → Documentation proposals

---

## Testing Plan

After implementing the fix:

1. **Test SpecAgent event subscription:**
   - Publish `git.commit.v1` event
   - Verify SpecAgent receives event
   - Verify documentation validation runs
   - Verify proposals created for issues

2. **Test DevelopmentAgent event subscription:**
   - Publish `retrospective.summary.v1` event
   - Verify DevelopmentAgent receives event
   - Verify implementation proposals created

3. **Verify agent metrics:**
   - Check `events_processed` metric increases
   - Check `events_published` metric increases
   - Verify agents are no longer "idle"

---

## References

- **Existing DevelopmentAgent:** `back-end/app/agents/development_agent.py` (lines 31-2277)
- **Existing SpecAgent:** `back-end/app/agents/spec_agent.py` (lines 15-299)
- **BaseAgent Pattern:** `back-end/app/agents/base_agent.py` (lines 27-408)
- **Event Types:** `back-end/app/services/event_bus.py` (lines 13-27)
- **Event Bus Interface:** `back-end/app/services/event_bus.py` (lines 41-63)

---

## Conclusion

**Recommendation:** Reject this proposal and implement the proper fix by adding event subscriptions to SpecAgent and verifying DevelopmentAgent event flow.

**Priority:** Medium (agents are idle but system is functional)

**Estimated Fix Time:** 1-2 hours (add subscriptions + implement handlers + test)



