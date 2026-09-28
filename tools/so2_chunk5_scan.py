"""Read-only candidate xref scan of existing SO2 disassembly (not a proof of reachability).

Run from repo root. Outputs ignored artifacts/so2-chunk5. F and G are distinct
live pointers. Bounded intraprocedural path exploration follows delay slots,
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
OUT = ROOT / 'artifacts/so2-chunk5'
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
    parser.add_argument('--write-catalog', action='store_true', help='refresh docs/SO2-CHUNK5-XREFS.tsv')
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
            if op == 'jal' and args == ['0x80055f78']:
                seeds.append((pc+4, '$v0', 'F', 0x28, True))
            if op != 'lw' or len(args) != 2:
                continue
            m = MEM.fullmatch(args[1])
            if not m or int(m[1] or '0', 0) not in (0x5710, 0x5704, 0x56fc):
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
                        seeds.append((pc, args[0], 'G' if glob==0x5704 else 'F', -0x220 if glob==0x56fc else 0, False))
                    break
        if source.endswith('/resident.asm'):
            # Manually traced initializer: s0 is resource 9; F = resource 9 + 220.
            seeds.append((0x8005EA7C, '$s0', 'F', -0x220, False))
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
                        if dyn or 0 <= off < (0x440 if fam=='F' else 0x170):
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
        catalog=['source\taddress\tbase\toffset_expression\taccess\twidth\treview']
        for r in records:
            pc=int(r['address'],16)
            op=cache[r['source']][pc][0]
            off=r['offset']
            if r['base']=='G':
                review='bitmap access; individual bit meanings mostly unresolved'
            elif r['indexed']:
                review='indexed candidate; see manual array bounds and limitations in mapping doc'
            elif 0x28<=off<0x118:
                review='character-name storage'
            elif off in (0x244,0x248,0x24a,0x24c):
                review='operational counter; player-facing name unresolved'
            elif 0x250<=off<0x264 or off==0x294:
                review='deferred item delivery'
            elif off in (0x268,0x28a,0x298,0x29c):
                review='object-14 constructor parameters'
            elif off in (0x27c,0x27e):
                review='mount-bank drawing order'
            elif off in (8,12,16,24,26,33,36,0x118,0x26c,0x270,0x274,0x278,0x28c,0x290):
                review='previously mapped field; see existing investigations'
            elif off==0x1e:
                review='saved scene-view parameter; exact axis unresolved'
            else:
                review='located only; meaning unresolved (see mapping doc)'
            if r['source'].endswith('/resident.asm') and any(lo<=pc<hi for lo,hi in (
                (0x8004DB20,0x8004DC28),(0x8004DC38,0x8004DC64),
                (0x8004DEBC,0x8004DFF0),(0x80055FF8,0x8005612C))):
                review='bulk snapshot/restore; first iteration only; no semantic coverage credit'
            width='pair endpoint' if op in ('lwl','lwr','swl','swr') else str(4 if op in ('lw','sw') else 2 if op in ('lh','lhu','sh') else 1)
            expr=f'{off:#x}'+('+unknown_index' if r['indexed'] else '')
            catalog.append('\t'.join((r['source'],r['address'],r['base'],expr,r['access'],width,review)))
        (ROOT/'docs/SO2-CHUNK5-XREFS.tsv').write_text('\n'.join(catalog)+'\n')
    print(json.dumps(dict(sources=len(sources),seeds=sum(s['seeds'] for s in sources),sites=len(records),limits=limits,
        fixed_offsets={f:sorted({hex(r['offset']) for r in records if r['base']==f and not r['indexed']}) for f in ('F','G')}),indent=2))


if __name__=='__main__':
    main()
