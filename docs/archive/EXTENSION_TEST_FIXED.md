# 🔧 Como Testar a Extension Corretamente

## ❌ Problema: "No workspace folder open"

A Extension Development Host abre **sem workspace**. Você precisa abrir o workspace do projeto dentro dela!

## ✅ Solução: Abrir Workspace na Extension Host

### Método 1: Abrir automaticamente (Recomendado)

1. **No Cursor principal**, abra o arquivo `extension/.vscode/launch.json`
2. Adicione a configuração do workspace:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Run Extension",
      "type": "extensionHost",
      "request": "launch",
      "args": [
        "--extensionDevelopmentPath=${workspaceFolder}",
        "${workspaceFolder}/.."  // ← ADICIONAR: Abre o workspace pai
      ],
      "outFiles": [
        "${workspaceFolder}/out/**/*.js"
      ],
      "preLaunchTask": "${defaultBuildTask}"
    }
  ]
}
```

3. **Salve** e pressione **F5** novamente
4. A Extension Development Host vai abrir COM o workspace do google-context-pilot

---

### Método 2: Abrir manualmente (Mais simples)

1. Pressione **F5** para abrir Extension Development Host
2. **Na janela nova** (Extension Host):
   - Menu: `File` → `Open Folder`
   - Navegue até: `/home/fsegall/Desktop/New_Projects/google-context-pilot`
   - Clique **Open**
3. Aguarde a extension ativar
4. Abra a sidebar do ContextPilot
5. Agora pode aprovar proposals!

---

### Método 3: Usar workspace atual (Mais rápido)

Se você está no workspace `google-context-pilot` no Cursor principal:

1. **Ctrl+Shift+P** → `Developer: Reload Window`
2. Isso vai recarregar a extension no workspace atual
3. Teste direto sem abrir Extension Host

**IMPORTANTE:** Este método só funciona se você instalou a extension globalmente.

---

## 🎯 Teste Correto (Passo a Passo)

### 1. Preparar Extension
```bash
cd /home/fsegall/Desktop/New_Projects/google-context-pilot/extension
cursor .
```

### 2. Abrir launch.json e adicionar workspace path

```json
"args": [
  "--extensionDevelopmentPath=${workspaceFolder}",
  "/home/fsegall/Desktop/New_Projects/google-context-pilot"  // ← workspace path
]
```

### 3. Pressionar F5

Nova janela abre COM workspace

### 4. Verificar
- Sidebar: Ver ContextPilot icon
- Proposals: Ver lista
- Terminal: `pwd` deve mostrar `/home/fsegall/Desktop/New_Projects/google-context-pilot`

### 5. Aprovar Proposal
- Clique em proposal
- "Approve & Commit"
- ✅ Deve funcionar!

---

## 🐛 Troubleshooting

### "No workspace folder open" ainda aparece

**Solução A: Abrir folder manualmente**
```
Extension Host → File → Open Folder → google-context-pilot
```

**Solução B: Verificar launch.json**
```bash
cat extension/.vscode/launch.json
# Deve ter "args" com workspace path
```

**Solução C: Testar no workspace atual**
```
Ctrl+Shift+P → Developer: Reload Window
```

---

## ✅ Quando Funcionar

Você vai ver:
```
1. Progress: "Applying proposal changes..."
2. Progress: "Committing changes..."
3. Success: "✅ Docs issue: ARCHITECTURE.md - Committed: abc1234"
4. Arquivo criado no workspace
5. git log -1 mostra commit do ContextPilot
```

---

**Próximo:** Teste com o método que preferir! 🚀
