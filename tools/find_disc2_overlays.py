import sys
from pathlib import Path
sys.path.insert(0, '.')
from tools.so2_disc_code import archive_table, read_sectors, slz
import struct

disc2_path = Path('C:/CodeTesting/StarOcean2/disc/Star Ocean - The Second Story (USA) (Disc 2).bin')
with open(disc2_path, 'rb') as f:
    table = dict((idx, (lba, size)) for idx, lba, size in archive_table(f))
    
    code_overlays = []
    for arch in range(2500, 3207):
        if arch not in table:
            continue
        lba, size = table[arch]
        head = read_sectors(f, lba, 16)
        if head[:3] == b'SLZ' and head[3] in (1, 2):
            b = read_sectors(f, lba, size)
            try:
                decomp = slz(b)
            except Exception:
                continue
            # Check if this decompressed data looks like MIPS code or has strings
            # Look for lui / addiu / jal or strings
            strings = []
            # Check ASCII strings >= 4 chars
            cur = []
            for byte in decomp:
                if 32 <= byte <= 126:
                    cur.append(chr(byte))
                else:
                    if len(cur) >= 6:
                        strings.append(''.join(cur))
                    cur = []
            if len(cur) >= 6:
                strings.append(''.join(cur))
                
            code_overlays.append({
                'arch': arch,
                'lba': lba,
                'raw_size': size,
                'decomp_size': len(decomp),
                'strings': strings[:10]
            })

print(f"Found {len(code_overlays)} SLZ overlays in 2500..3206 on Disc 2:")
for o in code_overlays:
    str_sample = ', '.join(f'"{s}"' for s in o['strings'][:4])
    print(f"  Entry {o['arch']}: decomp_size={hex(o['decomp_size'])} ({o['decomp_size']}) | strings: {str_sample}")
