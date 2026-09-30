# SO2 Status Ailment Sources (from the Enemies Reference)

Compiled 2026-09-25 from RPGClassics' SO2 "Enemies" shrine — extracted for the specific purpose of
planning the still-open **status ailment** investigation (poison/paralysis/stone are noted as
"entirely unmapped" in this session's earlier notes). The full enemy bestiary (~200 entries with
HP/MP/elemental resistance/EXP/drops) is not reproduced here — it's mostly gameplay reference with
no established save-format connection; only the status-ailment-relevant subset is kept.

## Notation key (from the source)

Each enemy can carry short-code notes for special abilities. The ones relevant to status ailments:

- **POI** — can poison a character
- **PAR** — can paralyze a character
- **STO** — can turn a character to stone

(Other codes exist for non-ailment mechanics — splitting, gulping, invincibility phases, etc. — not
reproduced here since they're not relevant to this project's open items.)

## Enemies that can inflict Poison (POI)

Alraune (Cross Continent/Cross Cave), Bugbear (Heraldry Forest), Landworm (Cross Continent/Cross
Cave), Gerel (Salva Drift Pt. 2), Otif (Energy Nede/Field of Courage), Ghastricgel-adjacent bosses,
Evilwater (Mihne Cavern), Meduslizzard (Fienal), Robinmaster (COT 9), F-thiefL99 (COT 6/7),
Weirdknight (COT 1), Punkponk (COT 4/6), Orbiterbeast (COT 7), Vesper (Fienal), Masterwizard (Field
of Love/Fienal), Soulmaster (COT 13), Visseyer (Sanctuary of Linga), Raystinger (Energy
Nede/Cave of Red Crystal), Ooze (Sanctuary of Linga), Lastavenger (COT 7).

## Enemies that can inflict Paralysis (PAR)

Alraune (Cross Continent/Cross Cave), Flyingray (Lasguss Mountain/Lacour Continent), Ghast (Field of
Power), Salamander (Hoffman Ruins), Slimepool (Mountain Temple), Ooze (Sanctuary of Linga),
Raystinger (Energy Nede/Cave of Red Crystal), Otif (Energy Nede/Field of Courage), Masterwizard
(Field of Love/Fienal), Meduslizzard (Fienal), Wisesorcerer (COT 9, Arc 1965), Lessassassin (Herlie, Claude's
route only).

## Enemies that can inflict Stone (STO)

Coldlizard (Eluria), Cockatrice (Lasguss Mountain/Lacour Continent), Fenrilbeast (Field of Courage),
Ghast (Field of Power) — via Paralysis Check drop hint, Periton (Cave of Red Crystal), Otif (Energy
Nede/Field of Courage), Ooze (Sanctuary of Linga), Meduslizzard (Fienal), Masterwizard (Field of
Love/Fienal), Bloodgerell (COT 2/3), Cokatricking (COT 9, Arc 1763), Wisesorcerer (COT 9, Arc 1965), Iselia-queen
(bonus superboss, Arc 1966).

## Practical note for testing

**Alraune** (Cross Continent / Cross Cave — very early game, Arc 1428) inflicts Poison and is one of the
earliest-accessible enemies on this list, making it a strong candidate for a real controlled
poison-status save test without needing to progress far. For Paralysis, **Ghast** (Arc 1556) or **Ooze**
(Arc 1497, mid-game, Field of Power / Sanctuary of Linga) are earliest options.

## Self-inflictable items (no enemy encounter needed — much more practical for a controlled test)

Sourced from `sources/Star Ocean_ The Second Story - Guide and Walkthrough - PlayStation - By A_I_e_x
- GameFAQs.html` (already saved locally, previously not extracted into this doc). "Always Usable"
items can be used on yourself outside of battle directly from the item menu; "Battle Only" items
generally cannot self-target (checked separately, see the incident note below).

| Item | Category | Effect | Notes |
|---|---|---|---|
| **Wolfsbane** | Always Usable | Poisons user | ~360 Fol, also a Compounding ingredient — best single candidate for a controlled Poison test |
| **Danger Pot** / **Nightmare Pot** | Always Usable | Heals the wounded, poisons/petrifies the healthy | Random outcome — use on a full-HP character for a chance at either Poison or Stone in one item |
| **Rotten Sashimi** | Food (non-battle) | Poisons user | A failed 'Seafood' cooking result, not directly purchasable |
| **Mandrake** | Always Usable | Kills user | Not useful for ailment testing (death, not poison) despite the name overlap with the Mandrake enemy |

**Confirmed NOT self-targetable** (checked against `Item Encyclopedia - EternalSphere.html`'s own
effect text before recommending them, then corrected): Killer Poison ("poisons the **nearest
monster**"), Paralysis Oil ("paralyzes **one enemy**"), Paralysis Mist ("paralyzes **all enemies**") —
all three are Battle Only and explicitly enemy-targeted by their own in-game description. Don't
recommend these for self-infliction again without re-checking; this was a real dead-end already hit
once.

## Save-format result (2026-09-29) — fully solved, live-confirmed

The save-state byte this whole investigation was aimed at is the per-character condition byte at
decoded `0x1A0 + slot*0x60 + 0x02` (mirrored at uncompressed card-header `0x0234 + slot*4 + 0x01`).
Full field-map entry and disassembly citations: `docs/SO2-PARTY-MEMBER-INVESTIGATION.md`'s field map,
`+02` row.

| Bit | Hex | Condition | Visible effect | Menu-blocking? |
|:---:|:---:|---|---|:---:|
| 0 | `0x01` | Dead / KO'd | Greyed out, HP shown as-is (doesn't force HP to 0 on its own) | Yes |
| 1 | `0x02` | Paralysis | No portrait change — icon next to HP bar only | Yes |
| 2 | `0x04` | Stone / Petrify | Grey stone palette; visually overrides Poison's tint if both are set | Yes |
| 3 | `0x08` | Poison | Purple palette; character stays fully controllable | No |

Bits 0/1/2 are gated as a group (`primary[2] & 7`) for Equipment/Skills/Specialty menu access; Poison
sits outside that mask. All four bits are independently tracked and freely combinable — confirmed live
with all four set simultaneously on one character (Stone's palette just visually hides Poison's tint
until Stone is cured; the underlying Poison bit was there the whole time).

**Live-testing gotcha worth keeping in mind if anyone else self-inflicts a status for testing:**
equipped accessories can silently block a status ailment from displaying even when the save byte is
set correctly. Necklace and Reverse Doll both did this in testing (both have vague "might protect its
wearer" flavor text). The item master table has a documented "Status Ailment Mask" field
(`+0x26..+0x27` in the 48-byte item record, see `tools/build_item_database.py`) that in principle
should predict this, but it read `0x0000` for Necklace, Reverse Doll, **and** "Resistance Ring" (an
item that should obviously show something) — that field can't be trusted as-is. If testing ailments
on a character with any accessory equipped, either strip accessories first or swap to an accessory
already proven neutral in that exact save (e.g. one already worn by a character showing an unblocked
ailment).

## Status

VERIFIED against `artifacts/so2-enemies/enemies_database.json`. Enemy names corrected to authentic internal ROM strings (Cokatricking without 'c', Wisesorcerer with '-er', Iselia-queen in Arc 1966). Save-state side (the condition byte and its 4 bits) is now fully solved and live-confirmed — see the section above. The enemy/item lists above remain useful as gameplay reference for anyone re-running a live test.
