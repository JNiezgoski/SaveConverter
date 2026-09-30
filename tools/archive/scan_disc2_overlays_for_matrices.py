import sys
from pathlib import Path
sys.path.insert(0, '.')
from tools.so2_disc_code import archive_table, read_sectors, slz
import struct
import capstone

md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32 + capstone.CS_MODE_LITTLE_ENDIAN)

disc2_path = Path('C:/CodeTesting/StarOcean2/disc/Star Ocean - The Second Story (USA) (Disc 2).bin')

def scan_overlays():
    with open(disc2_path, 'rb') as f:
        table = dict((idx, (lba, size)) for idx, lba, size in archive_table(f))
        
        # Test all SLZ overlays between 2500 and 3250
        print("Scanning overlays 2500..3250 on Disc 2 for Matrix A/B and S=[80075270] accesses...")
        
        for arch in sorted(table.keys()):
            if not (2500 <= arch <= 3250):
                continue
            lba, size = table[arch]
            head = read_sectors(f, lba, 16)
            if head[:3] != b'SLZ' or head[3] not in (1, 2):
                continue
            b = read_sectors(f, lba, size)
            try:
                decomp = slz(b)
            except Exception:
                continue
                
            # Disassemble and search for:
            # 1. 0x5270 (S base)
            # 2. 0x58 / 0xe8
            # 3. 0x80065990 (Matrix A Get), 0x800658C0 (Matrix B Get), 0x80066E58 (Ranker)
            disasm_hits = []
            
            # Fast scan for 0x5270 in words
            # In MIPS: lui $reg, 0x8007; lw $reg2, 0x5270($reg)
            # or jal 0x80065990, etc.
            for pos in range(0, len(decomp) - 4, 4):
                w = struct.unpack_from('<I', decomp, pos)[0]
                if (w & 0xffff) == 0x5270:
                    op = w >> 26
                    # check if it is lw (35), lhu (37), addiu (9), sw (43)
                    if op in (35, 37, 9, 43):
                        disasm_hits.append(f"offset 0x5270 op={op} at pos {hex(pos)}")
                    
            if disasm_hits:
                print(f"Arch {arch} (len={hex(len(decomp))}): {len(disasm_hits)} hits:")
                for h in disasm_hits:
                    print(f"   {h}")

if __name__ == '__main__':
    scan_overlays()
