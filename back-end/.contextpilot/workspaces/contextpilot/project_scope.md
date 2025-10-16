# ContextPilot - Project Scope

**Version:** 1.0  
**Last Updated:** October 15, 2025  
**Deadline:** October 20, 2025 (Hackathon Submission)

---

## 🎯 Project Vision

**ContextPilot is a multi-agent AI system that helps developers stay focused and productive by automating documentation, managing Git context, and rewarding contributions with blockchain tokens.**

**Target Users:**
- Solo developers working on complex projects
- Small teams (2-5 people)
- Open source maintainers
- Developers participating in hackathons

---

## ✅ In Scope (MVP - Must Have for Hackathon)

### Core Agents (Working End-to-End)
- ✅ **Spec Agent** - Detects missing/outdated docs, generates proposals with diffs
- ✅ **Git Agent** - Applies approved proposals, creates semantic commits
- ✅ **Coach Agent** - Provides actionable nudges (coming soon)

### VSCode/Cursor Extension
- ✅ Sidebar with proposals, rewards, agents status
- ✅ Proposal diff viewer
- ✅ AI-assisted review (Claude integration)
- ✅ Persistent chat context for reviews
- ✅ Approve/reject proposals from UI

### Backend (FastAPI)
- ✅ Proposal management (create, approve, reject)
- ✅ Event-driven architecture (in-memory bus)
- ✅ Gemini integration for content generation
- ✅ Workspace management
- ✅ Agent state persistence (JSON files)

### Custom Artifacts System
- ✅ BaseAgent supports artifact consumption
- ✅ `artifacts.yaml` configuration
- ✅ Templates (feature_spec, coding_standards)
- ✅ Natural language rules for agents

### Blockchain Integration
- ✅ CPT Token (ERC-20) deployed on Sepolia testnet
- ✅ Smart contract with minting, burning, activity tracking
- ✅ Backend connected to blockchain

### Documentation
- ✅ Architecture docs
- ✅ Development guides
- ✅ Custom artifacts guide
- ✅ Extension README

---

## 🚫 Out of Scope (Post-Hackathon / Future Versions)

### Not for MVP
- ❌ **Mobile app** - Desktop/web only for now
- ❌ **Real-time collaboration** - Single user for MVP
- ❌ **Video calls / Screen sharing** - Focus on async workflows
- ❌ **Advanced analytics dashboard** - Basic metrics only
- ❌ **Multi-language support** - English only for MVP
- ❌ **Complex permission system** - Simple API keys only
- ❌ **Production Pub/Sub** - In-memory event bus sufficient for demo
- ❌ **Production Firestore** - Local JSON storage for demo
- ❌ **Cloud Run deployment** - Local development for hackathon demo
- ❌ **VSCode Marketplace publication** - Manual VSIX install for demo
- ❌ **Mainnet blockchain** - Testnet only
- ❌ **Fiat payment integration** - Tokens only
- ❌ **Advanced LLM features** - Basic Gemini only
- ❌ **Multi-workspace UI** - Single workspace tested
- ❌ **Agent marketplace** - Pre-defined agents only
- ❌ **Custom agent creation** - Use existing agents only

### Defer to Post-Hackathon
- **Strategy Agent** - Architectural insights (nice to have)
- **Milestone Agent** - Advanced checkpoint system (nice to have)
- **Retrospective Agent** - Weekly reviews (future)
- **Advanced rewards distribution** - Manual testing OK for demo
- **Rate limiting** - Not critical for demo
- **User authentication** - Simple API keys OK
- **Comprehensive test suite** - Manual testing for demo
- **CI/CD pipeline** - Manual deployment for demo

---

## 🎯 Success Criteria (What Makes Hackathon Demo Successful)

### Functional Requirements
- [ ] **End-to-End Flow Works:**
  - Spec Agent detects missing doc
  - Creates proposal with AI-generated content (Gemini)
  - Shows diff in extension
  - User reviews with Claude
  - User approves
  - Git Agent applies changes and commits
  - File appears in workspace

- [ ] **Extension Polished:**
  - Proposals view shows real data
  - Diff viewer works smoothly
  - Claude integration is seamless
  - No crashes or UI glitches

- [ ] **AI Quality:**
  - Gemini generates useful documentation
  - Claude provides helpful review feedback
  - Proposals are actionable

- [ ] **Demo-Ready:**
  - Can show live demo in < 5 minutes
  - Video demo recorded (backup)
  - README has clear installation steps
  - Documentation explains architecture

### Non-Functional Requirements
- [ ] **Performance:** Proposals generated in < 10 seconds
- [ ] **Reliability:** Extension doesn't crash during demo
- [ ] **Usability:** Judges can install and test in < 5 minutes
- [ ] **Documentation:** Architecture is clear and impressive

---

## 📅 Timeline to Hackathon

### **Day 1 (Oct 15) - COMPLETED ✅**
- ✅ Extension fully functional
- ✅ Proposals with diffs working
- ✅ Claude review integration
- ✅ Git Agent applies changes
- ✅ End-to-end flow tested

### **Day 2 (Oct 16) - TODAY**
- [ ] Polish extension UI
- [ ] Test with ContextPilot workspace (dogfooding)
- [ ] Create demo video
- [ ] Write comprehensive README

### **Day 3 (Oct 17) - Buffer**
- [ ] Fix any bugs found during testing
- [ ] Improve Gemini prompts for better content
- [ ] Add more templates (if time permits)
- [ ] Prepare presentation

### **Day 4 (Oct 18) - Final Polish**
- [ ] Practice demo run-through
- [ ] Ensure all docs are complete
- [ ] Test installation from scratch
- [ ] Create backup demo video

### **Day 5 (Oct 19) - Submission Prep**
- [ ] Final testing
- [ ] Create submission materials
- [ ] Submit to hackathon platform

### **Day 6 (Oct 20) - Hackathon Day**
- [ ] Present to judges
- [ ] Demo live system
- [ ] Answer questions
- [ ] **WIN! 🏆**

---

## 🔧 Technical Constraints

### Must Follow
- **Python 3.10+** for backend
- **TypeScript** for extension
- **FastAPI** for API framework
- **Google Gemini** for LLM (free tier OK)
- **VSCode Extension API** (Cursor compatible)
- **Git** for version control
- **Sepolia testnet** for blockchain (no mainnet)

### Performance Targets
- **Proposal generation:** < 10 seconds
- **Diff display:** < 1 second
- **Extension load:** < 2 seconds
- **Backend startup:** < 5 seconds

### Cost Constraints
- **Gemini API:** Stay within free tier (15 req/min)
- **No paid services** required for demo
- **Sepolia ETH:** Faucet is free

---

## 🎨 Design Principles

### For Agents
1. **Single Responsibility:** Each agent has ONE job
2. **Event-Driven:** Agents communicate via events, not direct calls
3. **Fail Gracefully:** Errors don't crash the system
4. **Transparent:** Users see what agents are doing

### For Extension
1. **Non-Intrusive:** Don't interrupt developer flow
2. **Context-Aware:** Show relevant info only
3. **Fast:** No lag or waiting
4. **Beautiful:** Modern UI with icons

### For AI
1. **Useful:** Generate actionable content
2. **Accurate:** Follow project context
3. **Safe:** Human approval required
4. **Explainable:** Show reasoning

---

## 🎯 Hackathon Judging Criteria (Keep in Mind)

### Technical Excellence (40%)
- ✅ Multi-agent architecture (complex!)
- ✅ Event-driven system (production-ready!)
- ✅ AI/LLM integration (Gemini + Claude)
- ✅ VSCode extension (polished!)

### Innovation (30%)
- ✅ Custom artifacts system (unique!)
- ✅ AI-assisted code review (novel!)
- ✅ Spec-driven development (new paradigm!)
- ✅ Blockchain rewards (Web3 + AI combo!)

### Google Cloud Usage (20%)
- ⚠️ Uses Gemini API (primary Google Cloud service)
- ⚠️ Architecture ready for Cloud Run (even if not deployed)
- ⚠️ Pub/Sub architecture designed (in-memory for demo)

### Presentation (10%)
- ✅ Clear value proposition
- ✅ Live demo
- ✅ Good documentation

**Strategy:** Emphasize architecture readiness for Cloud Run, even if demo runs locally. Show we DESIGNED for Google Cloud.

---

## 🚀 Differentiation (What Makes Us Special)

### Unique Features
1. **Multi-Agent Coordination** - Not just one AI, but 3+ agents working together
2. **Custom Artifacts** - Users teach agents with natural language
3. **Spec-Driven Development** - Templates for feature specs
4. **AI-Assisted Review** - Claude helps review proposals
5. **Blockchain Integration** - Token rewards for contributions

### Compared to Competitors
- **GitHub Copilot:** We automate WORKFLOW, not just code completion
- **Cursor AI:** We have specialized agents, not general-purpose AI
- **Conventional CI/CD:** We're proactive (detect issues), not reactive
- **Project Management Tools:** We're integrated with code, not separate

---

## 📊 Metrics to Track

### For Demo
- Number of proposals generated
- Success rate of proposals (approved vs rejected)
- Time from detection to commit
- Lines of documentation generated
- User satisfaction (if we get beta testers)

### For Hackathon Judges
- "Look! 3 agents working together!"
- "Generated 500 lines of docs automatically!"
- "Human-in-the-loop with AI review!"
- "Custom artifacts = user control!"

---

## 🎬 Demo Script (5 Minutes)

### Minute 1: Problem
"Developers lose context. Docs get outdated. Reviews are manual."

### Minute 2: Solution
"ContextPilot: Multi-agent AI system that automates docs, manages Git, rewards contributions."

### Minute 3: Live Demo
1. Show missing README
2. Spec Agent detects issue
3. Creates proposal with Gemini
4. Show diff in extension
5. Ask Claude to review
6. Approve
7. Git Agent applies + commits
8. **README created!**

### Minute 4: Architecture
"Event-driven, 3+ agents, custom artifacts, blockchain rewards."

### Minute 5: Q&A
"Questions?"

---

## 🔒 Security & Ethics

### Guardrails
- ✅ Human approval required for all code changes
- ✅ Proposals include full diffs (transparency)
- ✅ AI review is advisory, not mandatory
- ✅ Users control scope via artifacts
- ✅ No automatic deployments

### Privacy
- ✅ Code stays local (no cloud storage of code)
- ✅ Only metadata sent to backend
- ✅ API keys stored securely (environment variables)

---

## 💡 Future Vision (Post-Hackathon)

### Phase 2 (Q4 2025)
- Deploy to Google Cloud Run
- Use production Pub/Sub
- Firestore for persistence
- Publish to VSCode Marketplace
- Add Strategy & Milestone Agents

### Phase 3 (Q1 2026)
- Agent marketplace (community agents)
- Advanced analytics
- Team collaboration features
- Multi-workspace support
- Mainnet deployment

### Phase 4 (Q2 2026+)
- Mobile app
- Real-time collaboration
- Video integration
- Multi-language support
- Enterprise features

---

## 🎯 Current Status (October 15, 2025)

### ✅ Completed
- Core architecture
- 3 agents (Spec, Git, Coach MVP)
- Extension with all views
- Proposal system with diffs
- Claude integration
- Gemini content generation
- Git automation
- Custom artifacts system
- Blockchain integration
- Comprehensive documentation

### 🚧 In Progress
- Extension polish
- Demo video
- Final testing

### ⏳ Remaining (1 Day)
- Bug fixes
- Demo preparation
- Submission materials

---

## 🚨 Rules for Agents

### Spec Agent Rules
**BEFORE creating ANY proposal:**
1. ✅ Check if feature is in "In Scope" section
2. ❌ REJECT proposals for "Out of Scope" features
3. 💡 Explain: "This is out of scope for pre-hackathon launch. Let's add it post-hackathon!"
4. 🎯 Focus on "Success Criteria" items
5. ⏰ Remember deadline: October 20, 2025

### Git Agent Rules
**BEFORE committing:**
1. ✅ Only commit approved proposals
2. ✅ Use semantic commit messages
3. ✅ Include proposal ID in commit message
4. ✅ Ensure all tests pass (manual for now)

### Coach Agent Rules
**When interacting with user:**
1. 🎯 Keep focus on "Success Criteria"
2. ⏰ Remind about deadline (5 days left!)
3. 🚫 Redirect out-of-scope suggestions to post-hackathon
4. 🎉 Celebrate milestones from timeline
5. 💡 Suggest next actionable item

---

**Last Review:** October 15, 2025  
**Status:** 🟢 **ON TRACK FOR HACKATHON!**  
**Next Milestone:** Demo video (Oct 16)

---

*"Focus on MVP. Ship for hackathon. Iterate post-launch."*
