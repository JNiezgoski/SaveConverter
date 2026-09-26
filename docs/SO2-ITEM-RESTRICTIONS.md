# SO2 Item Restrictions Reference

Compiled 2026-09-25 from two third-party fan sources — data (which items are restricted to which
characters) was extracted and reorganized here for the project's own reference; original prose from
either source is copyrighted to its authors and is not reproduced:

1. RPGClassics' SO2 Weapons and Armor shrines (Drak) — structured, actively-maintained wiki pages
   with consistent per-character letter/group codes. **Primary source** for everything below.
2. Star Ocean 2 Item List v1.7 (Jack N., 1999) — an older, less structured, crowdsourced community
   FAQ, self-described as incomplete. Superseded by (1) for weapons; no longer used.

## Status: LIKELY, cross-validated against real equip failures

Treat everything below as **LIKELY** rather than fully VERIFIED-from-code, but note it's now been
directly confirmed against real in-game equip attempts multiple times, not just trusted blind:

- **Empresia (R), Titan's Fists (B), Aura Blade (C)** — all currently equipped per this data,
  and all working correctly in-game.
- **Serpent's Tooth (N, Noel-exclusive)** — failed to equip on Rena and Bowman in-game, exactly as
  the single-letter code predicts.
- **Star Guard (As/Bo/Ch/Cl/Di/Er/Op/Pr)** — failed on Rena and Leon in-game, exactly matching
  their absence from that equip group. Bowman **is** in the group and confirmed working.
- **Leather Helm (All)** — confirmed working for Leon in-game.

Every real-world test so far has matched this source exactly (5/5). Still worth a quick check
before hand-equipping anything not yet tested, since it's fan-transcribed data, not code-verified.

## Armor equip-group key (RPGClassics notation)

- **Fighters**: Ashton, Bowman, Chisato, Claude, Dias, Ernest, Noel, Opera, Precis
- **Magicians**: Celine, Leon, Rena
- **Males**: Ashton, Bowman, Claude, Dias, Ernest, Leon, Noel
- **Females**: Celine, Chisato, Opera, Precis, Rena
- Individual characters given as two-letter codes (Cl=Claude, Re=Rena, Le=Leon, etc.) when the
  restriction doesn't match one of the broad groups above.

Note the game's own two coarse "class" groupings (Fighters/Magicians) don't map onto the finer
weapon-type restrictions above (Sword/Knuckles/Book/etc.) — they're a separate, broader armor-only
classification. Also note: **Noel counts as a Fighter for armor purposes** despite using
Knuckles/magic-adjacent weapons.

## Weapon restrictions, by type (letter code = single owner within that type unless noted)

Codes: C=Claude, D=Dias, As=Ashton, B=Bowman, N=Noel, R=Rena, Pr=Precis, Ce=Celine, Op=Opera,
Er=Ernest, Le=Leon, Ch=Chisato. A weapon type used by only one character (Books, Dual Swords,
Mechanical Hands, Rods, Stun Guns, Whips, Energy Packs) has no per-item code — the whole category
belongs to that character; only Swords and Knuckles are genuinely shared across multiple people.

**Swords (Claude, Dias)** — `C`: Aura Blade, Broad Sword, Eternal Sphere, Force Sword, Golden
Fangs, Heart Breaker, Long Edge, Sacred Tear, Sawed, Sinclair Sabre, Veil Piercer, Windsley Sword.
`D`: Baselard, Bastard Sword, Crimson Diablos, Cromlea Sword, Hard Cleaver, Murasame Sword,
Oriental Blade, Pleiad Sword, Ruins' Fate, Sharpness, Soul Slayer, The Hope of Breeze, Whirlwind.
`C/D`: Dull Sword, Flame Blade, Grand Stinger, Gusguine (C-only per some sources), Ignite Sword,
Long Sword, Marvel Sword, Minus Sword, Sharp Edge, Silvance, Silver Fangs (C-only), Walloon Sword,
Worn-out Sword. Multi-user (see below): Holy Sword Farwell, Levantine Sword (also Ashton).

**Knuckles (Bowman, Noel, Rena)** — `B`: Asura, Bagh Nakh, Flare Burst, Giant Fists, Hecatoncheire,
Titan's Fists. `N`: Cat's Fangs, Death Fangs, Eagle's Claws, Grizzly Claps, Platinum Nails,
Serpent's Tooth (**exclusive — confirmed by failed equip attempt on Rena/Bowman**), Tiger's Fangs.
`R`: Empresia, Fallen Hope, Fellper Nails. `B/R`: Braised Knuckles, Cestus, Magical Gloves,
Sorceress Knuckles. `N/R`: Dragon's Claws, Metal Fangs. `B/N/R`: Hard Knuckles, Kaiser Knuckles,
Knuckles, Worn Knuckles. `R` only (Rune Full Moon), `R` only (Pain Cestus, contradicts one older
source that also listed Noel — the RPGClassics single-letter code takes priority here as the more
structured source), `B` only (Moon Fists).

**Books (Leon)**: All About ESP, Ancient Wisdom, Book of Awakening, Book of Chaos, Book of Darkness,
Brain Structure, Dictionary, Encyclopedia, Heraldry, Heraldry Book, Holy Scriptures, Illustrated
Book, Mental Revolution, Reference Book, Thick Book, Treatise.

**Dual Swords (Ashton)**: Both Shaver, Doubledemon Sword, Double Masher, Gemini, Guard Sword, Holy
Cross, Lotus Eater, Melufa, Pair Nuts, Scyther, Shield Sword, Smaller, Twin Picks, Twin Swords,
Twin-Edge, Wobbly Sword.

**Mechanical Hands (Precis)**: Atomic Punch, Burning Hand, Fire Punch, Great Punch, Hyper Punch,
Ice Punch, Iron Punch, Magic Hand, One-two Punch, SD Punch, SDUGA Punch, Spark Hand, Straight
Punch, Thunder Punch, UGA Punch, Ultra Punch.

**Rods (Celine)**: Bent Rod, Clap Rod, Crest Rod, Dragon's Tusk, Holy Rod, Magical Rod, Prime
Prayer, Rod, Rod of Snakes, Ruby Rod, Ruby Wand, Silvermoon, Silver Rod, Tongue Twister.

**Stun Guns (Chisato)**: 10 Volt Stun Gun, Aero Gun, Cracker, Electric, Electro Gun, Electron,
Flame Gun, Flare Gun, Freeze, Lightning Gun, Psychic Gun, Shock Gun, Spark, Stun Gun, Voltage.

**Whips (Ernest)**: Cat o'9 Tails, Dark Whip, Flare Whip, Freeze Whip, Hard Whip, Invisible Whip,
Leather Whip, Light Whip, Limp Whip, Molecule Wire, Rose Whip, Spark Whip, Splinter, Twin-tail.

**Energy Packs for Kaleidoscope (Opera)**: Alpha Box, Beta Box, Black Box, Booster Box, Burst Box,
Gamma Box, Magic Box, Psycho Box, Pulse Box, Radio Box, Seventh Ray, X Box.

**Multi-user weapons (any of the listed characters)**: All-Purpose Knife/Funny Slayer (Everyone),
Holy Sword Farwell/Levantine Sword (As/Cl/Di), Million Staff (Ce/Le/No), Weird Slayer
(Bo/Ch/No/Pr/Re).

## Body armor (equip group)

All: Leather Armor, Odd Clothes, Flashy Armor. Fighters: Banded Mail, Barrier Armor, Bloody Armor,
Brigandine, Mithril Mesh, Plate Mail, Steel Armor. Magicians: Holy Cloak, Ishtar's Robe, Mirage
Robe, Robe, Silk Robe, Silver Robe, Star Cloak, Flying Hawk Robes. Males: Valiant Mail. Females:
Evening Dress, Mithril Dress, Valkyrie's Garb. Specific: Amber Robe (Ce/Le/Re), Chaos Mail
(As/Bo/Ch/Cl/Di/Er/No/Op), Core Plate (As/Bo/Ch/Cl/Di/Er/No/Op), Duel Suit (As/Cl/Di), Jeanne's
Armor (Ch/Op/Pr), Mithril Coat (Bo/Ce/Ch/Er/Le/No/Op/Pr/Re), Reflective Armor
(As/Bo/Ch/Cl/Di/No/Op/Pr), Sylvan Mail (Ch/Op/Pr), Wizard's Mail (Ce/Le/No/Re). Seraphic Armor and
Battle Suit: All. Perforated Armor: nobody (failed-creation item).

## Shields (equip group)

All: Buckler, Rare Gauntlets. Specific: Algol (Ch/Pr), Barrier Shield (Cl/Di/Er/Pr), Crestier Guard
(Cl/Di/Er/Pr), Fine Shield (Cl/Di), Knight's Shield (Cl/Di), Jeanne's Shield (Ch/Pr), Mithril Shield
(Cl/Di/Er/Pr), Odd Gauntlets (Cl/Di/Pr), Odd Shield (Cl/Di/Pr), Pallas Athena (Cl/Di/Er/Pr), Round
Shield (Cl/Di/Er/Pr), Rune Buckler (Ce/Le/No/Re), **Star Guard (As/Bo/Ch/Cl/Di/Er/Op/Pr — NOT
Re/Le/Ce/No, confirmed by real equip failure on Rena and Leon)**, The Armband of Kali
(Ce/Ch/Pr/Re), Valiant Guard (Males), Valkyrie Guard (Females), Wooden Shield (Cl/Di/Er/Pr).

## Head armor (equip group)

All: Beret, Crown, Golden Crown. Fighters: Banded Helm, Duel Helm, Frog, Iron Helm, Mithril Helm,
Odd Helmet, Plate Helm, Steel Helm. Magicians: Hermit's Helm, Isis Tiara, Odd Hat, Rune Cap,
Wizard's Hat. Specific: Bloody Helm (As/Bo/Ch/Cl/Di/Er/No/Op), Dream Crown (Ce/Le/No/Re), **Leather
Helm (All — confirmed working for Leon)**, Jeanne's Helm (Ch/Op/Pr), Moon Tiara (Ce/Re), Odin's
Helm (As/Cl/Di), Sylvan Helm (Ch/Op/Pr). Salamander Helmet: Ashton only (Private Action purchase in
Arlia).

## Foot armor (equip group)

All: Boots, Bunny Shoes, Leather Boots, Mud Boots, Odd Shoes, Sandals, Secret Boots, Steel-toed
Boots, Suede Boots. Fighters: Iron Greaves, Leather Greaves, Mithril Greaves, Silver Greaves.
Magicians: High-laced Shoes, Rune Shoes, Witch's Boots. Males: Valiant Boots. Females: Glass
Slippers, Original Boots, Valkyrie Boots. Specific: High Heels (Ce/Ch/Op), Neumann Boots (Precis
only, Machinery Specialty), Pin Heels (Ce/Ch/Op), Plate Greaves (Fighters), Star Greaves
(As/Bo/Ch/Cl/Di/Er/Op/Pr), Sylvan Boots (Ch/Op/Pr).

## Notable non-weapon, non-armor item

- **Israfil's Tear** (accessory) — unique story-quest item, not a general shop/drop item

## How to use this for save editing

Before hand-equipping any weapon via `so2_fol.py`-style decoded-state edits: check the target
character is listed here (or shares the item across characters). If a weapon has no listed
restriction, treat it as unconfirmed rather than assuming it's universal — test cautiously (backup
first) or prefer an item with a clear, matching restriction instead.
