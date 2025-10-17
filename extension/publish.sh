#!/bin/bash

# ContextPilot - Script de Publicação no VS Code Marketplace
# By Livre Solutions

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║       🚀 ContextPilot Publisher - Livre Solutions          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Verificar se estamos no diretório correto
if [ ! -f "package.json" ]; then
    echo "❌ Erro: Execute este script no diretório extension/"
    exit 1
fi

# Extrair informações do package.json
PUBLISHER=$(grep '"publisher"' package.json | cut -d'"' -f4)
NAME=$(grep '"name"' package.json | head -1 | cut -d'"' -f4)
VERSION=$(grep '"version"' package.json | head -1 | cut -d'"' -f4)

echo "📦 Extension: $NAME"
echo "🏢 Publisher: $PUBLISHER"
echo "🔖 Version: $VERSION"
echo ""

# Verificar se vsce está instalado
if ! command -v vsce &> /dev/null; then
    echo "⚠️  vsce não encontrado. Instalando..."
    npm install -g @vscode/vsce
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Verificar se já está logado
echo "🔐 Verificando login..."
if vsce ls-publishers 2>/dev/null | grep -q "$PUBLISHER"; then
    echo "✅ Já está logado como $PUBLISHER"
else
    echo "⚠️  Não está logado. Fazendo login..."
    echo ""
    echo "Cole o Personal Access Token (PAT) do Azure DevOps:"
    vsce login "$PUBLISHER"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Perguntar confirmação
read -p "🚀 Publicar $NAME@$VERSION no marketplace? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Publicação cancelada."
    exit 1
fi

echo ""
echo "📤 Publicando..."
echo ""

# Publicar
if vsce publish; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🎉 SUCESSO! Extension publicada!"
    echo ""
    echo "📍 Marketplace URL:"
    echo "   https://marketplace.visualstudio.com/items?itemName=${PUBLISHER}.${NAME}"
    echo ""
    echo "💡 Instalar via VS Code/Cursor:"
    echo "   Ctrl+Shift+X → Buscar \"ContextPilot\""
    echo ""
    echo "⏳ Pode levar alguns minutos para aparecer no marketplace."
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    echo ""
    echo "❌ Erro na publicação. Verifique:"
    echo "   • Personal Access Token válido"
    echo "   • Publisher '$PUBLISHER' existe"
    echo "   • Conexão com internet"
    echo ""
    echo "📚 Guia: docs/PUBLISH_GUIDE.md"
fi

