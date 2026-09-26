# SO2 Precious/Story Items Reference

Compiled 2026-09-25 from RPGClassics' SO2 "Precious Items" shrine (Drak) — a structured,
actively-maintained wiki page. Data (item names, where they're found, and their story purpose)
extracted and reorganized for this project's reference; original prose is copyrighted to its
author and is not reproduced.

## What these are

Unlike the weapon/armor items in [SO2-ITEM-RESTRICTIONS.md](SO2-ITEM-RESTRICTIONS.md), these are
non-equippable key items needed to progress the main story — they show up under "Precious Items" in
the Item Creation list but can't be used directly. Several are **route-exclusive** (Claude's game
vs. Rena's game), which is directly relevant to this project's save format:

- **Communicator** — Claude's game only, disappears after Eluria Tower.
- **Hut Key** — Rena's game only (after beating Azamgil in Heraldry Forest).
- **Rena's Hairpin** — Rena's game: start with it. Claude's game: found in Alen-Tax's mansion.
- **Rena's Pendant** — Rena's game only; not obtainable in Claude's game.

## Why this matters for the save format

This project has an open investigation into **story/event flags** (see
[SAVE-FORMAT.md](SAVE-FORMAT.md)'s "Known open items" — a ~48-byte block at old-raw-offset
`0x02B4`-`0x02E3`, all-zero early game, densely set late game; needs redoing as a decoded-state
diff per the compression discovery). Acquiring one of these precious items is a discrete,
easy-to-trigger story beat — a natural candidate for a clean before/after test to find the first
flag bits that flip, the same way the specialty-purchase tests worked once done as a decoded diff.
Route-exclusive items (Communicator/Hut Key/Rena's Pendant/Hairpin) are especially useful as test
cases since they should correspond to a flag that's reliably different between the two routes.

## Full item list (name — where obtained — purpose)

| Item | Where obtained | Purpose |
|---|---|---|
| Ancient Writings | End of Cross Cave | Give to Keith in Linga after the Lacour Tournament of Arms |
| Card Key | Password "APOCA" to the priest statue in Eluria Tower | Opens Eluria Tower's red barriers |
| Chisato's Job ID | Cave of Red Crystal, after required Central/North City scenes | Talk to Chisato with it to recruit her |
| Clarisage | Sanctuary of Linga (mutually exclusive with Dill Whip) | Show Bowman to get taken to Keith |
| Communicator | **Claude's game only** — starts with it | Disappears after Eluria Tower |
| Dill Whip | End of Sanctuary of Linga (if no Clarisage) | Show Bowman to get taken to Keith |
| Energy Stone | End of Hoffman Ruins | Give to King Lacour to power the Lacour Hope |
| Hut Key | **Rena's game only** — after beating Azamgil in Heraldry Forest | Opens the hut to rescue the children |
| ID Card | Given by the Eluria Colony armory man | Opens the door to Eluria Tower |
| Jewel of Courage | End of Field of Courage | Needed to defeat the Ten Wise Men |
| Jewel of Intelligence | End of Field of Intelligence | Needed to defeat the Ten Wise Men |
| Jewel of Love | End of Field of Love | Needed to defeat the Ten Wise Men |
| Jewel of Power | End of Field of Power | Needed to defeat the Ten Wise Men |
| LEA Metal | After defeating Bark in Mihne Cavern | Needed for Void Matter, Sacred Tear, Fallen Hope |
| Link Stock | COT Level 1 | Use Link Combo without stealing another character's Killer Move |
| Metox | Lassguss Mountain, Eleanor sidequest (Ashton in Rena's game / Bowman in Claude's) | Give to Eleanor to heal her |
| N.F.I.D. | Given by Narl after first Fienal attempt | Free access to Fun City |
| Pandora's Box | Given by the Dean after reading North City archive secrets 1-2 | Give to Professor Rayfus for secrets 3-4 |
| Passport | Given by the King of Cross, later the Captain after Clik's destruction | Passage to the continent of El |
| Rena's Hairpin | **Rena's game**: start with it. **Claude's game**: found in Alen-Tax's mansion | No gameplay purpose |
| Rena's Pendant | **Rena's game only** — start with it | Key item, not otherwise usable |
| Rune Codes | Given by Narl once you have a Synard | Access to the four Fields |
| Silver Goblet | Mountain Palace, with Ashton | Needed to exorcise Gyoro and Ururun |
| Tears of the King | After beating XINE on Lassguss Mountain | Needed to exorcise Gyoro and Ururun |
| The Key to Mihne Cave | Given after the Heraldry Research Lab scene | Allows entering Mihne Cavern |
| Tournament Pass | Given after registering for the Lacour Tournament of Arms | Pick a weapon shop sponsor |
| Treasure Map | Given by Celine when first met | Reach the end of Cross Cave |
| Void Matter | Given in Fun City after giving Mirage the LEA Metal | Allows damaging the Ten Wise Men |
| Warrior Statue | Field of Courage | Starts that field's boss fight |

## Status

LIKELY, not code-verified — same caveat as the other fan-sourced reference docs. Not yet
cross-checked against any real save (no story-item acquisition test has been run this session).
