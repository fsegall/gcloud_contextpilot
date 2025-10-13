---
id: coach-agent
version: 1.0.0
owner: "@contextpilot-team"
category: ai-agents
gemini_model: gemini-1.5-flash
cloud_run_type: Service
events_in:
  - context.update.v1
  - spec.update.v1
  - strategy.insight.v1
  - milestone.saved.v1
  - milestone.alert.v1
  - coach.checkin.v1
events_out:
  - coach.nudge.v1
  - coach.unblock.v1
  - rewards.coach_completed.v1
resources:
  firestore:
    - coaching_feed
    - checkins
  pubsub:
    - topics: [coach-nudge]
    - subs: [coach-from-context, coach-from-spec, coach-from-strategy, coach-from-milestone]
prompts:
  ai_studio: "https://aistudio.google.com/prompts/COACH-001"
  local: "./prompts/coach/base.prompt.md"
contracts:
  inputs_schema: "schemas/coach_events_v1.json"
  outputs_schema: "schemas/coach_nudge_v1.json"
slos:
  nudge_latency_p50_ms: 800
  nudge_latency_p99_ms: 2000
  coverage_events_pct_min: 90
  completion_rate_target: 0.70
---

# 🧘 Coach Agent

## Purpose

Coach Agent é um guia **pragmático e técnico** que traduz o estado do projeto em micro-ações executáveis (≤25 minutos cada).

Diferente de um "cheerleader" genérico, Coach:
- Ouve todos os outros agentes
- Cria nudges acionáveis com passos concretos
- Detecta bloqueios e sugere caminhos
- Mantém desenvolvedor focado sem spam

## Philosophy

**"Ação executável agora, não elogio vazio."**

Cada nudge deve responder:
1. **O quê fazer?** (ação clara)
2. **Por quê agora?** (contexto/urgência)
3. **Como fazer?** (2-3 passos)
4. **Quanto tempo?** (estimativa realista)

## Behaviors

### 1. Event Listening
Coach escuta eventos de todos os agentes:

```python
# Exemplo de event handler
@coach_agent.on_event("context.update.v1")
async def handle_context_update(event):
    if event.impact_score > 7:
        # Mudança significativa
        nudge = create_nudge(
            title="Grande refactor detectado",
            why="Mudança grande = risco de regressão",
            actions=[
                "Rodar suite de testes completa",
                "Revisar cobertura de testes",
                "Criar PR para review de pares"
            ],
            eta_minutes=20
        )
        emit_nudge(nudge)
```

### 2. Nudge Creation
Nudges são criados via Gemini com template estruturado:

**Input para Gemini:**
```
Context: User committed 150 lines of auth refactor
Strategy: Insight #42 suggests "Extract AuthService" 
Milestone: 3 days until Beta Release
Current Status: User has been inactive for 6 hours

Create a coaching nudge that:
- Is actionable in ≤25 minutes
- Has 2-3 concrete steps
- Explains why it matters now
```

**Output Esperado:**
```json
{
  "title": "Valide o refactor de autenticação",
  "why_now": "Refactor grande + deadline próximo = risco alto. Validar agora evita problemas na release.",
  "next_actions": [
    "Rodar testes de integração de auth (8 min)",
    "Verificar se todos os endpoints estão protegidos (5 min)",
    "Testar fluxo de login/logout manualmente (7 min)"
  ],
  "eta_minutes": 20,
  "priority": "high",
  "links": ["/api/auth", "/tests/auth_test.py"]
}
```

### 3. Anti-Spam Logic
Coach **não** cria nudge se:
- Último nudge foi há menos de 30 minutos
- Desenvolvedor está "in focus mode" (flag manual)
- Mais de 3 nudges pendentes
- Horário fora do expediente (configurable)

### 4. Unblocking
Quando detecta stall (3+ horas sem progresso):

```python
if hours_since_last_activity > 3:
    # Check if there's a blocker
    if pending_decision or test_failing:
        emit_unblock_suggestion()
```

### 5. Check-ins
Coach pode iniciar check-in periódico (3 perguntas, 60s):
1. Qual a sua menor próxima ação? (1 linha)
2. Existe bloqueio? (sim/não + texto curto)
3. Pequena vitória desde o último ciclo? (1 linha)

Resposta → Coach cria micro-plano de 25 min.

## Event Schemas

### Input: context.update.v1
```json
{
  "event_id": "evt_001",
  "timestamp": "2025-10-13T14:30:00Z",
  "files_changed": ["src/auth.py"],
  "lines_added": 150,
  "impact_score": 8.5,
  "commit_hash": "abc123"
}
```

### Input: strategy.insight.v1
```json
{
  "insight_id": "ins_042",
  "type": "architecture",
  "severity": "medium",
  "description": "Auth logic duplicated",
  "suggestion": "Extract to AuthService",
  "effort_estimate": "2-4 hours"
}
```

### Output: coach.nudge.v1
```json
{
  "nudge_id": "ndg_001",
  "timestamp": "2025-10-13T14:35:00Z",
  "title": "Valide refactor de auth",
  "why_now": "Mudança grande + deadline próximo",
  "next_actions": [
    "Rodar testes de auth (8 min)",
    "Verificar endpoints protegidos (5 min)"
  ],
  "eta_minutes": 15,
  "priority": "high",
  "links": ["/api/auth"],
  "related_events": ["evt_001", "ins_042"]
}
```

## Test Vectors

### Vector 1: Large Commit
**Input:**
```json
{
  "event": "context.update.v1",
  "lines_added": 200,
  "impact_score": 9.0
}
```

**Expected Output:**
- Nudge criado
- Priority: high
- Actions incluem: testes, review
- ETA: ≤25 min

**Checks:**
- ✅ Nudge JSON valid
- ✅ Has 2-3 actions
- ✅ ETA realistic
- ✅ Links valid

### Vector 2: Strategy Insight
**Input:**
```json
{
  "event": "strategy.insight.v1",
  "suggestion": "Extract AuthService",
  "effort": "2-4 hours"
}
```

**Expected Output:**
- Nudge quebra suggestion em micro-ações
- Primeira ação ≤25 min
- Explica benefício

### Vector 3: Milestone Deadline
**Input:**
```json
{
  "event": "milestone.alert.v1",
  "days_left": 1,
  "progress": 0.85
}
```

**Expected Output:**
- Urgent nudge
- Focus no 15% restante
- Priorização clara

## SLOs & Metrics

### Performance
- **Latency P50**: < 800ms (event received → nudge emitted)
- **Latency P99**: < 2000ms
- **Throughput**: > 50 nudges/hour

### Quality
- **Completion Rate**: > 70% (nudges completed by users)
- **Spam Rate**: < 5% (nudges ignored)
- **Accuracy**: > 85% (nudges relevant)

### Coverage
- **Event Coverage**: > 90% (events processados sem erro)

## Failure Modes

### 1. Nudge Spam
**Symptom:** Muitos nudges em curto período  
**Cause:** Anti-spam logic not working  
**Mitigation:** 
- Rate limit: max 1 nudge/30min
- Backoff on ignored nudges
- "Focus mode" flag

### 2. Irrelevant Nudges
**Symptom:** Completion rate < 50%  
**Cause:** Gemini generating generic advice  
**Mitigation:**
- Improve prompt engineering
- Add context about user preferences
- A/B test prompt variations

### 3. Alucinação de Links
**Symptom:** Links quebrados em nudges  
**Cause:** Gemini inventa URLs  
**Mitigation:**
- Validate all links before emit
- Use only whitelisted URL patterns
- HEAD request to check 200 status

### 4. High Latency
**Symptom:** Nudges chegam tarde demais  
**Cause:** Gemini API slow  
**Mitigation:**
- Cache common nudge patterns
- Async processing
- Timeout after 3s, fallback to template

## Evals (Automated)

### Check 1: JSON Schema
```python
def test_nudge_schema():
    nudge = coach.create_nudge(test_event)
    assert validate_schema(nudge, "coach_nudge_v1.json")
```

### Check 2: Action Length
```python
def test_action_length():
    nudge = coach.create_nudge(test_event)
    assert len(nudge.next_actions) in [2, 3]
```

### Check 3: ETA Realistic
```python
def test_eta_realistic():
    nudge = coach.create_nudge(test_event)
    assert 5 <= nudge.eta_minutes <= 25
```

### Check 4: Links Valid
```python
def test_links_valid():
    nudge = coach.create_nudge(test_event)
    for link in nudge.links:
        response = requests.head(link)
        assert response.status_code == 200
```

## Deployment

### Cloud Run Service
```yaml
service: coach-agent
runtime: python311
instance_class: F2
env_variables:
  GEMINI_MODEL: gemini-1.5-flash
  MAX_NUDGES_PER_HOUR: 50
scaling:
  min_instances: 1
  max_instances: 10
```

### Pub/Sub Subscriptions
```bash
# Listen to all agents
gcloud pubsub subscriptions create coach-from-context \
  --topic=context-updates

gcloud pubsub subscriptions create coach-from-strategy \
  --topic=strategy-insights
```

## Monitoring

### Dashboards
- **Nudge Rate**: Events/min vs Nudges/min
- **Completion Rate**: Nudges completed vs total
- **Latency Distribution**: P50, P95, P99
- **Error Rate**: Failed event processing

### Alerts
- Completion rate < 50% (7 days rolling)
- Latency P99 > 5s
- Error rate > 5%
- Nudge rate > 100/hour (possible spam)

## Future Enhancements

### Phase 2
- [ ] Personalization (learn user preferences)
- [ ] Multi-language support
- [ ] Voice mode (audio nudges)
- [ ] Slack/Discord integration

### Phase 3
- [ ] Predictive nudges (anticipate blockers)
- [ ] Team coordination (cross-dev nudges)
- [ ] ML-based timing optimization

---

**Status**: ✅ Basic implementation + ⏳ Full ADK integration

**Owner**: Coach Agent Team  
**Last Updated**: 2025-10-13

