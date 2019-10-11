#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Prints out the structure of the given GCD file.
"""

from grmn import Gcd, ChkSum
import sys

if len(sys.argv) <= 2:
    VERBOSE = False
    FILE = sys.argv[1]
elif sys.argv[1] == "--verbose":
    VERBOSE = True
    FILE = sys.argv[2]
elif sys.argv[2] == "--verbose":
    VERBOSE = True
    FILE = sys.argv[1]

print("Opening {}".format(FILE))

gcd = Gcd(FILE)

if VERBOSE:
    gcd.print_struct_full()
else:
    gcd.print_struct()

gcd.validate(True)
