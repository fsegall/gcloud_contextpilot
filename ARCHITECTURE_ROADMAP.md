# Architecture Roadmap: Event-Driven Multi-Agent System

**Date:** October 15, 2025  
**Status:** 📋 Planning Phase

## Current State vs. Desired State

### Current (MVP)
- ✅ Agents exist (Spec, Git, Strategy, Coach)
- ✅ HTTP endpoints work
- ✅ Proposals can be created and approved
- ✅ Git Agent commits on approval
- ❌ **No event bus** (direct HTTP calls)
- ❌ **No shared state** (agents are stateless)
- ❌ **No artifact consumption** (.md files not used by agents)
- ❌ **No agent collaboration** (no retrospectives)

### Desired (Production)
- ✅ Event-driven architecture (Pub/Sub)
- ✅ Persistent agent state (Firestore)
- ✅ Explicit artifact producer/consumer relationships
- ✅ Agent retrospectives for continuous improvement
- ✅ Observable event flow (all events logged)

---

## Key Architectural Changes

### 1. Event Bus (Pub/Sub)

**Replace:**
```python
# Direct call
git_agent.commit(proposal_id)
```

**With:**
```python
# Event-driven
event_bus.publish('proposal.approved.v1', {'proposal_id': proposal_id})
# Git Agent subscribes and reacts
```

**Topics:**
- `git-events` → git.commit.v1
- `proposal-events` → proposal.created.v1, proposal.approved.v1, proposal.rejected.v1
- `strategy-events` → strategy.updated.v1
- `retrospective-events` → retrospective.trigger.v1

### 2. Agent State Management

**Replace:**
```python
# Stateless agent
class SpecAgent:
    def __init__(self, workspace_id):
        self.workspace_id = workspace_id
```

**With:**
```python
# Stateful agent with memory
class SpecAgent(BaseAgent):
    def __init__(self, workspace_id):
        super().__init__(workspace_id, 'spec')
        self.state = self._load_state()  # From Firestore
        
    def remember(self, key, value):
        self.state['memory'][key] = value
        self._save_state()
```

**State Structure (Firestore):**
```json
{
  "workspace_id": "contextpilot",
  "agents": {
    "spec": {
      "issues_found": 5,
      "approval_rate": 0.75,
      "memory": {
        "patterns": ["docs_drift", "missing_tests"],
        "rejection_reasons": ["too aggressive", "out of scope"]
      }
    }
  }
}
```

### 3. Artifact Producer/Consumer Model

**Current:** Files are created but not consumed systematically

**Proposed:**
```python
# Spec Agent (Producer)
class SpecAgent(BaseAgent):
    def create_proposal(self):
        # Write proposals.md
        self._write_artifact('proposals.md', content)
        
        # Register in global context
        self.update_global_context({
            'artifacts': {
                'proposals_md': {
                    'producer': 'spec',
                    'consumers': ['git', 'strategy'],
                    'last_updated': datetime.now()
                }
            }
        })

# Strategy Agent (Consumer)
class StrategyAgent(BaseAgent):
    def analyze(self):
        # Read artifacts from producers
        artifacts = self.consume_artifacts()
        proposals = artifacts['proposals_md']
        
        # Synthesize strategy
        strategy = self._analyze(proposals)
        
        # Produce own artifact
        self._write_artifact('milestones.md', strategy)
```

### 4. Retrospective Agent (New!)

**Purpose:** Facilitate agent "meetings" to improve processes

**Flow:**
1. Trigger: Daily at 6pm OR milestone completed
2. Gather: Read all agent states from Firestore
3. Analyze: Detect patterns (low approval rate, high commits, etc.)
4. Generate: Create insights and action items
5. Publish: Send action items to agents via events
6. Agents: Update behavior based on feedback

**Example:**
```python
retrospective = {
    'date': '2025-10-15T18:00:00Z',
    'insights': [
        {
            'agent': 'spec',
            'issue': 'Approval rate dropped to 60%',
            'recommendation': 'Be more conservative with proposals'
        }
    ],
    'action_items': [
        {
            'agent': 'spec',
            'action': 'Reduce proposal aggressiveness',
            'status': 'pending'
        }
    ]
}
```

---

## Implementation Phases

### Phase 1: State Management + Custom Artifacts (Week 1) 🎯 PRIORITY
**Goal:** Agents remember context between runs AND consume custom artifacts with rules

#### Part A: State Management
- [ ] Create `BaseAgent` class with Firestore integration
- [ ] Implement `remember()` and `recall()` methods
- [ ] Migrate Spec Agent to use `BaseAgent`
- [ ] Test state persistence across runs
- [ ] Document agent state schema

#### Part B: Custom Artifacts
- [ ] Create `artifacts.yaml` configuration system
- [ ] Add `consume_artifact()` method to `BaseAgent`
- [ ] Implement artifact rule loading and injection
- [ ] Create templates: `project_scope.md`, `project_checklist.md`, `daily_checklist.md`
- [ ] Test Spec Agent with `project_scope.md` rules

**Deliverable:** Spec Agent remembers issues AND respects project_scope.md rules

---

### Phase 2: Event Bus (Week 2)
**Goal:** Replace direct calls with events

- [ ] Set up GCP Pub/Sub topics
- [ ] Implement `EventBus` service
- [ ] Add `publish_event()` to `BaseAgent`
- [ ] Refactor Spec Agent to publish `proposal.created.v1`
- [ ] Refactor Git Agent to subscribe to `proposal.approved.v1`
- [ ] Test event flow end-to-end

**Deliverable:** Proposal approval triggers Git Agent via event

---

### Phase 3: Artifact Consumption (Week 3)
**Goal:** Strategy Agent consumes artifacts from other agents

- [ ] Map all `.md` files in global context
- [ ] Implement `consume_artifacts()` in `BaseAgent`
- [ ] Migrate Strategy Agent to consume proposals.md
- [ ] Strategy Agent produces milestones.md
- [ ] Coach Agent consumes milestones.md
- [ ] Test producer/consumer flow

**Deliverable:** Strategy Agent reads proposals and updates milestones

---

### Phase 4: Retrospectives (Week 4)
**Goal:** Agents "meet" and improve processes

- [ ] Implement `RetrospectiveAgent`
- [ ] Schedule periodic retrospectives (daily/weekly)
- [ ] Analyze agent metrics (approval rate, commit frequency, etc.)
- [ ] Generate insights and action items
- [ ] Publish action items to agents
- [ ] Agents update behavior based on feedback
- [ ] Build dashboard to visualize retrospectives

**Deliverable:** Daily retrospective report with actionable insights

---

## Migration Strategy

### Backward Compatibility
- Keep existing HTTP endpoints during migration
- Add event publishing alongside HTTP calls
- Gradually deprecate direct calls
- Use feature flags to toggle event-driven mode

### Testing Strategy
- Test each phase with ContextPilot workspace (dogfooding)
- Compare event-driven vs. direct call performance
- Monitor Pub/Sub latency and costs
- Validate state consistency across agent runs

### Rollout Plan
1. **Dev Environment:** Test with local Firestore emulator
2. **Staging:** Deploy to GCP with real Pub/Sub
3. **Production:** Gradual rollout with feature flags
4. **Monitoring:** Set up alerts for event failures

---

## Technical Decisions

### Firestore vs. JSON Files
**Decision:** Start with JSON files for development, migrate to Firestore for production

**Rationale:**
- JSON files: Easier to debug, no GCP dependency
- Firestore: Better for production, real-time updates, scalability

### Event Schema
**Standard Event Format:**
```json
{
  "event_type": "proposal.approved.v1",
  "source": "spec-agent",
  "timestamp": "2025-10-15T11:30:59Z",
  "data": {
    "proposal_id": "spec-3",
    "workspace_id": "contextpilot"
  }
}
```

### Retrospective Triggers
**Options:**
1. Time-based (daily at 6pm)
2. Event-based (milestone completed)
3. Manual (user triggers)

**Decision:** Hybrid - daily + milestone-based

---

## Success Metrics

### Phase 1 (State)
- ✅ Agent state persists between runs
- ✅ Memory size < 10KB per agent
- ✅ State load time < 100ms

### Phase 2 (Events)
- ✅ Event latency < 500ms
- ✅ Zero event loss
- ✅ All events logged in Pub/Sub

### Phase 3 (Artifacts)
- ✅ Strategy Agent consumes 100% of artifacts
- ✅ Artifact updates trigger downstream agents
- ✅ No stale artifacts (all < 24h old)

### Phase 4 (Retrospectives)
- ✅ Daily retrospective runs successfully
- ✅ At least 3 insights generated per retro
- ✅ Action items tracked and completed
- ✅ Agent behavior improves over time (measurable)

---

## Open Questions

1. **Retrospective Frequency:** Daily or weekly?
2. **State Conflicts:** How to handle concurrent agent updates to global context?
3. **Event Ordering:** Do we need guaranteed event ordering?
4. **Artifact Versioning:** Should we version .md files?
5. **Agent Priorities:** Which agents should run first in a retrospective?

---

## Next Steps (Immediate)

1. ✅ Document architecture (this file)
2. 🎯 Implement `BaseAgent` class (Phase 1)
3. 🎯 Migrate Spec Agent to use `BaseAgent`
4. 🎯 Test state persistence with ContextPilot workspace
5. 📝 Review architecture with team
6. 🚀 Proceed to Phase 2 (Event Bus)

---

**Related Documents:**
- [Agent State Management](docs/architecture/AGENT_STATE_MANAGEMENT.md)
- [Event Flow Diagram](docs/architecture/EVENT_FLOW_DIAGRAM.md)
- [Proposal Approval Flow](docs/progress/PROPOSAL_APPROVAL_FLOW.md)

**Status:** 📋 Ready for implementation - Starting with Phase 1

