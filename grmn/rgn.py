# -*- coding: utf-8 -*-
# Thanks to Herbert Oppmann (herby) for all your work!

from .chksum import ChkSum
from .rgnbin import RgnBin
from struct import unpack
import configparser

RGN_SIG = b"KpGr"

# RGN structure might be: RGN > BIN or RGN > RGN > BIN
# RGN = outside hull
# BIN = firmware + hwid + checksum

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
        last_tlv6 = None
        last_tlv7 = None
        with open(self.filename, "rb") as f:
            sig = f.read(4)
            if sig != RGN_SIG:
                raise ParseException("Signature mismatch ({}, should be {})!".format(repr(sig), repr(RGN_SIG)))
            self.version = unpack("<H", f.read(2))[0]
            print("Version: {}".format(self.version))
            while True:
                cur_offset = f.tell()
                header = f.read(5)
                if len(header) == 0:
                    print("End of file reached.")
                    break
                (length, type_id) = unpack("<Lc", header)
                print("Found record type: {} with {} Bytes length.".format(type_id, length))
                rec = RgnRecord.factory(type_id, length, offset=cur_offset)
                payload = f.read(length)
                rec.set_payload(payload)
                self.add_rec(rec)
            f.close()

    def add_rec(self, new_rec):
        self.struct.append(new_rec)

    def print_struct(self):
        """
        Prints the structure of the parsed GCD file
        """
        pass

    def print_struct_full(self):
        """
        Prints the structure of the parsed GCD file
        """
        pass

    def validate(self, print_stats: bool=False):
        """
        Checks and verifies all checksums in the GCD.
        """
        # RGN has no checksum, but embedded BIN has

    def dump_to_files(self, output_basename: str):
        pass

    @staticmethod
    def from_recipe(recipe_file: str):
        pass

    def save(self, filename):
        pass

class RgnRecord():
    def __init__(self, type_id, expected_length, payload=None, offset=None):
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

class RgnRecordD(RgnRecord):
    """
    Data record (2 Bytes)
    - ushort - Version
    """

    def parse(self):
        self.is_parsed = True

class RgnRecordA(RgnRecord):
    """
    Application record
    - ushort - Application version
    - string - Builder
    - string - BuildDate
    - string - BuildTime
    """

    def parse(self):
        self.is_parsed = True

class RgnRecordR(RgnRecord):
    """
    Region record
    - ushort - Region ID
    - uint   - Delay in ms
    - uint   - Region size (is record length - 10)
    - byte[Region size] - Contents
    """

    def parse(self):
        self.is_parsed = True
