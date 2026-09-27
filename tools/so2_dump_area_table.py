"""Dump whatever entries of the 194-slot area-entrance table are populated
in a PS1 RAM image.

The table at RAM 0x80075360 is NOT static disc data - it is zero-filled
(BSS) in the compiled executable and lazily populated at runtime, one
pointer per area actually visited that session. A fresh RAM dump only
yields entries for areas visited before the dump was taken; there is no
way to extract all 194 from a static binary. See
docs/SO2-MAP-LOCATION-CHECK.md's 2026-09-27 "static extraction attempted"
follow-up for the evidence.

Usage: python tools/so2_dump_area_table.py <ram_image.ram|.bin>
  (a flat 2 MiB PS1 RAM dump starting at 0x80000000, e.g. from
  tools/extract_so2_ram.py or an emulator's raw RAM export)
"""
import struct
import sys

TABLE = 0x80075360
COUNT = 194
RAM_BASE = 0x80000000


def dump(path):
    data = open(path, "rb").read()
    off = TABLE - RAM_BASE
    ptrs = struct.unpack_from(f"<{COUNT}I", data, off)
    found = 0
    for i, ptr in enumerate(ptrs):
        if ptr == 0:
            continue
        struct_off = ptr - RAM_BASE
        if not (0 <= struct_off < len(data) - 0x24):
            print(f"area {i}: pointer {ptr:#x} outside this RAM image, skipped")
            continue
        x, y, z, w = struct.unpack_from("<4i", data, struct_off)
        facing = struct.unpack_from("<h", data, struct_off + 0x20)[0]
        sub = struct.unpack_from("<H", data, struct_off + 0x22)[0]
        print(f"area {i}: X={x/4096:.2f} Y={y/4096:.2f} Z={z/4096:.2f} "
              f"facing={facing} sub={sub}  (4th word {w}, purpose unconfirmed)")
        found += 1
    print(f"\n{found}/{COUNT} area entries populated in this RAM image "
          "(only areas visited before the dump was taken)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    dump(sys.argv[1])
