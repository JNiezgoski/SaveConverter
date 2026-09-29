import sys
from pathlib import Path
sys.path.insert(0, '.')
from tools.so2_disc_code import archive_table, read_sectors, slz
import struct

disc2_path = Path('C:/CodeTesting/StarOcean2/disc/Star Ocean - The Second Story (USA) (Disc 2).bin')
with open(disc2_path, 'rb') as f:
    table = dict((idx, (lba, size)) for idx, lba, size in archive_table(f))
    lba, size = table[3892]
    b = read_sectors(f, lba, size)
    tag, offset = struct.unpack_from('<II', b, 4 + 8 * 1)
    script_data = slz(b[offset:])
    print(f'Script size: {len(script_data)}')
    
    # Look at the last 500 instructions or all scene load opcodes
    # Opcodes in SO2 script:
    # 0x01 = jump/branch?
    # 0x07 = call scene?
    # Let's inspect the last 1000 bytes of the script
    end_bytes = script_data[-1000:]
    for pos in range(len(script_data) - 400, len(script_data) - 4, 4):
        w = struct.unpack_from('<I', script_data, pos)[0]
        op = w >> 24
        sub = (w >> 16) & 0xFF
        imm = w & 0xFFFF
        print(f'{hex(pos)}: op={hex(op)} sub={hex(sub)} imm={hex(imm)} raw={hex(w)}')
