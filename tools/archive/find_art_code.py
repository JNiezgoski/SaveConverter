from pathlib import Path
import struct
import capstone

b = Path('artifacts/so2-specialty/disc-code/code-2990-lba-36156.bin').read_bytes()
BASE = 0x8007E000
md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32)

print("Searching for addiu/ori/li with 0x0001 (Magic Canvas) or 0x002B (Magical Clay):")
for ins in md.disasm(b[:0x3F00], BASE):
    if ins.mnemonic in ('addiu', 'ori', 'li') and ('0x2b' in ins.op_str or ' 1' in ins.op_str or '0x1' in ins.op_str):
        if any(r in ins.op_str for r in ['$a0', '$a1', '$a2', '$v0', '$v1']):
            print(f"0x{ins.address:08X}: {ins.mnemonic:8s} {ins.op_str}")
