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

## 2026-09-27 follow-up: real position fields found, likely coarse not free-roam

Triggered by the field-leader investigation's discovery that `0x80051A34`
writes 20.12 fixed-point coordinates into `[0x80075710]` — the confirmed
source of decoded chunk 5's first `0x2A0` bytes (see above). This follow-up
disassembled resident entry 2576 more broadly to answer: is `[0x80075710]`
a live, continuously-updated position, or something set once per area entry?

**Tooling note:** capstone's `disasm()` silently stops at the first
undecodable word instead of skipping it, which is fatal for a binary mixing
code with jump tables/data — a naive linear sweep from the entry point
covers only `4166` instructions out of `75998` actually present and never
reaches most of the functions below. The correct approach restarts
disassembly at the next 4-byte word whenever the stream stops. Script:
`artifacts/so2-party/field_leader_scan6.py`. Anyone repeating a full-binary
disassembly on this file should use this pattern, not a single `md.disasm()`
call from the base address.

### Real, meaningful values in existing saves

Decoded offsets `0x1750/0x1754/0x1758` (chunk-5-relative `+8/+0xC/+0x10`,
signed 32-bit each), read directly from the current live card:

| Save | X | Y | Z | Facing (`+0x18` u16) | Sub (`+0x21` byte) | Area (`+0x24` byte) |
|---|---:|---:|---:|---:|---:|---:|
| S01 (Crawd LV255) | 81194 | -258 | 23907 | 1718 | 0 | 0 |
| S02 (Rena LV255) | 9062 | -152 | 13021 | 1084 | 0 | 1 |
| S15 (Rena LV97, current) | -12 | 0 | 49 | 64520 | 128 | 1 |

These are not noise: S01/S02 have large-scale values consistent with an
outdoor/field-scale area, S15 has small near-origin values consistent with a
compact interior space, and the area/sub-index bytes differ meaningfully
between saves. This is strong circumstantial confirmation these are real,
live position fields, not padding or an unrelated counter.

### Multiple writers, all scripted, none found to be per-frame movement

A corrected full-binary scan (see tooling note) found **165** loads of
`[0x80075710]` into a register across resident entry 2576, far more than the
single warp handler previously known. Cross-referencing stores at `+8/+C/+10`
found at least four distinct write call sites, not one:

- `0x80051A34` (previously documented): area-entry handler, source table at
  `[0x80075360]` indexed by `[0x80075710]+0x24`, triggered from a story-script
  jump-table dispatcher rolling a 2-outcome RNG (`0x8006BD14`).
- `0x8004C654..0x8004C7B0`: a near-identical routine - same `+0x24`-indexed
  table lookup at `[0x80075360]`, same `sra ...,0xC` fixed-point conversion
  into `+8/+0xC/+0x10`, same halfword/byte writes at `+0x18/+0x21` - gated by
  a comparison against script state `[0x80076196]` and, immediately after,
  copies the just-set position into a *second* location (`+0x26C.."+0x29C`
  range) chosen by a different script-state check (`[0x570C]+0x68 == 1`).
  This copy-to-a-second-slot behavior is consistent with a start/end pair for
  a scripted camera pan or transition animation, not live player tracking.
- Two further write sites (`0x8004E370`, `0x80063A24`) with the same
  `+8/+0xC/+0x10(+0x14)` shape, not fully traced in this pass.

Every write site examined is reached through a story-script/event-state
gate or an area-ID table lookup - the shape of "place the player at area N's
entrance," not a per-frame physics/movement update. No controller-input read
(pad state check) was found immediately preceding any of these writes.
**No genuine continuous free-roam movement writer was found in resident
entry 2576.** If ordinary walking also updates `+8/+0xC/+0x10`, that code
was not located here and most likely lives in a field-movement/rendering
overlay that has not been extracted in any pass so far (the same scope
boundary the field-leader investigation's "+0x41 consumer" search hit).

### Conclusion

**Upgraded from inconclusive to a real, positive, but qualified finding.**
The save very likely encodes *a* location - specifically, wherever the
player was last placed by a scripted area-entry/transition, not a live,
constantly-updated free-roam coordinate. This is enough to plausibly support
an entrance-to-entrance "teleport to area N" edit (write the target area's
table-driven values, or directly overwrite `+8/+0xC/+0x10/+0x18/+0x21/+0x24`
with another valid area's observed values) but **not** enough to support
placing the player at an arbitrary mid-room point with confidence, since the
in-room live position (if tracked at all) may only exist in RAM state this
pass did not reach. No candidate save or tool was built in this pass -
recommended before any teleport tool: confirm by writing one save's
`+8/+0xC/+0x10/+0x18/+0x21/+0x24` bytes to exactly match another known save's
values (same six fields, nothing else) and testing whether the game places
the player at that area correctly on load. No such live test was performed
here.

Evidence scripts: `artifacts/so2-party/field_leader_scan5.py` (initial,
flawed scan - kept for the record) and
`artifacts/so2-party/field_leader_scan6.py` (corrected full-binary scan).
No source save or card under `C:/CodeTesting/StarOcean2/SaveGames` was
modified; only the existing live card was read (not written) to pull the
table above.

## 2026-09-27 follow-up: area table structure confirmed (194 entries), no name strings found

Attempted to build a real area-ID → zone-name table from the game's own
data, to answer "what is each zone" now that the area ID field (decoded
`0x176C`, byte) and its coordinate-table lookup are known. Reused the
corrected full-binary capstone sweep (see the tooling note above);
disassembled all `75998` instructions of resident entry 2576 fresh for
this pass, one level deeper than the prior follow-up went.

**Table structure, confirmed with a third independent write site.** All
three area-entry code paths found so far follow the identical pattern:

```text
lbu   v0, 0x24(state)     ; area ID byte (decoded 0x176C)
sll   v0, v0, 2           ; index * 4 (pointer-sized entries)
lui   at, 0x8007
addu  at, at, v0
lw    a2, 0x5360(at)      ; entry = table[area_id]  -- a POINTER, not raw data
lw    v0, 0(a2)           ; X  (20.12 fixed-point, >> 12 elsewhere)
lw    v1, 4(a2)           ; Y
lw    a0, 8(a2)           ; Z
lw    a1, 0xc(a2)         ; (unused/4th word in the two handlers checked)
lh    v0, 0x20(a2)        ; facing, -> state+0x18
lhu   v0, 0x22(a2)        ; sub-index, -> state+0x21
```

So `0x80075360` is a fixed **194-entry array of pointers**, each pointing
to a small per-area struct (X/Y/Z + facing + sub-index) - this is the
game's own internal "area entrance definitions" table, not raw coordinate
data packed inline. The count is not a guess: the third site,
`0x8003df64` (a story-script opcode handler reading its area-ID argument
from the script byte-stream at `s2+0x2a2`, the same stream-position
pattern used by every other opcode argument reader in this engine),
explicitly bounds-checks it with **`sltiu v0,a0,0xc2`** (194) before using
it as the same index into `0x80075360` - confirmed by instruction-level
dump of `0x8003df3c..0x8003dfb0`. An out-of-range ID branches away instead
of dereferencing a garbage pointer. **Valid area IDs: 0..193.**

Other reference-scale check: a broad substring search on `0x5360(` across
the whole disassembly returned 150+ hits, almost all `lui $at,0x8007` /
`... 0x5360($at)` pairs at completely unrelated call sites throughout the
binary - meaning this table is a heavily-used, central piece of game
state (looked up from dozens of places), not a narrow one-off table. That
volume made a blind "grep every reference" approach useless; the three
sites analyzed here were selected because their surrounding code was
already tied to the known `state+0x24` area-ID field specifically.

**No area/zone name strings were found.** Searched printable-ASCII runs
(4+ chars) in the three most relevant already-extracted, commonly-loaded
files - resident entry 2576 (all 313,340 bytes), menu/status overlay 2982,
and shared UI overlay 2985. Found character names (Claude/Rena/Celine/...),
debug strings ("Memory ok", "DEBUG", "USP"), and status-screen labels
("ATK HIT MAG", "GUTS STM LUC CRT"...) - **no town, dungeon, or region name
text anywhere in these three files.** This means either: (a) a name table
exists but is not global - each area's own overlay/resource carries its own
name text, loaded only when that specific area is entered (plausible: the
area-entry handler at `0x80051A34` explicitly loads a numbered resource,
`addiu a1,zero,0x851`, right before the position lookup - a per-area
resource load is exactly the kind of place a per-area name would travel
with it), or (b) this game does not display a persistent on-screen
location-name label at all (some PS1-era RPGs don't), and "what zone am I
in" is conveyed to the player only through the map/background art itself,
never as text pulled from a save-adjacent table. Neither was distinguished
in this pass.

**Conclusion: partial, not the requested deliverable.** A complete,
instruction-verified list of *numeric* area IDs (0-193) is now established,
with the confirmed struct layout for each entry's position/facing data -
this is real, useful, and load-bearing for any future "warp to area N"
tool. A *named* area-ID → zone-name table was not recovered; that would
require extracting and searching the individual per-area overlays (dozens
of them, well beyond a bounded pass) or confirming the game has no such
label at all. Do not fabricate zone names by number or by guessing from
external wiki content - if named areas are wanted later, the next step is
either (1) picking a handful of per-area overlays via `tools/so2_disc_code.py`
and checking each for adjacent name text near its own resource data, or
(2) a live test: visit a known, identifiable location, save, read its area
ID byte directly, and build the table empirically one entry at a time
against real, confirmed locations - the same "change one thing, read the
byte" method this project has used from the start.

Evidence script: `artifacts/so2-party/area_name_scan1.py` through
`area_name_scan5.py`. No source save or card under
`C:/CodeTesting/StarOcean2/SaveGames` was modified.

## 2026-09-27 follow-up: targeted per-area overlay sample, no names found

Enumerated the full SO2.BIN archive via `archive_table()` (`tools/so2_disc_code.py`):
**4,155 total entries**, sizes ranging `2,048`..`53,309,440` bytes, median `26,624` -
far too many to search blindly, and evidently spanning every asset type in the
game (code, graphics, audio, video), not just area overlays.

Rather than guess by size/LBA heuristics, used the one piece of direct evidence
already in hand: the area-entry handler `0x80051A34` (see the prior follow-up)
loads a specific numbered resource immediately before its position-table
lookup - `addiu a1,zero,0x851` (decimal `2129`). Archive index `2129` exists
(`LBA 24323`, decoded size `381,148` bytes) and was extracted along with its
two sequential neighbors, `2130` (decoded `60,984` bytes) and `2131` (decoded
`14,672` bytes), as a 3-entry sample directly tied to this evidence rather
than a heuristic guess.

**Result: no text in any of the three.** A 4+ character printable-ASCII scan
of all three decoded files found only palette/tile-pattern noise (repeating
runs like `"""""` , `2333333"""` , `$!( ` characteristic of indexed-color
bitmap or tilemap data, not text) - no words, no place names, nothing
resembling the character-name/debug-string/stat-label text found in the
previously-checked resident/menu/UI files. This is consistent with resource
`0x851` being **graphics data** (background art or a tileset) for that area,
not a text-bearing structure.

One caveat not resolved here: it is not proven that "resource ID" `0x851` in
this call is a direct 1:1 index into the same `archive_table()` numbering
`so2_disc_code.py` exposes - it was treated as such because the value existed
in that table at a plausible size, but a translation layer between "resource
ID" and raw archive index (analogous to the established `0x80012108` tag
lookup used elsewhere, though that mechanism is documented as a narrow
16-tag lookup and does not obviously generalize to hundreds of assets) was
not ruled out or confirmed in this pass.

**Conclusion: sample exhausted, no names found, do not escalate to a blind
sweep.** Per scope, no broader search of the remaining ~4,150 archive entries
was attempted. Honest next steps, in order of promise:
1. Confirm whether `0x851` truly is a direct `archive_table()` index (trace
   the resource-ID-to-archive-index resolution path itself, if one exists,
   before trusting further "resource N" citations as archive indices).
2. If per-area name text exists at all, it more likely travels with a
   *text/dialogue* overlay for that area (distinct from its graphics
   resource) - the same area-entry code path likely loads more than one
   resource per area entry; only the one graphics load was traced here.
3. The live-test alternative remains fully available and arguably cheaper
   than further disassembly: visit a known location, save, read the area-ID
   byte (decoded `0x176C`) directly, and build the ID-to-name table
   empirically, a handful of real data points at a time.

Evidence: extracted files in `artifacts/so2-party/map-name-sample/` (entries
2129-2131, decoded). No source save or card under
`C:/CodeTesting/StarOcean2/SaveGames` was modified.

## 2026-09-27 follow-up: `0x851` is NOT an archive index — prior premise corrected

Re-traced the area-entry handler `0x80051A34` in full (window
`0x800519D4..0x80051B94`, entry 2576, corrected full-binary sweep per the
tooling note above) looking for a second, text-bearing resource load beside
the already-known `addiu a1,zero,0x851` call. Only **one** such call exists
in this function:

```text
80051a6c lui   a0,0x8007
80051a70 lw    a0,0x525c(a0)   ; a0 = [0x8007525c] (an object/list pointer)
80051a74 jal   0x80011b98
80051a78 addiu a1,zero,0x851
80051a7c jal   0x800130ec       ; consumes v0 (0x80011b98's return)
80051a80 move  a0,v0
...
80051a90 sw    v0,0x5350(at)    ; result cached at [0x80075350]
```

**Correction to the prior follow-up's premise.** `0x80011b98` was assumed to
be "the resource loader" and `0x851` its archive index. Disassembling
`0x80011b98` itself is not possible from entry 2576 - the address is *below*
this file's load base (`0x8002F810`), so it belongs to a different, lower
resident module (most likely the base executable payload at `0x80010000`,
per the Fol investigation's sources table) not extracted in this pass; an
earlier attempt to dump it here mistakenly read the start of entry 2576
itself and must be disregarded. Found a second, in-range call site for
`0x80011b98` instead, at `0x80038FC4` (inside `0x80038F68`, itself called
from `0x80038EEC`/`0x80038F38`): there, the second argument is built by
`sll/sra $a1,$a1,0x10` (sign-extending a caller-supplied 16-bit value) and
packed alongside other caller arguments into a small on-stack struct
(`sh`/`sh`/`sw` triple at `sp+0x10/0x12/0x14`, shaped like a position/flags
record) before the call. **This is a UI/object registration or layout
dispatch pattern, not "load asset N from the disc archive."** `0x851`
(2129) is therefore not shown to be an `archive_table()` index at all - it
is more likely a UI element, sprite, or registered-object ID local to
whatever subsystem `0x80011b98` dispatches into. The prior follow-up's
extraction of raw archive entry `2129` (which happened to decode as
graphics/tile noise) is not invalidated as a *fact about that archive
entry*, but its relevance to resource `0x851` was never actually
established - treat that "no text in entry 2129-2131" result as
uninformative about zone names, not as a real negative.

**No second resource-ID-style call was found in the other known write-site
handler either.** Re-checked `0x8004C654..0x8004C7B0` (the "near-identical
routine" with the start/end position-copy behavior) end to end: it only
manipulates `[0x80075710]`/`[0x8007570C]`/`[0x80075704]` state and the same
`0x5360` area table - no `addiu a1,zero,<N>` / resource-dispatch call
pattern anywhere in it.

**Conclusion: the specific narrow lead this pass targeted (a second resource
load near the known area-entry code) does not exist in either traced
handler, and the one resource-ID-shaped call that does exist (`0x851` to
`0x80011b98`) is now shown to likely not be an archive lookup at all.**
This closes out disassembly-based name hunting via this particular thread.
Per the standing recommendation, do not escalate to a blind sweep of the
remaining ~4,150 archive entries. **Live-testing (visit a known location,
read decoded `0x176C` directly, build the ID-to-name table empirically) is
now the clearly most efficient remaining path** - not a fallback, the
right next step. If disassembly is revisited later, first identify the
*actual* archive-loading function (something that takes a value bounds-
checked against a real `archive_table()`-sized count and reads disc
sectors, analogous to the confirmed `0x8006241C`/`0x8007359C` script-opcode
jump table or the `0x8003df64` bounds-check pattern already validated for
the position table) rather than trusting a `jal` target's name/assumed role
without disassembling it directly.

## 2026-09-27 follow-up: static full-table extraction is not possible — table is runtime-populated BSS

Attempted to dump all 194 area-entrance structs directly from the static
resident binary (`artifacts/so2-fol/disc-code/code-2576-lba-30736.bin`,
load `0x8002F810`), on the assumption that `0x80075360`'s 194-pointer
array is compiled-in constant data. **That assumption is wrong.**

Read the table directly at its file offset (`0x80075360 - 0x8002F810 =
0x45B50`, confirmed in-range and confirmed the load-address arithmetic
against a known-good disassembly at `0x80051A34` first): **all 194
pointers are zero.** This is a BSS region - reserved, zero-initialized
space in the executable, populated by game code at runtime as areas are
actually visited, not a lookup table baked into the disc image.

Checked the two existing RAM dumps in `artifacts/so2-fol/` for comparison:
`ram.bin` has **2/194** entries populated (only index 1, plus a null
consumed as one of the two); `SCUS-94422_resume.ram` also has **only
index 1** populated. Both sessions had only visited a handful of areas
before the dump was taken. Index 1's struct in the resume dump
(X=9062.00, Y=-152.00, Z=13021.00, facing=1080) matches the previously-
documented S02 save values almost exactly (X=9062, Y=-152, Z=13021,
facing=1084) - strong independent confirmation the struct layout is
correct, and that "area 1" is a consistent, stable identifier.

**Conclusion: a complete 194-entry coordinate table cannot be extracted
statically or from any single RAM snapshot - only whichever areas that
specific play session actually visited get populated.** No JSON of "all
194 coordinates" exists or can exist from a static/single-snapshot source.
The only ways to grow real coverage: (1) dump RAM after a session that
visited many areas (more areas visited = more populated slots, still
capped by what that playthrough touched), or (2) the already-standing
live-testing plan (visit a location, save, read `so2_location.py`'s
output) - which additionally gives area ID -> name correspondence,
which a raw RAM table dump alone never would.

New tool: `tools/so2_dump_area_table.py <ram_image>` - reads whatever
entries are actually populated in a given RAM dump and prints their real
coordinates; reusable for future partial captures, but cannot exceed
what that session visited.

Evidence: inline analysis only, no new script artifacts beyond the tool
above. No source save or card under `C:/CodeTesting/StarOcean2/SaveGames`
was modified; the two existing RAM dumps were read, not altered.

Evidence: `artifacts/so2-party/area_name_scan6.py` (handler window dump),
`area_name_scan7.py` (initial, address-confusion misfire - kept for the
record with its bug noted), `area_name_scan8.py` (corrected trace of the
real in-range `0x80011b98` caller at `0x80038F68`). No source save or card
under `C:/CodeTesting/StarOcean2/SaveGames` was modified.

## 2026-09-27: first live confirmation — area IDs verified in-game, and a real teleport-edit result

Card slot 2 was used as a dedicated live-testing card (disposable, backed up
before every write). The user played and saved at six real, known locations,
each read with the new `so2_location.py` tool:

| Save | Real location (user-confirmed) | Area | Sub | Notes |
|---|---|---:|---:|---|
| S01 | Hoffman area | 0 | 1 | pos (20.78, -0.10, 15.28) |
| S02 | en route, near Hoffman->Hilton boat | 0 | 1 | pos (22.79, -0.04, 14.95) |
| S03 | outside Hilton | 0 | 1 | pos (22.51, -0.04, 7.99) |
| S04 | outside Lacour | 0 | 1 | pos (25.35, -0.09, 6.16) |
| S05 | outside Linga | 0 | 1 | pos (22.05, -0.04, 3.35) |
| S06 | **inside** Linga (save-anywhere used to cross the trigger) | **128** | 1 | pos (-0.83, 0.00, -0.29) |

**Confirmed live: area ID does not change from ordinary walking, only from
crossing an actual scripted area-entry trigger.** S01-S05 span real,
substantial outdoor travel (Hoffman to Linga's outskirts) and all read as
area 0/sub 1 the whole way, with X/Z drifting smoothly and continuously
across saves — consistent with area 0 being one large connected
overworld/field zone, not per-town outdoor pockets. The moment the user
deliberately crossed into Linga itself (S06), the area ID immediately
changed to 128. This directly confirms the "scripted trigger, not per-frame
movement" conclusion from the earlier disassembly-only pass, now with real
gameplay evidence.

**Area 128 = Linga, confirmed.** Also notable: the user's actual real
progress save (S15, card slot 1) independently reads as area 128 too — S15
is currently sitting inside Linga. Both are now recorded with real names in
`area_data.json` via `so2_location.py name`.

### Teleport-edit test 1: cross-area (area 0 -> area 128) — FAILED

Took S01 (area 0, Hoffman), overwrote decoded `0x1750/54/58` (X/Y/Z),
`0x1760` (facing), `0x1769` (area ID), `0x176C` (sub-index) to exactly
match S06's recorded Linga-entrance values, re-encoded/signed, saved as a
new test box (S07, card slot 2), and loaded it in DuckStation.

**Result: black screen, but with area-0 (overworld) music still playing.**
The game did not crash outright, and evidently read *something* from the
new area ID, but rendered nothing and kept the old zone's audio. This
means area ID + position alone are **not sufficient** for a working
cross-area transition — some other state (near-certainly the current
background/tileset resource and the active BGM track ID, likely tracked in
the still-largely-unmapped chunk 1 or another unmapped region) must also be
kept in sync, and a legitimate in-game save never has this mismatch because
all of that state is already self-consistent at the moment a real save is
taken. Hand-editing only the known position fields produces a state the
game never naturally produces.

### Teleport-edit test 2: same-area reposition (area 0, new X/Z only) — SUCCEEDED

Took S05 (area 0, outside Linga), left area ID and sub-index untouched,
only moved X/Z back toward S01's recorded coordinates (same area, different
point within it), saved as a new test box (S08, card slot 2), loaded it.

**Result: loaded correctly, placing the character outside Hoffman on the
overworld** — exactly the intended new position, with (per the user) no
visible or audible problems. This is the first fully successful save-edit
teleport in this project.

### Open discrepancy: which byte is really "area ID" vs "sub-index"?

Earlier disassembly evidence in this doc states the 194-entry table lookup
uses `lbu v0,0x24(state)` — decoded `0x176C` — as the area-ID index, with
`0x1769` (`+0x21`) labeled sub-index. **Tonight's live data doesn't clearly
match that:** across all 6 real saves above, `0x1769` is what changed
exactly when crossing into Linga (`0 -> 128`), while `0x176C` stayed at `1`
for every single one, including inside Linga. Older test saves from earlier
in the project (not part of tonight's controlled walk) show the opposite
pattern — `0x176C` varying (0 vs 1) while `0x1769` stayed at 0 — so neither
byte is provably constant in general; this hasn't been cleanly isolated.

`so2_location.py` currently keys on `0x1769` as `area_id` and `0x176C` as
`sub_index`, because that's what produced a sensible, discriminating signal
tonight (matches the real Hoffman-to-Linga transition). This may not match
the disassembly-labeled `state+0x24`/`state+0x21` convention exactly — both
could be correct if different code paths order these fields differently, or
one of the two disassembly passes mislabeled which offset was which. Not
resolved here. If picked up again: visit a third, genuinely distinct area
and check whether `0x176C` changes too, and re-examine the exact
`lbu`/`lhu` instruction operands cited earlier against this tool's byte
offsets side by side.

### Conclusion

**Repositioning within an already-current area is confirmed safe and
working.** A tool that lets you jump to any other point already known
within your current area (or the overworld generally) is buildable today
with what's verified. **Cross-area teleportation remains unsolved** — it
requires finding and correctly setting whatever background/music/scene
state a real area transition also updates, which likely lives in the
unmapped chunk 1 region (still ~90% uncharacterized) or possibly another
resource-table mechanism analogous to the ones found for inventory/chunk 5.
The next concrete step for cross-area warps: trace exactly what changes
(in decoded chunk 1, or live state near `[0x80075270]`) during a *real*
scripted area transition — e.g. diff decoded state immediately before and
after actually walking through the Linga entrance trigger, now that a
`so2_location.py`-equipped live-test workflow exists to make that practical.

Test scripts: ad-hoc (not preserved as a permanent tool, since the exact
target values were test-specific); the reusable outputs of this session are
`so2_location.py`, `area_data.json`, and `so2_location.py map-html`. Backups
of card slot 2 before each edit: `cards/_backup/card2-before-warp-test-*.mcd`
and `cards/_backup/card2-before-reposition-test-*.mcd`. No file under
`C:/CodeTesting/StarOcean2/SaveGames` other than card slot 2 (explicitly
designated disposable/test by the user) was modified.

## 2026-09-27: three more real areas named; a "stuck area ID" anomaly found

Continued live-testing on card slot 2. Two more areas confirmed by walking
in and saving:

- **Area 118 = Cave of Trials** (also called Heraldic Ruins by the user,
  unconfirmed which name is official) — floor 1 entrance.
- **Area 148 = Love Alley** — floor 2 of the same dungeon.

Both are recorded in `area_data.json` alongside Overview Map (0) and Linga
(128).

**Anomaly:** saves made after descending to floors 3, 4, and 5 of the same
dungeon (three saves in a row, via the save-anywhere cheat) all read as
**area 128 (Linga)** instead of new, distinct area IDs — despite the user
confirming they only walked down stairs each time, never warped back to
town. Checked whether this is visible anywhere in the still-unmapped chunk 1
region by diffing all consecutive saves in this sequence: **no correlation
found** — chunk 1 changes identically (three mundane, already-documented
counters incrementing) whether the area ID updated correctly (floor 1->2)
or not (floor 2->3, 3->4, 4->5). This rules out chunk 1 as the explanation
for this specific symptom.

**Leading unconfirmed theory:** floors 1-2 may have been reached via a real
in-game save point, while floors 3-5 required the save-anywhere cheat
because no real save point exists that deep — and the cheat may bypass
whatever normal game logic refreshes this area-tracking field, instead
leaving it at its last real value (Linga, from before entering the dungeon).
Not confirmed; would need a controlled test (a real in-game save at a depth
where one exists, immediately compared to a cheat-forced save at the same
spot) to isolate cheat-artifact from genuine game behavior. Left open for a
future session.

No source save or card under `C:/CodeTesting/StarOcean2/SaveGames` other
than card slot 2 was modified. Ad-hoc analysis script, not preserved as a
permanent tool.
