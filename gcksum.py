#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from binascii import hexlify
from struct import unpack
import sys

FILE = sys.argv[1]

print("Opening {}".format(FILE))

csum = 0

with open(FILE, "rb") as f:
    while True:
        block = f.read(1024)
        for c in block:
            csum += c
            csum &= 0xff
        if len(block) < 1024:
            print("End reached.")
            break

print("Sum of all bytes: {}".format(csum))
