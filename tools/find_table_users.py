from pathlib import Path
import struct
import capstone

b = Path('artifacts/so2-specialty/disc-code/code-2990-lba-36156.bin').read_bytes()
BASE = 0x8007E000
md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32)

print("Scanning code-2990 code section for table references:")
# The table of pointers is at file offset 0x4AD4, which is RAM 0x80082AD4.
# Let's search for references to 0x2AD4 or 0x8008 in lui/addiu/lw
for ins in md.disasm(b[:0x3F00], BASE):
    if any(k in ins.op_str for k in ['2ad4', '2ad0', '2b34', '2b04', '2b64', '8008']):
        print(f"0x{ins.address:08X}: {ins.mnemonic} {ins.op_str}")
