#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Prints out the structure of the given GCD file.
"""

from grmn import Gcd, ChkSum
import sys

FILE = sys.argv[1]

print("Opening {}".format(FILE))

gcd = Gcd(FILE)

for i, tlv in enumerate(gcd.struct):
    print("#{:03d}: {}".format(i, tlv))
