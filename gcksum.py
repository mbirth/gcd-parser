#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from binascii import hexlify
from struct import unpack
import sys

FILE = sys.argv[1]

print("Opening {}".format(FILE))

csum_pre = 0
csum = 0
last_byte = 0xff

with open(FILE, "rb") as f:
    while True:
        block = f.read(1024)
        for c in block:
            csum_pre = csum
            csum += c
            csum &= 0xff
            last_byte = c
        if len(block) < 1024:
            print("End reached.")
            break

print("Sum of all bytes: {:02x}".format(csum))
if csum == 0:
    print("CHECKSUM VALID.")
else:
    print("CHECKSUM INVALID!!! (Or GCD or other type.)")

#print("Sum without last: {:02x}".format(csum_pre))

expected_cksum = ( 0x100 - csum_pre ) & 0xff

print("Expected last byte: {:02x}".format(expected_cksum))
print("Actual last byte: {:02x}".format(last_byte))
