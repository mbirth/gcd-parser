#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Parses a recipe file and builds a GCD file from it.
"""

from grmn import Gcd
import sys

if len(sys.argv) < 3:
    print("Syntax: {} RCPFILE GCDFILE".format(sys.argv[0]))
    sys.exit(1)

RECIPE = sys.argv[1]
OUTFILE = sys.argv[2]

print("Opening recipe {}".format(RECIPE))
gcd = Gcd.from_recipe(RECIPE)
gcd.print_struct()
#print("Dumping to {}".format(OUTFILE))
#gcd.write_to_file(OUTFILE)
