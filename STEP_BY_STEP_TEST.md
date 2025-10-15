# 🧪 Teste Passo a Passo - API Real

Testando funcionalidades REAIS da API, começando simples.

---

## 🎯 Abordagem

✅ Usar API existente (não mock)
✅ Testar neste próprio repositório
✅ Começar com 1 funcionalidade
✅ Evoluir organicamente

---

## 📋 Passo 1: Backend Rodando (2 min)

### Terminal 1: Backend
```bash
cd back-end
source .venv/bin/activate
python -m uvicorn app.server:app --reload --port 8000
```

✅ Deve aparecer: `Uvicorn running on http://127.0.0.1:8000`

### Teste Manual
Abrir: http://localhost:8000/docs

**Endpoints existentes para testar:**
- GET `/context` - Pegar contexto do workspace
- GET `/context/milestones` - Listar milestones
- POST `/commit` - Fazer commit manual
- GET `/coach` - Pegar dica do coach
- POST `/update` - Atualizar checkpoint

---

## 📋 Passo 2: Testar API com cURL (5 min)

### 2.1 - Health Check
```bash
curl http://localhost:8000/health
```

**Esperado**: `{"status":"ok","version":"2.0.0",...}`

### 2.2 - Get Context
```bash
curl "http://localhost:8000/context?workspace_id=default"
```

**Esperado**: JSON com checkpoint + history

### 2.3 - Fazer um Commit (API)
```bash
curl -X POST "http://localhost:8000/commit?message=Test%20commit&agent=manual&workspace_id=default"
```

**Esperado**: `{"status":"success","commit":"..."}`

Se funcionar ✅ = API está OK!

---

## 📋 Passo 3: Extension Chama API Real (10 min)

### 3.1 - Ajustar Extension para Usar `/context`

O endpoint `/context` já existe. Vamos fazer a extension chamar ele.

**Arquivo**: `extension/src/services/contextpilot.ts`

Adicionar método:
```typescript
async getContext(workspaceId: string = 'default'): Promise<any> {
  try {
    const response = await this.client.get('/context', {
      params: { workspace_id: workspaceId }
    });
    console.log('[ContextPilot] Context loaded:', response.data);
    return response.data;
  } catch (error) {
    console.error('Failed to get context:', error);
    return null;
  }
}
```

### 3.2 - Adicionar Comando: "Get Context"

**Arquivo**: `extension/src/commands/index.ts`

```typescript
export async function getContextCommand() {
  const service = getService();
  if (!service) {
    vscode.window.showErrorMessage('ContextPilot not initialized');
    return;
  }

  vscode.window.showInformationMessage('📦 Loading context...');
  
  const context = await service.getContext('default');
  
  if (context) {
    const checkpoint = context.checkpoint || {};
    const message = `
📦 Project: ${checkpoint.project_name || 'N/A'}
🎯 Goal: ${checkpoint.goal || 'N/A'}
📊 Status: ${checkpoint.current_status || 'N/A'}
🗓️ Milestones: ${(checkpoint.milestones || []).length}
    `.trim();
    
    vscode.window.showInformationMessage(message);
  } else {
    vscode.window.showErrorMessage('Failed to load context');
  }
}
```

### 3.3 - Registrar Comando

**Arquivo**: `extension/src/extension.ts`

```typescript
// Import
import { getContextCommand } from './commands';

// No activate(), adicionar:
context.subscriptions.push(
  vscode.commands.registerCommand('contextpilot.getContext', getContextCommand)
);
```

### 3.4 - Adicionar ao package.json

**Arquivo**: `extension/package.json`

```json
{
  "contributes": {
    "commands": [
      // ... outros comandos
      {
        "command": "contextpilot.getContext",
        "title": "ContextPilot: Get Context"
      }
    ]
  }
}
```

### 3.5 - Testar

1. Compile: `npm run compile`
2. Press F5 (Extension Development Host)
3. Cmd+Shift+P → "ContextPilot: Get Context"
4. Deve aparecer info box com dados do projeto

✅ Se funcionar = Extension conectada à API real!

---

## 📋 Passo 4: Fazer Commit Via Extension (15 min)

Agora vamos fazer um commit REAL neste repositório via extension.

### 4.1 - Adicionar Método `commitChanges`

**Arquivo**: `extension/src/services/contextpilot.ts`

```typescript
async commitChanges(message: string, agent: string = 'extension', workspaceId: string = 'default'): Promise<boolean> {
  try {
    const response = await this.client.post('/commit', null, {
      params: {
        message,
        agent,
        workspace_id: workspaceId
      }
    });
    
    console.log('[ContextPilot] Commit successful:', response.data);
    return response.status === 200;
  } catch (error) {
    console.error('Failed to commit:', error);
    return false;
  }
}
```

### 4.2 - Adicionar Comando: "Commit Context"

**Arquivo**: `extension/src/commands/index.ts`

```typescript
export async function commitContextCommand() {
  const service = getService();
  if (!service) {
    vscode.window.showErrorMessage('ContextPilot not initialized');
    return;
  }

  // Pedir mensagem ao usuário
  const message = await vscode.window.showInputBox({
    prompt: 'Enter commit message',
    placeHolder: 'Updated project context',
    value: 'Context update via ContextPilot extension'
  });

  if (!message) {
    return; // Usuário cancelou
  }

  vscode.window.showInformationMessage('💾 Committing context...');
  
  const success = await service.commitChanges(message, 'extension', 'default');
  
  if (success) {
    vscode.window.showInformationMessage('✅ Context committed successfully!');
  } else {
    vscode.window.showErrorMessage('❌ Failed to commit context');
  }
}
```

### 4.3 - Registrar Comando

**Arquivo**: `extension/src/extension.ts`

```typescript
import { getContextCommand, commitContextCommand } from './commands';

context.subscriptions.push(
  vscode.commands.registerCommand('contextpilot.getContext', getContextCommand),
  vscode.commands.registerCommand('contextpilot.commitContext', commitContextCommand)
);
```

### 4.4 - Adicionar ao package.json

```json
{
  "contributes": {
    "commands": [
      {
        "command": "contextpilot.commitContext",
        "title": "ContextPilot: Commit Context"
      }
    ]
  }
}
```

### 4.5 - Testar

1. Compile: `npm run compile`
2. F5 (Extension Development Host)
3. Faça uma mudança qualquer em um arquivo
4. Cmd+Shift+P → "ContextPilot: Commit Context"
5. Digite mensagem
6. Enter

**Verificar**:
```bash
cd back-end/.contextpilot/workspaces/default
git log --oneline -5
```

Deve ter um novo commit! ✅

---

## 📋 Passo 5: View Context na Sidebar (20 min)

Agora vamos mostrar o contexto do projeto na sidebar.

### 5.1 - Criar TreeDataProvider

**Arquivo**: `extension/src/views/context.ts` (novo)

```typescript
import * as vscode from 'vscode';
import { ContextPilotService } from '../services/contextpilot';

export class ContextTreeProvider implements vscode.TreeDataProvider<ContextItem> {
  private _onDidChangeTreeData = new vscode.EventEmitter<ContextItem | undefined>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  constructor(private service: ContextPilotService) {}

  refresh(): void {
    this._onDidChangeTreeData.fire(undefined);
  }

  getTreeItem(element: ContextItem): vscode.TreeItem {
    return element;
  }

  async getChildren(element?: ContextItem): Promise<ContextItem[]> {
    if (!element) {
      // Root level
      const context = await this.service.getContext('default');
      if (!context) {
        return [new ContextItem('No context loaded', '', vscode.TreeItemCollapsibleState.None)];
      }

      const checkpoint = context.checkpoint || {};
      return [
        new ContextItem(
          '📦 Project',
          checkpoint.project_name || 'N/A',
          vscode.TreeItemCollapsibleState.None
        ),
        new ContextItem(
          '🎯 Goal',
          checkpoint.goal || 'N/A',
          vscode.TreeItemCollapsibleState.None
        ),
        new ContextItem(
          '📊 Status',
          checkpoint.current_status || 'N/A',
          vscode.TreeItemCollapsibleState.None
        ),
        new ContextItem(
          '🗓️ Milestones',
          `${(checkpoint.milestones || []).length} total`,
          vscode.TreeItemCollapsibleState.Collapsed,
          checkpoint.milestones || []
        )
      ];
    } else if (element.label === '🗓️ Milestones' && element.milestones) {
      // Milestones children
      return element.milestones.map((m: any) => 
        new ContextItem(
          m.name,
          `Due: ${m.due}`,
          vscode.TreeItemCollapsibleState.None
        )
      );
    }

    return [];
  }
}

class ContextItem extends vscode.TreeItem {
  constructor(
    public readonly label: string,
    public readonly description: string,
    public readonly collapsibleState: vscode.TreeItemCollapsibleState,
    public readonly milestones?: any[]
  ) {
    super(label, collapsibleState);
    this.description = description;
    this.tooltip = `${label}: ${description}`;
  }
}
```

### 5.2 - Registrar View

**Arquivo**: `extension/src/extension.ts`

```typescript
import { ContextTreeProvider } from './views/context';

// No activate():
const contextProvider = new ContextTreeProvider(contextPilotService);
vscode.window.registerTreeDataProvider('contextpilot-context', contextProvider);

// Adicionar comando para refresh
context.subscriptions.push(
  vscode.commands.registerCommand('contextpilot.refreshContext', () => {
    contextProvider.refresh();
  })
);
```

### 5.3 - Adicionar View ao package.json

```json
{
  "contributes": {
    "views": {
      "contextpilot-sidebar": [
        {
          "id": "contextpilot-context",
          "name": "Project Context"
        }
      ]
    }
  }
}
```

### 5.4 - Testar

1. Compile: `npm run compile`
2. F5
3. Sidebar do ContextPilot deve mostrar:
   - 📦 Project: [nome]
   - 🎯 Goal: [goal]
   - 📊 Status: [status]
   - 🗓️ Milestones: X total
     - Expand para ver lista

✅ Context sendo exibido da API real!

---

## 📋 Passo 6: Coach Tips (10 min)

Mostrar dicas do coach na sidebar.

### 6.1 - Adicionar Método `getCoachTip`

**Arquivo**: `extension/src/services/contextpilot.ts`

```typescript
async getCoachTip(workspaceId: string = 'default'): Promise<string> {
  try {
    const response = await this.client.get('/coach', {
      params: { workspace_id: workspaceId }
    });
    return response.data.tip || 'No tips available';
  } catch (error) {
    console.error('Failed to get coach tip:', error);
    return 'Error loading tip';
  }
}
```

### 6.2 - Adicionar Comando

**Arquivo**: `extension/src/commands/index.ts`

```typescript
export async function getCoachTipCommand() {
  const service = getService();
  if (!service) return;

  vscode.window.showInformationMessage('🧠 Coach is thinking...');
  
  const tip = await service.getCoachTip('default');
  
  vscode.window.showInformationMessage(`🧠 Coach: ${tip}`, 'OK');
}
```

### 6.3 - Testar

Cmd+Shift+P → "ContextPilot: Get Coach Tip"

Deve mostrar dica baseada no estado real do projeto! ✅

---

## ✅ Checklist de Progresso

### API Real Funcionando
- [x] GET /health
- [x] GET /context
- [x] POST /commit
- [x] GET /coach
- [ ] GET /context/milestones
- [ ] POST /update

### Extension Integrada
- [ ] Conecta à API
- [ ] Get Context comando
- [ ] Commit Context comando
- [ ] Coach Tip comando
- [ ] Context View (sidebar)
- [ ] Milestones View (sidebar)

### Testado Neste Repo
- [ ] Extension carrega contexto
- [ ] Extension faz commit
- [ ] Extension mostra milestones
- [ ] Extension pega dicas do coach

---

## 🚀 Próximos Passos (Após Básico Funcionar)

1. **Proposals Reais** - Spec Agent sugere mudanças em docs
2. **Git Operations** - Git Agent faz branches/merges
3. **Rewards** - Track actions reais (não mock)
4. **Multi-workspace** - Suporte a múltiplos projetos

---

**Abordagem**: Incremental, usando funcionalidades reais  
**Objetivo**: Extension funcionando com API existente  
**Timeline**: 1-2 horas de desenvolvimento + teste

