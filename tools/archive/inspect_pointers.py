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

print("Pointers in code-2990 starting at 0x4AD4:")
pos = 0x4AD4
ptrs = []
while pos < len(b) - 3:
    val = struct.unpack_from('<I', b, pos)[0]
    if val == 0:
        break
    file_off = val - BASE
    ptrs.append((pos, val, file_off))
    pos += 4

print(f"Found {len(ptrs)} pointers.")
for p_pos, val, file_off in ptrs:
    # examine first 16 bytes at file_off
    sample = b[file_off:file_off+16]
    words = [struct.unpack_from('<H', sample, i*2)[0] for i in range(len(sample)//2)]
    w_names = [names.get(w, f'0x{w:04x}') for w in words]
    print(f"Ptr at 0x{p_pos:04X} -> 0x{val:08X} (file 0x{file_off:04X}): {w_names[:4]}")
