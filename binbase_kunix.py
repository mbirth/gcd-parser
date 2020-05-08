#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Many thanks to kunix!

"""
Calculates possible base address.
"""

from struct import unpack
import os.path
import sys

FILE = sys.argv[1]
BLOCKSIZE = 4096

END_MARKER = b"\xff\xff\x5a\xa5"

first_block = True
past_end = False
trailer = bytes()
trailer_pos = -1

print("Reading {} ...".format(FILE))
with open(FILE, "rb") as f:
    while True:
        block = f.read(BLOCKSIZE)
        if first_block:
            dw = unpack("<LLLLL", block[0:20])
            first_block = False
        if END_MARKER in block:
            end_pos = block.find(END_MARKER)
            marker_end = f.tell() - len(block) + end_pos + 2
            break
        if len(block) < BLOCKSIZE:
            break
    f.close()

size = os.path.getsize(FILE)

print("File is {} Bytes.".format(size))
print("First double-words: 0x{:x} / 0x{:x} / 0x{:x} / 0x{:x} / 0x{:x}".format(dw[0], dw[1], dw[2], dw[3], dw[4]))
print("Found end marker at: 0x{:x}".format(marker_end))

base_addr = dw[1] - marker_end

if base_addr % 4 != 0:
    print("Bad alignment. Calculated base address not aligned to doublewords.")
    #sys.exit(1)

if base_addr + size > 0xffffffff:
    print("Overflow")
    sys.exit(1)

if dw[2] % 2 != 0 or dw[2] - base_addr >= marker_end - 3:
    print("Align & Bounds dw2 wrong.")
    #sys.exit(1)

if dw[3] % 2 != 0 or dw[3] - base_addr >= marker_end - 3:
    print("Align & Bounds dw3 wrong.")
    #sys.exit(1)

print("Base address is probably 0x{:x}".format(base_addr))

# hwid = dw[2] - base_addr
# fwid = dw[3] - base_addr
