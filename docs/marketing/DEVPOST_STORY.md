# 🚀 ContextPilot - Project Story

## 💡 The Evolution of a Developer's Workflow

I've been writing code since 2016. Back then, the workflow was straightforward but manual: write code, test locally, commit, deploy, repeat. Documentation? An afterthought. Context? Stored in my head or scattered across Notion, Trello, and random `.txt` files.

Fast forward to 2022, and AI assistants started appearing—GitHub Copilot, ChatGPT for debugging, automated code reviews. These tools made us faster at *writing* code, but they introduced a new problem: **context overload**. With AI suggesting hundreds of changes, how do we maintain a coherent project vision? How do we remember *why* we made certain decisions three weeks ago when AI was generating code at breakneck speed?

Then came 2025, and AI agents became mainstream. Not just code completion, but actual autonomous systems that could analyze, propose, and coordinate. I realized: **what if we used AI agents not to replace developers, but to solve the problems AI itself created?**

That's the core insight behind ContextPilot.

---

## 🎯 The Real Problem

Modern developers face a paradox: we're more productive than ever (thanks to AI), but we're also more lost than ever. Here's what I observed in my own workflow and conversations with fellow developers:

**Context Loss is Expensive.** You spend an hour implementing a feature with AI assistance. You close your IDE, switch to another project, come back two days later—and you've forgotten the architectural decisions, the edge cases you handled, the future todos you had in mind. You re-read code, scroll through git history, try to reconstruct your mental model. That's 20-30 minutes of "context restoration" before you can write a single line of code.

**Documentation Drifts Immediately.** AI can generate perfect documentation for code that exists *right now*. But the moment you refactor (which happens constantly with AI suggesting improvements), that documentation becomes outdated. Keeping specs, architecture docs, and project goals aligned is a full-time job nobody has time for.

**Long-term Project Continuity is Hard.** With AI, you can build a feature in hours that would have taken days in 2016. But what about next month? Next quarter? How do you maintain momentum when the project scope evolves weekly? Traditional project management tools (Jira, Linear) feel heavy and disconnected from the code. You want context *where you code*, not in a separate browser tab.

What we needed was an AI system that *manages* AI-assisted development, not just assists with code generation.

---

## 🧠 The Solution: ContextPilot

ContextPilot is a multi-agent AI system that lives in your VS Code sidebar and maintains three critical aspects of modern development:

**1. Project Context (The "What" and "Why"):** A Spec Agent continuously analyzes your codebase and generates "quick reference" summaries. When you open a new coding session, you get: recent commits, current branch, modified files, project goals, architecture decisions—all condensed into a 2-minute read. No more scrolling through git logs or re-reading documentation. The AI remembers, so you don't have to.

**2. Living Documentation (The "How"):** Instead of documentation becoming stale, the Spec Agent *proposes* updates when it detects drift. You approve or reject with one click. For example, after you rename a key function, the agent notices and suggests updating the README. You click approve, the change is applied, a semantic git commit is created automatically, and you earn +10 CPT tokens. Documentation stays current because it's effortless and rewarding.

**3. Development Continuity (The "Next Steps"):** A Coach Agent tracks your progress and suggests micro-actions—tasks under 25 minutes that move the project forward. Completed a feature? The agent proposes writing tests. Stuck on architecture? It suggests breaking the problem into smaller pieces. This isn't just todo-list management; it's AI-powered momentum that keeps long-term projects on track.

All of this is coordinated through a multi-agent system deployed on Google Cloud Run, using Pub/Sub for event-driven communication and Firestore for persistent state. But from the developer's perspective, it's just a sidebar in VS Code with proposals you can approve or reject.

---

## 🛠️ How We Built It

The technical implementation centered around three architectural decisions that made everything else fall into place:

**Decision 1: Event-Driven Multi-Agent System.** Instead of building one monolithic AI that tries to do everything, we created six specialized agents (Spec, Git, Context, Coach, Milestone, Strategy). Each agent listens for specific events on Google Cloud Pub/Sub and reacts independently. For example, when you approve a proposal, the API publishes a `proposal.approved.v1` event. The Git Agent picks it up and logs the approval. The Spec Agent might trigger a context update. The Rewards system awards CPT tokens. This architecture scales naturally—adding a new agent is just subscribing to events, no refactoring needed.

**Decision 2: Local Git, Cloud AI.** Early on, we tried running git operations in Cloud Run. It failed spectacularly—Cloud Run containers are stateless; there's no persistent `.git` directory. We could have used Cloud Storage to persist git state, but that felt wrong. The breakthrough was realizing: git operations should happen on the developer's machine (where the code lives), while AI processing happens in the cloud (where Gemini API lives). This hybrid architecture solved privacy concerns (code never leaves the user's machine) and simplified the implementation (no complex cloud git management). The extension handles git via `simple-git`, the backend handles AI via Gemini.

**Decision 3: Gamification as First-Class Feature.** We almost shipped without gamification—it felt like a "nice to have." But during testing, I noticed something: approving proposals without rewards felt mechanical. Adding "+10 CPT earned!" notifications transformed the experience. Suddenly, maintaining documentation was *fun*. Achievement unlocks ("Productivity Pro!") created emotional connection. We realized gamification isn't decoration; it's a core mechanism for driving behavior change. Developers want to see their impact quantified, and CPT tokens do exactly that. Currently implemented as offchain points with a clear roadmap to blockchain integration on Polygon.

The implementation took four days of intense development with AI assistance (Claude for architecture, ChatGPT for design, Gemini for testing). In 2022, this would have taken three months or more. That acceleration is exactly the phenomenon ContextPilot helps manage—AI makes us faster, but we need systems to maintain coherence at that speed.

---

## 🚧 Challenges and Breakthroughs

The biggest technical challenge was **Pub/Sub event routing**. Initially, all agents subscribed to a single `agent-events` topic, which meant every agent received every event. A proposal approval would trigger six agents simultaneously, causing duplicate processing and wasted API calls. The breakthrough came from creating agent-specific subscriptions with an event routing map. Now, `proposal.approved.v1` goes only to the Git Agent, while `spec.update.v1` goes to the Spec Agent. This seems obvious in hindsight, but discovering it required debugging Cloud Run logs for hours, tracing why events were firing multiple times.

Another surprising challenge was **rate limiting Gemini API in the free tier**. At 15 requests per minute, we hit limits quickly during testing. The solution wasn't to upgrade to paid tier—it was to design the system to queue requests naturally. By using Pub/Sub, agent processing became asynchronous by default. If Gemini is rate-limited, the event waits in the queue. No error handling needed; the architecture absorbed the constraint elegantly.

The most rewarding breakthrough was **context summarization**. We implemented a feature where opening a new chat with Claude (or any AI) automatically receives a condensed project summary: crucial `.md` files (README, scope, architecture), recent commits, current branch, modified files. This 2K-token prompt gives the AI everything it needs to make informed suggestions without overwhelming it with 50K tokens of full codebase context. Watching this work in practice—opening a chat and seeing Claude immediately understand the project state—felt like magic.

---

## 🎓 What I Learned

**Technical:** Multi-agent systems are more robust than monolithic AI. When one agent fails, others continue working. When you want to improve documentation generation, you only update the Spec Agent, not the entire system. Event-driven architecture with Pub/Sub makes this coordination trivial on Cloud Run.

**Product:** Gamification isn't just for games. Developers respond strongly to visible progress (CPT balance going up, achievements unlocking). The "+10 CPT earned!" notification after approving a proposal creates a dopamine loop that makes documentation maintenance—traditionally a chore—actually enjoyable.

**Meta:** The best AI tools aren't the ones that automate everything. They're the ones that keep humans in the loop (you approve proposals, not auto-apply) while eliminating tedious work (generating semantic commit messages, updating docs). ContextPilot proposes, you decide — that balance feels right.

---

## 🚀 Why This Matters

In 2016, I could keep a project's context in my head. In 2022, I needed tools like Notion and wikis. In 2025, with AI generating code at incredible speeds, I need **AI-powered context management**—systems that track decisions, maintain documentation, and ensure continuity over weeks and months.

ContextPilot is that system. It's my answer to the question: *"How do we stay intentional and aligned when building at AI-accelerated speeds?"*

And it's built entirely on Cloud Run because serverless is the only architecture that makes sense for this use case. Agents wake up when needed (events arrive), process asynchronously, and scale from zero to hundreds of users without infrastructure management. Cloud Run didn't just host ContextPilot—it enabled the architecture.

**This is what modern developer tools should look like:** intelligent agents coordinating in the cloud, empowering developers locally, with rewards that make quality work feel like an achievement, not a chore.

---

**Thank you for reading. Let's build the future of AI-assisted development together.** 🚀

**— Felipe Segall, Livre Solutions**

**#CloudRunHackathon #AIAgents #DeveloperProductivity**
