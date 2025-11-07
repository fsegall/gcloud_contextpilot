#!/bin/bash
# Helper script to activate the .venv for this project

# Deactivate any existing venv
deactivate 2>/dev/null || true

# Activate the correct .venv
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
source .venv/bin/activate

echo "✅ Activated .venv at: $VIRTUAL_ENV"
echo "Python: $(which python3)"
echo "Pytest: $(which pytest)"

