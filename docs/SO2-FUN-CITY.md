# SO2 Fun City Reference

Compiled 2026-09-25 from RPGClassics' SO2 "Fun City" shrine. Mechanics and prize/data tables
extracted and reorganized for this project's reference; the source's detailed enemy-by-enemy combat
strategies are summarized only, not transcribed — that's narrative walkthrough content, not simple
facts. Original text is copyrighted to its author and is not reproduced.

## Cross-reference to this project's own findings

**Star Guard** (Team Battle Rank A prize here) matches the equip-restriction data already recorded
in [SO2-ITEM-RESTRICTIONS.md](SO2-ITEM-RESTRICTIONS.md) — same item, independent source, consistent
"Win Fun City Team Battle Rank A" origin note.

## Bunny Races

Bet on a first/second-place pair (tickets 1000 Fol each, up to 8 at once) among bunnies with
Speed/Stamina/Personality stats. Longer-shot wins pay better prizes. Verified items with Disc item IDs:
Bunny Shoe (ID 393), Magical Drops (ID 55), Ganze Sea Urchin (ID 785), Seltzer (ID 369), Wisdom Ring (ID 91),
Lunatic Ring (ID 111), Fairy Ring (ID 124), Cinderella Glass (ID 754), Fairy Glass (ID 238), Reverse Doll (ID 61),
Dummy Doll (ID 37), 50,000 Fol, Protection Bomb (ID 452), Tetra-bomb (ID 450), Stone Check (ID 72),
Paralysis Check (ID 71), Poison Check (ID 70), Spring Water (ID 278), Resurrection Bottle (ID 277),
Blackberry (ID 756), Aquaberry (ID 755), Blueberry (ID 757).

## Cooking Master

A timed (5-minute) minigame: combine ingredients from a central pool into dishes for points; a
"Pressure gauge" (eased by higher Courage skill) makes success harder as it rises. Score = sum of
each dish's HP/MP recovery %; beat a random opponent (usually ~1000 points) to win that match's
ingredient set as a prize:

| Battle | Prize Ingredients |
|---|---|
| Meat | 10 Meat, 10 Egg/Dairy Products, 3 Creamy Cheese (ID 787), 3 Juicy Beef (ID 783) |
| Seafood | 20 Seafood, 1 Ganze Sea Urchin (ID 785), 2 Prime Tuna (ID 784) |
| Veggie | 10 Vegetables, 10 Grain, 1 Magical Rice (ID 786), 2 Purity Leaf (ID 782) |
| Slime | 10 Slippery Slime (ID 789), 3 Jiggly Slime (ID 790) |
| Dessert | 10 Fruit, 4 Sweet Fruit (ID 788) |
| Full-course | 6 each Meat/Seafood/Vegetables/Fruit, 8 Egg/Dairy, 1 Juicy Beef, 2 Purity Leaf, 4 Sweet Fruit, 1 Ganze Sea Urchin, 3 Creamy Cheese, 3 Magical Rice, 3 Prime Tuna |

Beating all chefs plus secret opponent Puffy with one character unlocks a final bout against
Yarma — winning awards the unique **Yarma Cooking Set** (Item ID 822, often mistranslated as "Master of EATS").

## Battle Arena — four modes, each with 5 ranks (F/E through A)

**Duel Battle** (1v1): prizes differ for fighters (Killer Moves) vs. spellcasters at ranks B-E;
Rank A gives a character-specific unique weapon:
- Claude: Windsley Sword (ID 505)
- Dias: Cromlea Sword (ID 521)
- Rena: Fellper Nails (ID 542)

**Team Battle** (five sequential 1v1s, win 3 of 5): rank prizes —
- F: Purple Mist (ID 73)
- E: Zephyr Earring (ID 130)
- D: Magic Cross (ID 142)
- C: Dream Crown (ID 161)
- B: Right Cross (ID 144)
- **A: Star Guard (ID 719)**

**Bully Battle** (one character vs. a wave of enemies): rewards scale from 1,000 Fol/2 SP at Rank F
up to 80,000 Fol/100 SP at Rank A.

**Survival Battle**: a 50-fight gauntlet against progressively harder enemies, recommended only at
character level ~110+. Reward for completion: the **Fortune** accessory (ID 773).

## Status

VERIFIED against disc item database (`artifacts/so2-items/items_database.json`). Item names corrected to authentic PS1 US localized titles (Bunny Shoe ID 393, Ganze Sea Urchin ID 785, Yarma Cooking Set ID 822). Gameplay and bracket logic remain fan-sourced reference.
