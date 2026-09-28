import json
from pathlib import Path

ROOT = Path("C:/CodeTesting/SaveConverter")
with open(ROOT / 'artifacts/so2-script-flags/scan_part2.json') as f:
    data = json.load(f)

def inspect_range(name, min_id, max_id):
    print(f"\n=======================================================")
    print(f"=== {name} (flags {min_id}..{max_id}) ===")
    print(f"=======================================================")
    sub = {int(k): v for k, v in data.items() if min_id <= int(k) <= max_id}
    by_byte = {}
    for fid, info in sub.items():
        b = int(info['decoded_byte'], 16)
        by_byte.setdefault(b, []).append(info)
    print(f"Total flags: {len(sub)}, Bytes touched: {len(by_byte)}")
    for b in sorted(by_byte.keys()):
        flags = by_byte[b]
        flag_ids = [f['flag_id'] for f in flags]
        print(f"\n  Byte 0x{b:04X} ({len(flags)} flags): {flag_ids}")
        for f in sorted(flags, key=lambda x: -x['num_hits']):
            scenes = f['scenes']
            archs = f['archs']
            msgs = f['sample_dialogue']
            txt = msgs[0][:100] if msgs else 'NO_DIALOGUE'
            print(f"    Flag {f['flag_id']:4d} ({f['hex_id']}) bit {f['bit']}: {f['num_hits']} hits, scenes {scenes[:4]}, ops {f['ops']}")
            if msgs:
                for m in msgs[:2]:
                    print(f"      Dialogue: \"{m[:100]}\"")
            else:
                print(f"      Dialogue: None")

inspect_range('Open Range 1 (flags 24..109, 0x19EB..0x19F4)', 24, 109)
inspect_range('Open Range 2 (flags 512..695, 0x1A28..0x1A3E)', 512, 695)
inspect_range('Open Range 3a (flags 760..889, 0x1A47..0x1A57)', 760, 889)
inspect_range('Open Range 3b (flags 1000..2299, 0x1A65..0x1B06)', 1000, 2299)
inspect_range('Open Range 3c (flags 2343..2943, 0x1B0D..0x1B58)', 2343, 2943)
