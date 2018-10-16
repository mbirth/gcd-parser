# -*- coding: utf-8 -*-

class ChkSum:

    def __init__(self):
        self.chksum = 0
        self.chksum_without_last = 0
        self.last_byte = 0xff

    def add(self, data):
        for c in data[:-1]:
            self.chksum += c
        self.chksum_without_last = self.chksum
        self.chksum_without_last &= 0xff
        self.last_byte = data[-1]
        self.chksum += self.last_byte
        self.chksum &= 0xff

    def get(self):
        remainder = ( 0x100 - self.chksum ) & 0xff
        return remainder

    def get_sum(self):
        return self.chksum

    def is_valid(self):
        return (self.chksum == 0)

    def get_expected(self):
        expected = ( 0x100 - self.chksum_without_last ) & 0xff
        return expected

    def get_last_byte(self):
        return self.last_byte
