#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from grmn import ChkSum
import sys

FILE = sys.argv[1]
BLOCKSIZE = 4 * 1024

print("Reading {} ".format(FILE), end="")

csum = ChkSum()

with open(FILE, "rb") as f:
    while True:
        block = f.read(BLOCKSIZE)
        csum.add(block)
        print(".", end="", flush=True)
        if len(block) < BLOCKSIZE:
            print(" done.")
            break
    f.close()

print("Sum of all bytes: {:02x}".format(csum.get_sum()))
print("Last byte: {:02x}".format(csum.get_last_byte()))
if csum.is_valid():
    print("☑ CHECKSUM VALID.")
else:
    print("☒ CHECKSUM INVALID!!! (Or GCD or other type.)")
    expected_cksum = csum.get_expected()
    print("Expected last byte: {:02x}".format(expected_cksum))
