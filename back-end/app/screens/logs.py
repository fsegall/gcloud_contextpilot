# screens/logs.py
from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual.scroll_view import ScrollView
from textual.containers import Vertical
from datetime import datetime

from git_context_manager import Git_Context_Manager

class LogsScreen(Screen):
    BINDINGS = [("q", "app.pop_screen", "Back")]

    def __init__(self, workspace_id: str = "default"):
        super().__init__()
        self.manager = Git_Context_Manager(workspace_id)
        self.workspace_id = workspace_id

    def compose(self):
        yield Header()
        yield Static("📋 Últimos logs do projeto", id="title")

        history = self.manager.get_project_context().get("history", [])

        messages = []

        if not history:
            messages.append(Static("⚠️ No history entries found."))
        else:
            for entry in reversed(history[-20:]):
                ts = datetime.fromisoformat(entry["timestamp"]).strftime("%Y-%m-%d %H:%M")
                msg = (
                    f"📌 {entry['summary']}\n"
                    f"⏱️ {ts}\n"
                    f"🧠 Agent: {entry['agent']}\n"
                    f"💬 Commit: {entry['commit']}\n"
                    f"📝 {entry['message']}\n"
                    "─" * 40
                )
                messages.append(Static(msg, classes="log-entry"))

        yield ScrollView(*messages, id="context_log")

        yield Footer()
