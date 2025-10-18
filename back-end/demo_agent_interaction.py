#!/usr/bin/env python3
"""
Interactive Agent Retrospective Demo
Shows agents "talking" to each other in a retrospective meeting
Perfect for hackathon video demonstration
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_agent(agent_name, message, color=Colors.CYAN):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{Colors.BOLD}{color}[{timestamp}] 🤖 {agent_name}:{Colors.END}")
    print(f"  {message}\n")
    
def print_insight(insight):
    print(f"  {Colors.YELLOW}💡 {insight}{Colors.END}")

def print_action(action):
    priority_colors = {
        "high": Colors.RED,
        "medium": Colors.YELLOW,
        "low": Colors.GREEN
    }
    color = priority_colors.get(action.get("priority", "low"), Colors.GREEN)
    print(f"  {color}[{action['priority'].upper()}] ✓ {action['action']}{Colors.END}")

async def simulate_agent_meeting():
    """Simulate agents having a retrospective meeting"""
    
    print_header("🎬 CONTEXTPILOT AGENT RETROSPECTIVE")
    print(f"{Colors.BOLD}Facilitator:{Colors.END} Retrospective Agent")
    print(f"{Colors.BOLD}Date:{Colors.END} {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{Colors.BOLD}Trigger:{Colors.END} End of Development Cycle\n")
    
    await asyncio.sleep(1)
    
    # Phase 1: Opening
    print_header("📊 Phase 1: Metrics Collection")
    print_agent(
        "Retrospective Agent",
        "Good morning, team! Let's review our performance this cycle.\n"
        "  I've collected metrics from all agents. Let's hear from everyone.",
        Colors.BLUE
    )
    await asyncio.sleep(2)
    
    # Phase 2: Agent Reports
    print_header("🗣️ Phase 2: Agent Reports")
    
    print_agent(
        "Spec Agent",
        "I validated 15 documentation files this cycle.\n"
        "  • Found 8 inconsistencies\n"
        "  • Created 6 proposals for fixes\n"
        "  • 5 proposals were approved ✓\n"
        "  • Challenge: Need better context from Git Agent on commits",
        Colors.CYAN
    )
    await asyncio.sleep(2)
    
    print_agent(
        "Git Agent",
        "I handled 23 commit events this cycle.\n"
        "  • 20 successful semantic commits\n"
        "  • 3 rejections (no significant changes)\n"
        "  • Average commit quality: 92%\n"
        "  • Note: I can share commit context with Spec Agent via event bus",
        Colors.GREEN
    )
    await asyncio.sleep(2)
    
    print_agent(
        "Coach Agent",
        "I provided 12 development tips to the user.\n"
        "  • Daily streak: 5 days 🔥\n"
        "  • Most requested: debugging strategies\n"
        "  • Observation: User often works late—suggest work-life balance tips",
        Colors.YELLOW
    )
    await asyncio.sleep(2)
    
    print_agent(
        "Strategy Agent",
        "I analyzed 47 code files for patterns.\n"
        "  • Detected 3 code duplication opportunities\n"
        "  • Found 2 potential refactorings\n"
        "  • Suggestion: Collaborate with Spec Agent on architecture docs",
        Colors.RED
    )
    await asyncio.sleep(2)
    
    print_agent(
        "Context Agent",
        "I tracked 156 file changes across the workspace.\n"
        "  • High activity in /back-end/app/agents/\n"
        "  • New feature: RetrospectiveAgent added\n"
        "  • Trend: Test coverage improving (30+ tests added)",
        Colors.CYAN
    )
    await asyncio.sleep(2)
    
    # Phase 3: Cross-Agent Discussion
    print_header("💬 Phase 3: Cross-Agent Discussion")
    
    print_agent(
        "Retrospective Agent",
        "I see some opportunities for better collaboration:\n"
        "  1. Spec Agent needs commit context → Git Agent can publish richer events\n"
        "  2. Strategy Agent has architecture insights → Spec Agent should consume\n"
        "  3. Coach Agent noticed late-night work → Could auto-suggest breaks",
        Colors.BLUE
    )
    await asyncio.sleep(2)
    
    print_agent(
        "Git Agent",
        "Agreed! I can enhance my commit events with file context.\n"
        "  Publishing to 'git-events' topic with new schema version 2.0",
        Colors.GREEN
    )
    await asyncio.sleep(1)
    
    print_agent(
        "Spec Agent",
        "Perfect! I'll subscribe to the enhanced events.\n"
        "  This will help me correlate documentation with code changes.",
        Colors.CYAN
    )
    await asyncio.sleep(2)
    
    # Phase 4: Insights
    print_header("💡 Phase 4: Synthesized Insights")
    
    print(f"{Colors.BOLD}Retrospective Agent generated the following insights:{Colors.END}\n")
    
    insights = [
        "Agents processed 156 events in this cycle - strong activity!",
        "Cross-agent collaboration is working well (6 different event types)",
        "Most active agent: Context Agent (tracking 156 changes)",
        "⚠️ 3 errors occurred across all agents - review error logs",
        "Agents Git, Spec, and Strategy recorded learnings for future use"
    ]
    
    for insight in insights:
        print_insight(insight)
        await asyncio.sleep(1)
    
    # Phase 5: Action Items
    print_header("🎯 Phase 5: Action Items")
    
    print(f"{Colors.BOLD}Proposed improvements for next cycle:{Colors.END}\n")
    
    actions = [
        {
            "priority": "high",
            "action": "Git Agent: Enhance commit events with file context",
            "assigned_to": "git-agent"
        },
        {
            "priority": "medium",
            "action": "Spec Agent: Subscribe to enhanced Git Agent events",
            "assigned_to": "spec-agent"
        },
        {
            "priority": "medium",
            "action": "Strategy + Spec: Coordinate on architecture documentation",
            "assigned_to": "strategy-agent, spec-agent"
        },
        {
            "priority": "low",
            "action": "Coach Agent: Add work-life balance tips to daily nudges",
            "assigned_to": "coach-agent"
        }
    ]
    
    for action in actions:
        print_action(action)
        await asyncio.sleep(1)
    
    # Phase 6: Closing
    print_header("📝 Phase 6: Report Generation")
    
    print_agent(
        "Retrospective Agent",
        "Excellent discussion, team!\n"
        "  • Report saved to: workspace/retrospectives/retro-{timestamp}.json\n"
        "  • Markdown summary: workspace/retrospectives/retro-{timestamp}.md\n"
        "  • Publishing retrospective.summary.v1 event to event bus",
        Colors.BLUE
    )
    await asyncio.sleep(2)
    
    print_header("✅ Retrospective Complete")
    print(f"\n{Colors.GREEN}{Colors.BOLD}Result:{Colors.END}")
    print(f"  • 5 agents participated")
    print(f"  • 5 insights generated")
    print(f"  • 4 action items created")
    print(f"  • Next retrospective: End of next development cycle\n")
    
    print(f"{Colors.YELLOW}💡 This demonstrates true multi-agent coordination:{Colors.END}")
    print(f"  Agents don't just execute tasks—they reflect, learn, and")
    print(f"  self-improve together. A key innovation in AI systems!\n")

async def show_real_retrospective():
    """Show a real retrospective from the API"""
    print_header("🔍 Connecting to Real Backend")
    
    print(f"Triggering actual retrospective via API...\n")
    
    try:
        import httpx
        
        async with httpx.AsyncClient() as client:
            # Trigger retrospective
            response = await client.post(
                "http://localhost:8000/agents/retrospective/trigger",
                json={"trigger": "demo", "use_llm": False},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "success":
                    retro = data["retrospective"]
                    
                    print(f"{Colors.GREEN}✅ Real retrospective created!{Colors.END}\n")
                    
                    print(f"{Colors.BOLD}Retrospective ID:{Colors.END} {retro['retrospective_id']}")
                    print(f"{Colors.BOLD}Timestamp:{Colors.END} {retro['timestamp']}\n")
                    
                    # Show metrics
                    print(f"{Colors.BOLD}Agent Metrics:{Colors.END}")
                    for agent_id, metrics in retro.get("agent_metrics", {}).items():
                        print(f"  {Colors.CYAN}{agent_id}:{Colors.END}")
                        for key, value in metrics.items():
                            print(f"    • {key}: {value}")
                    print()
                    
                    # Show insights
                    print(f"{Colors.BOLD}Insights:{Colors.END}")
                    for insight in retro.get("insights", []):
                        print_insight(insight)
                    print()
                    
                    # Show action items
                    print(f"{Colors.BOLD}Action Items:{Colors.END}")
                    for action in retro.get("action_items", []):
                        print_action(action)
                    print()
                    
                else:
                    print(f"{Colors.RED}❌ Retrospective failed: {data.get('message')}{Colors.END}")
            else:
                print(f"{Colors.RED}❌ API error: {response.status_code}{Colors.END}")
                
    except Exception as e:
        print(f"{Colors.YELLOW}⚠️  Could not connect to backend: {e}{Colors.END}")
        print(f"Make sure backend is running: uvicorn app.server:app --reload\n")

async def main():
    """Main demo function"""
    print("\n" * 2)
    print(f"{Colors.BOLD}{Colors.BLUE}{'#' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}#{'CONTEXTPILOT - AGENT RETROSPECTIVE DEMO'.center(68)}#{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}#{'For Cloud Run Hackathon 2025'.center(68)}#{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'#' * 70}{Colors.END}\n")
    
    print(f"Choose demo mode:\n")
    print(f"  {Colors.GREEN}1{Colors.END}. Simulated Agent Meeting (no backend required)")
    print(f"  {Colors.GREEN}2{Colors.END}. Real Retrospective (requires backend running)")
    print(f"  {Colors.GREEN}3{Colors.END}. Both (simulation + real)\n")
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == "1":
        await simulate_agent_meeting()
    elif choice == "2":
        await show_real_retrospective()
    elif choice == "3":
        await simulate_agent_meeting()
        await asyncio.sleep(2)
        await show_real_retrospective()
    else:
        print(f"{Colors.RED}Invalid choice{Colors.END}")
        return

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Demo interrupted{Colors.END}")
        sys.exit(0)

