#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Queries the updateserver for given device's updates.
"""

__author__ = "mbirth"

from grmn import updateserver, devices
from optparse import OptionParser, OptionGroup
import os.path
import sys

optp = OptionParser(usage="usage: %prog [options] SKU1 [SKU2..SKUn]")
optp.add_option("-c", "--changelog", action="store_true", dest="changelog", help="also show changelog")
optp.add_option("-l", "--license", action="store_true", dest="license", help="also show license")
optp.add_option("-E", "--express", action="store_false", dest="webupdater", default=True, help="Only query Garmin Express")
optp.add_option("-W", "--webupdater", action="store_false", dest="express", default=True, help="Only query WebUpdater")
optp.add_option("--id", dest="unit_id", help="Specify custom Unit ID")
optp.add_option("--code", action="append", dest="unlock_codes", metavar="UNLOCK_CODE", default=[], help="Specify map unlock codes")
optp.add_option("--devicexml", dest="devicexml", metavar="FILE", help="Use specified GarminDevice.xml (also implies -E)")

optp.usage = """
  %prog [options] SKU1 [SKU2..SKUn]

Examples:
  %prog 3196           - Query update info for 006-B3196-00
  %prog 006-B3196-00   - Query update info for given SKU
  %prog --devicexml=~/fenix/GARMIN/GarminDevice.xml"""

(opts, device_skus) = optp.parse_args()

if len(device_skus) < 1 and not opts.devicexml:
    optp.print_help()
    sys.exit(1)

us = updateserver.UpdateServer()

if opts.devicexml:
    # Filename given, load GarminDevice.xml from there; also disable WebUpdater
    print("Using GarminDevice.xml from {}.".format(opts.devicexml))
    if not os.path.isfile(opts.devicexml):
        print("ERROR: Not a file.", file=sys.stderr)
        sys.exit(2)
    device_xml = ""
    with open(opts.devicexml, "rt") as f:
        device_xml = f.read()
    print("Querying Garmin Express ...", end="", flush=True)
    result = us.get_unit_updates(device_xml)
    print(" done.")
    print(result)
    sys.exit(0)

# If no GarminDevice.xml read from file, continue here
for i, sku in enumerate(device_skus):
    if len(sku) <= 4:
        device_skus[i] = "006-B{:>04}-00".format(sku)

if device_skus[0][0:5] == "006-B":
    primary_hwid = int(device_skus[0][5:9])
    device_name = devices.DEVICES.get(primary_hwid, "Unknown device")
    print("Device (guessed): {}".format(device_name))

if opts.unit_id:
    print("Custom Unit ID: {}".format(opts.unit_id))
    us.device_id = opts.unit_id

for uc in opts.unlock_codes:
    print("Unlock Code: {}".format(uc))
    us.unlock_codes.append(uc)

results = []

if opts.express:
    print("Querying Garmin Express ...", end="", flush=True)
    results.append(us.query_express(device_skus))
    print(" done.")

if opts.webupdater:
    print("Querying Garmin WebUpdater ...", end="", flush=True)
    results.append(us.query_webupdater(device_skus))
    print(" done.")

print(results)
