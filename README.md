# 🚀 ContextPilot — Cloud Run Native, IDE-First Multi-Agent Assistant

ContextPilot keeps developers in flow by combining a VS Code/Cursor extension with a Google Cloud Run backend powered by Google’s Agent Development Kit (ADK). Retrospectives, change proposals, and AI reviews happen without ever leaving the IDE.

---

## Why Developers Use ContextPilot
- **Stay in the IDE**: Trigger retrospectives, inspect diffs, and request AI reviews directly from the sidebar.
- **Immediate Feedback**: Every action returns guidance in seconds thanks to Cloud Run autoscaling and lightweight payloads.
- **Actionable Proposals**: The Development Agent converts high-priority retrospective items into ready-to-apply diffs.
- **Documented Decisions**: Markdown reports and git history capture context automatically for onboarding and audits.
- **Dashboard-first testing**: The built-in Dashboard view is the canonical way to validate proposals, rewards, and agent health.

---

## Quick Start

1. **Install the extension**
   - Download the latest `.vsix` from [GitHub Releases](https://github.com/fsegall/gcloud_contextpilot/releases/latest).
   - VS Code / Cursor → Command Palette → `Extensions: Install from VSIX...`.
2. **Configure backend endpoint**
   ```json
   {
     "contextpilot.apiUrl": "https://contextpilot-backend-581368740395.us-central1.run.app"
   }
   ```
3. **Open the Dashboard view (required test path)**
   - Click the ContextPilot rocket icon in the Activity Bar.
   - Use the Dashboard tree to inspect proposals, rewards, and agent status—the hackathon review should be performed here.
4. **Trigger your first retrospective**
   - Command Palette → `ContextPilot: Start Agent Retrospective`.
   - Pick a topic and watch Spec, Git, Strategy, and Coach agents discuss it live.

### Local Backend (Optional)
```bash
# Backend
cd back-end
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp env.local.example .env  # fill in Gemini key
uvicorn app.server:app --reload --port 8000

# Update extension setting to http://localhost:8000
```

---

## Architecture at a Glance

| Layer | Technology | Responsibilities |
|-------|------------|------------------|
| **IDE Experience** | VS Code extension (TypeScript) | Commands, proposal tree, review panel, clipboard integrations. |
| **API Orchestration** | FastAPI on Cloud Run | Normalizes IDE requests, enforces auth (future), fans out tasks to agents. |
| **Agent Runtime** | Google ADK-compatible agents | Retrospective, Development, Spec, Git, Coach, Milestone, Strategy agents share a common lifecycle. |
| **Event Fabric** | Cloud Pub/Sub | Decouples long-running actions; Development Agent processes proposals asynchronously. |
| **State & Artifacts** | Firestore + Cloud Storage | Persist retrospectives, proposals, rewards, and markdown reports. |
| **Secrets & CI/CD** | Secret Manager, Cloud Build, Artifact Registry | Secure API keys, automate builds, store signed images for Cloud Run deploys. |

The detailed breakdown lives in [`ARCHITECTURE.md`](ARCHITECTURE.md).

---

## Google ADK Integration
- All agents inherit from `BaseAgent`, mirroring ADK’s `start → handle_event → stop` lifecycle.
- The Retrospective Agent bundles high/medium/low action items and publishes ADK-compatible payloads so the Development Agent can produce one proposal per priority bucket.
- The orchestration layer can delegate to an external ADK runtime by toggling configuration flags—ensuring we remain future-proof as Google releases managed runtimes.

---

## Google Cloud Services
- **Cloud Run**: Stateless FastAPI service with autoscaling and revision rollbacks.
- **Pub/Sub**: `agent-events`, `retrospective-events`, and `proposal-events` topics for cross-agent coordination.
- **Firestore**: Durable storage for proposals, retrospectives, and agent metrics.
- **Secret Manager**: Gemini keys, GitHub tokens, sandbox repository credentials.
- **Cloud Build + Artifact Registry**: Container builds and artifact lifecycle management.
- **Cloud Logging & Monitoring**: Structured logs, latency dashboards, and alert policies.

See [`HACKATHON-SUBMISSION.md`](HACKATHON-SUBMISSION.md) for how these services satisfy Cloud Run Hackathon requirements.

---

## Key User Journeys
1. **Retrospective Loop**: IDE command → Cloud Run → ADK agents collaborate → Firestore stores findings → extension displays results.
2. **Proposal Review**: User expands a proposal → extension fetches canonical diff → optional “Ask Claude to Review” → approve → Git Agent + GitHub Actions apply change.
3. **Gamified Feedback**: Rewards widget and metrics board surface CPT token accrual and agent health to keep teams engaged.
4. **Dashboard Validation (testing requirement)**: Reviewers must exercise the Dashboard view to verify change proposals, reward accrual, and agent telemetry during evaluation.

---

## Documentation Map
- [`ARCHITECTURE.md`](ARCHITECTURE.md): Cloud orchestration, ADK integration, security posture.
- [`GIT_ARCHITECTURE.md`](GIT_ARCHITECTURE.md): Two-layer git workflow (local vs GitHub Actions).
- [`ROADMAP.md`](ROADMAP.md): Product phases and Web3 milestones.
- [`STATUS.md`](STATUS.md): Current health, active work, and next steps.
- [`HACKATHON-SUBMISSION.md`](HACKATHON-SUBMISSION.md): Judge-facing summary and deliverables.
- Full catalog (architecture deep dives, guides, retrospectives, tests): [`docs/INDEX.md`](docs/INDEX.md).

---

## Contributing & Support
- Issues and feature requests: [GitHub Issues](https://github.com/fsegall/gcloud_contextpilot/issues)
- Discussions: [GitHub Discussions](https://github.com/fsegall/gcloud_contextpilot/discussions)
- Security reporting: security@livre.solutions

We welcome contributions that strengthen the usability of the extension, deepen ADK integration, or expand Google Cloud observability.
