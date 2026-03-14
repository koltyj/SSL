"""Capabilities audit: send read-only messages and log responses.

Connects to the SSL Matrix console, sends each Tier 0-1 (read-only) message,
and reports pass/fail based on whether a response was received within timeout.

Usage:
    python3 -m ssl-matrix-client.audit [--ip 192.168.1.2] [--timeout 3]
"""

import argparse
import logging
import socket
import time

from .handlers.connection import build_get_desk
from .protocol import BUFFER_SIZE, PORT, TO_REMOTE, MessageCode, RxMessage, TxMessage

log = logging.getLogger(__name__)

# Tier 0-1 read-only messages: (description, builder_func, expected_reply_cmd)
AUDIT_MESSAGES = [
    # Tier 0: Discovery & heartbeat
    (
        "GET_DESK",
        lambda ds, ms: build_get_desk(ms),
        MessageCode.GET_DESK_REPLY,
    ),
    # Tier 0: Channel names
    (
        "GET_CHAN_NAMES",
        lambda ds, ms: _build_simple(
            MessageCode.GET_CHAN_NAMES_AND_IMAGES, ds, ms, first=0, last=0
        ),
        MessageCode.GET_CHAN_NAMES_AND_IMAGES_REPLY,
    ),
    # Tier 0: Project name & title
    (
        "GET_PROJECT_NAME_AND_TITLE",
        lambda ds, ms: _build_header_only(MessageCode.GET_PROJECT_NAME_AND_TITLE, ds, ms),
        MessageCode.GET_PROJECT_NAME_AND_TITLE_REPLY,
    ),
    # Tier 0: DAW layer protocol (layer 1)
    (
        "GET_DAW_LAYER_PROTOCOL",
        lambda ds, ms: _build_with_byte(MessageCode.SEND_GET_DAW_LAYER_PROTOCOL, ds, ms, 1),
        MessageCode.ACK_GET_DAW_LAYER_PROTOCOL,
    ),
    # Tier 0: Profile list
    (
        "GET_PROFILES",
        lambda ds, ms: _build_header_only(MessageCode.SEND_GET_PROFILES, ds, ms),
        MessageCode.ACK_GET_PROFILES,
    ),
    # Tier 0: Transport lock
    (
        "GET_TRANSPORT_LOCK",
        lambda ds, ms: _build_header_only(MessageCode.SEND_GET_TRANSPORT_LOCK_DAW_LAYER, ds, ms),
        MessageCode.ACK_GET_TRANSPORT_LOCK_DAW_LAYER,
    ),
    # Tier 0: Automation mode
    (
        "GET_AUTOMATION_MODE",
        lambda ds, ms: _build_header_only(MessageCode.SEND_GET_AUTOMATION_MODE, ds, ms),
        MessageCode.ACK_GET_AUTOMATION_MODE,
    ),
    # Tier 0: Motors off
    (
        "GET_MOTORS_OFF",
        lambda ds, ms: _build_header_only(MessageCode.SEND_GET_MOTORS_OFF_TOUCH_EN, ds, ms),
        MessageCode.ACK_GET_MOTORS_OFF_TOUCH_EN,
    ),
    # Tier 0: MDAC meters
    (
        "GET_MDAC_METERS",
        lambda ds, ms: _build_header_only(MessageCode.SEND_GET_MDAC_METER_EN, ds, ms),
        MessageCode.ACK_GET_MDAC_METER_EN,
    ),
    # Tier 1: Insert matrix V2
    (
        "GET_INSERT_NAMES_V2",
        lambda ds, ms: _build_with_two_bytes(MessageCode.SEND_GET_INSERT_INFO_V2, ds, ms, 0, 0),
        MessageCode.ACK_GET_INSERT_INFO_V2,
    ),
    # Tier 1: Chain info V2
    (
        "GET_CHAIN_INFO_V2",
        lambda ds, ms: _build_with_two_bytes(MessageCode.SEND_GET_CHAIN_INFO_V2, ds, ms, 0, 0),
        MessageCode.ACK_GET_CHAIN_INFO_V2,
    ),
    # Tier 1: Channel matrix info V2
    (
        "GET_CHAN_MATRIX_INFO_V2",
        lambda ds, ms: _build_with_two_bytes(
            MessageCode.SEND_GET_CHAN_MATRIX_INFO_V2, ds, ms, 0, 0
        ),
        MessageCode.ACK_GET_CHAN_MATRIX_INFO_V2,
    ),
    # Tier 1: Matrix preset list
    (
        "GET_MATRIX_PRESET_LIST",
        lambda ds, ms: _build_header_only(MessageCode.SEND_GET_MATRIX_PRESET_LIST, ds, ms),
        MessageCode.ACK_GET_MATRIX_PRESET_LIST,
    ),
    # Tier 1: TR state
    (
        "GET_TR_STATE",
        lambda ds, ms: _build_header_only(MessageCode.SEND_GET_TR_STATE, ds, ms),
        MessageCode.ACK_GET_TR_STATE,
    ),
    # Tier 1: TR list
    (
        "GET_TR_LIST",
        lambda ds, ms: _build_header_only(MessageCode.GET_TR_LIST, ds, ms),
        MessageCode.GET_TR_LIST_REPLY,
    ),
    # Tier 1: Directory list
    (
        "GET_DIRECTORY_LIST",
        lambda ds, ms: _build_dir_list(ds, ms),
        MessageCode.GET_DIRECTORY_LIST_REPLY,
    ),
    # Tier 1: Chan names preset list
    (
        "GET_CHAN_NAMES_PRESET_LIST",
        lambda ds, ms: _build_header_only(MessageCode.SEND_GET_CHAN_NAMES_PRESET_LIST, ds, ms),
        MessageCode.ACK_GET_CHAN_NAMES_PRESET_LIST,
    ),
    # Tier 1: XPatch channel setup
    (
        "GET_XPATCH_CHAN_SETUP",
        lambda ds, ms: _build_header_only(MessageCode.GET_XPATCH_CHAN_SETUP, ds, ms),
        MessageCode.GET_XPATCH_CHAN_SETUP_REPLY,
    ),
    # Tier 1: XPatch routing data
    (
        "GET_XPATCH_ROUTING_DATA",
        lambda ds, ms: _build_header_only(MessageCode.GET_XPATCH_ROUTING_DATA, ds, ms),
        MessageCode.GET_XPATCH_ROUTING_DATA_REPLY,
    ),
    # Tier 1: XPatch presets list
    (
        "GET_XPATCH_PRESETS_LIST",
        lambda ds, ms: _build_header_only(MessageCode.GET_XPATCH_PRESETS_LIST, ds, ms),
        MessageCode.GET_XPATCH_PRESETS_LIST_REPLY,
    ),
    # Tier 1: XPatch chains list
    (
        "GET_XPATCH_CHAINS_LIST",
        lambda ds, ms: _build_header_only(MessageCode.GET_XPATCH_CHAINS_LIST, ds, ms),
        MessageCode.GET_XPATCH_CHAINS_LIST_REPLY,
    ),
    # Tier 1: XPatch MIDI setup
    (
        "GET_XPATCH_MIDI_SETUP",
        lambda ds, ms: _build_header_only(MessageCode.GET_XPATCH_MIDI_SETUP, ds, ms),
        MessageCode.GET_XPATCH_MIDI_SETUP_REPLY,
    ),
    # Tier 1: Display 17-32
    (
        "GET_DISPLAY_17_32",
        lambda ds, ms: _build_header_only(MessageCode.SEND_GET_DISPLAY_17_32, ds, ms),
        MessageCode.ACK_GET_DISPLAY_17_32,
    ),
    # Tier 1: Flip scrib strip
    (
        "GET_FLIP_SCRIB_STRIP",
        lambda ds, ms: _build_header_only(MessageCode.SEND_GET_FLIP_SCRIB_STRIP, ds, ms),
        MessageCode.ACK_GET_FLIP_SCRIB_STRIP,
    ),
]


def _build_header_only(cmd, desk_serial, my_serial):
    msg = TxMessage(cmd, desk_serial, my_serial)
    return msg.to_bytes()


def _build_with_byte(cmd, desk_serial, my_serial, val):
    msg = TxMessage(cmd, desk_serial, my_serial)
    msg.write_byte(val)
    return msg.to_bytes()


def _build_with_two_bytes(cmd, desk_serial, my_serial, a, b):
    msg = TxMessage(cmd, desk_serial, my_serial)
    msg.write_byte(a)
    msg.write_byte(b)
    return msg.to_bytes()


def _build_simple(cmd, desk_serial, my_serial, first=0, last=0):
    msg = TxMessage(cmd, desk_serial, my_serial)
    msg.write_byte(first)
    msg.write_byte(last)
    return msg.to_bytes()


def _build_dir_list(desk_serial, my_serial):
    msg = TxMessage(MessageCode.GET_DIRECTORY_LIST, desk_serial, my_serial)
    msg.write_byte(1)  # mode=dirs
    msg.write_string("/projects")
    return msg.to_bytes()


def _discover(sock, my_serial, console_ip, timeout=5):
    """Send GET_DESK and wait for reply. Returns desk_serial or None."""
    packet = build_get_desk(my_serial)
    sock.sendto(packet, (console_ip, PORT))
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            data, _addr = sock.recvfrom(BUFFER_SIZE)
            if len(data) < 16:
                continue
            rx = RxMessage(data)
            if (
                rx.cmd_code == MessageCode.GET_DESK_REPLY
                and rx.dest_code == TO_REMOTE
                and rx.remote_serial == my_serial
            ):
                return rx.desk_serial
        except socket.timeout:
            continue
    return None


def _wait_for_reply(sock, expected_cmd, my_serial, timeout=3):
    """Wait for a specific reply cmd. Returns (True, rx_bytes) or (False, None)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        remaining = deadline - time.time()
        if remaining <= 0:
            break
        sock.settimeout(remaining)
        try:
            data, _addr = sock.recvfrom(BUFFER_SIZE)
            if len(data) < 16:
                continue
            rx = RxMessage(data)
            if rx.dest_code != TO_REMOTE:
                continue
            if rx.cmd_code == expected_cmd:
                return True, len(data)
        except socket.timeout:
            break
    return False, 0


def run_audit(console_ip="192.168.1.2", timeout=3):
    """Run the capabilities audit and return results list."""
    import random

    my_serial = random.randint(-(2**31), 2**31 - 1)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if hasattr(socket, "SO_REUSEPORT"):
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.bind(("0.0.0.0", PORT))
    sock.settimeout(timeout)

    try:
        # Discover console
        print(f"Discovering console at {console_ip}...")
        desk_serial = _discover(sock, my_serial, console_ip, timeout=5)
        if desk_serial is None:
            print("FAIL: No console response. Is the console on and reachable?")
            return []

        print(f"Console found (serial={desk_serial}). Running audit...\n")

        results = []
        for name, builder, expected_reply in AUDIT_MESSAGES:
            # GET_DESK uses my_serial as desk_serial=0
            if name == "GET_DESK":
                packet = builder(0, my_serial)
            else:
                packet = builder(desk_serial, my_serial)

            sock.sendto(packet, (console_ip, PORT))
            ok, nbytes = _wait_for_reply(sock, expected_reply, my_serial, timeout=timeout)
            status = "PASS" if ok else "FAIL"
            results.append((name, status, nbytes))
            indicator = "+" if ok else "-"
            size_str = f" ({nbytes}B)" if ok else ""
            print(f"  [{indicator}] {name}{size_str}")
            time.sleep(0.05)  # small delay between messages

        # Summary
        passed = sum(1 for _, s, _ in results if s == "PASS")
        total = len(results)
        print(f"\n{passed}/{total} messages responded.")
        return results

    finally:
        sock.close()


def main():
    parser = argparse.ArgumentParser(description="SSL Matrix capabilities audit")
    parser.add_argument("--ip", default="192.168.1.2", help="Console IP address")
    parser.add_argument("--timeout", type=float, default=3, help="Response timeout (seconds)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING)
    run_audit(console_ip=args.ip, timeout=args.timeout)


if __name__ == "__main__":
    main()
