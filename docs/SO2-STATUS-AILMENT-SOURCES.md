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

## Status

VERIFIED against `artifacts/so2-enemies/enemies_database.json`. Enemy names corrected to authentic internal ROM strings (Cokatricking without 'c', Wisesorcerer with '-er', Iselia-queen in Arc 1966). Ailment infliction mechanics remain gameplay reference pending save-state diffing.
