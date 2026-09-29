from pathlib import Path
import struct
import sys
sys.path.insert(0, '.')
from tools.so2_disc_code import archive_table, read_sectors, slz
from tools.so2_storyflags_part2 import decode_so2_text

disc1_path = Path('C:/CodeTesting/StarOcean2/disc/Star Ocean - The Second Story (USA) (Disc 1).bin')
with open(disc1_path, 'rb') as f:
    table = dict((idx, (lba, size)) for idx, lba, size in archive_table(f))
    
    # 1. Archive 3285: Flag 427 (0x1AB)
    lba, size = table[3285]
    b = read_sectors(f, lba, size)
    tag, offset = struct.unpack_from('<II', b, 4 + 8 * 1)
    sdata = slz(b[offset:])
    print('=== Archive 3285: Flag 427 (0x1AB) ===')
    for pos in range(0, len(sdata)-8, 4):
        w = struct.unpack_from('<I', sdata, pos)[0]
        if (w >> 16) == 0x2103 and (w & 0xFFFF) == 0x1AB:
            v = struct.unpack_from('<I', sdata, pos+4)[0]
            print(f'SET/CLEAR at 0x{pos:X}: val={v}')
            # print surrounding bytecode and dialogue
            for p in range(max(0, pos-48), min(len(sdata), pos+64), 4):
                w0 = struct.unpack_from('<I', sdata, p)[0]
                op = w0 >> 24
                imm = w0 & 0xFFFF
                extra = ""
                if op == 0x11: # text display?
                    extra = f"[MSG {imm}]"
                print(f'  0x{p:04X}: op=0x{op:02X} sub=0x{(w0>>16)&0xFF:02X} imm=0x{imm:04X} ({imm}) {extra}')

    # 2. Archive 3363: Flag 355 (0x163)
    lba, size = table[3363]
    b = read_sectors(f, lba, size)
    tag, offset = struct.unpack_from('<II', b, 4 + 8 * 1)
    sdata = slz(b[offset:])
    print('\n=== Archive 3363: Flag 355 (0x163) ===')
    for pos in range(0, len(sdata)-8, 4):
        w = struct.unpack_from('<I', sdata, pos)[0]
        if (w >> 16) == 0x2103 and (w & 0xFFFF) == 0x163:
            v = struct.unpack_from('<I', sdata, pos+4)[0]
            print(f'SET/CLEAR at 0x{pos:X}: val={v}')
            for p in range(max(0, pos-48), min(len(sdata), pos+64), 4):
                w0 = struct.unpack_from('<I', sdata, p)[0]
                op = w0 >> 24
                imm = w0 & 0xFFFF
                print(f'  0x{p:04X}: op=0x{op:02X} sub=0x{(w0>>16)&0xFF:02X} imm=0x{imm:04X} ({imm})')
