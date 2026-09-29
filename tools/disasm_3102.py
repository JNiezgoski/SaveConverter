import sys
from pathlib import Path
sys.path.insert(0, '.')
from tools.so2_disc_code import archive_table, read_sectors, slz
import struct
import capstone

md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32 + capstone.CS_MODE_LITTLE_ENDIAN)

disc2_path = Path('C:/CodeTesting/StarOcean2/disc/Star Ocean - The Second Story (USA) (Disc 2).bin')
with open(disc2_path, 'rb') as f:
    table = dict((idx, (lba, size)) for idx, lba, size in archive_table(f))
    lba, size = table[3102]
    b = read_sectors(f, lba, size)
    decomp = slz(b)
    print(f'Arch 3102 decomp size: {len(decomp)}')
    
    # Check what address it loads at (usually 8007e000 or similar)
    # Disassemble around pos 0x7af0..0x8600
    for target_pos in (0x7af8, 0x7bc8, 0x7c5c, 0x7db8, 0x8020, 0x8330, 0x85e4):
        print(f"\n--- Disassembly around {hex(target_pos)} ---")
        chunk = decomp[target_pos - 16 : target_pos + 64]
        for insn in md.disasm(chunk, target_pos - 16):
            print(f"  {hex(insn.address)}: {insn.mnemonic} {insn.op_str}")
