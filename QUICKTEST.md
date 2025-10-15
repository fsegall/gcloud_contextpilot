# ⚡ Quick Test - 15 Minutes

Como testar a extensão E2E AGORA.

---

## 🚀 Setup (5 min)

### Terminal 1: Backend
```bash
cd back-end

# Activate venv
source .venv/bin/activate  # ou .venv\Scripts\activate no Windows

# Run server
python -m uvicorn app.server:app --reload --port 8000
```

Deve aparecer:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

✅ Test: Abrir http://localhost:8000/docs

---

### Terminal 2: Extension

```bash
cd extension

# Install deps (primeira vez)
npm install

# Compile TypeScript
npm run compile
```

Sem erros? ✅ Pronto!

---

## 🧪 Teste 1: Launch Extension (2 min)

1. No VSCode, abra pasta `extension/`
2. Press **F5** (ou Run > Start Debugging)
3. Aguarde Extension Development Host abrir
4. Verifique status bar (canto inferior direito)

**Esperado**:
```
⭐ 150 CPT | ContextPilot: Connected
```

**Se não aparecer**: Check console do Extension Development Host
- Help > Toggle Developer Tools
- Console tab
- Procure erros

---

## 🧪 Teste 2: View Proposals (2 min)

1. Na Extension Development Host, clique no ícone do ContextPilot na Activity Bar (sidebar esquerda)
2. Deve ter 4 views:
   - Change Proposals
   - Rewards  
   - Agents Status
   - Coach

3. Clique em "Change Proposals"

**Esperado**:
- 2 proposals aparecem
- "Add error handling to API calls"
- "Update API documentation"
- Botões ✓ e ✗ em cada um

**Debug**: Se não aparecer
```
// Terminal Backend deve mostrar:
INFO: GET /proposals/mock - Status: 200
```

---

## 🧪 Teste 3: Approve Proposal (2 min)

1. Na lista de proposals, clique no primeiro
2. Clique no botão ✓ (approve)
3. Modal de confirmação aparece
4. Confirme

**Esperado**:
- Notificação: "✅ Proposal approved! You earned CPT tokens 🎉"
- Status bar atualiza (mas pode não mudar se mock)

**Debug**: Check console Extension Development Host

---

## 🧪 Teste 4: View Rewards (2 min)

1. Clique no status bar (⭐ X CPT)
2. Webview deve abrir

**Esperado**:
- Balance: 150 CPT
- Total Earned: 300 CPT
- Pending: 50 CPT
- Leaderboard (pode estar vazio)

---

## 🧪 Teste 5: Ask Coach (2 min)

1. Cmd+Shift+P (Ctrl+Shift+P no Windows/Linux)
2. Digite: "ContextPilot: Ask Coach"
3. Input aparece
4. Digite: "How can I improve my code?"
5. Enter

**Esperado**:
- Notificação: "Coach is thinking..."
- Após ~1s: "Coach responded!"
- Sidebar Coach view mostra Q&A

**Backend deve logar**:
```
INFO: POST /agents/coach/ask - Status: 200
```

---

## 🧪 Teste 6: Agents Status (1 min)

1. Sidebar > "Agents Status"
2. Deve listar 6 agents:
   - Context Agent (green)
   - Spec Agent (green)
   - Strategy Agent (yellow - idle)
   - Milestone Agent (green)
   - Git Agent (green)
   - Coach Agent (green)

---

## ✅ Success Criteria

Se todos passaram:
- ✅ Extension conecta
- ✅ Proposals aparecem
- ✅ Approve funciona
- ✅ Rewards mostra dados
- ✅ Coach responde
- ✅ Agents listados

**→ Core está funcionando! Pronto para build MVP real.**

---

## 🐛 Troubleshooting

### Extension não conecta

**Sintoma**: Status bar mostra "Disconnected"

**Fix**:
1. Backend rodando? Check terminal 1
2. URL correta? Default: http://localhost:8000
3. Settings: Cmd+, > Extensions > ContextPilot
4. Verifique: `contextpilot.apiUrl`

---

### Proposals não aparecem

**Sintoma**: Lista vazia

**Fix**:
1. Backend logs mostram GET /proposals/mock?
2. Extension console tem erros?
3. Try: Cmd+Shift+P > "ContextPilot: Refresh Status"

---

### TypeScript errors

**Sintoma**: `npm run compile` falha

**Fix**:
```bash
cd extension
rm -rf node_modules
npm install
npm run compile
```

---

## 📊 Backend Logs Esperados

Durante o teste, você deve ver:

```
INFO: GET /health - Status: 200
INFO: GET /proposals/mock called
INFO: GET /proposals/mock - Status: 200
INFO: GET /rewards/balance/mock called for user: test-user
INFO: GET /rewards/balance/mock - Status: 200
INFO: GET /agents/status called
INFO: GET /agents/status - Status: 200
INFO: POST /agents/coach/ask - user: test-user, question: How can I improve my code?
INFO: POST /agents/coach/ask - Status: 200
```

---

## 🎯 Next Steps

### Se tudo funciona:
1. ✅ Implementar agents reais (não mock)
2. ✅ Integrar com Firestore
3. ✅ Add auth real
4. ✅ Deploy to Cloud Run

### Se encontrou bugs:
1. 🐛 Anote em `BUGS.md`
2. 🔧 Fix antes de continuar
3. ✅ Re-test

---

## 💡 Tips

### Hot Reload Extension
- Após mudar código da extension
- No Extension Development Host: Cmd+R (recarregar)
- Não precisa parar e re-lançar

### View Backend Docs
- http://localhost:8000/docs
- Pode testar endpoints manualmente

### Debug Extension
- Extension Development Host
- Help > Toggle Developer Tools
- Console tab = seus console.logs

---

**Tempo total**: 15 minutos

**Status esperado**: ✅ Core funcionando com mocks

**Próximo**: Implementar funcionalidades reais

---

**Created**: 2025-10-14  
**Purpose**: Quick E2E validation

