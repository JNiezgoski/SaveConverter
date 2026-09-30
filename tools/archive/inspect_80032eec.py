with open('artifacts/so2-options-menu/resident.asm', 'r') as f:
    lines = [l.strip() for l in f]

for i, l in enumerate(lines):
    if '80032EEC' in l:
        print("=== 80032EEC ===")
        for j in range(max(0, i-10), min(len(lines), i+15)):
            print(lines[j])
        break
