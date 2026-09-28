# SO2 "Specialty" (= Skill-Derived Ability) Reference

Compiled 2026-09-25 from RPGClassics' SO2 "Specialties" shrine (contributor: Sherwin Tam).
Descriptions paraphrased and mechanics reorganized for this project's reference; original text is
copyrighted to its author and is not reproduced.

## This resolves an open question from SO2-SUPER-SPECIALTIES.md

Every "Needed Skill" below matches a name in this project's own already-VERIFIED 46-item **Skill**
list in `SAVE-FORMAT.md` exactly. So this wiki's "Specialty" is the same underlying system as this
project's "Skill" — just a different name for the ability built from combining skill levels, not a
new save-data field. See [SO2-SUPER-SPECIALTIES.md](SO2-SUPER-SPECIALTIES.md) for the full
three/four-way terminology breakdown (Skill vs. wiki-Specialty vs. Super Specialty vs. the unrelated
shop-bought "Specialty" system this project verified independently).

## The mechanic

A Specialty's level = average of its 1-3 related Skills' levels, rounded down, capped at 10 — a
**computed value**, the same category as ATK/HIT/AC (computed from stored data, not itself stored).
Without the associated Talent (see [SO2-TALENTS.md](SO2-TALENTS.md)), a Specialty is "virtually
guaranteed to fail" regardless of level.

## The 17 Specialties

All 17 Specialty names and their skill/talent inputs are extracted directly from **Disc 1 Archive
3015** (slices 98..114 and 169..185) via
[`tools/so2_skills_extract.py`](file:///C:/CodeTesting/SaveConverter/tools/so2_skills_extract.py).
In-game description text itself is not reproduced, consistent with this doc's sourcing note above —
see "Brief functional notes" below for a paraphrased summary of what each one does.

| ID | Specialty | Related Skills | Required Talent | Feeds into Super Specialty |
|---|---|---|---|---|
| 1 | Art | Esthetic Sense, Sketching | Sense of Design | Orchestra (minor) |
| 2 | Oracle | Piety, Playfulness, Radar | none | none |
| 3 | Musical Talent | Musical Notation, Music Instrument | Pitch, Sense of Rhythm | Orchestra (major) |
| 4 | Customize | Functionality, Craft, Metal Casting | Originality | Blacksmith (major) |
| 5 | Identify | Mineralogy, Herbal Medicine, Tool Knowledge | none | Identify All! (major) |
| 6 | Metalwork | Mineralogy, Esthetic Sense, Craft | Originality, Dexterity | Identify All! (minor) |
| 7 | Authoring | Writing | Writing Ability | Publishing (major) |
| 8 | Practice | Patience, Perseverance, Effort | none | Comprehension (major) |
| 9 | Scout | Danger Sense | Sixth Sense | Come on Bunny (minor) |
| 10 | Compounding | Herbal Medicine, Biology, Mental Science | Dexterity | Master Chef (minor) |
| 11 | Cooking | Recipe, Good Eye, Kitchen Knife | Sense of Taste | Master Chef (major) |
| 12 | Familiar | Whistling, Animal Training | Love of Animals | Come on Bunny (major) |
| 13 | Alchemy | Mineralogy, Fairyology, Scientific Ability | The Blessing of Manna | Blacksmith (minor) |
| 14 | Survival | Herbal Medicine, Patience | none | Comprehension (minor) |
| 15 | Pickpocketing | Courage, Poker Face | Dexterity | Reverse Side (major) |
| 16 | Reproduction | Copying | none | Reverse Side (minor) |
| 17 | Machinery | Mech Knowledge, Mech Operation | Dexterity, Sense of Design | Publishing (minor) |

## Brief functional notes (mechanics)

- **Alchemy**: converts Iron into higher-value ore/gems for Customize/Metalwork; spellcaster-only due to The Blessing of Manna requirement.
- **Art**: consumes Magical Canvas/Clay to create battle items, portraits, or dolls.
- **Authoring**: writes a guidebook (consumes a Fountain Pen) that grants another character level 5 in a skill the author has at level 5+.
- **Compounding**: mixes two herbs into one of several possible medicine results.
- **Cooking**: turns ingredients into food; characters have unique favorite dishes.
- **Customize**: combines a weapon with ore/gem into an upgraded or unique weapon.
- **Familiar**: remote shopping via bird messenger (consumes Pet Food).
- **Identify**: reveals unknown ("?"-prefixed) items; consumes a Spectacle.
- **Machinery**: crafts battle gadgets and support items (e.g. Precis/Opera unique moves/weapons).
- **Metalwork**: crafts accessories from gems and metals.
- **Musical Talent**: 3-stage process (find instrument -> compose music with Feather Pen -> play song with Conductor's Baton).
- **Oracle**: cosmetic hint system, no gameplay effect.
- **Pickpocketing**: requires Bandit's Glove or Magician's Hand equipped; executed using the [Square] button; decreases Emotional Levels with present party members.
- **Practice**: lowers battle abilities in exchange for bonus EXP.
- **Reproduction**: duplicates items using Magical Camera/Ririca and Magical Film.
- **Scout**: adjusts enemy encounter rate.
- **Survival**: field forage consuming 4 MP per attempt.

## Status

- **17 Specialty names, skill inputs, and talent gating**: 100% VERIFIED directly from Disc 1 Archive 3015.
- **Skill Inputs & Talents**: Fully reconciled with the verified 46-skill list and 10-talent system.
- **Specialty Level**: Computed value ($Average(\text{Skills})$, rounded down, capped at 10), not stored in save data.
