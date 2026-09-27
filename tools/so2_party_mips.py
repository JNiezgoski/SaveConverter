"""Bounded execution of extracted SO2 party instructions, not a PS1 emulator.

Branch delay slots are executed; scheduled loads are immediate. RNG and libc
memset/memcpy are host hooks. No game/runtime refresh calls are silently skipped.
"""
import hashlib
import random
import struct

CODE_SHA256 = '6dec3950348b57068a85759f472ea7d5c92241d28b00ff4ea139ddd8dc1587cf'


def signed(value, bits=32):
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


class Machine:
    def __init__(self, code, seed=0):
        if hashlib.sha256(code).hexdigest() != CODE_SHA256:
            raise ValueError('expected Disc 1 archive entry 2576, LBA 30736')
        self.memory = bytearray(0x200000)
        self.memory[0x2f810:0x2f810 + len(code)] = code
        self.rng = random.Random(seed)
        self.writes = []
        self.calls = []
        self.executable_ranges = [(0x8002f810, 0x8007c00c)]

    def put(self, address, data):
        address &= 0x1fffff
        if address + len(data) > len(self.memory):
            raise ValueError('memory write outside RAM')
        self.memory[address:address + len(data)] = data
        self.writes.append((address, len(data)))

    def run(self, entry, args=(), hooks=None):
        hooks = hooks or {}
        r = [0] * 32
        r[4:4 + len(args)] = args
        r[29], r[31] = 0x801f0000, 0x800ff000
        pc, nxt = entry, entry + 4
        hi = lo = 0
        for _ in range(200000):
            if pc == 0x800ff000:
                return r[2]
            if pc in (0x80023f10, 0x80023ed0, 0x800104d4) or pc in hooks:
                self.calls.append((pc, tuple(r[4:8])))
                if pc in hooks:
                    hooks[pc](self, r)
                elif pc == 0x800104d4:
                    r[2] = self.rng.randrange(r[4]) if r[4] else 0
                elif pc == 0x80023f10:
                    self.put(r[4], bytes([r[5] & 255]) * r[6])
                    r[2] = r[4]
                else:
                    a = r[5] & 0x1fffff
                    self.put(r[4], bytes(self.memory[a:a + r[6]]))
                    r[2] = r[4]
                pc, nxt = r[31], r[31] + 4
                continue
            if not any(lo <= pc < hi for lo, hi in self.executable_ranges):
                raise ValueError(f'unhandled external call {pc:08x}')
            here = pc
            w = struct.unpack_from('<I', self.memory, pc & 0x1fffff)[0]
            pc, nxt = nxt, nxt + 4
            op, rs, rt, rd = w >> 26, (w >> 21) & 31, (w >> 16) & 31, (w >> 11) & 31
            imm, sh, fn = w & 65535, (w >> 6) & 31, w & 63
            si = signed(imm, 16)
            if op == 0:
                if fn == 0: r[rd] = r[rt] << sh
                elif fn == 2: r[rd] = r[rt] >> sh
                elif fn == 3: r[rd] = signed(r[rt]) >> sh
                elif fn == 4: r[rd] = r[rt] << (r[rs] & 31)
                elif fn == 7: r[rd] = signed(r[rt]) >> (r[rs] & 31)
                elif fn == 8: nxt = r[rs]
                elif fn == 0x10: r[rd] = hi
                elif fn == 0x12: r[rd] = lo
                elif fn == 0x18:
                    product = signed(r[rs]) * signed(r[rt])
                    hi, lo = (product >> 32) & 0xffffffff, product & 0xffffffff
                elif fn == 0x21: r[rd] = r[rs] + r[rt]
                elif fn == 0x23: r[rd] = r[rs] - r[rt]
                elif fn == 0x24: r[rd] = r[rs] & r[rt]
                elif fn == 0x25: r[rd] = r[rs] | r[rt]
                elif fn == 0x26: r[rd] = r[rs] ^ r[rt]
                elif fn == 0x27: r[rd] = ~(r[rs] | r[rt])
                elif fn == 0x2a: r[rd] = int(signed(r[rs]) < signed(r[rt]))
                elif fn == 0x2b: r[rd] = int(r[rs] < r[rt])
                else: raise ValueError(f'unsupported {w:08x} at {here:08x}')
            elif op in (2, 3):
                nxt = ((here + 4) & 0xf0000000) | ((w & 0x3ffffff) << 2)
                if op == 3: r[31] = here + 8
            elif op in (1, 4, 5, 6, 7):
                if op == 1:
                    if rt not in (0, 1): raise ValueError('unsupported regimm')
                    take = signed(r[rs]) < 0 if rt == 0 else signed(r[rs]) >= 0
                elif op == 4: take = r[rs] == r[rt]
                elif op == 5: take = r[rs] != r[rt]
                elif op == 6: take = signed(r[rs]) <= 0
                else: take = signed(r[rs]) > 0
                if take: nxt = here + 4 + (si << 2)
            elif op == 9: r[rt] = r[rs] + si
            elif op == 10: r[rt] = int(signed(r[rs]) < si)
            elif op == 11: r[rt] = int(r[rs] < (si & 0xffffffff))
            elif op == 12: r[rt] = r[rs] & imm
            elif op == 13: r[rt] = r[rs] | imm
            elif op == 14: r[rt] = r[rs] ^ imm
            elif op == 15: r[rt] = imm << 16
            elif op in (0x20, 0x21, 0x23, 0x24, 0x25, 0x28, 0x29, 0x2b):
                a = (r[rs] + si) & 0x1fffff
                if op in (0x20, 0x21, 0x23, 0x24, 0x25):
                    fmt = {0x20:'b', 0x21:'h', 0x23:'I', 0x24:'B', 0x25:'H'}[op]
                    r[rt] = struct.unpack_from('<' + fmt, self.memory, a)[0]
                else:
                    size = {0x28:1, 0x29:2, 0x2b:4}[op]
                    self.put(a, (r[rt] & ((1 << (8 * size)) - 1)).to_bytes(size, 'little'))
            else: raise ValueError(f'unsupported {w:08x} at {here:08x}')
            r = [v & 0xffffffff for v in r]
            r[0] = 0
        raise ValueError('instruction budget exhausted')


def initial_records(code, character_id, seed=0):
    """Execute game initializer; substitute seeded RNG outputs in legal ranges."""
    if not 1 <= character_id <= 12:
        raise ValueError('character ID must be 1..12')
    m = Machine(code, seed)
    m.run(0x8007a20c, (0x80100000, 0x80110000, character_id))
    allowed = [(0x100000, 0x100060), (0x110000, 0x1100d0), (0x1ef000, 0x1f0000)]
    if any(not any(lo <= a and a + n <= hi for lo, hi in allowed) for a, n in m.writes):
        raise ValueError('initializer wrote outside records/stack')
    return bytes(m.memory[0x100000:0x100060]), bytes(m.memory[0x110000:0x1100d0])
