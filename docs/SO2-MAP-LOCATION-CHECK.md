# SO2 map/location: bounded save-writer check

Investigation date: 2026-09-26. US PS1, SCUS-94421 / BASCUS-94421.

## Finding

**No field was positively identified as current map ID, room/area ID, or
live coordinates in this pass. The answer remains inconclusive, not “the
save contains no position.”** The continued serializer trace accounts for
all five body copies and the remaining header stores. It establishes their
source pointers, but does not establish location semantics for the unknown
parts of those allocations. No safe teleport edit is supported.

One additional source relationship is concrete: before constructing the
save, the writer stages `0x2A0` bytes from `[0x80075710]` and `0x170` bytes
from `[0x80075704]` into resource E, which becomes the fifth decoded chunk.
These are not individually identified map/coordinate fields.

## Sources and conventions

Reused [Fol](SO2-FOL-INVESTIGATION.md),
[checksum](SO2-CHECKSUM-INVESTIGATION.md),
[story-flags header check](SO2-STORY-FLAGS-HEADER-CHECK.md), and the
[inventory serializer trace](SO2-INVENTORY-ADD-INVESTIGATION.md).
No new extraction, RAM dump, or save comparison was needed.

| Existing extract in `artifacts/so2-fol/disc-code/` | Disc LBA | Load address |
|---|---:|---|
| `code-2998-lba-36213.bin` | 36213 | `0x8007E000` |
| `code-2576-lba-30736.bin` | 30736 | `0x8002F810` |

Both are compressed entries of SO2.BIN (ISO LBA 300). Rechecked SHA256:

```text
2998 f56ace2f46ff6c3d886e5f372a1e8f41db9da1d3667e65c4afb9189ddc3d9186
2576 6dec3950348b57068a85759f472ea7d5c92241d28b00ff4ea139ddd8dc1587cf
```

Instruction addresses below refer to these loaded entries. Subtract the
load address to locate bytes in an extracted file, not on disc; e.g.
`80081BC8` is entry-2998 offset `3BC8`, and `80055FC8` is entry-2576
offset `267B8`. The established byte-copy helper `80023ED0` belongs to
`SCUS_944.21;1`, LBA 24 (payload LBA 25, load `80010000`); its listing is
in the story-flags check. `B` means whole save-block base,
`S=[80075270]`, `D` means temporary decoded buffer. Ranges are half-open.
Listings are selected instructions with intentional gaps; delay slots execute.

## Linear continuation: sources and destinations

At `800817E4`, the writer copies `S+[1A0,2A0)` to raw `B+[280,380)`.
Then `800817F0` sets `a1=0` (save), and `800817F4/F8` calls `80081A70`
with `a2=B+380`. Its complete body layout is:

| Decoded range | Source on save / destination on load | Copy call | Interpretation supported here or by prior work |
|---|---|---|---|
| `[000,1A0)` | `S` | `80081AEC` | General state; Fol at `18`; not fully interpreted |
| `[1A0,4A0)` | `[8007527C]`, length `300` | `80081B0C` | Eight primary character records, stride `60` |
| `[4A0,B20)` | `[80075280]`, length `680` | `80081B28` | Eight secondary character records, stride `D0` |
| `[B20,1748)` | `[80075278]`, length `C28` | `80081B74` | Inventory, recent list, runtime cache; prior inventory note |
| `[1748,1B88)` | Resource E from table `[80075258]`, length `440` | `80081BC8` | Staged live regions below; remaining semantics unknown |

Character-array meanings come from the
[party investigation](SO2-PARTY-MEMBER-INVESTIGATION.md). They do not
identify every byte of either array. The last copy and end of serializer:

```text
80081BA4 addiu s1,zero,0x440
80081BA8 lui   a0,0x8007
80081BAC lw    a0,0x5258(a0)
80081BB0 jal   0x80012108       ; resource lookup, established convention
80081BB4 addiu a1,zero,0xE
80081BBC move  a1,s5           ; direction flag
80081BC0 move  a2,s2           ; D+1748
80081BC4 move  a3,v0           ; resource E pointer
80081BC8 jal   0x80081C38
80081BCC sw    s1,0x10(sp)     ; length 440
80081BD0 addiu s2,s2,0x440
80081BD4 bnez  s5,0x80081BF8   ; load skips encoding
80081BD8 subu  s1,s2,fp        ; assembled length 1B88
80081BE0 move  a1,s7           ; B+380
80081BE4 move  a2,s4           ; D
80081BE8 jal   0x80081EF4       ; established zero-run encoder
80081BEC move  a3,s1
80081BF8 jal   0x8001FD70       ; free temporary buffer
80081BFC move  a0,s4
```

There is no sixth copy before the return at `80081C30`. Direction helper
`80081C40..60` chooses `(destination,source)=(D,live)` when flag zero,
`(live,D)` otherwise, then calls `80023ED0`. Load calls the serializer
with flag 1 at `80081A40..48`, after restoring the raw 256-byte range at
`80081A24..38`. Thus the unknown body bytes really are restored to RAM;
this alone does not show that they place the player.

## Fifth-chunk staging source

Writer entry `80080FF8` calls resident `80055FC8`. That helper resolves
resource E and returns without copying if its pointer is null. Otherwise:

```text
80055FD0 lw    a0,0x5258(a0)
80055FD8 jal   0x80012108
80055FDC addiu a1,zero,0xE
80055FE0 move  t0,v0           ; E
80055FF0 lw    a2,0x5710(a2)   ; first live source
80056004 move  a3,t0           ; destination E
80056060 addiu t1,a2,0x2A0     ; aligned path's source end
80056064 lw    v0,0(a2)
80056074 sw    v0,0(a3)        ; also copies words +4,+8,+C
80056084 addiu a2,a2,0x10
80056088 bne   a2,t1,0x80056064
8005608C addiu a3,a3,0x10
80056094 lw    a2,0x5704(a2)   ; second live source
80056098 addiu a3,t0,0x2A0
800560A8 addiu t0,a2,0x170     ; branch delay slot, also aligned path
80056100 lw    v0,0(a2)
80056110 sw    v0,0(a3)        ; also copies words +4,+8,+C
80056120 addiu a2,a2,0x10
80056124 bne   a2,t0,0x80056100
80056128 addiu a3,a3,0x10
```

The unaligned paths at `80056008..54` and `800560AC..F4` copy the same
lengths using `lwl/lwr/swl/swr`. Consequently decoded `[1748,19E8)` comes
from `[80075710]+[0,2A0)`, and `[19E8,1B58)` from
`[80075704]+[0,170)`. The remaining `[1B58,1B88)` is copied from E but
not populated by this helper. No field in these ranges was assigned a
location meaning, nor was a player-placement consumer established.

## Remaining header stores and chunk-1 check

With `s2=B+200`, the writer's stores resolve as follows:

| Raw destination | Source / instruction evidence |
|---|---|
| `21C`, `220` (words) | `S+10`, `S+14`; loads/stores `80081738..4C` |
| `[224,234)` | Four words `S+[30,40)`; loop `80081750..68` |
| `[234,254)` | Eight character-preview calls `80081774..94` to `80081E24` |
| `254` (word) | `[80082D18]+1`; `800817A0..B4` |
| `258`, `25C` (words) | Stack `+10/+14`; `800817C8..D4` |
| `[280,380)` | `S+[1A0,2A0)`; `800817D8..E8` |

The stack's eight bytes are zeroed at `8008103C..4C`, then supplied as
output to `80038858` at `80081094`, with source
`[80075280]+slot*D0+24` (`80081084..98`). They are character-derived,
not evidence of coordinates merely because there are two words.
`800817B8..C4` also increments `S+24`, saved through chunk 1; it is not
an extra header coordinate store. Following the serializer, `80081800..34`
writes length/checksums, and `80081838..5C` updates the I/O context,
not another live-state copy into B.

Inspected direct `lw ...,5270(...)` contexts in resident entry 2576 and
entry 2998, including chunk-1 halfword getters/setters `80033B08..80033C70`,
indexed byte accesses `8006584C..800659CC`, and the header-source contexts
above. These give access widths and indexing, but no demonstrated map or
placement meaning. Numeric pairs or small IDs alone are insufficient.
This was a bounded static inspection, not exhaustive pointer/alias analysis.

## Limits

The old raw-byte movement comparison predates compression-aware analysis;
its absent signal does not rule out saved position. Likewise, the old
“variable-length discovered areas list” interpretation is not independently
established by this trace. No live test, broader overlay extraction, or
mapping of unrelated state was attempted. Unknown portions of chunk 1,
the raw copied range, and resource E remain open. There is no demonstrated
teleport field or sufficiently understood editor candidate from this pass.

Only this note and the Map/location open item were changed. No writes were
made under `C:/CodeTesting/StarOcean2/SaveGames`.
