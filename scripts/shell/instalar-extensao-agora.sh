#!/bin/bash
# Script de instalação rápida da extensão ContextPilot
# Fase Final - Conecta com GCP

set -e

echo "🚀 Instalando ContextPilot Extension v0.2.1..."
echo "📡 Configurado para conectar ao GCP"
echo ""

# Navegar para a pasta da extensão
cd "$(dirname "$0")/extension"

# Verificar se o arquivo existe
if [ ! -f "contextpilot-0.2.1.vsix" ]; then
    echo "❌ Erro: Arquivo contextpilot-0.2.1.vsix não encontrado!"
    exit 1
fi

# Instalar a extensão
echo "📦 Instalando extensão..."
code --install-extension contextpilot-0.2.1.vsix --force

echo ""
echo "✅ Instalação concluída!"
echo ""
echo "⚡ Próximos passos:"
echo "   1. Recarregue o VSCode (Ctrl+Shift+P → 'Developer: Reload Window')"
echo "   2. Abra a sidebar do ContextPilot (ícone do foguete)"
echo "   3. A conexão com o GCP deve acontecer automaticamente"
echo ""
echo "🌐 Backend URL: https://contextpilot-backend-581368740395.us-central1.run.app"
echo "📊 Status: Online e funcional"
echo ""
echo "🔍 Para ver logs: View → Output → Selecione 'ContextPilot'"
echo ""


