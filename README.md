# SaveConverter

PS1 memory card / save-file tools, built primarily around reverse-engineering **Star Ocean: The
Second Story (US)**'s save format from scratch — there's no published spec for it. Every field
documented here was found by diffing real save files and matching numbers against the game's own
screens.

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
| Specialties (shop-bought Skill Shop tiers: Knowledge/Sensibility/Technique/Combat ×3 levels) | ✅ Verified — mechanism explained and full 12-tier bit table confirmed by executing the real purchase code — [details](docs/SO2-SPECIALTY-INVESTIGATION.md) |
| Adding/recruiting a party member | ✅ Verified in-game (via `so2_party.py`) — two parallel per-slot arrays, identity is a numeric ID not the name string — [details](docs/SO2-PARTY-MEMBER-INVESTIGATION.md) |
| Battle-ability quick-assignment slots (4 per character) | ✅ Mapped and disassembly-verified — decoded `0x56C-0x56F` per character, real candidate/read/write code executed against real saves — [details](docs/SO2-SPECIAL-ATTACK-LIST-CHECK.md) |
| Map position (X/Y/Z, facing, area ID) and area-ID → name lookup | ✅ Verified in-game — tool: `so2_location.py`. Area 128 = Linga, confirmed by walking in and saving — [details](docs/SO2-MAP-LOCATION-CHECK.md) |
| Same-area repositioning (teleport within your current area) | ✅ Verified in-game — first successful save-edit teleport in this project |
| Cross-area teleport | ✅ Verified in-game — copying position/area plus a newly-found 48-byte region (`0x1B58-0x1B88`) from a real reference save works; `so2_location.py teleport` implements it — [details](docs/SO2-MAP-LOCATION-CHECK.md) |
| Required disc (Disc 1 vs Disc 2) | ✅ Verified — decoded byte `0x4C` (0=Disc 1, 1=Disc 2), confirmed by executing the real disc-check code against both actual disc images — [details](docs/SO2-DISC-AND-PSYNARD-CHECK.md) |
| Psynard (flying mount) teleport | ✅ Verified in-game — editing its parking coordinates (`0x19B4-0x19D8`) moves it to the new spot, confirmed live twice — [details](docs/SO2-DISC-AND-PSYNARD-CHECK.md) |
| Options menu — all 8 settings (see table below) | ✅ Mapped and disassembly-verified — [details](docs/SO2-OPTIONS-MENU-INVESTIGATION.md) |
| Story/event flags, recipes | ⚠️ Open — [Private Actions](docs/SO2-PRIVATE-ACTIONS.md) documented as a lead, not yet tested against a save |

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

### Not started

| Task | Status | Validation | Notes |
|---|---|---|---|
| **Map terrain / collision data** | **In progress — record format decoded, area-ID→archive-entry link still open** | Disassembly (large, separate effort) | The 88-byte terrain-triangle record format is understood field-by-field (bounding box, 3 vertices, plane-equation height interpolation, surface-type byte). A second pass traced one layer deeper: terrain is asset type 0 of a 13-type per-area dispatch table, backed by a 12-slot loaded-area cache (`[0x80075768]`) with a fallback "currently loading" pointer (`[0x80075738]`) — but the actual code that fills that pointer from area ID on a fresh load was not found; that generic pointer is referenced 40+ places, so isolating the real loader needs tracing forward from the area-transition code instead. No numeric cross-check performed yet — [details](docs/SO2-MAP-TERRAIN-INVESTIGATION.md) |
| Specialty Knowledge-vs-Sensibility bit mapping | Resolved | Disassembly (done) | All 12 shop tiers now have a confirmed bit table (`0x1A3F`/`0x1A40`), verified by executing the real purchase code — [details](docs/SO2-SPECIALTY-INVESTIGATION.md). The old "contradiction" was a mislabeled historical test, not a code bug; one clean live purchase would fully close out the last loose end |
| Field-leader / walking-sprite slot | Corrected — resident connection ruled out; "can it be forced to a 3rd character?" still open | Disassembly (48 real trials + new overlay tracing) | The on-foot sprite constructor uses a simple 0/1 protagonist flag derived from a global story-route byte (`0x19E8`), independent of party order and of `0x41` — confirmed across 3 saves × 4 party selections × 2 flag values × 2 modes. Practical answer to "can the walking sprite be any party member": no, not via this mechanism — it's fixed to the route protagonist (Claude/Rena). A follow-up traced the actual constructors (`80082E5C`/`8007E540`, found inside a previously-unlocated field-engine overlay) and showed construction does NOT hard-branch into 2 fixed graphics — the selector just gets stored as a generic field — but the real graphics-selection code (one of ~12 further reads of the same resident index elsewhere in that overlay) was not located. Genuinely inconclusive on "can it be a third character (e.g. Dias)" — [details](docs/SO2-PARTY-MEMBER-INVESTIGATION.md) |
| Map decoded chunks 1 (`0x000–0x1A0`) and 5 (`0x1748–0x1B88`) — remaining unmapped portions | Pending | Disassembly | Partially mapped: Options now located at decoded `0x00..0x0F`, `0x30..0x3F`, `0x44`, `0x46`, `0x49..0x4B`, and `0x1860` — [evidence](docs/SO2-OPTIONS-MENU-INVESTIGATION.md). Remaining bytes still need investigation; story flags remain a separate task |
| Story/event flags (raw header `0x2B4`–`0x2E3`) | Checked, ruled out as flags | Disassembly (done) | Turned out to be a raw mirror of party-stat data (load-screen/status cache), not a flags bitmap — [details](docs/SO2-STORY-FLAGS-HEADER-CHECK.md). Still open inside the unmapped decoded chunks above |
| Map/location — "stuck area ID" anomaly | Open | In-game tested | Deeper dungeon floors reached via the save-anywhere cheat all read the same (wrong) area ID instead of updating — leading theory is the cheat bypasses normal tracking where no real save point exists; unconfirmed — [details](docs/SO2-MAP-LOCATION-CHECK.md) |
| Private Actions / emotion levels / item-creation recipes | Pending | Disassembly (trace PA-trigger script opcodes) + light in-game confirmation | Fan-sourced only so far, never located in the save itself |
| Options: message speed, sound, window colors, targeting, camera work, combat motion, key customization, vibration | Resolved (field mappings); live confirmation open | Disassembly + bounded execution (done) | All eight are in the per-save decoded body; extracted Options overlay 3016 and its actual labels, executed menu writers and serializer/codec checks. Sound has three modes; targeting uses reordered stored values. No new in-game test — [evidence and limits](docs/SO2-OPTIONS-MENU-INVESTIGATION.md) |
| Inventory word's bit-15 flag meaning | Pending | Disassembly (trace more callers) + minor in-game confirmation | Present on every add call; purpose not established |
| Party primary array — full byte-by-byte map | 69% mapped | Disassembly (done for now) | All 96 bytes covered; 66 named (ID/EXP/HP/MP/level/STR/CON/AGL/DEX/INT/GUTS), 12 are two unnamed stat triplets, 18 unresolved. Generic-accessor lead (selectors 1-17) and a whole-binary reader/writer scan both checked and ruled out for these bytes — [details](docs/SO2-PARTY-MEMBER-INVESTIGATION.md#primary-record-complete-byte-coverage-partial-semantic-map-2026-09-27). Revisit later to name the rest |

## Tools

| File | What it does |
|---|---|
| `saveconv.py` | Core library (checksums, card format detection/conversion) + a CLI: `convert`, `list`, `extract`, `import`. No arguments opens a small picker window. |
| `savemanager.py` | Two-card-side-by-side GUI: copy/move/rename/delete saves, import/export single saves, combine cards, convert formats, install as DuckStation's card 1/2. `python savemanager.py` |
| `so2_refill_sp.py` | Sets every character's SP to max, handling every internal encoding form. `python so2_refill_sp.py <slot> <box1> [box2]` — e.g. `python so2_refill_sp.py 1 1 2` |
| `so2_equip.py` | View/edit equipment. `python so2_equip.py show [box]` or `python so2_equip.py set <box> <Character> <slot> "<Item>"` |
| `so2_anatomy.py` | Labels every byte of one save block by confidence (verified/decoded/unknown) and writes a full map to disk. `python so2_anatomy.py [box]` |
| `so2_fol.py` | Sets Fol (money) through the real zero-run codec — decodes the compressed state, edits the value, re-encodes, re-signs. `python so2_fol.py <card> --save S13 --fol 5000 --out <new card>` (writes a new card file; never overwrites the source) |
| `so2_party.py` | Adds/recruits a party member into a genuinely empty slot pair by executing the game's own initializer code (both the primary and secondary arrays, correctly paired). `python so2_party.py <card> --save S15 --id 9 --out <new card>` (id is the character ID, 1-12; writes a new card file) |
| `so2_inventory.py` | Gives a character an item type they've never owned before (or tops up one they have) by executing the game's actual add-item routine — the only correct way to create a brand-new inventory entry. `python so2_inventory.py <card> --save S15 --id 364 --count 20 --out <new card>` (count is an increment; writes a new card file) |

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
