import sys
from pathlib import Path
sys.path.insert(0, '.')
from tools.so2_disc_code import archive_table, read_sectors, slz
from tools.find_disc2_endings import get_scene_messages
import struct

disc2_path = Path('C:/CodeTesting/StarOcean2/disc/Star Ocean - The Second Story (USA) (Disc 2).bin')
with open(disc2_path, 'rb') as f:
    table = dict((idx, (lba, size)) for idx, lba, size in archive_table(f))
    lba, size = table[3892]
    b = read_sectors(f, lba, size)
    tag, offset = struct.unpack_from('<II', b, 4 + 8 * 1)
    script_data = slz(b[offset:])
    msgs = get_scene_messages(script_data)
    print(f'Archive 3892 has {len(msgs)} messages:')
    for midx, msg in msgs:
        print(f'  M{midx}: {msg[:100]}')
