from pathlib import Path
import re

names = {}
for line in open('C:/CodeTesting/StarOcean2/item_ids.txt', encoding='utf-8'):
    m = re.match(r'^([0-9A-F]{4}) (.+)$', line.strip())
    if m:
        names[int(m.group(1), 16) - 0x5000] = m.group(2)

print("Searching for ingredient names:")
for code, name in sorted(names.items()):
    if any(k in name.lower() for k in ['meat', 'grain', 'fruit', 'vegetable', 'seafood', 'fish', 'egg', 'dairy', 'canvas', 'clay']):
        print(f"  0x{code:04X} ({code:3d}): {name}")
