"""Scan Disc 2 containers for matrix opcodes, endings, and dialogue."""
from pathlib import Path
import struct
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.so2_disc_code import archive_table, read_sectors, slz

def decode_so2_text(raw_bytes):
    chars = []
    i = 0
    while i < len(raw_bytes) - 1:
        code = struct.unpack_from('<H', raw_bytes, i)[0]
        i += 2
        if code == 0:
            break
        if 0x01B6 <= code <= 0x01CF:
            chars.append(chr(code - 0x01B6 + ord('A')))
        elif 0x01D0 <= code <= 0x01E9:
            chars.append(chr(code - 0x01D0 + ord('a')))
        elif 0x01AA <= code <= 0x01B3:
            chars.append(chr(code - 0x01AA + ord('0')))
        elif code in (0x0185, 0x0285):
            chars.append(' ')
        elif code in (0x0183, 0x0283):
            chars.append('.')
        elif code in (0x0184, 0x0284):
            chars.append(',')
        elif code in (0x0186, 0x0286):
            chars.append("'")
        elif code in (0x0187, 0x0287):
            chars.append('?')
        elif code in (0x0188, 0x0288):
            chars.append('!')
        elif code == 0x01B5:
            chars.append('-')
        elif code in (0x0189, 0x018A, 0x0289, 0x028A):
            chars.append('"')
        elif 0x02B6 <= code <= 0x02CF:
            chars.append(chr(code - 0x02B6 + ord('A')))
        elif 0x02D0 <= code <= 0x02E9:
            chars.append(chr(code - 0x02D0 + ord('a')))
        elif code in (0x0113, 0x0200):
            chars.append(' ')
        elif (code >> 8) == 0x80 or (code & 0xFF00) == 0:
            pass
        else:
            chars.append('')
    return ''.join(chars)

def get_scene_messages(script_data):
    if len(script_data) < 16:
        return []
    word0 = struct.unpack_from('<I', script_data, 0)[0]
    num_msgs = struct.unpack_from('<I', script_data, 0x0C)[0]
    if num_msgs == 0 or num_msgs > 500 or word0 + 0x1C + num_msgs * 2 > len(script_data):
        return []
    msg_table = word0 + 0x1C
    text_base = msg_table + num_msgs * 2
    msgs = []
    for m in range(num_msgs):
        off = struct.unpack_from('<H', script_data, msg_table + m * 2)[0]
        if text_base + off < len(script_data):
            txt = decode_so2_text(script_data[text_base + off : text_base + off + 600]).strip()
            txt_clean = ' '.join(txt.split())
            if txt_clean and len(txt_clean) > 3 and not txt_clean.startswith('MONEY'):
                msgs.append((m, txt_clean))
    return msgs

def scan_disc2_containers():
    disc2_path = Path("C:/CodeTesting/StarOcean2/disc/Star Ocean - The Second Story (USA) (Disc 2).bin")
    with open(disc2_path, "rb") as f:
        table = dict((idx, (lba, size)) for idx, lba, size in archive_table(f))
        
        # Look at all container archives (3207..4400)
        arch_list = sorted([a for a in table.keys() if 3200 <= a <= 4400])
        print(f"Scanning {len(arch_list)} container archives on Disc 2...")
        
        matrix_hits = []
        interesting_scenes = []
        
        for arch in arch_list:
            lba, size = table[arch]
            b = read_sectors(f, lba, size)
            if len(b) < 8:
                continue
            num_parts = struct.unpack_from('<I', b)[0]
            if not (1 <= num_parts <= 20):
                continue
            
            # Read parts
            part_offsets = [struct.unpack_from('<I', b, 4 + 4*i)[0] for i in range(num_parts)]
            part_offsets.append(len(b))
            
            # Script is usually part 1 if num_parts >= 2
            for part_idx in range(num_parts):
                part_start = part_offsets[part_idx]
                part_end = part_offsets[part_idx+1]
                part_data = b[part_start:part_end]
                
                if len(part_data) > 16 and part_data[:3] == b'SLZ':
                    try:
                        decomp = slz(part_data)
                    except Exception:
                        continue
                else:
                    decomp = part_data
                    
                # Scan for matrix opcodes:
                # 0xFF10 (A adj imm), 0xFF90 (A adj stk), 0xFF11 (A get imm), 0xFF91 (A get stk)
                # 0xFF12 (B adj imm), 0xFF92 (B adj stk), 0xFF13 (B get imm), 0xFF93 (B get stk)
                # 0xFF76 (rank imm), 0xFFF6 (rank stk)
                for i in range(0, len(decomp) - 4, 4):
                    w = struct.unpack_from('>I', decomp, i)[0] # check big-endian word or little-endian?
                    # The instruction word in MIPS script is little-endian:
                    # In LE: byte 0 = opcode (0xFF), byte 1 = sub-opcode (0x10..0x13, 0x76, etc.), byte 2 = arg, byte 3 = arg
                    # So unpack as '<I'
                    w_le = struct.unpack_from('<I', decomp, i)[0]
                    op = (w_le >> 24) & 0xFF
                    subop = (w_le >> 16) & 0x7F
                    mode = (w_le >> 23) & 1
                    
                    if op == 0xFF:
                        if subop in (0x10, 0x11, 0x12, 0x13, 0x76):
                            matrix_hits.append({
                                'arch': arch,
                                'part': part_idx,
                                'offset': i,
                                'subop': hex(subop),
                                'mode': mode,
                                'raw': hex(w_le)
                            })
                            
                # Check for dialogue mentioning endings, Gabriel, Indalecio, etc.
                msgs = get_scene_messages(decomp)
                if msgs:
                    for midx, msg in msgs:
                        msg_low = msg.lower()
                        keywords = ['ending', 'indalecio', 'gabriel', 'fienal', 'phynal', 'calnus', 'expel', 'farewell', 'earth', 'teleport']
                        if any(k in msg_low for k in keywords):
                            interesting_scenes.append({
                                'arch': arch,
                                'part': part_idx,
                                'msg_idx': midx,
                                'text': msg[:120]
                            })
                            
        print(f"Matrix opcode hits found: {len(matrix_hits)}")
        for h in matrix_hits:
            print(f"  Arch {h['arch']} Part {h['part']} Off {hex(h['offset'])}: subop={h['subop']} mode={h['mode']} raw={h['raw']}")
            
        print(f"\nInteresting dialogue scenes found: {len(interesting_scenes)}")
        for s in interesting_scenes[:30]:
            print(f"  Arch {s['arch']} Part {s['part']} M{s['msg_idx']}: {s['text']}")

if __name__ == "__main__":
    scan_disc2_containers()
