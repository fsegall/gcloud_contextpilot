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
| **Cloud Pub/Sub** | Event bus for agent coordination and async callbacks. | Topics: `agent-events`, `retrospective-events`, `proposal-events`; toggled off locally via `USE_PUBSUB=false` for deterministic dev runs. |
| **Cloud Firestore** | Durable system of record for retrospectives, proposals, and agent state. | Used in production; local mode writes JSON mirrors under `.contextpilot/`. |
| **Secret Manager** | Stores API keys and repository credentials. | Deploy script syncs `.env` values into secrets (Gemini key, GitHub tokens, sandbox URLs). |
| **Cloud Build** | CI/CD for container builds and migrations. | Triggered by tagged releases; outputs versioned images to Artifact Registry. |
| **Artifact Registry** | Container image registry. | Cloud Run pulls signed images; retains previous revisions for rollback. |
| **Cloud Logging & Monitoring** | Observability for all services. | Log router filters agent traces; dashboards watch latency, error rate, message backlog. |
| **Identity & Access Management** | Principle-of-least-privilege enforcement. | Dedicated service account `contextpilot-backend` holds `run.invoker`, `pubsub.publisher`, `datastore.user`, `secretmanager.secretAccessor`. |

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

### 3. Intelligence Layer (Google ADK-Compatible Agents)
- `BaseAgent` implements the Google ADK lifecycle: `start`, `handle_event`, `stop`, state persistence, and artifact ingestion.
- Specialized agents (Retrospective, Development, Spec, Git, Coach, Milestone, Strategy) extend `BaseAgent` and therefore conform to ADK semantics.
- The `AgentOrchestrator` composes ADK agents and dispatches tasks based on retrospectives, proposals, or direct extension requests.
- Retrospective Agent groups action items by priority and emits ADK-compatible payloads into the event bus so the Development Agent can create at most one proposal per bucket.
- Development Agent injects ADK context (workspace metadata, retrospective ID, priority bucket) before synthesizing changes, enabling reproducible conversations if we swap to a fully managed ADK runtime.

### 4. Knowledge & Persistence Layer
- Firestore collections
  - `proposals`: change bundles, status, diff metadata, ADK context.
  - `retrospectives`: per-meeting artifacts, summary, and action items.
  - `agent_states`: metrics (events processed, errors, runtime stats).
- Markdown artifacts (retro reports, improvement plans) live in Google Cloud Storage when deployed, mirroring the local `.contextpilot/workspaces` layout.
- Event history is mirrored in Cloud Logging for centralized auditing.

---

## Key Experience Flows

### Retrospective to Proposal Flow
```
IDE command → Cloud Run `/agents/retrospective/trigger`
    → Agent Orchestrator boots Retrospective Agent (ADK lifecycle)
        → Agents exchange perspectives via ADK conversations
        → Retrospective Agent records findings in Firestore & GCS
        → High/Medium/Low action buckets published to Pub/Sub
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
  - Pub/Sub backlog and ack times
  - Firestore read/write quota
  - Agent error rate (custom metric exported via Cloud Logging filter)
- **Alerting**: Paging alerts configured for
  - 5xx rate > 2% for 10 minutes
  - Pub/Sub backlog > 100 messages
  - Secret access denied (indicates missing IAM)
- **Resilience**: Pub/Sub retries ensure Development Agent eventually processes proposals; Cloud Run revision pinning allows instant rollback.

---

## Future Enhancements
- **Managed ADK Runtime**: Toggle `USE_ADK_RUNTIME=true` to delegate orchestration to Google ADK hosted runtimes once generally available.
- **Cloud Run Jobs**: Offload long-running retrospective analytics and batch content regeneration without impacting real-time APIs.
- **BigQuery Analytics**: Persist aggregated agent metrics for longitudinal reporting and ML fine-tuning.
- **Service Mesh**: Evaluate Cloud Run + Traffic Director for zero-trust networking between microservices as the platform grows.

---

*Last updated: 2025-11-08*
