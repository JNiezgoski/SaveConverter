from pathlib import Path
import re

asm_path = Path('artifacts/so2-specialty/disc-code/code-3012-lba-36282.asm')
lines = asm_path.read_text(errors='ignore').splitlines()

# Search for any store to offset 0x64
print("Stores to 0x64:")
for i, l in enumerate(lines):
    if re.search(r's[whb]\s+\$\w+,\s*0x64\(', l):
        print(f"  Line {i+1}: {l.strip()}")
        # print context
        for ctx in lines[max(0, i-25):i+5]:
            print(f"    {ctx.strip()}")

