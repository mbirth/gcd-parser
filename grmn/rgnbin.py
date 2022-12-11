# -*- coding: utf-8 -*-
# Thanks to Herbert Oppmann (herby) for all your work!

from . import devices
from .ansi import RESET, RED, GREEN
from .chksum import ChkSum
from struct import unpack

# RGN structure might be: RGN > BIN or RGN > RGN > BIN
# RGN = outside hull
# BIN = firmware + hwid + checksum

END_PATTERN = b"\xff\xff\x5a\xa5\xff\xff\xff\xff"

class ParseException(Exception):
    pass

class RgnBin:
    def __init__(self, filename: str=None):
        self.filename = filename
        self.hwid = None
        self.version = None
        self.payload = None
        if filename is not None:
            self.load()

    def load(self):
        if self.filename is None:
            return False
        with open(self.filename, "rb") as f:
            rawdata = f.read()
            f.close()
        self.load_from_bytes(rawdata)

    def find_metadata(self):
        try:
            end_loc = self.payload.rindex(END_PATTERN)
            #print("end_loc: {}".format(end_loc))
        except ValueError:
            # No END_PATTERN found
            end_loc = None
        jmp = unpack("<L", self.payload[0:4])[0]
        print("JMP: 0x{:08x}".format(jmp))
        hwid_addr = None
        swver_addr = None
        if jmp == 0xe59ff008:
            # Variant 1a or 1b (end > hwid > swver > entry OR hwid > swver > end > entry)
            (x1, x2, x3, entry_addr) = unpack("<LLLL", self.payload[4:20])
            #print("{:04x} / {:04x} / {:04x} / {:04x}".format(x1, x2, x3, entry_addr))
            # HWID and SWVER are near each other
            if abs(x2 - x1) == 2:
                # Assume 1b: x1 = hw_id, x2 = swver
                delta = 20 - entry_addr
                hwid_addr = x1 + delta
                swver_addr = x2 + delta
            else:
                # Assume 1a: x2 = hw_id, x3 = swver
                delta = 20 - entry_addr
                hwid_addr = x2 + delta
                swver_addr = x3 + delta
        if jmp == 0xe59ff00c:
            # Variant 2 (end > hwid > swver > lend > entry)
            # NOTE: This method doesn't seem to work with eTrex H firmware!
            (end_addr, hwid_addr, swver_addr, lend_addr, entry_addr) = unpack("<LLLlL", self.payload[4:24])
            #print("hwid_addr: {} / swver_addr: {}".format(hwid_addr, swver_addr))
            #print("end_addr: {} / lend_addr: {} / entry_addr: {}".format(end_addr, lend_addr, entry_addr))
            if lend_addr < 0:
                load_addr = -lend_addr
                print("load_addr: {}".format(load_addr))
                delta = 24 - load_addr
            else:
                delta = 24 - entry_addr
            #print("delta: {}".format(delta))
            hwid_addr += delta
            swver_addr += delta
            #print("hwaddr: {} / swveraddr: {}".format(hwid_addr, swver_addr))
        if end_loc and jmp == 0xea000002:
            # Variant 3 (end > hwid > swver)
            (end_addr, hwid_addr, swver_addr) = unpack("<LLL", self.payload[4:16])
            delta = end_loc + 2 - end_addr
            hwid_addr += delta
            swver_addr += delta
        if jmp == 0xea000003:
            print(RED + "Checking for 4" + RESET)
            # Variant 4 (end > hwid > swver > ???)
            (end_addr, hwid_addr, swver_addr) = unpack("<LLL", self.payload[4:16])
            delta = end_loc + 2 - end_addr
            hwid_addr += delta
            swver_addr += delta
        if jmp == 0xea000004:
            print(RED + "Checking for 5" + RESET)
            # Variant 5 - not mentioned in pdf doc
            print(repr(self.payload[4:20]))
        if self.payload[252:256] == b"\xff\xff\xff\xff":
            print("HWID at 256 possible")
            hwid_addr = 256
            swver_addr = 258
        if self.payload[508:512] == b"\xff\xff\xff\xff":
            print("HWID at 512 possible")
            hwid_addr = 512
            swver_addr = 514

        if hwid_addr:
            if hwid_addr < 0 or hwid_addr > len(self.payload)-2:
                print(RED + "HWID OFFSET {:04x} OUT OF BOUNDS {:04x}".format(hwid_addr, len(self.payload)) + RESET)
            else:
                self.hwid = unpack("<H", self.payload[hwid_addr:hwid_addr+2])[0]
        if swver_addr:
            if swver_addr < 0 or swver_addr > len(self.payload)-2:
                print(RED + "SWVER OFFSET {:04x} OUT OF BOUNDS {:04x}".format(swver_addr, len(self.payload)) + RESET)
            else:
                self.version = unpack("<H", self.payload[swver_addr:swver_addr+2])[0]

        # Try EOF-4
        if not self.hwid and not self.version:
            print("Checking for EOF-4")
            (hwid, version) = unpack("<HH", self.payload[-6:-2])
            if hwid < 0xffff and version < 0xffff:
                print("EOF-4 matches")
                self.hwid = hwid
                self.version = version

        return None

    def load_from_bytes(self, payload: bytes):
        self.payload = payload
        self.find_metadata()

    def __str__(self):
        txt = "Binary payload, {} Bytes".format(len(self.payload))
        if self.hwid:
            txt += "\n  -    hw_id: 0x{:04x} / {:d} ({})".format(self.hwid, self.hwid, devices.get_name(self.hwid, 0, RED + "Unknown device" + RESET))
        if self.version:
            txt += "\n  -  Version: 0x{:04x} / {:d}".format(self.version, self.version)
        cksum = ChkSum()
        cksum.add(self.payload)
        exp_byte = cksum.get_expected()
        last_byte = cksum.get_last_byte()
        txt += "\n  - Checksum: {:02x} (expected: {:02x}) = ".format(last_byte, exp_byte)
        if cksum.is_valid():
            txt += GREEN + "OK" + RESET
        else:
            txt += RED + "INVALID" + RESET
        return txt
