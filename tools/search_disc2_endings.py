import sys
from pathlib import Path
sys.path.insert(0, '.')
from tools.so2_disc_code import archive_table, read_sectors

def encode_16bit(text):
    # Encode ASCII string to SO2 16-bit character codes
    res = bytearray()
    for c in text:
        if 'A' <= c <= 'Z':
            res.extend(struct.pack('<H', ord(c) - ord('A') + 0x01B6))
        elif 'a' <= c <= 'z':
            res.extend(struct.pack('<H', ord(c) - ord('a') + 0x01D0))
        elif '0' <= c <= '9':
            res.extend(struct.pack('<H', ord(c) - ord('0') + 0x01AA))
        elif c == ' ':
            res.extend(struct.pack('<H', 0x0285))
        elif c == '.':
            res.extend(struct.pack('<H', 0x0283))
        elif c == ',':
            res.extend(struct.pack('<H', 0x0284))
        elif c == "'":
            res.extend(struct.pack('<H', 0x0286))
        elif c == '-':
            res.extend(struct.pack('<H', 0x01B5))
    return bytes(res)

import struct

disc2_path = Path('C:/CodeTesting/StarOcean2/disc/Star Ocean - The Second Story (USA) (Disc 2).bin')

def main():
    test_words = ['Gyoro', 'Ururun', 'Ninay', 'Eleanor', 'Ronyx', 'Ilia', 'heraldic', 'married', 'wedding']
    encoded_words = [(w, encode_16bit(w)) for w in test_words]
    ascii_words = [(w, w.encode('ascii')) for w in test_words]
    
    print("Searching Disc 2 archives for 16-bit and ASCII ending keywords...")
    
    with open(disc2_path, 'rb') as f:
        table = dict((idx, (lba, size)) for idx, lba, size in archive_table(f))
        
        found = []
        for arch, (lba, size) in sorted(table.items()):
            # Read first 1MB or full size
            data = read_sectors(f, lba, size)
            
            for w, enc in encoded_words:
                if enc in data:
                    found.append((arch, '16-bit', w, lba, size))
            for w, asc in ascii_words:
                if asc in data:
                    found.append((arch, 'ascii', w, lba, size))
                    
    print(f"Total occurrences: {len(found)}")
    by_arch = {}
    for arch, kind, w, lba, size in found:
        by_arch.setdefault(arch, []).append((kind, w, size))
        
    for arch, items in sorted(by_arch.items()):
        print(f"Arch {arch} (size {items[0][2]}): {', '.join(f'{k}:{w}' for k, w, _ in items)}")

if __name__ == '__main__':
    main()
