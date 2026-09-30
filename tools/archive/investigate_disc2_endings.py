"""Investigation script for Disc 2 endings and item creation."""
from pathlib import Path
import struct
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.so2_disc_code import archive_table, read_sectors, slz

def categorize_disc2():
    disc2_path = Path("C:/CodeTesting/StarOcean2/disc/Star Ocean - The Second Story (USA) (Disc 2).bin")
    with open(disc2_path, "rb") as f:
        table = dict((idx, (lba, size)) for idx, lba, size in archive_table(f))
        print(f"Total entries in Disc 2 table: {len(table)}")
        
        slz_entries = []
        container_entries = []
        other_entries = []
        for idx in sorted(table.keys()):
            lba, size = table[idx]
            head = read_sectors(f, lba, 16)
            if head[:3] == b'SLZ':
                slz_entries.append((idx, lba, size, head[3]))
            elif len(head) >= 4 and 1 <= struct.unpack_from('<I', head)[0] <= 20:
                container_entries.append((idx, lba, size, struct.unpack_from('<I', head)[0]))
            else:
                other_entries.append((idx, lba, size))
        
        print(f"SLZ entries: {len(slz_entries)}")
        print(f"Container entries: {len(container_entries)}")
        print(f"Other entries: {len(other_entries)}")
        
        # Check distribution
        print("\nSLZ index ranges:")
        for r_start in range(0, 4600, 500):
            sub = [e[0] for e in slz_entries if r_start <= e[0] < r_start + 500]
            if sub:
                print(f"  {r_start}..{r_start+499}: {len(sub)} entries (min={min(sub)}, max={max(sub)})")
                
        print("\nContainer index ranges:")
        for r_start in range(0, 4600, 500):
            sub = [e[0] for e in container_entries if r_start <= e[0] < r_start + 500]
            if sub:
                print(f"  {r_start}..{r_start+499}: {len(sub)} entries (min={min(sub)}, max={max(sub)})")

if __name__ == "__main__":
    categorize_disc2()
