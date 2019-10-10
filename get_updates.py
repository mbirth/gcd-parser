#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Queries the updateserver for given device's updates.
"""

__author__ = "mbirth"

from grmn import updateserver, devices
from optparse import OptionParser, OptionGroup
import json
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
optp.add_option("--json", action="store_true", dest="json", default=False, help="Output JSON")
optp.add_option("--list-devices", action="store_true", dest="list_devices", default=False, help="Show a list of SKUs and product names")
optp.add_option("--debug", action="store_true", dest="debug", default=False, help="Dump raw server requests and replies to files")

optp.usage = """
  %prog [options] SKU1 [SKU2..SKUn]

Examples:
  %prog 3196           - Query update info for 006-B3196-00
  %prog 006-B3196-00   - Query update info for given SKU
  %prog --devicexml=~/fenix/GARMIN/GarminDevice.xml"""

(opts, device_skus) = optp.parse_args()

if opts.list_devices:
    if opts.json:
        print(json.dumps(devices.DEVICES))
    else:
        print("HWID - Device/Component")
        for hwid, name in devices.DEVICES.items():
            print("{:>04} - {}".format(hwid, name))
        print()
        print("SKU format is 006-Bxxxx-00 with xxxx being the HWID.")
    sys.exit(0)
elif len(device_skus) < 1 and not opts.devicexml:
    optp.print_help()
    sys.exit(1)

us = updateserver.UpdateServer()

if opts.debug:
    us.debug = True

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
    reply = us.get_unit_updates(device_xml)
    print(" done.")

    results = []
    if reply:
        for i in range(0, len(reply.update_info)):
            ui = reply.update_info[i]
            r = updateserver.UpdateInfo()
            r.fill_from_protobuf(ui)
            results.append(r)

    print(results)
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
    results += us.query_express(device_skus)
    print(" done.")

if opts.webupdater:
    print("Querying Garmin WebUpdater ...", end="", flush=True)
    results += us.query_webupdater(device_skus)
    print(" done.")

for r in results:
    print(r)
