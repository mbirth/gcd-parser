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
OFFSET = 0
if len(sys.argv) > 2:
  OFFSET = int(sys.argv[2])
BLOCKSIZE = 4096

END_MARKER = b"\xff\xff\x5a\xa5"

first_block = True
end_marker_pos = 0xffffffff
print("Reading {} ...".format(FILE))
with open(FILE, "rb") as f:
    f.read(OFFSET)
    while True:
        block = f.read(BLOCKSIZE)
        if first_block:
            dw = unpack("<LLLLL", block[0:20])
            first_block = False
        if END_MARKER in block:
            end_pos = block.find(END_MARKER)
            found_pos = f.tell() - len(block) + end_pos + 2
            if found_pos > end_marker_pos:
                print("Found a second endmarker! Using that one.")
            end_marker_pos = found_pos
            #break
        if len(block) < BLOCKSIZE:
            break
    f.close()

size = os.path.getsize(FILE)

print("File is {} (0x{:x}) Bytes.".format(size, size))
print("First double-words: 0x{:x} / 0x{:x} / 0x{:x} / 0x{:x} / 0x{:x}".format(dw[0], dw[1], dw[2], dw[3], dw[4]))
print("Assuming this is end marker location in memory: 0x{:x}".format(dw[1]))
print("Found end marker in file at: 0x{:x}".format(end_marker_pos))

base_addr = dw[1] - (end_marker_pos - OFFSET)
if base_addr < 0:
    base_addr += 0xffffffff

print("This would make Base address probably 0x{:x}".format(base_addr))

if base_addr % 4 != 0:
    print("However, bad alignment. Calculated base address not aligned to doublewords.")

if base_addr + size > 0xffffffff:
    print("However, base address can't fit whole file.")

# Assumes second dword points to hwid
#if dw[2] % 2 != 0 or dw[2] - base_addr >= end_marker_pos - 3:
#    print("Align & Bounds dw2 wrong.")
#    sys.exit(1)

# Assumes third dword points to fwid
#if dw[3] % 2 != 0 or dw[3] - base_addr >= end_marker_pos - 3:
#    print("Align & Bounds dw3 wrong.")
#    sys.exit(1)

# hwid = dw[2] - base_addr
# fwid = dw[3] - base_addr
