import sys
from pathlib import Path
sys.path.insert(0, '.')
from tools.so2_disc_code import archive_table, read_sectors, slz
from tools.search_disc2_endings import encode_16bit
import struct

disc2_path = Path('C:/CodeTesting/StarOcean2/disc/Star Ocean - The Second Story (USA) (Disc 2).bin')

def main():
    test_words = ['Gyoro', 'Ururun', 'Ninay', 'Eleanor', 'Ronyx', 'Ilia', 'heraldic', 'married', 'wedding', 'ending', 'epilogue']
    encoded_words = [(w, encode_16bit(w)) for w in test_words]
    ascii_words = [(w, w.encode('ascii')) for w in test_words]
    
    print("Searching all decompressed SLZ archives and containers on Disc 2...")
    
    with open(disc2_path, 'rb') as f:
        table = dict((idx, (lba, size)) for idx, lba, size in archive_table(f))
        
        found = {}
        
        # 1. Test all SLZ archives
        for arch in sorted(table.keys()):
            lba, size = table[arch]
            head = read_sectors(f, lba, 16)
            
            decomp_list = []
            if head[:3] == b'SLZ' and head[3] in (1, 2):
                try:
                    decomp_list.append(('slz', slz(read_sectors(f, lba, size))))
                except Exception:
                    pass
            elif len(head) >= 12:
                num_parts = struct.unpack_from('<I', head)[0]
                if 1 <= num_parts <= 20:
                    b = read_sectors(f, lba, size)
                    for p in range(num_parts):
                        tag, off = struct.unpack_from('<II', b, 4 + 8*p)
                        if off < len(b) and b[off:off+3] == b'SLZ' and b[off+3] in (1, 2):
                            try:
                                decomp_list.append((f'part_{p}_tag_{tag}', slz(b[off:])))
                            except Exception:
                                pass
                                
            for src, data in decomp_list:
                for w, enc in encoded_words:
                    if enc in data:
                        found.setdefault(arch, []).append((src, '16-bit', w))
                for w, asc in ascii_words:
                    if asc in data:
                        found.setdefault(arch, []).append((src, 'ascii', w))
                        
    print(f"Total matching archives: {len(found)}")
    for arch in sorted(found.keys()):
        hits = found[arch]
        summary = ', '.join(f"{src}:{k}:{w}" for src, k, w in hits)
        print(f"Arch {arch}: {summary}")

if __name__ == '__main__':
    main()
