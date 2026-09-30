from pathlib import Path
import struct
import re

names = {}
for line in open('C:/CodeTesting/StarOcean2/item_ids.txt', encoding='utf-8'):
    m = re.match(r'^([0-9A-F]{4}) (.+)$', line.strip())
    if m:
        names[int(m.group(1), 16) - 0x5000] = m.group(2)

b = Path('artifacts/so2-specialty/disc-code/code-2990-lba-36156.bin').read_bytes()

print("=== Section 1: 0x3F60..0x3FC0 ===")
for pos in range(0x3F60, 0x3FC0, 2):
    w = struct.unpack_from('<H', b, pos)[0]
    print(f"  0x{pos:04X}: 0x{w:04X} ({w:5d}) -> {names.get(w, 'unk')}")

print("\n=== Section 2: 0x4A50..0x4AD4 ===")
for pos in range(0x4A50, 0x4AD4, 2):
    w = struct.unpack_from('<H', b, pos)[0]
    print(f"  0x{pos:04X}: 0x{w:04X} ({w:5d}) -> {names.get(w, 'unk')}")
