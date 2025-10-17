#!/bin/bash

# ContextPilot - GitHub Release Creator
# By Livre Solutions

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║       📦 ContextPilot - GitHub Release Creator             ║"
echo "║              By Livre Solutions                            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Verificar se gh está instalado
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) não encontrado!"
    echo "   Instale com: sudo snap install gh"
    exit 1
fi

# Verificar autenticação
echo "🔐 Verificando autenticação GitHub..."
if ! gh auth status &> /dev/null; then
    echo "⚠️  Não está autenticado no GitHub."
    echo ""
    echo "Vamos fazer login agora..."
    echo ""
    gh auth login
    echo ""
fi

echo "✅ Autenticado no GitHub!"
echo ""

# Variáveis
VERSION="v0.1.0"
VSIX_FILE="extension/contextpilot-0.1.0.vsix"
RELEASE_NOTES="docs/RELEASE_NOTES_v0.1.0.md"

# Verificar se o .vsix existe
if [ ! -f "$VSIX_FILE" ]; then
    echo "❌ Arquivo $VSIX_FILE não encontrado!"
    echo "   Execute: cd extension && npx vsce package"
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📦 Criando release $VERSION..."
echo ""

# Criar release notes se não existir
if [ ! -f "$RELEASE_NOTES" ]; then
    cat > "$RELEASE_NOTES" << 'RELEASE_EOF'
# 🎉 ContextPilot v0.1.0 - Beta Launch

**By Livre Solutions**

## 🚀 First Public Release!

ContextPilot is an AI-powered development assistant with multi-agent system and gamification rewards.

### ✨ Features

#### 🤖 Multi-Agent System
- **Spec Agent**: Automatically generates and maintains documentation
- **Git Agent**: Intelligent semantic commits with conventional format
- **Context Agent**: Real-time project analysis and insights
- **Coach Agent**: Personalized development tips and guidance
- **Milestone Agent**: Progress tracking and goal management

#### 🎮 Gamification & Rewards
- **CPT Tokens**: Earn ContextPilot Tokens for productive actions
- **Achievements**: Unlock badges for milestones and streaks
- **Daily Streaks**: Build consistent development habits
- **Leaderboards**: Compete with other developers worldwide

#### 📊 Project Management
- **Change Proposals**: AI-generated code change suggestions
- **Approval Workflow**: Review and approve proposals with 1 click
- **Automatic Git Commits**: Local commits with semantic messages
- **Context Tracking**: Keep your project scope and goals aligned

### 📥 Installation

#### Option 1: From Release (Recommended for Beta)
1. Download `contextpilot-0.1.0.vsix` from this release
2. Open VS Code/Cursor
3. Go to Extensions (Ctrl+Shift+X)
4. Click "..." menu → "Install from VSIX..."
5. Select the downloaded file

#### Option 2: Via Command Line
```bash
code --install-extension contextpilot-0.1.0.vsix
```

### 🔧 Configuration

After installation, configure your backend API URL in settings:

```json
{
  "contextpilot.apiUrl": "https://contextpilot-backend-581368740395.us-central1.run.app"
}
```

### 🎯 Quick Start

1. Open any project in VS Code/Cursor
2. Look for the ContextPilot icon (🚀) in the sidebar
3. Connect to backend (automatic)
4. View pending proposals
5. Approve proposals to earn +10 CPT tokens!

### 🛡️ Security & Privacy

- Rate limiting: 100 requests/hour per IP
- Abuse detection active
- All code stays on your machine (local Git)
- Backend uses Google Cloud Platform with enterprise-grade security

### 🐛 Known Issues

- Budget alerts not configured (manual setup required)
- Extension publisher name may differ (will be "livresolutions" on Marketplace)

### 📚 Documentation

- [README](https://github.com/fsegall/google-context-pilot/blob/main/extension/README.md)
- [Security Guide](https://github.com/fsegall/google-context-pilot/blob/main/SECURITY.md)
- [Roadmap](https://github.com/fsegall/google-context-pilot/blob/main/ROADMAP.md)

### 🎉 What's Next?

- VS Code Marketplace publication
- Blockchain integration (Polygon)
- Enhanced AI capabilities
- Team collaboration features
- Custom agent creation

### 🙏 Feedback

We'd love to hear from you!

- 🐛 **Bugs**: [GitHub Issues](https://github.com/fsegall/google-context-pilot/issues)
- 💡 **Ideas**: [Discussions](https://github.com/fsegall/google-context-pilot/discussions)
- 📧 **Email**: hello@livre.solutions

### 🏢 About Livre Solutions

ContextPilot is developed by [Livre Solutions](https://livre.solutions), focused on creating innovative AI-powered tools for developers.

---

**Made with ❤️ by Livre Solutions for developers who love productivity and gamification!**

**#AI #VSCode #Productivity #Gamification #Web3 #GoogleCloud**
RELEASE_EOF
    echo "✅ Release notes criadas: $RELEASE_NOTES"
fi

# Criar release no GitHub
echo "📤 Publicando release no GitHub..."
echo ""

gh release create "$VERSION" \
  "$VSIX_FILE" \
  --title "🚀 ContextPilot $VERSION - Beta Launch by Livre Solutions" \
  --notes-file "$RELEASE_NOTES" \
  --draft=false \
  --prerelease=false \
  --repo fsegall/google-context-pilot

if [ $? -eq 0 ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🎉 SUCESSO! Release publicado!"
    echo ""
    echo "📍 Release URL:"
    echo "   https://github.com/fsegall/google-context-pilot/releases/tag/$VERSION"
    echo ""
    echo "📥 Download direto do .vsix:"
    echo "   https://github.com/fsegall/google-context-pilot/releases/download/$VERSION/contextpilot-0.1.0.vsix"
    echo ""
    echo "💡 Compartilhe com usuários:"
    echo "   1. Download: [link acima]"
    echo "   2. Instalar: code --install-extension contextpilot-0.1.0.vsix"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🚀 Extension disponível para o mundo! 🎉"
    echo ""
else
    echo ""
    echo "❌ Erro ao criar release. Verifique:"
    echo "   • Autenticação GitHub (gh auth status)"
    echo "   • Nome do repositório correto"
    echo "   • Tag $VERSION não existe ainda"
    echo ""
fi

