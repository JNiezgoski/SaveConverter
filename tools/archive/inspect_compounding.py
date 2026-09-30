from pathlib import Path
import struct
import re

names = {}
for line in open('C:/CodeTesting/StarOcean2/item_ids.txt', encoding='utf-8'):
    m = re.match(r'^([0-9A-F]{4}) (.+)$', line.strip())
    if m:
        names[int(m.group(1), 16) - 0x5000] = m.group(2)

b2990 = Path('artifacts/so2-specialty/disc-code/code-2990-lba-36156.bin').read_bytes()

print("=== Section around 0x09E0..0x0A60 ===")
for p in range(0x09E0, 0x0A60, 2):
    w = struct.unpack_from('<H', b2990, p)[0]
    print(f"  0x{p:04X}: 0x{w:04X} ({w:5d}) -> {names.get(w, 'unk')}")

print("\n=== Section around 0x1EE0..0x1F60 ===")
for p in range(0x1EE0, 0x1F60, 2):
    w = struct.unpack_from('<H', b2990, p)[0]
    print(f"  0x{p:04X}: 0x{w:04X} ({w:5d}) -> {names.get(w, 'unk')}")
