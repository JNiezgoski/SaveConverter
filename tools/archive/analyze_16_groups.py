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

print("=== Analyzing 16 Cooking / Compounding Groups ===")
for g in range(16):
    ptr_good = struct.unpack_from('<I', b, 0x4B64 + 4*g)[0] - BASE
    ptr_bad  = struct.unpack_from('<I', b, 0x4BA4 + 4*g)[0] - BASE
    ptr_meta = struct.unpack_from('<I', b, 0x4BE4 + 4*g)[0] - BASE
    
    # Read until 0 or next pointer
    good_items = []
    pos = ptr_good
    while pos < len(b) - 1:
        w = struct.unpack_from('<H', b, pos)[0]
        if w == 0:
            break
        good_items.append((w, names.get(w, f'0x{w:04X}')))
        pos += 2
        
    bad_items = []
    pos = ptr_bad
    while pos < len(b) - 1:
        w = struct.unpack_from('<H', b, pos)[0]
        if w == 0:
            break
        bad_items.append((w, names.get(w, f'0x{w:04X}')))
        pos += 2

    print(f"\n--- Group {g:2d} (good=0x{ptr_good:04X}, bad=0x{ptr_bad:04X}, meta=0x{ptr_meta:04X}) ---")
    print(f"  Good outputs ({len(good_items)}): " + ", ".join(x[1] for x in good_items))
    print(f"  Bad outputs ({len(bad_items)}):  " + ", ".join(x[1] for x in bad_items))
