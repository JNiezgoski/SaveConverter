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

| Specialty | Related skills | Required talent | Feeds into (Super Specialty) |
|---|---|---|---|
| Alchemy | Mineralogy, Fairyology, Scientific Ability | Blessing of Mana (spellcasters only) | Blacksmith (minor) |
| Art | Esthetic Sense, Sketching | Sense of Design | Orchestra (minor) |
| Authoring | Writing | Writing Ability | Publishing (major) |
| Compounding | Herbal Medicine, Biology, Mental Science | Dexterity | Master Chef (minor) |
| Cooking | Recipe, Good Eye, Kitchen Knife | Sense of Taste | Master Chef (major) |
| Customize | Functionality, Craft, Metal Casting | Originality | Blacksmith (major) |
| Familiar | Whistling, Animal Training | Love of Animals | Come On Bunny (major) |
| Identify | Mineralogy, Herbal Medicine, Tool Knowledge | none | Identify All! (major) |
| Machinery | Mech Knowledge, Mech Operation | Dexterity, Sense of Design | Publishing (minor) |
| Metalwork | Mineralogy, Esthetic Sense, Craft | Originality, Dexterity | Identify All! (minor) |
| Musical Talent | Musical Notation, Music Instrument | Pitch, Sense of Rhythm | Orchestra (major) |
| Oracle | Piety, Playfulness, Radar | none | none |
| Pickpocket | Courage, Poker Face | Dexterity | Reverse Side (major) |
| Practice | Patience, Perseverance, Effort | none | Comprehension (major) |
| Reproduction | Copying | none | Reverse Side (minor) |
| Scout | Danger Sense | Sixth Sense | Come On Bunny (minor) |
| Survival | Herbal Medicine, Patience | none | Comprehension (minor) |

## Brief functional notes (mechanics, not flavor text)

- **Alchemy**: converts Iron into higher-value ore/gems for Customize/Metalwork; spellcaster-only
  due to the talent requirement.
- **Art**: consumes Magical Canvas/Clay to create battle items, portraits, or dolls.
- **Authoring**: writes a guidebook (consumes a Fountain Pen) that instantly grants another
  character level 5 in a skill the author has at level 5+; only ~20 skills are eligible.
- **Compounding**: mixes two herbs into one of several possible results, not all beneficial.
- **Cooking**: turns ingredients into food; each character but Chisato has a unique max-recovery
  "favorite dish."
- **Customize**: combines a weapon with ore/gem into a different weapon (or occasionally something
  else entirely); per-character, can't customize another character's weapon.
- **Familiar**: lets you remote-shop via a bird messenger (consumes Pet Food); the bird "species"
  changes with level and can't be reverted, so multiple characters at different levels is useful.
- **Identify**: reveals unknown ("?"-prefixed) items; consumes a Spectacle per attempt.
- **Machinery**: crafts battle bombs and other specialties' support items; important for
  Precis/Opera's unique weapons.
- **Metalwork**: crafts accessories from ore/gems; each character can only make about half the
  possible results per material, so multiple crafters are needed for full coverage.
- **Musical Talent**: 3-stage process (find instrument → compose up to 2 songs per instrument using
  a Feather Pen → play a composed song with a Conductor's Baton for a temporary party-wide effect).
- **Oracle**: cosmetic flavor-text specialty, no gameplay effect.
- **Pickpocket**: requires Bandit's Glove/Magician's Hand equipped; one attempt per NPC ever;
  lowers other present party members' Emotional Level toward the pickpocketing character each use.
- **Practice**: weakens the practicing character's stats in battle in exchange for bonus party-wide
  EXP; also grants bonus SP on level-up via its Super (Comprehension).
- **Reproduction**: duplicates most shop-bought items (not most rare ones) using a Magical
  Camera/Ririca and Magical Film.
- **Scout**: adjusts encounter rate; only the current party leader's level in this specialty
  matters.
- **Survival**: random item find, costs 4 MP, mostly yields cooking ingredients/minerals.

## Status

The **Skill** levels feeding these are already VERIFIED from real save data. The **Specialty**
computation rule (average, rounded down, capped 10) and the Talent gating are LIKELY (fan-sourced,
not independently re-derived from this project's own saves) but are a straightforward function of
already-known data, not a new field to locate.
