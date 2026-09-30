from pathlib import Path
import struct
import re

names = {}
for line in open('C:/CodeTesting/StarOcean2/item_ids.txt', encoding='utf-8'):
    m = re.match(r'^([0-9A-F]{4}) (.+)$', line.strip())
    if m:
        names[int(m.group(1), 16) - 0x5000] = m.group(2)

b = Path('artifacts/so2-specialty/disc-code/code-2990-lba-36156.bin').read_bytes()
print(f'code-2990 size: {len(b)} bytes (0x{len(b):X})')

# Search for art items (0x0001..0x0012)
art_items = set(range(1, 0x13))
print('\n=== Scanning for Art items (0x0001..0x0012) ===')
for i in range(0, len(b)-1, 2):
    w = struct.unpack_from('<H', b, i)[0]
    if w in art_items:
        neighbors = [struct.unpack_from('<H', b, i + 2*j)[0] for j in range(-2, 6) if 0 <= i + 2*j < len(b)-1]
        c = sum(1 for x in neighbors if x in art_items)
        if c >= 2:
            n_str = ' '.join(f'0x{x:04X}' for x in neighbors)
            print(f'  +0x{i:04X}: w=0x{w:04X} ({names.get(w, "?")}) neighbors=[{n_str}]')
