# 🏆 Cloud Run Hackathon Submission — ContextPilot

## Project Snapshot
- **Category:** AI Agents (Google Cloud Run Hackathon 2025)
- **Team:** Livre Solutions
- **Pitch:** ContextPilot keeps developers in flow by combining a VS Code/Cursor extension with a Cloud Run backend that orchestrates Google ADK-compatible agents, Pub/Sub eventing, and Firestore persistence.

---

## Challenge Alignment

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Build with multi-agent AI | ✅ | Six Google ADK-style agents (Retrospective, Development, Spec, Git, Coach, Strategy) coordinated through an ADK-compatible orchestrator. |
| Deploy to Cloud Run | ✅ | FastAPI container served at `contextpilot-backend-581368740395.us-central1.run.app`. |
| Demonstrate real problem solving | ✅ | Automates retrospectives, generates change proposals, and streamlines reviews inside the IDE. |
| Highlight Google Cloud services | ✅ | Cloud Run, Pub/Sub, Firestore, Secret Manager, Cloud Build, Artifact Registry, Cloud Logging/Monitoring. |

---

## What We Built
- **IDE-native assistant**: Dashboard view (required evaluation path), proposal diff viewers, AI review panel, and action commands surfaced via tree views and command palette.
- **Retrospective pipeline**: Cloud Run triggers ADK agents that generate insights, group action items, and persist reports in Firestore/GCS.
- **Development automation**: Development Agent converts high-priority buckets into executable proposals; Git Agent coordinates approvals with GitHub Actions.
- **Gamified feedback**: Rewards service and metrics overlays keep developers engaged while tracking progress.

---

## Google Cloud Orchestration

```
VS Code / Cursor
    │ HTTPS (authenticated on roadmap)
    ▼
Cloud Run (FastAPI)
    │ Pub/Sub topics (`agent-events`, `retrospective-events`)
    ▼
ADK-Compatible Agents (Retrospective, Development, ...)
    │ Firestore (proposals, retrospectives)
    │ Secret Manager (Gemini, GitHub, sandbox credentials)
    │ Cloud Storage (markdown artifacts)
    ▼
GitHub Actions + Local Git automation
```

| Service | Role |
|---------|------|
| **Cloud Run** | Autoscaled entry point for IDE requests and agent orchestration. |
| **Pub/Sub** | Decouples retrospective generation from proposal synthesis; supports retries. |
| **Firestore** | Durable state for proposals, retrospectives, metrics. |
| **Secret Manager** | Centralized secrets loaded at deploy; synced by `scripts/shell/deploy-cloud-run.sh`. |
| **Cloud Build + Artifact Registry** | Build & store signed images; integrate with GitHub releases. |
| **Cloud Logging & Monitoring** | Observability dashboards, error alerting, deploy verification. |

---

## Google ADK Usage
- Agents follow the ADK lifecycle (`start`, `handle_event`, `stop`) via the `BaseAgent` abstraction.
- Retrospective outcomes are packaged as ADK-ready payloads so downstream runtimes (Cloud Run or managed ADK) stay in sync.
- Configuration flag `USE_ADK_RUNTIME` allows experimentation with external ADK orchestration while preserving current in-process execution.

---

## Demo Narrative (3 Minutes)
1. **Problem & Setup (30s)**: Developers lose context when juggling tasks; open the extension and pin the Dashboard view.
2. **Dashboard Tour (30s)**: Walk through the Dashboard tree—proposals, rewards, and agent metrics—this is the mandatory testing surface for judges.
3. **Retrospective (45s)**: Trigger from IDE, show Cloud Run logs, watch ADK agents produce insights.
4. **Proposal Review (45s)**: Inspect diff, use “Ask Claude to Review,” approve to trigger Git workflow.
5. **Cloud Architecture (20s)**: Overlay diagram; highlight Cloud Run, Pub/Sub, Firestore, ADK runtime.
6. **Call to Action (10s)**: Share install link and live API endpoint.

---

## Deliverables Checklist
- [x] **Public repository** with MIT license.
- [x] **Architecture overview** (`ARCHITECTURE.md`) detailing Cloud Run and ADK orchestration.
- [x] **Try-it-now instructions** (`README.md`) for extension and backend.
- [x] **Testing guidance**: Judges are instructed to validate through the Dashboard view inside the extension.
- [x] **Live endpoint**: https://contextpilot-backend-581368740395.us-central1.run.app
- [ ] **Demo video** (recording in progress; outline finalized).
- [ ] **Devpost listing** (draft prepared, pending video upload).

---

## Judges’ Takeaways
1. **IDE-first usability**: The experience is anchored where developers work, with zero context switching.
2. **Cloud Run excellence**: Stateless service, infra-as-code deploy script, observability guardrails.
3. **ADK-ready agents**: Our agent runtime already mirrors Google ADK contracts, ensuring future compatibility.
4. **Scalable foundation**: Event-driven architecture tolerates bursts, with retries and durable state backing.
5. **Clear roadmap**: Roadmap highlights BYOK keys, dashboard, blockchain rewards, and managed ADK adoption.

---

*Contact:* hackathon@livre.solutions | [GitHub](https://github.com/fsegall/gcloud_contextpilot)
