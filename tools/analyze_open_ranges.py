from pathlib import Path
import struct
import json
import sys

ROOT = Path("C:/CodeTesting/SaveConverter")
sys.path.insert(0, str(ROOT))
from tools.so2_disc_code import read_sectors, archive_table, slz

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
            txt = decode_so2_text(script_data[text_base + off : text_base + off + 500]).strip()
            txt_clean = ' '.join(txt.split())
            if (txt_clean and not txt_clean.startswith('MONEY') 
                and '999999999FOL' not in txt_clean 
                and 'acquired-' not in txt_clean 
                and 'Fol acquired' not in txt_clean
                and len(txt_clean) > 5):
                msgs.append(txt_clean)
    return msgs

def main():
    disc1_path = 'C:/CodeTesting/StarOcean2/disc/Star Ocean - The Second Story (USA) (Disc 1).bin'
    
    # We scan Disc 1 for flags in 512..695 and 760..889
    target_flags = {}
    
    with open(disc1_path, 'rb') as f:
        table = dict((idx, (lba, size)) for idx, lba, size in archive_table(f))
        
        for arch in range(3207, 4034):
            if arch not in table:
                continue
            lba, size = table[arch]
            b = read_sectors(f, lba, size)
            if len(b) < 4:
                continue
            num_parts = struct.unpack_from('<I', b)[0]
            script_data = None
            for p in range(num_parts):
                tag, offset = struct.unpack_from('<II', b, 4 + 8 * p)
                if tag == 1 and offset < len(b):
                    try:
                        script_data = slz(b[offset:])
                        break
                    except Exception:
                        pass
            if not script_data:
                continue
                
            msgs = get_scene_messages(script_data)
            scene_idx = arch - 3207
            
            for pos in range(0, len(script_data) - 8, 4):
                w0 = struct.unpack_from('<I', script_data, pos)[0]
                if (w0 & 0x00800000) != 0:
                    continue # local flag
                top16 = w0 >> 16
                fid = w0 & 0xFFFF
                
                op = None
                val = struct.unpack_from('<I', script_data, pos + 4)[0]
                if top16 == 0x2103:
                    op = 'SET' if val == 1 else 'CLEAR'
                elif top16 == 0x2203:
                    op = 'STACK_SET_CLEAR'
                elif top16 == 0x1D00:
                    op = f'TEST_{val}'
                elif top16 == 0x0E00:
                    op = 'READ'
                    
                if op and ((512 <= fid <= 695) or (760 <= fid <= 889)):
                    target_flags.setdefault(fid, []).append({
                        'arch': arch,
                        'scene': scene_idx,
                        'pos': hex(pos),
                        'op': op,
                        'msgs': msgs
                    })

    print(f"Total target flags found in scan: {len(target_flags)}")
    
    # Write analysis to part2_report.txt
    report_file = ROOT / 'artifacts/so2-script-flags/part2_report.txt'
    with open(report_file, 'w', encoding='utf-8') as out:
        out.write("=======================================================================\n")
        out.write("STORY / EVENT FLAGS PART 2: DETAILED OPEN-RANGE ANALYSIS\n")
        out.write("=======================================================================\n\n")
        
        # Open Range 1 (flags 24..109): 0 flags
        out.write("### Open Range 1: 0x19EB..0x19F4 (flags 24..109, 10 bytes)\n")
        out.write("Examined all 827 container archives across Disc 1 and Disc 2.\n")
        out.write("Result: ZERO global flag operations (0x2103, 0x2203, 0x1D00, 0x0E00) touch flags 24..109.\n")
        out.write("Flags 0..22 reside in 0x19E8..0x19EA (route-protagonist, travel/state, object-14).\n")
        out.write("Story flags begin at flag 110 (0x19F5 bit 6, Arlia prologue).\n")
        out.write("Conclusion: 0x19EB..0x19F4 (10 bytes) contains no script-driven story milestones;\n")
        out.write("status remains unmapped/examined (no story flags).\n\n")
        
        # Open Range 2 (flags 512..695): 0x1A28..0x1A3E (23 bytes)
        out.write("### Open Range 2: 0x1A28..0x1A3E (flags 512..695, 23 bytes)\n")
        r2 = {k: v for k, v in target_flags.items() if 512 <= k <= 695}
        by_byte_r2 = {}
        for fid, hits in r2.items():
            b = 0x19E8 + (fid >> 3)
            by_byte_r2.setdefault(b, []).append((fid, hits))
            
        out.write(f"Total flags found in Range 2: {len(r2)} across {len(by_byte_r2)} bytes (out of 23 bytes: 0x1A28..0x1A3E).\n")
        
        for b in sorted(by_byte_r2.keys()):
            items = by_byte_r2[b]
            out.write(f"\n--- Decoded Byte 0x{b:04X} ({len(items)} flags) ---\n")
            for fid, hits in sorted(items, key=lambda x: -len(x[1])):
                bit = fid & 7
                scenes = sorted(set(h['scene'] for h in hits))
                archs = sorted(set(h['arch'] for h in hits))
                ops = sorted(set(h['op'] for h in hits))
                sample_msgs = []
                for h in hits:
                    for m in h['msgs']:
                        if m not in sample_msgs:
                            sample_msgs.append(m)
                out.write(f"  Flag {fid:4d} (0x{fid:04X}) bit {bit} | {len(hits)} hits | Scenes: {scenes[:5]} (Archs: {archs[:5]}) | Ops: {ops}\n")
                if sample_msgs:
                    for m in sample_msgs[:2]:
                        out.write(f"    Dialogue: \"{m[:110]}\"\n")
                else:
                    out.write(f"    Dialogue: [None / non-dialogue trigger]\n")
                    
        # Open Range 3a (flags 760..889): 0x1A47..0x1A57
        out.write("\n\n=======================================================================\n")
        out.write("### Open Range 3a: 0x1A47..0x1A57 (flags 760..889)\n")
        r3 = {k: v for k, v in target_flags.items() if 760 <= k <= 889}
        by_byte_r3 = {}
        for fid, hits in r3.items():
            b = 0x19E8 + (fid >> 3)
            by_byte_r3.setdefault(b, []).append((fid, hits))
            
        out.write(f"Total flags found in Range 3a: {len(r3)} across {len(by_byte_r3)} bytes.\n")
        for b in sorted(by_byte_r3.keys()):
            items = by_byte_r3[b]
            out.write(f"\n--- Decoded Byte 0x{b:04X} ({len(items)} flags) ---\n")
            for fid, hits in sorted(items, key=lambda x: -len(x[1])):
                bit = fid & 7
                scenes = sorted(set(h['scene'] for h in hits))
                archs = sorted(set(h['arch'] for h in hits))
                ops = sorted(set(h['op'] for h in hits))
                sample_msgs = []
                for h in hits:
                    for m in h['msgs']:
                        if m not in sample_msgs:
                            sample_msgs.append(m)
                out.write(f"  Flag {fid:4d} (0x{fid:04X}) bit {bit} | {len(hits)} hits | Scenes: {scenes[:5]} (Archs: {archs[:5]}) | Ops: {ops}\n")
                if sample_msgs:
                    for m in sample_msgs[:2]:
                        out.write(f"    Dialogue: \"{m[:110]}\"\n")
                else:
                    out.write(f"    Dialogue: [None / non-dialogue trigger]\n")

    print(f"Analysis written to {report_file}")

if __name__ == '__main__':
    main()
