#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from grmn import devices

last_id = 0
missing = []
for i in range(0, 9999):
    if i in devices.DEVICES:
        last_id = i
        continue
    missing.append(i)

print("./get_updates.py", end="")

missing_count = 0
cur_line = 0
for i in range(0, 9999):
    if i >= last_id:
        break
    if i % 10 == 0 and cur_line > 5:
        print()
        print("./get_updates.py", end="")
        cur_line = 0
    if not i in missing:
        continue
    if i <= last_id:
        print(" {:04}".format(i), end="")
        missing_count += 1
        cur_line += 1


print()
print("{} unknown ids.".format(missing_count))
print("Last known id is: {:04}".format(last_id))
print("-" * 100)
print("Here are some possible future ids:")

print("./get_updates.py", end="")

cur_line = 0
for i in range(last_id + 1, last_id + 100):
    if i % 10 == 0 and cur_line > 5:
        print()
        print("./get_updates.py", end="")
        cur_line = 0
    print(" {:04}".format(i), end="")
    cur_line += 1

print()
