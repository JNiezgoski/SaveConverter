import json

with open('artifacts/disc2_script_scan.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

hits = data['matrix_hits']
custom_gets = []
for h in hits:
    pos_int = int(h['pos'], 16)
    # The shared routine is at 0x3d00..0x4500 in standard field scenes
    if h['subop'] in ('0x11', '0x13'):
        # Check if outside the 0x3d00..0x4500 template
        if not (0x3d00 <= pos_int <= 0x4500):
            custom_gets.append(h)

print(f"Total custom Matrix Get (0x11/0x13) occurrences: {len(custom_gets)}")
for h in custom_gets:
    print(f"  Arch {h['arch']} pos {h['pos']}: subop={h['subop']} mode={h['mode']} w0={h['w0']} w1={h['w1']}")
