"""Bounded original-instruction chunk-1 checks using synthetic RAM; no card writes."""
from pathlib import Path
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.so2_party_mips import Machine


def main():
    m = Machine((ROOT/'artifacts/so2-options-menu/entry-2576.bin').read_bytes())
    S, D = 0x80100000, 0x80101000
    put32 = lambda a, v: m.put(a, struct.pack('<I', v & 0xffffffff))
    read = lambda a, n: bytes(m.memory[a & 0x1fffff:(a & 0x1fffff)+n])
    put32(0x80075270, S)

    def block(start, stop, registers):
        def enter(machine, r):
            for i, value in registers.items():
                r[i] = value
            r[31] = start
        def leave(machine, r):
            r[31] = 0x800ff000
        m.run(0x800ff100, hooks={0x800ff100: enter, stop: leave})

    # Execute both script adjustment arms after operand decoding, through their
    # actual shared store/delay slot. Operand decoding and dispatch are not tested.
    trials = 0
    for base, start in ((0x58, 0x8006590c), (0xe8, 0x80065838)):
        for row in range(12):
            for col in range(12):
                for old, delta in ((0,-1),(0,1),(7,-20),(7,3),(15,1),(15,-1)):
                    expected = bytearray([0xa5]*0x1a0)
                    index = base+12*row+col
                    expected[index] = old
                    m.put(S, expected)
                    for i, value in enumerate((row,col,delta)):
                        put32(0x1f800000+4*i, value)
                    block(start, 0x80067614, {19:0x1f800000})
                    expected[index] = min(15,max(0,old+delta))
                    assert read(S,0x1a0) == expected
                    trials += 1

    overlay = (ROOT/'artifacts/so2-options-menu/entry-2998.bin').read_bytes()
    m.put(0x8007e000, overlay)
    m.executable_ranges.append((0x8007e000,0x8007e000+len(overlay)))
    pattern = bytes((i*37+11)&255 for i in range(0x1a0))
    for direction in (0,1):
        m.put(S, pattern if direction == 0 else bytes([0xcc])*0x1a0)
        m.put(D, pattern if direction == 1 else bytes([0xdd])*0x1a0)
        m.put(S+0x1a0,b'LIVE-END')
        m.put(D+0x1a0,b'DEST-END')
        block(0x80081acc,0x80081af4,{20:D,21:direction,22:0})
        assert read(S,0x1a0) == read(D,0x1a0) == pattern
        assert read(S+0x1a0,8) == b'LIVE-END'
        assert read(D+0x1a0,8) == b'DEST-END'
    result = dict(status='Verified (executed), synthetic RAM; not in-game',
                  matrix_adjustments=trials, matrix_cells=288,
                  serializer_directions=2, serializer_bytes=416,
                  limits='Operand decoding/VM dispatch excluded; memcpy is a host hook; immediate loads, branch delay slots modeled.')
    out = ROOT/'artifacts/so2-chunk1'
    out.mkdir(exist_ok=True,parents=True)
    (out/'execution.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
