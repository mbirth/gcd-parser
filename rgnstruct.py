#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Prints out the structure of the given RGN file.
"""

from grmn import Rgn
import sys

FILE = sys.argv[1]

print("Opening {}".format(FILE))

rgn = Rgn(FILE)

rgn.print_struct()
#rgn.validate(True)
