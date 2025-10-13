from textual.screen import Screen
from textual.widgets import Header, Footer, Input, Button, Static, Label
from textual.containers import VerticalScroll, Horizontal
from git_context_manager import Git_Context_Manager


class CheckpointEditorScreen(Screen):
    BINDINGS = [("q", "app.pop_screen", "Back")]

    def __init__(self, workspace_id: str = "default"):
        super().__init__()
        self.manager = Git_Context_Manager(workspace_id)
        self.state = self.manager.get_project_context().get("checkpoint", {})
        self.workspace_id = workspace_id

    def compose(self):
        yield Header()
        yield Label("✏️ Edit Checkpoint", id="title")

        yield Input(placeholder="Project Name", id="project_name", value=self.state.get("project_name", ""))
        yield Input(placeholder="Goal", id="goal", value=self.state.get("goal", ""))
        yield Input(placeholder="Current Status", id="current_status", value=self.state.get("current_status", ""))

        yield Label("📅 Milestones (not editable in this version)", id="milestone-label")

        milestone_text = "\n".join([
            f"- {m['name']} ({m['due']})"
            for m in self.state.get("milestones", [])
        ]) or "⚠️ No milestones found."

        yield VerticalScroll(Static(milestone_text), id="milestones")

        yield Horizontal(
            Button("💾 Save", id="save"),
            Button("↩️ Cancel", id="cancel"),
            id="actions"
        )

        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "save":
            project_name = self.query_one("#project_name", Input).value
            goal = self.query_one("#goal", Input).value
            current_status = self.query_one("#current_status", Input).value

            checkpoint = {
                "project_name": project_name,
                "goal": goal,
                "current_status": current_status,
                "milestones": self.state.get("milestones", []),
            }

            self.manager.write_context({"checkpoint": checkpoint})
            self.manager.commit_changes("Checkpoint updated via TUI", agent="tui")
            await self.app.pop_screen()

        elif event.button.id == "cancel":
            await self.app.pop_screen()
