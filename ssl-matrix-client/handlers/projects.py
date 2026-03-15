"""Projects handler: project/title CRUD, directory listing, disk info.

Builders send commands to the console, handlers parse replies and update state.
Payload formats reverse-engineered from the SSL MatrixRemote protocol.
"""

import logging

from ..models import FileEntry
from ..protocol import MessageCode, TxMessage

log = logging.getLogger(__name__)


# --- Builders (Remote -> Console) ---


def build_get_project_name_and_title(desk_serial, my_serial):
    """Build GET_PROJECT_NAME_AND_TITLE (cmd=10). No payload."""
    msg = TxMessage(MessageCode.GET_PROJECT_NAME_AND_TITLE, desk_serial, my_serial)
    return msg.to_bytes()


def build_get_directory_list(desk_serial, my_serial, dir_path, mode=1):
    """Build GET_DIRECTORY_LIST (cmd=60).

    Payload: byte mode (0=all, 1=dirs, 2=files), string dirPath
    """
    msg = TxMessage(MessageCode.GET_DIRECTORY_LIST, desk_serial, my_serial)
    msg.write_byte(mode)
    msg.write_string(dir_path)
    return msg.to_bytes()


def build_make_new_project(desk_serial, my_serial):
    """Build SEND_MAKE_NEW_PROJECT (cmd=200). No payload."""
    msg = TxMessage(MessageCode.SEND_MAKE_NEW_PROJECT, desk_serial, my_serial)
    return msg.to_bytes()


def build_make_new_project_with_name(desk_serial, my_serial, name):
    """Build SEND_MAKE_NEW_PROJECT_WITH_NAME (cmd=264). Payload: string name."""
    msg = TxMessage(MessageCode.SEND_MAKE_NEW_PROJECT_WITH_NAME, desk_serial, my_serial)
    msg.write_string(name)
    return msg.to_bytes()


def build_make_new_title(desk_serial, my_serial, project):
    """Build SEND_MAKE_NEW_PROJECT_TITLE (cmd=210). Payload: string project."""
    msg = TxMessage(MessageCode.SEND_MAKE_NEW_PROJECT_TITLE, desk_serial, my_serial)
    msg.write_string(project)
    return msg.to_bytes()


def build_make_new_title_with_name(
    desk_serial, my_serial, proj, title, ch_flag=0, ch_preset="", mx_flag=0, mx_preset=""
):
    """Build SEND_MAKE_NEW_PROJECT_TITLE_WITH_NAME (cmd=212).

    Payload: string proj, string title, byte chFlag, string chPreset,
             byte mxFlag, string mxPreset
    """
    msg = TxMessage(MessageCode.SEND_MAKE_NEW_PROJECT_TITLE_WITH_NAME, desk_serial, my_serial)
    msg.write_string(proj)
    msg.write_string(title)
    msg.write_byte(ch_flag)
    msg.write_string(ch_preset)
    msg.write_byte(mx_flag)
    msg.write_string(mx_preset)
    return msg.to_bytes()


def build_make_new_project_with_presets(
    desk_serial, my_serial, proj, title, ch_flag=0, ch_preset="", mx_flag=0, mx_preset=""
):
    """Build SEND_MAKE_NEW_PROJECT_WITH_PRESET_OPTS (cmd=266).

    Payload: string proj, string title, byte chFlag, string chPreset,
             byte mxFlag, string mxPreset
    """
    msg = TxMessage(MessageCode.SEND_MAKE_NEW_PROJECT_WITH_PRESET_OPTS, desk_serial, my_serial)
    msg.write_string(proj)
    msg.write_string(title)
    msg.write_byte(ch_flag)
    msg.write_string(ch_preset)
    msg.write_byte(mx_flag)
    msg.write_string(mx_preset)
    return msg.to_bytes()


def build_select_title(desk_serial, my_serial, project, title):
    """Build SEND_SELECT_PROJECT_TITLE (cmd=220). Payload: string project, string title."""
    msg = TxMessage(MessageCode.SEND_SELECT_PROJECT_TITLE, desk_serial, my_serial)
    msg.write_string(project)
    msg.write_string(title)
    return msg.to_bytes()


def build_delete_project(desk_serial, my_serial, project):
    """Build SEND_DELETE_PROJECT (cmd=240). Payload: string project."""
    msg = TxMessage(MessageCode.SEND_DELETE_PROJECT, desk_serial, my_serial)
    msg.write_string(project)
    return msg.to_bytes()


def build_delete_project_title(desk_serial, my_serial, project, title):
    """Build SEND_DELETE_PROJECT_TITLE (cmd=230). Payload: string project, string title."""
    msg = TxMessage(MessageCode.SEND_DELETE_PROJECT_TITLE, desk_serial, my_serial)
    msg.write_string(project)
    msg.write_string(title)
    return msg.to_bytes()


def build_duplicate_title(desk_serial, my_serial, project, title):
    """Build SEND_COPY_PROJECT_TITLE (cmd=250). Payload: string project, string title."""
    msg = TxMessage(MessageCode.SEND_COPY_PROJECT_TITLE, desk_serial, my_serial)
    msg.write_string(project)
    msg.write_string(title)
    return msg.to_bytes()


# --- Handlers (Console -> Remote) ---


def handle_directory_list_reply(rx, state):
    """Parse GET_DIRECTORY_LIST_REPLY (cmd=61).

    Payload: string dirPath, then loop:
      short fileIndex (0=end), string name, string info,
      boolean isDir, string time, string date, int size
    """
    state.directory.clear()
    _dir_path = rx.get_string()
    while rx.remaining > 0:
        file_index = rx.get_short()
        if file_index == 0:
            break
        name = rx.get_string()
        info = rx.get_string()
        is_dir = rx.get_boolean()
        time_str = rx.get_string()
        date_str = rx.get_string()
        size = rx.get_int()
        state.directory.append(
            FileEntry(
                name=name,
                info=info,
                is_dir=is_dir,
                time_str=time_str,
                date_str=date_str,
                size=size,
            )
        )


def handle_disk_info(rx, state):
    """Parse SEND_DISK_INFO (cmd=72).

    Payload: int diskFree, int diskSize, int archiveDone (1=done)
    """
    disk_free = rx.get_int()
    disk_size = rx.get_int()
    archive_done = rx.get_int()
    if disk_size > 0:
        state.disk_info.free_percent = int((disk_free / disk_size) * 100)
    else:
        state.disk_info.free_percent = 0
    state.disk_info.archive_done = archive_done == 1


def handle_projects_ack(rx, state):
    """Handle generic ACK replies for project commands.

    Payload: string reply — "OK" or error message.
    Used for cmds: 201, 211, 213, 221, 231, 241, 251, 265, 267
    """
    reply = rx.get_string()
    if reply.lower() != "ok":
        log.warning("Projects ACK error: %s (cmd=%d)", reply, rx.cmd_code)
