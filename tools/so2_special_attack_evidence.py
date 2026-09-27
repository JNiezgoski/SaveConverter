"""Bounded execution of the extracted ability-selection UI; no source-save writes.

Requires capstone only for the byte-bearing listings. Uses the existing MIPS
interpreter (branch delay slots, immediate loads); this is not an emulator test.
"""
from pathlib import Path
import hashlib
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.so2_party_mips import Machine

OUT = ROOT / 'artifacts/so2-special-attack'
RES = ROOT / 'artifacts/so2-fol/disc-code/code-2576-lba-30736.bin'
MENU = ROOT / 'artifacts/so2-specialty/disc-code/code-3004-lba-36241.bin'
SAVE = ROOT / 'artifacts/so2-fol/disc-code/code-2998-lba-36213.bin'
sha = lambda data: hashlib.sha256(data).hexdigest()


def fragment(m, start, stop, registers):
    """Enter with explicit boundary registers; stop BEFORE the next routine.

    No instruction is replaced. The stop hook runs after any preceding branch
    delay slot. No UI/refresh function is silently simulated or skipped.
    """
    captured = []
    def enter(machine, r):
        for index, value in registers.items():
            r[index] = value
        r[31] = start
    def leave(machine, r):
        captured.extend(r)
        r[31] = 0x800ff000
    m.run(0x800ff004, hooks={0x800ff004: enter, stop: leave})
    return captured


def main():
    import capstone
    OUT.mkdir(exist_ok=True)
    code, menu, save = RES.read_bytes(), MENU.read_bytes(), SAVE.read_bytes()
    assert sha(menu) == '0960a153c9556a57f9d49d37a8943837199c88598b217a108b88ff8a8af937bb'
    assert sha(save) == 'f56ace2f46ff6c3d886e5f372a1e8f41db9da1d3667e65c4afb9189ddc3d9186'
    sources = [(RES, code, 0x8002f810, [(0x800331b8, 0x80033218),
                (0x80034e6c, 0x80035020), (0x80078eb4, 0x80078f50)]),
               (MENU, menu, 0x8007e000, [(0x8007ee00, 0x8007ee78),
                (0x8007efd8, 0x8007f018), (0x8007f938, 0x8007f9dc),
                (0x8007fae8, 0x8007fc60), (0x800800b8, 0x800802c4)]),
               (SAVE, save, 0x8007e000, [(0x80081af4, 0x80081b30),
                (0x80081c38, 0x80081c74)])]
    md = capstone.Cs(capstone.CS_ARCH_MIPS,
                     capstone.CS_MODE_MIPS32 | capstone.CS_MODE_LITTLE_ENDIAN)
    lines, manifest = [], []
    for path, data, base, ranges in sources:
        manifest.append(dict(path=str(path.relative_to(ROOT)), sha256=sha(data),
                             load=hex(base), size=hex(len(data))))
        lines.append(f'\n# {path.name}, load {base:08x}')
        for lo, hi in ranges:
            lines.append(f'# [{lo:08x},{hi:08x})')
            lines.extend(f'{i.address:08x} {i.bytes.hex()} {i.mnemonic} {i.op_str}'
                         for i in md.disasm(data[lo-base:hi-base], lo))
    (OUT / 'evidence.asm').write_text('\n'.join(lines) + '\n')
    results = []
    for name in ('S01', 'S02', 'S15'):
        path = ROOT / f'artifacts/so2-specialty/{name}.decoded'
        decoded = path.read_bytes()
        assert len(decoded) == 0x1b88
        sample = dict(path=str(path.relative_to(ROOT)), sha256=sha(decoded), slots=[])
        m = Machine(code)
        # Deliberately distinct allocations: no decoded-offset-to-RAM subtraction.
        primary, secondary, buffer, context = 0x80100000, 0x80110000, 0x80120000, 0x80130000
        def word(address, value):
            m.put(address, struct.pack('<I', value))
        def overlay(data):
            m.put(0x8007e000, data)
            m.executable_ranges = [(0x8002f810, 0x8007c00c),
                                   (0x8007e000, 0x8007e000 + len(data))]
        overlay(save)
        m.put(buffer, decoded)
        # Execute the serializer's real direction selector, host memcpy hook only.
        for offset, length, dest in ((0x1a0, 0x300, primary), (0x4a0, 0x680, secondary)):
            word(0x801f0010, length)
            m.run(0x80081c38, (0, 1, buffer+offset, dest))
            assert m.memory[dest & 0x1fffff:(dest & 0x1fffff)+length] == decoded[offset:offset+length]
        word(0x8007527c, primary)
        word(0x80075280, secondary)
        overlay(menu)
        for slot in range(8):
            m.run(0x800331c8, (slot,))
            assert struct.unpack_from('<I', m.memory, 0x74080)[0] == secondary+slot*0xd0
            off = 0x4a0+slot*0xd0
            record = decoded[off:off+0xd0]
            assigned = list(record[0xcc:0xd0])
            # UI's complete candidate loop: zero choice, 32 availability bytes,
            # exclusion of all four currently assigned IDs.
            m.put(context, bytes(0x200))
            r = fragment(m, 0x800800b8, 0x8008016c, {17: context})
            count = r[5]
            choices = list(struct.unpack_from('<'+'I'*count, m.memory, 0x13005c))
            expected = [0]+[i+1 for i,v in enumerate(record[0x3c:0x5c])
                           if v and i+1 not in assigned]
            assert choices == expected
            reads = []
            for group in range(2):
                for column in range(2):
                    r = fragment(m, 0x8007ee50, 0x8007ee68, {4: group, 5: column})
                    reads.append(r[5])
            assert reads == assigned
            # Read the halfword indexed by one-based ability ID. Stop before
            # display helper; no claimed interpretation of its numeric value.
            halfwords = []
            for ability in range(1, 33):
                r = fragment(m, 0x8007efe0, 0x8007f010,
                             {2: 1, 17: ability, 18: context})
                assert r[6] & 0xffff == struct.unpack_from('<H', record, 0x8a+2*ability)[0]
                halfwords.append(r[6] & 0xffff)
            edits = []
            for group in range(2):
                for column in range(2):
                    # Restore the real record for each isolated commit trial.
                    m.put(secondary+slot*0xd0, record)
                    new_id = choices[1] if len(choices) > 1 else 0
                    word(context+0x54, group)
                    word(context+0x58, column)
                    m.put(context+0x34, struct.pack('<h', 1 if new_id else 0))
                    before = bytes(m.memory)
                    m.writes.clear()
                    fragment(m, 0x80080238, 0x800e0984, {4: context, 5: 0})
                    target = (secondary+slot*0xd0+0xcc+2*group+column) & 0x1fffff
                    expected_memory = bytearray(before)
                    expected_memory[target] = new_id
                    # Prologue stack stores are the only other permitted writes.
                    for a,n in m.writes:
                        assert a == target and n == 1 or 0x1effe0 <= a and a+n <= 0x1f0000
                    expected_memory[0x1effe0:0x1f0000] = m.memory[0x1effe0:0x1f0000]
                    assert expected_memory == m.memory
                    edits.append(dict(offset=hex(off+0xcc+2*group+column),
                                      before=assigned[2*group+column], after=new_id))
            m.put(secondary+slot*0xd0, record)
            sample['slots'].append(dict(slot=slot, id=struct.unpack_from('<h', decoded, 0x1a0+slot*0x60)[0],
                                        assignments=reads, candidates=choices,
                                        indexed_halfwords=halfwords, commits=edits))
        results.append(sample)
    ram = []
    for name in ('ram.bin', 'SCUS-94422_resume.ram'):
        data = (ROOT/'artifacts/so2-fol'/name).read_bytes()
        ptr = struct.unpack_from('<I', data, 0x75280)[0]
        ram.append(dict(file=name, sha256=sha(data), secondary_pointer=hex(ptr),
                        slot0_assignments_address=hex(ptr+0xcc),
                        slot0_assignments=data[(ptr & 0x1fffff)+0xcc:(ptr & 0x1fffff)+0xd0].hex()))
    report = dict(sources=manifest, samples=results, ram=ram,
                  verification='24 candidate loops, 96 assignment reads, 768 halfword reads, 96 isolated commits; all assertions passed',
                  scope='Stops before UI close/refresh; no live controller input, game-load test, or source-save write.')
    (OUT/'verification.json').write_text(json.dumps(report, indent=2)+'\n')
    print(report['verification'])
    for s in results:
        print(s['path'], [(r['slot'], r['id'], r['assignments'], r['candidates']) for r in s['slots'] if r['id'] > 0])


if __name__ == '__main__':
    main()
