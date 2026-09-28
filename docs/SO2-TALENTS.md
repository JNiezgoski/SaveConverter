# SO2 Talents Reference

Compiled 2026-09-25 from RPGClassics' SO2 "Talents" shrine (contributor: Sherwin Tam; probability
table sourced there from the Prima Strategy Guide). Descriptions paraphrased and data reorganized
for this project's reference; original text is copyrighted to its authors and is not reproduced.

## Relationship to this project's own findings

This project has the **10-talent bitmask fully VERIFIED** directly from the Disc 1 game binary (Archive 3015)
and confirmed against real save data:
- In save memory, talents are stored as a 32-bit `u32` word at `secondary + 0x20` (lower 10 bits occupied,
  upper bits 0, immediately preceding the SP block).
- All 10 talent names were extracted and verified directly from Disc 1 Archive 3015 via
  [`tools/so2_skills_extract.py`](file:///C:/CodeTesting/SaveConverter/tools/so2_skills_extract.py). In-game
  description text itself is not reproduced here, consistent with this doc's sourcing note above.
- Note the official game localization spelling: **The Blessing of Manna** (double 'n'). It is fixed per
  character (all spellcasters start with it, no fighter can ever learn it), never random.
- Gaining a talent through practice (not starting with it) also awards a fixed 100 Skill Points.

## The 10 talents (verified bit order and names)

| Bit | Talent Name (Official) | What it does | Related specialty (★ = learnable via use) |
|---|---|---|---|
| `0x001` | Originality | Creative ability to modify/customize things | Customize, ★Metalwork |
| `0x002` | Sense of Taste | Judging what tastes good | ★Cooking |
| `0x004` | Dexterity | Fine fingertip control | ★Metalwork, Compounding, Pickpocketing, ★Machinery |
| `0x008` | Sense of Design | Artistic/creative talent | ★Art, ★Machinery |
| `0x010` | Writing Ability | Putting thoughts into words | ★Authoring |
| `0x020` | Sense of Rhythm | Grasping musical rhythm | ★Musical Talent |
| `0x040` | Pitch | Grasping musical tones | ★Musical Talent |
| `0x080` | Love of Animals | Animal affinity | ★Familiar |
| `0x100` | Sixth Sense | Sensing the inexpressible | ★Scout |
| `0x200` | The Blessing of Manna | Innate magical power | Alchemy (fixed, not learnable) |

Note: Dexterity cannot actually be learned via Pickpocketing despite the specialty relation — do not rely on farming it that way.

## Starting-talent probabilities by character (Prima Guide data)

Each cell is `starting % / learn-through-practice %`. Blessing of Manna is 100% fixed for Celine,
Leon, Noel, Rena and 0% (impossible) for everyone else — consistent with "spellcasters only."

| Talent | Ashton | Bowman | Celine | Chisato | Claude | Dias | Ernest | Leon | Noel | Opera | Precis | Rena |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Blessing of Manna | 0/0 | 0/0 | 100/0 | 0/0 | 0/0 | 0/0 | 0/0 | 100/0 | 100/0 | 0/0 | 0/0 | 100/0 |
| Dexterity | 50/3.9 | 20/0.4 | 80/15.6 | 60/3.9 | 50/7.8 | 50/5.9 | 60/7.8 | 20/0.8 | 10/2.0 | 100/0 | 30/62.5 | 70/3.9 |
| Love of Animals | 50/0.8 | 0/23.4 | 10/0 | 50/39.1 | 20/3.9 | 20/0.8 | 30/3.9 | 10/2.0 | 90/3.9 | 0/0 | 70/2.0 | 85/15.6 |
| Originality | 10/39.1 | 40/3.9 | 40/31.3 | 60/11.7 | 60/11.7 | 100/0 | 20/7.8 | 30/3.9 | 40/3.9 | 40/19.5 | 30/7.8 | 20/3.9 |
| Pitch | 10/11.7 | 30/0.8 | 80/3.9 | 30/3.9 | 40/2.0 | 60/0.8 | 50/3.9 | 10/2.0 | 70/3.9 | 70/11.7 | 40/3.9 | 90/2.0 |
| Sense of Design | 0/0 | 20/7.8 | 90/23.4 | 40/3.9 | 65/7.8 | 30/2.0 | 30/11.7 | 40/2.0 | 50/3.9 | 60/46.9 | 30/62.5 | 25/0.8 |
| Sense of Rhythm | 10/11.7 | 10/0.8 | 10/1.2 | 30/3.9 | 45/2.0 | 60/0.8 | 100/0 | 10/2.0 | 60/3.9 | 70/11.7 | 40/5.9 | 40/3.9 |
| Sense of Taste | 80/2.0 | 10/2.0 | 10/0.4 | 60/23.4 | 10/0.4 | 10/7.8 | 20/0.8 | 35/3.9 | 20/3.9 | 10/0.4 | 0/1.2 | 80/35.2 |
| Sixth Sense | 30/2.0 | 30/23.4 | 45/7.8 | 0/2.0 | 0/0.4 | 40/7.8 | 80/15.6 | 0/3.9 | 40/3.9 | 0/0 | 50/0.4 | 0/0 |
| Writing Ability | 40/2.0 | 80/23.4 | 20/2.0 | 100/0 | 80/15.6 | 20/0.8 | 40/15.6 | 100/0 | 10/3.9 | 10/2.0 | 20/0.8 | 30/15.6 |

## Status

- The talent **bitmask mapping** and **official names** are 100% VERIFIED from Disc 1 Archive 3015 and save data.
- The **starting probabilities** above are LIKELY (fan-sourced from the Prima Guide, not independently verified against game assembly) but explain observed variance across saves.
