"""Fol edits through SO2's zero-run codec, never through fixed card offsets.

See docs/SO2-FOL-INVESTIGATION.md for game-code evidence and limitations.
"""
import argparse
import os
import sys
from pathlib import Path
import struct

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import saveconv

STREAM = 0x380
STATE_SIZE = 0x1B88
FOL = 0x18
MAX_FOL = 999_999_999


def decode(encoded, limit=STATE_SIZE):
    """Decode 00 00 N as N+2 zeros (game routine 80081FE8)."""
    out = bytearray()
    pos = zeros = 0
    while pos < len(encoded):
        value = encoded[pos]
        pos += 1
        out.append(value)
        zeros = zeros + 1 if value == 0 else 0
        if zeros == 2:
            if pos == len(encoded):
                raise saveconv.SaveError('truncated zero-run token')
            out.extend(bytes(encoded[pos]))
            pos += 1
            zeros = 0
        if len(out) > limit:
            raise saveconv.SaveError('decoded state exceeds expected size')
    return bytes(out)


def encode(decoded):
    """Canonical game encoding: zero runs split at 256 (80081EF4)."""
    out = bytearray()
    pos = 0
    while pos < len(decoded):
        if decoded[pos]:
            out.append(decoded[pos])
            pos += 1
            continue
        end = pos + 1
        while end < len(decoded) and end - pos < 256 and decoded[end] == 0:
            end += 1
        count = end - pos
        out.extend(b'\0' if count == 1 else bytes([0, 0, count - 2]))
        pos = end
    return bytes(out)


def state(block):
    if len(block) != saveconv.BLOCK or block[0x200:0x20A] != b'STAR OCEAN':
        raise saveconv.SaveError('expected a single-block SO2 save')
    end = struct.unpack_from('<H', block, 0x21A)[0]
    count = struct.unpack_from('<H', block, STREAM)[0]
    if end != STREAM + 2 + count or end > len(block):
        raise saveconv.SaveError('inconsistent compressed length / C')
    decoded = decode(block[STREAM + 2:end])
    if len(decoded) != STATE_SIZE:
        raise saveconv.SaveError(f'unexpected decoded size: {len(decoded):#x}')
    return decoded


def set_fol(block, value):
    if not 0 <= value <= MAX_FOL:
        raise saveconv.SaveError(f'Fol must be between 0 and {MAX_FOL}')
    if not saveconv.so2_valid(block):
        raise saveconv.SaveError('source checksum mismatch; audit source first')
    before = state(block)
    edited = bytearray(before)
    struct.pack_into('<I', edited, FOL, value)
    compressed = encode(edited)
    end = STREAM + 2 + len(compressed)
    if end > len(block):
        raise saveconv.SaveError('edited data does not fit one block')
    result = bytearray(block)
    struct.pack_into('<H', result, STREAM, len(compressed))
    result[STREAM + 2:end] = compressed
    struct.pack_into('<H', result, 0x21A, end)
    saveconv.so2_sign(result)
    if state(result) != bytes(edited) or not saveconv.so2_valid(result):
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
    previous = struct.unpack_from('<I', state(old), FOL)[0]
    print(f'{first["name"]}: {previous} -> {args.fol}; wrote {args.out}')
    print('Decoded state and checksums verified. NOT tested in-game.')


if __name__ == '__main__':
    main()
