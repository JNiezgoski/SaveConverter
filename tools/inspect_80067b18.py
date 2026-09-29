with open('artifacts/so2-options-menu/resident.asm', 'r') as f:
    lines = [l.strip() for l in f]

for i, l in enumerate(lines):
    if '80067B18' in l:
        print("=== 80067B18 ===")
        for j in range(max(0, i-5), min(len(lines), i+30)):
            print(lines[j])
        break
