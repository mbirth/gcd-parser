# -*- coding: utf-8 -*-
# Thanks to Herbert Oppmann (herby) for all your work!

from .ansi import RESET, RED, YELLOW
from .chksum import ChkSum
from .rgnbin import RgnBin
from struct import unpack
import configparser

RGN_SIG = b"KpGr"
DEFAULT_BUILDER = "SQA"

# RGN structure might be: RGN > BIN or RGN > RGN > BIN
# RGN = outside hull
# BIN = firmware + hwid + checksum

REGION_TYPES = {
    0x000a: "dskimg.bin",
    0x000c: "boot.bin",
    0x000e: "fw_all.bin",
    0x0010: "logo.bin",
    0x0029: "NonVol (old)",
    0x004e: "ZIP file",
    0x0055: "fw_all2.bin",
    0x009a: "NonVol (new)",
    0x00f5: "GCD firmware update file",
    0x00f9: "Display firmware",
    0x00fa: "ANT firmware",
    0x00fb: "WiFi firmware",
    0x00ff: "pk_text.zip",
}

class ParseException(Exception):
    pass

class Rgn:
    def __init__(self, filename: str=None):
        self.filename = filename
        self.struct = []
        if filename is not None:
            self.load()

    def load(self):
        if self.filename is None:
            return False
        with open(self.filename, "rb") as f:
            sig = f.read(4)
            if sig != RGN_SIG:
                raise ParseException("Signature mismatch ({}, should be {})!".format(repr(sig), repr(RGN_SIG)))
            self.version = unpack("<H", f.read(2))[0]
            while True:
                cur_offset = f.tell()
                header = f.read(5)
                if len(header) == 0:
                    #print("End of file reached.")
                    break
                (length, type_id) = unpack("<Lc", header)
                #print("Found record type: {} with {} Bytes length.".format(type_id, length))
                rec = RgnRecord.factory(type_id, length, offset=cur_offset)
                rec.parent = self
                payload = f.read(length)
                rec.set_payload(payload)
                self.add_rec(rec)
            f.close()

    def load_from_bytes(self, payload: bytes):
        pos = 0
        sig = payload[pos:pos+4]
        if sig != RGN_SIG:
            raise ParseException("Signature mismatch ({}, should be {})!".format(repr(sig), repr(RGN_SIG)))
        pos += 4
        self.version = unpack("<H", payload[pos:pos+2])[0]
        pos += 2
        while True:
            cur_offset = pos
            if pos >= len(payload):
                #print("End of file reached.")
                break
            header = payload[pos:pos+5]
            pos += 5
            (length, type_id) = unpack("<Lc", header)
            #print("Found record type: {} with {} Bytes length.".format(type_id, length))
            rec = RgnRecord.factory(type_id, length, offset=cur_offset)
            rec.parent = self
            inner_payload = payload[pos:pos+length]
            pos += length
            rec.set_payload(inner_payload)
            self.add_rec(rec)

    def add_rec(self, new_rec):
        self.struct.append(new_rec)

    def print_struct(self):
        """
        Prints the structure of the parsed RGN file
        """
        print(str(self))

    def print_struct_full(self):
        """
        Prints the structure of the parsed RGN file
        """
        self.print_struct()

    def validate(self, print_stats: bool=False):
        """
        Checks and verifies all checksums in the RGN.
        """
        return True
        # RGN has no checksum, but embedded BIN has

    def dump_to_files(self, output_basename: str):
        pass

    @staticmethod
    def from_recipe(recipe_file: str):
        pass

    def save(self, filename):
        pass

    def __str__(self):
        txt = "RGN File Version: {}".format(self.version)
        txt += "\n{} records.".format(len(self.struct))
        for i, rec in enumerate(self.struct):
            txt += "\n#{:03d}: {}".format(i, rec)
        return txt

class RgnRecord():
    def __init__(self, type_id, expected_length, payload=None, offset=None):
        self.parent = None
        self.type_id = type_id
        self.length = expected_length
        self.is_binary = False
        self.payload = payload
        self.offset = offset
        self.is_parsed = False

    def set_payload(self, new_payload):
        self.payload = new_payload

    @staticmethod
    def factory(type_id, length: int = None, offset: int = None):
        if type_id == b"D":
            new_rec = RgnRecordD(type_id, length)
        elif type_id == b"A":
            new_rec = RgnRecordA(type_id, length)
        elif type_id == b"R":
            new_rec = RgnRecordR(type_id, length)
            new_rec.is_binary = True
        else:
            raise ParseException("Unknown record type: {} at offset 0x{:0x}".format(type_id, offset))
        new_rec.offset = offset
        return new_rec

    def __str__(self):
        rec_type = "Unknown"
        if self.type_id == b"D":
            rec_type = "Data Version"
        elif self.type_id == b"A":
            rec_type = "Application Version"
        elif self.type_id == b"R":
            rec_type = "Region"

        if self.length != 1:
            plural = "s"
        offset = ""
        if self.offset:
            offset = " at 0x{:x}".format(self.offset)
        lenstr = ""
        if self.length:
            lenstr = ", {:d} Byte{}".format(self.length, plural)
        return "RGN {} Record{}{}".format(rec_type, offset, lenstr)

class RgnRecordD(RgnRecord):
    """
    Data record (2 Bytes)
    - ushort - Version
    """

    def __init__(self, type_id, expected_length, payload=None, offset=None):
        super().__init__(type_id, expected_length, payload, offset)
        self.version = None

    def parse(self):
        if self.is_parsed:
            # already parsed
            return
        self.version = unpack("<H", self.payload)[0]
        self.is_parsed = True

    def __str__(self):
        txt = super().__str__()
        if not self.is_parsed:
            self.parse()
        txt += "\n  - Data Version: {}".format(self.version)
        return txt


class RgnRecordA(RgnRecord):
    """
    Application record
    - ushort - Application version
    - string - Builder
    - string - BuildDate
    - string - BuildTime
    """

    def __init__(self, type_id, expected_length, payload=None, offset=None):
        super().__init__(type_id, expected_length, payload, offset)
        self.version = None
        self.builder = None
        self.build_date = None
        self.build_time = None

    def parse(self):
        if self.is_parsed:
            # already parsed
            return
        self.version = unpack("<H", self.payload[0:2])[0]
        splits = self.payload[2:].split(b"\0", 2)
        self.builder = splits[0].decode("utf-8")
        self.build_date = splits[1].decode("utf-8")
        self.build_time = splits[2].decode("utf-8")
        self.is_parsed = True

    def __str__(self):
        txt = super().__str__()
        if not self.is_parsed:
            self.parse()
        txt += "\n  - Application Version: {}".format(self.version)
        txt += "\n  - Builder: {}".format(self.builder)
        txt += "\n  - Build time: {} {}".format(self.build_date, self.build_time)
        return txt

class RgnRecordR(RgnRecord):
    """
    Region record
    - ushort - Region ID
    - uint   - Delay in ms
    - uint   - Region size (is record length - 10)
    - byte[Region size] - Contents
    """

    def __init__(self, type_id, expected_length, payload=None, offset=None):
        super().__init__(type_id, expected_length, payload, offset)
        self.region_id = None
        self.delay_ms = None
        self.size = None

    def id_payload(self):
        if self.payload[10:10+len(RGN_SIG)] == RGN_SIG:
            return "RGN"
        return "BIN"

    def parse(self):
        if self.is_parsed:
            # already parsed
            return
        (self.region_id, self.delay_ms, self.size) = unpack("<HLL", self.payload[0:10])
        self.is_parsed = True

    def __str__(self):
        txt = super().__str__()
        if not self.is_parsed:
            self.parse()
        rgn_type = REGION_TYPES.get(self.region_id, RED + "Unknown" + RESET)
        txt += "\n  - Region ID: {:04x} ({})".format(self.region_id, rgn_type)
        txt += "\n  - Flash delay: {} ms".format(self.delay_ms)
        txt += "\n  - Binary size: {} Bytes".format(self.size)
        if len(self.payload) - 10 == self.size:
            txt += " (OK)"
        else:
            txt += " (" + RED + "MISMATCH!" + RESET + ")"
        payload_type = self.id_payload()
        if payload_type == "RGN":
            txt += "\n  " + YELLOW + "PAYLOAD IS ANOTHER RGN STRUCTURE:" + RESET
            #with open("innerrgn.rgn", "wb") as f:
            #    f.write(self.payload[10:])
            #    f.close()
            rgn = Rgn()
            rgn.load_from_bytes(self.payload[10:])
            txt += "\n      " + "\n      ".join(str(rgn).split("\n"))
        elif payload_type == "BIN":
            #with open("{}_{}.bin".format(self.parent.filename, self.offset), "wb") as f:
            #    f.write(self.payload[10:])
            binfw = RgnBin()
            binfw.load_from_bytes(self.payload[10:])
            txt += "\n      " + "\n      ".join(str(binfw).split("\n"))
        return txt
