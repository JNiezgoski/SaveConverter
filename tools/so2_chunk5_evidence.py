"""Bounded real-instruction checks for chunk 5; no card or emulator-state writes.

Requires already-extracted artifacts/so2-options-menu/entry-2576.bin.
The Machine checks its SHA-256. Synthetic RAM distinguishes live F, G and
resource E; only resource lookup is hooked in the snapshot test.
"""
from pathlib import Path
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.so2_party_mips import Machine


def main():
    m = Machine((ROOT/'artifacts/so2-options-menu/entry-2576.bin').read_bytes())
    F, G, E, B = 0x80100000, 0x80101000, 0x80102000, 0x80103000
    put32 = lambda a,v: m.put(a,struct.pack('<I',v))
    read = lambda a,n: bytes(m.memory[a&0x1fffff:(a&0x1fffff)+n])
    put32(0x80075710,F)
    put32(0x80075704,G)
    m.put(F,bytes([0x35])*0x440)
    m.put(G,bytes([0x97])*0x170)
    m.put(E,bytes([0xCD])*0x440)
    def resource(machine,r):
        assert r[5]==0xe
        r[2]=E
    m.run(0x80055FC8,hooks={0x80012108:resource})
    assert read(E,0x2a0)==read(F,0x2a0)
    assert read(E+0x2a0,0x170)==read(G,0x170)
    assert read(E+0x410,0x30)==bytes([0xCD])*0x30
    # Execute initializer pointer assignments with a distinguishable resource-9 address.
    def resource9(machine,r):
        assert r[5]==9
        r[2]=B
    m.run(0x80049460,hooks={0x80012108:resource9})
    assert read(0x80075710,4)==struct.pack('<I',B+0x220)
    assert read(0x80075704,4)==struct.pack('<I',B+0x8c0)
    put32(0x80075710,F)
    put32(0x80075704,G)
    m.put(G,bytes(0x170))
    for flag in range(0x170*8):
        m.run(0x80055EFC,(flag,))
        assert m.run(0x80055ECC,(flag,))==1
        expected=bytearray(0x170); expected[flag//8]=1<<(flag%8)
        assert read(G,0x170)==expected
        m.run(0x80055F38,(flag,))
        assert m.run(0x80055ECC,(flag,))==0
        assert read(G,0x170)==bytes(0x170)
    for slot in range(12):
        assert m.run(0x80055F78,(slot,))==F+0x28+20*slot
        name=bytes([0x61+slot])*7+b'\0'
        m.put(F+0x28+20*slot,name)
        assert m.run(0x8005CB90,(0,slot,E))==7
        assert read(E,8)==name
    report=dict(status='Verified (executed), synthetic RAM; not in-game',
        snapshot=dict(entry='80055FC8',prefix_bytes=0x2a0,global_bytes=0x170,
                      untouched_tail_bytes=0x30,hook='80012108 resource lookup only'),
        pointer_initializer=dict(entry='80049460',F='resource9+220',G='resource9+8C0',
                                 hook='80012108 resource lookup only'),
        flag_roundtrips=0x170*8,name_slots_checked=12,
        limits='Machine implements branch delay slots but immediate loads; no whole-game execution.')
    out=ROOT/'artifacts/so2-chunk5'
    out.mkdir(parents=True,exist_ok=True)
    (out/'execution.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
