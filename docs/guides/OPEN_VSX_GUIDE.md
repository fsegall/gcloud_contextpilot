# 🚀 Open VSX Publishing Guide - ContextPilot

## Por que Open VSX?

- ✅ **Sem Azure DevOps** (não precisa de PAT complicado)
- ✅ **Login com GitHub** (simples e rápido)
- ✅ **Processo de 5 minutos**
- ✅ **Funciona com VS Codium, Gitpod, Theia**
- ✅ **Alternativa ao Marketplace da Microsoft**

---

## 📋 Passo a Passo (5 minutos)

### 1. Criar Conta no Open VSX

🔗 https://open-vsx.org

1. Click em **"Sign in"** ou **"Publish Extensions"**
2. **Login com GitHub** (autorizar Open VSX)
3. Pronto! Conta criada automaticamente

---

### 2. Gerar Access Token

1. Após login, vá para: https://open-vsx.org/user-settings/tokens
2. Click **"Create new Access Token"**
3. Nome: `ContextPilot Publisher`
4. **Copiar o token** (guarde em local seguro)

---

### 3. Criar Namespace (Publisher)

1. Vá para: https://open-vsx.org/user-settings/namespaces
2. Click **"Create namespace"**
3. Preencher:
   ```
   Name: livresolutions (ou livre-solutions)
   Display Name: Livre Solutions
   Description: AI-powered development tools
   Website: https://livre.solutions
   ```
4. Confirmar

---

### 4. Publicar a Extension

No terminal:

```bash
cd /home/fsegall/Desktop/New_Projects/google-context-pilot/extension

# Instalar ovsx CLI (se não tiver)
npm install -g ovsx

# Login (usar o token do passo 2)
npx ovsx publish contextpilot-0.1.0.vsix -p YOUR_ACCESS_TOKEN

# Ou especificar namespace
npx ovsx publish -p YOUR_TOKEN --packagePath contextpilot-0.1.0.vsix
```

---

## ✅ Resultado

Após publicar, a extension estará disponível em:

🔗 https://open-vsx.org/extension/livresolutions/contextpilot

---

## 🎯 Instalação (para usuários)

### VS Codium / GitPod / Theia:
```
Funciona automaticamente na busca de extensions!
```

### VS Code (oficial):
```
Precisa configurar para usar Open VSX:
1. Settings → Extensions
2. Adicionar: https://open-vsx.org/vscode/gallery
3. Ou instalar .vsix manualmente
```

---

## 📊 Comparação: Open VSX vs Microsoft Marketplace

| Feature | Open VSX | MS Marketplace |
|---------|----------|----------------|
| Login | ✅ GitHub | ❌ Azure DevOps |
| Token | ✅ Simples | ❌ Complicado |
| Tempo setup | ✅ 5 min | ❌ 30+ min |
| Usuários | 🟡 Menos | ✅ Mais |
| VS Code oficial | ❌ Não por padrão | ✅ Sim |
| VS Codium | ✅ Sim | ❌ Não |
| Custo | ✅ Grátis | ✅ Grátis |

---

## 💡 Estratégia Recomendada

**Usar AMBOS:**

1. **Open VSX** (fácil, rápido)
   - Para VS Codium users
   - Para demonstração
   - Sem dor de cabeça

2. **Microsoft Marketplace** (depois)
   - Para maximizar usuários
   - Quando resolver Azure
   - Sem pressa

3. **GitHub Releases** (sempre)
   - Backup
   - Beta testers
   - Download direto

---

## 🆘 Troubleshooting

### "Namespace already exists"
→ Usar outro nome: `livre-solutions`, `livresoltech`, `contextpilot`

### "Token invalid"
→ Gerar novo token em: https://open-vsx.org/user-settings/tokens

### "Package validation failed"
→ Verificar package.json:
```json
{
  "publisher": "livresolutions",  // deve bater com namespace
  "name": "contextpilot",
  "version": "0.1.0"
}
```

---

## 📚 Links Úteis

- **Open VSX Homepage:** https://open-vsx.org
- **Publishing Guide:** https://github.com/eclipse/openvsx/wiki/Publishing-Extensions
- **CLI Docs:** https://github.com/eclipse/openvsx/wiki/CLI
- **Namespace Management:** https://open-vsx.org/user-settings/namespaces

---

## 🎉 Checklist Final

Antes de publicar, verificar:

- [ ] package.json tem `publisher` correto
- [ ] .vsix está compilado e testado
- [ ] README.md está completo
- [ ] Icon está incluído (assets/icon.png)
- [ ] LICENSE está presente
- [ ] Namespace criado no Open VSX
- [ ] Access token gerado

---

## 🚀 Comando Rápido (amanhã)

```bash
cd extension

# Se precisar recompilar
npm run compile && npx vsce package

# Publicar no Open VSX
npx ovsx publish contextpilot-0.1.0.vsix -p YOUR_TOKEN
```

**Tempo estimado: 5 minutos!** ⚡

---

**Made with ❤️ by Livre Solutions**

**Boa sorte amanhã! Vai ser moleza comparado com Azure! 😊**

