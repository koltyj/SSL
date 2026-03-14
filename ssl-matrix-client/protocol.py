"""Wire format for SSL Matrix UDP protocol.

Implements TxMessage (outgoing) and RxMessage (incoming) with the 16-byte
header format and payload serialization matching the Java MatrixRemote app.
"""

import struct
from enum import IntEnum

# Protocol constants
TO_DESK = 1
TO_REMOTE = 2
PORT = 50081
BUFFER_SIZE = 2048


class MessageCode(IntEnum):
    """All 197 message codes from MessageCodes.java."""

    GET_DESK = 5
    GET_DESK_REPLY = 6
    SEND_HEARTBEAT = 7
    SET_OWN_NAME = 8
    SET_OWN_NAME_REPLY = 9
    GET_PROJECT_NAME_AND_TITLE = 10
    GET_PROJECT_NAME_AND_TITLE_REPLY = 11
    GET_SYNC = 15
    XPATCH_IPHONE_GET_DESK = 16
    GET_CHAN_NAMES_AND_IMAGES = 20
    GET_CHAN_NAMES_AND_IMAGES_REPLY = 21
    SET_DEFAULT_CHAN_NAMES = 28
    SET_DEFAULT_CHAN_NAMES_REPLY = 29
    SET_CHAN_NAMES = 30
    SET_CHAN_IMAGES = 31
    SET_CHAN_NAMES_REPLY = 32
    SET_CHAN_IMAGES_REPLY = 33
    GET_IS_CHAN_STEREO = 34
    GET_IS_CHAN_STEREO_REPLY = 35
    GET_IMAGE_LIB_NAMES = 40
    GET_IMAGE_LIB_NAMES_REPLY = 41
    GET_EXT_NAMES = 50
    GET_EXT_NAMES_REPLY = 51
    SET_EXT_NAMES = 52
    SET_EXT_NAMES_REPLY = 53
    GET_DIRECTORY_LIST = 60
    GET_DIRECTORY_LIST_REPLY = 61
    GET_MIX_PASSES_LIST = 62
    GET_MIX_PASSES_LIST_REPLY = 63
    GET_TR_LIST = 64
    GET_TR_LIST_REPLY = 65
    SET_FILE_INFO = 70
    SET_FILE_INFO_REPLY = 71
    SEND_DISK_INFO = 72
    ACK_SEND_DISK_INFO = 73
    GET_DISK_INFO = 74
    ACK_GET_DISK_INFO = 75
    SEND_UPDATE_BLOCK = 80
    ACK_UPDATE_BLOCK = 81
    SEND_SAVE_TO_FLASH = 90
    ACK_SAVE_TO_FLASH = 91
    SEND_CREATE_ZIP = 100
    ACK_CREATE_ZIP = 101
    SEND_REQUEST_FILE_BLOCK = 110
    ACK_REQUEST_FILE_BLOCK = 111
    SEND_WRITE_FILE_BLOCK = 120
    ACK_WRITE_FILE_BLOCK = 121
    SEND_UNZIP_FILE = 130
    ACK_UNZIP_FILE = 131
    SEND_MOVE_FILE = 140
    ACK_MOVE_FILE = 141
    SEND_COPY_FILE = 150
    ACK_COPY_FILE = 151
    SEND_DELETE_FILE = 160
    ACK_DELETE_FILE = 161
    SEND_RTC = 170
    ACK_RTC = 171
    SEND_SMART_COPY = 180
    ACK_SMART_COPY = 181
    SEND_SMART_COPY_WITH_NAME = 182
    ACK_SMART_COPY_WITH_NAME = 183
    SEND_TITLE_DETAILS_CHANGED = 190
    ACK_TITLE_DETAILS_CHANGED = 191
    SEND_MAKE_NEW_PROJECT = 200
    ACK_MAKE_NEW_PROJECT = 201
    SEND_MAKE_NEW_PROJECT_TITLE = 210
    ACK_MAKE_NEW_PROJECT_TITLE = 211
    SEND_MAKE_NEW_PROJECT_TITLE_WITH_NAME = 212
    ACK_MAKE_NEW_PROJECT_TITLE_WITH_NAME = 213
    SEND_SELECT_PROJECT_TITLE = 220
    ACK_SELECT_PROJECT_TITLE = 221
    SEND_DELETE_PROJECT_TITLE = 230
    ACK_DELETE_PROJECT_TITLE = 231
    SEND_DELETE_PROJECT = 240
    ACK_DELETE_PROJECT = 241
    SEND_COPY_PROJECT_TITLE = 250
    ACK_COPY_PROJECT_TITLE = 251
    SEND_COPY_PROJECT = 260
    ACK_COPY_PROJECT = 261
    SEND_ARCHIVE_DONE = 262
    ACK_ARCHIVE_DONE = 263
    SEND_MAKE_NEW_PROJECT_WITH_NAME = 264
    ACK_MAKE_NEW_PROJECT_WITH_NAME = 265
    SEND_MAKE_NEW_PROJECT_WITH_PRESET_OPTS = 266
    ACK_MAKE_NEW_PROJECT_WITH_PRESET_OPTS = 267
    SEND_SET_TR_ENABLE = 300
    ACK_SET_TR_ENABLE = 301
    SEND_GET_TR_STATE = 302
    ACK_GET_TR_STATE = 303
    SEND_TAKE_TR_SNAP = 310
    ACK_TAKE_TR_SNAP = 311
    SEND_SELECT_TR_SNAP = 320
    ACK_SELECT_TR_SNAP = 321
    SEND_DELETE_TR_SNAP = 330
    ACK_DELETE_TR_SNAP = 331
    SEND_COPY_TR_CHAN_DATA = 340
    ACK_COPY_TR_CHAN_DATA = 341
    SEND_SWOP_TR_CHAN_DATA = 350
    ACK_SWOP_TR_CHAN_DATA = 351
    SEND_SET_TR_ALL_CHANS = 360
    ACK_SET_TR_ALL_CHANS = 361
    SEND_SET_TR_CHAN = 370
    ACK_SET_TR_CHAN = 371
    SEND_GET_INSERT_NAMES = 400
    ACK_GET_INSERT_NAMES = 401
    SEND_SET_INSERT_NAMES = 410
    ACK_SET_INSERT_NAMES = 411
    SEND_GET_CHAIN_NAMES = 420
    ACK_GET_CHAIN_NAMES = 421
    SEND_SET_INSERT_TO_CHAN = 430
    ACK_SET_INSERT_TO_CHAN = 431
    SEND_GET_CHAN_MATRIX_INFO = 440
    ACK_GET_CHAN_MATRIX_INFO = 441
    SEND_GET_NUM_CHAINS = 450
    ACK_GET_NUM_CHAINS = 451
    SEND_NEW_EDIT_CHAIN = 460
    ACK_NEW_EDIT_CHAIN = 461
    SEND_SAVE_EDIT_CHAIN = 470
    ACK_SAVE_EDIT_CHAIN = 471
    SEND_GET_EDIT_CHAIN_DATA = 480
    ACK_GET_EDIT_CHAIN_DATA = 481
    SEND_ADD_DEV_TO_EDIT_CHAIN = 490
    ACK_ADD_DEV_TO_EDIT_CHAIN = 491
    SEND_CANCEL_EDIT_CHAIN = 500
    ACK_CANCEL_EDIT_CHAIN = 501
    SEND_ASSIGN_CHAIN_TO_CHAN = 510
    ACK_ASSIGN_CHAIN_TO_CHAN = 511
    SEND_DEASSIGN_CHAN = 520
    ACK_DEASSIGN_CHAN = 521
    SEND_REM_FROM_EDIT_CHAIN = 530
    ACK_REM_FROM_EDIT_CHAIN = 531
    SEND_EDIT_EXISTING_CHAIN = 540
    ACK_EDIT_EXISTING_CHAIN = 541
    SEND_DELETE_CHAIN = 550
    ACK_DELETE_CHAIN = 551
    SEND_RENAME_EDIT_CHAIN = 560
    ACK_RENAME_EDIT_CHAIN = 561
    SEND_INS_DEV_TO_EDIT_CHAIN = 570
    ACK_INS_DEV_TO_EDIT_CHAIN = 571
    SEND_GET_VALID_EDIT_CHAIN_DEVS = 580
    ACK_GET_VALID_EDIT_CHAIN_DEVS = 581
    SEND_GET_EDIT_KEYMAP_NAME = 600
    ACK_GET_EDIT_KEYMAP_NAME = 601
    SEND_SET_EDIT_KEYMAP_NAME = 610
    ACK_SET_EDIT_KEYMAP_NAME = 611
    SEND_GET_EDIT_KEYMAP_DATA = 620
    ACK_GET_EDIT_KEYMAP_DATA = 621
    SEND_GET_EDIT_KEYMAP_KEYCAPS = 630
    ACK_GET_EDIT_KEYMAP_KEYCAP = 631
    SEND_GET_EDIT_KEYMAP_SIZE = 640
    ACK_GET_EDIT_KEYMAP_SIZE = 641
    SEND_SET_USB_CMD = 650
    ACK_SET_USB_CMD = 651
    SEND_SET_KEYCAP_NAME = 660
    ACK_SET_KEYCAP_NAME = 661
    SEND_SET_KEY_BLANK = 670
    ACK_SET_KEY_BLANK = 671
    SEND_SET_SAVE_EDIT_KEYMAP = 680
    ACK_SET_SAVE_EDIT_KEYMAP = 681
    SEND_GET_MIDI_FUNCTION_LIST = 690
    ACK_GET_MIDI_FUNCTION_LIST = 691
    SEND_SET_MIDI_CMD = 700
    ACK_SET_MIDI_CMD = 701
    SEND_SET_NEW_MENU_CMD = 710
    ACK_SET_NEW_MENU_CMD = 711
    SEND_SET_MENU_SUB_KEYCAP_NAME = 720
    ACK_SET_MENU_SUB_KEYCAP_NAME = 721
    SEND_SET_MENU_SUB_MIDI_CMD = 730
    ACK_SET_MENU_SUB_MIDI_CMD = 731
    SEND_SET_MENU_SUB_USB_CMD = 740
    ACK_SET_MENU_SUB_USB_CMD = 741
    SEND_SET_MENU_SUB_BLANK_CMD = 750
    ACK_SET_MENU_SUB_BLANK_CMD = 751
    SEND_RESTART_CONSOLE = 760
    SEND_FOLLOW_KEY_STATE = 770
    ACK_FOLLOW_KEY_STATE = 771
    SEND_GET_PROFILE_FOR_DAW_LAYER = 800
    ACK_GET_PROFILE_FOR_DAW_LAYER = 801
    SEND_COPY_PROFILE_TO_NEW = 810
    ACK_COPY_PROFILE_TO_NEW = 811
    SEND_SET_PROFILE_FOR_DAW_LAYER = 820
    ACK_SET_PROFILE_FOR_DAW_LAYER = 821
    SEND_CLEAR_PROFILE_FOR_DAW_LAYER = 830
    ACK_CLEAR_PROFILE_FOR_DAW_LAYER = 831
    SEND_GET_PROFILES = 840
    ACK_GET_PROFILES = 841
    SEND_RENAME_PROFILES = 850
    ACK_RENAME_PROFILES = 851
    SEND_DELETE_PROFILES = 860
    ACK_DELETE_PROFILES = 861
    SEND_GET_TRANSPORT_LOCK_DAW_LAYER = 870
    ACK_GET_TRANSPORT_LOCK_DAW_LAYER = 871
    SEND_SET_TRANSPORT_LOCK_DAW_LAYER = 880
    ACK_SET_TRANSPORT_LOCK_DAW_LAYER = 881
    SEND_PROFILE_NAME_EXISTS = 890
    ACK_PROFILE_NAME_EXISTS = 891
    SEND_PROFILE_NAME_IN_USE = 900
    ACK_PROFILE_NAME_IN_USE = 901
    SEND_GET_DAW_LAYER_PROTOCOL = 910
    ACK_GET_DAW_LAYER_PROTOCOL = 911
    SEND_SAVE_PROFILE_AS = 920
    ACK_SAVE_PROFILE_AS = 921
    SEND_PROFILE_IS_READ_ONLY = 930
    ACK_PROFILE_IS_READ_ONLY = 931
    SEND_GET_PROFILE_PATH = 940
    ACK_GET_PROFILE_PATH = 941
    SEND_GET_CC_NAMES_LIST = 950
    ACK_GET_CC_NAMES_LIST = 951
    SEND_SET_CC_NAMES_LIST = 960
    ACK_SET_CC_NAMES_LIST = 961
    SEND_GET_FLIP_STATUS = 1000
    ACK_GET_FLIP_STATUS = 1001
    SEND_SET_FLIP_STATUS = 1010
    ACK_SET_FLIP_STATUS = 1011
    SEND_GET_HANDSHAKING_STATUS = 1020
    ACK_GET_HANDSHAKING_STATUS = 1021
    SEND_SET_HANDSHAKING_STATUS = 1030
    ACK_SET_HANDSHAKING_STATUS = 1031
    SEND_GET_AUTO_MODE_ON_SCRIBS_STATUS = 1040
    ACK_GET_AUTO_MODE_ON_SCRIBS_STATUS = 1041
    SEND_SET_AUTO_MODE_ON_SCRIBS_STATUS = 1050
    ACK_SET_AUTO_MODE_ON_SCRIBS_STATUS = 1051
    SEND_GET_DEFAULT_WHEEL_MODE_STATUS = 1060
    ACK_GET_DEFAULT_WHEEL_MODE_STATUS = 1061
    SEND_SET_DEFAULT_WHEEL_MODE_STATUS = 1070
    ACK_SET_DEFAULT_WHEEL_MODE_STATUS = 1071
    SEND_SET_FADER_DB_READOUT_STATUS = 1080
    ACK_SET_FADER_DB_READOUT_STATUS = 1081
    SEND_GET_FADER_DB_READOUT_STATUS = 1090
    ACK_GET_FADER_DB_READOUT_STATUS = 1091
    SEND_DELETE_MIX = 1100
    ACK_DELETE_MIX = 1101
    SEND_COPY_MIX = 1102
    ACK_COPY_MIX = 1103
    GET_XPATCH_PRESETS_LIST = 2000
    GET_XPATCH_PRESETS_LIST_REPLY = 2001
    SEND_PRESET_DATA = 2005
    SET_XPATCH_PRESET_SELECTED = 2010
    GET_XPATCH_PRESET_SELECTED = 2011
    SET_XPATCH_PRESET_SELECTED_REPLY = 2012
    GET_XPATCH_PRESET_EDITED = 2013
    GET_XPATCH_PRESET_EDITED_REPLY = 2014
    SET_XPATCH_PRESET_NAME = 2020
    DELETE_XPATCH_PRESET = 2030
    PASTE_XPATCH_PRESET = 2040
    SWAP_XPATCH_PRESET = 2050
    SAVE_XPATCH_PRESET = 2051
    GET_XPATCH_CHAN_SETUP = 2060
    GET_XPATCH_CHAN_SETUP_REPLY = 2061
    SET_XPATCH_INPUT_MINUS10DB = 2070
    SET_XPATCH_INPUT_MINUS10DB_REPLY = 2071
    SET_XPATCH_OUTPUT_MINUS10DB = 2080
    SET_XPATCH_OUTPUT_MINUS10DB_REPLY = 2081
    SET_XPATCH_CHAN_MODE = 2090
    SET_XPATCH_CHAN_MODE_REPLY = 2091
    SET_XPATCH_DEVICE_NAME = 3000
    SET_XPATCH_DEVICE_NAME_REPLY = 3001
    SET_XPATCH_DEST_NAME = 3010
    SET_XPATCH_DEST_NAME_REPLY = 3011
    GET_XPATCH_MIDI_SETUP = 3015
    GET_XPATCH_MIDI_SETUP_REPLY = 3016
    SET_XPATCH_MIDI_ENABLE = 3020
    SET_XPATCH_MIDI_ENABLE_REPLY = 3021
    SET_XPATCH_MIDI_CHANNEL = 3040
    SET_XPATCH_MIDI_CHANNEL_REPLY = 3041
    GET_XPATCH_ROUTING_DATA = 3050
    GET_XPATCH_ROUTING_DATA_REPLY = 3051
    SET_XPATCH_ROUTE = 3060
    GET_XPATCH_CHAINS_LIST = 4000
    GET_XPATCH_CHAINS_LIST_REPLY = 4001
    SEND_CHAIN_DATA = 4005
    SET_XPATCH_CHAIN_NAME = 4010
    DELETE_XPATCH_CHAIN = 4020
    SET_XPATCH_EDIT_CHAIN = 4030
    GET_XPATCH_EDIT_CHAIN = 4040
    GET_XPATCH_EDIT_CHAIN_REPLY = 4050
    SET_XPATCH_EDIT_CHAIN_LINK_SRC = 4060
    GET_XPATCH_EDIT_CHAIN_TOUCHED = 4070
    GET_XPATCH_EDIT_CHAIN_TOUCHED_REPLY = 4071
    SAVE_XPATCH_EDIT_CHAIN = 4080
    SET_XPATCH_LINK_REPLACE_MODE = 4090
    SET_XPATCH_LINK_REPLACE_MODE_REPLY = 4091
    SEND_CLEAR_ALL = 5000
    SET_DHCP = 5100
    SET_IP = 5110
    GET_IP_SETTINGS = 5120
    SET_IP_SETTINGS_REPLY = 5121
    TEST_COMMS = 5122
    TEST_COMMS_REPLY = 5123
    SEND_SET_DANTE_ENABLED = 5130
    SEND_GET_DANTE_ENABLED = 5132
    ACK_GET_DANTE_ENABLED = 5133
    SEND_GET_CPU_VERSION = 5134
    ACK_GET_CPU_VERSION = 5135
    # V2 insert matrix codes
    SEND_GET_INSERT_INFO_V2 = 10400
    ACK_GET_INSERT_INFO_V2 = 10401
    SEND_SET_INSERT_NAMES_V2 = 10410
    ACK_SET_INSERT_NAMES_V2 = 10411
    SEND_GET_CHAIN_INFO_V2 = 10420
    ACK_GET_CHAIN_INFO_V2 = 10421
    SEND_SET_INSERT_TO_CHAN_V2 = 10430
    ACK_SET_INSERT_TO_CHAN_V2 = 10431
    SEND_GET_CHAN_MATRIX_INFO_V2 = 10440
    ACK_GET_CHAN_MATRIX_INFO_V2 = 10441
    SEND_GET_NUM_CHAINS_V2 = 10450
    ACK_GET_NUM_CHAINS_V2 = 10451
    SEND_ASSIGN_CHAIN_TO_CHAN_V2 = 10510
    ACK_ASSIGN_CHAIN_TO_CHAN_V2 = 10511
    SEND_DEASSIGN_CHAN_V2 = 10520
    ACK_DEASSIGN_CHAN_V2 = 10521
    SEND_DELETE_CHAIN_V2 = 10550
    ACK_DELETE_CHAIN_V2 = 10551
    SEND_RENAME_CHAIN = 10560
    ACK_RENAME_CHAIN = 10561
    SEND_SAVE_INSERTS_TO_CHAIN = 10570
    ACK_SAVE_INSERTS_TO_CHAIN = 10571
    SEND_SET_CHAN_INSERTS = 10580
    ACK_SET_CHAN_INSERTS = 10581
    SEND_DELETE_CHAN_INSERT = 10600
    ACK_DELETE_CHAN_INSERT = 10601
    SEND_REORDER_CHAN_INSERTS = 10610
    ACK_REORDER_CHAN_INSERTS = 10611
    SEND_SET_CHAN_STEREO_INSERT = 10620
    ACK_SET_CHAN_STEREO_INSERT = 10621
    SEND_GET_MATRIX_PRESET_LIST = 10630
    ACK_GET_MATRIX_PRESET_LIST = 10631
    SEND_LOAD_MATRIX_PRESET = 10640
    ACK_LOAD_MATRIX_PRESET = 10641
    SEND_SAVE_MATRIX_PRESET = 10650
    ACK_SAVE_MATRIX_PRESET = 10651
    SEND_DELETE_MATRIX_PRESET = 10660
    ACK_DELETE_MATRIX_PRESET = 10661
    SEND_RENAME_MATRIX_PRESET = 10670
    ACK_RENAME_MATRIX_PRESET = 10671
    SEND_CLEAR_INSERTS = 10680
    ACK_CLEAR_INSERTS = 10681
    SEND_SET_LOWER_SCRIB_MODE = 10710
    ACK_SET_LOWER_SCRIB_MODE = 10711
    SEND_GET_LOWER_SCRIB_MODE = 10720
    ACK_GET_LOWER_SCRIB_MODE = 10721
    SEND_SET_DISPLAY_17_32 = 10730
    ACK_SET_DISPLAY_17_32 = 10731
    SEND_GET_DISPLAY_17_32 = 10740
    ACK_GET_DISPLAY_17_32 = 10741
    SEND_SET_FLIP_SCRIB_STRIP = 10750
    ACK_SET_FLIP_SCRIB_STRIP = 10751
    SEND_GET_FLIP_SCRIB_STRIP = 10760
    ACK_GET_FLIP_SCRIB_STRIP = 10761
    SEND_RENAME_CHAN_NAMES_PRESET = 10770
    ACK_RENAME_CHAN_NAMES_PRESET = 10771
    SEND_DELETE_CHAN_NAMES_PRESET = 10780
    ACK_DELETE_CHAN_NAMES_PRESET = 10781
    SEND_GET_CHAN_NAMES_PRESET_LIST = 10790
    ACK_GET_CHAN_NAMES_PRESET_LIST = 10791
    SEND_SAVE_CHAN_NAMES_PRESET = 10800
    ACK_SAVE_CHAN_NAMES_PRESET = 10801
    SEND_LOAD_CHAN_NAMES_PRESET = 10810
    ACK_LOAD_CHAN_NAMES_PRESET = 10811
    SEND_GET_AUTOMATION_MODE = 10900
    ACK_GET_AUTOMATION_MODE = 10901
    SEND_SET_AUTOMATION_MODE = 11000
    ACK_SET_AUTOMATION_MODE = 11001
    SEND_GET_MOTORS_OFF_TOUCH_EN = 11100
    ACK_GET_MOTORS_OFF_TOUCH_EN = 11101
    SEND_SET_MOTORS_OFF_TOUCH_EN = 11200
    ACK_SET_MOTORS_OFF_TOUCH_EN = 11201
    SEND_GET_MDAC_METER_EN = 11300
    ACK_GET_MDAC_METER_EN = 11301
    SEND_SET_MDAC_METER_EN = 11400
    ACK_SET_MDAC_METER_EN = 11401
    # Note: _2 variants removed — they were duplicate IntEnum aliases for
    # SEND_GET_AUTO_MODE_ON_SCRIBS_STATUS (1040) and ACK (1041).


# Protocol name lookup
PROTOCOL_NAMES = {0: "-", 1: "HUI", 2: "MCU", 3: "CC"}
PROTOCOL_BY_NAME = {"HUI": 1, "MCU": 2, "CC": 3, "NONE": 0, "-": 0}


class TxMessage:
    """Outgoing message builder matching Java TxMessage.

    Builds a bytearray with the 16-byte header followed by payload fields.
    """

    def __init__(self, cmd_code, desk_serial, my_serial):
        self._buf = bytearray(BUFFER_SIZE)
        self._index = 0
        self.write_int(cmd_code)
        self.write_int(TO_DESK)
        self.write_int(desk_serial)
        self.write_int(my_serial)

    def _check_space(self, nbytes):
        if self._index + nbytes > BUFFER_SIZE:
            raise ValueError(
                f"TxMessage overflow: need {nbytes} bytes at offset {self._index}, "
                f"buffer size {BUFFER_SIZE}"
            )

    def write_int(self, value):
        self._check_space(4)
        struct.pack_into(">i", self._buf, self._index, value)
        self._index += 4

    def write_short(self, value):
        self._check_space(2)
        struct.pack_into(">h", self._buf, self._index, value)
        self._index += 2

    def write_byte(self, value):
        self._check_space(1)
        self._buf[self._index] = value & 0xFF
        self._index += 1

    def write_boolean(self, value):
        self._check_space(1)
        self._buf[self._index] = 1 if value else 0
        self._index += 1

    def write_string(self, s):
        encoded = s.encode("ascii", errors="replace")
        self._check_space(len(encoded) + 1)
        self._buf[self._index : self._index + len(encoded)] = encoded
        self._index += len(encoded)
        self._buf[self._index] = 0  # null terminator
        self._index += 1

    def to_bytes(self):
        return bytes(self._buf[: self._index])


class RxMessage:
    """Incoming message parser matching Java RxMessage.

    Wraps received bytes with header accessors and cursor-based payload readers.
    """

    def __init__(self, data):
        self._data = bytes(data)
        self._length = len(data)
        self._index = 16  # skip header

    @property
    def cmd_code(self):
        return struct.unpack_from(">i", self._data, 0)[0]

    @property
    def dest_code(self):
        return struct.unpack_from(">i", self._data, 4)[0]

    @property
    def desk_serial(self):
        return struct.unpack_from(">i", self._data, 8)[0]

    @property
    def remote_serial(self):
        return struct.unpack_from(">i", self._data, 12)[0]

    @property
    def remaining(self):
        return max(0, self._length - self._index)

    def _check_remaining(self, nbytes):
        if self._index + nbytes > self._length:
            raise BufferError(
                f"RxMessage underflow: need {nbytes} bytes at offset {self._index}, "
                f"packet length {self._length}"
            )

    def get_int(self):
        self._check_remaining(4)
        val = struct.unpack_from(">i", self._data, self._index)[0]
        self._index += 4
        return val

    def get_short(self):
        self._check_remaining(2)
        val = struct.unpack_from(">h", self._data, self._index)[0]
        self._index += 2
        return val

    def get_byte(self):
        self._check_remaining(1)
        val = self._data[self._index]
        # Match Java's signed byte behavior
        if val > 127:
            val -= 256
        self._index += 1
        return val

    def get_unsigned_byte(self):
        self._check_remaining(1)
        val = self._data[self._index]
        self._index += 1
        return val

    def get_boolean(self):
        self._check_remaining(1)
        val = self._data[self._index] > 0
        self._index += 1
        return val

    def get_string(self):
        try:
            end = self._data.index(0, self._index)
        except ValueError:
            end = self._length
        s = self._data[self._index : end].decode("ascii", errors="replace")
        self._index = min(end + 1, self._length)
        return s

    def peek_int(self, byte_pos):
        pos = 16 + byte_pos
        if pos + 4 > self._length:
            raise BufferError(
                f"RxMessage peek_int: offset {pos}+4 exceeds packet length {self._length}"
            )
        return struct.unpack_from(">i", self._data, pos)[0]
