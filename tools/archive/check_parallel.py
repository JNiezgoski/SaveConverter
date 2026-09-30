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
chars = ["Claude", "Rena", "Celine", "Bowman", "Dias", "Precis", "Ashton", "Leon", "Opera", "Ernest", "Noel", "Chisato"]

for i in range(12):
    ptr_in = struct.unpack_from('<I', b, 0x4B04 + 4*i)[0] - BASE
    ptr_out = struct.unpack_from('<I', b, 0x4B34 + 4*i)[0] - BASE
    print(f"\n=== Char {i}: {chars[i]} (in=0x{ptr_in:04X}, out=0x{ptr_out:04X}) ===")
    j = 0
    while True:
        w_in = struct.unpack_from('<H', b, ptr_in + 2*j)[0]
        w_out = struct.unpack_from('<H', b, ptr_out + 2*j)[0]
        if w_in == 0:
            break
        print(f"  {names.get(w_in, f'0x{w_in:04X}')} -> {names.get(w_out, f'0x{w_out:04X}')} (0x{w_out:04X})")
        j += 1
