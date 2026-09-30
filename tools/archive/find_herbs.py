from pathlib import Path
import struct
import re

names = {}
for line in open('C:/CodeTesting/StarOcean2/item_ids.txt', encoding='utf-8'):
    m = re.match(r'^([0-9A-F]{4}) (.+)$', line.strip())
    if m:
        names[int(m.group(1), 16) - 0x5000] = m.group(2)

b2990 = Path('artifacts/so2-specialty/disc-code/code-2990-lba-36156.bin').read_bytes()
b3012 = Path('artifacts/so2-specialty/disc-code/code-3012-lba-36282.bin').read_bytes()

print("Searching for Mandrake (0x00DC) and herbs in code-2990:")
herbs = list(range(0x00DC, 0x00E2))
for pos in range(0, len(b2990)-1, 2):
    w = struct.unpack_from('<H', b2990, pos)[0]
    if w in herbs:
        print(f"  2990 +0x{pos:04X}: {names.get(w)} (0x{w:04X})")

print("\nSearching for Mandrake (0x00DC) and herbs in code-3012:")
for pos in range(0, len(b3012)-1, 2):
    w = struct.unpack_from('<H', b3012, pos)[0]
    if w in herbs:
        # check if multiple in a row
        row = [struct.unpack_from('<H', b3012, pos + 2*j)[0] for j in range(6) if pos+2*j < len(b3012)-1]
        c = sum(1 for x in row if x in herbs or x in range(0xE2, 0x115))
        if c >= 2:
            print(f"  3012 +0x{pos:04X}: {[names.get(x, hex(x)) for x in row]}")
