# Extension Debug Steps

**Debugging ContextPilot Extension → Cloud Connection**

---

## 🔍 Situação Atual

### ✅ Confirmado (via logs):
- Backend Cloud Run está rodando
- Extension faz requests ao cloud (balance/mock)
- Backend responde corretamente
- Proposals existem no backend

### ❌ Problema:
- Console não mostra logs da extension
- Proposals não aparecem na sidebar
- Ou proposals aparecem mas IDs estão undefined

---

## 🧪 Testes para Fazer

### Teste 1: Verificar se Extension Carrega

**No Extension Development Host:**
1. Pressione `Ctrl+Shift+P`
2. Digite: `Developer: Show Running Extensions`
3. Procure por `contextpilot` na lista
4. **Status deve ser:** ✅ Activated

**Se NÃO aparecer:**
- Extension não está ativando
- Check `extension/out/extension.js` existe
- Check erros de compilação

---

### Teste 2: Forçar Refresh

**Na sidebar ContextPilot:**
1. Click com botão direito em "CHANGE PROPOSALS"
2. Se tiver opção "Refresh", click
3. Ou pressione `Ctrl+Shift+P` → `ContextPilot: Refresh Status`

**Deve aparecer proposals na lista**

---

### Teste 3: Console Logs

**Abra Developer Console (`Ctrl+Shift+I`):**

**Procure por:**
```
[ContextPilot] Extension activated
[ContextPilot] Initialized with URL: https://contextpilot-backend...
[ContextPilot] Attempting to connect
```

**Se NÃO aparecer:**
- Extension não está ativando
- Recompile: `cd extension && npm run compile`
- Reload window: `Ctrl+Shift+P` → `Developer: Reload Window`

**Se aparecer só "Failed to connect":**
- Copie a mensagem de erro completa
- Pode ser timeout, SSL, ou network issue

---

### Teste 4: Manual Connect

**Se extension não conectou automaticamente:**

1. Pressione `Ctrl+Shift+P`
2. Digite: `ContextPilot: Connect to Backend`
3. Execute o comando
4. Aguarde 10 segundos (cold start)
5. Check console para logs

---

### Teste 5: Verificar URL Configurada

**No Extension Development Host:**
1. Pressione `Ctrl+Shift+P`
2. Digite: `Preferences: Open Settings (UI)`
3. Busque por: `contextpilot`
4. Verifique: `Contextpilot: Api Url`
5. **Deve ser:** `https://contextpilot-backend-898848898667.us-central1.run.app`

**Se for `http://localhost:8000`:**
- Mude manualmente para cloud URL
- Reload window
- Test again

---

## 🔧 Soluções Rápidas

### Solução 1: Limpar Cache da Extension

```bash
# Remover cache compilado
cd /home/fsegall/Desktop/New_Projects/google-context-pilot/extension
rm -rf out/
npm run compile

# Reload window e pressionar F5
```

### Solução 2: Forçar Cloud URL no Código

No arquivo `extension/src/extension.ts`, linha 19, substituir:
```typescript
const apiUrl = config.get<string>('apiUrl', 'https://contextpilot-backend-898848898667.us-central1.run.app');
```

Para:
```typescript
const apiUrl = 'https://contextpilot-backend-898848898667.us-central1.run.app'; // Force cloud
```

### Solução 3: Test via Command Palette

```
Ctrl+Shift+P → ContextPilot: View Change Proposals
```

Se funcionar, problema é na sidebar rendering.

---

## 📋 Checklist de Debug

Marque o que já testou:

**Extension Loading:**
- [ ] Extension aparece em "Running Extensions"
- [ ] Console mostra "Extension activated"
- [ ] Sidebar mostra ícone rocket

**Connection:**
- [ ] Console mostra "Attempting to connect"
- [ ] Console mostra "Connect response: 200"
- [ ] Status bar mostra "ContextPilot"

**Proposals:**
- [ ] Console mostra "Fetching proposals"
- [ ] Console mostra "Fetched X proposals"
- [ ] Console mostra "Creating item with ID: spec-..."
- [ ] Sidebar mostra proposals

**Cloud Verification:**
- [x] Cloud Run logs show requests ✅
- [x] Backend responds to curl ✅
- [x] Proposals exist in backend ✅

---

## 🎯 Próximo Passo

**Se nada disso funcionar:**

Vamos criar uma **versão simplificada** da extension que apenas:
1. Conecta ao cloud
2. Lista proposals
3. Mostra diff
4. Aprova/rejeita

**Sem complexidade extra.**

---

**Por favor, me diga:**
1. Extension aparece em "Running Extensions"? (Ctrl+Shift+P → Show Running Extensions)
2. Console mostra ALGUMA coisa ao abrir? (qualquer log)
3. Sidebar mostra o ícone rocket?

**Isso vai me ajudar a diagnosticar! 🔍**

