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

print(f"Archive 3788 script size: {len(script_data)}")

# Let's write a mini bytecode printer that understands common SO2 script opcodes:
# 0x00: nop or push?
# 0x01: jump
# 0x0B: push imm
# 0x0E: read flag
# 0x13: branch?
# 0x15: jump
# 0x16: beqz / bnez
# 0x17: call
# 0x19: push local
# 0x1A: ret
# 0x1D: test flag
# 0x21: set flag / var
# 0x22: store local
# 0x3E: compare?
# 0x40: compare?
# 0x42: compare?
# 0xFF: custom sub-dispatch (0x10=A adj, 0x11=A get, 0x12=B adj, 0x13=B get, 0x76=rank)

pos = 0xad50
while pos < 0xaf00:
    w0 = struct.unpack_from('<I', script_data, pos)[0]
    op = w0 >> 24
    sub = (w0 >> 16) & 0x7F
    mode = (w0 >> 23) & 1
    imm = w0 & 0xFFFF
    
    extra = ""
    if op == 0xFF:
        sub_name = {0x10: 'Matrix_A_Adj', 0x11: 'Matrix_A_Get', 0x12: 'Matrix_B_Adj', 0x13: 'Matrix_B_Get', 0x76: 'Affinity_Rank'}.get(sub, hex(sub))
        extra = f"[{sub_name} char1={imm}]"
    elif op == 0x21:
        extra = f"[SET_VAR/FLAG var={hex(imm)} mode={sub}]"
    elif op in (0x15, 0x16):
        extra = f"[JUMP/BRANCH target_pc={hex(imm*4)}]"
    elif op == 0x0B:
        extra = f"[PUSH {imm}]"
        
    print(f"{hex(pos)}: op={hex(op)} sub={hex(sub)} mode={mode} imm={hex(imm)} ({imm}) {extra}")
    pos += 4
