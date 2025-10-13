# 🚌 ContextPilot Event Bus Architecture

## Overview

O Event Bus é a **fonte única de verdade** para comunicação entre agentes no ContextPilot. Usando Google Cloud Pub/Sub, garantimos comunicação assíncrona, confiável e auditável.

**Core Principle:** Event-driven architecture - Agentes reagem a eventos, não se chamam diretamente.

---

## 🎯 Why Google Pub/Sub?

### vs Kafka

| Feature | Kafka | **Pub/Sub** | Winner |
|---------|-------|-------------|--------|
| Setup | Complex (Zookeeper, brokers) | Zero setup | ✅ Pub/Sub |
| Scaling | Manual | Auto-scale | ✅ Pub/Sub |
| Integration | External | Native GCP | ✅ Pub/Sub |
| Cost | $$ (infra + ops) | $ (pay-per-use) | ✅ Pub/Sub |
| Reliability | 99.9% | 99.95% SLA | ✅ Pub/Sub |
| Global | Multi-region setup | Built-in | ✅ Pub/Sub |
| Monitoring | Custom | Cloud Console | ✅ Pub/Sub |

### vs Redis Streams

| Feature | Redis Streams | **Pub/Sub** | Winner |
|---------|---------------|-------------|--------|
| Persistence | In-memory | Durable | ✅ Pub/Sub |
| Message Retention | Manual | 7 days default | ✅ Pub/Sub |
| Ordering | Per-stream | Per-key | Tie |
| Dead Letter Queue | Custom | Built-in | ✅ Pub/Sub |
| Integration | External | Native GCP | ✅ Pub/Sub |
| Operations | Manage cluster | Serverless | ✅ Pub/Sub |

### Verdict

✅ **Google Pub/Sub** é a escolha ideal porque:
1. **Zero Ops**: Serverless, auto-scaling
2. **Native Integration**: Funciona perfeitamente com Cloud Run
3. **Cost-Effective**: Pay only for what you use
4. **Reliability**: 99.95% SLA, mensagens duráveis
5. **Simplicity**: API simples, setup em minutos

**Não é exagero** - é a ferramenta certa para o problema certo.

---

## 🏗️ Architecture

### Topic Structure

```
┌─────────────────────────────────────────────────┐
│           Google Cloud Pub/Sub                  │
├─────────────────────────────────────────────────┤
│                                                 │
│  Topics (Event Types):                          │
│  ├─ context-updates                             │
│  ├─ spec-updates                                │
│  ├─ strategy-insights                           │
│  ├─ milestone-events                            │
│  ├─ coach-nudges                                │
│  ├─ git-events                                  │
│  ├─ proposals-events                            │
│  └─ rewards-events                              │
│                                                 │
│  Subscriptions (Consumers):                     │
│  ├─ context-to-strategy (push)                  │
│  ├─ context-to-spec (push)                      │
│  ├─ context-to-coach (push)                     │
│  ├─ proposals-to-git (push)                     │
│  ├─ git-to-spec (push)                          │
│  ├─ all-to-audit (pull)                         │
│  └─ all-to-bigquery (push)                      │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Event Flow Example

```
Developer commits code
    ↓
Git Agent emits → "git-events" topic
    ↓
Pub/Sub routes to:
    ├─► Context Agent (via context-from-git sub)
    ├─► Spec Agent (via spec-from-git sub)
    └─► Audit Logger (via audit-from-all sub)
    ↓
Context Agent processes, emits → "context-updates" topic
    ↓
Pub/Sub routes to:
    ├─► Strategy Agent (via strategy-from-context sub)
    ├─► Coach Agent (via coach-from-context sub)
    └─► Rewards Engine (via rewards-from-context sub)
    ↓
Strategy Agent analyzes, emits → "strategy-insights" topic
    ↓
Coach Agent creates nudge → "coach-nudges" topic
    ↓
Frontend subscribes → User sees notification
```

---

## 📋 Topics & Subscriptions

### Topic: context-updates

**Published by:** Context Agent  
**Message Schema:**
```json
{
  "event_id": "evt_ctx_001",
  "event_type": "context.update.v1",
  "timestamp": "2025-10-14T10:00:00Z",
  "source": "context-agent",
  "data": {
    "files_changed": ["src/auth.py"],
    "lines_added": 150,
    "lines_removed": 30,
    "commit_hash": "abc123",
    "impact_score": 7.5,
    "change_type": "refactor"
  }
}
```

**Subscribers:**
- `strategy-from-context` → Strategy Agent
- `spec-from-context` → Spec Agent
- `coach-from-context` → Coach Agent
- `rewards-from-context` → Rewards Engine

### Topic: proposals-events

**Published by:** Strategy Agent, Spec Agent  
**Message Schema:**
```json
{
  "event_id": "evt_prop_001",
  "event_type": "proposal.created.v1",
  "timestamp": "2025-10-14T10:05:00Z",
  "source": "strategy-agent",
  "data": {
    "proposal_id": "cp_042",
    "type": "refactor",
    "title": "Extract AuthService",
    "files_affected": 4,
    "impact": "medium",
    "user_id": "dev_123"
  }
}
```

**Subscribers:**
- `git-from-proposals` → Git Agent (on approval)
- `coach-from-proposals` → Coach Agent (create nudge)
- `ui-from-proposals` → Frontend (notification)

### Topic: git-events

**Published by:** Git Agent  
**Message Schema:**
```json
{
  "event_id": "evt_git_001",
  "event_type": "git.commit.v1",
  "timestamp": "2025-10-14T10:10:00Z",
  "source": "git-agent",
  "data": {
    "branch": "agent/refactor-auth",
    "commit_hash": "def456",
    "message": "agent(auth): Extract AuthService",
    "files_changed": ["src/auth.py"],
    "proposal_id": "cp_042"
  }
}
```

**Subscribers:**
- `context-from-git` → Context Agent (detect changes)
- `spec-from-git` → Spec Agent (update CHANGELOG)
- `rewards-from-git` → Rewards Engine (track action)

---

## 🔧 Setup

### Create Topics

```bash
#!/bin/bash
# infra/setup-pubsub.sh

PROJECT_ID=$(gcloud config get-value project)

# Create topics
gcloud pubsub topics create context-updates --project=$PROJECT_ID
gcloud pubsub topics create spec-updates --project=$PROJECT_ID
gcloud pubsub topics create strategy-insights --project=$PROJECT_ID
gcloud pubsub topics create milestone-events --project=$PROJECT_ID
gcloud pubsub topics create coach-nudges --project=$PROJECT_ID
gcloud pubsub topics create git-events --project=$PROJECT_ID
gcloud pubsub topics create proposals-events --project=$PROJECT_ID
gcloud pubsub topics create rewards-events --project=$PROJECT_ID

# Create audit topic (collects all)
gcloud pubsub topics create audit-all --project=$PROJECT_ID
```

### Create Subscriptions

```bash
# Strategy Agent subscriptions
gcloud pubsub subscriptions create strategy-from-context \
  --topic=context-updates \
  --push-endpoint=https://strategy-agent-HASH.run.app/events \
  --ack-deadline=60

# Spec Agent subscriptions
gcloud pubsub subscriptions create spec-from-context \
  --topic=context-updates \
  --push-endpoint=https://spec-agent-HASH.run.app/events \
  --ack-deadline=60

gcloud pubsub subscriptions create spec-from-git \
  --topic=git-events \
  --push-endpoint=https://spec-agent-HASH.run.app/events \
  --ack-deadline=60

# Git Agent subscriptions
gcloud pubsub subscriptions create git-from-proposals \
  --topic=proposals-events \
  --filter='attributes.event_type="proposal.approved.v1"' \
  --push-endpoint=https://git-agent-HASH.run.app/events \
  --ack-deadline=120

# Audit subscription (pull mode)
gcloud pubsub subscriptions create audit-from-all \
  --topic=context-updates \
  --topic=spec-updates \
  --topic=strategy-insights \
  --topic=git-events \
  --topic=proposals-events
```

---

## 💻 Implementation

### Publishing Events (Python)

```python
# app/services/event_bus.py
from google.cloud import pubsub_v1
import json
from datetime import datetime, timezone

class EventBus:
    def __init__(self, project_id: str):
        self.publisher = pubsub_v1.PublisherClient()
        self.project_id = project_id
    
    async def publish(
        self, 
        topic: str, 
        event_type: str, 
        data: dict,
        source: str,
        attributes: dict = None
    ):
        """
        Publish event to Pub/Sub topic.
        
        Args:
            topic: Topic name (e.g., 'context-updates')
            event_type: Event type (e.g., 'context.update.v1')
            data: Event payload
            source: Agent that created event
            attributes: Optional message attributes
        """
        topic_path = self.publisher.topic_path(self.project_id, topic)
        
        # Standard event envelope
        event = {
            "event_id": generate_event_id(),
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": source,
            "data": data
        }
        
        # Message attributes for filtering
        attrs = attributes or {}
        attrs["event_type"] = event_type
        attrs["source"] = source
        
        # Publish
        message_json = json.dumps(event)
        future = self.publisher.publish(
            topic_path,
            data=message_json.encode("utf-8"),
            **attrs
        )
        
        message_id = future.result()
        logger.info(f"Published {event_type} to {topic}: {message_id}")
        
        return message_id


# Usage in agents
event_bus = EventBus(project_id="your-project")

# Context Agent publishes
await event_bus.publish(
    topic="context-updates",
    event_type="context.update.v1",
    source="context-agent",
    data={
        "files_changed": ["src/auth.py"],
        "impact_score": 7.5
    }
)
```

### Receiving Events (Cloud Run Push)

```python
# app/routers/events.py
from fastapi import APIRouter, Request, HTTPException
import base64
import json

router = APIRouter(prefix="/events", tags=["events"])

@router.post("/")
async def receive_event(request: Request):
    """
    Receive Pub/Sub push message.
    
    Pub/Sub sends:
    {
      "message": {
        "data": "base64-encoded-json",
        "attributes": { "event_type": "..." },
        "messageId": "...",
        "publishTime": "..."
      },
      "subscription": "..."
    }
    """
    envelope = await request.json()
    
    # Extract message
    pubsub_message = envelope.get("message")
    if not pubsub_message:
        raise HTTPException(400, "Invalid Pub/Sub message")
    
    # Decode data
    data_bytes = base64.b64decode(pubsub_message["data"])
    event = json.loads(data_bytes)
    
    # Get attributes
    attributes = pubsub_message.get("attributes", {})
    event_type = attributes.get("event_type")
    
    # Route to handler
    await handle_event(event_type, event)
    
    # Acknowledge (return 200)
    return {"status": "ok"}


async def handle_event(event_type: str, event: dict):
    """Route event to appropriate handler."""
    
    handlers = {
        "context.update.v1": handle_context_update,
        "git.commit.v1": handle_git_commit,
        "proposal.approved.v1": handle_proposal_approved,
    }
    
    handler = handlers.get(event_type)
    if handler:
        await handler(event)
    else:
        logger.warning(f"No handler for event type: {event_type}")
```

---

## 🛡️ Reliability Features

### 1. Message Retention

```bash
# Messages retained for 7 days by default
# Can extend up to 31 days

gcloud pubsub topics update context-updates \
  --message-retention-duration=7d
```

### 2. Dead Letter Queue

```bash
# Create DLQ topic
gcloud pubsub topics create context-updates-dlq

# Create DLQ subscription
gcloud pubsub subscriptions update strategy-from-context \
  --dead-letter-topic=context-updates-dlq \
  --max-delivery-attempts=5
```

### 3. Retry Policy

```bash
gcloud pubsub subscriptions update strategy-from-context \
  --min-retry-delay=10s \
  --max-retry-delay=600s
```

### 4. Message Ordering

```bash
# For events that must be processed in order
gcloud pubsub subscriptions create spec-from-git-ordered \
  --topic=git-events \
  --enable-message-ordering \
  --push-endpoint=https://spec-agent-HASH.run.app/events
```

---

## 📊 Monitoring

### Metrics to Track

**Cloud Monitoring Dashboard:**
```yaml
dashboard:
  widgets:
    - title: "Messages Published (by topic)"
      metric: pubsub.googleapis.com/topic/send_request_count
      
    - title: "Messages Delivered (by subscription)"
      metric: pubsub.googleapis.com/subscription/pull_request_count
      
    - title: "Unacked Messages"
      metric: pubsub.googleapis.com/subscription/num_undelivered_messages
      
    - title: "Oldest Unacked Message Age"
      metric: pubsub.googleapis.com/subscription/oldest_unacked_message_age
      
    - title: "Push Success Rate"
      metric: pubsub.googleapis.com/subscription/push_request_count
      filter: response_class="success"
```

### Alerts

```yaml
alerts:
  - name: "High Unacked Messages"
    condition: num_undelivered_messages > 1000
    duration: 5min
    action: "Page on-call engineer"
    
  - name: "Old Messages"
    condition: oldest_unacked_message_age > 3600s
    duration: 10min
    action: "Send Slack alert"
    
  - name: "Push Failures"
    condition: push_request_count(response_class="error") > 10%
    duration: 5min
    action: "Investigate endpoint health"
```

---

## 🧪 Testing

### Local Development (Emulator)

```bash
# Start Pub/Sub emulator
gcloud beta emulators pubsub start \
  --project=test-project \
  --host-port=localhost:8085

# Set env var
export PUBSUB_EMULATOR_HOST=localhost:8085

# Now your code uses emulator instead of production
```

### Integration Tests

```python
# tests/test_event_bus.py
import pytest
from app.services.event_bus import EventBus

@pytest.mark.asyncio
async def test_publish_event(pubsub_emulator):
    event_bus = EventBus(project_id="test-project")
    
    message_id = await event_bus.publish(
        topic="context-updates",
        event_type="context.update.v1",
        source="test",
        data={"test": True}
    )
    
    assert message_id is not None
    
    # Verify message received
    messages = await pull_messages("context-updates")
    assert len(messages) == 1
    assert messages[0]["data"]["test"] is True
```

---

## 💰 Cost Optimization

### Pricing

| Resource | Cost |
|----------|------|
| First 10 GB/month | Free |
| Next 50 GB/month | $40/TB |
| After 60 GB | $50/TB |

### Example: 1000 events/day

```
Events per month: 30,000
Average size: 1 KB
Total data: 30 MB/month

Cost: Free tier ✅
```

### Tips

1. **Batch messages** when possible
2. **Use attributes** for filtering (reduces unnecessary deliveries)
3. **Set appropriate retention** (don't need 31 days for all topics)
4. **Pull subscriptions** for batch processing (cheaper than push)

---

## 🚀 Deployment

### Terraform Config

```hcl
# infra/terraform/pubsub.tf
resource "google_pubsub_topic" "context_updates" {
  name = "context-updates"
  
  message_retention_duration = "604800s"  # 7 days
  
  labels = {
    environment = "production"
    component   = "event-bus"
  }
}

resource "google_pubsub_subscription" "strategy_from_context" {
  name  = "strategy-from-context"
  topic = google_pubsub_topic.context_updates.name
  
  push_config {
    push_endpoint = "https://strategy-agent-${var.hash}.run.app/events"
    
    oidc_token {
      service_account_email = google_service_account.strategy_agent.email
    }
  }
  
  ack_deadline_seconds = 60
  
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
  
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.context_updates_dlq.id
    max_delivery_attempts = 5
  }
}
```

---

## 🎯 Best Practices

### 1. Event Versioning

```python
# Good: Include version in event type
event_type = "context.update.v1"

# When breaking changes needed, create v2
event_type = "context.update.v2"

# Both can coexist during migration
```

### 2. Idempotency

```python
# Events may be delivered more than once
# Use event_id to deduplicate

processed_events = set()

async def handle_event(event):
    if event["event_id"] in processed_events:
        logger.info("Event already processed, skipping")
        return
    
    # Process event
    await do_work(event)
    
    # Mark as processed
    processed_events.add(event["event_id"])
```

### 3. Error Handling

```python
@router.post("/events")
async def receive_event(request: Request):
    try:
        event = await parse_event(request)
        await handle_event(event)
        return {"status": "ok"}
        
    except RetryableError as e:
        # Return 5xx to trigger retry
        raise HTTPException(500, str(e))
        
    except NonRetryableError as e:
        # Return 200 to ack (don't retry)
        logger.error(f"Non-retryable error: {e}")
        return {"status": "error", "error": str(e)}
```

---

## 📖 Summary

### Why Pub/Sub is Perfect for ContextPilot

✅ **Zero Operations** - No Kafka cluster to manage  
✅ **Auto-Scaling** - Handles spikes automatically  
✅ **Native GCP** - Works seamlessly with Cloud Run  
✅ **Cost-Effective** - Free tier covers development  
✅ **Reliable** - 99.95% SLA, durable messages  
✅ **Simple** - Setup in minutes, not days  

### Not Overkill

For a multi-agent system with 5+ agents:
- ✅ **Decoupling**: Agents don't know about each other
- ✅ **Reliability**: Messages not lost if agent is down
- ✅ **Scalability**: Each agent scales independently
- ✅ **Auditability**: Every event is logged
- ✅ **Replay**: Can replay events for debugging

**Verdict:** Pub/Sub is the RIGHT tool, not overkill! 🎯

---

**Status**: ✅ **Architecture complete**  
**Next**: Implement event handlers in agents  
**Cost**: ~$0-10/month (development), ~$50-100/month (production 1000 users)

