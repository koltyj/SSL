"""Wire format for SSL Sigma console UDP protocol (EXPERIMENTAL).

Implements SigmaTxMessage (outgoing) and SigmaRxMessage (incoming) with the
24-byte header format and payload serialization reverse-engineered from the
SSL Sigma Remote APK v2.1.33 via Ghidra decompilation of libjuce_jni.so.

The Sigma protocol uses a different framing format from the Matrix protocol.
All numeric values are big-endian. The magic byte is 0x53 ('S') and
ProductType is always 4 for Sigma consoles.
"""

import struct
from enum import IntEnum

# ---------------------------------------------------------------------------
# Protocol constants
# ---------------------------------------------------------------------------

SIGMA_MAGIC = 0x53  # 'S'
SIGMA_PRODUCT_TYPE = 4
SIGMA_PORT = 50081  # inferred from ELF binary; not confirmed from decompiled code paths
SIGMA_HANDSHAKE_MASTER_PORT = 29940
SIGMA_HANDSHAKE_SLAVE_PORT = 29939
SIGMA_MULTICAST_1 = "225.0.0.37"
SIGMA_MULTICAST_2 = "225.0.0.38"
SIGMA_BUFFER_SIZE = 2048
SIGMA_FIXED_PACKET_SIZE = 0x18  # 24 bytes
SIGMA_MAX_PACKET_SIZE = 0x32  # 50 bytes


# ---------------------------------------------------------------------------
# Payload type enum
# ---------------------------------------------------------------------------


class PayloadType(IntEnum):
    """Payload encoding type (top byte of offset 0x08 in wire format)."""

    FLOAT = 1  # float32 BE at offset 0x14
    UINT_PAIR = 2  # uint32 at 0x14 + uint32 at 0x18
    STRING = 3  # 7-bit ASCII at offset 0x14
    NONE = 4  # no payload
    UINT_AS_FLOAT = 5  # uint32 reinterpreted as float


# ---------------------------------------------------------------------------
# Message ID enum
# ---------------------------------------------------------------------------


class SigmaMessageId(IntEnum):
    """All known Sigma message IDs from Ghidra decompilation.

    Grouped by console section. The sub_param field typically carries the
    channel/slot number for per-channel messages.
    """

    # --- Channel controls (per-channel, slot = channel number) ---
    CHAN_SELECT = 0x1C
    CHAN_SELECT_ALL_16 = 0x1F
    SOLO = 0x26
    MUTE = 0x27
    PHASE = 0x28
    SOLO_SAFE = 0x29
    PAN_MODE = 0x2A
    FADER = 0x2B
    PAN = 0x2C
    CHAN_BTN_1 = 0x70
    CHAN_BTN_2 = 0x71
    CHAN_BTN_3 = 0x72
    CHAN_BTN_4 = 0x73
    CHAN_BTN_5 = 0x74
    CHAN_BTN_6 = 0x75
    CHAN_BTN_7 = 0x76
    CHAN_BTN_SLOT = 0x77
    CHAN_BTN_ALIAS = 0x78
    CHAN_SCRIBBLE = 0x79
    CHAN_BTN_8 = 0x7A

    # --- Monitor section ---
    MON_SRC_1 = 0x53
    MON_SRC_2 = 0x54
    MON_SRC_3 = 0x55
    MON_SRC_4 = 0x56
    MON_SRC_5 = 0x57
    MON_SRC_6 = 0x58
    MON_SRC_7 = 0x59

    # --- Headphone section ---
    HP_SRC_1 = 0x5A
    HP_SRC_2 = 0x5B
    HP_SRC_3 = 0x5C
    HP_SRC_4 = 0x5D

    # --- Insert section ---
    INSERT_A = 0x5E
    INSERT_B = 0x5F
    INSERT_A_SUM = 0x60
    INSERT_B_SUM = 0x61

    # --- Level / metering ---
    LEVEL_READOUT = 0x4E
    LEVEL_FADER = 0x4F
    METER_MODE = 0x50
    LEVEL_TOGGLE = 0x51
    METER_SOURCE = 0x52
    LEVEL_FLAG = 0x7D

    # --- Dim section ---
    DIM_LEVEL = 0x6A
    DIM_SECONDARY = 0x6B

    # --- Settings ---
    SETUP_BTN = 0x2D
    SETTINGS_BTN_1 = 0x62
    SETTINGS_BTN_2 = 0x63
    SETTINGS_BTN_3 = 0x64
    SETTINGS_BTN_4 = 0x65
    SETTINGS_BTN_5 = 0x68

    # --- Misc / network ---
    NET_MASTER_SLAVE = 0x33
    IP_OCTET_1 = 0x34
    IP_OCTET_2 = 0x35
    IP_OCTET_3 = 0x36
    IP_OCTET_4 = 0x37
    SUBNET_OCTET_1 = 0x38
    SUBNET_OCTET_2 = 0x39
    SUBNET_OCTET_3 = 0x3A
    SUBNET_OCTET_4 = 0x3B
    GW_DNS_1 = 0x3C
    GW_DNS_2 = 0x3D
    GW_DNS_3 = 0x3E
    GW_DNS_4 = 0x3F
    GW_DNS_5 = 0x40
    GW_DNS_6 = 0x41
    GW_DNS_7 = 0x42
    GW_DNS_8 = 0x43
    TALKBACK_MODE = 0x44
    OSCILLATOR = 0x45
    LISTENBACK = 0x46
    SCENE_RECALL = 0x47
    CONNECTION_STATUS = 0x48
    DAW_CONTROL = 0x49
    MISC_SLIDER = 0x4A
    LABEL_TEXT_1 = 0x4B
    LABEL_TEXT_2 = 0x4C

    # --- Connection / handshake ---
    REMOTE_RELAY = 0x69
    KEEPALIVE = 0x99
    HANDSHAKE = 0x9D
    UNICAST_MODE = 0x9F
    CONNECTION_MODE = 0xA0


# ---------------------------------------------------------------------------
# Value encoding helpers
# ---------------------------------------------------------------------------


def bool_to_sigma_float(value: bool) -> float:
    """Encode a boolean as a Sigma float (1.0 for True, 0.0 for False)."""
    return 1.0 if value else 0.0


def sigma_float_to_bool(value: float) -> bool:
    """Decode a Sigma float to boolean (value > 0.0 means True)."""
    return value > 0.0


def uint_to_sigma_float(value: int) -> float:
    """Reinterpret-cast a uint32 to float32 (same bit pattern).

    This matches the VectorFloatToUnsigned pattern in the Sigma firmware
    where an integer value is stored in the IEEE 754 float bit pattern.
    """
    return struct.unpack(">f", struct.pack(">I", value & 0xFFFFFFFF))[0]


def sigma_float_to_uint(value: float) -> int:
    """Reinterpret-cast a float32 to uint32 (same bit pattern)."""
    return struct.unpack(">I", struct.pack(">f", value))[0]


# ---------------------------------------------------------------------------
# Outgoing message builder
# ---------------------------------------------------------------------------


class SigmaTxMessage:
    """Builds an outgoing Sigma UDP packet.

    Wire format::

        Offset  Size  Field
        0x00    1     Magic (0x53)
        0x01    3     Padding / header extension
        0x04    4     ProductType (uint32 BE, always 4)
        0x08    4     MsgId composite (uint32 BE): (payload_type << 24) | msg_id
        0x0C    4     SubParam (uint32 BE): channel/slot number
        0x10    4     Reserved padding
        0x14    4+    Payload (varies by PayloadType)
    """

    def __init__(self, payload_type: int, msg_id: int, sub_param: int = 0):
        self._payload_type = PayloadType(payload_type)
        self._msg_id = msg_id
        self._sub_param = sub_param
        self._payload = b""

    def _build_header(self) -> bytearray:
        """Build the 20-byte header (offsets 0x00 through 0x13)."""
        buf = bytearray(0x14)
        # 0x00: magic byte
        buf[0] = SIGMA_MAGIC
        # 0x01-0x03: padding (zeros)
        # 0x04: product type
        struct.pack_into(">I", buf, 0x04, SIGMA_PRODUCT_TYPE)
        # 0x08: msg_id composite = (payload_type << 24) | msg_id
        composite = (int(self._payload_type) << 24) | (self._msg_id & 0x00FFFFFF)
        struct.pack_into(">I", buf, 0x08, composite)
        # 0x0C: sub_param
        struct.pack_into(">I", buf, 0x0C, self._sub_param)
        # 0x10: reserved (zeros)
        return buf

    def set_float_payload(self, value: float):
        """Set a float32 BE payload at offset 0x14."""
        self._payload = struct.pack(">f", value)

    def set_uint_pair_payload(self, val1: int, val2: int):
        """Set two uint32 BE values at offsets 0x14 and 0x18."""
        self._payload = struct.pack(">II", val1, val2)

    def set_string_payload(self, text: str):
        """Set a 7-bit ASCII string payload at offset 0x14."""
        self._payload = bytes(ord(c) & 0x7F for c in text)

    def to_bytes(self) -> bytes:
        """Serialize the complete packet."""
        return bytes(self._build_header() + self._payload)

    # --- Convenience builders ---

    @classmethod
    def build_float_message(cls, msg_id: int, sub_param: int, value: float) -> "SigmaTxMessage":
        """Build a message with a float32 payload (PayloadType.FLOAT)."""
        msg = cls(PayloadType.FLOAT, msg_id, sub_param)
        msg.set_float_payload(value)
        return msg

    @classmethod
    def build_bool_message(cls, msg_id: int, sub_param: int, value: bool) -> "SigmaTxMessage":
        """Build a boolean message (encoded as 1.0 / 0.0 float)."""
        msg = cls(PayloadType.FLOAT, msg_id, sub_param)
        msg.set_float_payload(bool_to_sigma_float(value))
        return msg

    @classmethod
    def build_uint_message(cls, msg_id: int, sub_param: int, value: int) -> "SigmaTxMessage":
        """Build a uint message (uint32 reinterpreted as float, PayloadType.UINT_AS_FLOAT)."""
        msg = cls(PayloadType.UINT_AS_FLOAT, msg_id, sub_param)
        msg.set_float_payload(uint_to_sigma_float(value))
        return msg

    @classmethod
    def build_string_message(cls, msg_id: int, sub_param: int, text: str) -> "SigmaTxMessage":
        """Build a string message (7-bit ASCII, PayloadType.STRING)."""
        msg = cls(PayloadType.STRING, msg_id, sub_param)
        msg.set_string_payload(text)
        return msg

    @classmethod
    def build_handshake(cls, msg_id: int) -> "SigmaTxMessage":
        """Build a handshake/keepalive message (no payload, PayloadType.NONE)."""
        return cls(PayloadType.NONE, msg_id, 0)


# ---------------------------------------------------------------------------
# Incoming message parser
# ---------------------------------------------------------------------------


class SigmaRxMessage:
    """Parses an incoming Sigma UDP packet.

    Validates the magic byte and product type, then extracts the payload
    according to the PayloadType encoded in the msg_id composite field.
    """

    def __init__(self, data: bytes):
        # Minimum viable packet is the 20-byte header (0x14).
        # SIGMA_FIXED_PACKET_SIZE (24) applies to numeric payloads;
        # NONE-type and short string packets can be smaller.
        _MIN_HEADER = 0x14
        if len(data) < _MIN_HEADER:
            raise ValueError(
                f"Packet too short: {len(data)} bytes, minimum header is {_MIN_HEADER}"
            )

        self._data = bytes(data)

        # Validate magic byte
        if self._data[0] != SIGMA_MAGIC:
            raise ValueError(
                f"Invalid magic byte: 0x{self._data[0]:02X}, expected 0x{SIGMA_MAGIC:02X}"
            )

        # Validate product type
        pt = struct.unpack_from(">I", self._data, 0x04)[0]
        if pt != SIGMA_PRODUCT_TYPE:
            raise ValueError(f"Invalid product type: {pt}, expected {SIGMA_PRODUCT_TYPE}")

        # Parse msg_id composite at offset 0x08
        composite = struct.unpack_from(">I", self._data, 0x08)[0]
        self._payload_type_raw = (composite >> 24) & 0xFF
        self._msg_id = composite & 0x00FFFFFF

        # Parse sub_param at offset 0x0C
        self._sub_param = struct.unpack_from(">I", self._data, 0x0C)[0]

        # Parse payload based on type
        self._float_value = None
        self._uint_value = None
        self._uint_extra = None
        self._string_value = None

        if self._payload_type_raw == PayloadType.FLOAT:
            if len(self._data) >= 0x18:
                self._float_value = struct.unpack_from(">f", self._data, 0x14)[0]

        elif self._payload_type_raw == PayloadType.UINT_PAIR:
            if len(self._data) >= 0x1C:
                self._uint_value = struct.unpack_from(">I", self._data, 0x14)[0]
                self._uint_extra = struct.unpack_from(">I", self._data, 0x18)[0]

        elif self._payload_type_raw == PayloadType.STRING:
            raw = self._data[0x14:SIGMA_MAX_PACKET_SIZE]  # cap at protocol max
            self._string_value = "".join(chr(b & 0x7F) for b in raw if b & 0x7F)

        elif self._payload_type_raw == PayloadType.NONE:
            pass  # no payload

        elif self._payload_type_raw == PayloadType.UINT_AS_FLOAT and len(self._data) >= 0x18:
            # Read as float, reinterpret as uint
            raw_float = struct.unpack_from(">f", self._data, 0x14)[0]
            self._float_value = raw_float
            self._uint_value = sigma_float_to_uint(raw_float)

    @property
    def magic(self) -> int:
        """Magic byte (always 0x53 for valid packets)."""
        return self._data[0]

    @property
    def product_type(self) -> int:
        """Product type (always 4 for Sigma)."""
        return struct.unpack_from(">I", self._data, 0x04)[0]

    @property
    def payload_type(self) -> int:
        """Payload type (1-5), from top byte of offset 0x08."""
        return self._payload_type_raw

    @property
    def msg_id(self) -> int:
        """Message ID, from lower bytes of offset 0x08."""
        return self._msg_id

    @property
    def sub_param(self) -> int:
        """Sub-parameter (channel/slot number), from offset 0x0C."""
        return self._sub_param

    @property
    def float_value(self):
        """Float payload (PayloadType.FLOAT or UINT_AS_FLOAT), or None."""
        return self._float_value

    @property
    def uint_value(self):
        """Uint payload (PayloadType.UINT_PAIR or UINT_AS_FLOAT), or None."""
        return self._uint_value

    @property
    def uint_extra(self):
        """Second uint in a UINT_PAIR payload, or None."""
        return self._uint_extra

    @property
    def string_value(self):
        """String payload (PayloadType.STRING), or None."""
        return self._string_value
