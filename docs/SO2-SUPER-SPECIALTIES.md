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

## The 8 Super Specialties

All 8 Super Specialty names and their major/minor Specialty inputs are extracted directly from
**Disc 1 Archive 3015** (slices 115..122 and 186..193) via
[`tools/so2_skills_extract.py`](file:///C:/CodeTesting/SaveConverter/tools/so2_skills_extract.py).
In-game description text itself is not reproduced, consistent with this doc's sourcing note above.

| ID | Super Specialty | Major Specialty | Minor Specialty | Consumes | What it does |
|---|---|---|---|---|---|
| 1 | Master Chef | Cooking | Compounding | 2 ingredients | Combine two ingredients into a unique high-value dish, one result per ingredient pair |
| 2 | Orchestra | Musical Talent | Art | Conductor's Baton | Boosts item-creation/Super success rates while active; needs one instrument+song per party member |
| 3 | Comprehension | Practice | Survival | — | Chance of bonus Skill Points on level-up; slows the whole party in combat while active |
| 4 | Come on Bunny | Familiar | Scout | — | Summons a large mount ("Bunny") for overland travel, all terrain except water |
| 5 | Publishing | Authoring | Machinery | Fountain Pen | Each character can write up to 2 books (one FP-themed, one rarer RP-themed) to sell or read to reset a relationship's Emotional Level to a fixed 8 |
| 6 | Identify All! | Identify | Metalwork | Spectacles | Temporarily shifts all shop prices by (skill level × 3%) — buy-only or sell-only, since it affects everything at once |
| 7 | Blacksmith | Customize | Alchemy | Ore (Iron, Damascus, etc.) | Armor-crafting counterpart to weapon Customize; a Magical Rasp unlocks different results, not just better odds |
| 8 | Reverse Side | Pickpocketing | Reproduction | Vellum Paper | Creates powerful but "illegal" items (free inn stays, XP cheats, etc.); failure creates the game's worst item (a money-draining "Bounced Check"), and use lowers the whole party's Emotional Levels |

## Status

- **8 Super Specialty names and their major/minor Specialty inputs**: 100% VERIFIED directly from Disc 1 Archive 3015.
- **Terminology Collision**: FULLY RESOLVED. Individual characters learn 46 **Skills**. Combining Skills enables 17 **Specialties**. Combining Specialties across the party enables 8 **Super Specialties**. The 12 items sold in Skill Guilds are **Skill Shop Tiers** that unlock learning tiers in the 46-skill list.
- **Save Storage**: Neither Specialties nor Super Specialties are stored as raw integers in save data; their levels are dynamically computed by the game engine from character skill levels.
