#!/bin/bash
# Ajuda rápida para subir o backend localmente

set -e

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
BACKEND_DIR="$ROOT_DIR/back-end"

echo "🛠️  ContextPilot - Deploy local (FastAPI + Uvicorn)"
echo "==================================================="
echo ""

if [ ! -d "$BACKEND_DIR" ]; then
    echo "❌ Pasta do backend não encontrada em $BACKEND_DIR"
    exit 1
fi

cd "$BACKEND_DIR"

echo "📦 Diretório: $BACKEND_DIR"
echo ""

if [ -f ".env" ]; then
    echo "🔑 Carregando variáveis de .env"
    # shellcheck disable=SC2046
    export $(grep -v '^#' .env | xargs)
else
    echo "⚠️  Nenhum .env encontrado. Continuando com variáveis padrão."
fi

echo "🚀 Iniciando uvicorn em modo reload (http://localhost:8000)"
echo ""

python3 -m uvicorn app.server:app --host 0.0.0.0 --port 8000 --reload

