#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Thanks to TurboCCC and kunix for all your work!

GCD_SIG = b"GARMINd\00"

from binascii import hexlify
from struct import unpack
import sys

FILE = sys.argv[1]

TLV_TYPES = {
    0x0001: "Checksum remainder",
    0x0002: "Skip?",
    0x0003: "Part number",
    0x0005: "Copyright notice",
    0x0006: "Block Type 7 format definition",
    0x0007: "Binary descriptor",
    0x0008: "Binary Region 0C (boot.bin)",
    0x0401: "Binary Component Firmware (SensorHub, ANT_BLE_BT, GPS, WiFi)",
    0x0505: "Binary Region 05",
    0x0555: "Binary Region 55",
    0x0557: "Binary Region 57",
    0x02bd: "Binary Region 0E (fw_all.bin)",
    0xffff: "EOF marker",
}

DEV_TYPES = {
    1551: "fenix/D2/tactix",
    2900: "fenix 5 Plus",
    3196: "D2 Delta",
}

running_cksum = 0
all_cksum_ok = True
last_type6_fids = []
last_type6_format = ""
last_type6_fields = []

def add_to_cksum(payload):
    global running_cksum
    for c in payload:
        running_cksum += c
        running_cksum &= 0xff

def get_tlv_comment(ttype):
    if ttype in TLV_TYPES:
        return TLV_TYPES[ttype]
    else:
        return "Type {:04x} / {:d}".format(ttype, ttype)

def get_device(hwid):
    if hwid in DEV_TYPES:
        return DEV_TYPES[hwid]
    else:
        return "Unknown"

print("Opening {}".format(FILE))

def parseTLVheader(hdr):
    (ttype, tlen) = unpack("<HH", hdr)
    return (ttype, tlen)

def parseTLV1(payload):
    global running_cksum, all_cksum_ok
    if len(payload) != 1:
        print("  ! Checksum has invalid length!")
        all_cksum_ok = False
    expected = ( 0x100 - running_cksum ) & 0xFF
    payload = unpack("B", payload)[0]
    state = "INVALID!"
    if expected == payload:
        state = "valid."
    else:
        all_cksum_ok = False
    print("  - Checksum expected: {:02x} / found: {:02x} - {}".format(expected, payload, state))

def parseTLV3(payload):
    # Part number?
    # 10 d4 5c 13 04 45 0d 14 41  - GPSMAP6x0_370
    # 10 d4 5c 13 04 45 0d 14 41  - fenix5Plus_SensorHub_220
    # 10 d4 5c 13 04 45 0d 14 41  - fenix_D2_tactix_500
    # 10 d4 5c 13 04 45 0d 14 41  - fenix5_1100
    # 10 d4 5c 13 04 45 0d 14 41  - fenix5Plus_420_rollback
    # 10 d4 5c 13 04 45 0d 14 41  - fenix5Plus_420
    # 10 d4 5c 13 04 45 0d 14 41  - fenix5Plus_510
    # 10 d4 5c 13 04 45 0d 14 41  - D2Delta_300
    print("  > " + " ".join("{:02x}".format(c) for c in payload))
    #print(hexlify(payload).decode("utf-8"))
    print("  > " + repr(payload))

def parseTLV6(payload):
    global last_type6_format, last_type6_fields, last_type6_fids
    # Describes following TLV7:
    # http://www.gpspassion.com/forumsen/topic.asp?TOPIC_ID=137838&whichpage=12
    # First nibble might be data type: 0 = B, 1 = H, 2 = L
    FIELD_TYPES = {
        0x000a: ["B", "XOR flag/value"],
        0x000b: ["B", "Reset/Downgrade flag"],
        0x1009: ["H", "Device hw_id"],
        0x100a: ["H", "Block type"],
        0x100d: ["H", "Firmware version"],
        0x1014: ["H", "Field 1014"],
        0x1015: ["H", "Field 1015"],
        0x1016: ["H", "Field 1016 (WiFi fw)"],
        0x2015: ["L", "Block size"],
        0x5003: ["", "End of definition marker"],
    }
    if len(payload) % 2 != 0:
        print("  ! Invalid payload length!")
    
    last_type6_fids = []
    last_type6_format = ""
    last_type6_fields = []

    for i in range(0, len(payload), 2):
        fid = unpack("H", payload[i:i+2])[0]
        fdef = FIELD_TYPES[fid]
        print("  - {:04x}: {}".format(fid, fdef[1]))
        last_type6_fids.append(fid)
        last_type6_format += fdef[0]
        last_type6_fields.append(fdef[1])

def parseTLV7(payload):
    global last_type6_format, last_type6_fields, last_type6_fids
    values = unpack("<" + last_type6_format, payload)
    for i, v in enumerate(values):
        fid = last_type6_fids[i]
        fdesc = last_type6_fields[i]
        if fid == 0x1009:
            print("  - {:>20}: 0x{:04x} / {:d} ({})".format(fdesc, v, v, get_device(v)))
        elif fid == 0x2015:
            print("  - {:>20}: {} Bytes".format(fdesc, v))
        else:
            print("  - {:>20}: 0x{:04x} / {:d}".format(fdesc, v, v))

with open(FILE, "rb") as f:
    sig = f.read(8)
    add_to_cksum(sig)
    if sig == GCD_SIG:
        print("Signature ok.")
    else:
        raise Exception("Signature mismatch ({}, should be {})!".format(repr(sig), repr(GCD_SIG)))

    i = 0

    while True:
        hdr = f.read(4)
        add_to_cksum(hdr)
        (ttype, tlen) = parseTLVheader(hdr)
        print("#{:04} TLV type {:04x} (offset 0x{:x}, length {} Bytes) - {}".format(i, ttype, f.tell(), tlen, get_tlv_comment(ttype)))
        if ttype == 0xFFFF:
            print("End of file reached.")
            break
        payload = f.read(tlen)
        if ttype == 0x01:
            parseTLV1(payload)
        elif ttype == 0x03:
            parseTLV3(payload)
        elif ttype == 0x06:
            parseTLV6(payload)
        elif ttype == 0x07:
            parseTLV7(payload)
        else:
            payloadshort = payload[:64]
            #print("  > " + " ".join("{:02x}".format(c) for c in payloadshort))
            #print(hexlify(payload).decode("utf-8"))
            #print("  > " + repr(payloadshort))
        add_to_cksum(payload)
        if ttype in [0x0505]:
            with open("fw_{:04x}.bin".format(ttype), "ab") as of:
                of.write(payload)
        i = i + 1

if not all_cksum_ok:
    print("There were problems with at least one checksum!")
