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
        self.struct = []
        if filename is not None:
            self.load()

    def load(self):
        if self.filename is None:
            return False
        with open(self.filename, "rb") as f:
            rawdata = f.read()
            f.close()
        self.load_from_bytes(rawdata)

    def load_from_bytes(self, payload: bytes):
        self.payload = payload
        print(repr(payload[0:10]))
        jmp = unpack("<L", payload[0:4])[0]
        print("{:08x}".format(jmp))

    def __str__(self):
        txt = "Binary payload, {} Bytes".format(len(self.payload))
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
