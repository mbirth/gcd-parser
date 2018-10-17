# -*- coding: utf-8 -*-
# Thanks to TurboCCC and kunix for all your work!

from .tlv import TLV, TLV6, TLV7

GCD_SIG = b"G\x41RM\x49Nd\00"
DEFAULT_COPYRIGHT = b"Copyright 1996-2017 by G\x61rm\x69n Ltd. or its subsidiaries."
DEFAULT_FIRST_PADDING = 21
DEFAULT_ALIGN = 0x1000    # second padding block pads until 0x1000

# Typical structure:
# first 0x1000 Bytes: GCD_SIG > 0x0001 > 0x0002 > 0x0003 > 0x0005 > 0x0001 > 0x0002
# then: 0x0001 > ( 0x0006 > 0x0007 > 0x???? > 0x0001 ... ) > 0xffff

class Gcd:
    def __init__(self, filename: str=None):
        self.filename = filename
        self.struct = []
        if filename is not None:
            self.load()

    def load(self):
        if self.filename is None:
            return False
        last_tlv6 = None
        with open(self.filename, "rb") as f:
            sig = f.read(8)
            if sig != GCD_SIG:
                raise Exception("Signature mismatch ({}, should be {})!".format(repr(sig), repr(GCD_SIG)))
            while True:
                cur_offset = f.tell()
                header = f.read(4)
                tlv = TLV.factory(header, offset=cur_offset)
                self.struct.append(tlv)
                if tlv.type_id == 0xFFFF:
                    # End of file reached
                    break
                tlength = tlv.get_length()
                payload = f.read(tlength)
                tlv.set_value(payload)
                if tlv.type_id == 0x0006:
                    last_tlv6 = tlv
                elif tlv.type_id == 0x0007:
                    tlv.set_tlv6(last_tlv6)
            f.close()

    def print_struct(self):
        last_tlv = 0xffff
        tlv_count = 0
        tlv_length = 0
        for i, tlv in enumerate(self.struct):
            if tlv.type_id != last_tlv:
                if tlv_count > 0:
                    print(" + {} more ({} Bytes total payload)".format(tlv_count, tlv_length))
                    tlv_count = 0
                tlv_length = tlv.length
                print("#{:03d}: {}".format(i, tlv))
            else:
                tlv_count += 1
                tlv_length += tlv.get_length()
            last_tlv = tlv.type_id
