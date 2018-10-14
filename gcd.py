#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
    global last_type6_format, last_type6_fields
    # Describes following TLV7:
    # http://www.gpspassion.com/forumsen/topic.asp?TOPIC_ID=137838&whichpage=12
    # First nibble might be data type: 0 = B, 1 = H, 2 = L
    FIELD_TYPES = {
        0x000a: ["B", "XOR flag/value"],
        0x000b: ["B", "Reboot/Downgrade flag"],
        0x1009: ["H", "Device hw_id"],
        0x100a: ["H", "Block type"],
        0x1014: ["H", "Field 1014"],
        0x1015: ["H", "Field 1015"],
        0x1016: ["H", "Field 1016 (WiFi fw)"],
        0x2015: ["L", "Block size"],
        0x5003: ["", "End of definition marker"],
    }
    #             0a 10 15 20 09 10             0d 10 03 50 - 10 - fenix_D2_tactix_500 (before 0008)
    # 0b 00 0a 00 0a 10 15 20 09 10             0d 10 03 50 - 14 - fenix_D2_tactix_500 (before 0555)
    # 0b 00 0a 00 0a 10 15 20 09 10             0d 10 03 50 - 14 - fenix_D2_tactix_500 (before 0557)
    # 0b 00 0a 00 0a 10 15 20                         03 50 - 10 - fenix5Plus_SensorHub_220
    # 0b 00 0a 00 0a 10 15 20                         03 50 - 10 - fenix5Plus_ANT_BLE_300
    # 0b 00 0a 00 0a 10 15 20                   16 10 03 50 - 12 - fenix5Plus_WiFi_250
    # 0b 00 0a 00 0a 10 15 20 09 10 14 10 15 10 0d 10 03 50 - 18 - fenix5_1100 (before 0505)
    # 0b 00 0a 00 0a 10 15 20 09 10 14 10 15 10 0d 10 03 50 - 18 - fenix5_1100 (before 02BD)
    # 0b 00 0a 00 0a 10 15 20 09 10 14 10 15 10 0d 10 03 50 - 18 - fenix5Plus_420_rollback.gcd (has only 1 Type 02BD)
    # 0b 00 0a 00 0a 10 15 20 09 10 14 10 15 10 0d 10 03 50 - 18 - fenix5Plus_420.gcd (before Type 0505)
    # 0b 00 0a 00 0a 10 15 20 09 10 14 10 15 10 0d 10 03 50 - 18 - fenix5Plus_420.gcd (before Type 02BD)
    # 0b 00 0a 00 0a 10 15 20 09 10 14 10 15 10 0d 10 03 50 - 18 - fenix5Plus_510.gcd (before Type 0505)
    # 0b 00 0a 00 0a 10 15 20 09 10 14 10 15 10 0d 10 03 50 - 18 - fenix5Plus_510.gcd (before Type 02BD)
    # 0b 00 0a 00 0a 10 15 20 09 10 14 10 15 10 0d 10 03 50 - 18 - D2Delta_300 (before 0505)
    # 0b 00 0a 00 0a 10 15 20 09 10 14 10 15 10 0d 10 03 50 - 18 - D2Delta_300 (before 02BD)
    print("  > " + " ".join("{:02x}".format(c) for c in payload))
    #print(hexlify(payload).decode("utf-8"))
    print("  > " + repr(payload))

def parseTLV7(payload):
    # fenix/D2/tactix: hwid 060f
    # fenix 5 Plus: hwid 0b54
    # D2 Delta: hwid 0c7c
    #       08 00 00 a2 04 00 0f 06             f4 01  - 10 - fenix_D2_tactix_500 (before 0008)
    # 00 00 55 05 00 c0 01 00 0f 06             f4 01  - 12 - fenix_D2_tactix_500 (before 0555)
    # 00 00 57 05 00 90 01 00 0f 06             f4 01  - 12 - fenix_D2_tactix_500 (before 0557)
    # 00 00 05 05 00 94 00 00 89 0a c8 00 4e 00 4c 04  - 16 - fenix5_1100 (before 0505)
    # 00 00 bd 02 00 46 3b 00 89 0a c8 00 4e 00 4c 04  - 16 - fenix5_1100 (before 02BD)
    # 01 00 01 04 0c 0e 06 00                          -  8 - fenix5Plus_SensorHub_220 (before 0401)
    # 01 00 01 04 f7 0f 02 00                          -  8 - fenix5Plus_ANT_BLE_300 (before 0401)
    # 00 00 01 04 e4 4f 06 00       40 33              - 10 - fenix5Plus_WiFi_250
    # 01 00 bd 02 00 2a 8d 00 54 0b c8 00 3b 00 a4 01  - 16 - fenix5Plus_420_rollback.gcd (has only 02BD)
    # 00 00 05 05 00 ce 00 00 54 0b c8 00 3b 00 a4 01  - 16 - fenix5Plus_420.gcd (before Type 0505)
    # 00 00 bd 02 00 2a 8d 00 54 0b c8 00 3b 00 a4 01  - 16 - fenix5Plus_420.gcd (before Type 02BD)
    # 00 00 05 05 00 ce 00 00 54 0b c8 00 3b 00 fe 01  - 16 - fenix5Plus_510.gcd (before Type 0505)
    # 00 00 bd 02 00 fa 93 00 54 0b c8 00 3b 00 fe 01  - 16 - fenix5Plus_510.gcd (before Type 02BD)
    # 00 00 05 05 00 ce 00 00 7c 0c c8 00 01 00 2c 01  - 16 - D2Delta_300.gcd (before Type 0505)
    # 00 00 bd 02 00 99 94 00 7c 0c c8 00 01 00 2c 01  - 16 - D2Delta_300.gcd (before Type 02BD)
    # ^^ ^^ ^___^ ^_________^ ^___^             ^___^
    # E  X  btype   blength    HWID             FwVer
    erase = None
    xor = None
    hwid = None
    nn6 = None
    nn7 = None
    fwver = None
    if len(payload) == 16:
        (erase, xor, btype, blen, hwid, nn6, nn7, fwver) = unpack("<BBHLHHHH", payload)
    elif len(payload) == 12:
        (erase, xor, btype, blen, hwid, fwver) = unpack("<BBHLHH", payload)
    elif len(payload) == 10:
        (btype, blen, hwid, fwver) = unpack("<HLHH", payload)
        if btype == 0x0:
            # other format
            print("  ! First try to parse didn't make sense. Trying other format.")
            hwid  = None   # reset
            fwver = None   # reset
            (erase, xor, btype, blen, nn6) = unpack("<BBHLH", payload)
    elif len(payload) == 8:
        (erase, xor, btype, blen) = unpack("<BBHL", payload)
    else:
        print("Type 7 not an expected length. ({} Bytes)".format(len(payload)))
        return
    if erase is not None: print("  - Reset/Downgrade flag?: {}".format(erase))
    if xor is not None: print("  - XOR flag?: {}".format(xor))
    print("  - Block type: {:04x}".format(btype))
    print("  - Block length: {:d} Bytes".format(blen))
    if hwid is not None: print("  - Device hw_id: 0x{:04x} / {:d} ({})".format(hwid, hwid, get_device(hwid)))
    if nn6 is not None: print("  - Unknown: {:04x} / {:d}".format(nn6, nn6))
    if nn7 is not None: print("  - Unknown: {:04x} / {:d}".format(nn7, nn7))
    if fwver is not None: print("  - Firmware version: {:d}".format(fwver))

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
