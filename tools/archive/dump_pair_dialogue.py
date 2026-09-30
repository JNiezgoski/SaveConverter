from pathlib import Path
import struct
import sys
sys.path.insert(0, '.')
from tools.so2_disc_code import archive_table, read_sectors, slz
from tools.so2_storyflags_part2 import decode_so2_text

disc1_path = Path('C:/CodeTesting/StarOcean2/disc/Star Ocean - The Second Story (USA) (Disc 1).bin')
with open(disc1_path, 'rb') as f:
    table = dict((idx, (lba, size)) for idx, lba, size in archive_table(f))
    
    for arch in (3285, 3363):
        lba, size = table[arch]
        b = read_sectors(f, lba, size)
        tag, offset = struct.unpack_from('<II', b, 4 + 8 * 1)
        script_data = slz(b[offset:])
        
        word0 = struct.unpack_from('<I', script_data, 0)[0]
        num_msgs = struct.unpack_from('<I', script_data, 0x0C)[0]
        msg_table = word0 + 0x1C
        text_base = msg_table + num_msgs * 2
        print(f"\n=== Archive {arch} (Scene {arch-3207}) messages ({num_msgs} total) ===")
        for m in range(min(num_msgs, 30)):
            off = struct.unpack_from('<H', script_data, msg_table + m * 2)[0]
            if text_base + off < len(script_data):
                txt = decode_so2_text(script_data[text_base + off : text_base + off + 500]).strip()
                txt_clean = ' '.join(txt.split())
                if len(txt_clean) > 5 and '999999999' not in txt_clean:
                    print(f"  M{m}: {txt_clean[:90]}")
