#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Queries the updateserver for given device's updates.
"""

from grmn import updateserver, devices
import sys

if len(sys.argv) < 2:
    print("Syntax: {} DEVICESKU1 [DEVICESKU2..n]".format(sys.argv[0]))
    print("Examples:")
    print("  {} 3196           - Query update info for 006-B3196-00".format(sys.argv[0]))
    print("  {} 006-B3196-00   - Query update info for given SKU".format(sys.argv[0]))
    sys.exit(1)

device_skus = sys.argv[1:]

us = updateserver.UpdateServer()

for i, sku in enumerate(device_skus):
    if len(sku) <= 4:
        device_skus[i] = "006-B{:>04}-00".format(sku)

primary_hwid = int(device_skus[0][5:9])
device_name = devices.DEVICES.get(primary_hwid, "Unknown device")

print("Device: {}".format(device_name))

us.query_updates(device_skus)
