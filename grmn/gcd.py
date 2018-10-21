# -*- coding: utf-8 -*-
# Thanks to TurboCCC and kunix for all your work!

from .chksum import ChkSum
from .tlv import TLV, TLV6, TLV7
from struct import unpack
import configparser

GCD_SIG = b"G\x41RM\x49Nd\00"
DEFAULT_COPYRIGHT = b"Copyright 1996-2017 by G\x61rm\x69n Ltd. or its subsidiaries."
DEFAULT_FIRST_PADDING = 21
DEFAULT_ALIGN = 0x1000    # second padding block pads until 0x1000
MAX_BLOCK_LENGTH = 0xff00   # binary blocks max len

# Typical structure:
# first 0x1000 Bytes: GCD_SIG > 0x0001 > 0x0002 > 0x0003 > 0x0005 > 0x0001 > 0x0002
# then: 0x0001 > ( 0x0006 > 0x0007 > 0x???? > 0x0001 ... ) > 0xffff

class ParseException(Exception):
    pass

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
        last_tlv7 = None
        with open(self.filename, "rb") as f:
            sig = f.read(8)
            if sig != GCD_SIG:
                raise ParseException("Signature mismatch ({}, should be {})!".format(repr(sig), repr(GCD_SIG)))
            while True:
                cur_offset = f.tell()
                header = f.read(4)
                (type_id, length) = unpack("<HH", header)
                tlv = TLV.factory(type_id, length, offset=cur_offset)
                self.add_tlv(tlv)
                if tlv.type_id == 0xFFFF:
                    # End of file reached
                    break
                tlength = tlv.length
                payload = f.read(tlength)
                tlv.set_value(payload)
                if tlv.type_id == 0x0006:
                    last_tlv6 = tlv
                elif tlv.type_id == 0x0007:
                    tlv.set_tlv6(last_tlv6)
                    last_tlv7 = tlv
                elif tlv.is_binary:
                    tlv.set_tlv7(last_tlv7)
            f.close()

    def add_tlv(self, new_tlv: TLV):
        self.struct.append(new_tlv)

    def print_struct(self):
        """
        Prints the structure of the parsed GCD file
        """
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
                if tlv.length is not None:
                    tlv_length += tlv.length
            last_tlv = tlv.type_id

    def validate(self, print_stats: bool=False):
        """
        Checks and verifies all checksums in the GCD.
        """
        chksum = ChkSum()
        chksum.add(GCD_SIG)
        all_ok = True
        if print_stats:
            print("\nChecksum validation:")
        for tlv in self.struct:
            chksum.add(tlv.get())
            if tlv.type_id == 0x0001:
                expected_cs = chksum.get_expected()
                file_cs = chksum.get_last_byte()
                if print_stats:
                    if expected_cs == file_cs:
                        state = "OK"
                    else:
                        state = "INVALID"
                    print("TLV{:04x} at 0x{:x}: {:02x} (expected: {:02x}) = {}".format(tlv.type_id, tlv.offset, file_cs, expected_cs, state))
                if expected_cs != file_cs:
                    all_ok = False
        if print_stats:
            if all_ok:
                print("☑ ALL CHECKSUMS VALID.")
            else:
                print("☒ ONE OR MORE CHECKSUMS INVALID!")
        return all_ok

    def write_dump_block(self, f, name):
        f.write("\n[BLOCK_{}]\n".format(name))
    
    def write_dump_param(self, f, key, value, comment=None):
        if comment is not None:
            f.write("# {}\n".format(comment))
        f.write("{} = {}\n".format(key, value))

    def dump_to_files(self, output_basename: str):
        output_file = "{}.rcp".format(output_basename)
        ctr = 0
        last_filename = None
        with open(output_file, "wt") as f:
            f.write("[GCD_DUMP]\n")
            f.write("dump_by = grmn-gcd\n")
            f.write("dump_ver = 1\n")
            f.write("original_filename = {}\n\n".format(self.filename))
            f.write("# [BLOCK_nn] headers are just for parsing/grouping purposes.\n")
            f.write("# Lengths are informational only, they will be calculated upon reassembly.\n")
            for tlv in self.struct:
                if tlv.is_binary:
                    outfile = "{}_{:04x}.bin".format(output_basename, tlv.type_id)
                    if outfile != last_filename:
                        self.write_dump_block(f, str(ctr))
                        self.write_dump_param(f, "from_file", outfile)
                        for item in tlv.dump():
                            self.write_dump_param(f, item[0], item[1], item[2])
                        last_filename = outfile
                        with open(outfile, "wb") as of:
                            of.write(tlv.value)
                    else:
                        with open(outfile, "ab") as of:
                            of.write(tlv.value)
                elif tlv.type_id == 0xffff:
                    # EOF marker
                    pass
                else:
                    tlvinfo = tlv.dump()
                    if len(tlvinfo) > 0:
                        self.write_dump_block(f, str(ctr))
                        for item in tlvinfo:
                            self.write_dump_param(f, item[0], item[1], item[2])
                ctr += 1
            f.close()

    @staticmethod
    def from_recipe(recipe_file: str):
        gcd = Gcd()
        rcp = configparser.ConfigParser()
        rcp.read(recipe_file)
        if rcp["GCD_DUMP"]["dump_by"] != "grmn-gcd":
            raise ParseException("Recipe file invalid.")
        if rcp["GCD_DUMP"]["dump_ver"] != "1":
            raise ParseException("Recipe file wrong version.")
        for s in rcp.sections():
            if s == "GCD_DUMP":
                continue
            print("Parsing {}".format(s))
            if "from_file" in rcp[s]:
                # BINARY! Must create type 0006, 0007 and actual binary blocks
                print("Binary block")
            else:
                params = []
                for k in rcp[s]:
                    params.append((k, rcp[s][k]))
                tlv = TLV.create_from_dump(params)
                gcd.struct.append(tlv)
        return gcd
