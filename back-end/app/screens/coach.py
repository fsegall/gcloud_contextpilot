from textual.screen import Screen
from textual.widgets import Header, Footer, Label, Button, Static
from textual.containers import VerticalScroll, Horizontal
from git_context_manager import Git_Context_Manager


class CoachScreen(Screen):
    BINDINGS = [("q", "app.pop_screen", "Back")]

    def __init__(self, workspace_id: str = "default"):
        super().__init__()
        self.workspace_id = workspace_id
        self.manager = Git_Context_Manager(workspace_id)

    def compose(self):
        yield Header()
        yield Label("🧠 Coach Tip Generator", id="title")

        context = self.manager.get_project_context()
        checkpoint = context.get("checkpoint", {})
        milestones = checkpoint.get("milestones", [])

        summary = Static(id="coach_tip")
        summary.update("🔄 Generating coach tip...")

        if not milestones:
            summary.update("⚠️ No milestones found in current checkpoint.")
        else:
            tip = self.manager.query_llm(
                prompt="Based on the current checkpoint and progress history, generate a brief and motivating coaching tip.",
                context=context
            )
            summary.update(tip)

        yield VerticalScroll(summary, id="coach_scroll")

        yield Horizontal(
            Button("↩️ Back", id="back"),
            id="actions"
        )
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "back":
            await self.app.pop_screen()
