# SO2 Specialties: in progress

Investigation started 2026-09-25, same session as the Fol/checksum work. Not yet complete —
this documents current findings and open questions so the next session doesn't restart from zero.

## Method

Every earlier attempt at this (the "33-byte flag run" and specialty-purchase diffs from earlier
in this session) used raw-byte diffing and produced 100-200+ changed bytes per test, dominated by
zero-run re-compression noise (see [SAVE-FORMAT.md](SAVE-FORMAT.md)'s compression note) — not
usable signal. Decoding both saves first with `so2_fol.py`'s `state()`/`decode()` and diffing the
*decoded* bytes instead dropped that to single digits. **All future before/after tests on this
save format should decode first.**

## Confirmed findings

- **Decoded offset `0x24`**: increments by 1 on every specialty-related purchase seen so far —
  both new unlocks and level-ups. Likely a general "specialty purchases made" counter.
- **Decoded offset `0x1A3F`**: a per-specialty **unlock bitmask**. Confirmed by two clean,
  isolated single-bit-flip observations:
  - Buying "Technique 1" (a new unlock): `0x30` → `0x70` (bit 6 newly set).
  - Buying "Combat 1" (a new unlock): `0x70` → `0xF0` (bit 7 newly set).
  - Bits 4 and 5 (`0x10`, `0x20`) were already set before either test began — from two earlier
    purchases (Knowledge 1 and Sensibility 1, bought before this investigation started and no
    longer re-testable, since they're already owned). **Which of bit 4 / bit 5 is Knowledge vs.
    Sensibility is not yet known** — see Open questions.
- **Decoded offset `0x1A40`**: a second bitmask, parallel to `0x1A3F` but for "has this specialty
  reached level 2+". Confirmed by:
  - Buying "Knowledge lvl 2" (a level-up): `0x00` → `0x01` (bit 0 newly set).
  - Buying "Sensibility lvl 2" (a level-up, different specialty): `0x01` → `0x03` (bit 1 newly
    set, bit 0 stayed set from the earlier Knowledge level-up).
  - This bitmask's bit order does **not** obviously match `0x1A3F`'s (bits 0/1 here vs. bits 4/5
    there for the same two specialties) — the two bitmasks likely use independent bit assignments,
    not a shared per-specialty ID. Not confirmed why.

## Open questions (Codex investigation in progress, paused on usage limit)

A Codex background investigation was launched to trace the actual shop/specialty code and get a
verified name-to-bit mapping (the same rigor as the Fol and checksum investigations) rather than
inferring it from purchase order, which no longer works since Knowledge 1 and Sensibility 1 are
already bought. It hit a usage-limit error mid-run (available again ~6:08 AM) before reaching a
conclusion. Still open when it resumes:

1. **Full specialty name list and its real bit/index order** in the game's own code — needed to
   resolve bit 4 vs. bit 5 (Knowledge vs. Sensibility) in `0x1A3F`, and to map `0x1A40`'s bits.
2. **Decoded offset `0x10`**: went `0x00` → `0x01` on the Knowledge-lvl-2 test, but did *not*
   change on the Technique-1 (new unlock) test. Possibly a level-up-specific counter, separate
   from `0x24`'s general purchase counter — not confirmed with enough samples.
3. **Decoded offsets `0x198` and `0x1880`**: a small paired change (`0x198` decreasing by 1,
   `0x1880` increasing by 1) appeared starting with the third test onward (Sensibility lvl 2,
   Combat 1) but not the first two. Didn't correlate with which specialty or unlock-vs-levelup —
   likely incidental/unrelated background counters, not specialty state, but not confirmed.
4. **Decoded offsets `0x1B58`-`0x1B82`** (~30 bytes): went from assorted nonzero values to all
   zero on the Knowledge-lvl-2 test only. Sits near the very end of the `0x1B88`-byte decoded
   state — likely uninitialized/leftover trailing data (consistent with the old raw-offset docs
   already flagging that region as "not real data"), but not confirmed.
5. Several bytes near Claude's character entry (`0x1750`, `0x1758`, `0x1760`, `0x1761`, `0x1769`,
   `0x1769`, and occasionally `0x1340`/`0x1341`) shift by small amounts on every specialty
   purchase test so far. Presumed to be recalculated derived stats (something like an ATK/effect
   total that changes once a character has access to a new specialty), not the unlock flag itself
   — not confirmed which stat.

## Raw test data (for whoever resumes this)

| Test | Before → After box | Fol Δ | `0x24` | `0x1A3F` | `0x1A40` | Notes |
|---|---|---:|---|---|---|---|
| Technique 1 (new) | S15 → S14 | −400 | +1 | `0x30`→`0x70` (bit 6) | — | |
| Knowledge lvl 2 | S14 → S13 | (paid) | +1 | — | `0x00`→`0x01` (bit 0) | `0x10` also 0→1; `0x1B58-0x1B82` zeroed |
| Sensibility lvl 2 | S13 → S12 | (paid) | +1 | — | `0x01`→`0x03` (bit 1) | `0x198`/`0x1880` first appear |
| Combat 1 (new) | S12 → S11 | (paid) | +1 | `0x70`→`0xF0` (bit 7) | — | `0x198`/`0x1880` continue |

All four are live on the current card as of this writing (boxes 11-15 in some order — check
`saveconv.py list` for current state, box contents get reorganized often during play).
