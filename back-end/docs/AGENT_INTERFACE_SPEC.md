# Agent Interface Specification

## Overview

This document defines the **precise interface specifications** for each agent's inputs, outputs, and communication protocols. This enables clear inter-agent requirements and simplifies validation of their integrated contributions.

**Purpose**: Enhance agent collaboration by standardizing:
- Event schemas
- Data contracts
- Communication protocols
- Handoff procedures
- Dependency checkpoints

---

## 1. Core Event Types

### Standard Event Format

```python
{
    "event_type": str,  # e.g., "proposal.approved.v1"
    "timestamp": str,   # ISO 8601 format
    "source_agent": str,  # Agent ID that published
    "data": dict,       # Event-specific payload
    "correlation_id": Optional[str]  # For tracking related events
}
```

### Event Naming Convention

Format: `{domain}.{action}.{version}`

Examples:
- `proposal.approved.v1`
- `git.commit.v1`
- `spec.requirement.created`
- `milestone.complete.v1`

---

## 2. Agent-Specific Interfaces

### 2.1 Spec Agent

**Purpose**: Requirements and specifications management

#### Publishes Events:
- `spec.requirement.created`
- `spec.update.v1`

#### Subscribes to Events:
- `git.commit.v1`
- `context.delta.v1`

#### Input Contract:
```python
# Via /specs/create endpoint
{
    "title": str,  # Required
    "description": str,  # Required
    "acceptance_criteria": List[str],  # Optional
    "priority": str,  # "high" | "medium" | "low"
    "tags": List[str]  # Optional
}
```

#### Output Contract:
```python
# spec.requirement.created event
{
    "requirement_id": str,
    "title": str,
    "description": str,
    "acceptance_criteria": List[str],
    "priority": str,
    "created_at": str,  # ISO 8601
    "agent": "spec"
}
```

#### Artifacts:
- `specifications/{spec_id}.md`
- State: `spec_state.json`

---

### 2.2 Git Agent

**Purpose**: Version control and commit operations

#### Publishes Events:
- `git.commit.v1`
- `git.push.v1` (future)

#### Subscribes to Events:
- `proposal.approved.v1`
- `milestone.complete.v1`

#### Input Contract:
```python
# Via handle_event(proposal.approved.v1)
{
    "proposal_id": str,
    "proposed_changes": List[{
        "file_path": str,
        "change_type": "create" | "modify" | "delete",
        "content": Optional[str]
    }]
}
```

#### Output Contract:
```python
# git.commit.v1 event
{
    "commit_hash": str,
    "message": str,
    "agent": str,
    "files_changed": List[str],
    "timestamp": str,  # ISO 8601
    "commit_type": str  # feat|fix|docs|chore|refactor
}
```

#### Side Effects:
- Updates `history.json`
- Updates `context.md`, `timeline.md`, `task_history.md`
- Tracks rewards via API call
- Creates git commit in repository

---

### 2.3 Development Agent

**Purpose**: Code implementation generation

#### Publishes Events:
- `development.proposal.created`
- `development.implementation.ready`

#### Subscribes to Events:
- `retrospective.trigger.v1`
- `spec.requirement.created`

#### Input Contract:
```python
# Via implement_feature()
{
    "description": str,  # Required
    "context": {
        "retrospective_id": Optional[str],
        "spec_id": Optional[str],
        "priority": Optional[str],
        "assigned_to": Optional[str]
    },
    "target_files": Optional[List[str]]  # Specific files to modify
}
```

#### Output Contract:
```python
# development.proposal.created event
{
    "proposal_id": str,
    "title": str,
    "description": str,
    "proposed_changes": List[ProposedChange],
    "overall_diff": ProposalDiff,
    "agent": "development",
    "requires_review": bool
}
```

#### Requirements:
- `GEMINI_API_KEY` must be set for AI-powered implementation
- Project context must be accessible

---

### 2.4 Context Agent

**Purpose**: Knowledge indexing and semantic search

#### Publishes Events:
- `context.delta.v1`
- `context.indexed.v1`

#### Subscribes to Events:
- `git.commit.v1`
- `proposal.approved.v1`
- `spec.update.v1`

#### Input Contract:
```python
# Via index_content()
{
    "content": str,
    "content_type": "code" | "spec" | "doc" | "commit",
    "source_file": Optional[str],
    "metadata": dict
}
```

#### Output Contract:
```python
# context.indexed.v1 event
{
    "indexed_items": int,
    "total_items": int,
    "index_type": str,
    "timestamp": str
}
```

#### Central Context Registry:
```python
# Shared context available to all agents
{
    "project_name": str,
    "goal": str,
    "current_status": str,
    "active_milestones": List[dict],
    "recent_commits": List[dict],
    "pending_proposals": List[dict],
    "agent_states": Dict[str, dict]
}
```

---

### 2.5 Strategy Coach Agent

**Purpose**: Strategic guidance, technical coaching, and quality assurance

#### Publishes Events:
- `coach.feedback.v1`
- `coach.quality_alert.v1`

#### Subscribes to Events:
- `proposal.created.v1`
- `proposal.rejected.v1`
- `git.commit.v1`

#### Input Contract:
```python
# Via provide_perspective()
{
    "event_type": str,
    "event_data": dict,
    "request_type": "strategic" | "technical" | "motivational"
}
```

#### Output Contract:
```python
# coach.feedback.v1 event
{
    "feedback_id": str,
    "target_agent": str,
    "feedback_type": "strategic" | "technical" | "motivational",
    "message": str,
    "suggestions": List[str],
    "quality_score": Optional[float],  # 0-10
    "timestamp": str
}
```

#### Quality Checks:
- Function length > 50 lines → Warning
- Parameter count > 5 → Warning
- Missing docstrings → Warning
- Cyclomatic complexity > 10 → Alert

---

### 2.6 Milestone Agent

**Purpose**: Track project progress and deliverables

#### Publishes Events:
- `milestone.created.v1`
- `milestone.updated.v1`
- `milestone.complete.v1`

#### Subscribes to Events:
- `proposal.approved.v1`
- `git.commit.v1`
- `spec.update.v1`

#### Input Contract:
```python
# Via create_milestone()
{
    "title": str,
    "description": str,
    "completion_criteria": List[str],
    "target_date": str,  # ISO 8601 date
    "dependencies": List[str],  # Other milestone IDs
    "related_specs": List[str]  # Spec IDs
}
```

#### Output Contract:
```python
# milestone.complete.v1 event
{
    "milestone_id": str,
    "title": str,
    "completed_at": str,  # ISO 8601
    "completion_evidence": List[{
        "criterion": str,
        "met": bool,
        "evidence": str  # commit hash, spec ID, etc.
    }],
    "next_milestones": List[str]  # Dependent milestones now unblocked
}
```

#### Dependency Checkpoints:
```python
# Before declaring milestone complete, verify:
{
    "all_criteria_met": bool,
    "dependencies_resolved": bool,
    "related_specs_implemented": bool,
    "code_quality_passed": bool,
    "tests_passing": bool
}
```

---

### 2.7 Retrospective Agent

**Purpose**: Conduct agent retrospectives and generate insights

#### Publishes Events:
- `retrospective.complete.v1`
- `retrospective.proposal.created.v1`

#### Subscribes to Events:
- `milestone.complete.v1`

#### Input Contract:
```python
# Via conduct_retrospective()
{
    "trigger": "manual" | "milestone_complete" | "cycle_end",
    "trigger_topic": Optional[str],
    "gemini_api_key": Optional[str]
}
```

#### Output Contract:
```python
# retrospective.complete.v1 event
{
    "retrospective_id": str,
    "timestamp": str,
    "trigger": str,
    "agent_metrics": Dict[str, dict],
    "insights": List[str],
    "action_items": List[{
        "priority": "high" | "medium" | "low",
        "action": str,
        "assigned_to": str
    }],
    "proposal_id": Optional[str],  # Auto-generated proposal
    "llm_summary": Optional[str]
}
```

---

## 3. Unified Operational Dashboard

### Dashboard Data Schema

```python
{
    "timestamp": str,  # ISO 8601
    "agents": {
        "spec": {
            "status": "active" | "idle" | "error",
            "events_processed": int,
            "events_published": int,
            "errors": int,
            "last_activity": str,  # ISO 8601
            "current_task": Optional[str]
        },
        # ... other agents
    },
    "event_bus": {
        "mode": "in_memory" | "pubsub",
        "total_events": int,
        "events_last_minute": int,
        "subscriptions": Dict[str, int]  # event_type -> subscriber_count
    },
    "system": {
        "storage_mode": "local" | "cloud",
        "rewards_mode": "local" | "firestore",
        "environment": "development" | "production"
    },
    "active_tasks": List[{
        "task_id": str,
        "agent": str,
        "description": str,
        "started_at": str,
        "dependencies": List[str]
    }],
    "pending_handoffs": List[{
        "from_agent": str,
        "to_agent": str,
        "event_type": str,
        "data": dict,
        "waiting_since": str
    }]
}
```

### Dashboard API Endpoint

```python
GET /agents/dashboard

Response:
{
    "dashboard": DashboardData,
    "health": "healthy" | "degraded" | "down",
    "alerts": List[str]
}
```

---

## 4. Standardized Handoff Protocol

### Phase 1: Pre-Handoff

```python
# Agent A prepares handoff
{
    "handoff_id": str,
    "from_agent": str,
    "to_agent": str,
    "event_type": str,
    "data": dict,
    "prerequisites": List[{
        "condition": str,
        "status": "met" | "pending" | "failed"
    }],
    "expected_output": str
}
```

### Phase 2: Handoff Event

```python
# Published event with handoff metadata
{
    "event_type": str,
    "handoff_id": str,
    "source_agent": str,
    "target_agent": str,  # NEW: Explicit target
    "data": dict,
    "correlation_id": str,
    "timestamp": str
}
```

### Phase 3: Acknowledgment

```python
# Target agent acknowledges receipt
{
    "event_type": "handoff.acknowledged.v1",
    "handoff_id": str,
    "receiving_agent": str,
    "status": "accepted" | "rejected",
    "rejection_reason": Optional[str],
    "estimated_completion": Optional[str]  # ISO 8601
}
```

### Phase 4: Completion

```python
# Target agent signals completion
{
    "event_type": "handoff.complete.v1",
    "handoff_id": str,
    "completing_agent": str,
    "output": dict,
    "next_handoff": Optional[dict]  # Chain to next agent
}
```

---

## 5. Agent Communication Best Practices

### 5.1 Event Publishing

```python
# ✅ GOOD: Clear, specific event type
await event_bus.publish(
    topic=Topics.PROPOSALS_EVENTS,
    event_type="proposal.approved.v1",
    data={
        "proposal_id": "prop-123",
        "approved_by": "developer",
        "approved_at": "2025-10-22T10:00:00Z"
    }
)

# ❌ BAD: Vague event type
await event_bus.publish(
    topic="general",
    event_type="update",
    data={"id": "123"}
)
```

### 5.2 Event Subscription

```python
# ✅ GOOD: Subscribe to specific, relevant events
self.subscribe_to_event("proposal.approved.v1")
self.subscribe_to_event("milestone.complete.v1")

# ❌ BAD: Subscribe to all events
self.subscribe_to_event("*")
```

### 5.3 Error Handling

```python
# ✅ GOOD: Graceful error handling with metrics
try:
    await self._process_event(data)
    self.increment_metric("events_processed")
except ValueError as e:
    logger.warning(f"Invalid data: {e}")
    self.increment_metric("events_skipped")
except Exception as e:
    logger.error(f"Processing error: {e}")
    self.increment_metric("errors")
    # Publish error event for monitoring
    await self._publish_error_event(e)

# ❌ BAD: Silent failure
try:
    await self._process_event(data)
except:
    pass
```

### 5.4 Data Validation

```python
# ✅ GOOD: Validate input contract
def _validate_proposal_data(self, data: dict) -> bool:
    required_fields = ["proposal_id", "proposed_changes"]
    return all(field in data for field in required_fields)

# Process only if valid
if self._validate_proposal_data(data):
    await self._apply_proposal(data)
else:
    logger.warning("Invalid proposal data")
    return

# ❌ BAD: Assume data is valid
await self._apply_proposal(data)  # May crash if missing fields
```

---

## 6. Milestone-Aligned Checkpoints

### Checkpoint Definition

```python
{
    "checkpoint_id": str,
    "milestone_id": str,
    "checkpoint_type": "dependency" | "deliverable" | "quality",
    "description": str,
    "verification_criteria": List[{
        "criterion": str,
        "verification_method": "automated" | "manual",
        "responsible_agent": str
    }],
    "status": "pending" | "verified" | "failed",
    "verified_at": Optional[str],
    "verified_by": Optional[str]
}
```

### Example Checkpoints

```python
# For Milestone: "User Authentication Feature Complete"
checkpoints = [
    {
        "checkpoint_id": "cp-001",
        "milestone_id": "ms-auth-001",
        "checkpoint_type": "dependency",
        "description": "Spec Agent has created authentication spec",
        "verification_criteria": [
            {
                "criterion": "spec-auth-001 exists and is approved",
                "verification_method": "automated",
                "responsible_agent": "spec"
            }
        ],
        "status": "verified"
    },
    {
        "checkpoint_id": "cp-002",
        "milestone_id": "ms-auth-001",
        "checkpoint_type": "deliverable",
        "description": "Development Agent has implemented auth routes",
        "verification_criteria": [
            {
                "criterion": "auth_routes.py exists with all required endpoints",
                "verification_method": "automated",
                "responsible_agent": "development"
            }
        ],
        "status": "pending"
    },
    {
        "checkpoint_id": "cp-003",
        "milestone_id": "ms-auth-001",
        "checkpoint_type": "quality",
        "description": "Coach Agent verifies code quality",
        "verification_criteria": [
            {
                "criterion": "No functions > 50 lines",
                "verification_method": "automated",
                "responsible_agent": "coach"
            },
            {
                "criterion": "All functions have docstrings",
                "verification_method": "automated",
                "responsible_agent": "coach"
            }
        ],
        "status": "pending"
    }
]
```

---

## 7. Testing and Validation

### Contract Testing

Each agent should have tests verifying:
1. Published events match output contract
2. Can parse all subscribed event types
3. Handles invalid data gracefully
4. Respects handoff protocol

### Example Test

```python
def test_git_agent_commit_event_contract():
    """Verify Git Agent publishes events matching contract"""
    agent = GitAgent(workspace_id="test")
    
    # Mock event bus
    events_published = []
    def mock_publish(topic, event_type, data):
        events_published.append((event_type, data))
    
    agent.event_bus.publish = mock_publish
    
    # Trigger commit
    agent.commit_changes("test: sample commit", agent="test")
    
    # Verify contract
    assert len(events_published) == 1
    event_type, data = events_published[0]
    
    assert event_type == "git.commit.v1"
    assert "commit_hash" in data
    assert "message" in data
    assert "agent" in data
    assert "files_changed" in data
    assert "timestamp" in data
    assert "commit_type" in data
```

---

## 8. Versioning

### Semantic Versioning for Events

- **v1.x**: Initial contract
- **v2.x**: Backward-incompatible changes
- **v1.1.x**: Backward-compatible additions

### Deprecation Strategy

```python
# When deprecating an event type:
# 1. Publish to both old and new for 2 versions
await event_bus.publish(
    topic=Topics.PROPOSALS_EVENTS,
    event_type="proposal.approved.v1",  # OLD
    data=data
)
await event_bus.publish(
    topic=Topics.PROPOSALS_EVENTS,
    event_type="proposal.approved.v2",  # NEW
    data=enhanced_data
)

# 2. Log deprecation warning
logger.warning("proposal.approved.v1 is deprecated, use v2")

# 3. Remove old version after 2 releases
```

---

## 9. Monitoring and Observability

### Required Metrics per Agent

```python
{
    "events_processed": int,
    "events_published": int,
    "events_skipped": int,
    "errors": int,
    "handoffs_sent": int,
    "handoffs_received": int,
    "handoffs_completed": int,
    "average_processing_time_ms": float
}
```

### Health Check Criteria

```python
# Agent is "healthy" if:
- errors < 5% of events_processed
- last_activity < 5 minutes ago
- no handoffs stuck > 10 minutes
- event processing time < 1000ms average

# Agent is "degraded" if:
- errors 5-10% of events_processed
- last_activity 5-15 minutes ago
- some handoffs stuck 10-30 minutes
- event processing time 1000-3000ms

# Agent is "down" if:
- errors > 10%
- last_activity > 15 minutes ago
- handoffs stuck > 30 minutes
- event processing time > 3000ms
```

---

## 10. Migration Guide

### Adding a New Agent

1. Create agent class inheriting from `BaseAgent`
2. Define interface in this document
3. Register in `AgentOrchestrator`
4. Add contract tests
5. Update dashboard schema
6. Document handoff protocols with other agents

### Modifying an Event Contract

1. Create new event version (e.g., v1 → v2)
2. Publish to both versions during transition
3. Update all subscribing agents
4. Run integration tests
5. Deprecate old version
6. Remove after 2 releases

---

**Last Updated**: 2025-10-22  
**Version**: 1.0  
**Status**: Living Document



