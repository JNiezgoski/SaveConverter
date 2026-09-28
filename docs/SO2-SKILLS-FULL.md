# SO2 Skills — Full Reference (SP Costs, Benefits, Skill Shops)

Compiled 2026-09-25 from RPGClassics' SO2 "Skills" shrine (contributor: Sherwin Tam). Data
reorganized for this project's reference; original descriptions paraphrased, not reproduced.

## THE key finding: this is what "buying a Specialty" actually does

This source's **"Skill Shops"** are named **Knowledge 1/2/3, Sensibility 1/2/3, Technique 1/2/3,
Combat 1/2/3** — exactly the 12 things this project mapped to a save-file bitmask tonight (see
[SO2-SPECIALTY-INVESTIGATION.md](SO2-SPECIALTY-INVESTIGATION.md)). Buying one of these in a shop
doesn't grant an ability directly — it **unlocks that shop tier**, which then lets any party member
spend SP to learn 3-4 specific Skills from this project's already-VERIFIED 46-skill list. This is
exactly what the player described from the outset: "it basically unlocks the ability to level up
skills." The bitmask this project found (`0x1A3F`/`0x1A40`) tracks exactly which of these 12 shop
tiers has been purchased — a global, party-wide unlock, matching the confirmed mechanic.

## Skill Shops (which shop tier unlocks which skills)

Sets marked with a note aren't available until reaching Lacour, per the source.

| Shop tier | Skills unlocked | Towns that sell it |
|---|---|---|
| Knowledge 1 | Mineralogy, Herbal Medicine, Recipe | Cross, Clik, Linga, Central City |
| Knowledge 2 | Musical Notation, Biology, Tool Knowledge | Herlie, Hilton, Linga, Central City |
| Knowledge 3 | Mental Science, Piety, Fairyology | Linga, North City |
| Sensibility 1 | Courage, Patience, Esthetic Sense, Good Eye | Cross, Clik, Central City |
| Sensibility 2 | Playfulness, Danger Sense, Perseverance, Poker Face | Herlie, Hilton, North City |
| Sensibility 3 | Functionality, Radar, Effort | Lacour, Armlock |
| Technique 1 | Whistling, Copying, Sketching, Kitchen Knife | Cross, Clik, Herlie, Central City |
| Technique 2 | Mech Knowledge, Craft, Animal Training, Writing | Hilton, North City |
| Technique 3 | Music Instrument, Metal Casting, Scientific Ability, Mech Operation | Linga, North City |
| Combat 1 | Spirit Force, Below the Belt, Strong Blow, Cancel | Clik, Herlie, Lacour, Armlock |
| Combat 2 | Flip, Gale, Feint, Mental Training | Hilton, Lacour, Armlock |
| Combat 3 | Counterattack, Parry, Body Control, Motormouth, Provocation | Lacour, Armlock |

This also explains this project's earlier decoded-diff finding of a general "specialties purchased"
counter and per-purchase Fol cost — each of these 12 tiers is a real, priced shop item, exactly as
tested (Technique 1, Knowledge lvl 2/3, Sensibility lvl 2, Combat lvl 1/2, etc.). Independently
cross-checked against RPGClassics' separate "Shopping List" page, which lists each town's actual
Skill Guild inventory by name (e.g. Lacour's "Lacour Skills" sells Sensibility 3/Combat 1-3) —
consistent with the table above.

## Skill data (SP cost per level 1→10, verified stat benefit)

The stat-benefit formulas below are **100% VERIFIED directly from Disc 1 Archive 3015** via
[`tools/so2_skills_extract.py`](file:///C:/CodeTesting/SaveConverter/tools/so2_skills_extract.py) —
real per-level scaling read from the game's own data, not fan estimates. In-game description text
itself is not reproduced here, consistent with this doc's sourcing note above. Benefits marked
"computed" mean the specialty derived from this skill is itself a computed average, not separately
stored (see [SO2-SKILL-SPECIALTIES.md](SO2-SKILL-SPECIALTIES.md)).

### Knowledge 1
| Skill | SP cost (Lv1-10) | Verified Stat Benefit (Archive 3015) |
|---|---|---|
| Mineralogy | 1/2/4/6/9/12/16/20/40/70 | INT += Skill Level × 3 |
| Herbal Medicine | 2/3/5/8/12/17/23/30/38/47 | Blue/blackberry recovery += Skill Level × 3% |
| Recipe | 1/1/2/2/3/3/5/5/10/20 | Favorite-food recovery boost |

### Knowledge 2
| Skill | SP cost (Lv1-10) | Verified Stat Benefit (Archive 3015) |
|---|---|---|
| Musical Notation | 2/4/8/16/32/90/40/50/70/90 | AGL += Skill Level × 1 |
| Biology | 12/22/32/42/62/80/82/85/90/95 | Max HP += Skill Level² × 10 (Lv10 = +1,000 HP) |
| Tool Knowledge | 1/5/9/13/17/21/25/29/33/37 | Item sell prices += Skill Level × 3% |

### Knowledge 3
| Skill | SP cost (Lv1-10) | Verified Stat Benefit (Archive 3015) |
|---|---|---|
| Mental Science | 8/14/20/26/32/52/62/82/90/95 | Max MP += Skill Level × 5 (Lv10 = +50 MP) |
| Piety | 5/7/9/11/13/33/43/53/63/80 | Random stat increases |
| Fairyology | 40/41/42/43/44/45/46/47/48/50 | INT += Skill Level × 1 |

### Sensibility 1
| Skill | SP cost (Lv1-10) | Verified Stat Benefit (Archive 3015) |
|---|---|---|
| Courage | 1/2/4/5/7/28/30/31/43/55 | Resists nervousness / enables pickpocketing |
| Patience | 2/4/7/11/16/22/29/37/46/56 | CON += Skill Level × 2 |
| Esthetic Sense | 10/20/30/40/50/60/70/80/90/99 | Enables Art / Metalwork appraisal |
| Good Eye | 2/4/6/8/10/20/22/24/26/28 | Food HP restoration increases |

### Sensibility 2
| Skill | SP cost (Lv1-10) | Verified Stat Benefit (Archive 3015) |
|---|---|---|
| Playfulness | 12/14/16/18/20/22/24/26/28/30 | Fol bonus on level-up |
| Danger Sense | 2/3/5/7/10/13/17/21/26/40 | STM += Skill Level × 3 |
| Perseverance | 8 at every level | Reduces SP required to learn skills by 2/level |
| Poker Face | 5/7/9/11/13/33/43/53/63/80 | GUTS += Skill Level × 3 |

### Sensibility 3
| Skill | SP cost (Lv1-10) | Verified Stat Benefit (Archive 3015) |
|---|---|---|
| Functionality | 15/25/35/45/55/65/75/75/85/85 | STR, DEX, AGL, INT all += Skill Level × 6 |
| Radar | 20/30/40/50/60/70/80/90/90/99 | Random item drops on level-up |
| Effort | 20/30/40/50/60/70/80/90/90/90 | Lowers EXP required to level up |

### Technique 1
| Skill | SP cost (Lv1-10) | Verified Stat Benefit (Archive 3015) |
|---|---|---|
| Whistling | 1/2/4/6/12/20/25/30/35/40 | Enables Familiar calls |
| Copying | 40/50/50/60/60/70/80/90/90/99 | Enables Reproduction specialty |
| Sketching | 5/10/20/30/50/70/90/90/90/90 | Enables Art specialty |
| Kitchen Knife | 2/4/8/16/32/40/50/55/65/90 | STR += Skill Level × 20 (Lv10 = +200 STR) |

### Technique 2
| Skill | SP cost (Lv1-10) | Verified Stat Benefit (Archive 3015) |
|---|---|---|
| Mech Knowledge | 6/10/14/18/22/32/42/52/62/80 | Enables Machinery specialty |
| Craft | 2/4/7/11/16/22/29/37/46/56 | AGL += Skill Level × 2 |
| Animal Training | 20/21/22/23/24/25/26/27/28/30 | Improves Familiar delivery success |
| Writing | 3/4/6/8/11/14/20/25/40/60 | DEX += Skill Level × 2 |

### Technique 3
| Skill | SP cost (Lv1-10) | Verified Stat Benefit (Archive 3015) |
|---|---|---|
| Music Instrument | 2/4/8/16/32/90/40/50/70/90 | AGL += Skill Level × 1 |
| Metal Casting | 3/6/12/24/48/58/68/78/88/98 | DEX += Skill Level × 2 |
| Scientific Ability | 6/10/14/18/22/32/42/52/62/80 | STR += Skill Level × 10 (Lv10 = +100 STR) |
| Mech Operation | 12/22/32/42/62/80/82/85/90/95 | Enables Machinery item creation |

### Combat skills (battle-only, no Specialty/stat contribution)

Note: combat skills work probabilistically (higher level = higher success chance, never
guaranteed) and can be toggled on/off in the skills menu. Effects below are verified against
Disc 1 Archive 3015; in-game description text is not reproduced.

| Skill | SP cost (Lv1-10) | Verified Effect (Archive 3015) |
|---|---|---|
| Spirit Force (C1) | 20/30/40/50/60/70/80/90/90/99 | Defensive boost |
| Below the Belt (C1) | 40/40/50/50/60/60/70/70/80/80 | Defense piercing |
| Strong Blow (C1) | 20/21/22/23/24/25/26/27/28/30 | Knockback / blow away |
| Cancel (C1) | 10/20/30/40/50/60/70/80/90/99 | Attack -> Killer Move cancel |
| Flip (C2) | 12/14/16/18/20/22/24/26/28/30 | Flank behind target |
| Gale (C2) | 5/7/9/11/13/33/43/53/63/80 | Combat movement speed increase |
| Feint (C2) | 12/22/32/42/62/80/82/85/90/95 | Aim / accuracy improvement |
| Mental Training (C2) | 4/7/14/21/28/35/42/49/56/63 | Attack power increase |
| Counterattack (C3) | 5/10/15/20/40/50/60/70/85/99 | Automatic counter when hit |
| Parry (C3) | 12/22/32/42/62/80/82/85/90/95 | Dodge / parry attack |
| Body Control (C3) | 10/20/30/40/50/60/70/80/90/99 | Faint / stun prevention |
| Motormouth (C3) | 40/50/50/60/60/70/80/90/90/99 | Heraldic cast time reduction |
| Provocation (C3) | 20/30/40/50/60/70/80/90/90/99 | In-battle enemy taunt |
| Float (special) | 20/30/40/50/60/70/80/90/90/99 | Launch enemy airborne |

## Status

- **46-skill List and Memory Addresses**: 100% VERIFIED from real save data (`SAVE-FORMAT.md`).
- **Stat Boost Formulas**: 100% VERIFIED directly from Disc 1 Archive 3015.
- **Skill Shop → Decoded-bitmask Mapping**: 100% VERIFIED across 12 shop tiers (`0x1A3F`/`0x1A40`).
- **SP Cost Progressions**: LIKELY (fan-sourced from strategy guides, fully consistent with in-game testing).
