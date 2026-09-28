"""Reproduce inventory instruction evidence and independently verify a candidate."""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import saveconv
import so2_fol
import so2_inventory as inv
from tools.so2_party_mips import Machine
from tools.verify_so2_fol import run_codec

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/so2-inventory'
CODEDIR = ROOT / 'artifacts/so2-fol/disc-code'
OVERLAY_SHA = 'f56ace2f46ff6c3d886e5f372a1e8f41db9da1d3667e65c4afb9189ddc3d9186'


def serialize(code, overlay, decoded, load=False):
    """Execute the entire real serializer (including codec and cache rebuilding).

    Alloc/free and resource E lookup are explicit host hooks; memcpy is the
    existing harness hook. RNG supplies legal seeded nibbles, not PS1 RNG state.
    """
    if hashlib.sha256(overlay).hexdigest() != OVERLAY_SHA:
        raise ValueError('expected Disc 1 save overlay')
    m = Machine(code)
    m.put(0x8007e000, overlay)
    m.executable_ranges.append((0x8007e000, 0x8007e000 + len(overlay)))
    layout = [(0x80075270, 0x80100000, 0, 0x1a0),
              (0x8007527c, 0x80101000, 0x1a0, 0x300),
              (0x80075280, 0x80102000, 0x4a0, 0x680),
              (0x80075278, 0x80103000, 0xb20, 0xc28),
              (None, 0x80105000, 0x1748, 0x440)]
    for ptr, addr, off, size in layout:
        if ptr:
            m.put(ptr, struct.pack('<I', addr))
        m.put(addr, bytes(size) if load else decoded[off:off+size])
    if load:
        stream = so2_fol.encode(decoded)
        m.put(0x80120000, struct.pack('<H', len(stream)) + stream)
    def allocate(m, r):
        assert r[4] == 0x2000
        r[2] = 0x80110000
    def resource(m, r):
        assert r[5] == 0xe
        r[2] = 0x80105000
    def free(m, r):
        assert r[4] == 0x80110000
    m.run(0x80081a70, (0, int(load), 0x80120000),
          {0x8001fe30: allocate, 0x80012108: resource, 0x8001fd70: free})
    if load:
        restored = b''.join(bytes(m.memory[addr & 0x1fffff:(addr & 0x1fffff)+size])
                            for _, addr, _, size in layout)
        cache = restored[inv.BASE+inv.CACHE:inv.BASE+inv.CACHE+inv.SLOTS]
        for i, w in enumerate(struct.unpack_from('<1024H', restored, inv.BASE)):
            nonce = (cache[i] >> 4) ^ (~i & 15)
            assert cache[i] == inv.integrity(w, i, nonce)
        expected = bytearray(decoded)
        expected[inv.BASE+inv.CACHE:inv.BASE+inv.CACHE+inv.SLOTS] = cache
        assert restored == expected
        return restored
    n = struct.unpack_from('<H', m.memory, 0x120000)[0]
    return bytes(m.memory[0x120000:0x120002+n])


def evidence():
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32 | capstone.CS_MODE_LITTLE_ENDIAN)
    sources = [
        ('code-2576-lba-30736.bin', 0x8002f810,
         [(0x8003368c, 0x800336c0), (0x8003c594, 0x8003c9d0), (0x800669bc, 0x800669e0)]),
        ('code-2986-lba-36126.bin', 0x8007e000, [(0x8007e728, 0x8007e750), (0x8007e8a8, 0x8007e8fc)]),
        ('code-2998-lba-36213.bin', 0x8007e000, [(0x80081a70, 0x80081c74)])]
    listing, manifest = [], {'sources': [], 'ram': []}
    resident = inv.DEFAULT_CODE.read_bytes()
    for name, base, ranges in sources:
        data = (CODEDIR / name).read_bytes()
        manifest['sources'].append({'file': name, 'load': hex(base), 'size': hex(len(data)), 'sha256': sha(data)})
        listing.append(f'\n# {name}, load {base:08x}')
        for lo, hi in ranges:
            listing.append(f'\n# [{lo:08x}, {hi:08x})')
            listing.extend(f'{i.address:08x} {i.bytes.hex()} {i.mnemonic} {i.op_str}'
                           for i in md.disasm(data[lo-base:hi-base], lo))
    for name in ['ram.bin', 'SCUS-94422_resume.ram']:
        data = (ROOT / 'artifacts/so2-fol' / name).read_bytes()
        ptr = struct.unpack_from('<I', data, 0x75278)[0]
        resources = struct.unpack_from('<I', data, 0x75258)[0] & 0x1fffff
        resource_slot = next(i for i in range(16) if struct.unpack_from('<I', data, resources+0x44+4*i)[0] == 0xe)
        fifth = struct.unpack_from('<I', data, resources+4+4*resource_slot)[0]
        chunk = data[ptr & 0x1fffff:(ptr & 0x1fffff) + inv.SIZE]
        good = 0
        for i, w in enumerate(struct.unpack_from('<1024H', chunk)):
            c = chunk[inv.CACHE+i]
            good += inv.integrity(w, i, (c >> 4) ^ (~i & 15)) == c
        manifest['ram'].append({'file': name, 'sha256': sha(data), 'inventory_pointer': hex(ptr),
            'resource_table': hex(resources | 0x80000000), 'resource_E_slot': resource_slot,
            'fifth_chunk_pointer': hex(fifth),
            'valid_integrity_slots': good,
            'add_remove_code_matches': data[0x3c594:0x3c9d0] == resident[0x3c594-0x2f810:0x3c9d0-0x2f810]})
        listing.append(f'\n# {name}: resource lookup in RAM, [80012108,80012144)')
        listing.extend(f'{i.address:08x} {i.bytes.hex()} {i.mnemonic} {i.op_str}'
                       for i in md.disasm(data[0x12108:0x12144], 0x80012108))
    OUT.mkdir(exist_ok=True)
    (OUT / 'evidence.asm').write_text('\n'.join(listing)+'\n')
    (OUT / 'sources.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return manifest


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify(source, candidate, suffix):
    _, old = saveconv.load_card(source)
    _, new = saveconv.load_card(candidate)
    found = [(f, o) for f, o in saveconv.chains(old) if f['name'].endswith(suffix)]
    assert len(found) == 1
    first, order = found[0]
    assert len(order) == 1
    start = order[0]*saveconv.BLOCK
    a, b = old[start:start+saveconv.BLOCK], new[start:start+saveconv.BLOCK]
    before, after = so2_fol.state(a), so2_fol.state(b)
    code = inv.DEFAULT_CODE.read_bytes()
    overlay = (CODEDIR / 'code-2998-lba-36213.bin').read_bytes()
    expected, slot = inv.add_item(a, 364, 20, code)
    assert b == expected and saveconv.so2_valid(b)
    assert old[:start] == new[:start] and old[start+saveconv.BLOCK:] == new[start+saveconv.BLOCK:]
    end = struct.unpack_from('<H', b, 0x21a)[0]
    assert run_codec(overlay, b[0x380:end]) == after
    assert run_codec(overlay, after, encode=True) == b[0x380:end]
    assert serialize(code, overlay, after) == b[0x380:end]
    serialize(code, overlay, after, load=True)
    def stats(block):
        return {'compressed_count': struct.unpack_from('<H', block, 0x380)[0],
                'C': struct.unpack_from('<H', block, 0x21a)[0],
                'A': struct.unpack_from('<I', block, 0x210)[0],
                'B': struct.unpack_from('<I', block, 0x214)[0]}
    report = {'source': str(source), 'candidate': str(candidate), 'save': first['name'], 'physical_block': order[0],
              'source_card_sha256': sha(old), 'candidate_card_sha256': sha(new),
              'source_block_sha256': sha(a), 'candidate_block_sha256': sha(b),
              'slot': slot, 'decoded_word_offset': hex(inv.BASE+2*slot),
              'before_word': hex(struct.unpack_from('<H', before, inv.BASE+2*slot)[0]),
              'after_word': hex(struct.unpack_from('<H', after, inv.BASE+2*slot)[0]),
              'before': stats(a), 'after': stats(b),
              'decoded_changes': [{'offset': hex(i), 'before': x, 'after': y}
                                  for i, (x, y) in enumerate(zip(before, after)) if x != y],
              'physical_changed_bytes': sum(x != y for x, y in zip(old, new)),
              'outside_target_block_identical': True, 'actual_codec_matches': True,
              'actual_full_serializer_save_and_load_match': True, 'loaded_in_game': False}
    (OUT / 'candidate-report.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path)
    p.add_argument('--candidate', type=Path)
    p.add_argument('--save', default='S15')
    args = p.parse_args()
    print(json.dumps(evidence(), indent=2))
    if args.source and args.candidate:
        print(json.dumps(verify(args.source, args.candidate, args.save), indent=2))
