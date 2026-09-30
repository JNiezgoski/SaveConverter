"""Search all Disc 2 scene containers with tag==1 for matrix opcodes, endings, and dialogue."""
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

def main():
    disc2_path = Path("C:/CodeTesting/StarOcean2/disc/Star Ocean - The Second Story (USA) (Disc 2).bin")
    with open(disc2_path, "rb") as f:
        table = dict((idx, (lba, size)) for idx, lba, size in archive_table(f))
        
        print(f"Scanning all {len(table)} archives on Disc 2 for tag=1 script containers...")
        
        matrix_hits = []
        ending_scenes = []
        valid_containers = 0
        
        for arch in sorted(table.keys()):
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
                
            # Read full archive if not fully read
            if size > len(b):
                b = read_sectors(f, lba, size)
                
            try:
                script_data = slz(b[script_offset:])
            except Exception:
                continue
                
            valid_containers += 1
            msgs = get_scene_messages(script_data)
            
            # Check dialogue for ending / epilogue content
            for midx, msg in msgs:
                low = msg.lower()
                if any(w in low for w in ['indalecio', 'gabriel', 'fienal', 'phynal', 'calnus', 'earth', 'farewell', 'epilogue', 'wedding', 'married', 'credits']):
                    ending_scenes.append((arch, midx, msg))
            
            # Scan script bytecode for 0xFF10..0xFF13, 0xFF76, and any 0xFF sub-opcodes
            for pos in range(0, len(script_data) - 8, 4):
                w0 = struct.unpack_from('<I', script_data, pos)[0]
                opcode = w0 >> 24
                subop = (w0 >> 16) & 0x7F
                mode = (w0 >> 23) & 1
                imm = w0 & 0xFFFF
                
                if opcode == 0xFF:
                    if subop in (0x10, 0x11, 0x12, 0x13, 0x76):
                        w1 = struct.unpack_from('<I', script_data, pos + 4)[0]
                        matrix_hits.append({
                            'arch': arch,
                            'pos': hex(pos),
                            'subop': hex(subop),
                            'mode': mode,
                            'imm': imm,
                            'w0': hex(w0),
                            'w1': hex(w1),
                            'msgs': [m[1] for m in msgs[:3]]
                        })
                        
        print(f"Total valid script containers on Disc 2: {valid_containers}")
        print(f"Total matrix opcode occurrences in scripts: {len(matrix_hits)}")
        
        # Save results to json for detailed analysis
        out_data = {
            'matrix_hits': matrix_hits,
            'ending_scenes': [{'arch': a, 'midx': m, 'text': t} for a, m, t in ending_scenes]
        }
        with open('artifacts/disc2_script_scan.json', 'w', encoding='utf-8') as out_f:
            json.dump(out_data, out_f, indent=2)
            
        print(f"Ending dialogue scenes count: {len(ending_scenes)}")
        print("\nFirst 15 matrix hits:")
        for h in matrix_hits[:15]:
            print(f"  Arch {h['arch']} pos {h['pos']}: subop={h['subop']} mode={h['mode']} w0={h['w0']} w1={h['w1']}")
            if h['msgs']:
                print(f"    Context: {h['msgs'][0][:80]}")
                
        print("\nFirst 15 ending dialogue scenes:")
        for a, m, t in ending_scenes[:15]:
            print(f"  Arch {a} M{m}: {t[:100]}")

if __name__ == "__main__":
    main()
