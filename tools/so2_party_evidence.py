"""Reproduce focused instruction listings and RAM anchors (requires capstone)."""
from pathlib import Path
import hashlib
import json
import struct
import capstone

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/so2-party'
SOURCES = [
    ('code-2576-lba-30736.bin', 0x8002f810, [
        (0x800331c8,0x80033218), (0x800337a4,0x80033878),
        (0x8003ba74,0x8003baa8), (0x8003bb2c,0x8003bb94),
        (0x80053000,0x80053158), (0x8006241c,0x80062478),
        (0x800637c8,0x80063808), (0x80069008,0x800692ec),
        (0x80069610,0x80069634), (0x8006a8ec,0x8006ab4c),
        (0x8007a20c,0x8007a37c), (0x8007ad28,0x8007ae54),
        (0x8007b1f0,0x8007b36c)]),
    ('code-2982-lba-36099.bin',0x8007e000,[(0x8007e440,0x8007e4a8)]),
    ('code-2985-lba-36109.bin',0x800d1b28,[(0x800d5c00,0x800d5cb8),
        (0x800d5cf4,0x800d5d38),(0x800dbf18,0x800dbfc0)]),
    ('code-2998-lba-36213.bin',0x8007e000,[(0x80081acc,0x80081b30),
        (0x80081c38,0x80081c74)]),
]


def main():
    OUT.mkdir(exist_ok=True)
    md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32 | capstone.CS_MODE_LITTLE_ENDIAN)
    listing, manifest = [], {'sources': [], 'ram': []}
    for name, base, ranges in SOURCES:
        data = (ROOT / 'artifacts/so2-fol/disc-code' / name).read_bytes()
        manifest['sources'].append({'file':name,'load':hex(base),'size':hex(len(data)),
                                    'sha256':hashlib.sha256(data).hexdigest()})
        listing.append(f'\n# {name}, load {base:08x}')
        for lo, hi in ranges:
            listing.append(f'\n# [{lo:08x}, {hi:08x})')
            listing.extend(f'{i.address:08x} {i.bytes.hex()} {i.mnemonic} {i.op_str}'
                           for i in md.disasm(data[lo-base:hi-base],lo))
    code = (ROOT / 'artifacts/so2-fol/disc-code/code-2576-lba-30736.bin').read_bytes()
    for name in ['ram.bin','SCUS-94422_resume.ram']:
        data = (ROOT / 'artifacts/so2-fol' / name).read_bytes()
        ptr = lambda a: struct.unpack_from('<I',data,a & 0x1fffff)[0]
        a,b = ptr(0x8007527c),ptr(0x80075280)
        item = {'file':name,'sha256':hashlib.sha256(data).hexdigest(),
                'state_pointer':hex(ptr(0x80075270)),'primary_pointer':hex(a),
                'secondary_pointer':hex(b),'slots':[], 'code_matches':{}}
        for lo,hi in [(0x80069008,0x800692ec),(0x8007a20c,0x8007b36c)]:
            item['code_matches'][f'{lo:08x}-{hi:08x}'] = data[lo&0x1fffff:hi&0x1fffff] == code[lo-0x8002f810:hi-0x8002f810]
        for slot in range(8):
            aa,bb = (a&0x1fffff)+96*slot,(b&0x1fffff)+208*slot
            item['slots'].append({'slot':slot,'signed_id':struct.unpack_from('<h',data,aa)[0],
                                  'class_byte':data[aa+3],
                                  'name':data[bb+0x24:bb+0x2c].split(b'\0')[0].decode('ascii')})
        manifest['ram'].append(item)
    (OUT / 'evidence.asm').write_text('\n'.join(listing)+'\n')
    (OUT / 'sources.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))


if __name__ == '__main__':
    main()
