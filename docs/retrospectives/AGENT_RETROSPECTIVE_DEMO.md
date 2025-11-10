# 🎬 Agent Retrospective Demo Guide

This guide shows you how to demonstrate the agent retrospective feature for the hackathon video.

---

## 🎯 Why This Feature Matters for Judges

**Most AI agent systems** have agents that:
- Execute tasks independently
- Don't communicate about their work
- Can't learn from each other
- Have no coordination mechanism

**ContextPilot's agents**:
- 🧠 Hold "retrospective meetings" to discuss their work
- 📊 Share metrics and learnings
- 💡 Generate insights about collaboration
- 🎯 Propose improvements to their own workflows
- 🤝 Coordinate to optimize team performance

**This demonstrates true multi-agent intelligence and self-improvement!**

---

## 🎥 Demo Options

### Option 1: Interactive Simulation (Best for Video)

**What it shows:** Agents "talking" to each other in real-time with colors and animations.

```bash
cd back-end
python demo_agent_interaction.py
# Choose option 1: Simulated Agent Meeting
```

**Duration:** ~60 seconds  
**Requirements:** None (no backend needed)  
**Visual:** Colorful terminal output showing agent dialogue

**Screen recording tips:**
- Use full-screen terminal
- Dark terminal theme for better contrast
- Record at 1080p or higher
- Add calm background music

---

### Option 2: Real API Demo

**What it shows:** Actual retrospective via the backend API.

```bash
# Terminal 1: Start backend
cd back-end
uvicorn app.server:app --reload

# Terminal 2: Run demo
python demo_agent_interaction.py
# Choose option 2: Real Retrospective
```

**Duration:** ~30 seconds  
**Requirements:** Backend running  
**Visual:** Shows actual API responses with metrics

---

### Option 3: Shell Script Demo (Simple)

**What it shows:** Retrospective via curl commands.

```bash
cd back-end
./demo_retrospective.sh
```

**Duration:** ~45 seconds  
**Requirements:** Backend running  
**Output:** JSON responses + file paths

---

## 📋 Demo Script for Video

### Scene 1: Introduction (15 seconds)

**Narration:**
> "ContextPilot has 7 AI agents that don't just execute tasks—they learn from each other. Let me show you how agents hold 'retrospective meetings' to improve their coordination."

**Screen:** Show agent list or architecture diagram

---

### Scene 2: Agent Meeting (45 seconds)

**Narration:**
> "Watch as agents discuss their work, share insights, and propose improvements..."

**Screen:** Run `python demo_agent_interaction.py` (option 1)

**Key moments to capture:**
1. Spec Agent reports metrics
2. Git Agent responds with coordination offer
3. Spec Agent accepts and commits to improvement
4. Retrospective Agent synthesizes insights
5. Action items generated

---

### Scene 3: Results (15 seconds)

**Narration:**
> "The retrospective generates detailed reports with metrics, insights, and actionable improvements—enabling true multi-agent learning."

**Screen:** Show generated files:
```bash
ls workspaces/default/retrospectives/
cat workspaces/default/retrospectives/retro-*.md
```

---

### Scene 4: Testing (15 seconds)

**Narration:**
> "And of course, we have comprehensive tests covering all endpoints."

**Screen:** Run tests
```bash
pytest tests/test_server.py::test_trigger_retrospective -v
```

---

## 🎨 Visual Flow Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                 RETROSPECTIVE AGENT MEETING                   │
│              (Triggered by Milestone Completion)              │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│  Phase 1: Retrospective Agent collects metrics               │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ Spec    │  │  Git    │  │ Coach   │  │Strategy │        │
│  │ Agent   │  │ Agent   │  │ Agent   │  │ Agent   │        │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘        │
│       │            │            │            │               │
│       └────────────┴────────────┴────────────┘               │
│                    │                                          │
│                    ▼                                          │
│         ┌──────────────────────┐                             │
│         │ Retrospective Agent  │ Reads agent state files     │
│         │ (Facilitator)        │ & event bus history         │
│         └──────────────────────┘                             │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│  Phase 2: Each agent shares metrics & learnings              │
│                                                               │
│  🤖 Spec Agent: "Validated 15 docs, found 8 issues..."       │
│  🤖 Git Agent: "Handled 23 commits, 92% quality..."          │
│  🤖 Coach Agent: "Provided 12 tips, 5-day streak..."         │
│  🤖 Strategy Agent: "Detected 3 duplication patterns..."     │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│  Phase 3: Cross-agent discussion & coordination              │
│                                                               │
│  💬 Retrospective: "Spec needs commit context..."            │
│  💬 Git Agent: "I can publish richer events!"                │
│  💬 Spec Agent: "Perfect! I'll subscribe to them."           │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│  Phase 4: Retrospective Agent synthesizes insights           │
│                                                               │
│  💡 "156 events processed - strong activity"                 │
│  💡 "Most active agent: Context Agent"                       │
│  💡 "3 errors - review logs"                                 │
│  💡 "Strong cross-agent collaboration"                       │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│  Phase 5: Generate action items for next cycle               │
│                                                               │
│  ✓ [HIGH] Git Agent: Enhance commit event schema             │
│  ✓ [MEDIUM] Spec: Subscribe to enhanced events               │
│  ✓ [LOW] Coach: Add work-life balance tips                   │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│  Phase 6: Save report & publish event                        │
│                                                               │
│  📄 retro-20250117-093000.json                                │
│  📄 retro-20250117-093000.md                                  │
│  📡 Event: retrospective.summary.v1 → Event Bus               │
└──────────────────────────────────────────────────────────────┘
```

---

## 🎤 Key Talking Points for Video

1. **"Agents have meetings"** - Use this phrase! It's memorable and shows sophistication.

2. **"Self-improving system"** - Emphasize that agents identify their own coordination issues and propose fixes.

3. **"Not just task execution"** - Contrast with typical AI agents that just follow commands.

4. **"Learning from each other"** - Highlight the cross-agent knowledge sharing.

5. **"Production-ready"** - Mention the 30+ tests covering this feature.

---

## 📊 What Files to Show

1. **Generated retrospective report:**
```bash
cat workspaces/default/retrospectives/retro-*.md
```

2. **Agent state files (show agents have memory):**
```bash
ls -la workspaces/default/.agent_state/
```

3. **Test coverage:**
```bash
pytest tests/test_server.py -v | grep retrospective
```

---

## 🚀 Quick Test Before Recording

```bash
# Test the demo works
cd back-end
python demo_agent_interaction.py

# Test the real API
uvicorn app.server:app --reload &
sleep 5
curl -X POST http://localhost:8000/agents/retrospective/trigger \
  -H "Content-Type: application/json" \
  -d '{"trigger":"test"}'
```

---

## 💡 Pro Tips for Video

1. **Use iTerm2 or Windows Terminal** for better color support
2. **Set terminal to 80x30** for readable text
3. **Record at 60 FPS** for smooth animations
4. **Add subtitles** highlighting key agent messages
5. **Background music:** Calm, tech-focused (no copyright)
6. **Total video length:** Aim for 2:30-3:00 minutes

---

**Remember:** This feature alone could win the hackathon—it's genuinely innovative! Most competitors will have agents that execute tasks. You have agents that **reflect, coordinate, and self-improve as a team**. 🏆

