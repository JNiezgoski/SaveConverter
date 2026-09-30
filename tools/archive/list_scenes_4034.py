import sys
from pathlib import Path
sys.path.insert(0, '.')
from tools.so2_disc_code import archive_table, read_sectors, slz
from tools.find_disc2_endings import get_scene_messages
import struct

disc2_path = Path('C:/CodeTesting/StarOcean2/disc/Star Ocean - The Second Story (USA) (Disc 2).bin')
with open(disc2_path, 'rb') as f:
    table = dict((idx, (lba, size)) for idx, lba, size in archive_table(f))
    
    # Check archives 4034..4330
    for arch in range(4034, 4330):
        if arch not in table:
            continue
        lba, size = table[arch]
        b = read_sectors(f, lba, min(size, 4096))
        if len(b) < 12:
            continue
        num_parts = struct.unpack_from('<I', b)[0]
        if not (1 <= num_parts <= 20):
            continue
        script_offset = None
        for p in range(num_parts):
            tag, offset = struct.unpack_from('<II', b, 4 + 8 * p)
            if tag == 1 and offset < size:
                script_offset = offset
                break
        if script_offset is None:
            continue
        b = read_sectors(f, lba, size)
        try:
            script_data = slz(b[script_offset:])
            msgs = get_scene_messages(script_data)
            scene_msgs = [m[1] for m in msgs if not m[1].startswith('Fol acquired') and not m[1].startswith('Lavender acquired')]
            if scene_msgs:
                print(f"Arch {arch}: {len(scene_msgs)} scene msgs | {scene_msgs[0][:80]}")
            else:
                print(f"Arch {arch}: {len(msgs)} msgs (all standard)")
        except Exception as e:
            print(f"Arch {arch}: error {e}")
