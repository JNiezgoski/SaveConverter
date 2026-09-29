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

# Where is item 0x0001 (Magic Canvas)?
print("Searching for references to Magic Canvas (0x0001) and Magical Clay in code-2990:")
for pos in range(0, len(b)-1, 2):
    w = struct.unpack_from('<H', b, pos)[0]
    if w == 1:
        # Check surrounding words
        context = [struct.unpack_from('<H', b, pos + 2*j)[0] for j in range(-4, 8) if 0 <= pos + 2*j < len(b)-1]
        c_names = [names.get(x, hex(x)) for x in context]
        # if any other art item is in context
        if any(x in range(2, 0x20) for x in context):
            print(f"  Offset 0x{pos:04X} (RAM 0x{BASE+pos:08X}): {c_names}")
