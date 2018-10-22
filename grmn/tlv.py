# -*- coding: utf-8 -*-

from . import devices
from binascii import hexlify, unhexlify
from struct import pack, unpack

TLV_TYPES = {
    0x0001: "Checksum rectifier",
    0x0002: "Padding",
    0x0003: "Part number?",
    0x0005: "Copyright notice",
    0x0006: "Block Type 7 format definition",
    0x0007: "Binary descriptor",
    0x0008: "Binary Region 0C (boot.bin)",
    0x0401: "Binary Component Firmware (SensorHub, ANT_BLE_BT, GPS, WiFi)",
    0x0505: "Binary Region 05",
    0x0555: "Binary Region 55",
    0x0557: "Binary Region 57",
    0x02bd: "Binary Region 0E (fw_all.bin)",
    0xffff: "EOF marker",
}

class TLV:
    def __init__(self, type_id: int, expected_length: int, value=None, offset: int=None):
        self.type_id = type_id
        self.is_binary = False
        self.offset = offset
        self.comment = TLV_TYPES.get(type_id, "Type {:04x} / {:d}".format(type_id, type_id))
        self.length = expected_length
        self.value = None
        self.is_parsed = False
        if value is not None:
            self.value = bytes(value)

    @staticmethod
    def factory(type_id: int, length: int = None, offset: int = None):
        if type_id == 0x0001:
            new_tlv = TLV1(type_id, length)
        elif type_id == 0x0002:
            new_tlv = TLV2(type_id, length)
        elif type_id == 0x0005:
            new_tlv = TLV5(type_id, length)
        elif type_id == 0x0006:
            new_tlv = TLV6(type_id, length)
        elif type_id == 0x0007:
            new_tlv = TLV7(type_id, length)
        elif type_id in [0x0008, 0x0401, 0x0505, 0x0555, 0x0557, 0x02bd]:
            new_tlv = TLVbinary(type_id, length)
            new_tlv.is_binary = True
        else:
            new_tlv = TLV(type_id, length)
        new_tlv.offset = offset
        return new_tlv

    def __str__(self):
        plural = ""
        if self.length != 1:
            plural = "s"
        offset = ""
        if self.offset:
            offset = " at 0x{:x}".format(self.offset)
        lenstr = ""
        if self.length:
            lenstr = ", {:d} Byte{}".format(self.length, plural)
        return "TLV Type {:04x}{}{} - {}".format(self.type_id, offset, lenstr, self.comment)

    def set_value(self, new_value: bytes):
        self.value = new_value

    def get_actual_length(self):
        if self.value is None:
            return 0
        return len(self.value)

    def get_record_length(self):
        # Length including record definition
        return self.get_actual_length() + 4

    def get_value(self):
        return self.value

    def get_header(self):
        header = pack("HH", self.type_id, self.get_actual_length())
        return header

    def get(self):
        header = self.get_header()
        if self.value is None:
            return header
        return header + self.value

    def dump(self):
        """Should return a list of key-value-comment tuples so the object can be recreated using create_from_dump() later."""
        data = []
        data.append(("type", "0x{:04x}".format(self.type_id), self.comment))
        data.append(("length", self.get_actual_length(), None))
        if self.value is not None:
            hexstr = hexlify(self.value).decode("utf-8")
            hexstr = " ".join(hexstr[i:i+2] for i in range(0, len(hexstr), 2))
            data.append(("value", hexstr, None))
        return data

    def load_dump(self, values):
        for (k, v) in values:
            if k == "value":
                self.value = unhexlify("".join(v.split(" ")))
                self.length = len(self.value)

    @staticmethod
    def create_from_dump(values):
        """Use data exported with dump() to recreate object."""
        tlv = None
        for (k, v) in values:
            if k == "type":
                type_id = int(v, 0)
        tlv = TLV.factory(type_id)
        tlv.load_dump(values)
        return tlv

class TLV1(TLV):
    def dump(self):
        data = []
        data.append(("type", "0x{:04x}".format(self.type_id), self.comment))
        return data

    def load_dump(self, values):
        # Will be calculated in a final pass
        self.value = 0x00
        self.length = 1

class TLV2(TLV):
    def dump(self):
        data = []
        data.append(("type", "0x{:04x}".format(self.type_id), self.comment))
        data.append(("length", self.get_actual_length(), "Length of padding block"))
        return data

    def load_dump(self, values):
        for (k, v) in values:
            if k == "length":
                self.value = b"\x00" * int(v)
                self.length = len(self.value)

class TLV5(TLV):
    def dump(self):
        data = []
        data.append(("type", "0x{:04x}".format(self.type_id), self.comment))
        data.append(("length", self.get_actual_length(), None))
        data.append(("text", self.value.decode("utf-8"), None))
        return data

    def load_dump(self, values):
        for (k, v) in values:
            if k == "text":
                self.value = v.encode("utf-8")
            elif k == "length":
                self.length = int(v)
        if len(self.value) != self.length:
            print("WARNING: Imported copyright text doesn't match supposed length.")
            self.length = len(self.value)

class TLV6(TLV):
    """
    Describes following TLV7:
    http://www.gpspassion.com/forumsen/topic.asp?TOPIC_ID=137838&whichpage=12
    """

    # Field ids in Type 6 payloads (describe Type 7 data format)
    # First nibble might be data type: 0 = B, 1 = H, 2 = L
    FIELD_TYPES = {
        0x000a: ["B", "XOR flag/value"],
        0x000b: ["B", "Reset/Downgrade flag"],
        0x1009: ["H", "Device hw_id"],
        0x100a: ["H", "Block type"],
        0x100d: ["H", "Firmware version"],
        0x1014: ["H", "Field 1014"],
        0x1015: ["H", "Field 1015"],
        0x1016: ["H", "Field 1016 (WiFi fw)"],
        0x2015: ["L", "Binary length"],
        0x5003: ["", "End of definition marker"],
    }

    def __init__(self, type_id: int, expected_length: int, value=None, offset: int=None):
        super().__init__(type_id, expected_length, value, offset)
        self.fids = []
        self.format = ""
        self.fields = []

    def add_fid(self, fid: int):
        fdef = self.FIELD_TYPES[fid]
        self.fids.append(fid)
        self.format += fdef[0]
        self.fields.append(fdef[1])

    def parse(self):
        if self.is_parsed:
            # already parsed
            return
        if len(self.value) % 2 != 0:
            raise Exception("Invalid TLV6 payload length!")

        for i in range(0, len(self.value), 2):
            fid = unpack("<H", self.value[i:i+2])[0]
            self.add_fid(fid)

        self.is_parsed = True

    def __str__(self):
        txt = super().__str__()
        if not self.is_parsed:
            self.parse()
        for i, fid in enumerate(self.fids):
            txt += "\n  - Field {:d}: {:04x} - {}".format(i+1, fid, self.fields[i])
        return txt

    def dump(self):
        # Dump nothing as important info will be chained in binary dump
        return []

    def load_dump(self, values):
        self.value = b""
        for (k, v) in values:
            if k == "from_file":
                continue
            elif k[0:2] != "0x":
                continue
            fid = int(k, 0)
            self.value += pack("<H", fid)
        self.value += pack("<H", 0x5003)
        self.length = len(self.value)

class TLV7(TLV):
    def __init__(self, type_id: int, expected_length: int, value=None, offset: int=None):
        super().__init__(type_id, expected_length, value, offset)
        self.tlv6 = None
        self.binary_type_id = None
        self.attr = []

    def set_tlv6(self, tlv6: TLV6):
        self.tlv6 = tlv6

    def parse(self):
        if self.is_parsed:
            # already parsed
            return
        if not self.tlv6.is_parsed:
            # Make sure we have the structure analysed
            self.tlv6.parse()
        values = unpack("<" + self.tlv6.format, self.value)
        for i, v in enumerate(values):
            fid = self.tlv6.fids[i]
            self.attr.append((fid, v))
            if fid == 0x100a:
                self.binary_type_id = v
        self.is_parsed = True

    def __str__(self):
        txt = super().__str__()
        if not self.is_parsed:
            self.parse()
        for i, pair in enumerate(self.attr):
            fdesc = self.tlv6.fields[i]
            (fid, v) = pair
            if fid == 0x1009:
                txt += "\n  - Field {:d}: {:>20}: 0x{:04x} / {:d} ({})".format(i+1, fdesc, v, v, devices.DEVICES.get(v, "Unknown device"))
            elif fid == 0x2015:
                txt += "\n  - Field {:d}: {:>20}: {} Bytes".format(i+1, fdesc, v)
            else:
                txt += "\n  - Field {:d}: {:>20}: 0x{:04x} / {:d}".format(i+1, fdesc, v, v)
        return txt

    def dump(self):
        # Dump nothing as important info will be chained in binary dump
        return []

    def load_dump(self, values):
        self.value = b""
        new_values = []
        for (k, v) in values:
            if k == "from_file":
                continue
            elif k[0:2] != "0x":
                continue
            numval = int(v, 0)
            new_values.append(numval)
        if not self.tlv6.is_parsed:
            # Make sure we have the structure analysed (need format attr)
            self.tlv6.parse()
        self.value = pack("<" + self.tlv6.format, *new_values)
        self.length = len(self.value)

class TLVbinary(TLV):
    def __init__(self, type_id: int, expected_length: int, value=None, offset: int=None):
        super().__init__(type_id, expected_length, value, offset)
        self.tlv7 = None

    def set_tlv7(self, tlv7: TLV7):
        self.tlv7 = tlv7

    def dump(self):
        data = []
        # type is given in fields list from TLV7 already
        if not self.tlv7.is_parsed:
            self.tlv7.parse()
        for i, pair in enumerate(self.tlv7.attr):
            fdesc = self.tlv7.tlv6.fields[i]
            valtype = self.tlv7.tlv6.format[i]
            (fid, v) = pair
            if valtype == "B":
                valstr = "0x{:02x}".format(v)
            elif valtype == "H":
                valstr = "0x{:04x}".format(v)
            else:
                valstr = "0x{:08x}".format(v)
            data.append(("0x{:04x}".format(fid), valstr, fdesc))
        return data
