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

print("=== Analyzing ptr_meta for Groups 0..15 ===")
for g in range(16):
    ptr_meta = struct.unpack_from('<I', b, 0x4BE4 + 4*g)[0] - BASE
    # print 16 bytes
    chunk = b[ptr_meta:ptr_meta+16]
    hex_bytes = ' '.join(f'{x:02X}' for x in chunk)
    hwords = [struct.unpack_from('<H', chunk, 2*i)[0] for i in range(len(chunk)//2)]
    print(f"Group {g:2d} (0x{ptr_meta:04X}): {hex_bytes} | words: {[f'0x{w:04X}' for w in hwords]}")
