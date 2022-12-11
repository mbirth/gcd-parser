#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Many thanks to Alex W. who figured this out!

"""
Calculates the SHA1 of a fw_all.bin until the ending marker.
"""

from hashlib import sha1
from struct import unpack
from grmn import devices
import sys

FILE = sys.argv[1]
BLOCKSIZE = 4096

END_MARKER = b"\xff\xff\x5a\xa5\xff\xff\xff\xff"

first_block = True
past_end = False
trailer = bytes()
trailer_pos = -1

csum = sha1()
print("Reading {} ...".format(FILE))
with open(FILE, "rb") as f:
    while True:
        block = f.read(BLOCKSIZE)
        if first_block:
            start = block.find(b"\xff\xff\xff\xff\xf0\xb9\x9d\x38\x0f\x46\x62\xc7")
            if start < 0:
                print("No Fenix firmware header found.")
            else:
                start += 4
                hwid = unpack("<H", block[start+24:start+24+2])[0]
                fver = unpack("<H", block[start+28:start+28+2])[0]
                print("- Hardware ID: 0x{:04x} / {:d} ({})".format(hwid, hwid, devices.get_name(hwid, 0, "Unknown device")))
                print("- Firmware Version: 0x{:04x} / {:04d}".format(fver, fver))
            first_block = False
        if END_MARKER in block:
            end_pos = block.find(END_MARKER)
            marker_end = end_pos + len(END_MARKER)
            past_end = True
            csum.update(block[0:marker_end])
            block = block[marker_end:]
            trailer_pos = f.tell() - len(block)
        if past_end:
            trailer += block
        else:
            csum.update(block)
        if len(block) < BLOCKSIZE:
            break
    f.close()

expected_sha1 = csum.hexdigest()
found_sha1 = trailer[:20].hex()
print("Calculated SHA1: {}".format(expected_sha1))
print("SHA1 in file   : {} (offset 0x{:x})".format(found_sha1, trailer_pos))

if expected_sha1 == found_sha1:
    print("☑ CHECKSUM VALID.")
else:
    print("☒ CHECKSUM INVALID!!! (Or GCD or other type.)")
