with open('artifacts/so2-options-menu/entry-2998.asm', 'r') as f:
    lines = [l.strip() for l in f]

for i, l in enumerate(lines):
    if '80081740' in l:
        print("=== entry-2998.asm 80081740 ===")
        for j in range(max(0, i-10), min(len(lines), i+15)):
            print(lines[j])
        break
