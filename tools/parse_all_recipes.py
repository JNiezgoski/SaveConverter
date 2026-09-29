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

# Let's search for all pointers or headers in code-2990
# Let's inspect 0x3000 to len(b)
print("Scanning code-2990 data sections:")
# Character order:
chars = ["Claude", "Rena", "Celine", "Bowman", "Dias", "Precis", "Ashton", "Leon", "Opera", "Ernest", "Noel", "Chisato"]

# Let's decode customization recipes starting at 0x3fbc
pos = 0x3fbc
recipes = []
while pos < len(b) - 8:
    prob = struct.unpack_from('<H', b, pos)[0]
    out_item = struct.unpack_from('<H', b, pos+2)[0]
    mat_item = struct.unpack_from('<H', b, pos+4)[0]
    if out_item in names and mat_item in names and 1 <= prob <= 100:
        # Read inputs until 0
        inputs = []
        cur = pos + 6
        while cur < len(b) - 2:
            in_item = struct.unpack_from('<H', b, cur)[0]
            if in_item == 0:
                cur += 2
                break
            if in_item in names:
                inputs.append(in_item)
                cur += 2
            else:
                break
        if inputs:
            recipes.append({
                'pos': hex(pos),
                'prob': prob,
                'out_id': out_item,
                'out_name': names[out_item],
                'mat_id': mat_item,
                'mat_name': names[mat_item],
                'inputs': [(i, names.get(i, f'unk_{i}')) for i in inputs]
            })
            pos = cur
            continue
    pos += 2

print(f"Decoded {len(recipes)} weapon customization recipes in code-2990!")
for r in recipes[:30]:
    in_names = ', '.join(x[1] for x in r['inputs'][:3])
    if len(r['inputs']) > 3:
        in_names += f" (+{len(r['inputs'])-3} more)"
    print(f"  {r['pos']}: [{in_names}] + {r['mat_name']} -> {r['out_name']} ({r['prob']}%)")

print("\nLast 15 recipes:")
for r in recipes[-15:]:
    in_names = ', '.join(x[1] for x in r['inputs'][:3])
    if len(r['inputs']) > 3:
        in_names += f" (+{len(r['inputs'])-3} more)"
    print(f"  {r['pos']}: [{in_names}] + {r['mat_name']} -> {r['out_name']} ({r['prob']}%)")
