# LLM Integration Status

**Date:** October 15, 2025  
**Current:** ⚠️ OpenAI referenced but NOT configured

---

## 🔍 Current State

### Where OpenAI is Used

**File:** `back-end/app/git_context_manager.py`

**Usage:**
1. **Get AI Insights** (line 275-290)
   - Method: `get_ai_insights()`
   - Model: `gpt-4`
   - Purpose: Generate insights about project state

2. **Generate Commit Message** (line 482-500)
   - Method: `generate_commit_message_with_ai()`
   - Model: `gpt-4`
   - Purpose: Create semantic commit messages from diff

3. **Get Strategic Recommendation** (line 523-540)
   - Method: `get_strategic_recommendation()`
   - Model: `gpt-4`
   - Purpose: Strategic advice for next steps

### Configuration Check

```python
self.openai_key = os.getenv("OPENAI_API_KEY")
if self.openai_key:
    self.client = OpenAI(api_key=self.openai_key)
else:
    logger.warning("OpenAI API key not found")
    self.client = None
```

**Current Status:**
- ❌ `OPENAI_API_KEY` NOT set
- ❌ `self.client = None`
- ❌ All AI methods return fallback messages

**Fallback Messages:**
```python
if not self.client:
    return "OpenAI API não configurada. Configure OPENAI_API_KEY..."
```

---

## 🎯 Recommended Approach: Migrate to Gemini

### Why Gemini?

1. **GCP Native**: Already using GCP infrastructure
2. **Cost**: Gemini Flash is cheaper than GPT-4
3. **Performance**: Gemini 1.5 Pro/Flash very capable
4. **Integration**: Better with Cloud Run/Pub/Sub
5. **Consistency**: All agents use same LLM

### Current Issue

**Spec Agent** (NEW code):
- Uses `BaseAgent` ✅
- Generates diffs ✅
- **Missing:** Gemini integration for content generation ❌

**Git Context Manager** (LEGACY code):
- Uses OpenAI ❌
- Not configured ❌
- Needs migration to Gemini ✅

---

## 📋 Migration Plan

### Option 1: Quick Fix (Use OpenAI)
**Time:** 5 minutes

```bash
export OPENAI_API_KEY=sk-...
```

**Pros:**
- Works immediately
- No code changes

**Cons:**
- Costs more than Gemini
- Adds external dependency
- Not GCP-native

---

### Option 2: Migrate to Gemini (Recommended)
**Time:** 1-2 hours

#### Step 1: Create LLM Service Abstraction

```python
# back-end/app/services/llm_service.py

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import os

class LLMService(ABC):
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        pass
    
    @abstractmethod
    async def chat(self, messages: List[Dict], **kwargs) -> str:
        pass


class GeminiService(LLMService):
    def __init__(self):
        import google.generativeai as genai
        api_key = os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    async def generate(self, prompt: str, **kwargs) -> str:
        response = self.model.generate_content(prompt)
        return response.text
    
    async def chat(self, messages: List[Dict], **kwargs) -> str:
        # Convert messages to Gemini format
        prompt = self._format_messages(messages)
        return await self.generate(prompt)


class OpenAIService(LLMService):
    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    async def generate(self, prompt: str, **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=kwargs.get('model', 'gpt-4'),
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    
    async def chat(self, messages: List[Dict], **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=kwargs.get('model', 'gpt-4'),
            messages=messages
        )
        return response.choices[0].message.content


def get_llm_service() -> LLMService:
    """Get configured LLM service (Gemini preferred)"""
    llm_provider = os.getenv("LLM_PROVIDER", "gemini")
    
    if llm_provider == "gemini":
        return GeminiService()
    elif llm_provider == "openai":
        return OpenAIService()
    else:
        raise ValueError(f"Unknown LLM provider: {llm_provider}")
```

#### Step 2: Update Agents to Use LLM Service

```python
# back-end/app/agents/spec_agent.py

from app.services.llm_service import get_llm_service

class SpecAgent(BaseAgent):
    def __init__(self, workspace_path, workspace_id, project_id=None):
        super().__init__(workspace_id, 'spec', project_id)
        
        # Get LLM service
        self.llm = get_llm_service()
    
    async def _generate_doc_content(self, file_path: str, issue: Dict) -> str:
        """Generate documentation content using Gemini"""
        
        prompt = f"""Generate professional documentation for {file_path}.

Issue: {issue['message']}

Create a comprehensive markdown document with:
- Clear overview
- Detailed sections
- Examples where appropriate
- Follow best practices

Output only the markdown content, no explanations."""

        content = await self.llm.generate(prompt)
        return content
```

#### Step 3: Update Git Context Manager

```python
# back-end/app/git_context_manager.py

from app.services.llm_service import get_llm_service

class Git_Context_Manager:
    def __init__(self, workspace_id="default", user_id=None):
        # Replace OpenAI with LLM service
        try:
            self.llm = get_llm_service()
        except Exception as e:
            logger.warning(f"LLM service not configured: {e}")
            self.llm = None
    
    async def generate_commit_message_with_ai(self, diff):
        if not self.llm:
            return "Commit manual - LLM não configurada"
        
        prompt = f"""Generate semantic commit message for:

{diff}

Format: type(scope): subject
Example: feat(api): add user authentication"""

        return await self.llm.generate(prompt)
```

---

## ⚡ Quick Implementation (Now)

Vou criar o LLM service abstraction agora:

### Benefits

1. **Flexibility**: Easy to switch between OpenAI, Gemini, Anthropic
2. **Cost**: Use cheapest/best for each task
3. **Fallback**: If one fails, try another
4. **Testing**: Mock LLM for tests

---

## 🎯 Recommendation

**For MVP (Now):**
- Use Gemini Flash (fast, cheap, GCP-native)
- Set `GOOGLE_API_KEY` environment variable
- Migrate existing OpenAI code

**For Production:**
- LLM service abstraction
- Gemini primary, OpenAI fallback
- Per-agent LLM configuration

**For Future:**
- User chooses LLM (Gemini, GPT, Claude, etc.)
- Agent-specific models (Gemini Flash for Spec, GPT-4 for Strategy)
- Cost optimization per task

---

## 📝 Action Items

### Immediate (Before Testing)
- [ ] Create `llm_service.py` abstraction
- [ ] Update Spec Agent to use Gemini
- [ ] Update Git Context Manager
- [ ] Set `GOOGLE_API_KEY` environment variable
- [ ] Test AI-generated content

### Short Term
- [ ] Add Gemini to requirements.txt
- [ ] Document LLM configuration
- [ ] Add LLM tests
- [ ] Cost monitoring

---

## 💰 Cost Comparison

| Model | Input | Output | Use Case |
|-------|-------|--------|----------|
| **Gemini 1.5 Flash** | $0.075/1M | $0.30/1M | Fast tasks (Spec Agent) |
| **Gemini 1.5 Pro** | $1.25/1M | $5.00/1M | Complex tasks (Strategy) |
| **GPT-4 Turbo** | $10/1M | $30/1M | Fallback only |
| **GPT-3.5** | $0.50/1M | $1.50/1M | Budget option |

**Recommendation:** Gemini Flash for 90% of tasks, Pro for complex reasoning

---

**Status:** ⚠️ OpenAI referenced but NOT operational  
**Action:** Migrate to Gemini (1-2 hours)  
**Priority:** Medium (works without LLM for now, but needed for content generation)

**Quer que eu implemente o LLM Service agora?** 🤔

