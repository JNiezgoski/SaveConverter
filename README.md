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
| Item ID table, inventory counts (max 20) | ✅ Verified |
| Equipment — full 7-slot characters (incl. Noel, Chisato) | ✅ Verified |
| Equipment — compressed 6-slot (missing one accessory) | ✅ Verified |
| Fol (money) | ✅ Verified in-game (via `so2_fol.py` — see below) |
| Specialties (shop-bought Skill Shop tiers: Knowledge/Sensibility/Technique/Combat ×3 levels) | ✅ Verified — mechanism fully explained, mapping mostly confirmed — [details](docs/SO2-SPECIALTY-INVESTIGATION.md) |
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

## Tools

| File | What it does |
|---|---|
| `saveconv.py` | Core library (checksums, card format detection/conversion) + a CLI: `convert`, `list`, `extract`, `import`. No arguments opens a small picker window. |
| `savemanager.py` | Two-card-side-by-side GUI: copy/move/rename/delete saves, import/export single saves, combine cards, convert formats, install as DuckStation's card 1/2. `python savemanager.py` |
| `so2_refill_sp.py` | Sets every character's SP to max, handling every internal encoding form. `python so2_refill_sp.py <slot> <box1> [box2]` — e.g. `python so2_refill_sp.py 1 1 2` |
| `so2_equip.py` | View/edit equipment. `python so2_equip.py show [box]` or `python so2_equip.py set <box> <Character> <slot> "<Item>"` |
| `so2_anatomy.py` | Labels every byte of one save block by confidence (verified/decoded/unknown) and writes a full map to disk. `python so2_anatomy.py [box]` |
| `so2_fol.py` | Sets Fol (money) through the real zero-run codec — decodes the compressed state, edits the value, re-encodes, re-signs. `python so2_fol.py <card> --save S13 --fol 5000 --out <new card>` (writes a new card file; never overwrites the source) |

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
