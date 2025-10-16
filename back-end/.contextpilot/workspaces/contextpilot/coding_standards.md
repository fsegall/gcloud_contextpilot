# ContextPilot - Multi-Agent Dev Assistant Coding Standards

> **For AI Agents:** Follow these standards when generating code proposals.

---

## 🐍 Python (Backend)

### Code Style
- **Formatter:** Black (line length: 100)
- **Linter:** Ruff
- **Type Hints:** Required for all public functions
- **Docstrings:** Google style

### Architecture Patterns

#### 1. Agent Pattern
```python
from app.agents.base_agent import BaseAgent
from typing import Dict, Any

class MyAgent(BaseAgent):
    """
    Brief description of agent purpose.
    
    Responsibilities:
    - Responsibility 1
    - Responsibility 2
    """
    
    def __init__(self, workspace_id: str, project_id: str = None):
        super().__init__(
            workspace_id=workspace_id,
            agent_id='my-agent',
            project_id=project_id
        )
        # Agent-specific initialization
        self.subscribe_to_event(EventTypes.MY_EVENT)
    
    async def handle_event(self, event_type: str, data: Dict) -> None:
        """Handle incoming events."""
        if event_type == EventTypes.MY_EVENT:
            await self._handle_my_event(data)
    
    async def _handle_my_event(self, data: Dict) -> None:
        """Process specific event type."""
        # Implementation
        await self.publish_event(
            topic=Topics.MY_TOPIC,
            event_type=EventTypes.MY_RESPONSE,
            data={'result': 'success'}
        )
```

#### 2. Service Pattern
```python
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class MyService:
    """
    Service for [domain logic].
    
    Handles:
    - Functionality 1
    - Functionality 2
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        logger.info("[MyService] Initialized")
    
    async def do_something(self, param: str) -> Optional[Dict]:
        """
        Does something useful.
        
        Args:
            param: Description of parameter
            
        Returns:
            Result dict or None if failed
            
        Raises:
            ValueError: If param is invalid
        """
        try:
            # Implementation
            result = await self._internal_method(param)
            logger.info(f"[MyService] Success: {result}")
            return result
        except Exception as e:
            logger.error(f"[MyService] Failed: {e}")
            raise
    
    async def _internal_method(self, param: str) -> Dict:
        """Private method - only used internally."""
        return {'data': param}
```

#### 3. API Endpoint Pattern
```python
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api/v1/my-resource", tags=["my-resource"])

# Request/Response Models
class MyRequest(BaseModel):
    field1: str
    field2: Optional[int] = None

class MyResponse(BaseModel):
    id: str
    result: str

@router.post("/", response_model=MyResponse)
async def create_resource(
    request: MyRequest,
    workspace_id: str = Query(..., description="Workspace ID")
) -> MyResponse:
    """
    Create a new resource.
    
    Args:
        request: Resource creation request
        workspace_id: Target workspace
        
    Returns:
        Created resource
        
    Raises:
        HTTPException: If creation fails
    """
    try:
        # Validate
        if not request.field1:
            raise HTTPException(status_code=400, detail="field1 required")
        
        # Process
        result = await service.create(request, workspace_id)
        
        # Return
        return MyResponse(id=result['id'], result='success')
    except Exception as e:
        logger.error(f"Failed to create resource: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Error Handling
```python
# ✅ GOOD: Specific exceptions
try:
    result = await risky_operation()
except FileNotFoundError as e:
    logger.error(f"File not found: {e}")
    return None
except PermissionError as e:
    logger.error(f"Permission denied: {e}")
    raise HTTPException(status_code=403, detail="Access denied")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise

# ❌ BAD: Catch-all without logging
try:
    result = await risky_operation()
except:
    pass
```

### Logging
```python
import logging

logger = logging.getLogger(__name__)

# ✅ GOOD: Structured logging with context
logger.info(f"[{agent_id}] Processing event {event_type}")
logger.error(f"[{agent_id}] Failed to process: {error}", exc_info=True)

# ✅ GOOD: Different log levels
logger.debug("Detailed debug info")
logger.info("Important milestone reached")
logger.warning("Something unusual but not critical")
logger.error("Error occurred", exc_info=True)
```

### Testing
```python
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.mark.asyncio
async def test_agent_handles_event():
    """Test agent processes events correctly."""
    # Given: Agent with mocked dependencies
    agent = MyAgent(workspace_id='test')
    agent.event_bus = Mock()
    
    # When: Event is received
    await agent.handle_event(EventTypes.MY_EVENT, {'data': 'test'})
    
    # Then: Agent publishes response
    agent.event_bus.publish.assert_called_once()
    call_args = agent.event_bus.publish.call_args
    assert call_args[1]['event_type'] == EventTypes.MY_RESPONSE

@pytest.fixture
def mock_service():
    """Reusable mock service."""
    service = Mock()
    service.create = AsyncMock(return_value={'id': 'test-123'})
    return service
```

---

## 📝 TypeScript (Extension)

### Code Style
- **Formatter:** Prettier
- **Linter:** ESLint
- **Type Safety:** Strict mode enabled

### Architecture Patterns

#### 1. Command Pattern
```typescript
import * as vscode from 'vscode';
import { ContextPilot - Multi-Agent Dev AssistantService } from '../services/contextpilot';

export async function myCommand(
  service: ContextPilot - Multi-Agent Dev AssistantService,
  param: string
): Promise<void> {
  try {
    // Show progress
    await vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: 'Processing...',
        cancellable: false,
      },
      async () => {
        // Do work
        const result = await service.doSomething(param);
        
        // Update UI
        vscode.window.showInformationMessage(
          `✅ Success: ${result.message}`
        );
      }
    );
  } catch (error) {
    vscode.window.showErrorMessage(
      `❌ Failed: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}
```

#### 2. Service Pattern
```typescript
import axios, { AxiosInstance } from 'axios';

export interface MyData {
  id: string;
  value: string;
}

export class MyService {
  private client: AxiosInstance;
  
  constructor(baseURL: string) {
    this.client = axios.create({
      baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json'
      }
    });
  }
  
  async getData(id: string): Promise<MyData | null> {
    try {
      const response = await this.client.get<MyData>(`/data/${id}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch data:', error);
      return null;
    }
  }
}
```

#### 3. TreeView Provider Pattern
```typescript
import * as vscode from 'vscode';

export class MyTreeItem extends vscode.TreeItem {
  constructor(
    public readonly label: string,
    public readonly data: MyData,
    public readonly collapsibleState: vscode.TreeItemCollapsibleState
  ) {
    super(label, collapsibleState);
    this.tooltip = `${label} - ${data.description}`;
    this.description = data.status;
    this.iconPath = new vscode.ThemeIcon('symbol-file');
  }
}

export class MyTreeProvider implements vscode.TreeDataProvider<MyTreeItem> {
  private _onDidChangeTreeData = new vscode.EventEmitter<MyTreeItem | undefined>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;
  
  constructor(private service: MyService) {}
  
  refresh(): void {
    this._onDidChangeTreeData.fire(undefined);
  }
  
  getTreeItem(element: MyTreeItem): vscode.TreeItem {
    return element;
  }
  
  async getChildren(element?: MyTreeItem): Promise<MyTreeItem[]> {
    if (!element) {
      // Root level
      const data = await this.service.getData();
      return data.map(item => new MyTreeItem(item.name, item, vscode.TreeItemCollapsibleState.None));
    }
    return [];
  }
}
```

### Error Handling
```typescript
// ✅ GOOD: Typed errors with user-friendly messages
try {
  const result = await riskyOperation();
} catch (error) {
  if (error instanceof NetworkError) {
    vscode.window.showErrorMessage('Network error. Check your connection.');
  } else if (error instanceof ValidationError) {
    vscode.window.showWarningMessage(`Invalid input: ${error.message}`);
  } else {
    console.error('Unexpected error:', error);
    vscode.window.showErrorMessage('An unexpected error occurred.');
  }
}
```

---

## 📁 File Organization

### Backend
```
back-end/
├── app/
│   ├── agents/          # All agents (base + specialized)
│   │   ├── base_agent.py
│   │   ├── spec_agent.py
│   │   └── git_agent.py
│   ├── services/        # Business logic services
│   │   ├── llm_service.py
│   │   └── event_bus.py
│   ├── models/          # Pydantic models
│   │   └── proposal.py
│   ├── routers/         # API endpoints
│   │   └── proposals.py
│   ├── utils/           # Utilities
│   │   └── workspace.py
│   └── server.py        # FastAPI app
├── tests/               # All tests
│   ├── test_agents/
│   └── test_services/
└── requirements.txt
```

### Extension
```
extension/
├── src/
│   ├── commands/        # Command implementations
│   │   └── index.ts
│   ├── services/        # API clients
│   │   └── contextpilot.ts
│   ├── views/           # Tree providers, webviews
│   │   ├── proposals.ts
│   │   └── review-panel.ts
│   └── extension.ts     # Entry point
├── package.json
└── tsconfig.json
```

---

## 🧪 Testing Standards

### Coverage Requirements
- **Unit Tests:** > 80% coverage
- **Integration Tests:** Critical paths covered
- **E2E Tests:** Happy path + major error cases

### Test Naming
```python
# Pattern: test_[function]_[scenario]_[expected]

def test_agent_handles_event_success():
    """Agent successfully processes valid event"""
    pass

def test_agent_handles_event_invalid_data_raises_error():
    """Agent raises ValueError for invalid event data"""
    pass
```

---

## 📚 Documentation Standards

### Code Comments
```python
# ✅ GOOD: Explain WHY, not WHAT
# Use exponential backoff to avoid overwhelming the API during retries
await asyncio.sleep(2 ** attempt)

# ❌ BAD: Obvious comment
# Sleep for 2 seconds
await asyncio.sleep(2)
```

### Docstrings
```python
def process_proposal(proposal_id: str, workspace_id: str) -> Dict[str, Any]:
    """
    Process a proposal and apply changes.
    
    This function validates the proposal, applies the changes to the workspace,
    and commits them via the Git Agent. It handles rollback if any step fails.
    
    Args:
        proposal_id: Unique identifier for the proposal
        workspace_id: Target workspace to apply changes
        
    Returns:
        Dictionary containing:
        - status: 'success' or 'failed'
        - commit_hash: Git commit hash (if successful)
        - error: Error message (if failed)
        
    Raises:
        ProposalNotFoundError: If proposal doesn't exist
        WorkspaceNotFoundError: If workspace doesn't exist
        
    Example:
        >>> result = process_proposal('prop-123', 'my-workspace')
        >>> print(result['status'])
        'success'
    """
```

---

## 🔐 Security Standards

### API Keys
```python
# ✅ GOOD: Use environment variables
api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    raise ValueError("GOOGLE_API_KEY not set")

# ❌ BAD: Hardcoded keys
api_key = "AIzaSyDxxx..."  # NEVER DO THIS
```

### Input Validation
```python
from pydantic import BaseModel, validator

class ProposalRequest(BaseModel):
    title: str
    description: str
    
    @validator('title')
    def title_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('title cannot be empty')
        return v.strip()
```

---

## 🚀 Performance Standards

### Async/Await
```python
# ✅ GOOD: Run independent operations in parallel
results = await asyncio.gather(
    fetch_proposals(),
    fetch_rewards(),
    fetch_context()
)

# ❌ BAD: Sequential when parallel is possible
proposals = await fetch_proposals()
rewards = await fetch_rewards()
context = await fetch_context()
```

### Caching
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_computation(param: str) -> str:
    """Cache results for repeated calls"""
    return complex_calculation(param)
```

---

## 📊 Monitoring Standards

### Metrics
```python
# Track important metrics
self.increment_metric('proposals_created')
self.increment_metric('errors')
self.set_metric('processing_time_ms', elapsed_ms)
```

### Logging Levels
- **DEBUG:** Detailed info for debugging
- **INFO:** Important milestones
- **WARNING:** Unusual but handled
- **ERROR:** Errors with stack traces

---

**Last Updated:** 2025-10-15  
**Owner:** Engineering Team

