#!/bin/bash
# Reinstalação LIMPA da extensão ContextPilot
# Este script remove completamente a versão antiga e instala a nova

set -e

echo "🧹 REINSTALAÇÃO LIMPA - ContextPilot Extension"
echo "=============================================="
echo ""

# 1. Desinstalar versão antiga
echo "📦 Passo 1: Removendo versão antiga..."
code --uninstall-extension livresoltech.contextpilot 2>/dev/null || echo "   (Nenhuma versão anterior encontrada)"
echo ""

# 2. Limpar cache do VSCode
echo "🗑️  Passo 2: Limpando cache do VSCode..."
rm -rf ~/.vscode/extensions/livresoltech.contextpilot-* 2>/dev/null || true
rm -rf ~/.config/Code/User/workspaceStorage/*/livresoltech.contextpilot-* 2>/dev/null || true
echo "   ✅ Cache limpo"
echo ""

# 3. Limpar configurações antigas (backup primeiro)
echo "⚙️  Passo 3: Verificando configurações..."
SETTINGS_FILE="$HOME/.config/Code/User/settings.json"
if [ -f "$SETTINGS_FILE" ]; then
    if grep -q "contextpilot.apiUrl.*localhost" "$SETTINGS_FILE" 2>/dev/null; then
        echo "   ⚠️  AVISO: Encontrada configuração antiga no settings.json"
        echo "   📝 Backup criado em: ${SETTINGS_FILE}.backup"
        cp "$SETTINGS_FILE" "${SETTINGS_FILE}.backup"
        echo "   "
        echo "   ⚠️  AÇÃO NECESSÁRIA: Remova ou atualize esta linha no settings.json:"
        echo '   "contextpilot.apiUrl": "http://localhost:8000"'
        echo "   Para:"
        echo '   "contextpilot.apiUrl": "https://contextpilot-backend-581368740395.us-central1.run.app"'
        echo ""
    else
        echo "   ✅ Configurações OK"
    fi
fi
echo ""

# 4. Instalar nova versão
echo "📥 Passo 4: Instalando nova versão..."
cd "$(dirname "$0")/extension"
if [ ! -f "contextpilot-0.2.1.vsix" ]; then
    echo "❌ Erro: Arquivo contextpilot-0.2.1.vsix não encontrado!"
    exit 1
fi

code --install-extension contextpilot-0.2.1.vsix --force
echo "   ✅ Instalação concluída"
echo ""

# 5. Verificações finais
echo "🔍 Passo 5: Verificações finais..."
echo "   Backend GCP: https://contextpilot-backend-581368740395.us-central1.run.app"

# Testar backend
if curl -s -f "https://contextpilot-backend-581368740395.us-central1.run.app/health" > /dev/null 2>&1; then
    echo "   ✅ Backend online e acessível"
else
    echo "   ❌ Backend não acessível (verifique sua conexão)"
fi
echo ""

echo "✅ INSTALAÇÃO COMPLETA!"
echo ""
echo "🔄 PRÓXIMOS PASSOS:"
echo "   1. Feche TODAS as janelas do VSCode"
echo "   2. Abra o VSCode novamente"
echo "   3. Pressione Ctrl+Shift+P"
echo "   4. Digite: 'Developer: Reload Window'"
echo "   5. Abra a sidebar do ContextPilot (ícone do foguete)"
echo ""
echo "🐛 SE AINDA NÃO FUNCIONAR:"
echo "   1. Abra: View → Output"
echo "   2. Selecione 'ContextPilot' no dropdown"
echo "   3. Copie os logs e envie para análise"
echo ""
echo "🌐 URL configurada: https://contextpilot-backend-581368740395.us-central1.run.app"
echo ""










