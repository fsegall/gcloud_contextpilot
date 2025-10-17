# Contributing to ContextPilot

Thank you for your interest in contributing to ContextPilot! 🎉

We're excited to have you join our community of developers building the future of AI-powered development tools.

---

## 🎯 Ways to Contribute

### 🐛 Report Bugs
Found a bug? Please [open an issue](https://github.com/fsegall/google-context-pilot/issues/new) with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Screenshots (if applicable)
- Your environment (OS, VS Code version, extension version)

### 💡 Suggest Features
Have an idea? [Start a discussion](https://github.com/fsegall/google-context-pilot/discussions) or open a feature request issue.

### 🔧 Submit Code
Ready to code? Follow the guidelines below!

### 📖 Improve Documentation
Documentation improvements are always welcome - from fixing typos to adding examples.

---

## 🚀 Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git
- Docker (optional, for local Cloud Run testing)
- Google Cloud SDK (optional, for deployment)

### Backend Setup

```bash
cd back-end

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your GOOGLE_API_KEY (get from https://makersuite.google.com/app/apikey)

# Run tests
pytest

# Run server
uvicorn app.server:app --reload --port 8000
```

### Extension Setup

```bash
cd extension

# Install dependencies
npm install

# Compile TypeScript
npm run compile

# Run in debug mode
# Press F5 in VS Code to open Extension Development Host
```

### Frontend Setup (Optional)

```bash
cd front-end

# Install dependencies
npm install

# Run dev server
npm run dev
```

---

## 📝 Code Style & Standards

### Python (Backend)
- Follow [PEP 8](https://pep8.org/)
- Use type hints
- Docstrings for all public functions
- Max line length: 100 characters

```python
def example_function(param: str) -> Dict[str, Any]:
    """
    Brief description of function.
    
    Args:
        param: Description of parameter
        
    Returns:
        Description of return value
    """
    pass
```

### TypeScript (Extension)
- Use strict mode
- Prefer `const` over `let`
- Use async/await over promises
- Add JSDoc for exported functions

```typescript
/**
 * Approve a proposal and commit changes locally
 * @param proposalId - The ID of the proposal to approve
 * @returns Promise that resolves when complete
 */
export async function approveProposal(proposalId: string): Promise<void> {
    // Implementation
}
```

### Commit Messages
We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(agents): add context summarization to Spec Agent
fix(extension): correct workspace detection logic
docs(readme): update installation instructions
chore(deps): upgrade httpx to 0.27.0
```

Format: `<type>(<scope>): <subject>`

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

---

## 🔄 Pull Request Process

### 1. Fork & Clone
```bash
# Fork on GitHub first
git clone https://github.com/YOUR_USERNAME/google-context-pilot.git
cd google-context-pilot
git remote add upstream https://github.com/fsegall/google-context-pilot.git
```

### 2. Create Branch
```bash
git checkout -b feat/your-feature-name
# or
git checkout -b fix/bug-description
```

### 3. Make Changes
- Write tests for new features
- Update documentation as needed
- Follow code style guidelines
- Keep commits atomic and well-described

### 4. Test Locally
```bash
# Backend tests
cd back-end && pytest

# Extension compilation
cd extension && npm run compile

# Lint (if available)
npm run lint
```

### 5. Push & Open PR
```bash
git push origin feat/your-feature-name
```

Then open a Pull Request on GitHub with:
- Clear title (following conventional commits)
- Description of what changed and why
- Screenshots/videos for UI changes
- Link to related issue (if applicable)

### 6. Code Review
- Address review comments promptly
- Keep discussion constructive and respectful
- Update your PR based on feedback

---

## 🧪 Testing Guidelines

### Backend Tests
```bash
cd back-end
pytest tests/
pytest tests/test_agents.py -v  # Specific file
pytest -k "test_spec_agent"      # Specific pattern
```

### Extension Tests
```bash
cd extension
npm test
```

### Integration Tests
- Test the full flow: Extension → Backend → Agents → Response
- Verify git operations work correctly
- Check gamification rewards are awarded

---

## 📂 Project Structure

```
google-context-pilot/
├── back-end/          # FastAPI backend
│   ├── app/
│   │   ├── agents/    # AI agent implementations
│   │   ├── services/  # Event bus, Firestore, etc.
│   │   └── server.py  # Main API
│   └── tests/         # Backend tests
├── extension/         # VS Code extension
│   ├── src/
│   │   ├── commands/  # Extension commands
│   │   ├── services/  # API client, rewards
│   │   └── views/     # Sidebar providers
│   └── package.json
├── docs/              # Documentation
│   ├── architecture/  # Design docs
│   ├── deployment/    # Setup guides
│   └── guides/        # How-to guides
├── terraform/         # Infrastructure as Code
└── README.md
```

---

## 🐛 Debugging

### Backend
```bash
# Run with debug logging
LOG_LEVEL=DEBUG uvicorn app.server:app --reload

# Check logs
tail -f server.log
```

### Extension
```bash
# Open Extension Development Host
# F5 in VS Code

# View logs
# Help → Toggle Developer Tools → Console tab
# Look for "[ContextPilot]" messages
```

### Cloud Run (Production)
```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=contextpilot-backend" --limit 50

# Check health
curl https://contextpilot-backend-581368740395.us-central1.run.app/health
```

---

## 🎨 Design Guidelines

### UI/UX
- Keep sidebar panels clean and scannable
- Use VS Code's native icons (codicons)
- Provide clear success/error messages
- Show progress for long operations

### Agent Behavior
- Agents propose, never auto-modify code
- Clear event naming (`proposal.approved.v1`)
- Idempotent operations (safe to retry)
- Graceful degradation (fallback to local if backend unavailable)

---

## 📊 Performance Considerations

- Extension should start in < 2 seconds
- Backend API responses should be < 500ms
- Agent processing should be async (don't block user)
- Rate limiting: 100 requests/hour per IP

---

## 🔐 Security

### Do NOT commit:
- API keys or secrets
- `.env` files (use `.env.example` templates)
- Private keys or tokens
- User data or PII

### Always:
- Use environment variables for secrets
- Validate user input
- Sanitize file paths
- Check permissions before file operations

---

## 📋 Checklist Before Submitting PR

- [ ] Code follows style guidelines
- [ ] Tests pass (`pytest` for backend, `npm test` for extension)
- [ ] Documentation updated (if needed)
- [ ] Commit messages follow conventional commits
- [ ] No secrets or API keys in code
- [ ] PR description is clear and complete
- [ ] Linked to related issue (if applicable)

---

## 🏆 Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Eligible for CPT token rewards (future)
- Given credit in documentation

---

## 💬 Communication

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and ideas
- **Email**: hello@livre.solutions (for private matters)

---

## 📄 License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).

---

## 🙏 Thank You!

Every contribution, no matter how small, helps make ContextPilot better for everyone.

**Happy coding!** 🚀

---

**Made with ❤️ by Livre Solutions**

