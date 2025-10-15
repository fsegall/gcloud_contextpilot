# Event-Driven Architecture - Flow Diagram

## Current Architecture (Direct Calls)

```
┌──────────┐
│   User   │
│ (curl)   │
└────┬─────┘
     │ POST /proposals/create
     ↓
┌────────────────┐
│  Spec Agent    │
│  (creates      │
│   proposal)    │
└────┬───────────┘
     │ (no event)
     ↓
┌────────────────┐
│  proposals.md  │
│  (persisted)   │
└────────────────┘
     
     User manually approves
     ↓
┌────────────────┐
│  Git Agent     │ ← Direct HTTP call
│  (commits)     │
└────────────────┘
```

**Problems:**
- ❌ Tight coupling
- ❌ No event history
- ❌ Hard to add new agents
- ❌ No shared state

---

## Proposed Architecture (Event-Driven)

```
┌─────────────────────────────────────────────────────────────────┐
│                    GCP Pub/Sub Event Bus                        │
│  Topics: git-events, proposal-events, strategy-events, etc.     │
└─────────────────────────────────────────────────────────────────┘
                              ↑ ↓
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ↓                     ↓                     ↓
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ Spec Agent   │      │  Git Agent   │      │Strategy Agent│
│              │      │              │      │              │
│ State:       │      │ State:       │      │ State:       │
│ • issues: [] │      │ • commits:156│      │ • phase: X   │
│ • patterns   │      │ • auto: 12   │      │ • blockers   │
└──────┬───────┘      └──────┬───────┘      └──────┬───────┘
       │                     │                     │
       │ reads/writes        │ reads/writes        │ reads/writes
       ↓                     ↓                     ↓
┌─────────────────────────────────────────────────────────────────┐
│              Firestore: Global Workspace Context                │
│                                                                 │
│  {                                                              │
│    workspace_id: "contextpilot",                                │
│    agents: { spec: {...}, git: {...}, strategy: {...} },        │
│    artifacts: {                                                 │
│      context_md: { producer: "git", consumers: ["spec",...] },  │
│      proposals_md: { producer: "spec", consumers: ["git"] }     │
│    },                                                           │
│    retrospectives: [...]                                        │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Example Flow: Proposal Creation → Approval → Commit

```
1. Git Commit Detected
   ┌──────────┐
   │   Git    │ git push
   │ (user)   │─────────┐
   └──────────┘         │
                        ↓
                 ┌──────────────┐
                 │ Git Webhook  │
                 │  or Polling  │
                 └──────┬───────┘
                        │
                        ↓ publish
                 ┌──────────────────────┐
                 │ Event: git.commit.v1 │
                 │ data: {commit_hash}  │
                 └──────┬───────────────┘
                        │
                        ↓ subscribed
                 ┌──────────────┐
                 │ Spec Agent   │
                 │ (listening)  │
                 └──────┬───────┘
                        │
                        ↓ analyzes commit

2. Spec Agent Creates Proposal
                 ┌──────────────┐
                 │ Spec Agent   │
                 │ finds issue  │
                 └──────┬───────┘
                        │
                        ↓ persist
                 ┌──────────────┐
                 │proposals.json│
                 │proposals.md  │
                 └──────────────┘
                        │
                        ↓ publish
                 ┌────────────────────────────┐
                 │ Event: proposal.created.v1 │
                 │ data: {proposal_id}        │
                 └────────┬───────────────────┘
                          │
                ┌─────────┴─────────┐
                ↓                   ↓
         ┌──────────────┐    ┌──────────────┐
         │Strategy Agent│    │   Extension  │
         │ (validates)  │    │ (shows user) │
         └──────────────┘    └──────┬───────┘
                                    │
                                    ↓ user clicks "Approve"

3. User Approves Proposal
                             ┌──────────────┐
                             │   Extension  │
                             │ POST /approve│
                             └──────┬───────┘
                                    │
                                    ↓
                             ┌──────────────┐
                             │   Backend    │
                             │ updates DB   │
                             └──────┬───────┘
                                    │
                                    ↓ publish
                             ┌────────────────────────────┐
                             │ Event: proposal.approved.v1│
                             │ data: {proposal_id}        │
                             └────────┬───────────────────┘
                                      │
                        ┌─────────────┴─────────────┐
                        ↓                           ↓
                 ┌──────────────┐          ┌──────────────┐
                 │  Git Agent   │          │ Spec Agent   │
                 │ (commits)    │          │ (tracks rate)│
                 └──────┬───────┘          └──────────────┘
                        │
                        ↓ if auto_commit=true
                 ┌──────────────┐
                 │ git commit   │
                 │ git push     │
                 └──────┬───────┘
                        │
                        ↓ publish
                 ┌────────────────────────┐
                 │ Event: git.commit.v1   │
                 │ data: {commit_hash}    │
                 └────────┬───────────────┘
                          │
                          ↓ cycle continues...
```

---

## Retrospective Flow (Agent "Meeting")

```
Trigger: Daily at 6pm OR milestone completed

┌─────────────────────────────────────────┐
│  Event: retrospective.trigger.v1        │
└─────────────────┬───────────────────────┘
                  │
                  ↓
         ┌────────────────────┐
         │ Retrospective Agent│
         │ (facilitator)      │
         └────────┬───────────┘
                  │
                  ↓ reads global context
         ┌────────────────────┐
         │   Firestore        │
         │ • agents states    │
         │ • artifacts        │
         │ • past retros      │
         └────────┬───────────┘
                  │
                  ↓ analyzes
         ┌────────────────────┐
         │  Generate Insights │
         │                    │
         │ • Spec approval↓   │
         │ • Git commits↑     │
         │ • Strategy blocked │
         └────────┬───────────┘
                  │
                  ↓ creates action items
         ┌────────────────────────────────┐
         │  Action Items:                 │
         │  1. Spec: be more conservative │
         │  2. Git: batch commits         │
         │  3. Strategy: unblock X        │
         └────────┬───────────────────────┘
                  │
                  ↓ publish events
         ┌────────┴────────┬────────────────┐
         ↓                 ↓                ↓
  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
  │ Spec Agent   │  │  Git Agent   │  │Strategy Agent│
  │ receives     │  │ receives     │  │ receives     │
  │ action item  │  │ action item  │  │ action item  │
  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
         │                 │                 │
         ↓                 ↓                 ↓
  Updates behavior   Updates behavior   Updates behavior
  in memory          in memory          in memory
```

---

## Artifact Producer/Consumer Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Workspace Directory                       │
│  .contextpilot/workspaces/contextpilot/                     │
├─────────────────────────────────────────────────────────────┤
│  • context.md       ← Git Agent (producer)                  │
│  • proposals.md     ← Spec Agent (producer)                 │
│  • milestones.md    ← Strategy Agent (producer)             │
│  • task_history.md  ← Git Agent (producer)                  │
│  • timeline.md      ← Git Agent (producer)                  │
└─────────────────────────────────────────────────────────────┘
                              ↑ write
                              │
                    ┌─────────┴─────────┐
                    │                   │
            ┌───────────────┐   ┌───────────────┐
            │  Spec Agent   │   │  Git Agent    │
            │  (producer)   │   │  (producer)   │
            └───────────────┘   └───────────────┘
                              
                              ↓ read
                              
                    ┌─────────────────────┐
                    │  Strategy Agent     │
                    │  (consumer)         │
                    │                     │
                    │  Reads all .md      │
                    │  Synthesizes plan   │
                    │  Updates strategy   │
                    └─────────┬───────────┘
                              │
                              ↓ write
                    ┌─────────────────────┐
                    │  milestones.md      │
                    │  (updated)          │
                    └─────────────────────┘
                              │
                              ↓ read
                    ┌─────────────────────┐
                    │  Coach Agent        │
                    │  (consumer)         │
                    │                     │
                    │  Reads milestones   │
                    │  Gives advice       │
                    └─────────────────────┘
```

---

## State Persistence Example

```
Agent Run #1 (Monday 9am)
┌──────────────┐
│ Spec Agent   │
│ runs         │
└──────┬───────┘
       │
       ↓ saves state
┌─────────────────────────────┐
│ Firestore                   │
│ agents.spec = {             │
│   issues_found: 3,          │
│   memory: {                 │
│     patterns: ["docs_drift"]│
│   }                         │
│ }                           │
└─────────────────────────────┘

Agent Run #2 (Monday 3pm)
┌──────────────┐
│ Spec Agent   │
│ runs again   │
└──────┬───────┘
       │
       ↓ loads previous state
┌─────────────────────────────┐
│ Firestore                   │
│ agents.spec = {             │
│   issues_found: 3,  ← remembers!
│   memory: {                 │
│     patterns: ["docs_drift"]│
│   }                         │
│ }                           │
└──────┬──────────────────────┘
       │
       ↓ updates state
┌─────────────────────────────┐
│ Firestore                   │
│ agents.spec = {             │
│   issues_found: 5,  ← updated
│   memory: {                 │
│     patterns: ["docs_drift",│
│                "missing_tests"]
│   }                         │
│ }                           │
└─────────────────────────────┘
```

---

## Benefits Summary

| Aspect | Current | Proposed |
|--------|---------|----------|
| **Coupling** | Tight (direct calls) | Loose (events) |
| **State** | Stateless | Persistent |
| **Scalability** | Hard to add agents | Easy to add agents |
| **Observability** | No event log | Full event history |
| **Collaboration** | None | Retrospectives |
| **Artifact Flow** | Unclear | Explicit producer/consumer |

---

**Next:** Implement `BaseAgent` class and migrate one agent (Spec) as proof of concept.

