"""Project info panel widget."""

from textual.widgets import Static


class ProjectInfoPanel(Static):
    """Project name, title, disk info, settings."""

    DEFAULT_CSS = """
    ProjectInfoPanel {
        height: auto;
        padding: 1;
        border: solid #444444;
    }
    """

    def __init__(self):
        super().__init__("Project: ---")

    def update_state(self, snapshot):
        project = snapshot.project_name or "(none)"
        title = snapshot.title_name or "(none)"
        mode = "Delta" if snapshot.automation_mode else "Legacy"
        motors = "Off" if snapshot.motors_off else "On"
        mdac = "On" if snapshot.mdac_meters else "Off"
        lock = snapshot.transport_lock_layer or "---"

        lines = [
            f"Project: {project}",
            f"Title:   {title}",
            f"Mode:    {mode}",
            f"Motors:  {motors}",
            f"MDAC:    {mdac}",
            f"Tr Lock: Layer {lock}",
        ]
        self.update("\n".join(lines))
