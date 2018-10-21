#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dumps the structure of the given GCD file to file.
"""

from grmn import Gcd
import sys

if len(sys.argv) < 3:
    print("Syntax: {} GCDFILE OUTPUTBASENAME (extension .rcp will be added)".format(sys.argv[0]))
    sys.exit(1)

FILE = sys.argv[1]
OUTBASENAME = sys.argv[2]

print("Opening {}".format(FILE))
gcd = Gcd(FILE)
print("Dumping to {}.rcp".format(OUTBASENAME))
gcd.dump_to_files(OUTBASENAME)
