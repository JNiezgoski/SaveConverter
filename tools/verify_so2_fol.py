"""Compare the Python codec with the actual save-overlay MIPS instructions.

This is an isolated leaf-routine interpreter, not an emulator/game-load test.
Only reads the supplied overlay and save archive. No source files are written.
"""
from pathlib import Path
import argparse
import hashlib
import random
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import saveconv
import so2_fol


def signed(value, bits=32):
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def run_codec(overlay, data, encode=False):
    """Execute the bounded codec leaves with branch delay slots.

    Loads are immediate here; these leaves schedule their load consumers safely.
    Unknown instructions fail closed. No host calls or console peripherals.
    """
    memory = bytearray(0x200000)
    memory[0x7e000:0x7e000 + len(overlay)] = overlay
    memory[0x110000:0x110000 + len(data)] = data
    regs = [0] * 32
    regs[5], regs[6], regs[7] = 0x80100000, 0x80110000, len(data)
    regs[29], regs[31] = 0x801f0000, 0x800ff000
    pc = 0x80081ef4 if encode else 0x80081fe8
    next_pc = pc + 4
    for _ in range(1_000_000):
        if pc == regs[31]:
            length = regs[2] if encode else regs[5] - 0x80100000
            return bytes(memory[0x100000:0x100000 + length])
        here = pc
        word = struct.unpack_from('<I', memory, pc & 0x1fffff)[0]
        pc, next_pc = next_pc, next_pc + 4
        op, rs, rt, rd = word >> 26, (word >> 21) & 31, (word >> 16) & 31, (word >> 11) & 31
        imm, shift, fn = word & 0xffff, (word >> 6) & 31, word & 63
        simm = signed(imm, 16)
        if op == 0:
            if fn == 0: regs[rd] = regs[rt] << shift
            elif fn == 3: regs[rd] = signed(regs[rt]) >> shift
            elif fn == 8: next_pc = regs[rs]
            elif fn == 0x21: regs[rd] = regs[rs] + regs[rt]
            elif fn == 0x23: regs[rd] = regs[rs] - regs[rt]
            elif fn == 0x25: regs[rd] = regs[rs] | regs[rt]
            elif fn == 0x2a: regs[rd] = int(signed(regs[rs]) < signed(regs[rt]))
            else: raise AssertionError(f'unsupported special {word:08x} at {here:08x}')
        elif op == 2: next_pc = ((here + 4) & 0xf0000000) | ((word & 0x3ffffff) << 2)
        elif op in (4, 5, 6):
            condition = {4: regs[rs] == regs[rt], 5: regs[rs] != regs[rt],
                         6: signed(regs[rs]) <= 0}[op]
            if condition: next_pc = here + 4 + (simm << 2)
        elif op == 9: regs[rt] = regs[rs] + simm
        elif op == 10: regs[rt] = int(signed(regs[rs]) < simm)
        elif op == 12: regs[rt] = regs[rs] & imm
        elif op in (0x21, 0x24, 0x28, 0x29):
            address = (regs[rs] + simm) & 0x1fffff
            if op == 0x21: regs[rt] = struct.unpack_from('<h', memory, address)[0]
            elif op == 0x24: regs[rt] = memory[address]
            elif op == 0x28: memory[address] = regs[rt] & 255
            else: struct.pack_into('<H', memory, address, regs[rt] & 0xffff)
        else: raise AssertionError(f'unsupported {word:08x} at {here:08x}')
        regs = [r & 0xffffffff for r in regs]
        regs[0] = 0
    raise AssertionError('instruction budget exceeded')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('overlay', type=Path, help='Disc 1 archive entry 2998')
    parser.add_argument('saves', type=Path)
    args = parser.parse_args()
    overlay = args.overlay.read_bytes()
    seen = set()
    canonical = valid = checked = rejected = 0
    for path in sorted(args.saves.rglob('*')):
        if path.suffix.lower() not in ('.mcd', '.mcs', '.gme'):
            continue
        try:
            saves = saveconv.read_saves(path)
        except (OSError, saveconv.SaveError):
            continue
        for save in saves:
            block = save.data
            digest = hashlib.sha256(block).digest()
            if block[0x200:0x20a] != b'STAR OCEAN' or digest in seen:
                continue
            seen.add(digest)
            try:
                decoded = so2_fol.state(block)
            except saveconv.SaveError as error:
                rejected += 1
                print('STRUCTURE REJECT', path.relative_to(args.saves), save.name, str(error))
                continue
            checked += 1
            end = struct.unpack_from('<H', block, 0x21a)[0]
            packed = block[0x380:end]
            assert run_codec(overlay, packed) == decoded, (path, save.name)
            encoded = so2_fol.encode(decoded)
            actual = run_codec(overlay, decoded, encode=True)
            assert actual == struct.pack('<H', len(encoded)) + encoded
            canonical += actual == packed
            valid += saveconv.so2_valid(block)
    print(f'{len(seen)} distinct blocks: {checked} MIPS/Python decode and encode agree; '
          f'{canonical} canonical encodings; {valid} checksum-valid; {rejected} structure rejects.')
    rng = random.Random(13)
    cases = [bytes(n) for n in (0, 1, 2, 3, 255, 256, 257, 258, 512, 1025)]
    cases += [bytes(rng.choice((0, 0, 0, rng.randrange(256))) for _ in range(1024))]
    for data in cases:
        encoded = so2_fol.encode(data)
        actual = run_codec(overlay, data, encode=True)
        assert actual == struct.pack('<H', len(encoded)) + encoded
        assert run_codec(overlay, actual) == data
    print(f'{len(cases)} additional zero-run/mixed-data cases agree with MIPS.')


if __name__ == '__main__':
    main()
