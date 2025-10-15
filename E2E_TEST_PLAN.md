# 🧪 E2E Test Plan - Extension + Backend

Plano completo para testar o ContextPilot como uma extensão real em um projeto.

---

## 🎯 Objetivo

Testar o fluxo completo:
```
Developer codes → Extension detects → Backend processes → 
Agents analyze → Proposals created → Developer approves → 
Rewards tracked → Balance updates
```

---

## 🏗️ Estado Atual vs Estado Necessário

### ✅ O Que Já Temos
- Smart contract deployed (Sepolia)
- Extension code criada (TypeScript)
- Backend FastAPI existe
- Routers: rewards, proposals, events
- Git_Context_Manager

### ⚠️ O Que Precisa Ajustar

#### Backend (Modelo Antigo → Multi-Agent)
```python
# ANTIGO (workspace-based):
@app.get("/context")
def get_context(workspace_id: str):
    # Retorna checkpoint + milestones

# NOVO (multi-agent + proposals):
@app.get("/proposals")
def get_proposals(user_id: str):
    # Retorna change proposals dos agents

@app.post("/proposals/{id}/approve")
def approve_proposal(id: str, user_id: str):
    # Aplica mudança, tracked rewards
```

#### Endpoints Faltando
```python
# Health check
GET /health

# Auth simples
POST /auth/signup
POST /auth/login

# Agents
GET /agents/status
POST /agents/coach/ask

# Context (novo estilo)
POST /context/commit
GET /context/diff
```

---

## 📋 Checklist de Ajustes

### 1. Backend Endpoints (Prioridade Alta)

- [ ] **GET /health** - Extension verifica conectividade
  ```python
  @app.get("/health")
  def health():
      return {"status": "ok", "version": "2.0.0"}
  ```

- [ ] **Ajustar GET /proposals** - Retornar formato esperado pela extension
  ```python
  # Atual: usa Firestore
  # Precisamos: mockar alguns proposals para teste
  ```

- [ ] **POST /context/commit** - Extension envia mudanças
  ```python
  @app.post("/context/commit")
  def commit_context(user_id: str, workspace_path: str):
      # Trigger agents analysis
      # Return: {"status": "analyzing", "job_id": "..."}
  ```

- [ ] **GET /agents/status** - Extension mostra status dos agents
  ```python
  @app.get("/agents/status")
  def agents_status():
      # Return mock status for now
      return [
          {"agent_id": "context", "name": "Context Agent", "status": "active"},
          {"agent_id": "spec", "name": "Spec Agent", "status": "active"},
          # ...
      ]
  ```

### 2. Extension Config (Prioridade Alta)

- [ ] Atualizar `package.json` default API URL
  ```json
  "contextpilot.apiUrl": {
    "default": "http://localhost:8000"
  }
  ```

- [ ] Criar arquivo `.env.example` na extension
  ```
  VITE_API_URL=http://localhost:8000
  ```

### 3. Mock Data (Prioridade Alta - Para Teste)

- [ ] Criar endpoint `/proposals/mock` que retorna proposals fake
  ```python
  @app.get("/proposals/mock")
  def mock_proposals():
      return [
          {
              "id": "prop-1",
              "agent_id": "strategy",
              "title": "Add error handling to API calls",
              "description": "Found 3 API calls without try/catch",
              "proposed_changes": [
                  {
                      "file_path": "src/api.ts",
                      "change_type": "update",
                      "description": "Wrap fetch in try-catch"
                  }
              ],
              "status": "pending",
              "created_at": "2025-10-14T10:00:00Z"
          }
      ]
  ```

- [ ] Criar endpoint `/rewards/balance/mock`
  ```python
  @app.get("/rewards/balance/mock")
  def mock_balance():
      return {
          "balance": 150,
          "total_earned": 300,
          "pending_rewards": 50
      }
  ```

---

## 🧪 Teste E2E - Passo a Passo

### Setup (One Time)

#### 1. Backend
```bash
cd back-end

# Create virtual env
python -m venv .venv
source .venv/bin/activate  # ou .venv\Scripts\activate no Windows

# Install deps
pip install -r requirements.txt

# Run server
python -m uvicorn app.server:app --reload --port 8000
```

Verifique: http://localhost:8000/docs

#### 2. Extension
```bash
cd extension

# Install deps
npm install

# Compile TypeScript
npm run compile

# Open in VSCode
code .

# Press F5 to launch Extension Development Host
```

---

### Teste 1: Connection

**Objetivo**: Extension conecta ao backend

**Steps**:
1. Extension Development Host abre
2. Status bar deve mostrar: "ContextPilot: Connecting..."
3. Após ~2s: "ContextPilot: Connected" (ou ⭐ 0 CPT)
4. Sidebar deve ter ícone do ContextPilot

**Verificar**:
- [ ] Status bar atualiza
- [ ] Sem erros no console
- [ ] Backend logs mostram: GET /health

**Debug**:
```typescript
// extension/src/extension.ts
console.log('Connecting to:', config.get('apiUrl'));
```

```python
# back-end/app/server.py
@app.get("/health")
def health():
    logger.info("Health check called")
    return {"status": "ok"}
```

---

### Teste 2: View Proposals

**Objetivo**: Proposals aparecem na sidebar

**Steps**:
1. Abrir sidebar do ContextPilot
2. Clicar em "Change Proposals" view
3. Deve aparecer 1+ proposal (mock)

**Verificar**:
- [ ] View "Change Proposals" existe
- [ ] Lista não está vazia
- [ ] Proposals têm título e descrição
- [ ] Botões ✓ e ✗ aparecem

**Mock Data Necessário**:
```python
# Usar endpoint /proposals/mock ou
# Modificar /proposals para retornar mock se user_id == "test"
```

---

### Teste 3: Approve Proposal

**Objetivo**: Clicar approve funciona

**Steps**:
1. Na sidebar, clicar em proposal
2. Clicar botão ✓ (approve)
3. Modal de confirmação aparece
4. Confirmar
5. Notificação: "✅ Proposal approved! +15 CPT"

**Verificar**:
- [ ] Modal aparece
- [ ] Notificação aparece
- [ ] Backend logs: POST /proposals/{id}/approve
- [ ] Status bar CPT balance atualiza (0 → 15)

**Backend Necessário**:
```python
@app.post("/proposals/{proposal_id}/approve")
def approve_proposal(proposal_id: str, user_id: str = Body(...)):
    # Mock: just return success
    return {
        "status": "approved",
        "rewards": {
            "cpt_earned": 15
        }
    }
```

---

### Teste 4: Rewards Balance

**Objetivo**: Ver balance de CPT

**Steps**:
1. Clicar no status bar (⭐ X CPT)
2. Webview abre mostrando:
   - Balance atual
   - Total earned
   - Pending rewards
   - Leaderboard (mock)

**Verificar**:
- [ ] Webview abre
- [ ] Dados aparecem formatados
- [ ] Leaderboard tem pelo menos 3 entradas

---

### Teste 5: Ask Coach

**Objetivo**: Perguntar algo ao Coach

**Steps**:
1. Cmd+Shift+P → "ContextPilot: Ask Coach"
2. Digitar: "How can I improve my code?"
3. Notificação: "Coach is thinking..."
4. Após ~2s: "Coach responded!"
5. Sidebar Coach view mostra Q&A

**Verificar**:
- [ ] Input aparece
- [ ] Loading state
- [ ] Resposta aparece
- [ ] Backend logs: POST /agents/coach/ask

**Backend Necessário**:
```python
@app.post("/agents/coach/ask")
def coach_ask(user_id: str, question: str):
    # Mock response
    return {
        "answer": "Focus on adding error handling and tests!"
    }
```

---

### Teste 6: Commit Context

**Objetivo**: Commitar mudanças

**Steps**:
1. Fazer mudança em um arquivo do projeto de teste
2. Cmd+Shift+P → "ContextPilot: Commit Context"
3. Loading: "Committing context..."
4. Notificação: "✅ Context committed!"

**Verificar**:
- [ ] Notificação aparece
- [ ] Backend logs: POST /context/commit
- [ ] Agents começam análise (pode ser mock)

---

### Teste 7: Agent Status

**Objetivo**: Ver status dos agents

**Steps**:
1. Sidebar → "Agents Status" view
2. Deve mostrar 6 agents
3. Cada um com icon (verde = active, amarelo = idle)

**Verificar**:
- [ ] 6 agents listados
- [ ] Icons coloridos
- [ ] Tooltip com last activity

---

## 🔧 Ajustes Necessários no Backend

### Arquivo: `back-end/app/server.py`

Adicionar no final:

```python
# ===== ENDPOINTS FOR EXTENSION =====

@app.get("/health")
def health_check():
    """Health check for extension connectivity"""
    return {
        "status": "ok",
        "version": "2.0.0",
        "agents": ["context", "spec", "strategy", "milestone", "git", "coach"]
    }

@app.get("/agents/status")
def get_agents_status():
    """Get status of all agents (mock for now)"""
    return [
        {
            "agent_id": "context",
            "name": "Context Agent",
            "status": "active",
            "last_activity": "Just now"
        },
        {
            "agent_id": "spec",
            "name": "Spec Agent",
            "status": "active",
            "last_activity": "5 minutes ago"
        },
        {
            "agent_id": "strategy",
            "name": "Strategy Agent",
            "status": "idle",
            "last_activity": "1 hour ago"
        },
        {
            "agent_id": "milestone",
            "name": "Milestone Agent",
            "status": "active",
            "last_activity": "10 minutes ago"
        },
        {
            "agent_id": "git",
            "name": "Git Agent",
            "status": "active",
            "last_activity": "2 minutes ago"
        },
        {
            "agent_id": "coach",
            "name": "Coach Agent",
            "status": "active",
            "last_activity": "Just now"
        }
    ]

@app.post("/agents/coach/ask")
def coach_ask(
    user_id: str = Body(...),
    question: str = Body(...)
):
    """Ask the coach agent a question (mock for now)"""
    # TODO: Integrate with actual coach agent
    mock_answer = f"Great question! For '{question}', I recommend: 1) Break it into smaller tasks, 2) Write tests first, 3) Document as you go."
    return {"answer": mock_answer}

@app.get("/proposals/mock")
def get_mock_proposals():
    """Get mock proposals for testing"""
    return [
        {
            "id": "prop-001",
            "agent_id": "strategy",
            "title": "Add error handling to API calls",
            "description": "Found 3 API calls without proper error handling. This could cause silent failures.",
            "proposed_changes": [
                {
                    "file_path": "src/api.ts",
                    "change_type": "update",
                    "description": "Wrap fetch calls in try-catch blocks"
                }
            ],
            "status": "pending",
            "created_at": "2025-10-14T10:30:00Z"
        },
        {
            "id": "prop-002",
            "agent_id": "spec",
            "title": "Update API documentation",
            "description": "API endpoints in api.ts need documentation with examples.",
            "proposed_changes": [
                {
                    "file_path": "src/api.ts",
                    "change_type": "update",
                    "description": "Add JSDoc comments with examples"
                }
            ],
            "status": "pending",
            "created_at": "2025-10-14T10:45:00Z"
        }
    ]

@app.get("/rewards/balance/mock")
def get_mock_balance():
    """Get mock rewards balance for testing"""
    return {
        "balance": 150,
        "total_earned": 300,
        "pending_rewards": 50
    }
```

---

## 📊 Success Criteria

### Teste Passa Se:

1. ✅ **Connection**: Extension conecta ao backend sem erro
2. ✅ **Proposals**: Pelo menos 1 proposal aparece na sidebar
3. ✅ **Approve**: Clicar approve funciona e mostra notificação
4. ✅ **Balance**: CPT balance atualiza após approve
5. ✅ **Coach**: Perguntar retorna resposta (mock OK)
6. ✅ **Agents**: 6 agents listados com status
7. ✅ **Commit**: Commit context não dá erro

### Logs Esperados:

**Backend:**
```
INFO: GET /health - Status: 200
INFO: GET /proposals - Status: 200
INFO: POST /proposals/prop-001/approve - Status: 200
INFO: GET /rewards/balance - Status: 200
INFO: POST /agents/coach/ask - Status: 200
INFO: GET /agents/status - Status: 200
```

**Extension Console:**
```
ContextPilot: Connecting to http://localhost:8000
ContextPilot: Connected!
Fetching proposals...
Proposals loaded: 2
Approving proposal: prop-001
Proposal approved! Earned: 15 CPT
```

---

## 🐛 Troubleshooting

### Extension não conecta
```typescript
// Check: extension/src/services/contextpilot.ts
console.log('API URL:', this.client.defaults.baseURL);
```

### Proposals não aparecem
```python
# Check: back-end/app/routers/proposals.py
logger.info(f"Returning {len(proposals)} proposals")
```

### Balance não atualiza
```typescript
// Check: extension/src/extension.ts
async function updateStatusBar() {
    const balance = await service.getBalance();
    console.log('Balance:', balance);
}
```

---

## 🚀 Próximos Passos Após Teste

### Se Tudo Funciona:
1. ✅ Remover endpoints /mock
2. ✅ Implementar agents reais
3. ✅ Integrar com Firestore
4. ✅ Deploy to Cloud Run

### Se Encontrar Bugs:
1. 🐛 Documentar em GitHub Issues
2. 🔧 Priorizar por severidade
3. ✅ Fix antes de launch

---

**Created**: 2025-10-14  
**Purpose**: E2E testing before launch  
**Status**: Ready to execute

