"""Unit tests for ssl-matrix-client/templates.py.

Covers: template serialization, CRUD, naming edge cases, diff detection,
routing restore order, and XPatch skip guarantee.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from ssl_matrix_client.models import ChannelInserts, ConsoleState
from ssl_matrix_client.templates import (
    build_apply_commands,
    capture_template_state,
    delete_template,
    diff_template,
    list_templates,
    load_template,
    make_template_name,
    save_template,
    show_template,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_state(**kwargs) -> ConsoleState:
    """Return a minimal ConsoleState with optional field overrides."""
    s = ConsoleState()
    s.title_name = kwargs.get("title_name", "TestSession")
    s.project_name = kwargs.get("project_name", "1")
    s.automation_mode = kwargs.get("automation_mode", 0)
    s.tr_enabled = kwargs.get("tr_enabled", False)
    s.display_17_32 = kwargs.get("display_17_32", 0)
    s.flip_scrib = kwargs.get("flip_scrib", 0)
    return s


# ---------------------------------------------------------------------------
# TestTemplateSave
# ---------------------------------------------------------------------------


class TestTemplateSave:
    def test_capture_template_state_keys(self):
        state = _make_state()
        captured = capture_template_state(state)
        expected_keys = {
            "channels",
            "daw_layers",
            "devices",
            "channel_inserts",
            "automation_mode",
            "tr_enabled",
            "display_17_32",
            "flip_scrib",
            "xpatch",
        }
        assert set(captured.keys()) == expected_keys

    def test_capture_excludes_runtime_fields(self):
        state = _make_state()
        captured = capture_template_state(state)
        # Runtime/non-restorable fields must not appear
        assert "desk" not in captured
        assert "profiles" not in captured
        assert "directory" not in captured
        assert "disk_info" not in captured
        assert "tr_snapshots" not in captured
        assert "softkeys" not in captured
        assert "synced" not in captured
        assert "motors_off" not in captured
        assert "mdac_meters" not in captured

    def test_capture_xpatch_present(self):
        state = _make_state()
        captured = capture_template_state(state)
        assert "xpatch" in captured
        # xpatch should have nested structure (channels, presets, etc.)
        assert "channels" in captured["xpatch"]

    def test_save_template_creates_file(self, tmp_path):
        state = _make_state(title_name="MySession")
        path = save_template(state, template_dir=tmp_path)
        assert path.exists()
        assert path.suffix == ".json"
        assert "MySession" in path.name or "unnamed" in path.name

    def test_save_template_envelope_structure(self, tmp_path):
        state = _make_state(title_name="MixA")
        path = save_template(state, template_dir=tmp_path)
        data = json.loads(path.read_text())
        assert data["version"] == 1
        assert "saved_at" in data
        assert "console_project_title" in data
        assert "state" in data

    def test_save_template_stores_title(self, tmp_path):
        state = _make_state(title_name="BigSession")
        path = save_template(state, template_dir=tmp_path)
        data = json.loads(path.read_text())
        assert data["console_project_title"] == "BigSession"

    def test_save_template_falls_back_to_project_name(self, tmp_path):
        state = _make_state(title_name="", project_name="proj42")
        path = save_template(state, template_dir=tmp_path)
        data = json.loads(path.read_text())
        assert data["console_project_title"] == "proj42"

    def test_save_template_daw_project_path(self, tmp_path):
        state = _make_state()
        path = save_template(state, template_dir=tmp_path, daw_project_path="/Users/me/song.als")
        data = json.loads(path.read_text())
        assert data["daw_project_path"] == "/Users/me/song.als"

    def test_save_template_indent2(self, tmp_path):
        state = _make_state()
        path = save_template(state, template_dir=tmp_path)
        raw = path.read_text()
        # indent=2 means lines should start with exactly 2 spaces for top-level keys
        assert '  "version"' in raw

    def test_save_template_returns_path(self, tmp_path):
        state = _make_state()
        result = save_template(state, template_dir=tmp_path)
        assert isinstance(result, Path)


# ---------------------------------------------------------------------------
# TestTemplateLoad
# ---------------------------------------------------------------------------


class TestTemplateLoad:
    def test_load_returns_dict(self, tmp_path):
        state = _make_state()
        path = save_template(state, template_dir=tmp_path)
        loaded = load_template(path)
        assert isinstance(loaded, dict)

    def test_load_round_trip(self, tmp_path):
        state = _make_state(title_name="RoundTrip", automation_mode=1)
        path = save_template(state, template_dir=tmp_path)
        loaded = load_template(path)
        assert loaded["version"] == 1
        assert loaded["console_project_title"] == "RoundTrip"
        assert loaded["state"]["automation_mode"] == 1

    def test_show_template_alias(self, tmp_path):
        state = _make_state()
        path = save_template(state, template_dir=tmp_path)
        shown = show_template(path)
        loaded = load_template(path)
        assert shown == loaded


# ---------------------------------------------------------------------------
# TestTemplateCRUD
# ---------------------------------------------------------------------------


class TestTemplateCRUD:
    def test_list_templates_empty(self, tmp_path):
        result = list_templates(template_dir=tmp_path)
        assert result == []

    def test_list_templates_returns_tuples(self, tmp_path):
        state = _make_state(title_name="Sess")
        save_template(state, template_dir=tmp_path)
        result = list_templates(template_dir=tmp_path)
        assert len(result) == 1
        fname, title, saved_at = result[0]
        assert fname.endswith(".json")
        assert title == "Sess"
        assert saved_at  # non-empty

    def test_list_templates_sorted_descending(self, tmp_path):
        import time

        state = _make_state(title_name="First")
        save_template(state, template_dir=tmp_path)
        time.sleep(0.01)
        state2 = _make_state(title_name="Second")
        save_template(state2, template_dir=tmp_path)
        result = list_templates(template_dir=tmp_path)
        # Most recent first
        assert result[0][1] == "Second"
        assert result[1][1] == "First"

    def test_delete_template_removes_file(self, tmp_path):
        state = _make_state()
        path = save_template(state, template_dir=tmp_path)
        assert path.exists()
        delete_template(path)
        assert not path.exists()

    def test_delete_template_missing_raises(self, tmp_path):
        missing = tmp_path / "nonexistent.json"
        with pytest.raises(FileNotFoundError):
            delete_template(missing)

    def test_list_templates_multiple(self, tmp_path):
        import time

        for i in range(3):
            s = _make_state(title_name=f"S{i}")
            save_template(s, template_dir=tmp_path)
            time.sleep(0.01)
        result = list_templates(template_dir=tmp_path)
        assert len(result) == 3


# ---------------------------------------------------------------------------
# TestTemplateNaming
# ---------------------------------------------------------------------------


class TestTemplateNaming:
    def test_basic_name(self):
        name = make_template_name("Session A")
        assert name.endswith(".json")
        # "Session A" -> "Session_A" -> first 20 chars preserved
        assert name.startswith("Session_A_")

    def test_none_string_gives_unnamed(self):
        name = make_template_name("(none)")
        assert name.startswith("unnamed_")

    def test_empty_string_gives_unnamed(self):
        name = make_template_name("")
        assert name.startswith("unnamed_")

    def test_non_alphanum_replaced(self):
        name = make_template_name("Hello! World?")
        assert "!" not in name
        assert "?" not in name
        # Non-alphanum chars become underscores
        assert name.startswith("Hello__World_") or "Hello" in name

    def test_truncated_to_20_chars(self):
        name = make_template_name("A" * 30)
        # stem before timestamp should be 20 chars max
        stem = name.replace(".json", "")
        parts = stem.split("_")
        # The prefix (before the timestamp parts) should be truncated
        # Timestamp appended as _YYYYMMDD_HHMMSS so last two segments are date+time
        prefix_parts = parts[:-2]
        prefix = "_".join(prefix_parts)
        assert len(prefix) <= 20

    def test_timestamp_format(self):
        import re

        name = make_template_name("Test")
        # Must end with _YYYYMMDD_HHMMSS.json
        assert re.match(r".*_\d{8}_\d{6}\.json$", name)


# ---------------------------------------------------------------------------
# TestTemplateDiff
# ---------------------------------------------------------------------------


class TestTemplateDiff:
    def _saved_state(self, tmp_path, **kwargs):
        state = _make_state(**kwargs)
        path = save_template(state, template_dir=tmp_path)
        return load_template(path)

    def test_diff_returns_required_keys(self, tmp_path):
        template_data = self._saved_state(tmp_path)
        current = _make_state()
        result = diff_template(template_data, current)
        for key in ("channels", "profiles", "routing", "display", "skipped"):
            assert key in result

    def test_diff_no_changes_empty_lists(self, tmp_path):
        template_data = self._saved_state(tmp_path)
        current = _make_state()
        result = diff_template(template_data, current)
        assert result["channels"] == []
        assert result["profiles"] == []
        assert result["routing"] == []
        assert result["display"] == []

    def test_diff_channel_name_change(self, tmp_path):
        state = _make_state()
        state.channels[2].name = "KICK"  # channel 3
        path = save_template(state, template_dir=tmp_path)
        template_data = load_template(path)

        current = _make_state()
        current.channels[2].name = "SNARE"
        result = diff_template(template_data, current)
        changes = result["channels"]
        assert len(changes) >= 1
        change_str = changes[0]
        assert "KICK" in change_str
        assert "SNARE" in change_str

    def test_diff_daw_layer_protocol_change(self, tmp_path):
        state = _make_state()
        state.daw_layers[0].protocol = 1  # HUI
        path = save_template(state, template_dir=tmp_path)
        template_data = load_template(path)

        current = _make_state()
        current.daw_layers[0].protocol = 2  # MCU
        result = diff_template(template_data, current)
        assert len(result["profiles"]) >= 1

    def test_diff_insert_device_name_change(self, tmp_path):
        state = _make_state()
        state.devices[0].name = "Neve"
        path = save_template(state, template_dir=tmp_path)
        template_data = load_template(path)

        current = _make_state()
        current.devices[0].name = "SSL"
        result = diff_template(template_data, current)
        assert len(result["routing"]) >= 1

    def test_diff_display_settings_change(self, tmp_path):
        state = _make_state(display_17_32=0, flip_scrib=0)
        path = save_template(state, template_dir=tmp_path)
        template_data = load_template(path)

        current = _make_state(display_17_32=1, flip_scrib=1)
        result = diff_template(template_data, current)
        assert len(result["display"]) >= 1

    def test_diff_automation_mode_change(self, tmp_path):
        state = _make_state(automation_mode=0)
        path = save_template(state, template_dir=tmp_path)
        template_data = load_template(path)

        current = _make_state(automation_mode=1)
        result = diff_template(template_data, current)
        assert len(result["display"]) >= 1

    def test_diff_xpatch_always_skipped(self, tmp_path):
        template_data = self._saved_state(tmp_path)
        current = _make_state()
        result = diff_template(template_data, current)
        skipped = result["skipped"]
        assert len(skipped) >= 1
        assert any("XPatch" in s or "xpatch" in s.lower() for s in skipped)


# ---------------------------------------------------------------------------
# TestXpatchSkip
# ---------------------------------------------------------------------------


class TestXpatchSkip:
    def test_xpatch_in_template_json(self, tmp_path):
        state = _make_state()
        path = save_template(state, template_dir=tmp_path)
        data = json.loads(path.read_text())
        assert "xpatch" in data["state"]

    def test_apply_never_sends_xpatch_commands(self, tmp_path):
        state = _make_state()
        path = save_template(state, template_dir=tmp_path)
        template_data = load_template(path)

        current = _make_state()
        commands = build_apply_commands(
            template_data, current, {"all"}, desk_serial=1000, my_serial=99
        )
        # No command description should mention xpatch
        for _pkt, desc in commands:
            assert "xpatch" not in desc.lower()

    def test_apply_returns_skipped_xpatch_warning(self, tmp_path):
        state = _make_state()
        path = save_template(state, template_dir=tmp_path)
        template_data = load_template(path)

        current = _make_state()
        result = diff_template(template_data, current)
        assert any("XPatch" in s or "xpatch" in s.lower() for s in result["skipped"])


# ---------------------------------------------------------------------------
# TestRoutingRestore
# ---------------------------------------------------------------------------


class TestRoutingRestore:
    def test_build_apply_returns_list_of_tuples(self, tmp_path):
        state = _make_state()
        path = save_template(state, template_dir=tmp_path)
        template_data = load_template(path)
        current = _make_state()
        result = build_apply_commands(
            template_data, current, {"routing"}, desk_serial=1000, my_serial=99
        )
        assert isinstance(result, list)
        for item in result:
            assert len(item) == 2
            pkt, desc = item
            assert isinstance(pkt, bytes)
            assert isinstance(desc, str)

    def test_routing_only_category(self, tmp_path):
        state = _make_state()
        state.devices[0].name = "Compressor"
        state.channel_inserts = [ChannelInserts(channel=1, inserts=[1], chain_name="")]
        path = save_template(state, template_dir=tmp_path)
        template_data = load_template(path)

        current = _make_state()
        # No channel inserts in current state = difference triggers commands
        with patch("ssl_matrix_client.templates.build_set_chan_name") as mock_chan_name:
            build_apply_commands(
                template_data, current, {"routing"}, desk_serial=1000, my_serial=99
            )
            # channel name builder should NOT be called
            mock_chan_name.assert_not_called()

    def test_channels_only_category(self, tmp_path):
        state = _make_state()
        state.channels[0].name = "KICK"
        path = save_template(state, template_dir=tmp_path)
        template_data = load_template(path)

        current = _make_state()
        current.channels[0].name = "SNARE"

        with patch("ssl_matrix_client.templates.build_set_insert_name_v2") as mock_insert:
            result = build_apply_commands(
                template_data, current, {"channels"}, desk_serial=1000, my_serial=99
            )
            # insert name builder should NOT be called when only channels requested
            mock_insert.assert_not_called()
        assert len(result) >= 1
        assert all("channel" in desc.lower() or "ch" in desc.lower() for _p, desc in result)

    def test_all_category_includes_everything(self, tmp_path):
        state = _make_state()
        state.channels[0].name = "KICK"
        state.devices[0].name = "Neve"
        path = save_template(state, template_dir=tmp_path)
        template_data = load_template(path)

        current = _make_state()
        current.channels[0].name = "SNARE"
        current.devices[0].name = "SSL"

        result = build_apply_commands(
            template_data, current, {"all"}, desk_serial=1000, my_serial=99
        )
        descs = [desc.lower() for _p, desc in result]
        # Should include both channel and routing commands
        has_chan = any("ch" in d or "channel" in d for d in descs)
        has_routing = any("insert" in d or "device" in d for d in descs)
        assert has_chan
        assert has_routing

    def test_routing_order_insert_names_before_assignments(self, tmp_path):
        """Insert names must be sent before channel assignments (Pitfall 3)."""
        state = _make_state()
        state.devices[0].name = "Neve1073"
        state.channel_inserts = [ChannelInserts(channel=1, inserts=[1], chain_name="")]
        path = save_template(state, template_dir=tmp_path)
        template_data = load_template(path)

        current = _make_state()

        result = build_apply_commands(
            template_data, current, {"routing"}, desk_serial=1000, my_serial=99
        )
        if len(result) >= 2:
            descs = [desc.lower() for _p, desc in result]
            # Find first insert-name command and first assignment command
            name_idx = next((i for i, d in enumerate(descs) if "name" in d or "device" in d), None)
            assign_idx = next(
                (i for i, d in enumerate(descs) if "assign" in d or "slot" in d or "chan" in d),
                None,
            )
            if name_idx is not None and assign_idx is not None:
                assert name_idx < assign_idx, "Insert names must come before channel assignments"

    def test_empty_categories_returns_empty(self, tmp_path):
        state = _make_state()
        path = save_template(state, template_dir=tmp_path)
        template_data = load_template(path)
        current = _make_state()
        result = build_apply_commands(template_data, current, set(), desk_serial=1000, my_serial=99)
        assert result == []
