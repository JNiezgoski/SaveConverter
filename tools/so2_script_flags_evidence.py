"""Bounded VM flag dispatch checks and extraction of four existing script artifacts.

No disc/card writes. Uses the same hashed resident image and Machine as chunk 5.
Hooks only inject entry registers and stop at the VM loop boundary; original
fetch, dispatch tables, operand decoding and bitmap instructions are executed.
"""
from pathlib import Path
import hashlib
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.so2_party_mips import Machine
from tools.so2_disc_code import slz


def main():
    m = Machine((ROOT/'artifacts/so2-options-menu/entry-2576.bin').read_bytes())
    C, G, W, P, T, L = (0x80100000, 0x80102000, 0x80103000,
                         0x80104000, 0x80105000, 0x80106000)
    put = lambda a, v: m.put(a, struct.pack('<I', v & 0xffffffff))
    read = lambda a, n: bytes(m.memory[a & 0x1fffff:(a & 0x1fffff)+n])
    word = lambda a: int.from_bytes(read(a, 4), 'little')
    put(0x80075704, G)
    put(0x80075708, W)
    trials = []

    def dispatch(words, stack=(), computed=0, width=0):
        m.put(P, struct.pack('<'+'I'*len(words), *words))
        put(C+0x10, P)
        put(C+0x24, T+4*len(stack))
        put(C+0x1c, L+0x100)
        put(C+0x18, W+0x100)
        for i, value in enumerate(stack):
            put(T+4*i, value)
        def enter(machine, r):
            for reg, value in {17:C, 19:0x7fffff, 20:0x800000,
                               21:computed, 23:1, 30:width}.items():
                r[reg] = value
            r[31] = 0x8006c358
        def leave(machine, r):
            r[31] = 0x800ff000
        m.run(0x800ff100, hooks={0x800ff100:enter, 0x8006bb0c:leave})

    ids = [1, 7, 8, 199, 200, 255, 256, 299, 300, 399, 400, 499, 500,
           0x2bc, 0x2e9, 2943]
    for n in ids:
        for op, stack in [(0x21030000, ()), (0x22030000, (1,)),
                          (0x07000000, (1,))]:
            m.put(G, bytes([0xa5])*0x170)
            expected = bytearray(read(G, 0x170))
            dispatch([op | n, 1], stack)
            expected[n//8] |= 1 << (n%8)
            assert read(G, 0x170) == expected
            dispatch([0x0e000000 | n])
            assert word(T) == 1 and word(C+0x24) == T+4
            dispatch([0x1d000000 | n, 1])
            assert word(T) == 1 and word(C+0x10) == P+8
            dispatch([op | n, 0], () if op == 0x21030000 else (0,))
            expected[n//8] &= ~(1 << (n%8))
            assert read(G, 0x170) == expected
            dispatch([0x0e000000 | n])
            assert word(T) == 0
            trials.append([hex(op), n])
    # Zero is special for 0E and typed 21: accumulator / computed address.
    put(W, 0x12345678)
    dispatch([0x0e000000])
    assert word(T) == 0x12345678
    m.put(G, bytes(0x170))
    dispatch([0x21030000, 1], computed=0x345)
    assert read(G+0x345//8, 1) == bytes([1 << (0x345%8)])
    dispatch([0x07000000], (1,))
    assert read(G, 1) == b'\x01'
    # Computed read: variable word at W+4 plus next bytecode word.
    put(W+4, 0x340)
    dispatch([0x10000004, 5], width=0)
    assert word(W) == 1
    # Accumulator plus low-24-bit immediate uses the same bit reader.
    put(W, 0x340)
    dispatch([0x0a000005], width=0)
    assert word(W) == 1
    before = read(G, 0x170)
    m.put(L, bytes(0x100))
    dispatch([0x21830009, 1])
    assert read(L+0xfe, 1) == b'\x02' and read(G, 0x170) == before

    out = ROOT/'artifacts/so2-script-flags'
    out.mkdir(parents=True, exist_ok=True)
    archives = []
    for entry in [3287, 3390, 4125, 4270]:
        source = ROOT/f'artifacts/so2-terrain-pass3/entry-{entry}.bin'
        b = source.read_bytes()
        for i in range(struct.unpack_from('<I', b)[0]):
            tag, offset = struct.unpack_from('<II', b, 4+8*i)
            if tag != 1:
                continue
            d = slz(b[offset:])
            (out/f'entry-{entry}-script.bin').write_bytes(d)
            h = struct.unpack_from('<7I', d)
            archives.append(dict(entry=entry, source_sha256=hashlib.sha256(b).hexdigest(),
                                 tag=tag, container_offset=hex(offset),
                                 script_sha256=hashlib.sha256(d).hexdigest(),
                                 header=list(h), initial_pc_offset=hex(0x1c+4*h[2])))
            if entry == 3287:
                assert d[0x7614:0x761c] == bytes.fromhex('e9 02 03 21 01 00 00 00')
                m.put(G, bytes(0x170))
                dispatch(list(struct.unpack_from('<2I', d, 0x7614)))
                expected = bytearray(0x170)
                expected[0x2e9//8] = 1 << (0x2e9%8)
                assert read(G, 0x170) == expected
    result = dict(status='Verified (executed), bounded synthetic RAM; not in-game',
                  direct_trials=trials, special_and_computed_checks=6,
                  archive_literal_executed='3287 tag 1, decompressed +7614: flag 2E9 = 1',
                  archives=archives,
                  limits='Register/context setup and loop stop hooked; immediate loads; no complete event execution or named milestone.')
    (out/'execution.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
