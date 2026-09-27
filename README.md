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
| Giving a character an item type they've **never** owned before | ✅ Solved via actual game-code execution (`so2_inventory.py`) — [details](docs/SO2-INVENTORY-ADD-INVESTIGATION.md) |
| Equipment — full 7-slot characters (incl. Noel, Chisato) | ✅ Verified |
| Equipment — compressed 6-slot (missing one accessory) | ✅ Verified |
| Fol (money) | ✅ Verified in-game (via `so2_fol.py` — see below) |
| Specialties (shop-bought Skill Shop tiers: Knowledge/Sensibility/Technique/Combat ×3 levels) | ✅ Verified — mechanism explained and full 12-tier bit table confirmed by executing the real purchase code — [details](docs/SO2-SPECIALTY-INVESTIGATION.md) |
| Adding/recruiting a party member | ✅ Verified in-game (via `so2_party.py`) — two parallel per-slot arrays, identity is a numeric ID not the name string — [details](docs/SO2-PARTY-MEMBER-INVESTIGATION.md) |
| Battle-ability quick-assignment slots (4 per character) | ✅ Mapped and disassembly-verified — decoded `0x56C-0x56F` per character, real candidate/read/write code executed against real saves — [details](docs/SO2-SPECIAL-ATTACK-LIST-CHECK.md) |
| Story/event flags, map location, recipes | ⚠️ Open — [Private Actions](docs/SO2-PRIVATE-ACTIONS.md) documented as a lead, not yet tested against a save |

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

### Done, awaiting in-game testing

| Task | Verified? | Validation |
|---|---|---|
| Dias/Opera "best gear" equip on save 15 | Unverified | In-game testing needed — not yet booted since the edit |
| Angel Armband → 20 on save 15 | Unverified | In-game testing needed |
| Seraphic Garb 0 → 20 on save 15 (first-ever item) | Unverified — disassembly-verified only (actual add-routine instructions executed and matched) | In-game testing needed |

### Not started

| Task | Status | Validation | Notes |
|---|---|---|---|
| Specialty Knowledge-vs-Sensibility bit mapping | Resolved | Disassembly (done) | All 12 shop tiers now have a confirmed bit table (`0x1A3F`/`0x1A40`), verified by executing the real purchase code — [details](docs/SO2-SPECIALTY-INVESTIGATION.md). The old "contradiction" was a mislabeled historical test, not a code bug; one clean live purchase would fully close out the last loose end |
| Field-leader / walking-sprite slot | Pending | Disassembly | Party investigation found a candidate pointer (decoded `0x41`) but didn't trace it to the actual field/sprite code |
| Map decoded chunks 1 (`0x000–0x1A0`) and 5 (`0x1748–0x1B88`) — ~1,200 of 7,048 decoded bytes never looked at | Pending | Disassembly | Most likely home for story flags, now that the raw-header candidate below has been ruled out |
| Story/event flags (raw header `0x2B4`–`0x2E3`) | Checked, ruled out as flags | Disassembly (done) | Turned out to be a raw mirror of party-stat data (load-screen/status cache), not a flags bitmap — [details](docs/SO2-STORY-FLAGS-HEADER-CHECK.md). Still open inside the unmapped decoded chunks above |
| Map/location | Inconclusive | Disassembly | Save-writer trace found the copy sources but not semantic meaning — [details](docs/SO2-MAP-LOCATION-CHECK.md). Next step: find the live overworld position variable first (trace the field-movement code), then check if it's saved, rather than guessing at save bytes |
| Private Actions / emotion levels / item-creation recipes | Pending | Disassembly (trace PA-trigger script opcodes) + light in-game confirmation | Fan-sourced only so far, never located in the save itself |
| Message speed / audio settings | Pending | Disassembly | Three rounds of live before/after diffing already failed — switch to disassembling the settings-menu code directly instead |
| 9-slot Special Attack/Magic list (old GameShark claim) | Inconclusive | Disassembly (done) | The specific historical claim doesn't check out — the referenced cheat-list entry doesn't even exist in the saved cheat-code file. Along the way, found and fully verified a real, different system instead: each character's 4 assignable battle-ability slots — [details](docs/SO2-SPECIAL-ATTACK-LIST-CHECK.md) |
| Inventory word's bit-15 flag meaning | Pending | Disassembly (trace more callers) + minor in-game confirmation | Present on every add call; purpose not established |
| Party primary array — full byte-by-byte map | 69% mapped | Disassembly (done for now) | All 96 bytes covered; 66 named (ID/EXP/HP/MP/level/STR/CON/AGL/DEX/INT/GUTS), 12 are two unnamed stat triplets, 18 unresolved — [details](docs/SO2-PARTY-MEMBER-INVESTIGATION.md#primary-record-complete-byte-coverage-partial-semantic-map-2026-09-27). Revisit later to name the rest |

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
