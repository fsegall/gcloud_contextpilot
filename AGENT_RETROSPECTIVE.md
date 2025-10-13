# 🤝 Agent Retrospective System

## Philosophy

**"Agents learn from experience, improve processes, but never decide for developers."**

Agents podem se reunir para:
- ✅ Analisar sucessos e falhas
- ✅ Compartilhar padrões detectados
- ✅ Ajustar seus próprios prompts
- ✅ **Sugerir** melhorias de processo/arquitetura (via Coach)
- ❌ **NUNCA** tomar decisões sem aprovação humana

---

## 🎯 Meta-Agent: Coordination Agent

### Papel

O **Coordination Agent** (ou Meta-Agent) facilita "reuniões" periódicas entre agentes para:
- Analisar métricas de performance
- Compartilhar insights cross-domain
- Detectar patterns recorrentes
- Propor ajustes nos próprios processos

**Importante:** Isso é para **melhorar os agentes**, não para tomar decisões do projeto.

### Frequência

**Daily Sync (5 min):**
- Quick status de cada agente
- Bloqueios entre agentes
- Event queue health

**Weekly Retrospective (30 min):**
- Análise de métricas da semana
- Patterns identificados
- Sugestões de melhoria
- Ajustes de prompts

**Monthly Review (1 hora):**
- Deep dive em falhas
- Success stories
- Roadmap de evolução dos agentes
- A/B test results

---

## 🔄 Agent Meeting Structure

### Weekly Retrospective Format

```json
{
  "meeting_id": "retro_2025_w42",
  "date": "2025-10-18T10:00:00Z",
  "type": "weekly_retrospective",
  "duration_minutes": 30,
  
  "participants": [
    "context-agent",
    "spec-agent", 
    "strategy-agent",
    "milestone-agent",
    "git-agent",
    "coach-agent"
  ],
  
  "agenda": [
    {
      "section": "metrics_review",
      "duration_minutes": 10,
      "data": {
        "context_agent": {
          "events_processed": 1250,
          "avg_latency_ms": 1800,
          "errors": 3,
          "slo_met": true
        },
        "spec_agent": {
          "docs_updated": 42,
          "proposals_created": 15,
          "approval_rate": 0.73,
          "slo_met": true
        },
        "strategy_agent": {
          "insights_generated": 28,
          "acceptance_rate": 0.65,
          "false_positives": 4,
          "slo_met": true
        }
      }
    },
    
    {
      "section": "what_went_well",
      "duration_minutes": 5,
      "items": [
        {
          "agent": "coach-agent",
          "observation": "Nudge completion rate up to 78% (was 65%)",
          "reason": "Shorter action items (avg 18min vs 25min)"
        },
        {
          "agent": "spec-agent",
          "observation": "Doc approval rate increased to 73%",
          "reason": "Better preview formatting in proposals"
        }
      ]
    },
    
    {
      "section": "what_to_improve",
      "duration_minutes": 8,
      "items": [
        {
          "agent": "strategy-agent",
          "issue": "False positive rate too high (14%)",
          "root_cause": "Not considering legacy code patterns",
          "proposed_fix": "Add context about legacy/ folder to prompt"
        },
        {
          "agent": "git-agent",
          "issue": "Merge conflicts on 3 proposals",
          "root_cause": "Not checking branch freshness",
          "proposed_fix": "Rebase before applying proposal"
        }
      ]
    },
    
    {
      "section": "cross_agent_insights",
      "duration_minutes": 5,
      "items": [
        {
          "pattern": "High-impact commits correlate with low doc coverage",
          "agents_involved": ["context-agent", "spec-agent"],
          "suggestion": "Spec should prioritize docs for high-impact changes",
          "action": "Update Spec Agent prompt to check impact_score"
        }
      ]
    },
    
    {
      "section": "action_items",
      "duration_minutes": 2,
      "items": [
        {
          "action": "Update Strategy Agent prompt to exclude legacy/",
          "owner": "coordination-agent",
          "deadline": "2025-10-20"
        },
        {
          "action": "Add rebase check to Git Agent",
          "owner": "coordination-agent", 
          "deadline": "2025-10-19"
        },
        {
          "action": "Monitor Spec approval rate (target: >75%)",
          "owner": "coordination-agent",
          "deadline": "ongoing"
        }
      ]
    }
  ],
  
  "outputs": {
    "prompt_updates": [
      {
        "agent": "strategy-agent",
        "change": "Add legacy code awareness",
        "expected_improvement": "Reduce false positives by 40%"
      }
    ],
    "process_improvements": [
      {
        "process": "proposal_application",
        "change": "Add git rebase before apply",
        "expected_improvement": "Reduce merge conflicts by 80%"
      }
    ]
  }
}
```

---

## 🧠 Learning Mechanisms

### 1. Metrics-Driven Learning

```python
# app/agents/coordination.py

class CoordinationAgent:
    async def analyze_agent_performance(self):
        """Analyze metrics from all agents and identify improvements."""
        
        # Fetch metrics from Firestore
        metrics = await self.fetch_weekly_metrics()
        
        # Analyze with Gemini
        prompt = f"""
        Analyze these agent performance metrics and identify:
        1. Which agents are underperforming (vs SLOs)
        2. Patterns in failures
        3. Opportunities for cross-agent coordination
        4. Suggested improvements
        
        Metrics:
        {json.dumps(metrics, indent=2)}
        
        Constraints:
        - Suggestions must be actionable (code/prompt changes)
        - Focus on system improvements, not feature requests
        - Respect developer control principles
        """
        
        analysis = await gemini.generate(prompt)
        
        return analysis
```

### 2. Pattern Detection

```python
async def detect_patterns(self):
    """Detect recurring patterns across agent interactions."""
    
    # Query BigQuery for event patterns
    query = """
    SELECT 
      source_agent,
      event_type,
      outcome,
      COUNT(*) as frequency
    FROM agent_events
    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
    GROUP BY source_agent, event_type, outcome
    HAVING frequency > 10
    ORDER BY frequency DESC
    """
    
    patterns = await bigquery.execute(query)
    
    # Identify interesting patterns
    insights = []
    
    for pattern in patterns:
        if pattern.outcome == "rejected" and pattern.frequency > 20:
            insights.append({
                "type": "high_rejection",
                "agent": pattern.source_agent,
                "event": pattern.event_type,
                "suggestion": "Review prompt or add context filters"
            })
    
    return insights
```

### 3. Prompt Evolution

```python
async def evolve_prompts(self):
    """
    A/B test prompt variations and evolve based on results.
    
    NOT for making decisions, but for improving agent quality.
    """
    
    # Example: Strategy Agent has low acceptance rate
    current_acceptance = 0.58  # Below 0.60 target
    
    # Try variation
    prompt_variants = {
        "current": "Analyze code and suggest improvements",
        "variant_a": "Analyze code, prioritize quick wins (<1h)",
        "variant_b": "Analyze code, focus on security and maintainability"
    }
    
    # A/B test for 3 days
    results = await ab_test_prompts(
        agent="strategy-agent",
        variants=prompt_variants,
        duration_days=3,
        metric="acceptance_rate"
    )
    
    # Pick winner
    if results["variant_a"].acceptance_rate > 0.70:
        await update_agent_prompt("strategy-agent", "variant_a")
        log_improvement("Strategy Agent prompt updated, acceptance +20%")
```

---

## 📊 Retrospective Storage

### Firestore Collections

```
agent_retrospectives/
  └── retro_2025_w42/
      ├── summary
      ├── metrics
      ├── improvements_proposed
      └── improvements_applied

agent_performance/
  └── strategy-agent/
      ├── weekly_stats
      ├── prompt_versions
      └── ab_test_results
```

### BigQuery Tables

```sql
-- agent_events: All events for analysis
CREATE TABLE agent_events (
  event_id STRING,
  timestamp TIMESTAMP,
  source_agent STRING,
  event_type STRING,
  outcome STRING,  -- success, rejected, error
  latency_ms INT64,
  metadata JSON
);

-- agent_improvements: Track improvements over time
CREATE TABLE agent_improvements (
  improvement_id STRING,
  timestamp TIMESTAMP,
  agent STRING,
  type STRING,  -- prompt_update, process_change, etc
  description STRING,
  expected_impact STRING,
  actual_impact JSON,
  status STRING  -- proposed, applied, validated
);
```

---

## 🎯 Meeting Triggers

### Automatic Triggers

```python
# Daily sync if:
- Any agent SLO breached
- Error rate > 5%
- Event queue backed up (>100 messages)

# Weekly retro:
- Every Friday 10 AM (Cloud Scheduler)

# Emergency meeting if:
- Multiple agent failures
- Critical bug detected
- Security issue found
```

---

## 🔐 Safety Rules

### What Coordination Agent CAN Do

✅ **Analyze metrics and patterns**  
✅ **Suggest prompt improvements**  
✅ **A/B test prompt variations**  
✅ **Update agent configuration**  
✅ **Flag coordination issues**  
✅ **Generate retrospective reports**

### What Coordination Agent CANNOT Do

❌ **Change project code**  
❌ **Approve/reject proposals**  
❌ **Make architectural decisions**  
❌ **Change developer workflows**  
❌ **Modify SLOs without human approval**

---

## 🎬 Example: Learning from Failure

### Scenario

Strategy Agent suggests "Add rate limiting" but gets rejected 8 times in a row.

### Coordination Agent Analysis

```json
{
  "pattern_detected": {
    "agent": "strategy-agent",
    "suggestion": "Add rate limiting",
    "rejection_count": 8,
    "rejection_reasons": [
      "Already implemented",
      "Not a priority",
      "Wrong approach suggested"
    ]
  },
  
  "root_cause_analysis": {
    "issue": "Strategy Agent not aware of existing rate limiting",
    "why": "Not scanning middleware folder",
    "fix": "Update Context Agent to index middleware/"
  },
  
  "proposed_improvements": [
    {
      "target": "context-agent",
      "change": "Add middleware/ to indexed paths",
      "expected": "Strategy won't suggest existing features"
    },
    {
      "target": "strategy-agent",
      "change": "Check existing implementation before suggesting",
      "expected": "False positive rate -50%"
    }
  ],
  
  "status": "awaiting_human_approval"
}
```

### Human Review

Dev reviews the analysis and approves:
```bash
contextpilot coordination approve-improvement improve_001

# Coordination Agent applies changes:
# - Updates Context Agent config
# - Updates Strategy Agent prompt  
# - Monitors for improvement
```

---

**Status**: 📐 **Architecture defined**  
**Next**: Implement Coordination Agent + retrospective system


