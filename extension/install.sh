#!/bin/bash

# ContextPilot Extension Installer
# Works for both VS Code and Cursor

echo "🚀 Installing ContextPilot Extension..."

VSIX_FILE="contextpilot-BUNDLED-v0.2.1.vsix"

if [ ! -f "$VSIX_FILE" ]; then
    echo "❌ Error: $VSIX_FILE not found!"
    exit 1
fi

# Try VS Code first
if command -v code &> /dev/null; then
    echo "📦 Installing for VS Code..."
    code --install-extension "$VSIX_FILE"
fi

# Try Cursor
if command -v cursor &> /dev/null; then
    echo "📦 Installing for Cursor..."
    # Manual installation for Cursor (bypasses alias issues)
    TEMP_DIR=$(mktemp -d)
    unzip -q "$VSIX_FILE" -d "$TEMP_DIR"
    INSTALL_DIR="$HOME/.cursor/extensions/livresoltech.contextpilot-0.2.1"
    mkdir -p "$INSTALL_DIR"
    cp -r "$TEMP_DIR/extension/"* "$INSTALL_DIR/"
    rm -rf "$TEMP_DIR"
    echo "✅ ContextPilot installed to: $INSTALL_DIR"
fi

echo ""
echo "✅ Installation complete!"
echo "📝 Next steps:"
echo "   1. Restart VS Code/Cursor completely"
echo "   2. Press Cmd+Shift+P (or Ctrl+Shift+P)"
echo "   3. Type 'ContextPilot: Start Agent Retrospective'"
echo ""
echo "🔧 Configure backend URL in settings:"
echo "   ContextPilot › API URL: https://contextpilot-backend-581368740395.us-central1.run.app"

