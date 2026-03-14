"""Template save/load/diff/apply core logic for SSL Matrix session templates.

Templates capture restorable ConsoleState fields and write them to JSON files
at ~/.ssl-matrix/templates/. The CLI commands in Plan 03 call these functions
directly. XPatch data is stored for reference but never applied via SET
commands (all XPatch SET commands fail silently on this console).
"""

import dataclasses
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .handlers.channels import (
    build_set_chan_name,
    build_set_display_17_32,
    build_set_flip_scrib_strip,
)
from .handlers.delta import build_set_auto_mode
from .handlers.profiles import build_set_profile_for_daw_layer
from .handlers.routing import build_set_insert_name_v2, build_set_insert_to_chan_v2
from .handlers.total_recall import build_set_tr_enable
from .models import ConsoleState

log = logging.getLogger(__name__)

TEMPLATE_DIR: Path = Path.home() / ".ssl-matrix" / "templates"

# Fields included in the template snapshot (restorable only)
_RESTORABLE_FIELDS = (
    "channels",
    "daw_layers",
    "devices",
    "channel_inserts",
    "automation_mode",
    "tr_enabled",
    "display_17_32",
    "flip_scrib",
    "xpatch",
)

_XPATCH_SKIP_MSG = "XPatch: SET commands fail silently on this console -- stored for reference only"


# ---------------------------------------------------------------------------
# Directory helpers
# ---------------------------------------------------------------------------


def ensure_template_dir(template_dir: Optional[Path] = None) -> Path:
    """Create template directory if it does not exist. Returns the directory."""
    d = template_dir if template_dir is not None else TEMPLATE_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------------------
# Naming
# ---------------------------------------------------------------------------


def make_template_name(project_title: str) -> str:
    """Generate a filename for a new template.

    Sanitizes project_title: non-alphanumeric chars become underscores,
    result truncated to 20 characters. Empty titles or "(none)" become
    "unnamed". Appended with _YYYYMMDD_HHMMSS.json.
    """
    title = project_title.strip() if project_title else ""
    if not title or title == "(none)":
        prefix = "unnamed"
    else:
        sanitized = re.sub(r"[^A-Za-z0-9]", "_", title)
        prefix = sanitized[:20]
        if not prefix:
            prefix = "unnamed"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{ts}.json"


# ---------------------------------------------------------------------------
# Capture
# ---------------------------------------------------------------------------


def capture_template_state(state: ConsoleState) -> dict:
    """Serialize restorable fields from ConsoleState into a plain dict.

    Uses dataclasses.asdict for deep serialization of nested dataclasses.
    Fields excluded: desk, profiles, directory, disk_info, tr_snapshots,
    softkeys, synced, motors_off, mdac_meters, transport_lock_layer,
    project_name, title_name, selected_tr_index, chan_names_presets,
    chains, matrix_presets.
    """
    full = dataclasses.asdict(state)
    return {k: full[k] for k in _RESTORABLE_FIELDS}


# ---------------------------------------------------------------------------
# Save / Load
# ---------------------------------------------------------------------------


def save_template(
    state: ConsoleState,
    template_dir: Optional[Path] = None,
    daw_project_path: Optional[str] = None,
) -> Path:
    """Capture ConsoleState and write to a new JSON template file.

    Args:
        state: Current console state to snapshot.
        template_dir: Directory to write into (default: TEMPLATE_DIR).
        daw_project_path: Optional path to linked DAW project file.

    Returns:
        Path of the created file.
    """
    d = ensure_template_dir(template_dir)
    console_project_title = state.title_name or state.project_name
    filename = make_template_name(console_project_title)
    path = d / filename

    envelope = {
        "version": 1,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "console_project_title": console_project_title,
        "daw_project_path": daw_project_path,
        "state": capture_template_state(state),
    }
    path.write_text(json.dumps(envelope, indent=2))
    return path


def load_template(path: Path) -> dict:
    """Read and parse a template JSON file. Returns the envelope dict."""
    return json.loads(Path(path).read_text())


def show_template(path: Path) -> dict:
    """Inspect a template file. Alias for load_template."""
    return load_template(path)


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


def list_templates(template_dir: Optional[Path] = None) -> list:
    """List all template files in the directory, sorted by saved_at descending.

    Returns list of (filename, console_project_title, saved_at) tuples.
    """
    d = template_dir if template_dir is not None else TEMPLATE_DIR
    if not d.exists():
        return []

    results = []
    for p in sorted(d.glob("*.json")):
        try:
            data = json.loads(p.read_text())
            results.append(
                (p.name, data.get("console_project_title", ""), data.get("saved_at", ""))
            )
        except (json.JSONDecodeError, OSError) as exc:
            log.warning("Skipping unreadable template %s: %s", p.name, exc)

    # Sort by saved_at descending (ISO8601 strings sort lexicographically)
    results.sort(key=lambda t: t[2], reverse=True)
    return results


def delete_template(path: Path) -> None:
    """Delete a template file. Raises FileNotFoundError if it does not exist."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Template not found: {path}")
    p.unlink()


# ---------------------------------------------------------------------------
# Diff
# ---------------------------------------------------------------------------


def diff_template(template_data: dict, current_state: ConsoleState) -> dict:
    """Compare a loaded template against current ConsoleState.

    Returns a dict with keys: channels, profiles, routing, display, skipped.
    Each value is a list of human-readable change description strings.
    Empty list means no changes in that category.
    XPatch always appears in skipped.
    """
    tmpl = template_data.get("state", {})
    changes: dict = {
        "channels": [],
        "profiles": [],
        "routing": [],
        "display": [],
        "skipped": [_XPATCH_SKIP_MSG],
    }

    # --- channels ---
    tmpl_channels = tmpl.get("channels", [])
    for i, tmpl_ch in enumerate(tmpl_channels):
        if i < len(current_state.channels):
            cur_name = current_state.channels[i].name
            tmpl_name = tmpl_ch.get("name", "")
            if cur_name != tmpl_name:
                ch_num = tmpl_ch.get("number", i + 1)
                changes["channels"].append(f"Ch{ch_num}: '{tmpl_name}' -> '{cur_name}'")

    # --- profiles (daw_layers) ---
    tmpl_layers = tmpl.get("daw_layers", [])
    for i, tmpl_layer in enumerate(tmpl_layers):
        if i < len(current_state.daw_layers):
            cur_layer = current_state.daw_layers[i]
            tmpl_proto = tmpl_layer.get("protocol", 0)
            tmpl_profile = tmpl_layer.get("profile_name", "")
            layer_num = tmpl_layer.get("number", i + 1)
            if cur_layer.protocol != tmpl_proto:
                changes["profiles"].append(
                    f"Layer{layer_num} protocol: {tmpl_proto} -> {cur_layer.protocol}"
                )
            if cur_layer.profile_name != tmpl_profile:
                changes["profiles"].append(
                    f"Layer{layer_num} profile: '{tmpl_profile}' -> '{cur_layer.profile_name}'"
                )

    # --- routing (devices + channel_inserts) ---
    tmpl_devices = tmpl.get("devices", [])
    for i, tmpl_dev in enumerate(tmpl_devices):
        if i < len(current_state.devices):
            cur_dev = current_state.devices[i]
            dev_num = tmpl_dev.get("number", i + 1)
            tmpl_name = tmpl_dev.get("name", "")
            if cur_dev.name != tmpl_name:
                changes["routing"].append(
                    f"Device{dev_num} name: '{tmpl_name}' -> '{cur_dev.name}'"
                )
            tmpl_stereo = tmpl_dev.get("is_stereo", 0)
            if cur_dev.is_stereo != tmpl_stereo:
                changes["routing"].append(
                    f"Device{dev_num} stereo: {tmpl_stereo} -> {cur_dev.is_stereo}"
                )
            tmpl_assigned = tmpl_dev.get("is_assigned", 0)
            if cur_dev.is_assigned != tmpl_assigned:
                changes["routing"].append(
                    f"Device{dev_num} assigned: {tmpl_assigned} -> {cur_dev.is_assigned}"
                )

    tmpl_inserts = tmpl.get("channel_inserts", [])
    cur_inserts_map = {ci.channel: ci for ci in current_state.channel_inserts}
    for tmpl_ci in tmpl_inserts:
        chan = tmpl_ci.get("channel", 0)
        tmpl_inserts_list = tmpl_ci.get("inserts", [])
        cur_ci = cur_inserts_map.get(chan)
        cur_inserts_list = cur_ci.inserts if cur_ci else []
        if tmpl_inserts_list != cur_inserts_list:
            changes["routing"].append(
                f"Ch{chan} inserts: {tmpl_inserts_list} -> {cur_inserts_list}"
            )
        tmpl_chain = tmpl_ci.get("chain_name", "")
        cur_chain = cur_ci.chain_name if cur_ci else ""
        if tmpl_chain != cur_chain:
            changes["routing"].append(f"Ch{chan} chain: '{tmpl_chain}' -> '{cur_chain}'")

    # --- display ---
    for field_name, label in [
        ("automation_mode", "automation_mode"),
        ("tr_enabled", "tr_enabled"),
        ("display_17_32", "display_17_32"),
        ("flip_scrib", "flip_scrib"),
    ]:
        tmpl_val = tmpl.get(field_name)
        cur_val = getattr(current_state, field_name, None)
        if tmpl_val is not None and cur_val != tmpl_val:
            changes["display"].append(f"{label}: {tmpl_val} -> {cur_val}")

    return changes


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------


def build_apply_commands(
    template_data: dict,
    current_state: ConsoleState,
    categories: set,
    desk_serial: int,
    my_serial: int,
) -> list:
    """Build UDP command packets to restore template state.

    Args:
        template_data: Parsed template dict from load_template().
        current_state: Current console state (caller must hold _lock).
        categories: Set of category names to apply. May include:
            "channels", "profiles", "routing", "display", "all".
            XPatch SET commands are NEVER included regardless of category.
        desk_serial: Console serial number for packet header.
        my_serial: Remote serial number for packet header.

    Returns:
        List of (bytes, str) tuples: (UDP packet bytes, human-readable description).
        Routing commands are ordered: insert names first, then channel assignments.
    """
    if not categories:
        return []

    expand_all = "all" in categories
    tmpl = template_data.get("state", {})
    commands: list = []

    # --- channels ---
    if expand_all or "channels" in categories:
        tmpl_channels = tmpl.get("channels", [])
        for i, tmpl_ch in enumerate(tmpl_channels):
            if i < len(current_state.channels):
                cur_name = current_state.channels[i].name
                tmpl_name = tmpl_ch.get("name", "")
                if cur_name != tmpl_name:
                    ch_num = tmpl_ch.get("number", i + 1)
                    pkt = build_set_chan_name(desk_serial, my_serial, ch_num, tmpl_name)
                    commands.append((pkt, f"Set channel {ch_num} name: '{tmpl_name}'"))

    # --- profiles ---
    if expand_all or "profiles" in categories:
        tmpl_layers = tmpl.get("daw_layers", [])
        for i, tmpl_layer in enumerate(tmpl_layers):
            if i < len(current_state.daw_layers):
                cur_layer = current_state.daw_layers[i]
                tmpl_profile = tmpl_layer.get("profile_name", "")
                layer_num = tmpl_layer.get("number", i + 1)
                if cur_layer.profile_name != tmpl_profile:
                    pkt = build_set_profile_for_daw_layer(
                        desk_serial, my_serial, layer_num, tmpl_profile
                    )
                    commands.append((pkt, f"Set layer {layer_num} profile: '{tmpl_profile}'"))

    # --- routing: insert names FIRST, then assignments (Pitfall 3) ---
    if expand_all or "routing" in categories:
        # Step 1: device names
        tmpl_devices = tmpl.get("devices", [])
        for i, tmpl_dev in enumerate(tmpl_devices):
            if i < len(current_state.devices):
                cur_dev = current_state.devices[i]
                tmpl_name = tmpl_dev.get("name", "")
                dev_idx = tmpl_dev.get("number", i + 1) - 1  # 0-based index for builder
                if cur_dev.name != tmpl_name:
                    pkt = build_set_insert_name_v2(desk_serial, my_serial, dev_idx, tmpl_name)
                    commands.append((pkt, f"Set insert device {dev_idx + 1} name: '{tmpl_name}'"))

        # Step 2: channel insert assignments
        tmpl_inserts = tmpl.get("channel_inserts", [])
        cur_inserts_map = {ci.channel: ci for ci in current_state.channel_inserts}
        for tmpl_ci in tmpl_inserts:
            chan = tmpl_ci.get("channel", 0)
            tmpl_inserts_list = tmpl_ci.get("inserts", [])
            cur_ci = cur_inserts_map.get(chan)
            cur_inserts_list = cur_ci.inserts if cur_ci else []
            if tmpl_inserts_list != cur_inserts_list:
                for slot, insert_num in enumerate(tmpl_inserts_list, start=1):
                    pkt = build_set_insert_to_chan_v2(
                        desk_serial, my_serial, chan, insert_num, slot
                    )
                    commands.append(
                        (
                            pkt,
                            f"Assign insert {insert_num} to ch{chan} slot {slot}",
                        )
                    )

    # --- display ---
    if expand_all or "display" in categories:
        tmpl_auto = tmpl.get("automation_mode")
        if tmpl_auto is not None and current_state.automation_mode != tmpl_auto:
            pkt = build_set_auto_mode(desk_serial, my_serial, tmpl_auto)
            commands.append((pkt, f"Set automation_mode: {tmpl_auto}"))

        tmpl_d17 = tmpl.get("display_17_32")
        if tmpl_d17 is not None and current_state.display_17_32 != tmpl_d17:
            pkt = build_set_display_17_32(desk_serial, my_serial, tmpl_d17)
            commands.append((pkt, f"Set display_17_32: {tmpl_d17}"))

        tmpl_flip = tmpl.get("flip_scrib")
        if tmpl_flip is not None and current_state.flip_scrib != tmpl_flip:
            pkt = build_set_flip_scrib_strip(desk_serial, my_serial, tmpl_flip)
            commands.append((pkt, f"Set flip_scrib: {tmpl_flip}"))

        tmpl_tr = tmpl.get("tr_enabled")
        if tmpl_tr is not None and current_state.tr_enabled != tmpl_tr:
            pkt = build_set_tr_enable(desk_serial, my_serial, tmpl_tr)
            commands.append((pkt, f"Set tr_enabled: {tmpl_tr}"))

    # XPatch commands are NEVER added here — they silently fail on this console.

    return commands


# ---------------------------------------------------------------------------
# apply_template convenience wrapper
# ---------------------------------------------------------------------------


def apply_template(
    template_data: dict,
    current_state: ConsoleState,
    categories: Optional[set] = None,
    desk_serial: int = 0,
    my_serial: int = 0,
) -> list:
    """Convenience wrapper: build all apply commands for given categories.

    Returns list of (bytes, str) tuples. XPatch never included.
    """
    if categories is None:
        categories = {"all"}
    return build_apply_commands(template_data, current_state, categories, desk_serial, my_serial)
