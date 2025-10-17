# 🚀 ContextPilot Backend

**Multi-agent AI system deployed on Google Cloud Run**

FastAPI backend that coordinates 6 specialized AI agents via Pub/Sub and Firestore, providing intelligent development assistance through a VS Code extension.

---

## 🏗️ Architecture

```
VS Code Extension
    ↓ (HTTPS/REST)
FastAPI Backend (Cloud Run Service)
    ↓
Multi-Agent System
    ├─► Spec Agent (documentation)
    ├─► Git Agent (commits)
    ├─► Context Agent (analysis)
    ├─► Coach Agent (tips)
    ├─► Milestone Agent (tracking)
    └─► Strategy Agent (patterns)
    ↓
Google Cloud Services
    ├─► Pub/Sub (event bus)
    ├─► Firestore (database)
    ├─► Gemini API (AI generation)
    └─► Secret Manager (API keys)
```

---

## 🚀 Quick Start

### Option 1: Use Production API (Easiest)

Extension connects automatically to our deployed backend:
```
https://contextpilot-backend-581368740395.us-central1.run.app
```

No setup needed! Just install the extension.

### Option 2: Run Locally with Docker Compose

```bash
# From project root
echo "GOOGLE_API_KEY=your-key" > .env
docker-compose up

# Backend will be at http://localhost:8000
```

### Option 3: Run Locally with Python

```bash
cd back-end

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp ../ENV_TEMPLATE.md .env
# Edit .env with your GOOGLE_API_KEY

# Run server
uvicorn app.server:app --reload --port 8000

# Test
curl http://localhost:8000/health
```

### Option 4: Deploy to Cloud Run with Terraform

See [../terraform/README.md](../terraform/README.md) for complete deployment guide.

---

## 📁 Project Structure

```
back-end/
├── app/
│   ├── agents/              # 6 specialized AI agents
│   │   ├── base_agent.py    # Base class for all agents
│   │   ├── spec_agent.py    # Documentation agent
│   │   ├── git_agent.py     # Git operations agent
│   │   ├── context_agent.py # Project analysis
│   │   ├── coach_agent.py   # Development tips
│   │   ├── milestone_agent.py
│   │   └── strategy_agent.py
│   ├── services/            # Core services
│   │   ├── event_bus.py     # Pub/Sub & in-memory event bus
│   │   ├── firestore_service.py
│   │   └── llm_service.py   # Gemini API wrapper
│   ├── middleware/          # Request processing
│   │   └── abuse_detection.py
│   ├── repositories/        # Data access layer
│   │   └── proposal_repository.py
│   ├── templates/           # Markdown templates for agents
│   ├── server.py            # FastAPI application
│   └── git_context_manager.py
├── requirements.txt         # Python dependencies
├── Dockerfile              # Cloud Run container
└── README.md              # This file
```

---

## 🌐 API Endpoints

### Core Endpoints

```bash
# Health check
GET /health

# List proposals
GET /proposals?workspace_id=default&status=pending

# Get specific proposal
GET /proposals/{proposal_id}

# Create proposal
POST /proposals/create

# Approve proposal
POST /proposals/{proposal_id}/approve

# Reject proposal
POST /proposals/{proposal_id}/reject

# Agent status
GET /agents/status

# Context summary (for AI)
GET /context/summary?workspace_id=default

# Admin stats
GET /admin/abuse-stats
```

**Full API Spec:** See [../openapi.yaml](../openapi.yaml) or visit `/docs` on running server.

---

## 🤖 Multi-Agent System

### How Agents Work

1. **Event Subscription**: Each agent subscribes to specific Pub/Sub topics
2. **Event Processing**: When event arrives, agent processes asynchronously
3. **AI Generation**: Agent may call Gemini API for intelligent responses
4. **State Persistence**: Results saved to Firestore
5. **Event Publishing**: Agent may publish new events for other agents

### Example: Proposal Approval Flow

```python
# 1. Extension calls API
POST /proposals/{id}/approve

# 2. API marks as approved in Firestore
proposal.status = "approved"
firestore.update(proposal)

# 3. API publishes event
event_bus.publish(
    topic="proposal-events",
    event_type="proposal.approved.v1",
    data={"proposal_id": id}
)

# 4. Git Agent receives event
# (if using Pub/Sub)
git_agent.handle_event("proposal.approved.v1", data)

# 5. Extension handles locally
# (applies changes, commits, rewards user)
```

---

## 🛡️ Security Features

- **Rate Limiting**: 100 requests/hour per IP
- **Abuse Detection**: Automatic blacklisting of malicious patterns
- **Secret Management**: API keys in GCP Secret Manager (production)
- **Input Validation**: Pydantic models for all endpoints
- **Error Handling**: Safe error messages (no stack traces leaked)

See [../SECURITY.md](../SECURITY.md) for details.

---

## 🧪 Testing

```bash
# Run tests (if implemented)
pytest

# Test specific agent
pytest tests/test_spec_agent.py

# Test with coverage
pytest --cov=app tests/
```

---

## 📊 Monitoring

### Cloud Run (Production)

```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50

# Check abuse stats
curl https://contextpilot-backend-581368740395.us-central1.run.app/admin/abuse-stats

# View monitoring dashboard
# GCP Console → Monitoring → Dashboards → "ContextPilot Monitoring"
```

### Local Development

```bash
# Logs go to console and server.log
tail -f server.log
```

---

## 🔧 Configuration

### Environment Variables

See [ENV_TEMPLATE.md](../ENV_TEMPLATE.md) for complete list.

**Key variables:**
- `GOOGLE_API_KEY`: Gemini API key (required)
- `FIRESTORE_ENABLED`: Use Firestore (true) or local files (false)
- `USE_PUBSUB`: Use Pub/Sub (true) or in-memory (false)
- `GCP_PROJECT_ID`: Google Cloud project ID

### Feature Flags

- `CONTEXTPILOT_AUTO_APPROVE_PROPOSALS`: Auto-approve proposals (for testing)

---

## 📚 Documentation

- **Architecture**: [../ARCHITECTURE.md](../ARCHITECTURE.md)
- **Agents**: [../docs/agents/](../docs/agents/)
- **Security**: [../SECURITY.md](../SECURITY.md)
- **Deployment**: [../terraform/README.md](../terraform/README.md)

---

## 🤝 Contributing

See [../CONTRIBUTING.md](../CONTRIBUTING.md) for development guidelines.

---

**Built with ❤️ by Livre Solutions for the Cloud Run Hackathon 2025**
