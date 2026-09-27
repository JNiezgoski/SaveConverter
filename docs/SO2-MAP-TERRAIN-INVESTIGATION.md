# SO2 map terrain / collision: real record format found, per-area archive entry still open

Investigation: **2026-09-27**. US PS1 BASCUS-94421/SCUS-94421 (Disc 1). Continues
from the field-leader follow-up's side finding (see
[SO2-PARTY-MEMBER-INVESTIGATION.md](SO2-PARTY-MEMBER-INVESTIGATION.md), "side
finding worth flagging separately"), which located and extracted the
field/movement-engine overlay containing real terrain code. This is not in the
save file at all — it is per-area data loaded from the disc.

**Status: real progress, genuinely partial, across two passes.** The
terrain-triangle record format is understood field-by-field from actual
executed-instruction evidence. The resident RAM structures that hold a
loaded area's terrain are identified, and a second pass traced one layer
deeper: terrain is confirmed as asset type 0 of a 13-type per-area dispatch
table, backed by a 12-slot loaded-area cache. What is **still not** found:
which disc archive entry supplies terrain data for any specific area, or how
area ID ultimately selects it — that link sits one level deeper still, in
whatever populates the cache/current-area-table on an actual fresh load, not
yet located. No numeric cross-check against a known real save position was
possible either pass for that reason — see "What's still open" and the
2026-09-27 second-pass section below.

All source material: `artifacts/so2-field-control/field-overlay-full.asm`
(the field-engine overlay, functions below) and
`artifacts/so2-options-menu/resident.asm` (always-resident code, loader
function). No new extraction was performed; both were already on disk from
prior investigations. No card was read or written. This is disassembly
tracing only — nothing was executed in an interpreter/harness, unlike most
of this project's other "Verified" claims. Treat everything here as
**disassembly-derived, not execution-verified.**

## 1. Resident terrain-view globals

Three RAM globals hold the currently-loaded area's terrain:

| Global | Meaning |
|---|---|
| `[80075330]` | Raw pointer to the loaded terrain resource's header (call it `R`) |
| `[80075338]` (`TB`) | `R + *(R+0x80)` — base address of the resource's actual data section |
| `[80075334]` (`T`) | `TB + 4` — a convenience alias, 4 bytes into the same data |

Both `T` and `TB` are read throughout the field-engine overlay (over 40 call
sites reference `0x5334`/`0x5338`); none of those sites write them. The only
write site found is in the always-resident loader below.

## 2. The loader

Found in the always-resident code, roughly `8004AD9C..8004AF94`
(addresses per `artifacts/so2-options-menu/resident.asm`, which happens to
contain a full resident disassembly from an earlier investigation):

```text
8004ADA4 jal   80012154       ; fetch sub-chunk N of resource s4
8004ADA8 move  s2,zero
...
8004ADC4 jal   800121a8       ; load/decompress that sub-chunk
8004ADC8 addiu s3,s5,0x10
...                            ; loop: s2 = 0,1,2,... fetching further sub-chunks
8004AE68 lw    v0,4(s5)
8004AE70 beqz  v0,8004af24
...                            ; one more sub-chunk fetched conditionally
8004AF14 jal   80020e5c        ; cleanup / commit call
8004AF34 lw    a0,5260(a0)
8004AF38 jal   80012154        ; final fetch, a2=0
8004AF54 sw    a2,5330(at)     ; R = returned pointer
8004AF64 lw    v0,5330(v0)     ; v0 = R
8004AF6C lw    v1,0x80(v0)     ; v1 = *(R+0x80)
8004AF7C sw    v0,5338(at)     ; TB = R + v1 (already added at 8004AF78)
8004AF88 sw    v0,5334(at)     ; T  = TB + 4 (v0 already +4'd at 8004AF84)
```

`80012154`/`800121a8` are the same generic two-step resource-fetch pair used
elsewhere in this codebase (paired the same way the Options overlay fetches
its separate text/font resource — see
[SO2-OPTIONS-MENU-INVESTIGATION.md](SO2-OPTIONS-MENU-INVESTIGATION.md)).
`[80075260]` is the resource-manager context pointer passed as `a0` to both
calls; `s4` is a resource-selector value whose origin (a specific archive
entry number, or something computed from the area ID) was **not traced back
further in this pass** — this loader loads *several* indexed sub-chunks
before assembling `R`, consistent with one per-area archive entry bundling
terrain together with other per-area assets (scripts, layout, etc.), not a
terrain-only entry. Finding what feeds `s4` for a specific area is the
concrete next step.

## 3. Terrain header (relative to `TB`)

| Offset from `TB` | Field |
|---|---|
| `+0x20` (u16) | Number of triangle records |
| `+0x5C` (u32) | Byte offset from `TB` to the start of the triangle-record array |

Read at `80083660..80083678` (point-in-cell search) and confirmed at
`800838a4..800838c8` (a second, similar walk in a neighboring function).

## 4. Triangle record (88 / `0x58` bytes each)

Traced from two real functions: the point-in-cell test `80083c3c` (full
bounding-box + 2D cross-product polygon test) and the height-interpolation
function `80083944`/its caller `80083628`.

| Offset | Field | Evidence |
|---|---|---|
| `+0x00` (i16) | Y-range low bound | `80083c50` compared against object Y `[obj+4]` |
| `+0x02` (i16) | Y-range high bound | `80083c64` |
| `+0x04` (i16) | AABB corner0 X (grid units) | `80083c84` vs `worldX>>12` |
| `+0x06` (i16) | AABB corner0 Z | `80083cac` vs `worldZ>>12` |
| `+0x08` (i16) | AABB corner1 X | `80083c98` |
| `+0x0A` (i16) | AABB corner1 Z | `80083cc0` |
| `+0x0C` (u8) | Enabled/valid flag — 0 skips this record entirely | `80083c3c` entry check |
| `+0x0D..0x0F` | Unidentified; `+0x0F` is read by the caller (`80083c3c`'s caller in `80083628` at `800837e0`) as a "has neighbor/apply surface" gate | not fully traced |
| `+0x10/+0x12/+0x14` (i16 each) | Vertex 0: X, Y, Z | height formula's reference vertex; also point-in-cell's first polygon vertex |
| `+0x18/+0x1A/+0x1C` (i16 each) | Vertex 1: X, Y, Z | point-in-cell polygon vertex 2; Y used in the height clamp loop |
| `+0x20/+0x22/+0x24` (i16 each) | Vertex 2: X, Y, Z | point-in-cell polygon vertex 3; Y used in the height clamp loop |
| `+0x28..0x2F` | Unidentified (8 bytes) | not traced — candidate: a 4th vertex/normal, or neighbor-record convenience data |
| `+0x30` (i32) | Plane coefficient A | `80083714` `mult` |
| `+0x34` (i32) | Plane coefficient B (also the height-formula divisor) | `80083754` `div` |
| `+0x38` (i32) | Plane coefficient C | `80083730` `mult` |
| `+0x3C..0x53` | Unidentified (24 bytes) | not traced this pass — plausible neighbor-triangle links for the search walk, unconfirmed |
| `+0x54` (u8) | Surface/footstep-type ID | `80083814..8008381c`, conditionally copied into the moving object's current-surface field |
| `+0x55..0x57` | Unidentified (3 bytes) | not traced, likely padding |

Only 3 vertices (0x10, 0x18, 0x20) plus a separate AABB corner pair are
identified — this is a **triangle**, not a quad, despite the record's 88-byte
size leaving room for a 4th vertex-sized block at `+0x28` that was not
resolved.

**Height interpolation** (`80083628` calling `80083944`'s surrounding logic,
real instructions at `80083704..80083760`): given object world X (`[obj+0]`)
and Z (`[obj+8]`), and the matched triangle's vertex 0 and plane coefficients:

```text
height = Y0 - (A*(worldX - X0*4096) + C*(worldZ - Z0*4096)) / B
```

(sign convention derived from the real subtract/negate/divide sequence, not
independently re-derived by a second method — treat the overall shape of the
formula as solid, individual signs as likely-but-unconfirmed). The result is
written to `[obj+4]`, then clamped between the min and max Y of the triangle's
three real corners (a real min/max loop over `+0x12/+0x1A/+0x22`) before being
used, and finally compared against the record's own `+0x00/+0x02` fast-reject
Y range from the bounding check.

## 5. Coordinate scale (confirmed cross-reference)

Terrain vertex coordinates are small `i16` grid integers. The interpolation
code shifts them left by 12 bits (`sll ..., 0xc`, i.e. `× 4096`) before
comparing against the object's position fields — the **same 20.12
fixed-point scale already established for the save's own position fields**
(decoded `0x1750` X / `0x1754` Y / `0x1758` Z — see
[SO2-MAP-LOCATION-CHECK.md](SO2-MAP-LOCATION-CHECK.md)). This is a genuine,
useful confirmation: terrain geometry is authored on a coarse integer grid
(1 grid unit = 1.0 world unit = 4096 raw units), while the player's live
position is sub-unit precise on top of that grid.

## What's still open

- **The archive entry (or entries) supplying terrain data for any specific
  area, and how area ID selects it, was not found.** The loader fetches
  several sub-chunks by an opaque selector `s4`; tracing `s4`'s origin back
  to the area-ID field (decoded `0x1769`) is the direct next step, and was
  explicitly out of scope for what this pass could finish.
- **No numeric cross-check was performed.** The plan was to decode one real
  area's triangle array and sanity-check it against a known player Y from an
  existing archived save (e.g. `area_data.json`'s recorded sightings). That
  requires the archive-entry mapping above, so it could not be done this
  pass — this is the natural verification step once that mapping exists.
- **Fields `+0x0D-0x0F`, `+0x28-0x2F`, and `+0x3C-0x53`** (34 of the 88 bytes)
  are unidentified. The `+0x3C-0x53` block is large enough to plausibly hold
  neighbor-triangle pointers/indices for the search-and-walk pattern typical
  of navmesh-style terrain, but this is a guess, not a traced finding.
- **The point-in-cell search itself (`80083628`'s outer loop) is a linear
  scan of every triangle in the area**, not a spatial index — fine for
  understanding the format, but worth knowing if a future pass wants to
  reason about performance or ordering assumptions.
- No emulator was run and no interpreter/harness executed any of this code;
  everything above is static tracing of real, extracted instructions, one
  level less verified than this project's usual "executed and asserted"
  standard.

## 2026-09-27 second pass: traced one layer deeper into `s4`, mapping still open

**Real, concrete progress; the area-ID → archive-entry link is still not
found.** This chases exactly the "still open" item above. All addresses are
from `artifacts/so2-options-menu/resident.asm` (always-resident code) unless
noted; nothing new was extracted, and this is disassembly tracing only — no
interpreter/harness execution, same caveat as the rest of this document.

**Terrain is confirmed as asset type 0 of 13.** The area asset-table dispatch
jump table lives in RAM data at `[0x80072f8c]` (read directly from the
already-extracted `artifacts/so2-options-menu/ram-disc1.bin` at file offset
`0x72f8c`, 13 consecutive `u32` pointers):

```text
type 0  -> 8004ad94   (terrain loader, this document's subject)
type 1  -> 8004afdc
type 2  -> 8004b0a8
type 3  -> 8004b0c0
type 4  -> 8004b278
type 5  -> 8004b104
type 6  -> 8004b14c
type 7  -> 8004b194
type 8  -> 8004b194   (shares a handler with 7, 9, 10)
type 9  -> 8004b194
type 10 -> 8004b194
type 11 -> 8004b1d4
type 12 -> 8004b21c
```

This dispatch is reached at `8004AD6C..8004AD90` in the loader function
(`8004ACA0`): it walks a per-area asset table `s7` (element stride 8 bytes:
`+4` = type index, checked `< 0xD`; `+8` = a byte offset added to `s7` to
locate that type's own data blob, called `s4` in the prior pass) and jumps to
`jump_table[type*4]` for each present entry. `s4` is therefore **not an
archive index at all — it's a pointer into the current area's already-loaded
asset bundle**, and the fetch calls (`80012154`/`800121a8`) that follow are
pulling sub-chunks out of that already-resident bundle, not hitting the disc
directly at this point. The real disc-archive selection happens earlier,
when that bundle itself is loaded.

**Traced the asset-table source one more level up: a 12-slot loaded-area
cache.** `8004ACD8`'s call to `80056ACC(a0=area_selector, a1=&stack_temp,
a2=0)` is a linear search (real disassembly at `80056ACC..80056B40`) over a
fixed 12-entry table at `[80075768]`, stride `0x14` (20) bytes per entry:

| Entry offset | Field | Evidence |
|---|---|---|
| `+0x00` (u8) | Active/loaded flag — 0 skips the slot | `80056AE4/AEC` |
| `+0x08` (u32) | Cache key, compared equal to the search input | `80056AF4/AFC` |
| `+0x0C` (u32) | A second stored value, returned via the caller's optional `a1` out-pointer | `80056B18/B20` |
| `+0x10` (u32) | The cached asset-table pointer, always the function's return value on a hit | `80056B24` |

If found (a matching, active slot), `8004ACA0` uses that slot's `+0x10`
pointer as `s7` directly — this is a real "already loaded, reuse it" fast
path for revisiting an area, consistent with adjacent-area caching. If not
found, it falls back to `s7 = [80075738]`, a separate global that must hold
the asset table for whichever area is *currently* being freshly loaded from
disc.

**Where the trail goes cold.** Locating the code that fills `[80075738]` (or
a fresh slot in the `[80075768]` cache) on an actual cache miss — the point
where a real disc archive-entry number must be chosen from the area
ID — was not completed this pass. `[80075738]` is written and read from
dozens of places throughout the resident code (over 40 references), and is
evidently a generic "current context" pointer reused across multiple
subsystems, not a narrowly-scoped variable that makes the real load site
easy to isolate by reference count alone; distinguishing the real "fresh
area load" writer from the rest needs tracing forward from the
already-documented area-transition code in
[SO2-MAP-LOCATION-CHECK.md](SO2-MAP-LOCATION-CHECK.md) (the teleport-ranges
work), not backward from this generic pointer.

**Traced the cache-search's own caller one level further, inconclusively.**
`8004ACA0` (this whole loader) is called from exactly one site,
`80055008` (`jal 0x8004aca0`, `a1 = s0`), where `s0` comes from
`lh $s0, 0x2c($sp)` — a halfword loaded from that caller's own stack frame,
strongly suggestive of an area/room identifier but **not confirmed identical
to decoded save byte `0x1769`** in this pass; that caller function itself
starts well before the traced region and was not walked back to its own
entry point or its caller.

**Data-quality note for the eventual cross-check.** `area_data.json`'s
currently recorded live sightings are almost all at or extremely near local
origin (X/Z within ~0.2, Y = 0.0) for every area except the overworld (area
0) — likely because these were recorded right at a fresh area-entry spawn
point rather than a distinctive mid-room position. This isn't enough
positional variation to meaningfully distinguish one decoded triangle from
another once real per-area terrain data can be decoded. A future pass either
needs a live sighting recorded from a distinctive, deliberately-chosen
position inside a specific area, or should use area 0's overworld sightings
(which do have real non-trivial X/Z) for the first real cross-check attempt.

**Net effect on next steps:** the concrete next action is still "trace the
area-ID → archive-entry link," but it is now known to live specifically in
whatever writes `[80075738]` or a `[80075768]` slot on a genuine fresh load —
not in the per-area asset-table dispatch itself, which is now fully
understood and is not the missing piece.
