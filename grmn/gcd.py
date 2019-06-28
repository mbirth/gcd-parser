# -*- coding: utf-8 -*-
# Thanks to TurboCCC and kunix for all your work!

from .chksum import ChkSum
from .tlv import TLV, TLV6, TLV7, TLVbinary
from struct import unpack
import configparser
import sys

GCD_SIG = b"G\x41RM\x49Nd\00"
DEFAULT_COPYRIGHT = b"Copyright 1996-2017 by G\x61rm\x69n Ltd. or its subsidiaries."
DEFAULT_FIRST_PADDING = 21
DEFAULT_ALIGN = 0x1000    # second padding block pads until 0x1000
MAX_BLOCK_LENGTH = 0xff00   # binary blocks max len (0xff40 for some blocks)

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

    def print_struct_full(self):
        """
        Prints the structure of the parsed GCD file
        """
        for i, tlv in enumerate(self.struct):
            print("#{:03d}: {}".format(i, tlv))

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

    def fix_checksums(self):
        chksum = ChkSum()
        chksum.add(GCD_SIG)
        for tlv in self.struct:
            if tlv.type_id == 0x0001:
                chksum.add(b"\x01\x00\x01\x00")
                expected_cs = chksum.get()
                tlv.value = bytes([expected_cs])
                chksum.add(bytes([expected_cs]))
            else:
                chksum.add(tlv.get())

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
                    if outfile is None:
                        outfile = "{}_{:04x}_{:x}.bin".format(output_basename, tlv.type_id, tlv.offset)
                        self.write_dump_block(f, str(ctr))
                        self.write_dump_param(f, "from_file", outfile)
                        for item in tlv.dump():
                            self.write_dump_param(f, item[0], item[1], item[2])
                        with open(outfile, "wb") as of:
                            of.write(tlv.value)
                    else:
                        with open(outfile, "ab") as of:
                            of.write(tlv.value)
#                        if tlv.length < MAX_BLOCK_LENGTH:
#                            # Reset outfile name, so should new binary block begin, dump that to new file
#                            outfile = None
                elif tlv.type_id == 0xffff:
                    # EOF marker
                    pass
                else:
                    outfile = None
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
            params = []
            for k in rcp[s]:
                params.append((k, rcp[s][k]))
            if "from_file" in rcp[s]:
                # BINARY! Must create type 0006, 0007 and actual binary block(s)
                tlv6 = TLV6(0x0006, None)
                tlv6.load_dump(params)
                gcd.struct.append(tlv6)

                tlv7 = TLV7(0x0007, None)
                tlv7.set_tlv6(tlv6)
                tlv7.load_dump(params)
                gcd.struct.append(tlv7)

                tlv7.parse()
                filename = rcp[s]["from_file"]
                file_type_id = tlv7.binary_type_id

                running_count = 0
                with open(filename, "rb") as bf:
                    while True:
                        read_bytes = bf.read(MAX_BLOCK_LENGTH)
                        btlv = TLVbinary(file_type_id, len(read_bytes))
                        btlv.value = read_bytes
                        gcd.struct.append(btlv)
                        running_count += len(read_bytes)
                        if len(read_bytes) < MAX_BLOCK_LENGTH:
                            break
                    bf.close()
                tlv7.set_binary_length(running_count)
            else:
                tlv = TLV.create_from_dump(params)
                gcd.struct.append(tlv)
        gcd.fix_checksums()
        return gcd

    def save(self, filename):
        self.filename = filename
        with open(filename, "wb") as f:
            f.write(GCD_SIG)
            for tlv in self.struct:
                f.write(tlv.get())
            f.write(b"\xff\xff\x00\x00")   # footer
            f.close()
