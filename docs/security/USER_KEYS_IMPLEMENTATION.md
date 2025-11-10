# User-Managed Keys Implementation Plan

## 🎯 **Problem Statement**

Currently, ContextPilot uses the developer's GitHub token and API keys, which creates:
- **Billing issues**: Codespaces costs charged to developer's account
- **Security concerns**: Developer's tokens exposed to all users
- **Scalability limits**: Single token limits for all users

## 🛡️ **Solution: User-Managed Keys**

### **1. Extension Configuration**

#### **Settings UI:**
```typescript
interface UserConfig {
  // GitHub Integration
  githubToken?: string;
  githubUsername?: string;
  githubRepo?: string;
  
  // AI Integration  
  geminiApiKey?: string;
  claudeApiKey?: string;
  
  // Feature Toggles
  codespacesEnabled?: boolean;
  sandboxEnabled?: boolean;
  
  // Repository Settings
  sandboxRepo?: string;
  mainRepo?: string;
}
```

#### **Configuration Screen:**
```typescript
// Extension settings page
export class ConfigPage {
  private githubTokenInput: HTMLInputElement;
  private geminiKeyInput: HTMLInputElement;
  private codespacesToggle: HTMLInputElement;
  
  async validateGitHubToken(token: string): Promise<boolean> {
    // Validate token has required permissions
    // Check: repo access, codespaces creation, etc.
  }
  
  async validateGeminiKey(key: string): Promise<boolean> {
    // Test API key with simple request
  }
}
```

### **2. Backend Integration**

#### **User Context:**
```python
class UserContext:
    def __init__(self, user_id: str, config: Dict):
        self.user_id = user_id
        self.github_token = config.get("github_token")
        self.gemini_api_key = config.get("gemini_api_key")
        self.codespaces_enabled = config.get("codespaces_enabled", False)
        self.sandbox_repo = config.get("sandbox_repo")
```

#### **Development Agent Update:**
```python
class DevelopmentAgent(BaseAgent):
    def __init__(self, user_context: UserContext):
        self.user_context = user_context
        self.github_token = user_context.github_token
        self.gemini_api_key = user_context.gemini_api_key
        
    async def implement_feature(self, description: str):
        if self.user_context.codespaces_enabled:
            return await self._implement_in_codespace(description)
        elif self.user_context.sandbox_enabled:
            return await self._implement_in_sandbox(description)
        else:
            return await self._implement_proposal_mode(description)
```

### **3. Security & Validation**

#### **Token Validation:**
```python
async def validate_user_github_token(token: str) -> Dict:
    """Validate GitHub token and return permissions."""
    try:
        response = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {token}"}
        )
        
        if response.status_code == 200:
            user_data = response.json()
            return {
                "valid": True,
                "username": user_data["login"],
                "permissions": await check_permissions(token)
            }
        else:
            return {"valid": False, "error": "Invalid token"}
    except Exception as e:
        return {"valid": False, "error": str(e)}

async def check_permissions(token: str) -> Dict:
    """Check if token has required permissions."""
    required_permissions = [
        "repo",           # Repository access
        "codespaces",     # Codespaces creation
        "workflow",       # GitHub Actions
    ]
    
    # Implementation to check each permission
    return {"has_all_permissions": True}
```

#### **API Key Validation:**
```python
async def validate_gemini_api_key(key: str) -> bool:
    """Validate Gemini API key."""
    try:
        url = "https://generativelanguage.googleapis.com/v1/models"
        response = requests.get(f"{url}?key={key}")
        return response.status_code == 200
    except:
        return False
```

### **4. User Experience Flow**

#### **First Time Setup:**
```
1. User installs extension
2. Extension shows "Setup Required" screen
3. User enters GitHub token
4. Extension validates token
5. User enters Gemini API key (optional)
6. User configures feature preferences
7. Extension saves config securely
8. User can now use ContextPilot
```

#### **Ongoing Usage:**
```
1. User triggers retrospective
2. Backend loads user's config
3. Development Agent uses user's keys
4. Codespaces created with user's billing
5. User sees their own repositories
6. All operations use user's permissions
```

### **5. Implementation Phases**

#### **Phase 1: Basic User Keys (Week 1)**
- ✅ Extension settings UI
- ✅ GitHub token validation
- ✅ Backend user context
- ✅ Sandbox mode with user keys

#### **Phase 2: Codespaces Integration (Week 2)**
- ✅ Codespaces with user billing
- ✅ User repository management
- ✅ Permission validation
- ✅ Error handling

#### **Phase 3: Advanced Features (Week 3)**
- ✅ Multiple AI providers
- ✅ Custom repository settings
- ✅ Team/organization support
- ✅ Usage analytics

### **6. Security Considerations**

#### **Token Storage:**
- ✅ **Encrypted storage** in extension
- ✅ **No server storage** of tokens
- ✅ **Token rotation** support
- ✅ **Permission scoping** (minimal required)

#### **API Security:**
- ✅ **Rate limiting** per user
- ✅ **Usage monitoring** 
- ✅ **Error sanitization**
- ✅ **Audit logging**

## 🚀 **Benefits**

### **For Users:**
- ✅ **Own billing** - pay only for what you use
- ✅ **Own repositories** - work with your projects
- ✅ **Own permissions** - control access levels
- ✅ **Privacy** - your keys stay with you

### **For Developer:**
- ✅ **No billing liability** - users pay their own costs
- ✅ **Scalable** - unlimited users
- ✅ **Secure** - no token exposure
- ✅ **Professional** - enterprise-ready

## 📋 **Next Steps**

1. **Test current implementation** with your keys
2. **Implement Phase 1** - Basic user keys
3. **Add validation** and error handling
4. **Deploy** user-managed version
5. **Gather feedback** and iterate

**This makes ContextPilot truly scalable and professional!** 🎉

