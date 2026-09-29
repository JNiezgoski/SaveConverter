from pathlib import Path
import re

names = {}
for line in open('C:/CodeTesting/StarOcean2/item_ids.txt', encoding='utf-8'):
    m = re.match(r'^([0-9A-F]{4}) (.+)$', line.strip())
    if m:
        names[int(m.group(1), 16) - 0x5000] = m.group(2)

print("Items 0x30E..0x316:")
for i in range(0x30E, 0x317):
    print(f"  0x{i:04X} ({i:3d}): {names.get(i, 'unk')}")
