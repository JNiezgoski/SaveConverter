"""SO2's zero-run save-body codec: decode()/encode() the compression the game
uses inside a save block, plus state() to pull the decoded body out of a raw
block and verify its length/checksums line up.

See docs/SO2-FOL-INVESTIGATION.md for the game-code evidence (this is where
the codec was first reverse-engineered, hence the doc name) and limitations.
"""
import os
import sys
import struct

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import saveconv

STREAM = 0x380
STATE_SIZE = 0x1B88


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
