"""Comprehensive scan and milestone correlation for story flags part 2.

Scans container archives on Disc 1 and Disc 2 for script flag opcodes:
0x2103 (set/clear imm), 0x2203 (set/clear stack), 0x1D00 (test imm), 0x0E00 (read).
Focuses on the three target open ranges:
1. 0x19EB..0x19F4 (flags 24..109)
2. 0x1A28..0x1A3E (flags 512..695)
3. Bulk of Range B 0x1A49..0x1B58 (excluding already mapped 0x1A57..0x1A64 and 0x1B07..0x1B0C)
"""
from pathlib import Path
import struct
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
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
            # Clean up text
            txt_clean = ' '.join(txt.split())
            if txt_clean and not txt_clean.startswith('MONEY') and '999999999FOL' not in txt_clean and len(txt_clean) > 3:
                msgs.append(txt_clean)
    return msgs

def scan_disc(disc_path, disc_name):
    print(f"Scanning {disc_name} at {disc_path}...")
    results = {}
    with open(disc_path, 'rb') as f:
        table = dict((idx, (lba, size)) for idx, lba, size in archive_table(f))
        print(f"Found {len(table)} archives in table on {disc_name}.")
        
        # Determine archive range (3207..4033 or full range)
        arch_list = sorted([a for a in table.keys() if 3200 <= a <= 4500])
        print(f"Scanning {len(arch_list)} candidate scene archives...")
        
        for arch in arch_list:
            lba, size = table[arch]
            b = read_sectors(f, lba, size)
            if len(b) < 4:
                continue
            num_parts = struct.unpack_from('<I', b)[0]
            if num_parts < 2 or num_parts > 15:
                continue
                
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
            
            # Scan bytecode
            for pos in range(0, len(script_data) - 8, 4):
                w0 = struct.unpack_from('<I', script_data, pos)[0]
                opcode = w0 >> 24
                sub_or_mode = (w0 >> 16) & 0xFF
                fid = w0 & 0xFFFF
                
                # Check for global flag operations (bit 23 = 0, so bit 7 of sub_or_mode is 0)
                is_global = (w0 & 0x00800000) == 0
                if not is_global:
                    continue
                    
                op_type = None
                val = None
                
                # 0x2103xxxx
                if (w0 >> 16) == 0x2103:
                    val = struct.unpack_from('<I', script_data, pos + 4)[0]
                    op_type = 'SET' if val == 1 else ('CLEAR' if val == 0 else f'IMM_{val}')
                # 0x2203xxxx
                elif (w0 >> 16) == 0x2203:
                    op_type = 'STACK_SET_CLEAR'
                # 0x1D00xxxx
                elif (w0 >> 16) == 0x1D00:
                    val = struct.unpack_from('<I', script_data, pos + 4)[0]
                    op_type = f'TEST_{val}'
                # 0x0E00xxxx
                elif (w0 >> 16) == 0x0E00:
                    op_type = 'READ'
                    
                if op_type and fid < 2944:
                    if fid not in results:
                        results[fid] = []
                    results[fid].append({
                        'disc': disc_name,
                        'arch': arch,
                        'scene': scene_idx,
                        'pos': hex(pos),
                        'op': op_type,
                        'val': val,
                        'msgs': msgs
                    })
    return results

def main():
    disc1_path = 'C:/CodeTesting/StarOcean2/disc/Star Ocean - The Second Story (USA) (Disc 1).bin'
    disc2_path = 'C:/CodeTesting/StarOcean2/disc/Star Ocean - The Second Story (USA) (Disc 2).bin'
    
    d1_res = scan_disc(disc1_path, 'Disc 1')
    d2_res = scan_disc(disc2_path, 'Disc 2')
    
    # Merge results
    all_flags = {}
    for fid, hits in d1_res.items():
        all_flags.setdefault(fid, []).extend(hits)
    for fid, hits in d2_res.items():
        all_flags.setdefault(fid, []).extend(hits)
        
    print(f"\nTotal distinct global flags touched: {len(all_flags)}")
    
    # Analyze by target open ranges:
    # Open Range 1: 0x19EB..0x19F4 (flags 24..109)
    r1 = {k: v for k, v in all_flags.items() if 24 <= k <= 109}
    # Open Range 2: 0x1A28..0x1A3E (flags 512..695)
    r2 = {k: v for k, v in all_flags.items() if 512 <= k <= 695}
    # Open Range 3: Range B remainder (760..2943 excluding 890..999 and 2300..2342)
    # Specifically:
    # 760..889 (0x1A47..0x1A57)
    # 1000..2299 (0x1A65..0x1B06)
    # 2343..2943 (0x1B0D..0x1B58)
    r3_a = {k: v for k, v in all_flags.items() if 760 <= k < 890}
    r3_b = {k: v for k, v in all_flags.items() if 1000 <= k < 2300}
    r3_c = {k: v for k, v in all_flags.items() if 2343 <= k < 2944}
    
    print(f"Open Range 1 (flags 24..109, 0x19EB..0x19F4): {len(r1)} flags found")
    print(f"Open Range 2 (flags 512..695, 0x1A28..0x1A3E): {len(r2)} flags found")
    print(f"Open Range 3a (flags 760..889, 0x1A47..0x1A57): {len(r3_a)} flags found")
    print(f"Open Range 3b (flags 1000..2299, 0x1A65..0x1B06): {len(r3_b)} flags found")
    print(f"Open Range 3c (flags 2343..2943, 0x1B0D..0x1B58): {len(r3_c)} flags found")
    
    compact = {}
    for fid, hits in sorted(all_flags.items()):
        dec_byte = 0x19E8 + (fid >> 3)
        bit = fid & 7
        scenes = sorted(set(h['scene'] for h in hits))
        archs = sorted(set(h['arch'] for h in hits))
        ops = sorted(set(h['op'] for h in hits))
        discs = sorted(set(h['disc'] for h in hits))
        sample_msgs = []
        for h in hits:
            for m in h['msgs']:
                if m not in sample_msgs:
                    sample_msgs.append(m)
        compact[fid] = {
            'flag_id': fid,
            'hex_id': f'0x{fid:04X}',
            'decoded_byte': f'0x{dec_byte:04X}',
            'bit': bit,
            'num_hits': len(hits),
            'discs': discs,
            'scenes': scenes,
            'archs': archs,
            'ops': ops,
            'sample_dialogue': sample_msgs[:6]
        }

    summary_path = ROOT / 'artifacts/so2-script-flags/scan_part2.json'
    summary_path.write_text(json.dumps(compact, indent=2), encoding='utf-8')
    print(f"Wrote compact scan summary to {summary_path}")

    # Generate detailed report of open ranges
    report_path = ROOT / 'artifacts/so2-script-flags/part2_report.txt'
    with open(report_path, 'w', encoding='utf-8') as out:
        def write_range_analysis(title, min_id, max_id):
            out.write(f"\n{'='*70}\n")
            out.write(f"{title} (flags {min_id}..{max_id})\n")
            out.write(f"{'='*70}\n")
            sub = {k: v for k, v in compact.items() if min_id <= k <= max_id}
            by_byte = {}
            for fid, info in sub.items():
                b = int(info['decoded_byte'], 16)
                by_byte.setdefault(b, []).append(info)
            out.write(f"Total flags found: {len(sub)}, Bytes touched: {len(by_byte)}\n")
            for b in sorted(by_byte.keys()):
                flags = by_byte[b]
                flag_ids = [f['flag_id'] for f in flags]
                out.write(f"\nByte 0x{b:04X} ({len(flags)} flags touched: {flag_ids}):\n")
                for f in sorted(flags, key=lambda x: -x['num_hits']):
                    scenes = f['scenes']
                    archs = f['archs']
                    ops = f['ops']
                    discs = f['discs']
                    msgs = f['sample_dialogue']
                    out.write(f"  Flag {f['flag_id']:4d} ({f['hex_id']}) bit {f['bit']} | {f['num_hits']} hits | Discs: {discs} | Scenes: {scenes[:5]} (Archs: {archs[:5]}) | Ops: {ops}\n")
                    if msgs:
                        for m in msgs[:3]:
                            out.write(f"    Dialogue: \"{m[:120]}\"\n")
                    else:
                        out.write(f"    Dialogue: [None / non-dialogue]\n")

        write_range_analysis("Open Range 1: 0x19EB..0x19F4", 24, 109)
        write_range_analysis("Open Range 2: 0x1A28..0x1A3E", 512, 695)
        write_range_analysis("Open Range 3a: 0x1A47..0x1A56 (excluding 1A47..1A48)", 760, 889)
        write_range_analysis("Open Range 3b: 0x1A65..0x1B06", 1000, 2299)
        write_range_analysis("Open Range 3c: 0x1B0D..0x1B58", 2343, 2943)

    print(f"Wrote detailed report to {report_path}")


if __name__ == '__main__':
    main()
