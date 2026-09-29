from pathlib import Path
import struct

# Mineral IDs:
# 51A3 Iron = 0x1A3 (419)
# 51A7 Orichalcum = 0x1A7 (423)
# 51A8 Meteorite = 0x1A8 (424)
# 51A9 Mithril = 0x1A9 (425)
# 51AA Damascus = 0x1AA (426)

minerals = [0x1a3, 0x1a7, 0x1a8, 0x1a9, 0x1aa]

root = Path('artifacts/so2-specialty')
for p in sorted(root.glob('**/*.bin')):
    b = p.read_bytes()
    # Check if multiple mineral IDs appear as halfwords close to each other
    hits = []
    for pos in range(0, len(b) - 2, 2):
        hw = struct.unpack_from('<H', b, pos)[0]
        if hw in minerals:
            hits.append((pos, hw))
            
    # Look for clusters of hits
    clusters = []
    for i in range(len(hits) - 2):
        if hits[i+2][0] - hits[i][0] <= 32:
            clusters.append((hits[i][0], [h[1] for h in hits[i:i+3]]))
            
    if clusters:
        print(f"File {p.name} has {len(clusters)} mineral clusters:")
        for c in clusters[:5]:
            print(f"   pos {hex(c[0])}: {[hex(x) for x in c[1]]}")
