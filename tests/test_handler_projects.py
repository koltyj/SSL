"""Tests for handlers/projects.py."""

import struct

from conftest import (
    build_rx_packet,
    payload_bool,
    payload_int,
    payload_short,
    payload_string,
)
from ssl_matrix_client.handlers.projects import (
    build_delete_project,
    build_delete_project_title,
    build_duplicate_title,
    build_get_directory_list,
    build_make_new_title_with_name,
    build_select_title,
    handle_directory_list_reply,
    handle_disk_info,
    handle_projects_ack,
)
from ssl_matrix_client.protocol import MessageCode


class TestDirectoryList:
    def test_parse(self, state):
        payload = (
            payload_string("/projects")
            + payload_short(1)
            + payload_string("Proj1")
            + payload_string("info")
            + payload_bool(True)
            + payload_string("12:00")
            + payload_string("2024-01-01")
            + payload_int(4096)
            + payload_short(0)  # terminator
        )
        rx = build_rx_packet(MessageCode.GET_DIRECTORY_LIST_REPLY, payload)
        handle_directory_list_reply(rx, state)
        assert len(state.directory) == 1
        entry = state.directory[0]
        assert entry.name == "Proj1"
        assert entry.is_dir is True
        assert entry.size == 4096
        assert entry.date_str == "2024-01-01"


class TestDiskInfo:
    def test_percent_calc(self, state):
        payload = payload_int(75) + payload_int(100) + payload_int(1)
        rx = build_rx_packet(MessageCode.SEND_DISK_INFO, payload)
        handle_disk_info(rx, state)
        assert state.disk_info.free_percent == 75
        assert state.disk_info.archive_done is True

    def test_zero_div_guard(self, state):
        payload = payload_int(0) + payload_int(0) + payload_int(0)
        rx = build_rx_packet(MessageCode.SEND_DISK_INFO, payload)
        handle_disk_info(rx, state)
        assert state.disk_info.free_percent == 0
        assert state.disk_info.archive_done is False


class TestProjectsAck:
    def test_ok_case_insensitive(self, state):
        rx = build_rx_packet(MessageCode.ACK_MAKE_NEW_PROJECT, payload_string("OK"))
        handle_projects_ack(rx, state)  # no error

    def test_error(self, state):
        rx = build_rx_packet(MessageCode.ACK_MAKE_NEW_PROJECT, payload_string("File exists"))
        handle_projects_ack(rx, state)  # logs warning


class TestBuildMakeNewTitleWithName:
    def test_builder(self):
        data = build_make_new_title_with_name(1000, 99, "Proj", "Title")
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_MAKE_NEW_PROJECT_TITLE_WITH_NAME
        # Verify payload contains both strings
        payload = data[16:]
        assert b"Proj\x00" in payload
        assert b"Title\x00" in payload


class TestBuildGetDirectoryList:
    def test_mode_and_path(self):
        data = build_get_directory_list(1000, 99, "/projects", mode=2)
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.GET_DIRECTORY_LIST
        assert data[16] == 2  # mode
        assert b"/projects\x00" in data[17:]


class TestBuildSelectTitle:
    def test_two_strings(self):
        data = build_select_title(1000, 99, "MyProj", "MyTitle")
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_SELECT_PROJECT_TITLE
        payload = data[16:]
        assert b"MyProj\x00" in payload
        assert b"MyTitle\x00" in payload


class TestBuildDeleteProject:
    def test_payload(self):
        data = build_delete_project(1000, 99, "OldProj")
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_DELETE_PROJECT
        assert b"OldProj\x00" in data[16:]


class TestBuildDeleteProjectTitle:
    def test_two_strings(self):
        data = build_delete_project_title(1000, 99, "Proj", "Title")
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_DELETE_PROJECT_TITLE
        payload = data[16:]
        assert b"Proj\x00" in payload
        assert b"Title\x00" in payload


class TestBuildDuplicateTitle:
    def test_payload(self):
        data = build_duplicate_title(1000, 99, "Proj", "Title")
        cmd = struct.unpack_from(">i", data, 0)[0]
        assert cmd == MessageCode.SEND_COPY_PROJECT_TITLE
        payload = data[16:]
        assert b"Proj\x00" in payload
        assert b"Title\x00" in payload
