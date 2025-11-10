#!/bin/bash
# Script para testar compilação da extensão

echo "🔍 Testando compilação da extensão..."
cd "$(dirname "$0")"

echo ""
echo "1️⃣ Compilando TypeScript..."
npm run compile 2>&1 | tee compile.log

if [ $? -eq 0 ]; then
    echo "✅ TypeScript compilado com sucesso"
else
    echo "❌ Erro na compilação TypeScript"
    exit 1
fi

echo ""
echo "2️⃣ Compilando com Webpack..."
npm run webpack 2>&1 | tee webpack.log

if [ $? -eq 0 ]; then
    echo "✅ Webpack compilado com sucesso"
    echo ""
    echo "✅✅✅ Extensão pronta para teste!"
    echo ""
    echo "Próximos passos:"
    echo "1. Recarregue a janela do VS Code (Ctrl+Shift+P → 'Developer: Reload Window')"
    echo "2. Abra o Console do Extension Host (Ctrl+Shift+P → 'Developer: Toggle Developer Tools' → aba 'Console')"
    echo "3. Procure por logs '[ContextPilot]' para ver quais providers foram inicializados"
    echo "4. Verifique se o dashboard aparece na barra lateral"
else
    echo "❌ Erro na compilação Webpack"
    echo ""
    echo "Verifique os erros em webpack.log"
    exit 1
fi

