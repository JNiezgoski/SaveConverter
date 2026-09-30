from pathlib import Path
import capstone

b = Path('artifacts/so2-specialty/disc-code/code-2990-lba-36156.bin').read_bytes()
BASE = 0x8007E000
md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32)

print("=== Disassembly of 0x80080E40..0x800810A0 ===")
for ins in md.disasm(b[0x80080E40 - BASE : 0x800810A0 - BASE], 0x80080E40):
    print(f"0x{ins.address:08X}: {ins.mnemonic:8s} {ins.op_str}")
