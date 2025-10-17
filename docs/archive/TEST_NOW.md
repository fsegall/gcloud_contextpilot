# ⚡ TESTE AGORA - 3 Passos Simples

## 1️⃣ Abrir Extension (30 segundos)

```bash
cd /home/fsegall/Desktop/New_Projects/google-context-pilot/extension
cursor .
```

**No Cursor:**
- Pressione **F5**
- Nova janela abre COM workspace google-context-pilot
- Aguarde "ContextPilot extension is now active!"

## 2️⃣ Aprovar Proposal (30 segundos)

**Na Extension Development Host:**
1. Sidebar → Ícone 🚀 (ContextPilot)
2. Expanda **"Change Proposals"**
3. Clique em qualquer proposal (ex: "Docs issue: ARCHITECTURE.md")
4. Clique **"Approve & Commit"**
5. Aguarde notificação: "✅ Committed: abc1234"

## 3️⃣ Verificar (30 segundos)

```bash
cd /home/fsegall/Desktop/New_Projects/google-context-pilot

# Ver commit
git log -1

# Ver arquivo criado
ls -la ARCHITECTURE.md
cat ARCHITECTURE.md | head -30
```

---

## 🎉 O que você vai ver

### No Cursor:
```
Applying proposal changes...
Committing changes...
✅ Docs issue: ARCHITECTURE.md - Committed: abc1234
```

### No Terminal:
```bash
$ git log -1
commit abc1234 (HEAD -> main)
Author: fsegall
Date: Thu Oct 16 2025

feat(contextpilot): Docs issue: ARCHITECTURE.md

ARCHITECTURE.md not found

Applied by ContextPilot Extension.
Proposal-ID: spec-missing_doc-1760645282
Agent: spec
```

### Arquivo criado:
```markdown
# ContextPilot Architecture

## Overview
[5000+ caracteres de documentação profissional]
[Gerado pelo Gemini AI]
[Diagramas mermaid, seções estruturadas]
```

---

## ⚡ Se der algum erro

### "No workspace folder open"
**Na Extension Host:** File → Open Folder → Selecione `google-context-pilot`

### "Failed to approve"
**Verifique:** Cloud Run está respondendo?
```bash
curl https://contextpilot-backend-581368740395.us-central1.run.app/health
```

### "Git command failed"
**Verifique:** Está em um repositório Git?
```bash
cd /home/fsegall/Desktop/New_Projects/google-context-pilot
git status
```

---

## 🎯 Tempo Total: 2 minutos

✅ Extension abre com workspace
✅ Proposal aprovada
✅ Commit feito automaticamente
✅ Arquivo criado com conteúdo do Gemini

**Pronto para demo!** 🚀
