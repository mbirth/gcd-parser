#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Adds up all bytes from the beginning of a file and shows where
a byte in the file matches the expected checksum at that location.
"""

from grmn import ChkSum
import sys

FILE = sys.argv[1]
BLOCKSIZE = 4096
OFFSET = 0x0

csum = ChkSum()
prev_remainder = b"\x00"
print("Reading {} ...".format(FILE))
with open(FILE, "rb") as f:
    while True:
        start_pos = f.tell()
        block = f.read(BLOCKSIZE)
        block = block[OFFSET:]
        for i in range(0, len(block)):
            c = block[i:i+1]
            exp = bytes([csum.get_expected()])
            if c == exp:
                print("Found matching 0x{:02x} at 0x{:x} ({:x} + {:d}).".format(c[0], OFFSET + start_pos + i, OFFSET, start_pos + i))
            csum.add(bytes(c))
        if len(block) < BLOCKSIZE:
            break
        #break
    f.close()
