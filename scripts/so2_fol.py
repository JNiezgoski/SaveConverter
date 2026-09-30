"""Fol (in-game money) edits through SO2's zero-run codec, never through fixed card offsets.

See docs/SO2-FOL-INVESTIGATION.md for game-code evidence and limitations.
"""
import argparse
import os
import sys
from pathlib import Path
import struct

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import saveconv
import so2_codec

FOL = 0x18
MAX_FOL = 999_999_999


def set_fol(block, value):
    if not 0 <= value <= MAX_FOL:
        raise saveconv.SaveError(f'Fol must be between 0 and {MAX_FOL}')
    if not saveconv.so2_valid(block):
        raise saveconv.SaveError('source checksum mismatch; audit source first')
    before = so2_codec.state(block)
    edited = bytearray(before)
    struct.pack_into('<I', edited, FOL, value)
    compressed = so2_codec.encode(edited)
    end = so2_codec.STREAM + 2 + len(compressed)
    if end > len(block):
        raise saveconv.SaveError('edited data does not fit one block')
    result = bytearray(block)
    struct.pack_into('<H', result, so2_codec.STREAM, len(compressed))
    result[so2_codec.STREAM + 2:end] = compressed
    struct.pack_into('<H', result, 0x21A, end)
    saveconv.so2_sign(result)
    if so2_codec.state(result) != bytes(edited) or not saveconv.so2_valid(result):
        raise saveconv.SaveError('edited save failed verification')
    return bytes(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--save', required=True, help='save suffix, e.g. S13')
    parser.add_argument('--fol', required=True, type=int)
    parser.add_argument('--out', required=True, type=Path, help='NEW raw card copy')
    args = parser.parse_args()
    _, card = saveconv.load_card(args.source)
    matches = [(first, order) for first, order in saveconv.chains(card)
               if first['name'].endswith(args.save)]
    if len(matches) != 1:
        parser.error('save suffix must select exactly one save')
    first, order = matches[0]
    if len(order) != 1 or first['size'] != saveconv.BLOCK or first['next'] != 0xffff:
        parser.error('expected a complete single-block directory entry')
    start = order[0] * saveconv.BLOCK
    old = card[start:start + saveconv.BLOCK]
    new = set_fol(old, args.fol)
    result = card[:start] + new + card[start + saveconv.BLOCK:]
    # Exclusive creation forbids replacing the source or an existing card.
    with args.out.open('xb') as handle:
        handle.write(result)
    previous = struct.unpack_from('<I', so2_codec.state(old), FOL)[0]
    print(f'{first["name"]}: {previous} -> {args.fol}; wrote {args.out}')
    print('Decoded state and checksums verified. NOT tested in-game.')


if __name__ == '__main__':
    main()
