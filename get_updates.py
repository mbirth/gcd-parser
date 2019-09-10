#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Queries the updateserver for given device's updates.
"""

from grmn import updateserver, devices
import sys

if len(sys.argv) < 2:
    print("Syntax: {} DEVICESKU".format(sys.argv[0]))
    print("Examples:")
    print("  {} 3196           - Query update info for 006-B3196-00".format(sys.argv[0]))
    print("  {} 006-B3196-00   - Query update info for given SKU".format(sys.argv[0]))
    sys.exit(1)

DEVICE = sys.argv[1]

us = updateserver.UpdateServer()

device_sku = DEVICE
if len(device_sku) <= 4:
    device_sku = "006-B{:>04}-00".format(device_sku)

hwid = int(device_sku[5:9])
device_name = devices.DEVICES.get(hwid, "Unknown device")

print("Device: {}".format(device_name))

us.query_updates([device_sku])
