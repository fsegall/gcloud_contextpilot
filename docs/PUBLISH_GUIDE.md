# 📦 Guia de Publicação - ContextPilot Extension

## 🎯 Objetivo

Publicar a extensão **ContextPilot by Livre Solutions** no VS Code Marketplace para instalação pública.

---

## 📋 Pré-requisitos Completos

### ✅ Já Preparado:
- [x] Extension empacotada (`contextpilot-0.1.0.vsix`)
- [x] README.md profissional
- [x] LICENSE.txt (MIT)
- [x] Icon profissional (512x512px PNG)
- [x] Banner (optional, mas recomendado)
- [x] Repositório GitHub público
- [x] package.json configurado com:
  - `displayName`: "ContextPilot by Livre Solutions"
  - `publisher`: "livresolutions"
  - `repository`: Link do GitHub
  - `icon`: "assets/icon.png"

### ⚠️ Falta Fazer:
- [ ] Criar conta Azure DevOps (Microsoft)
- [ ] Criar Publisher "livresolutions" verificado
- [ ] Gerar Personal Access Token (PAT)
- [ ] Publicar no marketplace

---

## 🚀 Passo a Passo Detalhado

### **Passo 1: Criar Conta Azure DevOps**

1. **Acesse:** https://dev.azure.com
2. **Login com Microsoft Account** (pode usar Gmail/GitHub)
3. **Criar nova organização** (ex: "livresolutions")
4. **Confirmar email** e ativar conta

---

### **Passo 2: Criar Publisher no Marketplace**

1. **Acesse:** https://marketplace.visualstudio.com/manage
2. **Login com a mesma conta Microsoft**
3. **Create Publisher:**
   ```
   Publisher Name: Livre Solutions
   Publisher ID: livresolutions (deve ser único!)
   Email: hello@livre.solutions
   Website: https://livre.solutions
   Description: AI-powered tools for developers
   ```
4. **Verificar email** (Microsoft envia confirmação)

---

### **Passo 3: Gerar Personal Access Token (PAT)**

1. **Acesse:** https://dev.azure.com/{sua-org}/_usersSettings/tokens
2. **New Token:**
   ```
   Name: ContextPilot Publisher
   Organization: All accessible organizations
   Expiration: 90 days (ou Custom)
   Scopes: Marketplace (Acquire & Manage)
   ```
3. **Copy token** (só aparece uma vez!)
4. **Salvar em local seguro** (vai usar no próximo passo)

---

### **Passo 4: Configurar vsce com o Token**

No terminal:

```bash
cd /home/fsegall/Desktop/New_Projects/google-context-pilot/extension

# Login com o publisher
npx vsce login livresolutions

# Vai pedir o Personal Access Token
# Cole o token que você copiou no Passo 3
```

---

### **Passo 5: Publicar a Extension**

```bash
cd /home/fsegall/Desktop/New_Projects/google-context-pilot/extension

# Primeira publicação
npx vsce publish

# Se já existe no marketplace e quer atualizar:
npx vsce publish patch  # 0.1.0 → 0.1.1
npx vsce publish minor  # 0.1.0 → 0.2.0
npx vsce publish major  # 0.1.0 → 1.0.0
```

**Output esperado:**
```
Publishing livresolutions.contextpilot@0.1.0...
Successfully published livresolutions.contextpilot@0.1.0!
Your extension will live at https://marketplace.visualstudio.com/items?itemName=livresolutions.contextpilot (might take a few minutes to show up)
```

---

### **Passo 6: Verificar Publicação**

1. **Marketplace URL:**
   ```
   https://marketplace.visualstudio.com/items?itemName=livresolutions.contextpilot
   ```

2. **Instalar via VS Code/Cursor:**
   ```
   Ctrl+Shift+X → Buscar "ContextPilot"
   ```

3. **Verificar:**
   - [ ] README renderizado corretamente
   - [ ] Icon aparecendo
   - [ ] Banner (se tiver)
   - [ ] Link do GitHub funcionando
   - [ ] Instalação funcionando

---

## 🔄 Atualizações Futuras

### **Atualizar a Extension:**

```bash
cd extension

# 1. Fazer mudanças no código
npm run compile

# 2. Atualizar versão no package.json
# "version": "0.1.1"  (ou usar vsce publish patch)

# 3. Publicar atualização
npx vsce publish
```

**Usuários que já instalaram receberão update automático!**

---

## ⚠️ Troubleshooting

### **Erro: "Publisher 'livresolutions' not found"**
- **Solução:** Criar o publisher no marketplace primeiro (Passo 2)

### **Erro: "Extension not found in package.json"**
- **Solução:** Verificar que `publisher` no package.json é exatamente `livresolutions`

### **Erro: "Personal Access Token expired"**
- **Solução:** Gerar novo token no Azure DevOps e fazer login novamente

### **Erro: "README.md too large"**
- **Solução:** Marketplace tem limite de ~5MB. Nossa está OK (5.88KB)

---

## 📊 Pós-Publicação

### **Monitoramento:**

1. **Analytics do Marketplace:**
   - Installs/downloads
   - Rating/reviews
   - Countries
   - Trends

2. **GitHub Issues:**
   - Bugs reportados
   - Feature requests
   - User feedback

3. **GCP Monitoring:**
   - Backend usage
   - API calls
   - Costs

---

## 🎯 Checklist Final Antes de Publicar

- [ ] Testei a extension localmente
- [ ] README está completo e sem erros
- [ ] LICENSE.txt incluído
- [ ] Icon está na resolução correta (512x512px)
- [ ] package.json tem todas as informações corretas
- [ ] Repositório GitHub é público
- [ ] Backend GCP está deployado e funcionando
- [ ] Criei conta Azure DevOps
- [ ] Criei publisher "livresolutions"
- [ ] Gerei Personal Access Token
- [ ] Fiz login com `vsce login livresolutions`

---

## 🚀 Comando para Publicar (depois do setup)

```bash
cd /home/fsegall/Desktop/New_Projects/google-context-pilot/extension
npx vsce publish
```

---

## 📞 Suporte

Se tiver problemas:
- **Docs oficiais:** https://code.visualstudio.com/api/working-with-extensions/publishing-extension
- **vsce troubleshooting:** https://github.com/microsoft/vscode-vsce/issues
- **Azure DevOps support:** https://developercommunity.visualstudio.com/

---

## 🎉 Próximos Passos Pós-Launch

### **Marketing:**
1. Tweet sobre o launch
2. Post no LinkedIn (Livre Solutions)
3. Post no Dev.to / Medium
4. Reddit (r/vscode, r/programming)
5. Product Hunt launch

### **Engagement:**
1. Responder reviews
2. Fix bugs rapidamente
3. Adicionar features pedidas
4. Update semanal (changelog)

### **Growth:**
1. SEO no README (keywords)
2. Video demo no YouTube
3. Blog post técnico
4. Case studies de usuários

---

**Made with ❤️ by Livre Solutions**

