"""Create an experimental SO2 recruitment candidate from the game's initializer.

Writes both saved character records into a genuinely unused slot. No story
events are simulated. See docs/SO2-PARTY-MEMBER-INVESTIGATION.md before use.
"""
import argparse
from pathlib import Path
import struct

import saveconv
import so2_fol
from tools.so2_party_mips import initial_records

PRIMARY, PRIMARY_SIZE = 0x1a0, 0x60
SECONDARY, SECONDARY_SIZE = 0x4a0, 0xd0
DEFAULT_CODE = Path(__file__).resolve().parent / 'artifacts/so2-fol/disc-code/code-2576-lba-30736.bin'


def add_member(block, character_id, code, slot=None, seed=0):
    if not saveconv.so2_valid(block):
        raise saveconv.SaveError('source checksum mismatch')
    before = so2_fol.state(block)
    ids = [struct.unpack_from('<h', before, PRIMARY + i * PRIMARY_SIZE)[0] for i in range(8)]
    if character_id in map(abs, ids):
        raise saveconv.SaveError('character already present or retained with negative ID')
    def empty(i):
        a, b = PRIMARY + i * PRIMARY_SIZE, SECONDARY + i * SECONDARY_SIZE
        return not any(before[a:a + PRIMARY_SIZE]) and not any(before[b:b + SECONDARY_SIZE])
    if slot is None:
        slot = next((i for i in range(8) if empty(i)), None)
    if slot is None or not 0 <= slot < 8 or not empty(slot):
        raise saveconv.SaveError('requires a slot with BOTH complete records all zero')
    primary, secondary = initial_records(code, character_id, seed)
    edited = bytearray(before)
    a, b = PRIMARY + slot * PRIMARY_SIZE, SECONDARY + slot * SECONDARY_SIZE
    edited[a:a + PRIMARY_SIZE], edited[b:b + SECONDARY_SIZE] = primary, secondary
    compressed = so2_fol.encode(edited)
    end = so2_fol.STREAM + 2 + len(compressed)
    if end > len(block):
        raise saveconv.SaveError('edited data does not fit one block')
    result = bytearray(block)
    struct.pack_into('<H', result, so2_fol.STREAM, len(compressed))
    result[so2_fol.STREAM + 2:end] = compressed
    struct.pack_into('<H', result, 0x21a, end)
    saveconv.so2_sign(result)
    if so2_fol.state(result) != edited or not saveconv.so2_valid(result):
        raise saveconv.SaveError('round-trip/checksum verification failed')
    if any(x != y and not (a <= i < a + PRIMARY_SIZE or b <= i < b + SECONDARY_SIZE)
           for i, (x, y) in enumerate(zip(before, edited))):
        raise saveconv.SaveError('unexpected decoded edit outside paired records')
    return bytes(result), slot


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('--save', required=True)
    p.add_argument('--id', required=True, type=int, choices=range(1, 13))
    p.add_argument('--slot', type=int, choices=range(8))
    p.add_argument('--seed', type=int, default=0, help='reproducible talent RNG, default 0')
    p.add_argument('--code', type=Path, default=DEFAULT_CODE)
    p.add_argument('--out', required=True, type=Path)
    args = p.parse_args()
    _, card = saveconv.load_card(args.source)
    found = [(f, order) for f, order in saveconv.chains(card) if f['name'].endswith(args.save)]
    if len(found) != 1:
        p.error('save suffix must identify exactly one save')
    first, order = found[0]
    if len(order) != 1 or first['size'] != saveconv.BLOCK or first['next'] != 0xffff:
        p.error('expected complete single-block save')
    start = order[0] * saveconv.BLOCK
    block, slot = add_member(card[start:start + saveconv.BLOCK], args.id,
                             args.code.read_bytes(), args.slot, args.seed)
    result = card[:start] + block + card[start + saveconv.BLOCK:]
    with args.out.open('xb') as f:
        f.write(result)
    print(f'{first["name"]}: initialized ID {args.id} in slot {slot}; wrote {args.out}')
    print('Paired records, codec and checksums verified. NOT tested in-game; story flags unchanged.')


if __name__ == '__main__':
    main()
