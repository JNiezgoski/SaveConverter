# SO2 Super Specialties Reference

Compiled 2026-09-25 from RPGClassics' SO2 "Super Specialties" shrine (contributor: Sherwin Tam).
Descriptions paraphrased and mechanics reorganized for this project's reference; original text is
copyrighted to its authors and is not reproduced. Detailed usage strategies (which items to combine,
optimal play patterns) are summarized, not transcribed.

## RESOLVED: terminology collision confirmed and explained

This is now confirmed rather than an open question, using RPGClassics' own "Specialties" page (see
[SO2-SKILL-SPECIALTIES.md](SO2-SKILL-SPECIALTIES.md)): every "Needed Skill" listed for each
wiki-Specialty matches a name in this project's already-VERIFIED 46-item **Skill** list exactly
(Mineralogy, Esthetic Sense, Herbal Medicine, Recipe, Craft, Metal Casting, etc.). So there are
genuinely **three distinct things that share overlapping "specialty" terminology**:

1. This project's VERIFIED **Skill** list (46 items, 0-10 per character) — the real save data.
2. The wiki's **Specialty** (17 items: Alchemy, Art, Authoring, Compounding, Cooking, Customize,
   Familiar, Identify, Machinery, Metalwork, Musical Talent, Oracle, Pickpocket, Practice,
   Reproduction, Scout, Survival) — each one's level is just the **average of 1-3 related Skills**,
   rounded down, capped at 10. A **computed value**, like ATK/HIT — not separately stored.
3. **Super Specialty** (this page's 8 items) — combines multiple party members' Specialty-related
   Skill levels further. Also computed, not stored.

The shop-bought system this project verified tonight (Knowledge, Sensibility, Technique, Combat —
see [SO2-SPECIALTY-INVESTIGATION.md](SO2-SPECIALTY-INVESTIGATION.md)) is a genuinely **separate,
fourth system** that happens to share the English word "specialty" in the game's own UI — a real
naming collision in the source material, not a project misunderstanding.

## The mechanic

A Super Specialty pools multiple party members' individual skill levels into one shared, party-wide
ability. Each has a **major** skill (determines the Super's level: sum of all party members' levels
in that skill, divided by 3, rounded down) and a **minor** skill (only needs one character to know
it at level 1, just to unlock the Super's name on the menu). To unlock a Super at all: two
characters at level 4+ in the major skill, one character at level 1+ in the minor skill. Level cap
is 10. Because low levels are easier to raise than high ones, spreading the major skill across more
characters raises a Super faster than maxing it on one or two.

## The Super Specialties

| Super | Major skill | Minor skill | Consumes | What it does |
|---|---|---|---|---|
| Master Chef | Cooking | Compounding | 2 ingredients | Combine two ingredients into a unique high-value dish, one result per ingredient pair |
| Orchestra | Musical Talent | Art | Conductor's Baton | Boosts item-creation/Super success rates while active; needs one instrument+song per party member |
| Comprehension | Practice | Survival | — | Chance of bonus Skill Points on level-up; slows the whole party in combat while active |
| Come on Bunny | Familiar | Scout | — | Summons a large mount ("Bunny") for overland travel, all terrain except water |
| Publishing | Writing | Machinery | Fountain Pen | Each character can write up to 2 books (one FP-themed, one rarer RP-themed) to sell or read to reset a relationship's Emotional Level to a fixed 8 |
| Identify All! | Identify | Metalwork | Spectacles | Temporarily shifts all shop prices by (skill level × 3%) — buy-only or sell-only, since it affects everything at once |
| Blacksmith | Customize | Alchemy | Ore (Iron, Damascus, etc.) | Armor-crafting counterpart to weapon Customize; a Magical Rasp unlocks different results, not just better odds |
| Reverse Side | Pickpocket | Copying | Vellum Paper | Creates powerful but "illegal" items (free inn stays, XP cheats, etc.); failure creates the game's worst item (a money-draining "Bounced Check"), and use lowers the whole party's Emotional Levels |

## Status

LIKELY, fan-sourced, and — critically — **not yet reconciled** with this project's own verified
Skill/Specialty terminology. Before using this to interpret any save bytes, first determine whether
"Specialty" here means this project's "Skill" (46-item list) or something not yet found at all.
