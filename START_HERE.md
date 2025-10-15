# 🚀 START HERE - Teste Rápido da API Real

## ⚡ 7 Minutos para Testar

### Passo 1: Backend (1 min)

```bash
cd back-end
source .venv/bin/activate
python -m uvicorn app.server:app --reload --port 8000
```

✅ Deve aparecer: `Uvicorn running on http://127.0.0.1:8000`

**Teste rápido**:
```bash
curl http://localhost:8000/health
```

Esperado: `{"status":"ok","version":"2.0.0",...}`

---

### Passo 1.5: Criar Workspace "contextpilot" (2 min) 🆕

**Usar o ContextPilot para gerenciar o desenvolvimento do ContextPilot!** (dogfooding)

```bash
# Em outro terminal (deixe o backend rodando)
./scripts/shell/create-contextpilot-workspace.sh
```

✅ Deve criar workspace e mostrar checkpoint + git log

**Ou manualmente via cURL**:
```bash
curl -X POST "http://localhost:8000/generate-context?workspace_id=contextpilot" \
  -H "Content-Type: application/json" \
  -d '{"project_name":"ContextPilot - Multi-Agent Dev Assistant","goal":"Build a multi-agent system deployed on Google Cloud Run for the Cloud Run Hackathon","initial_status":"Extension integration in progress","milestones":[{"name":"Extension MVP","due":"2025-10-16"},{"name":"Cloud Run deployment","due":"2025-10-25"},{"name":"Hackathon submission","due":"2025-11-10"}]}'
```

**Verificar**:
```bash
ls back-end/.contextpilot/workspaces/contextpilot/
cat back-end/.contextpilot/workspaces/contextpilot/checkpoint.yaml
```

---

### Passo 2: Extension (2 min)

```bash
cd extension

# Se primeira vez:
npm install

# Compile
npm run compile
```

Sem erros? ✅ Pronto!

---

### Passo 3: Testar no VSCode (2 min)

1. Abra a pasta `extension/` no VSCode
2. Press **F5** (Extension Development Host abre)
3. **Cmd+Shift+P** (Ctrl+Shift+P no Linux)
4. Digite: **"ContextPilot: Get Project Context"**
5. Enter

**Esperado**: Notificação mostrando:
```
📦 Project: ContextPilot - Multi-Agent Dev Assistant
🎯 Goal: Build a multi-agent system deployed on Google Cloud Run...
📊 Status: Extension integration in progress
🗓️ Milestones: 3 (ou 5, dependendo do que você criou)
```

✅ **Funciona? Extension está conectada à API real e mostrando dados do workspace "contextpilot"!**

---

## 🎯 Próximo Teste: Commit

1. **Cmd+Shift+P** → "ContextPilot: Commit Context (Real API)"
2. Digite mensagem: "Test commit from extension"
3. Enter

**Verificar se funcionou**:
```bash
cd back-end/.contextpilot/workspaces/default
git log --oneline -1
```

Deve mostrar seu commit! ✅

---

## 🧠 Próximo: Coach

**Cmd+Shift+P** → "ContextPilot: Get Coach Tip (Real API)"

Deve mostrar dica baseada no estado do projeto!

---

## ✅ Se Tudo Funcionar

Você terá comprovado:
- ✅ Backend rodando
- ✅ Extension conectada
- ✅ API real sendo usada
- ✅ Comandos funcionando

**Próximo passo**: Expandir funcionalidades reais, passo a passo!

---

## 🐛 Se Não Funcionar

### Extension não conecta
- Backend está rodando? Check terminal
- URL correta? Default: http://localhost:8000

### Comando não aparece
```bash
cd extension
npm run compile
# Press F5 novamente
```

### Erro no console
- Extension Development Host > Help > Toggle Developer Tools
- Console tab = ver erro detalhado

---

**Tempo total**: 5 minutos
**Objetivo**: Provar que a integração real funciona!

