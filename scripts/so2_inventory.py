"""Add SO2 items using the extracted game routine; create a NEW card only.

See docs/SO2-INVENTORY-ADD-INVESTIGATION.md. Counts are increments, not totals.
"""
import argparse
import os
import sys
from pathlib import Path
import struct

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)
sys.path.insert(0, os.path.dirname(_here))
import saveconv
import so2_codec
from tools.so2_party_mips import Machine

BASE, SIZE, SLOTS = 0xb20, 0xc28, 0x400
RECENT, CACHE, FLAG = 0x800, 0x824, 0xc24
RAM = 0x80100000
DEFAULT_CODE = Path(__file__).resolve().parent.parent / 'artifacts/so2-fol/disc-code/code-2576-lba-30736.bin'


def integrity(word, slot, random_nibble):
    """8003C8A0: bit 15 is excluded; the other four nibbles are XOR folded."""
    word &= 0x7fff
    folded = (word ^ (word >> 4) ^ (word >> 8) ^ (word >> 12)) & 15
    return (((~slot & 15) ^ random_nibble) << 4) | (folded ^ random_nibble)


def predict(chunk, item_id, count, marked=1):
    """Independent persisted-state model of 8003C594 and 8003C70C."""
    if len(chunk) != SIZE or not 1 <= item_id <= 1023 or not 1 <= count <= 20 or marked not in (0, 1):
        raise saveconv.SaveError('expected inventory chunk, ID 1..1023, count 1..20, flag 0/1')
    if any(chunk[CACHE:CACHE + SLOTS]):
        raise saveconv.SaveError('expected saved (zeroed) inventory integrity cache')
    words = struct.unpack_from('<1024H', chunk)
    owned = [(i, w) for i, w in enumerate(words) if (w >> 10) & 31]
    ids = [w & 1023 for _, w in owned]
    if len(ids) != len(set(ids)) or any(not (w & 1023) or ((w >> 10) & 31) > 20 for _, w in owned):
        raise saveconv.SaveError('invalid or duplicate occupied inventory entries')
    slot = next((i for i, w in owned if w & 1023 == item_id), None)
    old_count = ((words[slot] >> 10) & 31) if slot is not None else 0
    if old_count + count > 20:
        raise saveconv.SaveError('addition would exceed stack limit 20')
    if slot is None:
        slot = next((i for i, w in enumerate(words) if not ((w >> 10) & 31)), None)
    if slot is None:
        raise saveconv.SaveError('inventory has no vacant slot')
    out = bytearray(chunk)
    struct.pack_into('<H', out, 2 * slot, item_id | ((old_count + count) << 10) | (marked << 15))
    recent = list(struct.unpack_from('<16H', chunk, RECENT))
    if out[FLAG]:
        recent = [0] * 16
        out[FLAG] = 0
    end = recent.index(item_id) if item_id in recent else 15
    recent[1:end + 1] = recent[:end]
    recent[0] = item_id
    struct.pack_into('<16H', out, RECENT, *recent)
    return bytes(out), slot


def loaded_machine(code, chunk, seed=0):
    """Restore chunk and rebuild runtime cache as the serializer does on load."""
    if len(chunk) != SIZE:
        raise ValueError('wrong inventory chunk size')
    m = Machine(code, seed)
    m.put(RAM, chunk)
    for slot, word in enumerate(struct.unpack_from('<1024H', chunk)):
        # A legal deterministic RNG substitute, independently tested against MIPS.
        m.put(RAM + CACHE + slot, bytes([integrity(word, slot, 0)]))
    m.writes.clear()
    return m


def execute_add(code, chunk, item_id, count, marked=1):
    expected, slot = predict(chunk, item_id, count, marked)
    m = loaded_machine(code, chunk)
    if m.run(0x8003c594, (RAM, item_id, count, marked)) != 1:
        raise saveconv.SaveError('game add routine rejected the operation')
    allowed = [(0x100000 + 2*slot, 0x100002 + 2*slot),
               (0x100800, 0x100820), (0x100824 + slot, 0x100825 + slot),
               (0x100c24, 0x100c25), (0x1ef000, 0x1f0000)]
    if any(not any(lo <= a and a+n <= hi for lo, hi in allowed) for a, n in m.writes):
        raise saveconv.SaveError('game wrote outside slot, history, cache, flag and stack')
    out = bytearray(m.memory[0x100000:0x100000 + SIZE])
    out[CACHE:CACHE + SLOTS] = bytes(SLOTS)  # actual serializer's save behavior
    if out != expected:
        raise saveconv.SaveError('MIPS result disagrees with independent prediction')
    return bytes(out), slot


def add_item(block, item_id, count, code, marked=1):
    if not saveconv.so2_valid(block):
        raise saveconv.SaveError('source checksum mismatch')
    before = so2_codec.state(block)
    chunk, slot = execute_add(code, before[BASE:BASE + SIZE], item_id, count, marked)
    edited = before[:BASE] + chunk + before[BASE + SIZE:]
    allowed = set(range(BASE + slot*2, BASE + slot*2 + 2)) | set(range(BASE + RECENT, BASE + RECENT + 32)) | {BASE + FLAG}
    if any(a != b and i not in allowed for i, (a, b) in enumerate(zip(before, edited))):
        raise saveconv.SaveError('unexpected decoded edit')
    compressed = so2_codec.encode(edited)
    end = so2_codec.STREAM + 2 + len(compressed)
    if end > len(block):
        raise saveconv.SaveError('edited data does not fit one block')
    result = bytearray(block)
    struct.pack_into('<H', result, so2_codec.STREAM, len(compressed))
    result[so2_codec.STREAM + 2:end] = compressed
    struct.pack_into('<H', result, 0x21a, end)
    saveconv.so2_sign(result)
    if so2_codec.state(result) != edited or not saveconv.so2_valid(result):
        raise saveconv.SaveError('round-trip/checksum verification failed')
    physical_allowed = set(range(0x210, 0x218)) | {0x21a, 0x21b} | set(range(0x380, end))
    if any(a != b and i not in physical_allowed for i, (a, b) in enumerate(zip(block, result))):
        raise saveconv.SaveError('unexpected physical block edit')
    return bytes(result), slot


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('--save', required=True)
    p.add_argument('--id', required=True, type=int)
    p.add_argument('--count', required=True, type=int, help='quantity to ADD, 1..20')
    p.add_argument('--marked', type=int, choices=(0, 1), default=1, help='bit 15; default 1 matches shop/script callers')
    p.add_argument('--code', type=Path, default=DEFAULT_CODE)
    p.add_argument('--out', required=True, type=Path)
    args = p.parse_args()
    # Keep every tool-generated candidate inside this investigation directory.
    root = Path(__file__).resolve().parent.parent / 'artifacts/so2-inventory'
    if not args.out.resolve().is_relative_to(root.resolve()):
        p.error('output must be a new file under artifacts/so2-inventory/')
    _, card = saveconv.load_card(args.source)
    found = [(f, o) for f, o in saveconv.chains(card) if f['name'].endswith(args.save)]
    if len(found) != 1:
        p.error('save suffix must identify exactly one save')
    first, order = found[0]
    if len(order) != 1 or first['size'] != saveconv.BLOCK or first['next'] != 0xffff:
        p.error('expected complete single-block save')
    start = order[0] * saveconv.BLOCK
    block, slot = add_item(card[start:start + saveconv.BLOCK], args.id, args.count, args.code.read_bytes(), args.marked)
    result = card[:start] + block + card[start + saveconv.BLOCK:]
    if result[:start] != card[:start] or result[start+saveconv.BLOCK:] != card[start+saveconv.BLOCK:]:
        raise saveconv.SaveError('unexpected edit outside target save')
    root.mkdir(exist_ok=True)
    with args.out.open('xb') as f:
        f.write(result)
    print(f'{first["name"]}: added {args.count} of ID {args.id} in slot {slot}; wrote {args.out}')
    print('Actual add instructions, independent prediction, preservation, codec and checksums verified. Not loaded in-game.')


if __name__ == '__main__':
    main()
