from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button
from textual.containers import Vertical, Horizontal
from git_context_manager import Git_Context_Manager


class HomeScreen(Screen):
    BINDINGS = [("q", "app.pop_screen", "Back")]

    def __init__(self, workspace_id: str = "default"):
        super().__init__()
        self.workspace_id = workspace_id
        self.manager = Git_Context_Manager(workspace_id)

    def compose(self):
        yield Header()
        yield Static("📊 Project Summary", id="title")

        context = self.manager.get_project_context()
        cp = context.get("checkpoint", {})

        yield Static(f"📦 Project: {cp.get('project_name', 'N/A')}")
        yield Static(f"🎯 Goal: {cp.get('goal', 'N/A')}")
        yield Static(f"📍 Status: {cp.get('current_status', 'N/A')}")

        yield Static("\n🗓️ Milestones:")
        milestones = cp.get("milestones", [])
        for m in milestones:
            yield Static(f"  • {m['name']} — due: {m['due']}")

        yield Horizontal(
            Button("↩️ Back", id="back"),
            id="actions"
        )
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "back":
            await self.app.pop_screen()
