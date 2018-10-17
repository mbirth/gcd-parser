# -*- coding: utf-8 -*-
# Thanks to TurboCCC and kunix for all your work!

from . import chksum
from . import devices
from binascii import hexlify
from struct import pack, unpack
import sys

GCD_SIG = b"G\x41RM\x49Nd\00"
DEFAULT_COPYRIGHT = b"Copyright 1996-2017 by G\x61rm\x69n Ltd. or its subsidiaries."
DEFAULT_FIRST_PADDING = 21
DEFAULT_ALIGN = 0x1000    # second padding block pads until 0x1000

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

# Typical structure:
# first 0x1000 Bytes: GCD_SIG > 0x0001 > 0x0002 > 0x0003 > 0x0005 > 0x0001 > 0x0002
# then: 0x0001 > ( 0x0006 > 0x0007 > 0x???? > 0x0001 ... ) > 0xffff

class TLV:
    def __init__(self, type_id: int, expected_length: int, value=None, offset: int=None):
        self.type_id = type_id
        self.offset = offset
        self.comment = TLV_TYPES.get(type_id, "Type {:04x} / {:d}".format(type_id, type_id))
        self.length = expected_length
        self.value = None
        self.is_parsed = False
        if value is not None:
            self.value = bytes(value)

    @staticmethod
    def factory(header: bytes, offset: int = None):
        (type_id, length) = unpack("<HH", header)
        if type_id == 0x0006:
            new_tlv = TLV6(type_id, length)
        elif type_id == 0x0007:
            new_tlv = TLV7(type_id, length)
        else:
            new_tlv = TLV(type_id, length)
        new_tlv.offset = offset
        return new_tlv

    def __str__(self):
        plural = ""
        if self.length != 1:
            plural = "s"
        return "TLV Type {:04x} at 0x{:x}, {:d} Byte{} - {}".format(self.type_id, self.offset, self.length, plural, self.comment)

    def set_value(self, new_value: bytes):
        self.value = new_value

    def get_length(self):
        return self.length

    def get_actual_length(self):
        if self.value is None:
            return 0
        return len(self.value)

    def get_record_length(self):
        # Length including record definition
        return self.get_actual_length() + 4

    def get_value(self):
        return self.value

    def get(self):
        header = pack("HH", self.type_id, self.get_actual_length())
        if self.value is None:
            return header
        return header + self.value

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
        0x2015: ["L", "Block size"],
        0x5003: ["", "End of definition marker"],
    }

    def parse(self):
        if len(self.value) % 2 != 0:
            raise Exception("Invalid TLV6 payload length!")

        self.fids = []
        self.format = ""
        self.fields = []

        for i in range(0, len(self.value), 2):
            fid = unpack("H", self.value[i:i+2])[0]
            fdef = self.FIELD_TYPES[fid]
            self.fids.append(fid)
            self.format += fdef[0]
            self.fields.append(fdef[1])

        self.is_parsed = True

class TLV7(TLV):
    def set_tlv6(self, tlv6: TLV6):
        self.tlv6 = tlv6

    def parse(self):
        if not self.tlv6.is_parsed:
            # Make sure we have the structure analysed
            self.tlv6.parse()
        values = unpack("<" + self.tlv6.format, self.value)
        for i, v in enumerate(values):
            fid = self.tlv6.fids[i]
            fdesc = self.tlv6.fields[i]
            if fid == 0x1009:
                print("  - {:>20}: 0x{:04x} / {:d} ({})".format(fdesc, v, v, devices.DEVICES.get(v, "Unknown device")))
            elif fid == 0x2015:
                print("  - {:>20}: {} Bytes".format(fdesc, v))
            else:
                print("  - {:>20}: 0x{:04x} / {:d}".format(fdesc, v, v))

class Gcd:
    def __init__(self, filename: str=None):
        self.filename = filename
        self.struct = []
        if filename is not None:
            self.load()

    def load(self):
        if self.filename is None:
            return False
        last_tlv6 = None
        with open(self.filename, "rb") as f:
            sig = f.read(8)
            if sig != GCD_SIG:
                raise Exception("Signature mismatch ({}, should be {})!".format(repr(sig), repr(GCD_SIG)))
            while True:
                cur_offset = f.tell()
                header = f.read(4)
                tlv = TLV.factory(header, offset=cur_offset)
                self.struct.append(tlv)
                if tlv.type_id == 0xFFFF:
                    # End of file reached
                    break
                tlength = tlv.get_length()
                payload = f.read(tlength)
                tlv.set_value(payload)
                if tlv.type_id == 0x0006:
                    last_tlv6 = tlv
                elif tlv.type_id == 0x0007:
                    tlv.set_tlv6(last_tlv6)
            f.close()
