---
managed_by: spec-agent
template: decisions
version: 1.0.0
last_updated: 2025-10-14T00:00:00Z
auto_update: false
---

# 🎯 {{project_name}} — Architecture Decision Records (ADRs)

> **Important technical decisions and their rationale**

---

## ADR-001: Use Google Pub/Sub for Event Bus

**Date:** 2025-10-14  
**Status:** ✅ Accepted  
**Deciders:** @team

### Context
Need a reliable event bus for multi-agent communication. Considered Kafka, Redis Streams, and Pub/Sub.

### Decision
Use Google Cloud Pub/Sub as the event bus.

### Rationale
- ✅ Zero operations (serverless)
- ✅ Native integration with Cloud Run
- ✅ 99.95% SLA
- ✅ Auto-scaling
- ✅ Cost-effective for our scale

### Consequences

**Positive:**
- No infrastructure to manage
- Seamless GCP integration
- Built-in monitoring
- Dead letter queues included

**Negative:**
- Vendor lock-in to GCP (mitigated by adapter pattern)
- 7-day max retention (acceptable for our use case)

**Neutral:**
- Learning curve for team

### Alternatives Considered
1. **Kafka**: Too complex for our scale
2. **Redis Streams**: Requires managing Redis cluster

---

## ADR-002: Adapter Pattern for Rewards

**Date:** 2025-10-13  
**Status:** ✅ Accepted  
**Deciders:** @team

### Context
Need to support both off-chain (Firestore) and on-chain (Polygon) rewards during transition period.

### Decision
Implement Adapter Pattern with `RewardsAdapter` interface.

### Rationale
- ✅ Pluggable backends (off-chain ↔ on-chain)
- ✅ Testable (can mock blockchain)
- ✅ Gradual migration path
- ✅ No code changes in agents when switching

### Consequences

**Positive:**
- Can develop with Firestore, deploy with blockchain
- Easy to test (no blockchain required)
- Business logic decoupled from infrastructure

**Negative:**
- Extra abstraction layer
- Slightly more code

---

## ADR-003: Change Proposals (No Auto-Modify)

**Date:** 2025-10-14  
**Status:** ✅ Accepted  
**Deciders:** @team

### Context
Agents need to suggest code improvements, but auto-modifying code breaks developer trust.

### Decision
Agents create "Change Proposals" that require human approval before applying.

### Rationale
- ✅ Developer trust (preview before apply)
- ✅ Learning opportunity (devs understand WHY)
- ✅ Safety (rollback points)
- ✅ Control (can edit before applying)

### Consequences

**Positive:**
- High adoption rate (devs trust system)
- Better code quality (reviewed suggestions)
- Educational value

**Negative:**
- Extra step (not fully automated)
- Requires IDE integration for good UX

**Mitigations:**
- Make approval flow seamless in IDE
- Allow batch approval for doc updates
- Auto-approve for safe operations (optional)

---

## ADR-004: Git Agent as Single Git Authority

**Date:** 2025-10-14  
**Status:** ✅ Accepted  
**Deciders:** @team

### Context
Multiple agents need to interact with Git, but direct access creates chaos.

### Decision
Only Git Agent can perform Git operations. Other agents emit events, Git Agent executes.

### Rationale
- ✅ Single responsibility principle
- ✅ Audit trail (all Git ops logged)
- ✅ Rollback capability
- ✅ Consistent commit messages
- ✅ Git-flow enforcement

### Consequences

**Positive:**
- Clear separation of concerns
- Easier to debug Git issues
- All operations auditable
- Rollback system centralized

**Negative:**
- Extra event hop (latency +100ms)
- More complex architecture

---

## Template for New ADRs

```markdown
## ADR-XXX: [Title]

**Date:** YYYY-MM-DD  
**Status:** 🤔 Proposed / ✅ Accepted / ❌ Rejected / 🔄 Superseded  
**Deciders:** @mentions

### Context
[What's the issue we're facing?]

### Decision
[What did we decide?]

### Rationale
[Why did we make this decision?]
- Reason 1
- Reason 2

### Consequences

**Positive:**
- Benefit 1
- Benefit 2

**Negative:**
- Drawback 1
- Drawback 2

**Mitigations:**
- How we address the drawbacks

### Alternatives Considered
1. **Option A**: Why not chosen
2. **Option B**: Why not chosen
```

---

*Managed by Spec Agent*  
*Format: Lightweight ADRs (not full ADR template)*

