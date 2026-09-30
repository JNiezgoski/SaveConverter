from pathlib import Path
import struct
import re

# Load item names
names = {}
for line in open(r"C:\CodeTesting\StarOcean2\item_ids.txt", encoding="utf-8"):
    m = re.match(r"^([0-9A-F]{4}) (.+)$", line.strip())
    if m:
        code = int(m.group(1), 16)
        names[code - 0x5000] = m.group(2)

p = Path('artifacts/so2-specialty/disc-code/code-2990-lba-36156.bin')
b = p.read_bytes()
print(f"code-2990 size: {len(b)}")

print("\nHex dump of 0x3f60..0x4100 as u16:")
for pos in range(0x3f60, 0x4100, 16):
    row = [struct.unpack_from('<H', b, pos + 2*i)[0] for i in range(8)]
    row_str = ' '.join(f'{x:04x}' for x in row)
    name_str = ', '.join(names.get(x, f'unk({hex(x)})') for x in row if x != 0)
    print(f"{hex(pos)}: {row_str} | {name_str}")

