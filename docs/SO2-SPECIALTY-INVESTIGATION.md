# SO2 Specialties

Investigation started 2026-09-25, same session as the Fol/checksum work. Core mapping now resolved
via Codex tracing the actual purchase/shop code (same rigor as the Fol and checksum investigations,
run across two sessions after hitting usage limits mid-run each time — nothing lost, just slow).

## Method

Every earlier attempt at this (the "33-byte flag run" and specialty-purchase diffs from earlier
in this session) used raw-byte diffing and produced 100-200+ changed bytes per test, dominated by
zero-run re-compression noise (see [SAVE-FORMAT.md](SAVE-FORMAT.md)'s compression note) — not
usable signal. Decoding both saves first with `so2_fol.py`'s `state()`/`decode()` and diffing the
*decoded* bytes instead dropped that to single digits. **All future before/after tests on this
save format should decode first.**

## VERIFIED: the specialty system

There are exactly **4 specialties**, each purchasable at **3 levels**, for **12 fixed flags total**
— confirmed by Codex tracing the actual purchase script in the game's MIPS code. The flags use
fixed IDs assigned by the game, not acquisition order (an early theory, now disproved by the code).

- **Decoded offset `0x1A3F`, bits 4-7**: "has reached level 1" (i.e. unlocked) for the 4
  specialties. Bits 0-3 unused (always 0 in every sample seen).
- **Decoded offset `0x1A40`, bits 0-3**: "has reached level 2" for the same 4 specialties, in the
  **same order** as `0x1A3F`'s bits 4-7 (just shifted down by 4 bit positions).
- **Decoded offset `0x1A40`, bits 4-7**: "has reached level 3" for the same 4 specialties, same
  order again.

Combining that structural rule (from the code) with four real purchase tests (from direct
before/after observation — see the table below) gives the complete name-to-bit mapping:

| Bit (in `0x1A3F`'s upper nibble / `0x1A40`'s corresponding nibble) | Specialty |
|---|---|
| 4 | Knowledge |
| 5 | Sensibility |
| 6 | Technique |
| 7 | Combat |

To check whether character X has specialty Y at level Z: level 1 → bit `(4+index)` of `0x1A3F` is
set; level 2 → bit `index` of `0x1A40` is set; level 3 → bit `(4+index)` of `0x1A40` is set, where
`index` is 0=Knowledge, 1=Sensibility, 2=Technique, 3=Combat. This is a **party-wide** unlock, not
per-character — matches real gameplay (buying a specialty makes it available to every character at
once; how far each character has individually leveled *within* it is tracked separately by the
existing, already-VERIFIED per-character SP/skill-level system).

## Corrected: earlier wrong guesses

Two fields we guessed were specialty-related turned out not to be, once Codex traced the actual code:

- **Decoded offset `0x24`** is a general **save counter** (increments every time the game saves),
  not a specialty-purchase counter. It only *looked* correlated because we happened to save once
  per purchase in testing.
- **Decoded offset `0x10`** is used to **display playtime**, unrelated to specialties.
- **Decoded offset `0x198`** is the game's remembered **cursor position for which save box was last
  selected** in the load/save menu (UI state, not game data) — it tracked our own box navigation
  during testing (S14→S11), nothing to do with any purchase.

## LIKELY (strong evidence, not fully closed out)

- **Decoded offsets `0x1B58`-`0x1B82`** (~48 bytes near the very end of the `0x1B88`-byte decoded
  state): Codex traced the save serializer and confirmed this range is **saved beyond the portion
  the snapshot routine actually populates** — i.e. it's very likely genuinely unused/uninitialized
  trailing data, consistent with what the old raw-offset docs already flagged for this same region.
  Codex was still checking allocation/load behavior to fully close this out when it ran out of
  usage credits a second time; treat as LIKELY rather than fully VERIFIED.
- **Decoded offset `0x1880`**: appeared alongside `0x198` starting with the third test onward.
  Not yet traced in code — plausibly another UI/navigation counter given its correlation with
  `0x198`, but unconfirmed.
- Several bytes near Claude's character entry (`0x1750`, `0x1758`, `0x1760`, `0x1761`, `0x1769`,
  occasionally `0x1340`/`0x1341`) shift by small amounts on every specialty purchase test so far —
  presumed to be a recalculated derived stat (something like an effect total that changes once a
  character has access to a new specialty), not the unlock flag itself. Not traced in code.

## UNRESOLVED CONTRADICTION (2026-09-25, later same session)

Two more real purchase tests, both reported by the player as accurate labels (not assumed or
inferred by us):

| Test | Before → After box | `0x1A40` | Bit that flipped | Expected (per mapping above) |
|---|---|---|---|---|
| "Sensibility 2" | S10 → S09 | `0x03`→`0x07` | bit 2 | bit 1 (Sensibility's level-2 bit was already set from the earlier confirmed Sensibility-lvl-2 test) |
| "Combat lvl 2" | S09 → S08 | `0x07`→`0x0F` | bit 3 | bit 3 (Combat) — **matches, no contradiction** |

The Combat test lines up perfectly with the mapping. The "Sensibility 2" test does not: bit 2 is
Technique's slot per the mapping above (built from Codex's code-level finding that the flag order
is fixed, not acquisition-dependent, combined with two earlier clean single-bit tests that
established bit 0 = Knowledge and bit 1 = Sensibility). The player maintains the box labels are
accurate to what was actually purchased in-game — this was not a testing/labeling mistake on the
data-collection side.

**This is a real, unresolved conflict, not resolved by assuming either side is wrong:**
- If the bit mapping (bit 1 = Sensibility) is correct, then the "Sensibility 2" purchase should
  have produced no change at all in `0x1A40` (already set from the earlier test) — it didn't; bit 2
  changed instead.
- If the purchase label is correct, then either Sensibility's flag isn't bit 1 after all (which
  would also mean the earlier "Sensibility lvl 2" test's bit-1 flip was coincidental or mislabeled),
  or the fixed-ID theory from the code trace is incomplete somehow (e.g. an index that isn't
  purely static, or a level-2-vs-level-3 mixup — bit 2 in the *level-3* nibble, i.e. `0x1A40` bit 6,
  is not what changed here, so it's not simply a level-2/level-3 confusion).

**What's needed to resolve this:** re-open the code trace specifically on the purchase script's
flag-ID assignment for Sensibility, rather than trusting the two-earlier-tests inference. Ideally
also get one more real purchase test of a specialty whose bit is *not yet* directly confirmed by an
isolated single-bit-flip (so far only Technique-unlock and Combat-unlock were clean isolated flips
in `0x1A3F`; Knowledge and Sensibility's *unlock* bits were both already-set before testing began
and were only ever inferred, never directly observed flipping in `0x1A3F` itself).

## Bonus lead for future work

Codex located the game's general flag storage while tracing this: **global flags start at decoded
offset `0x19E8`**, and these specialty purchases correspond to global flag IDs starting at `0x2BC`.
This is very likely the same flag system the still-open **story/event flags** investigation
(see [SAVE-FORMAT.md](SAVE-FORMAT.md)'s open items) has been looking for — worth pointing a future
Codex investigation at `0x19E8`+ directly instead of diffing raw save-file regions.

## Raw test data

| Test | Before → After box | Fol Δ | `0x1A3F` | `0x1A40` |
|---|---|---:|---|---|
| Technique 1 (new) | S15 → S14 | −400 | `0x30`→`0x70` (bit 6) | — |
| Knowledge lvl 2 | S14 → S13 | (paid) | — | `0x00`→`0x01` (bit 0) |
| Sensibility lvl 2 | S13 → S12 | (paid) | — | `0x01`→`0x03` (bit 1) |
| Combat 1 (new) | S12 → S11 | (paid) | `0x70`→`0xF0` (bit 7) | — |
| "Sensibility 2" (player-labeled) | S10 → S09 | (paid) | — | `0x03`→`0x07` (bit 2 — see contradiction above) |
| Combat lvl 2 | S09 → S08 | (paid) | — | `0x07`→`0x0F` (bit 3, matches) |

All six purchases were made on the same card during this session; box contents get reorganized
often during play, so check `saveconv.py list` for current state rather than assuming these box
numbers still hold this data.
