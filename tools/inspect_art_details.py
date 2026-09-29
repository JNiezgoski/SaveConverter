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

print("=== Analyzing Art tables for each character ===")
art_ptrs = [struct.unpack_from('<I', b, 0x4B34 + 4*i)[0] - BASE for i in range(12)]

for c_idx, off in enumerate(art_ptrs):
    next_off = art_ptrs[c_idx + 1] if c_idx < 11 else 0x485C
    chunk = b[off:next_off]
    words = [struct.unpack_from('<H', chunk, 2*i)[0] for i in range(len(chunk)//2)]
    print(f"\nCharacter {c_idx} ({chars[c_idx]}) at offset 0x{off:04X} ({len(words)} words):")
    # print raw words and item names
    for i, w in enumerate(words):
        in_art = w in range(1, 0x13)
        name = names.get(w, f"0x{w:04X}")
        print(f"  [{i:2d}] 0x{w:04X} ({w:5d}) -> {name}")
