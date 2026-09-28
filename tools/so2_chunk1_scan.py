"""Read-only candidate xref scan of existing SO2 disassembly (not a proof of reachability).

Run from repo root. Outputs ignored artifacts/so2-chunk1. S=[80075270] is the serializer-confirmed chunk-1 source. Bounded intraprocedural path exploration follows delay slots,
register copies, constant pointer adjustments and unknown indexed additions.
No inferred index is counted as a resolved byte. Calls kill caller-saved regs;
stack spills, indirect jumps and callee argument propagation are not modeled.
"""
from pathlib import Path
import hashlib
import json
import re
import argparse

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/so2-chunk1'
LINE = re.compile(r'^([0-9a-fA-F]{8}):?\s+(?:[0-9a-fA-F]{8}\s+)?(\S+)\s*(.*)$')
MEM = re.compile(r'(-?(?:0x[0-9a-f]+|\d+))?\((\$\w+)\)')
LOADS = {'lb', 'lbu', 'lh', 'lhu', 'lw', 'lwl', 'lwr'}
STORES = {'sb', 'sh', 'sw', 'swl', 'swr'}
KEEP = {'nop', 'mult', 'multu', 'div', 'divu', 'mthi', 'mtlo'}


def parse(path):
    result = {}
    for line in path.read_text().splitlines():
        m = LINE.match(line)
        if m:
            a, op, args = m.groups()
            result[int(a, 16)] = (op, [x.strip() for x in args.split(',')] if args else [], line)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-catalog', action='store_true', help='refresh docs/SO2-CHUNK1-XREFS.tsv')
    options = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    paths = [ROOT/'artifacts/so2-options-menu/resident.asm',
             ROOT/'artifacts/so2-field-control/field-overlay-full.asm',
             ROOT/'artifacts/so2-terrain-pass3/overworld.asm',
             ROOT/'artifacts/so2-options-menu/shared.asm']
    paths += sorted((ROOT/'artifacts/so2-options-menu').glob('entry-*.asm'))
    paths += sorted((ROOT/'artifacts/so2-specialty').glob('code-*.asm'))
    paths += sorted((ROOT/'artifacts/so2-specialty/disc-code').glob('code-*.asm'))
    paths += sorted((ROOT/'artifacts/so2-special-attack').glob('code-*.asm'))
    seen_sources, sources, rows, limits = set(), [], {}, []
    for path in paths:
        code = parse(path)
        digest = hashlib.sha256('\n'.join(f'{a:x} {op} {args}' for a, (op,args,_) in code.items()).encode()).hexdigest()
        if digest in seen_sources:
            continue
        seen_sources.add(digest)
        source = path.relative_to(ROOT).as_posix()
        seeds = []
        for pc, (op, args, _) in code.items():
            if op == 'jal' and args == ['0x80012108']:
                # Resource 2 is S; accept only a locally proven constant argument.
                for back in [pc+4] + list(range(pc-4, pc-36, -4)):
                    if back not in code:
                        break
                    bop, ba, _ = code[back]
                    if ba and ba[0] == '$a1' and bop not in STORES:
                        if bop == 'addiu' and ba[1:] == ['$zero', '2']:
                            seeds.append((pc+4, '$v0', 'S', 0, False))
                        break
                    if back < pc and bop in ('jal', 'jalr', 'jr', 'j'):
                        break
            if op != 'lw' or len(args) != 2:
                continue
            m = MEM.fullmatch(args[1])
            if not m or int(m[1] or '0', 0) not in (0x5270,):
                continue
            base = m[2]
            # Require the actual 8007 high-half producer, not an immediate match alone.
            for back in range(pc-4, pc-52, -4):
                if back not in code:
                    break
                bop, ba, _ = code[back]
                if ba and ba[0] == base and bop not in STORES and not bop.startswith('b'):
                    if bop == 'lui' and ba[1] == '0x8007':
                        glob = int(m[1],0)
                        seeds.append((pc, args[0], 'S', 0, False))
                    break
        sources.append(dict(path=source, normalized_sha256=digest, instructions=len(code), seeds=len(seeds)))
        for seed, reg, family, initial_offset, initial_indexed in seeds:
            todo = [(seed+4, {reg:(family,initial_offset,initial_indexed)}, frozenset())]
            visited = set()

            def step(pc, state):
                state = state.copy()
                if pc not in code:
                    return state
                op, args, line = code[pc]
                if op in LOADS | STORES and len(args)==2:
                    m = MEM.fullmatch(args[1])
                    if m and m[2] in state:
                        fam, off, dyn = state[m[2]]
                        off += int(m[1] or '0',0)
                        if dyn or 0 <= off < 0x1a0:
                            key = (source,pc,fam,off,dyn)
                            rows[key] = dict(source=source, address=f'{pc:08X}', base=fam,
                                offset=off, indexed=dyn, access='R' if op in LOADS else 'W',
                                instruction=line, seed=f'{seed:08X}')
                if op=='move':
                    value = state.get(args[1])
                elif op in ('addiu','addi') and args[1] in state:
                    fam,off,dyn=state[args[1]]
                    value=(fam,off+int(args[2],0),dyn)
                elif op in ('addu','or') and len(args)==3 and (args[1] in state or args[2] in state):
                    src = args[1] if args[1] in state else args[2]
                    other = args[2] if src==args[1] else args[1]
                    fam,off,dyn=state[src]
                    value=(fam,off,dyn or other!='$zero')
                else:
                    value=None
                if args and op not in STORES|KEEP and not op.startswith('b') and op not in ('j','jr','jal','jalr'):
                    state.pop(args[0],None)
                    if value is not None:
                        state[args[0]]=value
                return state

            while todo and len(visited)<5000:
                pc,state,trail=todo.pop()
                key=(pc,tuple(sorted(state.items())))
                if pc not in code or not state or key in visited:
                    continue
                visited.add(key)
                op,args,_=code[pc]
                control=op in ('j','jr','jal','jalr') or op.startswith('b') and op not in ('break',)
                if control:
                    state=step(pc+4,state)
                    if op in ('jal','jalr'):
                        state={r:v for r,v in state.items() if r.startswith('$s') and r!='$sp' or r=='$fp'}
                        todo.append((pc+8,state,trail))
                    elif op=='jr':
                        pass
                    else:
                        try:
                            target=int(args[-1],0)
                            # Stop back edges: output loop sites once; bounds require manual tracing.
                            edge=(pc,target)
                            if target>pc:
                                todo.append((target,state,trail|{edge} if target<=pc else trail))
                        except ValueError:
                            pass
                        if op!='j' and op!='b':
                            todo.append((pc+8,state,trail))
                else:
                    todo.append((pc+4,step(pc,state),trail))
            if todo:
                limits.append(dict(source=source,seed=f'{seed:08X}',reason='5000 states'))
    records=sorted(rows.values(),key=lambda r:(r['base'],r['indexed'],r['offset'],r['source'],r['address']))
    (OUT/'sites.json').write_text(json.dumps(dict(sources=sources,limits=limits,sites=records),indent=2)+'\n')
    lines=['source\taddress\tbase\toffset\tindexed\taccess\tinstruction']
    lines += ['\t'.join((r['source'],r['address'],r['base'],hex(r['offset']),str(r['indexed']),r['access'],r['instruction'])) for r in records]
    (OUT/'sites.tsv').write_text('\n'.join(lines)+'\n')
    contexts=[]
    cache={}
    for r in records:
        if r['source'] not in cache:
            cache[r['source']]=parse(ROOT/r['source'])
        code=cache[r['source']]; pc=int(r['address'],16)
        contexts.append(f"\n# {r['source']} {r['base']}+{r['offset']:x} indexed={r['indexed']} {r['access']}")
        contexts += [code[a][2] for a in range(pc-24,pc+36,4) if a in code]
    (OUT/'contexts.txt').write_text('\n'.join(contexts)+'\n')
    if options.write_catalog:
        catalog=['source\taddress\tbase\toffset_expression\taccess\twidth\treview\tinstruction']
        for r in records:
            pc=int(r['address'],16)
            op=cache[r['source']][pc][0]
            off=r['offset']
            roles = {
                0x10:'clock/60 snapshot and preview; entry 2982 writer',
                0x14:'increment/add-with-zero-floor counter; preview/script reader',
                0x18:'prior Fol mapping', 0x1c:'script return only; meaning unresolved',
                0x20:'unconditional menu-operation increment; script reader',
                0x24:'save-preparation increment; script reader',
                0x28:'menu-operation increment conditional on object+B2; script reader',
                0x2c:'script return only; meaning unresolved',
                0x40:'menu selection import/commit; visible meaning unresolved',
                0x41:'prior validated party-slot lead; not walking-sprite proof',
                0x42:'rename selector 0 differs from Crawd',
                0x43:'rename selector 1 differs from Rena',
                0x45:'route initialization / lead-ID preview selector',
                0x47:'UI stack argument / Options writer; meaning unresolved',
                0x48:'UI stack argument / Options writer; meaning unresolved',
                0x4d:'local update flag store; consumer unresolved',
                0x4e:'script byte store; consumer unresolved',
                0x54:'clock throttle: clock > marker+60; store clock',
                0x178:'script result / compare 1 for F+244 increment; compare 2 for field return',
                0x181:'script operand byte / transition clear; meaning unresolved',
                0x182:'script operand byte / transition clear; meaning unresolved',
                0x184:'stat-selector-1 signed percentage modifier',
                0x186:'stat-selector-2 signed percentage modifier',
                0x198:'save-menu remembered selection word / zero sentinel / position+1',
                0x19c:'second save-menu remembered selection word',
            }
            review=roles.get(off,'located lead; meaning unresolved')
            if off < 0x10 or off in (0x30,0x34,0x38,0x3c,0x44,0x46,0x49,0x4a,0x4b,0x4c):
                review='previously mapped Options/disc; no new byte credit'
            if off in (0x58,0xe8):
                review='pair-value matrix A' if off==0x58 else 'pair-value matrix B'
                review+='; script clamp / getter, matrix sum, ranking or overlay update (see mapping doc)'
            if 0x188 <= off < 0x198:
                review='modifier setter/adjustment; affected mechanic unresolved'
            if r['indexed']:
                review+='; indexed expression requires manual bounds'

            width='pair endpoint' if op in ('lwl','lwr','swl','swr') else str(4 if op in ('lw','sw') else 2 if op in ('lh','lhu','sh') else 1)
            expr=f'{off:#x}'+('+unknown_index' if r['indexed'] else '')
            catalog.append('\t'.join((r['source'],r['address'],r['base'],expr,r['access'],width,review,r['instruction'])))
        (ROOT/'docs/SO2-CHUNK1-XREFS.tsv').write_text('\n'.join(catalog)+'\n')
    print(json.dumps(dict(sources=len(sources),seeds=sum(s['seeds'] for s in sources),sites=len(records),limits=limits,
        fixed_offsets={f:sorted({hex(r['offset']) for r in records if r['base']==f and not r['indexed']}) for f in ('S',)}),indent=2))


if __name__=='__main__':
    main()
