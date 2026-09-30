import json

with open('artifacts/disc2_script_scan.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

scenes = data['ending_scenes']
print(f'Total candidate scenes: {len(scenes)}')

target_words = ['ninay', 'eleanor', 'ronyx', 'ilia', 'admiral', 'swordsman', 'newspaper', 'chris', 'wedding', 'married', 'forever', 'together', 'farewell']
found = {}
for s in scenes:
    t = s['text'].lower()
    for w in target_words:
        if w in t:
            found.setdefault(w, []).append((s['arch'], s['midx'], s['text']))

for w, hits in found.items():
    print(f'Keyword "{w}": {len(hits)} hits')
    for a, m, txt in hits[:3]:
        print(f'  Arch {a} M{m}: {txt[:100]}')
