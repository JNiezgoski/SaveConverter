from pathlib import Path
import struct
import re

names = {}
for line in open(r"C:\CodeTesting\StarOcean2\item_ids.txt", encoding="utf-8"):
    m = re.match(r"^([0-9A-F]{4}) (.+)$", line.strip())
    if m:
        code = int(m.group(1), 16)
        names[code - 0x5000] = m.group(2)

p = Path('artifacts/so2-specialty/disc-code/code-2990-lba-36156.bin')
b = p.read_bytes()

# Let's inspect the exact layout around 0x3f90..0x4500
print("Detailed dump of 0x3f70..0x4200:")
pos = 0x3f74
# Let's trace the mineral list first
minerals = []
for i in range(18):
    m = struct.unpack_from('<H', b, pos + 2*i)[0]
    minerals.append(m)
print(f"Minerals table at 0x3f74 ({len(minerals)} minerals):")
for m in minerals:
    print(f"  {hex(m)}: {names.get(m, 'unknown')}")

pos = 0x3f74 + 18*2
print(f"\nAfter minerals, at {hex(pos)}:")
# Next is entries
while pos < 0x4500:
    # Read uint16s
    val = struct.unpack_from('<H', b, pos)[0]
    if val == 0:
        pos += 2
        continue
    # Let's see what structure this has
    print(f"Offset {hex(pos)}: {val} ({hex(val)}) -> {names.get(val, 'non-item')}")
    pos += 2
    if pos >= 0x4100:
        break
