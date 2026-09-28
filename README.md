# StarOcean2-SaveTools

PS1 memory-card save tools for **Star Ocean: The Second Story (US)**. Started as a format-ingestion
tool (bringing GME/VGS/DexDrive/raw card images into a usable form) and grew into full save-format
reverse engineering — there's no published spec for this format, so every field documented here was
found by diffing real save files, matching numbers against the game's own screens, or disassembling
the actual PS1 code that reads and writes it.

## What's solved

| Area | Status |
|---|---|
| Checksums, party list, character ID swaps | ✅ Verified |
| Level, HP, MP, STR/CON/AGL/DEX/INT | ✅ Verified (999 safe; 9999 unproven) |
| All 46 skill levels **and** all 46 skill names/order | ✅ Verified |
| SP (skill points) — every internal form, all 12 characters | ✅ Verified |
| Talents (all 10) | ✅ Verified |
| Item ID table, inventory counts for items already owned (max 20) | ✅ Verified |
| Giving a character an item type they've **never** owned before | ✅ Verified in-game (via `so2_inventory.py`) — Seraphic Garb 0→20 confirmed equipped and usable on save 15 — [details](docs/SO2-INVENTORY-ADD-INVESTIGATION.md) |
| Equipment — full 7-slot characters (incl. Noel, Chisato) | ✅ Verified |
| Equipment — compressed 6-slot (missing one accessory) | ✅ Verified |
| Fol (money) | ✅ Verified in-game (via `so2_fol.py` — see below) |
| Specialties (shop-bought Skill Shop tiers: Knowledge/Sensibility/Technique/Combat ×3 levels) | ✅ Verified — mechanism explained and full 12-tier bit table (`0x1A3F`/`0x1A40`) confirmed by executing the real purchase code; one clean live purchase would close out the last loose end — [details](docs/SO2-SPECIALTY-INVESTIGATION.md) |
| Adding/recruiting a party member | ✅ Verified in-game (via `so2_party.py`) — two parallel per-slot arrays, identity is a numeric ID not the name string — [details](docs/SO2-PARTY-MEMBER-INVESTIGATION.md) |
| Battle-ability quick-assignment slots (4 per character) | ✅ Mapped and disassembly-verified — decoded `0x56C-0x56F` per character, real candidate/read/write code executed against real saves — [details](docs/SO2-SPECIAL-ATTACK-LIST-CHECK.md) |
| Map position (X/Y/Z, facing, area ID + real scene selector) and area/scene → name lookup | ✅ Verified in-game — tool: `so2_location.py`. 8 areas / 24 sightings recorded, including all 13 floors of Cave of Trials plus 2 in-cave escape points — [details](docs/SO2-MAP-LOCATION-CHECK.md) |
| Same-area repositioning (teleport within your current area) | ✅ Verified in-game — first successful save-edit teleport in this project |
| Cross-area teleport | ✅ Verified in-game — copying position/area plus a newly-found 48-byte region (`0x1B58-0x1B88`) from a real reference save works; `so2_location.py teleport` implements it — [details](docs/SO2-MAP-LOCATION-CHECK.md) |
| Required disc (Disc 1 vs Disc 2) | ✅ Verified — decoded byte `0x4C` (0=Disc 1, 1=Disc 2), confirmed by executing the real disc-check code against both actual disc images — [details](docs/SO2-DISC-AND-PSYNARD-CHECK.md) |
| Psynard (flying mount) teleport | ✅ Verified in-game — editing its parking coordinates (`0x19B4-0x19D8`) moves it to the new spot, confirmed live twice — [details](docs/SO2-DISC-AND-PSYNARD-CHECK.md) |
| Options menu — all 8 settings (see table below) | ✅ Mapped and disassembly-verified — [details](docs/SO2-OPTIONS-MENU-INVESTIGATION.md) |
| The "stuck area ID" mystery | ✅ Resolved — decoded `0x1769` (long assumed to be a location ID) is actually a saved sprite drawing-order value; the real location selector is decoded `0x1762` ("scene"), confirmed by real code. `so2_location.py` uses scene throughout — [details](docs/SO2-MAP-LOCATION-CHECK.md#2026-09-27-disassembly-follow-up-0x1769-is-saved-drawing-order-not-an-area-id) |

### Menu settings — verified

Found by extracting the real Options overlay (disc archive entry 3016) and executing its actual
menu-construction, input-callback, and save-serializer code — not by diffing saves, which is why
three earlier attempts at this found nothing. All offsets are **decoded**, not raw card-block
offsets. In-game save/reload has not yet been tested for any of these.
**[Full evidence](docs/SO2-OPTIONS-MENU-INVESTIGATION.md)**

| Setting | Decoded offset | Values |
|---|---|---|
| Message speed | `0x1860` | u8 `0..7`, displayed `1..8` (fast → slow) |
| Sound output | `0x44` | `0` Surround, `1` Stereo, `2` Monaural |
| Message window color | `0x30` / `0x34` / `0x38` / `0x3C` | Four `0x00BBGGRR` words: UL, UR, LL, LR corners |
| Targeting mode | `0x49` | `2` Auto, `0` Semi-Auto, `1` Manual |
| Camera work | `0x4A` | `0` Normal, `1` Leader-Centered |
| Combat motion mode | `0x4B` | `0` button + direction icon, `1` direction icon only |
| Key customization | `0x00..0x0F` | Eight u16 button masks, one per assignable action |
| Vibration | `0x46` | `0` OFF, `1` ON |

Full byte-level reference, including every offset and the exact SP/equipment encoding rules:
**[docs/SAVE-FORMAT.md](docs/SAVE-FORMAT.md)**

**Game-mechanic reference docs** (fan-sourced, cross-validated against real saves/equip attempts
where noted — see each doc's own Status section): item restrictions
([weapons/armor/accessories](docs/SO2-ITEM-RESTRICTIONS.md)), [Skills](docs/SO2-SKILLS-FULL.md) and
their derived [Specialties](docs/SO2-SKILL-SPECIALTIES.md)/[Super Specialties](docs/SO2-SUPER-SPECIALTIES.md),
[Talents](docs/SO2-TALENTS.md), [Private Actions](docs/SO2-PRIVATE-ACTIONS.md),
[Emotional Levels](docs/SO2-EMOTIONAL-LEVELS.md), [story/precious items](docs/SO2-STORY-ITEMS.md),
[status ailment sources](docs/SO2-STATUS-AILMENT-SOURCES.md), [spells](docs/SO2-SPELLS.md), and
[Fun City](docs/SO2-FUN-CITY.md).

**2026-09-25 — important structural correction:** part of every save block (starting at `0x0380`) is
**zero-run compressed**, not raw bytes — `00 00 N` means "N+2 zero bytes." Earlier notes in this repo
describe fixed offsets and "01 &lt;value&gt; 00 00"-shaped records in that region; those were compression
artifacts, not real field boundaries, and don't generalize as raw-offset editing rules. The checksum
formula was also wrong (an old `[0x206,0x281)` byte-sum rule that only worked by coincidence on
late-game saves) and has been corrected in `so2_sign()`. Both were confirmed by disassembling the
actual PS1 game code — see
[docs/SO2-CHECKSUM-INVESTIGATION.md](docs/SO2-CHECKSUM-INVESTIGATION.md) and
[docs/SO2-FOL-INVESTIGATION.md](docs/SO2-FOL-INVESTIGATION.md). Any tool that edits inside the
compressed region must decode → edit → re-encode → re-sign (see `so2_fol.py` for the pattern) —
never poke raw bytes there directly.

## Ongoing tasks

"Disassembly" = disc image + disassembly + existing save files only, no emulator run required.
"In-game testing" = the result has to actually be booted and observed in-game to confirm it.

### Open items

Genuinely unresolved work — fully resolved items live in "What's solved" above, not here.

| Task | Status | Validation | Notes |
|---|---|---|---|
| **Map terrain / collision data** | **In progress — overworld traced to a quadtree streaming system; node layout/height output still open** | Disassembly + read-only extraction | Dungeon format solved: scene-to-archive rule, 88-byte triangle records, height formula. Overworld ("type 3") is a fundamentally different system: a 9-slot streaming cache of large decompressed chunks, each apparently holding a 16-level quadtree spatial structure (not a triangle list) — found by tracing the real tag dispatcher and its handlers. The quadtree's node byte layout and what value it actually returns (boolean walkability vs. a real height) were not decoded, so the area-0 height cross-check is still open. Real recorded overworld Y values are both near 0, suggestive of a flat/near-flat overworld but not proven — [details](docs/SO2-MAP-TERRAIN-INVESTIGATION.md) |
| **Map decoded chunks 1 (`0x000–0x1A0`) and 5 (`0x1748–0x1B88`) / story-event flags** | **Next up — recommended fresh disassembly target** | Disassembly | ~1,150 of the ~1,500 bytes across these two chunks are still completely unexamined; Options (`0x00..0x0F`, `0x30..0x3F`, `0x44`, `0x46`, `0x49..0x4B`, `0x1860`) is the only part mapped so far. Story/event flags were already ruled out of their old suspected raw-header location (`0x2B4–0x2E3` — confirmed to just be a party-stat mirror, [details](docs/SO2-STORY-FLAGS-HEADER-CHECK.md)) and haven't been searched for here yet. Picked as the next target because it's the single largest coherent unmapped region left, directly adjacent to fields already traced tonight (Options, map/position), and story flags would be high-value for save editing — [details](docs/SO2-STORY-FLAGS-HEADER-CHECK.md) |
| Private Actions / emotion levels / item-creation recipes | Pending | Disassembly (trace PA-trigger script opcodes) + light in-game confirmation | Fan-sourced only so far, never located in the save itself |
| Inventory word's bit-15 flag meaning | Pending | Disassembly (trace more callers) + minor in-game confirmation | Present on every add call; purpose not established |
| Party primary array — full byte-by-byte map | 69% mapped | Disassembly (done for now) | All 96 bytes covered; 66 named (ID/EXP/HP/MP/level/STR/CON/AGL/DEX/INT/GUTS), 12 are two unnamed stat triplets, 18 unresolved. Generic-accessor lead (selectors 1-17) and a whole-binary reader/writer scan both checked and ruled out for these bytes — [details](docs/SO2-PARTY-MEMBER-INVESTIGATION.md#primary-record-complete-byte-coverage-partial-semantic-map-2026-09-27). Revisit later to name the rest |
| Field-leader / walking-sprite slot — "can it be forced to a 3rd character?" | Genuinely inconclusive, on hold | Disassembly (48 real trials + overlay tracing) | The walking sprite is a fixed 0/1 protagonist flag from a global story-route byte (`0x19E8`), independent of party order and `0x41` — confirmed it's fixed to the route protagonist (Claude/Rena), not swappable by party order. A follow-up showed construction does NOT hard-branch into exactly 2 fixed graphics — the selector is stored as a generic field — but the real graphics-selection code (one of ~12 further reads of the same resident index) was not located, so whether a 3rd character (e.g. Dias) is reachable remains open — [details](docs/SO2-PARTY-MEMBER-INVESTIGATION.md) |

## Layout

```
saveconv.py, saveconv.bat    core library + launcher (double-click opens savemanager)
area_data.json                map/location database (so2_location.py's data)
scripts/                      every other user-facing tool (see table below)
tools/                        disassembly/evidence scripts behind each investigation doc
tests/                        unit tests (python -m pytest, from the repo root)
docs/                         investigation write-ups and the byte-level reference
```

## Tools

All of these live in `scripts/` and are run from the repo root, e.g. `python scripts/so2_fol.py ...`.

| File | What it does |
|---|---|
| `saveconv.py` *(repo root)* | Core library (checksums, card format detection/conversion) + a CLI: `convert`, `list`, `extract`, `import`. No arguments opens `scripts/savemanager.py`'s picker window. |
| `savemanager.py` | Two-card-side-by-side GUI: copy/move/rename/delete saves, import/export single saves, combine cards, convert formats, install as DuckStation's card 1/2. `python scripts/savemanager.py` |
| `so2_refill_sp.py` | Sets every character's SP to max, handling every internal encoding form. `python scripts/so2_refill_sp.py <slot> <box1> [box2]` — e.g. `python scripts/so2_refill_sp.py 1 1 2` |
| `so2_equip.py` | View/edit equipment. `python scripts/so2_equip.py show [box]` or `python scripts/so2_equip.py set <box> <Character> <slot> "<Item>"` |
| `so2_anatomy.py` | Labels every byte of one save block by confidence (verified/decoded/unknown) and writes a full map to disk. `python scripts/so2_anatomy.py [box]` |
| `so2_coverage.py` | Static knowledge map of the decoded save state — what fraction is mapped/partial/runtime/unknown, region by region. `python scripts/so2_coverage.py` |
| `so2_fol.py` | Sets Fol (money) through the real zero-run codec — decodes the compressed state, edits the value, re-encodes, re-signs. `python scripts/so2_fol.py <card> --save S13 --fol 5000 --out <new card>` (writes a new card file; never overwrites the source) |
| `so2_party.py` | Adds/recruits a party member into a genuinely empty slot pair by executing the game's own initializer code (both the primary and secondary arrays, correctly paired). `python scripts/so2_party.py <card> --save S15 --id 9 --out <new card>` (id is the character ID, 1-12; writes a new card file) |
| `so2_inventory.py` | Gives a character an item type they've never owned before (or tops up one they have) by executing the game's actual add-item routine — the only correct way to create a brand-new inventory entry. `python scripts/so2_inventory.py <card> --save S15 --id 364 --count 20 --out <new card>` (count is an increment; writes a new card file) |
| `so2_location.py` | Reads/records/names map locations and teleports between recorded ones. `python scripts/so2_location.py show [box]`, `name`, `list`, `map`, `map-html`, `teleport` — see the script's own docstring for full usage. |

## Usage notes

- **Close DuckStation before writing any card** — it rewrites the card file on exit and will clobber your changes.
- These tools always back up a card before writing to it.
- After any manual edit, both checksums must be recomputed (`so2_sign()` in `saveconv.py` does this automatically in every tool above).
- Character identity inside a save is tracked by the name string embedded in each entry, not by slot position — characters can be freely reordered between party slots.

## Card formats supported

| Ext | Format |
|---|---|
| `.mcd` `.mcr` `.mc` `.mem` `.bin` `.srm` `.ps1` | Raw 131,072-byte card image |
| `.gme` | DexDrive |
| `.vgs` | Virtual Game Station |
| `.vmp` | PSP virtual card (read-only — writing needs Sony signing keys) |
| `.mcs` | Single save (128-byte directory frame + block) |
