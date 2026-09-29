from pathlib import Path
import struct
import re

names = {}
for line in open('C:/CodeTesting/StarOcean2/item_ids.txt', encoding='utf-8'):
    m = re.match(r'^([0-9A-F]{4}) (.+)$', line.strip())
    if m:
        names[int(m.group(1), 16) - 0x5000] = m.group(2)

b = Path('artifacts/so2-specialty/disc-code/code-2990-lba-36156.bin').read_bytes()
BASE = 0x8007E000
chars = ["Claude", "Rena", "Celine", "Bowman", "Dias", "Precis", "Ashton", "Leon", "Opera", "Ernest", "Noel", "Chisato"]

print("=== Analyzing Table 1 (0x4AD4..0x4B04) ===")
for i in range(12):
    ptr = struct.unpack_from('<I', b, 0x4AD4 + 4*i)[0] - BASE
    # Read until next pointer or 0
    words = []
    p = ptr
    for _ in range(20):
        w = struct.unpack_from('<H', b, p)[0]
        words.append(w)
        p += 2
        if w == 0:
            break
    print(f"\nChar {i:2d} ({chars[i]}): Ptr 0x{ptr:04X}:")
    for idx, w in enumerate(words):
        print(f"  [{idx:2d}] 0x{w:04X} ({w:5d}) -> {names.get(w, f'0x{w:04X}')}")
