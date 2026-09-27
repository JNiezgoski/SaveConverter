"""Execute extracted skill-shop commit bytecode through the real MIPS interpreter.

No source saves are written. This isolates the successful confirmation tail;
dialogue, affordability and already-owned checks are not simulated game input.
"""
from pathlib import Path
import hashlib
import json
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import saveconv
import so2_fol
from tools.so2_party_mips import Machine

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/so2-specialty/verified'
CODE = ROOT / 'artifacts/so2-fol/disc-code/code-2576-lba-30736.bin'
SCRIPT = ROOT / 'artifacts/so2-specialty/disc-code/script-3207-part-1137c-lba-38691.bin'
SKILLS = ROOT / 'artifacts/so2-specialty/disc-code/code-3014-lba-36286.bin'
CARD = ROOT / 'artifacts/so2-fol/fol-5000-candidate.mcd'
CAPTURED = ROOT / 'artifacts/so2-specialty/S15.decoded'
sha = lambda d: hashlib.sha256(d).hexdigest()
u32 = lambda d, o: struct.unpack_from('<I', d, o)[0]


def commit(code, script, decoded, flag, price):
    m = Machine(code)
    state, flags, ctx, frame, stack, variables, bytecode = (
        0x80100000, 0x80110000, 0x80120000, 0x80130000,
        0x80140000, 0x80150000, 0x80160000)
    def word(a, v): m.put(a, struct.pack('<I', v))
    m.put(state, decoded[:0x1a0])
    m.put(flags, decoded[0x19e8:0x1b58])
    m.put(bytecode, script)
    word(0x80075270, state)
    word(0x80075704, flags)
    word(0x80075708, variables)
    word(ctx+0x10, bytecode+0x4ca4)
    word(ctx+0x18, frame)
    word(ctx+0x24, stack)
    word(frame-4, flag)
    word(frame-8, price)
    executed = []
    def start(m, r):
        r[17], r[19], r[20], r[23] = ctx, 0x7fffff, 0x800000, 1
        r[31] = 0x8006c358
    def boundary(m, r):
        pc = u32(m.memory, (ctx+0x10) & 0x1fffff)
        executed.append(hex(pc-bytecode))
        r[31] = 0x800ff000 if pc == bytecode+0x4cc8 else 0x8006c358
    m.writes.clear()
    m.run(0x800ff004, hooks={0x800ff004: start, 0x8006bb0c: boundary})
    after = bytearray(decoded)
    after[:0x1a0] = m.memory[0x100000:0x1001a0]
    after[0x19e8:0x1b58] = m.memory[0x110000:0x110170]
    expected = bytearray(decoded)
    expected[0x19e8+flag//8] |= 1 << (flag % 8)
    struct.pack_into('<I', expected, 0x18, u32(decoded, 0x18)-price)
    assert after == expected
    allowed = [(0x100018, 0x10001c), (0x110000+flag//8, 0x110001+flag//8),
               (0x120000, 0x121200), (0x12fff8, 0x130000),
               (0x140000, 0x140100), (0x150000, 0x150004),
               (0x1ef000, 0x1f0000), (0, 4)]  # scratchpad alias in bounded harness
    assert all(any(lo <= a and a+n <= hi for lo, hi in allowed) for a,n in m.writes)
    return {'flag': hex(flag), 'price': price, 'before': decoded[0x1a3f:0x1a41].hex(),
            'after': after[0x1a3f:0x1a41].hex(), 'fol_before': u32(decoded,24),
            'fol_after': u32(after,24), 'bytecode_boundaries': executed,
            'changes': [hex(i) for i,(a,b) in enumerate(zip(decoded,after)) if a != b]}


def main():
    OUT.mkdir(exist_ok=True)
    code, script, skills = CODE.read_bytes(), SCRIPT.read_bytes(), SKILLS.read_bytes()
    assert sha(script) == '30923618f001a29e257b02fa06762e16a16c7542fa90d42a821b4018dadc5ce8'
    assert sha(skills) == '3e345c0ab652387a23c3a8da259f3372a6c8ef6adaa0d793d36d0fdf4bc86c53'
    _, card = saveconv.load_card(CARD)
    first, order = next((f,o) for f,o in saveconv.chains(card) if f['name'].endswith('S13'))
    block = card[order[0]*8192:(order[0]+1)*8192]
    assert saveconv.so2_valid(block)
    decoded = so2_fol.state(block)
    rows = []
    for flag in range(0x2bc,0x2c8):
        # Read actual repeated shop initialization records, not a guessed cost table.
        hits = [i for i in range(0x4d00,0x5468,4)
                if u32(script,i) == flag and u32(script,i-4) >> 24 == 0x21]
        prices = {u32(script,i+4) & 0xffffff for i in hits}
        assert len(prices) == 1
        price = prices.pop()
        index = flag-0x2bc
        rows.append({'name': f'{("Knowledge","Sensibility","Technique","Combat")[index%4]} {index//4+1}',
                     'flag': hex(flag), 'offset': hex(0x19e8+flag//8), 'bit': flag%8,
                     'price': price, 'script_flag_offsets': [hex(i) for i in hits],
                     'skill_ids_one_based': list(skills[0x3168+index*5:0x316d+index*5])})
    results = [commit(code,script,decoded,int(row['flag'],16),row['price']) for row in rows]
    # Also expose each bit from a controlled copy with all twelve flags cleared.
    clear = bytearray(decoded)
    clear[0x1a3f] &= 15
    clear[0x1a40] = 0
    controls = [commit(code,script,clear,int(row['flag'],16),row['price']) for row in rows]
    captured = CAPTURED.read_bytes()
    captured_runs = [commit(code,script,captured,int(row['flag'],16),row['price']) for row in rows]
    anomaly = bytearray(decoded)
    anomaly[0x1a40] = 3
    anomaly_runs = [commit(code,script,anomaly,f,1600) for f in (0x2c1,0x2c2)]
    report = {'sources': [{'path':str(p.relative_to(ROOT)), 'size':p.stat().st_size,
                           'sha256':sha(p.read_bytes())} for p in (CODE,SCRIPT,SKILLS,CARD,CAPTURED)],
              'save':first['name'], 'block_sha256':sha(block), 'decoded_sha256':sha(decoded),
              'rows':rows, 'fol_candidate_runs':results, 'captured_real_save_runs':captured_runs,
              'controlled_cleared_runs':controls, 'controlled_anomaly_runs':anomaly_runs,
              'scope':'Real MIPS execution of successful commit tail 0x4ca4..0x4cc8; no UI hooks or game-load claim.'}
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    import capstone
    md=capstone.Cs(capstone.CS_ARCH_MIPS,capstone.CS_MODE_MIPS32|capstone.CS_MODE_LITTLE_ENDIAN)
    listing=[]
    for lo,hi in [(0x80055ecc,0x80055f38),(0x80056090,0x8005613c),
                  (0x8006241c,0x80062478),(0x80063f1c,0x80063fc8),
                  (0x8006c358,0x8006c39c),(0x8006cd48,0x8006cf64)]:
        listing.extend(f'{i.address:08x} {i.bytes.hex()} {i.mnemonic} {i.op_str}'
                       for i in md.disasm(code[lo-0x8002f810:hi-0x8002f810],lo))
    listing.extend(f'{o:04x} {u32(script,o):08x}' for o in range(0x4c0c,0x4cf8,4))
    listing.append('# Entry 3014 skill availability check and raw five-byte groups')
    listing.extend(f'{i.address:08x} {i.bytes.hex()} {i.mnemonic} {i.op_str}'
                   for i in md.disasm(skills[0x6bc:0x740],0x8007e6bc))
    listing.extend(f'{0x80081168+5*i:08x} {skills[0x3168+5*i:0x316d+5*i].hex(" ")}' for i in range(12))
    listing.append('# Script tier initialization words (flag and following cost)')
    for row in rows:
        o=int(row['script_flag_offsets'][0],16)
        listing.append(f'{o:04x} {u32(script,o):08x} {u32(script,o+4):08x}')
    (OUT/'evidence.asm').write_text('\n'.join(listing)+'\n')
    print('PASS: 12 captured real-save commits, 12 Fol-candidate commits, 14 controlled commits')


if __name__ == '__main__': main()
