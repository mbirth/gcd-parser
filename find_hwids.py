#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Parses a binary file for 006-Bxxxx-xx or 006Bxxxxxx occurrances.
"""

import os.path
import re
import sys
from grmn import devices

FILE = sys.argv[1]

pattern = re.compile(rb"006-?B\d\d\d\d-?[0-9A-F]{2}")

print("Reading {} ...".format(FILE))
with open(FILE, "rb") as f:
    data = f.read()
    f.close()

matches = pattern.findall(data)
results = []

for i in matches:
    i = i.decode("utf-8")
    if len(i) == 10:
        i = "{}-{}-{}".format(i[0:3], i[3:8], i[8:])
    results.append(i)

results = sorted(set(results))

for r in results:
    print(r, end="")
    hw_id = int(r[5:9])
    if hw_id in devices.DEVICES:
        print(" - {}".format(devices.DEVICES[hw_id]), end="")
    print()
