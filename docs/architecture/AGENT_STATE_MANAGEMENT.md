# Agent State Management & Event-Driven Architecture

**Date:** October 15, 2025  
**Status:** 🚧 Design Document

## Problem Statement

1. **No Event Bus**: Agents are called directly via HTTP, not through Pub/Sub
2. **No Shared State**: `.md` files exist but aren't consumed as "global context"
3. **No Agent Memory**: Agents don't persist state between executions
4. **No Collaboration**: No mechanism for agents to "meet" and improve processes

## Proposed Architecture

### 1. Event-Driven Flow

```
┌─────────────────────────────────────────────────────────────┐
│                        Pub/Sub Topics                       │
├─────────────────────────────────────────────────────────────┤
│  • git.commit.v1          → New commit detected             │
│  • proposal.created.v1    → Spec Agent creates proposal     │
│  • proposal.approved.v1   → User approves proposal          │
│  • proposal.rejected.v1   → User rejects proposal           │
│  • strategy.updated.v1    → Strategy Agent updates plan     │
│  • milestone.completed.v1 → Milestone reached               │
│  • context.updated.v1     → Global context changed          │
│  • retrospective.trigger.v1 → Time for agent meeting        │
└─────────────────────────────────────────────────────────────┘
```

### 2. Global Context Store (Firestore)

**Collection: `workspaces/{workspace_id}/context`**

```javascript
{
  workspace_id: "contextpilot",
  last_updated: "2025-10-15T11:30:59Z",
  
  // Global project state
  project: {
    name: "ContextPilot",
    goal: "Launch before hackathon",
    status: "in_progress",
    health_score: 0.85
  },
  
  // Agent states (persistent memory)
  agents: {
    spec: {
      last_run: "2025-10-15T11:28:38Z",
      issues_found: 2,
      proposals_created: 4,
      approval_rate: 0.75,
      memory: {
        known_issues: ["README.md missing", "ARCHITECTURE.md outdated"],
        patterns_detected: ["docs_drift", "missing_tests"]
      }
    },
    strategy: {
      last_run: "2025-10-15T10:00:00Z",
      current_phase: "implementation",
      blockers: [],
      memory: {
        past_decisions: [...],
        learned_patterns: [...]
      }
    },
    git: {
      commits_made: 156,
      auto_commits: 12,
      last_commit: "d6145978...",
      memory: {
        commit_patterns: ["feat", "fix", "docs"],
        frequent_files: ["server.py", "extension.ts"]
      }
    }
  },
  
  // Artifacts (references to .md files)
  artifacts: {
    context_md: {
      path: "context.md",
      last_updated: "2025-10-15T11:30:59Z",
      producer: "git-agent",
      consumers: ["spec-agent", "strategy-agent", "coach-agent"]
    },
    proposals_md: {
      path: "proposals.md",
      last_updated: "2025-10-15T11:28:38Z",
      producer: "spec-agent",
      consumers: ["git-agent", "user"]
    },
    milestones_md: {
      path: "milestones.md",
      producer: "strategy-agent",
      consumers: ["coach-agent", "user"]
    }
  },
  
  // Retrospective data
  retrospectives: [
    {
      date: "2025-10-14T18:00:00Z",
      participants: ["spec", "strategy", "git", "coach"],
      insights: [
        "Approval rate dropped to 60% - proposals too aggressive",
        "Git Agent creating too many micro-commits",
        "Missing integration tests"
      ],
      action_items: [
        {
          agent: "spec",
          action: "Be more conservative with proposals",
          status: "in_progress"
        }
      ]
    }
  ]
}
```

### 3. Agent Base Class with State

```python
# back-end/app/agents/base_agent.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import json
from datetime import datetime
from google.cloud import firestore

class BaseAgent(ABC):
    """Base class for all agents with persistent state and event handling"""
    
    def __init__(self, workspace_id: str, agent_id: str):
        self.workspace_id = workspace_id
        self.agent_id = agent_id
        self.db = firestore.Client()
        self.state = self._load_state()
        self.event_bus = get_event_bus()
        
    def _load_state(self) -> Dict[str, Any]:
        """Load agent state from Firestore"""
        doc_ref = self.db.collection('workspaces').document(self.workspace_id)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            return data.get('agents', {}).get(self.agent_id, {})
        return {}
    
    def _save_state(self):
        """Persist agent state to Firestore"""
        doc_ref = self.db.collection('workspaces').document(self.workspace_id)
        doc_ref.set({
            'agents': {
                self.agent_id: {
                    **self.state,
                    'last_updated': datetime.utcnow().isoformat()
                }
            }
        }, merge=True)
    
    def remember(self, key: str, value: Any):
        """Store something in agent memory"""
        if 'memory' not in self.state:
            self.state['memory'] = {}
        self.state['memory'][key] = value
        self._save_state()
    
    def recall(self, key: str, default=None):
        """Retrieve from agent memory"""
        return self.state.get('memory', {}).get(key, default)
    
    def publish_event(self, event_type: str, data: Dict):
        """Publish event to Pub/Sub"""
        self.event_bus.publish(
            topic=f"{self.agent_id}-events",
            event_type=event_type,
            source=self.agent_id,
            data=data
        )
    
    @abstractmethod
    async def handle_event(self, event_type: str, data: Dict):
        """Handle incoming events - must be implemented by subclasses"""
        pass
    
    def get_global_context(self) -> Dict:
        """Read global workspace context"""
        doc_ref = self.db.collection('workspaces').document(self.workspace_id)
        doc = doc_ref.get()
        return doc.to_dict() if doc.exists else {}
    
    def update_global_context(self, updates: Dict):
        """Update global workspace context"""
        doc_ref = self.db.collection('workspaces').document(self.workspace_id)
        doc_ref.set(updates, merge=True)
        
        # Publish event so other agents know context changed
        self.publish_event('context.updated.v1', updates)
```

### 4. Spec Agent with State (Example)

```python
# back-end/app/agents/spec_agent.py

class SpecAgent(BaseAgent):
    def __init__(self, workspace_id: str):
        super().__init__(workspace_id, 'spec')
        
        # Subscribe to events
        self.event_bus.subscribe('git.commit.v1', self.handle_event)
        self.event_bus.subscribe('proposal.approved.v1', self.handle_event)
        self.event_bus.subscribe('proposal.rejected.v1', self.handle_event)
    
    async def handle_event(self, event_type: str, data: Dict):
        """React to events"""
        if event_type == 'git.commit.v1':
            # New commit → analyze for issues
            await self.analyze_commit(data['commit_hash'])
            
        elif event_type == 'proposal.approved.v1':
            # Track approval rate
            self.remember('approvals', self.recall('approvals', 0) + 1)
            
        elif event_type == 'proposal.rejected.v1':
            # Learn from rejection
            reason = data.get('reason', 'unknown')
            rejections = self.recall('rejection_reasons', [])
            rejections.append(reason)
            self.remember('rejection_reasons', rejections)
    
    async def create_proposal(self, issue: Dict) -> str:
        """Create proposal and publish event"""
        proposal_id = self._generate_proposal(issue)
        
        # Publish event instead of calling Git Agent directly
        self.publish_event('proposal.created.v1', {
            'proposal_id': proposal_id,
            'issue': issue
        })
        
        return proposal_id
```

### 5. Strategy Agent as Consumer

```python
# back-end/app/agents/strategy_agent.py

class StrategyAgent(BaseAgent):
    def __init__(self, workspace_id: str):
        super().__init__(workspace_id, 'strategy')
        
        # Subscribe to multiple events
        self.event_bus.subscribe('proposal.created.v1', self.handle_event)
        self.event_bus.subscribe('milestone.completed.v1', self.handle_event)
        self.event_bus.subscribe('context.updated.v1', self.handle_event)
    
    async def handle_event(self, event_type: str, data: Dict):
        if event_type == 'proposal.created.v1':
            # Analyze if proposal aligns with strategy
            await self.validate_proposal_alignment(data['proposal_id'])
            
        elif event_type == 'milestone.completed.v1':
            # Update strategy based on progress
            await self.adjust_strategy()
    
    def consume_artifacts(self) -> Dict:
        """Read all .md artifacts produced by other agents"""
        context = self.get_global_context()
        artifacts = context.get('artifacts', {})
        
        consumed_data = {}
        for artifact_name, artifact_info in artifacts.items():
            # Read the actual .md file
            path = self._get_workspace_path(artifact_info['path'])
            with open(path, 'r') as f:
                consumed_data[artifact_name] = f.read()
        
        return consumed_data
    
    async def run_strategy_analysis(self):
        """Main strategy loop - consumes all artifacts"""
        # 1. Read global context
        global_ctx = self.get_global_context()
        
        # 2. Consume artifacts from other agents
        artifacts = self.consume_artifacts()
        
        # 3. Analyze
        analysis = self._analyze_project_health(global_ctx, artifacts)
        
        # 4. Update strategy
        self.update_global_context({
            'strategy': {
                'current_phase': analysis['recommended_phase'],
                'blockers': analysis['blockers'],
                'recommendations': analysis['recommendations']
            }
        })
        
        # 5. Publish event
        self.publish_event('strategy.updated.v1', analysis)
```

### 6. Retrospective Agent (New!)

```python
# back-end/app/agents/retrospective_agent.py

class RetrospectiveAgent(BaseAgent):
    """Facilitates agent 'meetings' to improve processes"""
    
    def __init__(self, workspace_id: str):
        super().__init__(workspace_id, 'retrospective')
    
    async def run_retrospective(self):
        """Gather all agents for a 'meeting'"""
        
        # 1. Gather data from all agents
        global_ctx = self.get_global_context()
        agents_data = global_ctx.get('agents', {})
        
        # 2. Analyze patterns
        insights = []
        
        # Check Spec Agent approval rate
        spec_state = agents_data.get('spec', {})
        approval_rate = spec_state.get('approval_rate', 1.0)
        if approval_rate < 0.7:
            insights.append({
                'severity': 'warning',
                'agent': 'spec',
                'issue': f'Low approval rate: {approval_rate:.0%}',
                'recommendation': 'Be more conservative with proposals'
            })
        
        # Check Git Agent commit frequency
        git_state = agents_data.get('git', {})
        commits_per_day = git_state.get('commits_per_day', 0)
        if commits_per_day > 50:
            insights.append({
                'severity': 'info',
                'agent': 'git',
                'issue': 'High commit frequency',
                'recommendation': 'Consider batching smaller changes'
            })
        
        # 3. Create action items
        action_items = []
        for insight in insights:
            action_items.append({
                'agent': insight['agent'],
                'action': insight['recommendation'],
                'status': 'pending',
                'created_at': datetime.utcnow().isoformat()
            })
        
        # 4. Store retrospective
        retrospective = {
            'date': datetime.utcnow().isoformat(),
            'participants': list(agents_data.keys()),
            'insights': insights,
            'action_items': action_items
        }
        
        # Update global context
        retros = global_ctx.get('retrospectives', [])
        retros.append(retrospective)
        self.update_global_context({'retrospectives': retros})
        
        # 5. Notify agents of action items
        for item in action_items:
            self.publish_event('retrospective.action_item.v1', item)
        
        return retrospective
```

### 7. Event Bus Integration

```python
# back-end/app/services/event_bus.py

from google.cloud import pubsub_v1
from typing import Callable, Dict
import json

class EventBus:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.publisher = pubsub_v1.PublisherClient()
        self.subscriber = pubsub_v1.SubscriberClient()
        self.subscriptions = {}
    
    def publish(self, topic: str, event_type: str, source: str, data: Dict):
        """Publish event to Pub/Sub"""
        topic_path = self.publisher.topic_path(self.project_id, topic)
        
        message = {
            'event_type': event_type,
            'source': source,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        future = self.publisher.publish(
            topic_path,
            json.dumps(message).encode('utf-8')
        )
        return future.result()
    
    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to event type"""
        if event_type not in self.subscriptions:
            self.subscriptions[event_type] = []
        self.subscriptions[event_type].append(handler)
    
    def start_listening(self, subscription_name: str):
        """Start listening to Pub/Sub subscription"""
        subscription_path = self.subscriber.subscription_path(
            self.project_id, subscription_name
        )
        
        def callback(message):
            data = json.loads(message.data.decode('utf-8'))
            event_type = data['event_type']
            
            # Call all registered handlers
            if event_type in self.subscriptions:
                for handler in self.subscriptions[event_type]:
                    handler(event_type, data['data'])
            
            message.ack()
        
        future = self.subscriber.subscribe(subscription_path, callback)
        return future
```

## Implementation Plan

### Phase 1: State Management (Week 1)
- [ ] Implement `BaseAgent` class
- [ ] Migrate existing agents to inherit from `BaseAgent`
- [ ] Set up Firestore collections for workspace context
- [ ] Test state persistence

### Phase 2: Event Bus (Week 2)
- [ ] Set up GCP Pub/Sub topics
- [ ] Implement `EventBus` service
- [ ] Refactor agents to publish events instead of direct calls
- [ ] Test event flow: Spec → Git Agent

### Phase 3: Artifact Consumption (Week 3)
- [ ] Map all `.md` files as artifacts in global context
- [ ] Implement Strategy Agent as consumer
- [ ] Test artifact flow: Spec produces → Strategy consumes

### Phase 4: Retrospectives (Week 4)
- [ ] Implement `RetrospectiveAgent`
- [ ] Schedule periodic retrospectives (daily/weekly)
- [ ] Build dashboard to visualize insights
- [ ] Test full agent collaboration loop

## Benefits

1. **Decoupling**: Agents don't call each other directly
2. **Scalability**: Easy to add new agents that react to events
3. **Observability**: All events logged in Pub/Sub
4. **State Persistence**: Agents remember context between runs
5. **Collaboration**: Agents can "meet" and improve processes
6. **Artifact Tracking**: Clear producer/consumer relationships

## Next Steps

1. Start with Phase 1 (State Management)
2. Keep current HTTP endpoints for backward compatibility
3. Gradually migrate to event-driven architecture
4. Test with ContextPilot workspace (dogfooding)

---

**Questions for Discussion:**
- Should retrospectives be triggered by time (daily) or events (milestone completed)?
- How do we handle conflicts when multiple agents update global context?
- Should we use Firestore or a simpler JSON file for state during development?

