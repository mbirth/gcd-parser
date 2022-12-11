#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Supply any parameter to the script to also show possible future hwids.

from grmn import devices
import sys

largest_gap = -1
gap_counter = 0
last_id = 0
missing = []
for i in range(0, 9999):
    if i in devices.DEVICES:
        last_id = i
        if gap_counter > largest_gap:
            largest_gap = gap_counter
        gap_counter = 0
        continue
    missing.append(i)
    gap_counter += 1

missing_count = 0
cur_line = []
queue = []
for i in range(0, last_id+1):
    if i % 10 == 0:
        if len(cur_line) + len(queue) > 15:
            print("./get_updates.py -q {}".format(" ".join(cur_line)))
            cur_line = queue
        else:
            cur_line += queue
        queue = []
    if i not in missing:
        continue
    queue.append("{:04}".format(i))
    missing_count += 1

cur_line += queue
if len(cur_line) > 0:
    print("./get_updates.py -q {}".format(" ".join(cur_line)))

known_count = len(devices.DEVICES)
print()
print("{} known, {} unknown ids. Last known id is: {:04d}".format(known_count, missing_count, last_id))
print("Largest gap is: {}".format(largest_gap))


if len(sys.argv) > 1:
    print("-" * 100)
    print("Here are some possible future ids:")

    print("./get_updates.py -q", end="")

    cur_line = 0
    for i in range(last_id + 1, last_id + 300):
        if i % 10 == 0 and cur_line > 5:
            print()
            print("./get_updates.py -q", end="")
            cur_line = 0
        print(" {:04}".format(i), end="")
        cur_line += 1

    print()
