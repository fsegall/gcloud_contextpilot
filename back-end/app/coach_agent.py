from datetime import datetime

def get_coach_tip(checkpoint, history):
    if not checkpoint:
        return "No checkpoint data available yet."

    today = datetime.today().date()
    milestones = checkpoint.get("milestones", [])
    status = checkpoint.get("current_status", "No current status recorded.")

    # Check how long since last commit
    if history:
        last_entry = history[-1]
        last_time = datetime.fromisoformat(last_entry["timestamp"]).date()
        days_inactive = (today - last_time).days

        if days_inactive >= 3:
            return (
                f"You haven't made updates in {days_inactive} days.\n"
                f🔄"Review your current status: '{status}' and consider logging progress today!"
            )
        elif days_inactive == 0:
            return "You're on a roll! Keep the momentum going 💪"

    # Suggestion based on next milestone
    if milestones:
        next_milestone = sorted(milestones, key=lambda m: m["due"])[0]
        due_date = datetime.strptime(next_milestone["due"], "%Y-%m-%d").date()
        days_left = (due_date - today).days
        name = next_milestone["name"]

        if days_left < 0:
            return f"The milestone '{name}' was due {abs(days_left)} days ago. Consider updating your checkpoint."
        elif days_left == 0:
            return f"Today is the deadline for '{name}'! Time to wrap it up 🎯"
        else:
            return f"{days_left} day(s) left until the milestone '{name}'. Stay focused and make progress today!"

    return "No milestones found. You can add one to help guide your progress!"
