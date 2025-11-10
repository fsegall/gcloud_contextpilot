# ContextPilot Architecture

## Experience Intent

- Deliver actionable guidance inside the IDE in under 10 seconds from the moment a developer asks for help.
- Keep all code on the developer laptop while still unlocking assisted workflows powered by Google Cloud.
- Automate the retrospective → proposal → implementation loop so teams spend time deciding, not compiling.
- Document every architectural decision in-place so onboarding takes hours, not weeks.

These usability targets drive every architectural choice described below.

---

## Layered Platform Overview

```
┌───────────────────────────────────────────────────────────────┐
│ Developer Experience Layer                                    │
│  • VS Code / Cursor extension                                 │
│  • Proposal review panel + AI review webview                  │
│  • Commands surfaced in command palette & tree views          │
└───────────────▲───────────────────────────────────────────────┘
                │ HTTPS                                           
┌───────────────┴───────────────────────────────────────────────┐
│ Cloud Run Orchestration Layer                                 │
│  • FastAPI service packaged as a Cloud Run container          │
│  • Routes user intents to multi-agent runtimes                │
│  • Exposes health, status, proposal, and retrospective APIs   │
└───────────────▲───────────────────────────────────────────────┘
                │ Pub/Sub events & ADK runtime calls             
┌───────────────┴───────────────────────────────────────────────┐
│ Intelligence Layer (Google ADK)                               │
│  • BaseAgent interface mirrors Google Agent Development Kit   │
│  • Retrospective, Development, Spec, Git, Coach, Strategy     │
│  • Agent orchestrator multiplexes ADK conversations           │
└───────────────▲───────────────────────────────────────────────┘
                │ State & artifact lookups                       
┌───────────────┴───────────────────────────────────────────────┐
│ Knowledge & Persistence Layer                                 │
│  • Firestore: proposals, retrospectives, agent metrics        │
│  • GCS / local artifacts: markdown reports & context bundles  │
│  • Secret Manager: API keys & repository credentials          │
└───────────────────────────────────────────────────────────────┘
```

---

## Google Cloud Orchestration Summary

| Service | Role in ContextPilot | Notes |
|---------|----------------------|-------|
| **Cloud Run** | Hosts the FastAPI backend that translates IDE actions to agent workloads. | Stateless container, autoscaling 0→N; `scripts/shell/deploy-cloud-run.sh` publishes new revisions with correct env vars. |
| **Google Agent Development Kit (ADK)** | Provides agent blueprints and runtime contracts. | Each agent inherits from `BaseAgent`, implementing the ADK-compatible lifecycle (`start`, `handle_event`, `stop`). The orchestrator can hand off tasks to an external ADK runtime when available. |
| **Event Fabric (in-memory / Pub/Sub-ready)** | Pluggable bus that routes agent events. | Default runtime uses `InMemoryEventBus` (`app/services/event_bus.py`); a `USE_PUBSUB=true` toggle will re-enable Google Pub/Sub once production hardening finishes (topics align with `Topics` enum). |
| **Cloud Firestore** | Durable system of record for retrospectives, proposals, and agent state. | Used in production; local mode writes JSON mirrors under `.contextpilot/`. |
| **Secret Manager** | Stores API keys and repository credentials. | Deploy script syncs `.env` values into secrets (Gemini key, GitHub tokens, sandbox URLs). |
| **Cloud Build** | CI/CD for container builds and migrations. | Triggered by tagged releases; outputs versioned images to Artifact Registry. |
| **Artifact Registry** | Container image registry. | Cloud Run pulls signed images; retains previous revisions for rollback. |
| **Cloud Logging & Monitoring** | Observability for all services. | Log router filters agent traces; dashboards watch latency, error rate, message backlog. |
| **Identity & Access Management** | Principle-of-least-privilege enforcement. | Dedicated service account `contextpilot-backend` holds `run.invoker`, `pubsub.publisher`, `datastore.user`, `secretmanager.secretAccessor`. |

> Detailed subsystem docs live under `docs/architecture/` (diagrams, ADRs, and agent-specific notes).

---

## Component Architecture

### 1. Developer Experience Layer (VS Code / Cursor Extension)
- Built in TypeScript with Webpack bundling for fast reloads.
- Presents proposals, agent health, and retrospectives as tree views aimed at minimizing cognitive load; the **Dashboard view is the canonical testing surface** for reviewers.
- When a user opens a diff, the extension lazily fetches proposal metadata to avoid blocking the UI.
- `askClaudeReview` and `viewProposalChange` commands surface a consistent usability pattern: the user never leaves the IDE to review improvements.
- Configuration is stored via VS Code settings; the default Cloud Run endpoint is injected during activation.

### 2. Cloud Run Orchestration Layer (FastAPI Service)
- Primary entry point: `back-end/app/server.py` packaged as a container.
- Routes include `/health`, `/agents/retrospective/trigger`, `/proposals`, and `/agents/status`.
- Each request is traced with contextual metadata (workspace, proposal ID, agent).
- The container is memory-tuned for ADK workloads (default 1 vCPU, 2 GB RAM) and supports up to 10 concurrent instances.
- Startup loads environment configuration from Secret Manager backed variables; credentials are injected at deploy time to avoid storing secrets inside the image.
- The runtime wires up the shared `InMemoryEventBus`; once the Pub/Sub toggle returns, the same interface will forward events to Google Cloud Pub/Sub with no agent-side changes.

### 3. Intelligence Layer (Google ADK-Compatible Agents)
- `BaseAgent` implements the Google ADK lifecycle plus shared infrastructure: JSON-backed state persistence, artifact ingestion, workspace analysis, and event bus helpers (`publish_event`, `subscribe_to_event`).
- Specialized agents (Retrospective, Development, Spec, Git, Coach, Milestone, Strategy) extend `BaseAgent`, so they inherit unified logging/metrics and the new `ProjectStructureAnalyzer` summaries.
- The `AgentOrchestrator` composes ADK agents and dispatches tasks based on retrospectives, proposals, or direct extension requests.
- Retrospective Agent groups action items by priority and emits ADK-compatible payloads into the event bus so the Development Agent can create at most one proposal per bucket.
- Development Agent injects ADK context (workspace metadata, retrospective ID, priority bucket) before synthesizing changes; current builds run on the in-memory bus while sandbox/Codespaces PR workflows are stabilized.

### 4. Knowledge & Persistence Layer
- Firestore collections
  - `proposals`: change bundles, status, diff metadata, ADK context.
  - `retrospectives`: per-meeting artifacts, summary, and action items.
  - `agent_states`: metrics (events processed, errors, runtime stats).
- Markdown artifacts (retro reports, improvement plans) live in Google Cloud Storage when deployed, mirroring the local `.contextpilot/workspaces` layout.
- Event history is mirrored in Cloud Logging for centralized auditing.

---

## Context Engineering & Workspace Artifacts

ContextPilot treats context as a first-class system component:

- **Workspace roots**: On startup the backend ensures `.contextpilot/workspaces/<workspace_id>/` exists (locally under the repo; in Cloud Run under `/app/.contextpilot`). `meta.json` and `history.json` capture creation metadata and event timelines.
- **Checkpoint contract**: `checkpoint.yaml` stores `project_name`, `goal`, `current_status`, and `milestones`. The `/context` endpoint reads this file first, and the Spec, Strategy, and Coach agents update it after retrospectives or manual edits via the extension. Legacy `PROJECT.md/GOAL.md/STATUS.md` remain fallback-only for backwards compatibility.
- **Knowledge artifacts**: `context.md`, `project_scope.md`, `project_checklist.md`, `milestones.md`, `timeline.md`, `daily_checklist.md`, `DECISIONS.md`, and `coding_standards.md` are maintained collaboratively by agents (Spec, Strategy, Git, Coach) and developers. Each file includes natural-language rules declared in `artifacts.yaml`, defining which agent produces or consumes it.
- **Retrospective evidence**: Every retrospective saves JSON + Markdown under `retrospectives/`. The Development Agent links proposals back to these artifacts for traceability.
- **IDE bridge**: The extension’s Context Tree, “View Context Detail”, “View Related Files”, and “Ask Claude to Review” commands read/write the same workspace directory so human edits, agent updates, and AI prompts stay in sync. When files are missing the extension scaffolds them with templates that match `checkpoint.yaml`.
- **Cloud mirroring**: In cloud mode the Git agent and storage utilities mirror `.contextpilot/workspaces/...` to Cloud Storage so downstream analytics (BigQuery, dashboards) have the same structure as local development.

This context engineering strategy ensures every agent action and IDE surface is grounded in the same living knowledge base, reducing drift and keeping long-running projects aligned.

---

## Key Experience Flows

### Retrospective to Proposal Flow
```
IDE command → Cloud Run `/agents/retrospective/trigger`
    → Agent Orchestrator boots Retrospective Agent (ADK lifecycle)
        → Agents exchange perspectives via ADK conversations
        → Retrospective Agent records findings in Firestore & GCS
        → High/Medium/Low action buckets published to the event bus (in-memory today, Pub/Sub when enabled)
    → Development Agent consumes events, generates code proposals
    → Firestore stores proposal; extension receives push update
```

### Proposal Review Flow
```
User selects proposal in extension tree
    → Extension requests `/proposals/{id}` from Cloud Run
    → Backend loads Firestore record + diffs from storage
    → Response streamed to extension; diff rendered in IDE
    → Approve action triggers `/proposals/{id}/approve`
        → Backend emits `proposal.approved.v1` event
        → Git Agent applies change locally (workspace checkout)
        → GitHub Actions workflow receives repository_dispatch
```

### Deployment Workflow
1. `env.cloud-run.example` → `.env` with real credentials.
2. `scripts/shell/deploy-cloud-run.sh` loads env vars, syncs Secret Manager, builds container (Cloud Build), deploys revision to Cloud Run.
3. Smoke test: `curl https://.../health` and `gcloud run services logs read` to verify runtime.

---

## Security & Governance
- **Secret Boundary**: No secrets committed; deploy script ensures Secret Manager has the latest Gemini, GitHub, and sandbox tokens before deploy.
- **IAM Separation**: Cloud Run service account does not possess project owner rights; infrastructure changes require Terraform service account.
- **Request Hardening**: FastAPI middleware applies request ID stamping, log correlation, and rate-limiting hooks; Cloud Armor (optional) can guard the public endpoint.
- **Data Residency**: Firestore (us-central) keeps proposals and retrospectives; sensitive code never leaves the developer machine—only diffs and metadata are stored.

---

## Observability & Reliability
- **Logging**: Structured logs with `agent`, `workspace`, `proposal_id` fields. `gcloud run services logs read contextpilot-backend --log-filter="severity>=ERROR"` is part of runbooks.
- **Metrics**: Cloud Monitoring dashboard tracks
  - Cloud Run latency & concurrency
  - Event bus health (Pub/Sub backlog once the remote bus is re-enabled)
  - Firestore read/write quota
  - Agent error rate (custom metric exported via Cloud Logging filter)
- **Alerting**: Paging alerts configured for
  - 5xx rate > 2% for 10 minutes
  - Event backlog (Pub/Sub) > 100 messages (future toggle)
  - Secret access denied (indicates missing IAM)
- **Resilience**: The event bus interface is idempotent; once Pub/Sub is reintroduced its retries will ensure Development Agent eventually processes proposals, while Cloud Run revision pinning allows instant rollback today.

---

## Future Enhancements
- **Managed ADK Runtime**: Toggle `USE_ADK_RUNTIME=true` to delegate orchestration to Google ADK hosted runtimes once generally available.
- **Cloud Run Jobs**: Offload long-running retrospective analytics and batch content regeneration without impacting real-time APIs.
- **BigQuery Analytics**: Persist aggregated agent metrics for longitudinal reporting and ML fine-tuning.
- **Service Mesh**: Evaluate Cloud Run + Traffic Director for zero-trust networking between microservices as the platform grows.

---

*Last updated: 2025-11-08*
