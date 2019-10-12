# -*- coding: utf-8 -*-
# Thanks to Herbert Oppmann (herby) for all your work!

from . import devices
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
            f.close()
