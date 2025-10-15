# 🏗️ Criar Workspace "contextpilot"

Vamos usar a própria API para criar um workspace para este projeto!

---

## Passo 1: Backend Rodando

```bash
cd back-end
source .venv/bin/activate
python -m uvicorn app.server:app --reload --port 8000
```

---

## Passo 2: Criar Workspace via API

### Opção A: Via cURL (Terminal)

```bash
curl -X POST "http://localhost:8000/generate-context?workspace_id=contextpilot" \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "ContextPilot - Multi-Agent Dev Assistant",
    "goal": "Build a multi-agent system that helps developers manage project context, deployed on Google Cloud Run for the Cloud Run Hackathon",
    "initial_status": "Extension integration in progress. Backend API working, smart contract deployed on Sepolia. Next: E2E testing.",
    "milestones": [
      {
        "name": "Extension MVP with real API integration",
        "due": "2025-10-16"
      },
      {
        "name": "Multi-agent system fully integrated",
        "due": "2025-10-20"
      },
      {
        "name": "Deploy to Cloud Run",
        "due": "2025-10-25"
      },
      {
        "name": "Beta launch with 50 users",
        "due": "2025-11-01"
      },
      {
        "name": "Hackathon submission",
        "due": "2025-11-10"
      }
    ]
  }'
```

### Opção B: Via Swagger UI

1. Abrir: http://localhost:8000/docs
2. Procurar: `POST /generate-context`
3. Click "Try it out"
4. Preencher:
   - `workspace_id`: `contextpilot`
   - Request body:
     ```json
     {
       "project_name": "ContextPilot - Multi-Agent Dev Assistant",
       "goal": "Build a multi-agent system that helps developers manage project context, deployed on Google Cloud Run for the Cloud Run Hackathon",
       "initial_status": "Extension integration in progress. Backend API working, smart contract deployed on Sepolia. Next: E2E testing.",
       "milestones": [
         {
           "name": "Extension MVP with real API integration",
           "due": "2025-10-16"
         },
         {
           "name": "Multi-agent system fully integrated",
           "due": "2025-10-20"
         },
         {
           "name": "Deploy to Cloud Run",
           "due": "2025-10-25"
         },
         {
           "name": "Beta launch with 50 users",
           "due": "2025-11-01"
         },
         {
           "name": "Hackathon submission",
           "due": "2025-11-10"
         }
       ]
     }
     ```
5. Click "Execute"

---

## Passo 3: Verificar Workspace Criado

```bash
# Ver estrutura criada
ls -la back-end/.contextpilot/workspaces/contextpilot/

# Ver checkpoint
cat back-end/.contextpilot/workspaces/contextpilot/checkpoint.yaml

# Ver git log
cd back-end/.contextpilot/workspaces/contextpilot
git log --oneline
```

**Esperado**: 1 commit inicial: "Initial context generated for project: ContextPilot..."

---

## Passo 4: Testar API com Novo Workspace

```bash
# Get context
curl "http://localhost:8000/context?workspace_id=contextpilot"

# Get milestones
curl "http://localhost:8000/context/milestones?workspace_id=contextpilot"

# Get coach tip
curl "http://localhost:8000/coach?workspace_id=contextpilot"

# Fazer um commit
curl -X POST "http://localhost:8000/commit?workspace_id=contextpilot&message=Testing%20workspace&agent=manual"
```

---

## Passo 5: Extension Usando Workspace Correto

Agora vamos configurar a extension para usar `contextpilot` em vez de `default`.

### Atualizar comandos

**Arquivo**: `extension/src/commands/index.ts`

Mudar `'default'` para `'contextpilot'` em todos os comandos:

```typescript
const context = await service.getContextReal('contextpilot');
```

**OU** melhor ainda, detectar automaticamente do workspace path:

```typescript
// Get workspace name from folder
const workspaceName = vscode.workspace.name || 'contextpilot';
const context = await service.getContextReal(workspaceName);
```

---

## Passo 6: Testar Extension com Workspace Real

```bash
cd extension
npm run compile
# Press F5
```

No Extension Development Host:
- **Cmd+Shift+P** → "ContextPilot: Get Project Context"
- Deve mostrar dados do projeto ContextPilot! 🎉

---

## ✅ Workspace Criado - Próximos Passos

Agora você tem:
- ✅ Workspace `contextpilot` criado via API
- ✅ Checkpoint inicial configurado
- ✅ 5 milestones definidos
- ✅ Git repo inicializado

**Usar o ContextPilot para desenvolver o ContextPilot!** 🚀

A cada progresso:
```bash
# Via API
curl -X POST "http://localhost:8000/commit?workspace_id=contextpilot&message=Feature%20X%20completed&agent=manual"

# Ou via extension (depois de configurar)
Cmd+Shift+P → "ContextPilot: Commit Context (Real API)"
```

---

## 🎯 Dogfooding em Ação

Você vai:
1. Desenvolver features da extension
2. Usar a extension para commitar progresso
3. Coach Agent vai te dar dicas sobre os milestones
4. Ver o próprio projeto evoluindo no ContextPilot!

**Meta-recursivo e muito útil!** 🤯

---

**Tempo**: 5 minutos
**Resultado**: Workspace real criado, pronto para uso

