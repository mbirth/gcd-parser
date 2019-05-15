GCD Parser
==========

This is a parser and some tools for working with GCD files (firmware updates from a well-known manufacturer).

It's in Python, so feel free to add cool new features and submit pull requests.

Thanks to TurboCCC, kunix and Alex W. for your work.

Most info from:

* http://www.gpspassion.com/forumsen/topic.asp?TOPIC_ID=115804&whichpage=1
* http://www.gpspassion.com/forumsen/topic.asp?TOPIC_ID=137838&whichpage=50
* hours of looking at hex numbers


Tools
-----

### gcdstruct.py [gcdfile]

Will show the general structure of the GCD file and also validate the contained checksums, e.g.:

```
$ ./gcdstruct.py fenix5Plus_510.gcd
Opening fenix5Plus_510.gcd
#000: TLV Type 0001 at 0x8, 1 Byte - Checksum rectifier
#001: TLV Type 0002 at 0xd, 21 Bytes - Padding
#002: TLV Type 0003 at 0x26, 9 Bytes - Part number?
#003: TLV Type 0005 at 0x33, 55 Bytes - Copyright notice
#004: TLV Type 0001 at 0x6e, 1 Byte - Checksum rectifier
#005: TLV Type 0002 at 0x73, 3977 Bytes - Padding
#006: TLV Type 0001 at 0x1000, 1 Byte - Checksum rectifier
#007: TLV Type 0006 at 0x1005, 18 Bytes - Block Type 7 format definition
  - Field 1: 000b - Reset/Downgrade flag
  - Field 2: 000a - XOR flag/value
  - Field 3: 100a - Block type
  - Field 4: 2015 - Binary length
  - Field 5: 1009 - Device hw_id
  - Field 6: 1014 - Field 1014
  - Field 7: 1015 - Field 1015
  - Field 8: 100d - Firmware version
  - Field 9: 5003 - End of definition marker
#008: TLV Type 0007 at 0x101b, 16 Bytes - Binary descriptor
  - Field 1: Reset/Downgrade flag: 0x0000 / 0
  - Field 2:       XOR flag/value: 0x0000 / 0
  - Field 3:           Block type: 0x0505 / 1285
  - Field 4:        Binary length: 52736 Bytes
  - Field 5:         Device hw_id: 0x0b54 / 2900 (Fenix 5 Plus)
  - Field 6:           Field 1014: 0x00c8 / 200
  - Field 7:           Field 1015: 0x003b / 59
  - Field 8:     Firmware version: 0x01fe / 510
#009: TLV Type 0505 at 0x102f, 52736 Bytes - Binary Region 05
#010: TLV Type 0001 at 0xde33, 1 Byte - Checksum rectifier
#011: TLV Type 0006 at 0xde38, 18 Bytes - Block Type 7 format definition
  - Field 1: 000b - Reset/Downgrade flag
  - Field 2: 000a - XOR flag/value
  - Field 3: 100a - Block type
  - Field 4: 2015 - Binary length
  - Field 5: 1009 - Device hw_id
  - Field 6: 1014 - Field 1014
  - Field 7: 1015 - Field 1015
  - Field 8: 100d - Firmware version
  - Field 9: 5003 - End of definition marker
#012: TLV Type 0007 at 0xde4e, 16 Bytes - Binary descriptor
  - Field 1: Reset/Downgrade flag: 0x0000 / 0
  - Field 2:       XOR flag/value: 0x0000 / 0
  - Field 3:           Block type: 0x02bd / 701
  - Field 4:        Binary length: 9697792 Bytes
  - Field 5:         Device hw_id: 0x0b54 / 2900 (Fenix 5 Plus)
  - Field 6:           Field 1014: 0x00c8 / 200
  - Field 7:           Field 1015: 0x003b / 59
  - Field 8:     Firmware version: 0x01fe / 510
#013: TLV Type 02bd at 0xde62, 65280 Bytes - Binary Region 0E (fw_all.bin)
 + 148 more (9697792 Bytes total payload)
#162: TLV Type 0001 at 0x94dab6, 1 Byte - Checksum rectifier
#163: TLV Type ffff at 0x94dabb - EOF marker

Checksum validation:
TLV0001 at 0x8: dc (expected: dc) = OK
TLV0001 at 0x6e: 47 (expected: 47) = OK
TLV0001 at 0x1000: 64 (expected: 64) = OK
TLV0001 at 0xde33: 88 (expected: 88) = OK
TLV0001 at 0x94dab6: c7 (expected: c7) = OK
☑ ALL CHECKSUMS VALID.
```


### gcksum.py [binfile]

Will calculate and verify the trailing byte for binary files, e.g.:

```
$ ./gcksum.py test_0505.bin 
Reading test_0505.bin ...... done.
Sum of all bytes: 00
Last byte: f2
☑ CHECKSUM VALID.
```


### binsum.py [binfile]

Will calculate and verify the SHA1 checksum of (Fenix?) firmware files, e.g.:

```
$ ./binsum.py test_02bd.bin 
Reading test_02bd.bin ...
- Hardware ID: 0x0b54 / 2900 (Fenix 5 Plus)
- Firmware Version: 0x0136 / 0310
Calculated SHA1: f0d31379e0de29d3710e815570d346c5dda4ef9a
SHA1 in file   : f0d31379e0de29d3710e815570d346c5dda4ef9a (offset 0x8d1bbc)
☑ CHECKSUM VALID.
```


### gcddump.py [gcdfile] [basename]

**Note:** Second parameter doesn't have an extension!

Extracts binaries from GCD file and also creates a "recipe" file from which the GCD can be rebuilt, e.g.:

```
$ ./gcddump.py fenix5Plus_510.gcd f5p_v510
Opening fenix5Plus_510.gcd
Dumping to f5p_v510.rcp
```

Will write 3 files:

* `f5p_v510.rcp` --- the "recipe" to recreate the GCD
* `f5p_v510_0505.bin` --- loader (region 05)
* `f5p_v510_02bd.bin` --- firmware (region 0E)

The recipe is human-readable. And while the block titles (e.g. `[BLOCK_234]`) are ignored, the order of the blocks in the file is important.


### gcdcompile.py [recipefile] [gcdfile]

Creates a GCD file from the given recipe, e.g.:

```
$ ./gcdcompile.py f5p_v510.rcp fenix5Plus_510_new.gcd
Opening recipe f5p_v510.rcp
Parsing BLOCK_0
Parsing BLOCK_1
Parsing BLOCK_2
Parsing BLOCK_3
Parsing BLOCK_4
Parsing BLOCK_5
Parsing BLOCK_6
Parsing BLOCK_9
Parsing BLOCK_10
Parsing BLOCK_13
Parsing BLOCK_162
... here will be the structure of the to-be-created file ...
Dumping to fenix5Plus_510_new.gcd
```

Checksums (in the GCD file, NOT in the binaries!) will be corrected automatically.
