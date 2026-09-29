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
print(f"code-2990 size: {len(b)} (0x{len(b):x})")

# Let's search for item ID tables across the entire file
# In Customization, each record seems to be:
# Success rate / difficulty? Output item, Mineral item, Input item(s)...
# Let's examine the structure of the customization records at 0x3f60..0x4500
pos = 0x3f60
while pos < len(b) - 8:
    # Let's see what is at pos
    words = [struct.unpack_from('<H', b, pos + 2*i)[0] for i in range(8)]
    # Look for known patterns
    pos += 16
