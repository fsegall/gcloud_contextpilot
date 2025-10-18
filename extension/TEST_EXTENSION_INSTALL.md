# Testing ContextPilot Extension Installation

## Problem
Extension works in Extension Development Host but not when installed via `.vsix`

## Debugging Steps

### 1. Check if extension is loaded

1. Install extension:
   ```bash
   cursor --install-extension contextpilot-v0.2.1-FINAL-HACKATHON.vsix
   ```

2. Restart Cursor completely (close all windows)

3. Open Cursor and check:
   - Command Palette: `Developer: Show Running Extensions`
   - Look for "ContextPilot" in the list

### 2. Check extension logs

1. Command Palette: `Developer: Open Extension Logs`
2. Select "ContextPilot" from dropdown
3. Look for errors or activation messages

### 3. Check activation events

The extension should activate:
- `onStartupFinished` - automatically on Cursor start
- When any `contextpilot.*` command is invoked

### 4. Verify package.json

```json
{
  "main": "./out/extension.js",  // Must point to compiled JS
  "activationEvents": [
    "onStartupFinished"
  ]
}
```

### 5. Check compiled output

```bash
ls -la extension/out/
# Should see:
# - extension.js (main entry point)
# - commands/index.js
# - services/contextpilot.js
# - views/*.js
```

### 6. Test with minimal extension

If still not working, try installing a minimal test version:

```bash
cd extension
npx @vscode/vsce package --out test-minimal.vsix
cursor --uninstall-extension livresoltech.contextpilot
cursor --install-extension test-minimal.vsix
```

### 7. Check Cursor-specific issues

Cursor may have different behavior than VS Code:

1. Check extensions directory:
   ```bash
   ls -la ~/.cursor/extensions/
   ```

2. Look for ContextPilot installation:
   ```bash
   ls -la ~/.cursor/extensions/livresoltech.contextpilot-*
   ```

3. Check if package.json exists:
   ```bash
   cat ~/.cursor/extensions/livresoltech.contextpilot-*/package.json
   ```

### 8. Common Issues

**Issue**: Extension not showing in Command Palette
- **Fix**: Restart Cursor completely
- **Fix**: Run `Developer: Reload Window`

**Issue**: Commands registered but don't execute
- **Fix**: Check extension output logs for errors
- **Fix**: Verify `extension.js` exists in `out/` folder

**Issue**: Extension shows error about missing modules
- **Fix**: Ensure all dependencies in `node_modules` are bundled
- **Fix**: Consider using webpack to bundle extension

### 9. Alternative: Bundle with Webpack

If the issue persists, bundle the extension:

```bash
cd extension
npm install --save-dev webpack webpack-cli ts-loader
```

Create `webpack.config.js`:
```javascript
const path = require('path');

module.exports = {
  target: 'node',
  entry: './src/extension.ts',
  output: {
    path: path.resolve(__dirname, 'out'),
    filename: 'extension.js',
    libraryTarget: 'commonjs2'
  },
  externals: {
    vscode: 'commonjs vscode'
  },
  resolve: {
    extensions: ['.ts', '.js']
  },
  module: {
    rules: [{ test: /\.ts$/, use: 'ts-loader' }]
  }
};
```

Then package:
```bash
npx webpack
npx @vscode/vsce package
```

### 10. Final Test

Install fresh:
```bash
# Completely remove old version
cursor --uninstall-extension livresoltech.contextpilot
rm -rf ~/.cursor/extensions/livresoltech.contextpilot-*

# Install new version
cursor --install-extension contextpilot-v0.2.1-FINAL-HACKATHON.vsix

# Restart Cursor
# Check: Cmd+Shift+P → "ContextPilot"
```

---

## Current Status

- ✅ Extension compiles without errors
- ✅ VSIX packages successfully
- ✅ Works in Extension Development Host
- ❌ Doesn't work when installed via VSIX in Cursor

**Next**: Try each debugging step above to identify root cause




