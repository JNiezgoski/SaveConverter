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

## Skill data (SP cost per level 1→10, stat benefit, related Specialty)

Benefits marked "computed" mean the specialty derived from this skill is itself a computed average,
not separately stored (see [SO2-SKILL-SPECIALTIES.md](SO2-SKILL-SPECIALTIES.md)).

### Knowledge 1
| Skill | SP cost (Lv1-10) | Stat benefit |
|---|---|---|
| Mineralogy | 1/2/4/6/9/12/16/20/40/70 | INT +3 per level |
| Herbal Medicine | 2/3/5/8/12/17/23/30/38/47 | Blue/blackberry healing +3%/level |
| Recipe | 1/1/2/2/3/3/5/5/10/20 | Boosts favorite-food recovery |

### Knowledge 2
| Skill | SP cost (Lv1-10) | Stat benefit |
|---|---|---|
| Musical Notation | 2/4/8/16/32/90/40/50/70/90 | AGL +1/level |
| Biology | 12/22/32/42/62/80/82/85/90/95 | Max HP += level²×10 (only skill affecting max HP) |
| Tool Knowledge | 1/5/9/13/17/21/25/29/33/37 | Sell prices +3%/level (highest party member's level applies) |

### Knowledge 3
| Skill | SP cost (Lv1-10) | Stat benefit |
|---|---|---|
| Mental Science | 8/14/20/26/32/52/62/82/90/95 | Max MP += level×5 (only skill affecting max MP) |
| Piety | 5/7/9/11/13/33/43/53/63/80 | Random small stat boosts; may raise item-creation odds |
| Fairyology | 40/41/42/43/44/45/46/47/48/50 | INT +1/level |

### Sensibility 1
| Skill | SP cost (Lv1-10) | Stat benefit |
|---|---|---|
| Courage | 1/2/4/5/7/28/30/31/43/55 | (none listed) |
| Patience | 2/4/7/11/16/22/29/37/46/56 | CON +2/level (only skill affecting CON) |
| Esthetic Sense | 10/20/30/40/50/60/70/80/90/99 | (none listed) |
| Good Eye | 2/4/6/8/10/20/22/24/26/28 | Increases food HP-recovery effectiveness |

### Sensibility 2
| Skill | SP cost (Lv1-10) | Stat benefit |
|---|---|---|
| Playfulness | 12/14/16/18/20/22/24/26/28/30 | Passive Fol income; roughly 100/700/1900/…/27,100 at level 10 |
| Danger Sense | 2/3/5/7/10/13/17/21/26/40 | STM +3/level |
| Perseverance | 8 at every level | Reduces every other skill's SP cost by 2/level (min 1) — described as the single most valuable skill |
| Poker Face | 5/7/9/11/13/33/43/53/63/80 | GUTS +3/level (only skill affecting GUTS) |

### Sensibility 3
| Skill | SP cost (Lv1-10) | Stat benefit |
|---|---|---|
| Functionality | 15/25/35/45/55/65/75/75/85/85 | STR, DEX, AGL, INT all +6/level (only skill affecting 4 stats at once) |
| Radar | 20/30/40/50/60/70/80/90/90/99 | Random bonus item drops |
| Effort | 20/30/40/50/60/70/80/90/90/90 | Reduces EXP needed per level by ~4%/level |

### Technique 1
| Skill | SP cost (Lv1-10) | Stat benefit |
|---|---|---|
| Whistling | 1/2/4/6/12/20/25/30/35/40 | (none listed) |
| Copying | 40/50/50/60/60/70/80/90/90/99 | (none listed) |
| Sketching | 5/10/20/30/50/70/90/90/90/90 | (none listed) |
| Kitchen Knife | 2/4/8/16/32/40/50/55/65/90 | STR +20/level (fastest STR growth in the game) |

### Technique 2
| Skill | SP cost (Lv1-10) | Stat benefit |
|---|---|---|
| Mech Knowledge | 6/10/14/18/22/32/42/52/62/80 | (none listed) |
| Craft | 2/4/7/11/16/22/29/37/46/56 | AGL +2/level |
| Animal Training | 20/21/22/23/24/25/26/27/28/30 | (none listed) |
| Writing | 3/4/6/8/11/14/20/25/40/60 | DEX +2/level |

### Technique 3
| Skill | SP cost (Lv1-10) | Stat benefit |
|---|---|---|
| Music Instrument | 2/4/8/16/32/90/40/50/70/90 | AGL +1/level |
| Metal Casting | 3/6/12/24/48/58/68/78/88/98 | DEX +2/level |
| Scientific Ability | 6/10/14/18/22/32/42/52/62/80 | STR +10/level |
| Mech Operation | 12/22/32/42/62/80/82/85/90/95 | (none listed) |

### Combat skills (battle-only, no Specialty/stat contribution)

Note: combat skills work probabilistically (higher level = higher success chance, never
guaranteed) and can be toggled on/off in the skills menu.

| Skill | SP cost (Lv1-10) | Effect |
|---|---|---|
| Spirit Force (C1) | 20/30/40/50/60/70/80/90/90/99 | Raises defense |
| Below the Belt (C1) | 40/40/50/50/60/60/70/70/80/80 | Ignores enemy defense |
| Strong Blow (C1) | 20/21/22/23/24/25/26/27/28/30 | Knocks enemy back/airborne |
| Cancel (C1) | 10/20/30/40/50/60/70/80/90/99 | Chain directly into a Killer Move |
| Flip (C2) | 12/14/16/18/20/22/24/26/28/30 | Move behind the enemy to attack |
| Gale (C2) | 5/7/9/11/13/33/43/53/63/80 | Increases movement speed |
| Feint (C2) | 12/22/32/42/62/80/82/85/90/95 | Improves aim |
| Mental Training (C2) | 4/7/14/21/28/35/42/49/56/63 | Increases attack power |
| Counterattack (C3) | 5/10/15/20/40/50/60/70/85/99 | Chance to counter when hit |
| Parry (C3) | 12/22/32/42/62/80/82/85/90/95 | Increases dodge chance |
| Body Control (C3) | 10/20/30/40/50/60/70/80/90/99 | Reduces fainting/dizzy/status-ailment chance |
| Motormouth (C3) | 40/50/50/60/60/70/80/90/90/99 | Reduces spell cast time; spellcaster-exclusive |
| Provocation (C3) | 20/30/40/50/60/70/80/90/90/99 | Taunt, once per battle |
| Float (special, bonus-dungeon item only) | 20/30/40/50/60/70/80/90/90/99 | Launches enemy airborne on hit |

## Status

The 46-skill **list itself and its bit-level location** are already VERIFIED from real save data
(see `SAVE-FORMAT.md`). The **SP-cost progressions and stat-benefit formulas** above are LIKELY
(fan-sourced) — not yet independently re-derived from this project's own saves, but they explain
observed behavior (e.g. a skill costing very little SP at low levels) rather than requiring new
byte-level investigation. The **Skill Shop → decoded-bitmask mapping** is the one piece of this
document that directly resolves a real open question from tonight's investigation.
