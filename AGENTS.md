# 🤖 ContextPilot - Multi-Agent System

## Overview

ContextPilot é um sistema **multi-agente coordenado** onde 5 agentes especializados colaboram para gerenciar contexto de projetos e recompensar desenvolvedores.

Cada agente tem:
- **Papel específico** (domain expertise)
- **Eventos de entrada** (o que ele "ouve")
- **Eventos de saída** (o que ele "fala")
- **Storage próprio** (onde persiste dados)
- **Contrato executável** (AGENT.*.md com SLOs)

---

## Arquitetura de Comunicação

```
┌─────────────────────────────────────────────────────────────┐
│                    Google Pub/Sub Event Bus                  │
│  (context.update, spec.update, strategy.insight, etc)       │
└────┬────────┬────────┬────────┬────────┬────────────────────┘
     │        │        │        │        │
     ▼        ▼        ▼        ▼        ▼
┌─────────┐ ┌──────┐ ┌──────┐ ┌─────────┐ ┌──────────┐
│ Context │ │ Spec │ │Strategy│Milestone│ │  Coach   │
│  Agent  │ │Agent │ │ Agent  │  Agent  │ │  Agent   │
└────┬────┘ └──┬───┘ └───┬───┘ └────┬───┘ └────┬─────┘
     │         │         │          │          │
     └─────────┴─────────┴──────────┴──────────┘
                        │
                   ┌────▼─────┐
                   │ Firestore│
                   │  Storage │
                   └──────────┘
```

---

## 🎯 Agente 1: Context Agent

### Papel
Indexa e interpreta o estado atual do projeto (arquivos, commits, issues).

### Responsabilidades
- Monitorar mudanças no repositório Git
- Detectar deltas significativos (novos arquivos, refactors, etc)
- Construir grafo semântico do código
- Emitir eventos quando o contexto muda

### Eventos

**Input:**
- Git hooks (post-commit, post-merge)
- File system watchers
- Manual triggers via API

**Output:**
- `context.update.v1` - Mudança detectada
  ```json
  {
    "files_changed": ["src/app.py", "README.md"],
    "lines_added": 150,
    "lines_removed": 30,
    "commit_hash": "abc123",
    "impact_score": 7.5
  }
  ```
- `context.delta.v1` - Delta semântico
  ```json
  {
    "type": "refactor|feature|bugfix",
    "scope": ["authentication", "api"],
    "description": "Added JWT authentication"
  }
  ```

### Storage
- Firestore: `context_snapshots` collection
- Cloud Storage: Full repo snapshots (weekly)

### Cloud Run Type
**Job** (triggered by Pub/Sub or Cloud Scheduler)

### Recompensas
- Detecta ações → chama `/rewards/track`
- Tipos: `cli_action`, `doc_update`, `code_review`

### Status Atual
✅ **Implementado parcialmente** como `git_context_manager.py`  
⏳ Precisa: Pub/Sub integration, semantic analysis

---

## 📄 Agente 2: Spec Agent

### Papel
Gera e atualiza especificações técnicas e documentação Markdown.

**⚠️ IMPORTANTE:** Spec Agent **sugere** mudanças em docs via Change Proposals. Não modifica arquivos diretamente (exceto markdown em `docs/`).

### Responsabilidades
- Criar/atualizar README, ARCHITECTURE, API docs
- Converter design notes em specs estruturadas
- Validar documentação vs código real
- Sugerir melhorias de clareza
- **Gerar Change Proposals** para atualizações de docs importantes

### Eventos

**Input:**
- `context.delta.v1` - Código mudou, docs precisam atualizar
- `spec.request.v1` - Pedido manual de geração
- `coach.suggest.doc.v1` - Coach detectou doc defasada

**Output:**
- `spec.update.v1` - Documento atualizado
  ```json
  {
    "file": "README.md",
    "section": "Architecture",
    "action": "updated|created",
    "preview": "Updated architecture diagram...",
    "confidence": 0.9
  }
  ```
- `spec.validation.v1` - Validação de consistência
  ```json
  {
    "mismatches": ["API endpoint missing docs"],
    "suggestions": ["Add example for /rewards/track"]
  }
  ```

**Input (para recompensas):**
- `rewards.spec_commit.v1` - Quando Spec atualiza docs

### Storage
- Git repository (docs como código)
- Firestore: `spec_history` (metadata)

### Cloud Run Type
**Service** (HTTP endpoint + Pub/Sub subscriber)

### Recompensas
Quando Spec atualiza documentação:
- `spec_commit`: +5 CPT (creditado ao usuário que triggou)
- `doc_update`: +8 CPT (se mudanças significativas)

### Status Atual
❌ **Não implementado**  
⏳ Precisa: Gemini integration, template system, Git automation

---

## 🧠 Agente 3: Strategy Agent

### Papel
Analisa dependências, detecta code smells, sugere melhorias táticas.

**🎯 CORE PRINCIPLE:** Strategy Agent **nunca modifica código**. Apenas analisa e cria Change Proposals.

### Responsabilidades
- Analisar arquitetura (patterns, anti-patterns)
- Detectar débito técnico
- **Criar Change Proposals** para refactorings
- Identificar security issues
- Mapear impacto de mudanças propostas (blast radius)

### Eventos

**Input:**
- `context.delta.v1` - Código mudou, análise necessária
- `strategy.analyze.v1` - Análise manual solicitada
- `milestone.blocked.v1` - Milestone travado, precisa insights

**Output:**
- `strategy.insight.v1` - Insight estratégico
  ```json
  {
    "type": "architecture|security|performance|maintainability",
    "severity": "low|medium|high|critical",
    "description": "Auth logic duplicated across 3 files",
    "suggestion": "Extract to AuthService",
    "effort_estimate": "2-4 hours",
    "impact": "Reduces maintenance burden by 40%"
  }
  ```
- `strategy.options.v1` - Quando há dilema técnico
  ```json
  {
    "question": "How to handle rate limiting?",
    "options": [
      {"approach": "Redis", "pros": [...], "cons": [...]},
      {"approach": "In-memory", "pros": [...], "cons": [...]}
    ]
  }
  ```

### Storage
- BigQuery: `strategy_analysis` table (para analytics)
- Firestore: `insights` collection (active insights)

### Cloud Run Type
**Job** (execução periódica ou on-demand)

### Recompensas
Quando desenvolvedor implementa sugestão:
- `strategy_accepted`: +15 CPT
- Detectado via commit message ou manual confirmation

### Status Atual
❌ **Não implementado**  
⏳ Precisa: Static analysis tools, Gemini integration, pattern detection

---

## 🏁 Agente 4: Milestone Agent

### Papel
Rastreia milestones, cria checkpoints versionados, salva snapshots do projeto.

### Responsabilidades
- Gerenciar lifecycle de milestones
- Criar checkpoints Git + metadata
- Versionar contexto (como "save points")
- Alertar sobre deadlines próximos

### Eventos

**Input:**
- `milestone.create.v1` - Novo milestone definido
- `milestone.complete.v1` - Milestone marcado como completo
- `context.checkpoint.v1` - Pedido de checkpoint manual

**Output:**
- `milestone.saved.v1` - Checkpoint criado
  ```json
  {
    "milestone_id": "m-001",
    "name": "MVP Launch",
    "snapshot_url": "gs://bucket/snapshots/2025-10-13.tar.gz",
    "git_tag": "v0.1.0-milestone",
    "context_hash": "sha256:abc...",
    "completed": true
  }
  ```
- `milestone.alert.v1` - Deadline approaching
  ```json
  {
    "milestone_id": "m-002",
    "name": "Beta Release",
    "days_left": 3,
    "progress": 0.75
  }
  ```

### Storage
- Firestore: `milestones` collection
- Cloud Storage: Snapshots (tarball do projeto)
- Git: Tags para cada milestone

### Cloud Run Type
**Worker Pool** (processa filas de checkpoint requests)

### Recompensas
Quando milestone é completado:
- `milestone_saved`: +20 CPT
- Distribuído entre contribuidores do milestone

### Status Atual
✅ **Implementado parcialmente** em `git_context_manager.py`  
⏳ Precisa: Snapshot system, Cloud Storage integration, alerting

---

## 🌳 Agente 5: Git Agent

### Papel
Único agente autorizado a interagir com Git. Implementa git-flow, gerencia branches e rollbacks.

### Responsabilidades
- Criar/gerenciar branches (git-flow)
- Aplicar Change Proposals aprovados
- Commits semânticos bem formatados
- Sistema de rollback para todas as ações
- Proteger branches críticas (main, develop)

### Eventos

**Input:**
- `proposal.approved.v1` - Aplicar mudanças
- `milestone.created.v1` - Criar release branch
- `rollback.requested.v1` - Reverter mudanças

**Output:**
- `git.commit.v1` - Commit criado
- `git.branch.created.v1` - Branch criado
- `git.merge.v1` - Merge realizado
- `git.rollback.v1` - Rollback executado

### Storage
- Firestore: `git_history`, `branches`, `rollback_points`
- Git: Repository com git-flow structure

### Cloud Run Type
**Service** (HTTP endpoint + Pub/Sub subscriber)

### Recompensas
Quando mudanças são commitadas:
- Registra ação original que triggerou commit
- Credita dev que aprovou proposal

### Status Atual
❌ **Não implementado**  
⏳ Precisa: Git automation, rollback system, branch management

---

## 🧘 Agente 6: Coach Agent

### Papel
Guia pragmático e técnico, traduz estado dos agentes em micro-ações executáveis.

### Responsabilidades
- Ouvir TODOS os outros agentes
- Criar "nudges" acionáveis (≤25 min cada)
- Detectar bloqueios e sugerir caminhos
- Manter desenvolvedor focado e motivado

### Eventos

**Input:**
- `context.update.v1` - Mudança no projeto
- `spec.update.v1` - Docs atualizados
- `strategy.insight.v1` - Insight disponível
- `milestone.saved.v1` - Progresso registrado
- `milestone.alert.v1` - Deadline próximo
- `coach.checkin.v1` - Check-in manual do dev

**Output:**
- `coach.nudge.v1` - Micro-ação sugerida
  ```json
  {
    "title": "Valide a seção de Arquitetura",
    "why_now": "Spec Agent reorganizou; validar evita divergência com código",
    "next_actions": [
      "Abrir README e conferir fluxos de dados",
      "Criar 1 issue se notar lacuna",
      "Marcar milestone 'Spec-validated'"
    ],
    "eta_minutes": 15,
    "priority": "medium",
    "links": ["/docs/README#architecture"]
  }
  ```
- `coach.unblock.v1` - Sugestão de desbloqueio
  ```json
  {
    "blocker": "Decisão entre Redis vs In-memory",
    "suggestion": "Use Strategy options: Redis para prod, in-memory para dev",
    "next_step": "Criar PR com config toggle"
  }
  ```

### Storage
- Firestore: `coaching_feed` collection
- Firestore: `checkins` collection

### Cloud Run Type
**Service** (HTTP + Pub/Sub subscriber)

### Recompensas
Quando desenvolvedor completa nudge:
- `coach_completed`: +10 CPT
- Registrado via UI ou API

### Status Atual
✅ **Implementado básico** em `coach_agent.py`  
⏳ Precisa: Event listening, nudge generation via Gemini, UI integration

---

## 🔄 Fluxos de Interação

### Exemplo 1: Developer Commits Code

```
1. Developer commits to Git
   └─► Context Agent detecta
       └─► Emite "context.delta.v1"
           ├─► Strategy Agent analisa
           │   └─► Emite "strategy.insight.v1"
           │       └─► Coach cria nudge
           │           └─► UI mostra notification
           │
           ├─► Spec Agent verifica docs
           │   └─► Emite "spec.update.v1"
           │       └─► Coach confirma: "Docs atualizados ✓"
           │
           └─► Rewards Engine registra
               └─► +10 CPT (cli_action)
```

### Exemplo 2: Strategy Insight Aceito

```
1. Strategy Agent: "Extract AuthService"
   └─► Coach transforma em nudge:
       "Refactor auth em 3 passos (25min)"
   └─► Developer implementa
       └─► Commit com "Implements strategy-insight-042"
           └─► Context Agent detecta keyword
               └─► Rewards: +15 CPT (strategy_accepted)
               └─► Strategy Agent: marca insight como "implemented"
```

### Exemplo 3: Milestone Approaching

```
1. Milestone Agent: 3 dias até deadline
   └─► Emite "milestone.alert.v1"
       └─► Coach cria plano de ação:
           "Faltam 3 dias para Beta Release (75% completo)"
           ├─► Ação 1: Finalizar feature X (hoje)
           ├─► Ação 2: Testes E2E (amanhã)
           └─► Ação 3: Deploy staging (dia 3)
       └─► Spec Agent: Valida docs estão ok
       └─► Strategy Agent: Quick security scan
```

---

## 📋 Contratos de Agente (AGENT.*.md)

Cada agente tem um contrato executável:

### Formato
```markdown
---
id: agent-name
version: 1.0.0
gemini_model: gemini-1.5-flash
events_in: [list]
events_out: [list]
slos:
  latency_p50_ms: 500
  coverage_events_pct: 90
---

## Purpose
Breve descrição

## Behaviors
- Comportamento 1
- Comportamento 2

## Test Vectors
- Input → Expected Output

## Failure Modes
- Modo de falha + mitigação
```

### Arquivos a Criar
- `docs/AGENT.context.md`
- `docs/AGENT.spec.md`
- `docs/AGENT.strategy.md`
- `docs/AGENT.milestone.md`
- `docs/AGENT.coach.md`

---

## 🎯 Google ADK Integration

### O Que Usar do ADK

**Agent Development Kit** fornece:
- Event routing entre agentes
- State management compartilhado
- Handoff mechanisms
- Observability built-in

### Exemplo de Handoff

```python
from google.cloud import adk

# Coach passa para Strategy quando precisa análise
coach_agent.handoff_to(
    agent=strategy_agent,
    request={
        "type": "analyze",
        "scope": "authentication",
        "urgency": "high"
    },
    callback=coach_agent.handle_strategy_response
)
```

---

## 🚀 Roadmap de Implementação

### Fase 1 (Esta Semana)
- ✅ Coach Agent básico
- ✅ Context Agent (partial)
- ⏳ Pub/Sub infrastructure
- ⏳ Event schemas

### Fase 2 (Próxima Semana)
- ⏳ Spec Agent MVP
- ⏳ Strategy Agent MVP
- ⏳ Milestone Agent complete
- ⏳ ADK integration

### Fase 3 (Semana 3)
- ⏳ Agent contracts (AGENT.*.md)
- ⏳ Test vectors
- ⏳ SLO monitoring
- ⏳ UI dashboards

### Fase 4 (Semana 4)
- ⏳ Advanced coordination
- ⏳ ML-based insights
- ⏳ Auto-optimization

---

## 📊 Métricas de Sucesso

### Por Agente

| Agente | Métrica | Target |
|--------|---------|--------|
| Context | Latency (detect → emit) | < 2s |
| Spec | Doc freshness | < 24h |
| Strategy | Insight acceptance rate | > 60% |
| Milestone | Checkpoint success rate | > 95% |
| Coach | Nudge completion rate | > 70% |

### Sistema
- **Event throughput**: > 100 events/min
- **Cross-agent latency**: < 5s (event → action)
- **Uptime**: > 99.5%

---

## 🔐 Segurança & Governança

### Access Control
- Cada agente tem service account próprio
- Permissões mínimas necessárias
- Audit logs em Cloud Logging

### Rate Limiting
- Max 1000 events/min por agente
- Backpressure via Pub/Sub

### Failure Handling
- Circuit breakers
- Exponential backoff
- Dead letter queues

---

## 💡 Inovações do Sistema

### 1. Event-Driven
Diferente de "AI assistants" que são pull-based, nossos agentes reagem em tempo real.

### 2. Specialization
Cada agente é expert no seu domínio, não "general purpose AI".

### 3. Quantifiable Impact
Rewards tokenizados permitem medir ROI de cada agente.

### 4. Self-Improving
Agentes aprendem com feedback (acceptance rates, completion rates).

---

## 🎬 Para o Hackathon

### Narrativa
> "ContextPilot é um ecossistema de 6 agentes especializados que colaboram via Google ADK para manter desenvolvedores focados e produtivos, enquanto recompensam contribuições com CPT tokens na blockchain."

### Demo Flow
1. Developer commits → Context detecta
2. Strategy analisa → encontra issue
3. Coach cria nudge acionável
4. Developer completa → ganha CPT
5. Leaderboard atualiza em tempo real

### Diferenciais
- ✅ Multi-agent (5 agentes coordenados)
- ✅ Google ADK
- ✅ Web3 + AI combo único
- ✅ Quantificável (tokens, métricas)
- ✅ Production-ready architecture

---

**Status**: 🟡 **Arquitetura definida, implementação em progresso**

**Next**: Implementar Spec e Strategy Agents + ADK integration

---

*Documento criado: 13/10/2025*  
*Para: Cloud Run Hackathon 2025 - AI Agents Category*

