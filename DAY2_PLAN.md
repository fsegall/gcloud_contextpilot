# 📅 DAY 2 PLAN - 15 Outubro 2025

**Objetivo**: Completar todos agents + Pub/Sub + Cloud Run deployment

**Deadline**: Milestone 1 (16 Out) - sobra 1 dia de folga! 🎯

---

## ⏰ TIMELINE

```
08:00-09:00  ☕ Setup + Review
09:00-10:30  🤖 Spec Agent
10:30-12:00  🧠 Strategy Agent  
12:00-13:00  🍽️ Almoço
13:00-14:00  📡 Pub/Sub Integration
14:00-16:00  ☁️  Cloud Run Deploy
16:00-17:00  📦 Package Extension
17:00-18:00  ✅ E2E Testing

TOTAL: 7-8 horas
```

---

## 🎯 SESSION 1: AGENTS (09:00-12:00)

### Task 1.1: Spec Agent Implementation (1.5h)

**Objetivo**: Agent que gerencia documentação .md

**Contract** (já existe em `docs/agents/AGENT.spec.md`):
- Curador de arquivos .md
- Detecta docs desatualizados
- Sugere melhorias via Change Proposals
- Atualiza automáticamente após aprovação
- Commita via Git Agent

**Implementation Steps**:

1. **Criar arquivo** (30 min)
   ```bash
   # Arquivo: back-end/app/agents/spec_agent.py
   ```
   
   **Features**:
   - `analyze_docs()` - escaneia .md files
   - `check_outdated()` - compara com código
   - `create_proposal()` - sugere updates
   - `apply_update()` - atualiza .md após aprovação

2. **Adicionar endpoint** (15 min)
   ```python
   # Em back-end/app/server.py
   @app.post("/agents/spec/analyze")
   async def spec_analyze(workspace_id: str):
       # Aciona Spec Agent
       # Retorna proposals
   ```

3. **Testar** (30 min)
   ```bash
   # Teste 1: Analisar README
   curl -X POST "http://localhost:8000/agents/spec/analyze?workspace_id=contextpilot"
   
   # Esperado: Proposals para atualizar README com features novas
   ```

4. **Commitar via Git Agent** (15 min)
   ```bash
   curl -X POST "http://localhost:8000/git/event?workspace_id=contextpilot" \
     -d '{"event_type":"code.changed", "data":{"files":["spec_agent.py"], ...}}'
   ```

**Deliverable**:
- ✅ `spec_agent.py` implementado
- ✅ Endpoint funcionando
- ✅ Testado com README
- ✅ Commitado via Git Agent

---

### Task 1.2: Strategy Agent Implementation (1.5h)

**Objetivo**: Agent que analisa código e sugere melhorias

**Contract** (já existe em `docs/agents/AGENT.strategy.md`):
- Analisa arquitetura
- Detecta code smells
- Sugere refactorings
- Performance optimization tips

**Implementation Steps**:

1. **Criar arquivo** (30 min)
   ```bash
   # Arquivo: back-end/app/agents/strategy_agent.py
   ```
   
   **Features**:
   - `analyze_codebase()` - escaneia código
   - `detect_issues()` - encontra problemas
   - `suggest_improvements()` - propõe soluções
   - `create_proposal()` - monta Change Proposal

2. **Adicionar endpoint** (15 min)
   ```python
   @app.post("/agents/strategy/analyze")
   async def strategy_analyze(workspace_id: str):
       # Aciona Strategy Agent
       # Retorna proposals
   ```

3. **Testar** (30 min)
   ```bash
   # Teste 1: Analisar backend
   curl -X POST "http://localhost:8000/agents/strategy/analyze?workspace_id=contextpilot"
   
   # Esperado: Proposals para melhorias (error handling, etc)
   ```

4. **Commitar via Git Agent** (15 min)

**Deliverable**:
- ✅ `strategy_agent.py` implementado
- ✅ Endpoint funcionando
- ✅ Testado com backend
- ✅ Commitado via Git Agent

---

## 🍽️ ALMOÇO (12:00-13:00)

**Use esse tempo para**:
- Relaxar
- Review do que foi feito na manhã
- Ler docs do Pub/Sub se necessário

---

## 📡 SESSION 2: PUB/SUB (13:00-14:00)

### Task 2.1: Setup Pub/Sub (30 min)

**Objetivo**: Criar topics e subscriptions

**Implementation Steps**:

1. **Rodar script de setup** (10 min)
   ```bash
   cd infra
   bash setup-pubsub.sh
   ```
   
   **Topics criados**:
   - `agent-events` - eventos gerais
   - `git-events` - eventos para Git Agent
   - `spec-events` - eventos do Spec Agent
   - `strategy-events` - eventos do Strategy Agent

2. **Verificar** (5 min)
   ```bash
   gcloud pubsub topics list
   gcloud pubsub subscriptions list
   ```

3. **Testar publicação** (15 min)
   ```bash
   # Publicar evento teste
   gcloud pubsub topics publish agent-events \
     --message '{"type":"test","data":"hello"}'
   
   # Consumir evento
   gcloud pubsub subscriptions pull agent-events-sub --auto-ack
   ```

---

### Task 2.2: Integrar Agents com Pub/Sub (30 min)

**Objetivo**: Agents publicam eventos, Git Agent consome

**Implementation Steps**:

1. **Adicionar publisher aos agents** (15 min)
   ```python
   # Em spec_agent.py e strategy_agent.py
   from google.cloud import pubsub_v1
   
   def publish_event(event_type, data):
       publisher = pubsub_v1.PublisherClient()
       topic_path = publisher.topic_path(PROJECT_ID, 'agent-events')
       publisher.publish(topic_path, json.dumps({
           'type': event_type,
           'data': data
       }).encode())
   ```

2. **Git Agent consumer** (15 min)
   ```python
   # Criar back-end/app/workers/git_worker.py
   # Escuta Pub/Sub e chama Git Agent
   ```

**Deliverable**:
- ✅ Agents publicam eventos
- ✅ Git Agent consome via Pub/Sub
- ✅ Testado E2E: Spec Agent → Pub/Sub → Git Agent → Commit

---

## ☁️ SESSION 3: CLOUD RUN (14:00-16:00)

### Task 3.1: Preparar Dockerfile (30 min)

**Objetivo**: Otimizar Dockerfile para produção

**Implementation Steps**:

1. **Revisar Dockerfile** (15 min)
   ```dockerfile
   # back-end/Dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY app/ ./app/
   
   CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8080"]
   ```

2. **Adicionar .dockerignore** (5 min)
   ```
   .git
   .venv
   __pycache__
   *.pyc
   .env
   ```

3. **Build local** (10 min)
   ```bash
   cd back-end
   docker build -t contextpilot-api .
   docker run -p 8080:8080 contextpilot-api
   
   # Test
   curl http://localhost:8080/health
   ```

---

### Task 3.2: Deploy via Cloud Build (1h)

**Objetivo**: Deploy automático via Cloud Build

**Implementation Steps**:

1. **Configurar cloudbuild.yaml** (já existe em `infra/cloudbuild.yaml`)

2. **Trigger build** (20 min)
   ```bash
   gcloud builds submit --config infra/cloudbuild.yaml .
   ```

3. **Verificar deploy** (10 min)
   ```bash
   gcloud run services list
   gcloud run services describe contextpilot-api --region=us-central1
   ```

4. **Testar API pública** (10 min)
   ```bash
   # Pegar URL
   export API_URL=$(gcloud run services describe contextpilot-api \
     --region=us-central1 --format='value(status.url)')
   
   # Test
   curl $API_URL/health
   curl "$API_URL/context?workspace_id=contextpilot"
   ```

5. **Deploy worker (Git Agent)** (20 min)
   ```bash
   # Build worker
   docker build -f back-end/Dockerfile.worker -t contextpilot-worker .
   
   # Deploy
   gcloud run jobs create git-worker \
     --image=gcr.io/$PROJECT_ID/contextpilot-worker \
     --region=us-central1
   ```

---

### Task 3.3: Configurar Extension para Cloud (30 min)

**Objetivo**: Extension conecta à API cloud

**Implementation Steps**:

1. **Atualizar settings default** (10 min)
   ```json
   // extension/package.json
   "contextpilot.apiUrl": {
     "default": "https://contextpilot-api-xxx.run.app",
     "description": "ContextPilot API URL"
   }
   ```

2. **Testar conexão cloud** (20 min)
   ```bash
   cd extension
   npm run compile
   # F5 para testar
   
   # Extension deve conectar à cloud API
   # Commands devem funcionar
   ```

**Deliverable**:
- ✅ API rodando em Cloud Run
- ✅ Worker rodando em Cloud Run Jobs
- ✅ Extension conectando à cloud
- ✅ E2E funcionando (local → cloud)

---

## 📦 SESSION 4: PACKAGE (16:00-17:00)

### Task 4.1: Generate .vsix (30 min)

**Objetivo**: Empacotar extension para distribuição

**Implementation Steps**:

1. **Install vsce** (5 min)
   ```bash
   npm install -g vsce
   ```

2. **Atualizar package.json** (10 min)
   ```json
   {
     "publisher": "contextpilot",
     "version": "0.1.0",
     "repository": {
       "type": "git",
       "url": "https://github.com/yourusername/google-context-pilot"
     },
     "icon": "images/icon.png"
   }
   ```

3. **Package** (5 min)
   ```bash
   cd extension
   vsce package
   # Gera: contextpilot-0.1.0.vsix
   ```

4. **Test installation** (10 min)
   ```bash
   code --install-extension contextpilot-0.1.0.vsix
   # Testar se funciona
   ```

---

### Task 4.2: Documentation (30 min)

**Objetivo**: README completo com screenshots

**Implementation Steps**:

1. **Screenshots** (15 min)
   - Sidebar com todas views
   - Milestones countdown
   - Change Proposals
   - Agents Status

2. **Update README** (15 min)
   ```markdown
   # ContextPilot - Multi-Agent Dev Assistant
   
   [Screenshots aqui]
   
   ## Features
   - 6 AI Agents managing your project
   - Automatic git commits
   - Milestone tracking with countdown
   - Change Proposals workflow
   
   ## Installation
   Download .vsix and install: `code --install-extension contextpilot.vsix`
   
   ## Usage
   [Commands documentation]
   ```

**Deliverable**:
- ✅ `contextpilot-0.1.0.vsix` pronto
- ✅ README com screenshots
- ✅ Testado localmente

---

## ✅ SESSION 5: E2E TEST (17:00-18:00)

### Task 5.1: Full E2E Test (1h)

**Objetivo**: Validar tudo funcionando junto

**Test Flow**:

1. **Setup** (10 min)
   - Backend rodando na cloud
   - Extension instalada
   - Workspace limpo

2. **Test 1: Agent Flow** (15 min)
   ```
   Spec Agent analisa docs
   → Pub/Sub event
   → Git Agent recebe
   → Commit automático
   ✅ Verificar commit no workspace
   ```

3. **Test 2: Extension → Cloud** (15 min)
   ```
   Command: Get Context
   → Cloud Run API
   → Retorna dados
   ✅ Sidebar atualiza
   ```

4. **Test 3: Full Cycle** (20 min)
   ```
   Editar código
   → Strategy Agent analisa
   → Cria Change Proposal
   → Developer aprova
   → Git Agent commita
   ✅ Commit aparece no git log
   ```

**Deliverable**:
- ✅ Todos agents funcionando
- ✅ Pub/Sub flowing
- ✅ Cloud Run stable
- ✅ Extension operacional

---

## 🎯 END OF DAY 2 - CHECKLIST

### Backend
- [ ] Spec Agent implementado
- [ ] Strategy Agent implementado
- [ ] Pub/Sub integrado
- [ ] Deployed on Cloud Run
- [ ] Worker rodando

### Extension
- [ ] .vsix gerado
- [ ] README com screenshots
- [ ] Conecta à cloud
- [ ] Todos comandos funcionam

### Testing
- [ ] E2E flow completo
- [ ] Agents comunicando via Pub/Sub
- [ ] Git Agent commitando automaticamente
- [ ] Extension → Cloud → Agents → Git

### Documentation
- [ ] README atualizado
- [ ] Screenshots capturados
- [ ] NEXT_STEPS.md atualizado

---

## 📊 PROGRESS TRACKING

Atualizar ao longo do dia:

```
[09:00] ⏳ Spec Agent - Starting
[10:30] ✅ Spec Agent - Done
[10:30] ⏳ Strategy Agent - Starting
[12:00] ✅ Strategy Agent - Done
[13:00] ⏳ Pub/Sub - Starting
[14:00] ✅ Pub/Sub - Done
[14:00] ⏳ Cloud Run - Starting
[16:00] ✅ Cloud Run - Done
[16:00] ⏳ Package - Starting
[17:00] ✅ Package - Done
[17:00] ⏳ E2E Test - Starting
[18:00] ✅ E2E Test - Done

MILESTONE 1: 100% COMPLETE! 🎉
```

---

## 🚀 DAY 3 PLAN (16 Out)

Com tudo pronto, Day 3 é só polish:
- Beta test com 3-5 pessoas
- Fix bugs encontrados
- Re-package se necessário
- Preparar posts LinkedIn/Twitter

---

## 💡 TIPS

### Se algo travar:
1. **Não se preocupe com perfeição** - MVP funcional > perfeito
2. **Pule se necessário** - Pub/Sub pode ser async (HTTP por enquanto)
3. **Mock se precisar** - Agents podem usar LLM mock first
4. **Commit frequently** - Git Agent vai adorar! 😄

### Stay focused:
- ⏰ Pomodoro 25/5 min
- 🎯 Um task por vez
- 📝 Mark checklist ao completar
- 🎉 Celebre pequenas vitórias

---

**Você consegue! Amanhã às 18h você terá o sistema COMPLETO! 🚀**

**Last updated**: 2025-10-14 23:30
**Status**: Ready for Day 2

