from pathlib import Path
import struct
import capstone

b = Path('artifacts/so2-specialty/disc-code/code-2990-lba-36156.bin').read_bytes()
BASE = 0x8007E000
md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32)

print("=== Disassembly of 0x800810A0..0x80081300 ===")
for ins in md.disasm(b[0x800810A0 - BASE : 0x80081300 - BASE], 0x800810A0):
    print(f"0x{ins.address:08X}: {ins.mnemonic:8s} {ins.op_str}")

print("\n=== Disassembly of 0x80081310..0x80081450 ===")
for ins in md.disasm(b[0x80081310 - BASE : 0x80081450 - BASE], 0x80081310):
    print(f"0x{ins.address:08X}: {ins.mnemonic:8s} {ins.op_str}")
