# SO2 Emotional Levels (FP/RP) Reference

Compiled 2026-09-25 from RPGClassics' SO2 "Emotional Levels" shrine (Drak, starting values credited
to Ian Kelley). Data extracted and reorganized for this project's reference; original prose is
copyrighted to its authors and is not reproduced.

## Why this matters for the save format

This directly corresponds to an already-documented **open item** in
[SAVE-FORMAT.md](SAVE-FORMAT.md) ("Private Actions / emotion levels, item-creation recipes — not
located"). This page gives the actual game mechanic and a full starting-value matrix, which is
exactly what's needed to go find it in decoded save data — search for a character's known starting
FP/RP values (as small adjacent bytes, likely one per relationship) the same way equipment and
inventory entries were located by searching for known real values.

**Notable cross-validation**: the "preordered list" used to break pairing ties is —

```
Claude, Rena, Celine, Bowman, Dias, Precis, Ashton, Leon, Opera, Ernest, Noel, Chisato
```

— the **exact same order** as this project's own VERIFIED character-ID table in `SAVE-FORMAT.md`.
Strong independent confirmation that this ID ordering is a fundamental part of the game's internal
data structures, not just a convention this wiki happens to use.

## The mechanic

- Every character tracks two values (**FP** = Friendship Points, **RP** = Romance Points) toward
  each of the other 11 characters — not symmetric (Noel's FP toward Chisato can differ from
  Chisato's FP toward Noel). That's up to 12 × 11 × 2 = 264 individual values in principle, though
  only 8 characters are in any single playthrough's roster.
- For same-sex pairs, FP is primary and RP is secondary. For opposite-sex pairs, RP is primary and
  FP is secondary.
- Character endings pair up whoever has the highest **primary** value above 10 for another
  character; ties break via the preordered list above. No primary value above 10 → that character
  ends the game alone.
- For a given pair, which of the two characters' scenes plays (they can differ) is determined by
  which one has the *lower* primary value toward the other; secondary values pick between multiple
  variants of that same scene. (Not reproducing the actual ending scripts here — that's substantial
  narrative content, unlike the factual restriction/mechanic data elsewhere in this doc.)
- Values also affect AI behavior in battle (healing/protecting favored characters first, calling
  out their name and having a higher berserk chance if they're KO'd).
- Three ways to change values: certain crafted books (set one relationship's FP or RP to a fixed
  8), Private Actions (mostly affect the protagonist's own relationships), and fighting ~100
  battles together (increases the primary value by 1).
- Values are a shared pool per character — raising FP/RP toward one character generally lowers it
  toward others.

## Starting values (FP-RP) by character pair

Row = whose value it is (Source Character `0..11`), column = toward whom (Target Character `0..11`). `---` = not applicable (self, or route-exclusive pairing not present together). Reordered to canonical internal engine Character ID order (`0..11`).

| | Claude | Rena | Celine | Bowman | Dias | Precis | Ashton | Leon | Opera | Ernest | Noel | Chisato |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Claude** | — | 5-6 | 5-5 | 5-5 | 6-4 | 5-5 | 5-4 | 5-4 | 6-5 | 5-5 | 5-5 | 5-5 |
| **Rena** | 6-5 | — | 5-5 | 5-5 | 7-6 | 5-4 | 5-5 | 5-5 | 6-5 | 5-5 | 5-5 | 5-5 |
| **Celine** | 5-5 | 5-5 | — | 5-5 | 4-3 | 4-3 | 5-4 | 5-4 | 5-5 | 5-7 | 5-5 | 5-5 |
| **Bowman** | 5-5 | 7-5 | 6-5 | — | 5-5 | — | 5-5 | 5-5 | 6-5 | 5-5 | 6-5 | 6-5 |
| **Dias** | 5-5 | 7-5 | 4-4 | 4-4 | — | 4-4 | 4-4 | — | 4-4 | 4-4 | 4-4 | 4-4 |
| **Precis** | 7-6 | 7-6 | 6-5 | — | 5-5 | — | 5-5 | 6-5 | 5-5 | 5-5 | 6-5 | 5-5 |
| **Ashton** | 4-4 | 5-4 | 4-4 | 5-5 | 5-4 | 5-7 | — | 5-5 | — | — | 5-5 | 5-5 |
| **Leon** | 6-5 | 5-5 | 5-5 | 5-5 | — | 6-5 | 5-4 | — | 5-4 | 4-4 | 6-5 | 5-5 |
| **Opera** | 6-5 | 4-4 | 5-4 | 5-4 | 5-4 | 5-4 | — | 5-5 | — | 7-8 | 5-4 | 5-5 |
| **Ernest** | 6-5 | 5-5 | 5-6 | 5-5 | 5-5 | 5-5 | — | 5-5 | 5-7 | — | 6-5 | 5-5 |
| **Noel** | 5-5 | 5-5 | 5-5 | 5-5 | 5-5 | 5-5 | 5-5 | 6-6 | 5-5 | 6-5 | — | 6-5 |
| **Chisato** | 6-6 | 5-5 | 5-5 | 5-5 | 4-4 | 6-5 | 6-5 | 5-5 | 6-5 | 6-5 | 5-5 | — |

## Status

**VERIFIED (Storage & Engine Architecture)**:
The underlying physical storage for these relationship values is confirmed in [docs/SO2-CHUNK1-MAPPING.md](SO2-CHUNK1-MAPPING.md):
- **Matrix A (Friendship Points - FP)**: Stored at decoded save chunk 1 offset `0x058..0x0E8` (144 bytes, indexed as `0x058 + 12 * source_id + target_id`, values clamped 0..15).
- **Matrix B (Romance / Affection Points - RP)**: Stored at decoded save chunk 1 offset `0x0E8..0x178` (144 bytes, indexed as `0x0E8 + 12 * source_id + target_id`, values clamped 0..15).
- Traced through resident script interpreter opcode `0xFF` sub-dispatcher `80064F30` / `8006590C..8006598C` and bounded matrix traversal `8006B59C..8006B62C`. The fan-sourced starting matrix above aligns directly with this 12×12 architecture.
