import sys
from pathlib import Path
sys.path.insert(0, '.')
from tools.so2_disc_code import archive_table, read_sectors, slz
from tools.find_disc2_endings import get_scene_messages
import struct

disc2_path = Path('C:/CodeTesting/StarOcean2/disc/Star Ocean - The Second Story (USA) (Disc 2).bin')
with open(disc2_path, 'rb') as f:
    table = dict((idx, (lba, size)) for idx, lba, size in archive_table(f))
    lba, size = table[3788]
    b = read_sectors(f, lba, size)
    tag, offset = struct.unpack_from('<II', b, 4 + 8 * 1)
    script_data = slz(b[offset:])
    print(f'Archive 3788 script size: {len(script_data)}')
    
    msgs = get_scene_messages(script_data)
    print(f'Total messages: {len(msgs)}')
    for midx, msg in msgs[:25]:
        print(f'  M{midx}: {msg[:100]}')
    for midx, msg in msgs[80:110]:
        print(f'  M{midx}: {msg[:100]}')
        
    print("\n--- Bytecode around 0xad5c (Claude <-> Rena) ---")
    for pos in range(0xad50, 0xae00, 4):
        w0 = struct.unpack_from('<I', script_data, pos)[0]
        op = w0 >> 24
        sub = (w0 >> 16) & 0xFF
        imm = w0 & 0xFFFF
        print(f"  {hex(pos)}: op={hex(op)} sub={hex(sub)} imm={hex(imm)} ({imm}) raw={hex(w0)}")
