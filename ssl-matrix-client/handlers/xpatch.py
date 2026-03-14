"""XPatch handler: crosspoint audio routing — presets, chains, routing, setup.

Combines XpatchPresetsHandler, XpatchChainsHandler, XpatchRoutingHandler,
and XpatchSetupHandler from the decompiled Java sources.
"""

import logging

from ..protocol import MessageCode, TxMessage
from ..models import XpatchPreset, XpatchChain, XpatchRoute

log = logging.getLogger(__name__)

NUM_CHANS = 16  # XPatch has 16 channels


# =============================================================================
# Setup (XpatchSetupHandler)
# =============================================================================

def build_get_chan_setup(desk_serial, my_serial):
    """Build GET_XPATCH_CHAN_SETUP (cmd=2060). No payload."""
    msg = TxMessage(MessageCode.GET_XPATCH_CHAN_SETUP, desk_serial, my_serial)
    return msg.to_bytes()


def build_set_input_minus_10db(desk_serial, my_serial, chan, selected):
    """Build SET_XPATCH_INPUT_MINUS10DB (cmd=2070). Payload: int chan, boolean selected."""
    msg = TxMessage(MessageCode.SET_XPATCH_INPUT_MINUS10DB, desk_serial, my_serial)
    msg.write_int(chan)
    msg.write_boolean(selected)
    return msg.to_bytes()


def build_set_output_minus_10db(desk_serial, my_serial, chan, selected):
    """Build SET_XPATCH_OUTPUT_MINUS10DB (cmd=2080). Payload: int chan, boolean selected."""
    msg = TxMessage(MessageCode.SET_XPATCH_OUTPUT_MINUS10DB, desk_serial, my_serial)
    msg.write_int(chan)
    msg.write_boolean(selected)
    return msg.to_bytes()


def build_set_chan_mode(desk_serial, my_serial, chan, mode):
    """Build SET_XPATCH_CHAN_MODE (cmd=2090). Payload: int chan, int mode."""
    msg = TxMessage(MessageCode.SET_XPATCH_CHAN_MODE, desk_serial, my_serial)
    msg.write_int(chan)
    msg.write_int(mode)
    return msg.to_bytes()


def build_set_device_name(desk_serial, my_serial, chan, name):
    """Build SET_XPATCH_DEVICE_NAME (cmd=3000). Payload: int chan, string name."""
    msg = TxMessage(MessageCode.SET_XPATCH_DEVICE_NAME, desk_serial, my_serial)
    msg.write_int(chan)
    msg.write_string(name)
    return msg.to_bytes()


def build_set_dest_name(desk_serial, my_serial, chan, name):
    """Build SET_XPATCH_DEST_NAME (cmd=3010). Payload: int chan, string name."""
    msg = TxMessage(MessageCode.SET_XPATCH_DEST_NAME, desk_serial, my_serial)
    msg.write_int(chan)
    msg.write_string(name)
    return msg.to_bytes()


def build_get_midi_setup(desk_serial, my_serial):
    """Build GET_XPATCH_MIDI_SETUP (cmd=3015). No payload."""
    msg = TxMessage(MessageCode.GET_XPATCH_MIDI_SETUP, desk_serial, my_serial)
    return msg.to_bytes()


def build_set_midi_enable(desk_serial, my_serial, enabled):
    """Build SET_XPATCH_MIDI_ENABLE (cmd=3020). Payload: boolean enabled."""
    msg = TxMessage(MessageCode.SET_XPATCH_MIDI_ENABLE, desk_serial, my_serial)
    msg.write_boolean(enabled)
    return msg.to_bytes()


def build_set_midi_channel(desk_serial, my_serial, channel):
    """Build SET_XPATCH_MIDI_CHANNEL (cmd=3040). Payload: int channel."""
    msg = TxMessage(MessageCode.SET_XPATCH_MIDI_CHANNEL, desk_serial, my_serial)
    msg.write_int(channel)
    return msg.to_bytes()


def build_clear_all(desk_serial, my_serial):
    """Build SEND_CLEAR_ALL (cmd=5000). No payload."""
    msg = TxMessage(MessageCode.SEND_CLEAR_ALL, desk_serial, my_serial)
    return msg.to_bytes()


# =============================================================================
# Routing (XpatchRoutingHandler)
# =============================================================================

def build_get_routing_data(desk_serial, my_serial):
    """Build GET_XPATCH_ROUTING_DATA (cmd=3050). No payload."""
    msg = TxMessage(MessageCode.GET_XPATCH_ROUTING_DATA, desk_serial, my_serial)
    return msg.to_bytes()


def build_set_route(desk_serial, my_serial, dest, src):
    """Build SET_XPATCH_ROUTE (cmd=3060). Payload: int dest, int src."""
    msg = TxMessage(MessageCode.SET_XPATCH_ROUTE, desk_serial, my_serial)
    msg.write_int(dest)
    msg.write_int(src)
    return msg.to_bytes()


# =============================================================================
# Presets (XpatchPresetsHandler)
# =============================================================================

def build_get_presets_list(desk_serial, my_serial):
    """Build GET_XPATCH_PRESETS_LIST (cmd=2000). No payload."""
    msg = TxMessage(MessageCode.GET_XPATCH_PRESETS_LIST, desk_serial, my_serial)
    return msg.to_bytes()


def build_set_preset_selected(desk_serial, my_serial, index):
    """Build SET_XPATCH_PRESET_SELECTED (cmd=2010). Payload: int index."""
    msg = TxMessage(MessageCode.SET_XPATCH_PRESET_SELECTED, desk_serial, my_serial)
    msg.write_int(index)
    return msg.to_bytes()


def build_get_preset_edited(desk_serial, my_serial):
    """Build GET_XPATCH_PRESET_EDITED (cmd=2013). No payload."""
    msg = TxMessage(MessageCode.GET_XPATCH_PRESET_EDITED, desk_serial, my_serial)
    return msg.to_bytes()


def build_set_preset_name(desk_serial, my_serial, index, name):
    """Build SET_XPATCH_PRESET_NAME (cmd=2020). Payload: int index, string name."""
    msg = TxMessage(MessageCode.SET_XPATCH_PRESET_NAME, desk_serial, my_serial)
    msg.write_int(index)
    msg.write_string(name)
    return msg.to_bytes()


def build_paste_preset(desk_serial, my_serial, src_index, dest_index):
    """Build PASTE_XPATCH_PRESET (cmd=2040). Payload: int src, int dest."""
    msg = TxMessage(MessageCode.PASTE_XPATCH_PRESET, desk_serial, my_serial)
    msg.write_int(src_index)
    msg.write_int(dest_index)
    return msg.to_bytes()


def build_swap_preset(desk_serial, my_serial, src_index, dest_index):
    """Build SWAP_XPATCH_PRESET (cmd=2050). Payload: int src, int dest."""
    msg = TxMessage(MessageCode.SWAP_XPATCH_PRESET, desk_serial, my_serial)
    msg.write_int(src_index)
    msg.write_int(dest_index)
    return msg.to_bytes()


def build_delete_preset(desk_serial, my_serial, index):
    """Build DELETE_XPATCH_PRESET (cmd=2030). Payload: int index."""
    msg = TxMessage(MessageCode.DELETE_XPATCH_PRESET, desk_serial, my_serial)
    msg.write_int(index)
    return msg.to_bytes()


def build_save_preset(desk_serial, my_serial, index):
    """Build SAVE_XPATCH_PRESET (cmd=2051). Payload: int index."""
    msg = TxMessage(MessageCode.SAVE_XPATCH_PRESET, desk_serial, my_serial)
    msg.write_int(index)
    return msg.to_bytes()


def build_send_preset_data(desk_serial, my_serial, index, name, srcs):
    """Build SEND_PRESET_DATA (cmd=2005). Payload: int index, string name, N x int src."""
    msg = TxMessage(MessageCode.SEND_PRESET_DATA, desk_serial, my_serial)
    msg.write_int(index)
    msg.write_string(name)
    for s in srcs:
        msg.write_int(s)
    return msg.to_bytes()


# =============================================================================
# Chains (XpatchChainsHandler)
# =============================================================================

def build_get_chains_list(desk_serial, my_serial):
    """Build GET_XPATCH_CHAINS_LIST (cmd=4000). No payload."""
    msg = TxMessage(MessageCode.GET_XPATCH_CHAINS_LIST, desk_serial, my_serial)
    return msg.to_bytes()


def build_set_chain_name(desk_serial, my_serial, index, name):
    """Build SET_XPATCH_CHAIN_NAME (cmd=4010). Payload: int index, string name."""
    msg = TxMessage(MessageCode.SET_XPATCH_CHAIN_NAME, desk_serial, my_serial)
    msg.write_int(index)
    msg.write_string(name)
    return msg.to_bytes()


def build_delete_chain(desk_serial, my_serial, index):
    """Build DELETE_XPATCH_CHAIN (cmd=4020). Payload: int index."""
    msg = TxMessage(MessageCode.DELETE_XPATCH_CHAIN, desk_serial, my_serial)
    msg.write_int(index)
    return msg.to_bytes()


def build_set_edit_chain(desk_serial, my_serial, index):
    """Build SET_XPATCH_EDIT_CHAIN (cmd=4030). Payload: int index."""
    msg = TxMessage(MessageCode.SET_XPATCH_EDIT_CHAIN, desk_serial, my_serial)
    msg.write_int(index)
    return msg.to_bytes()


def build_set_edit_chain_link_src(desk_serial, my_serial, link, src):
    """Build SET_XPATCH_EDIT_CHAIN_LINK_SRC (cmd=4060). Payload: int link, int src."""
    msg = TxMessage(MessageCode.SET_XPATCH_EDIT_CHAIN_LINK_SRC, desk_serial, my_serial)
    msg.write_int(link)
    msg.write_int(src)
    return msg.to_bytes()


def build_save_edit_chain(desk_serial, my_serial, index):
    """Build SAVE_XPATCH_EDIT_CHAIN (cmd=4080). Payload: int index."""
    msg = TxMessage(MessageCode.SAVE_XPATCH_EDIT_CHAIN, desk_serial, my_serial)
    msg.write_int(index)
    return msg.to_bytes()


def build_set_replace_mode(desk_serial, my_serial, selected):
    """Build SET_XPATCH_LINK_REPLACE_MODE (cmd=4090). Payload: boolean selected."""
    msg = TxMessage(MessageCode.SET_XPATCH_LINK_REPLACE_MODE, desk_serial, my_serial)
    msg.write_boolean(selected)
    return msg.to_bytes()


def build_send_chain_data(desk_serial, my_serial, index, name, links):
    """Build SEND_CHAIN_DATA (cmd=4005). Payload: int index, string name, N x int link."""
    msg = TxMessage(MessageCode.SEND_CHAIN_DATA, desk_serial, my_serial)
    msg.write_int(index)
    msg.write_string(name)
    for l in links:
        msg.write_int(l)
    return msg.to_bytes()


# =============================================================================
# Handlers (Console -> Remote)
# =============================================================================

def handle_chan_setup_reply(rx, state):
    """Parse GET_XPATCH_CHAN_SETUP_REPLY (cmd=2061).

    Payload: 16 channels x (int skip, boolean in10, boolean out10,
             int mode, string deviceName, string destName)
    """
    xp = state.xpatch
    for i in range(NUM_CHANS):
        chan = i + 1
        rx.get_int()  # skip
        in_10 = rx.get_boolean()
        out_10 = rx.get_boolean()
        mode = rx.get_int()
        dev_name = rx.get_string()
        dest_name = rx.get_string()
        if not dev_name:
            dev_name = f"Source {chan}"
        if not dest_name:
            dest_name = f"Destination {chan}"
        ch = xp.channels[i]
        ch.input_minus_10db = in_10
        ch.output_minus_10db = out_10
        ch.mode = mode
        ch.device_name = dev_name
        ch.dest_name = dest_name


def handle_input_minus_10db_reply(rx, state):
    """Parse SET_XPATCH_INPUT_MINUS10DB_REPLY (cmd=2071). Payload: int chan, boolean selected."""
    chan = rx.get_int()
    selected = rx.get_boolean()
    if 1 <= chan <= NUM_CHANS:
        state.xpatch.channels[chan - 1].input_minus_10db = selected


def handle_output_minus_10db_reply(rx, state):
    """Parse SET_XPATCH_OUTPUT_MINUS10DB_REPLY (cmd=2081). Payload: int chan, boolean selected."""
    chan = rx.get_int()
    selected = rx.get_boolean()
    if 1 <= chan <= NUM_CHANS:
        state.xpatch.channels[chan - 1].output_minus_10db = selected


def handle_chan_mode_reply(rx, state):
    """Parse SET_XPATCH_CHAN_MODE_REPLY (cmd=2091). Payload: int chan, int mode."""
    chan = rx.get_int()
    mode = rx.get_int()
    if 1 <= chan <= NUM_CHANS:
        state.xpatch.channels[chan - 1].mode = mode


def handle_device_name_reply(rx, state):
    """Parse SET_XPATCH_DEVICE_NAME_REPLY (cmd=3001). Payload: int chan, string name."""
    chan = rx.get_int()
    name = rx.get_string()
    if 1 <= chan <= NUM_CHANS:
        state.xpatch.channels[chan - 1].device_name = name or f"Source {chan}"


def handle_dest_name_reply(rx, state):
    """Parse SET_XPATCH_DEST_NAME_REPLY (cmd=3011). Payload: int chan, string name."""
    chan = rx.get_int()
    name = rx.get_string()
    if 1 <= chan <= NUM_CHANS:
        state.xpatch.channels[chan - 1].dest_name = name or f"Destination {chan}"


def handle_midi_setup_reply(rx, state):
    """Parse GET_XPATCH_MIDI_SETUP_REPLY (cmd=3016). Payload: boolean enabled, int channel."""
    state.xpatch.midi_enabled = rx.get_boolean()
    state.xpatch.midi_channel = rx.get_int()


def handle_midi_enable_reply(rx, state):
    """Parse SET_XPATCH_MIDI_ENABLE_REPLY (cmd=3021). Payload: boolean enabled."""
    state.xpatch.midi_enabled = rx.get_boolean()


def handle_midi_channel_reply(rx, state):
    """Parse SET_XPATCH_MIDI_CHANNEL_REPLY (cmd=3041). Payload: int channel."""
    state.xpatch.midi_channel = rx.get_int()


def handle_routing_data_reply(rx, state):
    """Parse GET_XPATCH_ROUTING_DATA_REPLY (cmd=3051).

    Payload: NUM_CHANS x (int skip, int display_src, int skip, boolean protect),
             then src disable booleans, src counts, chain src counts.
    """
    xp = state.xpatch
    xp.routes.clear()
    for dest in range(1, NUM_CHANS + 1):
        rx.get_int()  # skip
        display_src = rx.get_int()
        rx.get_int()  # skip
        protect = rx.get_boolean()
        xp.routes.append(XpatchRoute(dest=dest, display_src=display_src, protect=protect))
    # Remaining data: src disable flags and counts — consume but don't track yet
    # (numDevices + numChains) booleans, then same count ints, then numChans ints


def handle_presets_list_reply(rx, state):
    """Parse GET_XPATCH_PRESETS_LIST_REPLY (cmd=2001).

    Payload: loop of [int index (-1=end), boolean used, string name,
             NUM_CHANS x int src]
    """
    xp = state.xpatch
    xp.presets.clear()
    while rx.remaining > 0:
        index = rx.get_int()
        if index == -1:
            break
        used = rx.get_boolean()
        name = rx.get_string()
        srcs = []
        for _ in range(NUM_CHANS):
            srcs.append(rx.get_int())
        xp.presets.append(XpatchPreset(index=index, used=used, name=name, srcs=srcs))


def handle_preset_selected_reply(rx, state):
    """Parse SET_XPATCH_PRESET_SELECTED_REPLY (cmd=2012). Payload: int index."""
    state.xpatch.selected_preset = rx.get_int()


def handle_preset_edited_reply(rx, state):
    """Parse GET_XPATCH_PRESET_EDITED_REPLY (cmd=2014). Payload: boolean edited."""
    state.xpatch.preset_edited = rx.get_boolean()


def handle_chains_list_reply(rx, state):
    """Parse GET_XPATCH_CHAINS_LIST_REPLY (cmd=4001).

    Payload: loop of [int index (-1=end), boolean used, string name,
             numChainElements x int link]
    """
    xp = state.xpatch
    xp.chains.clear()
    while rx.remaining > 0:
        index = rx.get_int()
        if index == -1:
            break
        used = rx.get_boolean()
        name = rx.get_string()
        # Chain elements: read until we hit the next index or end
        # The Java code uses remote.getNumChainElements() — typically 8
        # We read available ints until we'd read the next chain's index
        links = []
        # Conservatively read 8 link ints (standard chain size)
        for _ in range(8):
            if rx.remaining >= 4:
                links.append(rx.get_int())
            else:
                break
        xp.chains.append(XpatchChain(index=index, used=used, name=name, links=links))


def handle_edit_chain_reply(rx, state):
    """Parse GET_XPATCH_EDIT_CHAIN_REPLY (cmd=4050).

    Payload: int chain, then numChainElements x (int skip, int src),
             boolean replaceMode
    """
    xp = state.xpatch
    chain = rx.get_int()
    xp.edit_chain = chain if chain != 0 else -1
    xp.edit_chain_links = []
    while rx.remaining >= 8:
        link_index = rx.get_int()
        src = rx.get_int()
        xp.edit_chain_links.append((link_index, src))
    if rx.remaining >= 1:
        xp.replace_mode = rx.get_boolean()


def handle_edit_chain_touched_reply(rx, state):
    """Parse GET_XPATCH_EDIT_CHAIN_TOUCHED_REPLY (cmd=4071). Payload: boolean touched."""
    state.xpatch.edit_chain_touched = rx.get_boolean()


def handle_replace_mode_reply(rx, state):
    """Parse SET_XPATCH_LINK_REPLACE_MODE_REPLY (cmd=4091). Payload: boolean mode."""
    state.xpatch.replace_mode = rx.get_boolean()
