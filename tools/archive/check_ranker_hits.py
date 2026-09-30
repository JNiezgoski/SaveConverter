import json

with open('artifacts/disc2_script_scan.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

hits = data['matrix_hits']
ranker_hits = [h for h in hits if h['subop'] == '0x76']
print(f'Total 0xFF76 ranker hits: {len(ranker_hits)}')
for h in ranker_hits:
    print(f"  Arch {h['arch']} pos {h['pos']}: w0={h['w0']} w1={h['w1']}")
    if h['msgs']:
        print(f"     Msgs: {h['msgs'][:2]}")
