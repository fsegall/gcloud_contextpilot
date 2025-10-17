# 🤖 ContextPilot AI Agents

## Overview

ContextPilot uses a **multi-agent system** where 6 specialized AI agents collaborate to maintain project context, documentation, and development momentum.

All agents are deployed on **Google Cloud Run** and communicate via **Pub/Sub** event bus.

---

## 🎯 The 6 Agents

### 1. 📄 Spec Agent
**Purpose:** Documentation curator and validator

**Responsibilities:**
- Generate and maintain `.md` documentation files
- Validate documentation freshness
- Create custom templates
- Detect documentation drift
- Generate context summaries for AI

**Events Consumed:** `context.delta.v1`, `spec.request.v1`, `git.commit.v1`  
**Events Published:** `spec.update.v1`, `spec.validation.v1`

**Example:** When you rename a function, Spec Agent detects it and proposes updating the README.

---

### 2. 🌳 Git Agent
**Purpose:** Centralized Git operations manager

**Responsibilities:**
- Create semantic commits (conventional commits format)
- Manage branches (git-flow)
- Generate commit messages from proposals
- Provide git context for other agents

**Events Consumed:** `proposal.approved.v1`, `milestone.complete.v1`  
**Events Published:** `git.commit.v1`, `git.branch.created.v1`

**Example:** When you approve a proposal, Git Agent logs the approval and provides commit history to Spec Agent.

**Note:** In current architecture, git operations happen **locally** (extension), not in Cloud Run (stateless containers).

---

### 3. 🔍 Context Agent
**Purpose:** Real-time project analysis

**Responsibilities:**
- Track file changes
- Detect architectural shifts
- Monitor project health
- Generate project insights

**Events Consumed:** `file.changed.v1`, `context.request.v1`  
**Events Published:** `context.delta.v1`, `context.update.v1`

**Example:** Detects when you add many new files in a directory and suggests updating the architecture docs.

---

### 4. 💬 Coach Agent
**Purpose:** Personalized development guidance

**Responsibilities:**
- Provide actionable tips (<25 min tasks)
- Unblock developers
- Suggest next steps
- Celebrate wins

**Events Consumed:** `coach.ask.v1`, `milestone.complete.v1`  
**Events Published:** `coach.tip.v1`, `coach.nudge.v1`

**Example:** When you're stuck, suggests breaking the problem into smaller pieces or taking a different approach.

---

### 5. 🎯 Milestone Agent
**Purpose:** Progress tracking and goal management

**Responsibilities:**
- Track project milestones
- Monitor progress toward goals
- Create checkpoints
- Generate progress reports

**Events Consumed:** `milestone.check.v1`, `context.delta.v1`  
**Events Published:** `milestone.complete.v1`, `milestone.at_risk.v1`

**Example:** Tracks that you completed 8/10 tasks for a milestone and notifies you're almost done.

---

### 6. 📊 Strategy Agent
**Purpose:** Pattern analysis and strategic suggestions

**Responsibilities:**
- Analyze development patterns
- Suggest improvements
- Detect anti-patterns
- Recommend best practices

**Events Consumed:** `strategy.analyze.v1`, `context.delta.v1`  
**Events Published:** `strategy.suggestion.v1`

**Example:** Notices you're creating many similar components and suggests extracting a base class.

---

## 🔄 How Agents Collaborate

### Event-Driven Architecture

```
User Action (Extension)
    ↓
API Request → Cloud Run Service
    ↓
Event Published → Pub/Sub Topic
    ↓
Multiple Agents Subscribe
    ├─► Spec Agent (generates docs)
    ├─► Git Agent (provides context)
    ├─► Context Agent (analyzes change)
    └─► Coach Agent (suggests next step)
    ↓
Agents Process Independently
    ↓
Results Saved to Firestore
    ↓
Events Published (if needed)
    ↓
Extension Receives Updates
```

### Example: Approving a Proposal

```
1. User approves proposal in extension
   ↓
2. Extension → POST /proposals/{id}/approve
   ↓
3. Backend → Firestore (mark approved)
   ↓
4. Backend → Pub/Sub (publish proposal.approved.v1)
   ↓
5. Git Agent → Receives event, logs approval
   ↓
6. Spec Agent → May update related docs
   ↓
7. Extension → Applies changes locally, commits, rewards user
```

---

## 🏗️ Agent Architecture

### Base Agent Class

All agents inherit from `BaseAgent`:

```python
class BaseAgent:
    def __init__(self, workspace_id: str, agent_id: str):
        self.workspace_id = workspace_id
        self.agent_id = agent_id
        self.event_bus = get_event_bus(agent_id=agent_id)
        
    async def handle_event(self, event_type: str, data: Dict):
        # Process event
        pass
    
    def subscribe_to_event(self, event_type: str):
        # Subscribe to Pub/Sub topic
        pass
```

### Agent Lifecycle

1. **Initialization**: Agent subscribes to relevant Pub/Sub topics
2. **Listening**: Waits for events (serverless, pay-per-use)
3. **Processing**: When event arrives, agent wakes up and processes
4. **AI Generation**: May call Gemini API for intelligent responses
5. **State Update**: Saves results to Firestore
6. **Event Publishing**: May publish new events for other agents
7. **Shutdown**: Auto-scales to zero when idle

---

## 🎛️ Configuration

Agents are configured via environment variables and Firestore:

```python
# Global config
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
FIRESTORE_ENABLED = os.getenv("FIRESTORE_ENABLED", "false") == "true"
USE_PUBSUB = os.getenv("USE_PUBSUB", "false") == "true"

# Agent-specific config (from Firestore or defaults)
agent_config = {
    "gemini_model": "gemini-1.5-flash",
    "max_tokens": 2048,
    "temperature": 0.7,
    "enable_auto_actions": False  # Agents propose, don't auto-apply
}
```

---

## 📚 Detailed Documentation

For complete specifications of each agent:

- **[Spec Agent](AGENT.spec.md)** - Documentation management (Portuguese - legacy)
- **[Git Agent](AGENT.git.md)** - Git operations (Portuguese - legacy)
- **[Coach Agent](AGENT.coach.md)** - Development guidance (Portuguese - legacy)

**Note:** Detailed agent docs are in Portuguese from early development. 
This README provides the essential overview in English. 
Full English documentation coming in next iteration.

---

## 🔧 Development

### Adding a New Agent

```python
# 1. Create agent file
# back-end/app/agents/my_agent.py

from .base_agent import BaseAgent
from ..services.event_bus import EventTypes, Topics

class MyAgent(BaseAgent):
    def __init__(self, workspace_id: str):
        super().__init__(workspace_id=workspace_id, agent_id="my_agent")
        self.subscribe_to_event(EventTypes.MY_EVENT)
    
    async def handle_event(self, event_type: str, data: Dict):
        # Process event
        result = await self.process(data)
        
        # Publish result
        await self.publish_event(
            topic=Topics.MY_EVENTS,
            event_type=EventTypes.MY_RESULT,
            data=result
        )
```

```hcl
# 2. Add to Terraform (terraform/main.tf)

resource "google_pubsub_topic" "my_events" {
  name = "my-events"
}

resource "google_pubsub_subscription" "my_agent_sub" {
  name  = "my-agent-sub"
  topic = google_pubsub_topic.my_events.name
}
```

---

## 🎯 Design Principles

1. **Single Responsibility**: Each agent has one clear purpose
2. **Event-Driven**: Agents react to events, don't poll
3. **Propose, Don't Auto-Apply**: Agents suggest, humans approve
4. **Idempotent**: Safe to retry operations
5. **Observable**: Comprehensive logging and metrics
6. **Scalable**: Stateless services on Cloud Run

---

**Built for Cloud Run Hackathon 2025 - AI Agents Category**

