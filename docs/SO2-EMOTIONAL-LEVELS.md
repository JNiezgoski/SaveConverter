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
- Values also affect AI behavior in battle (healing/protecting favored characters first, calling
  out their name and having a higher berserk chance if they're KO'd).
- Three ways to change values: certain crafted books (set one relationship's FP or RP to a fixed
  8), Private Actions (mostly affect the protagonist's own relationships), and fighting ~100
  battles together (increases the primary value by 1).
- Values are a shared pool per character — raising FP/RP toward one character generally lowers it
  toward others.

## Starting values (FP-RP) by character pair

Row = whose value it is, column = toward whom. `---` = not applicable (self, or route-exclusive
pairing not present together).

| | Claude | Rena | Celine | Ashton | Opera | Precis | Bowman | Ernest | Dias | Leon | Noel | Chisato |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Claude** | — | 5-6 | 5-5 | 5-4 | 6-5 | 5-5 | 5-5 | 5-5 | 6-4 | 5-4 | 5-5 | 5-5 |
| **Rena** | 6-5 | — | 5-5 | 5-5 | 6-5 | 5-4 | 5-5 | 5-5 | 7-6 | 5-5 | 5-5 | 5-5 |
| **Celine** | 5-5 | 5-5 | — | 5-4 | 5-5 | 4-3 | 5-5 | 5-7 | 4-3 | 5-4 | 5-5 | 5-5 |
| **Ashton** | 4-4 | 5-4 | 4-4 | — | — | 5-7 | 5-5 | — | 5-4 | 5-5 | 5-5 | 5-5 |
| **Opera** | 6-5 | 4-4 | 5-4 | — | — | 5-4 | 5-4 | 7-8 | 5-4 | 5-5 | 5-4 | 5-5 |
| **Precis** | 7-6 | 7-6 | 6-5 | 5-5 | 5-5 | — | — | 5-5 | 5-5 | 6-5 | 6-5 | 5-5 |
| **Bowman** | 5-5 | 7-5 | 6-5 | 5-5 | 6-5 | — | — | 5-5 | 5-5 | 5-5 | 6-5 | 6-5 |
| **Ernest** | 6-5 | 5-5 | 5-6 | — | 5-7 | 5-5 | 5-5 | — | 5-5 | 5-5 | 6-5 | 5-5 |
| **Dias** | 5-5 | 7-5 | 4-4 | 4-4 | 4-4 | 4-4 | 4-4 | 4-4 | — | — | 4-4 | 4-4 |
| **Leon** | 6-5 | 5-5 | 5-5 | 5-4 | 5-4 | 6-5 | 5-5 | 4-4 | — | — | 6-5 | 5-5 |
| **Noel** | 5-5 | 5-5 | 5-5 | 5-5 | 5-5 | 5-5 | 5-5 | 6-5 | 5-5 | 6-6 | — | 6-5 |
| **Chisato** | 6-6 | 5-5 | 5-5 | 6-5 | 6-5 | 6-5 | 5-5 | 6-5 | 4-4 | 5-5 | 5-5 | — |

## Status

LIKELY, not code/save-verified — same caveat as the other fan-sourced reference docs here. No save
data has been searched for these values yet; a good next step would be picking one character's
distinctive starting pair (e.g. Precis's 7-6 toward both Claude and Rena) and searching a fresh
early save's decoded state for that exact byte pattern, the same technique used to locate equipment
and inventory data.
