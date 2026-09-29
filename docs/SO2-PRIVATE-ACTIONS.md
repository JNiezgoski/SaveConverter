# SO2 Private Actions (PAs) Reference — Both Routes

Compiled 2026-09-25 from RPGClassics' SO2 Private Actions shrine (contributor: Ian Kelley), covering
both Rena's-route and Claude's-route PAs. Structural facts (location, trigger requirement,
mechanical effect) extracted for this project's reference; the actual dialogue and choice text is
not reproduced — that's real game script, unlike the simple fact tables in this project's other
reference docs. (The source also publishes "by place" versions of both lists — same PAs, just
re-sorted by town instead of by character; no new facts there, so not separately compiled here.)

## Why this matters for the save format

This directly addresses the still-open **"Private Actions"** item in `SAVE-FORMAT.md`'s known-open
list, and is a strong lead for the also-open **story/event flags** investigation: PAs are one-time,
cleanly-gated events (each needs a specific location + a specific prior-state requirement) that
produce a specific, testable effect — exactly the shape of before/after test needed for a clean
decoded-state diff, the same technique that worked for the specialty-purchase tests. A PA that's
about to trigger (met its requirement, not yet seen) is an excellent save-before/save-after test
case, probably cleaner than a random story beat since the trigger condition is already known.

Two PAs explicitly set a **"special ending flag"** (Ashton's Herlie(3), Celine's Cross(3)) — call
this out specifically as the single best test candidate, since it's described as a discrete boolean
state change with a known narrative consequence (an alternate ending), not just a numeric FP/RP
adjustment.

## The mechanic

A Private Action is a location-gated, mostly one-time scene, usually presenting a dialogue choice
that adjusts one or more characters' Friendship/Romance Points (see
[SO2-EMOTIONAL-LEVELS.md](SO2-EMOTIONAL-LEVELS.md)) toward each other, and sometimes: gives an item,
unlocks a later PA, recruits or loses a party member, or sets a special-ending flag. Many are gated
on a specific EL threshold or on having previously seen a different PA — they chain together.

## PA list (location — requirement — what changes, no dialogue)

| PA | Location | Requirement | Effect (mechanical only) |
|---|---|---|---|
| Ashton — Arlia | Item shop | 2000+ Fol | Choice: gain a Salamander Helmet (costs 75% of Fol) or no change |
| Celine & Ashton — Salva | Jewelry store | — | Gain one of 3 possible rings; several FP changes among Rena/Celine/Ashton |
| Ashton — Herlie (1) | Outside Eleanor's house | — | Unlocks Herlie PA 2 |
| Ashton — Herlie (2) | Inside Eleanor's house | Seen PA 1 | Unlocks Metox Plant search on Lassguss Mountain |
| Ashton — Herlie (3) | Auto-triggers entering Herlie | Have Metox Plant | **Sets a special-ending flag for Ashton** (overridden if his EL for someone else exceeds 20) |
| Ashton — Giveaway | Inn, top floor | — | FP change; one choice-branch also affects RP |
| Ashton & Precis — Fun City | Battle Stadium | FP>8, Ashton knows "Sword Dance" | Item/skill unlock ("Holoprojector" / "Holoholograph" per two source mentions) |
| Bowman — Arlia | Newlyweds' house | — | FP change; one branch unlocks a later Linga PA |
| Bowman — Salva | Jewelry store | — | FP change; choice affects a later Linga PA's variant |
| Claude & Bowman — Cross | In front of church | — | FP/RP decrease (all choices) |
| Bowman — Linga (1)/(2)/(3) | Library / his house / his store | Chained on earlier Bowman PAs | FP/RP changes, variant depends on earlier choices |
| Celine — Arlia | Right screen | Before Mars quest | FP increase |
| Celine — Salva | Jam store | After Clik destroyed | Branches into a follow-up scene; FP changes |
| Celine — Cross (1)/(2)/(3) | Various | Chained | (3) **Sets a special-ending flag for Celine** (overridden if her EL exceeds 26); also moves two NPCs |
| Celine — Hilton (1)/(2) | Various | — | FP/RP changes |
| Celine & Precis — Lacour | West end of town | — | FP changes among Rena/Celine/Precis |
| Celine — Fun City | Battle Stadium | FP≥8 with Claude, Celine knows Compounding | Large FP/RP changes |
| Chisato — Central City (1)/(2)/(3) | Grocery / newspaper office | Chained; (2) needs prior Rayfus dialogue | FP/RP changes; advances a side quest |
| Chisato — Giveaway | University library | Not all 4 Fields finished | No mechanical change |
| Claude — Arlia (1)/(2) | Various | Story-progress gated | FP/RP changes |
| Claude — Salva | North screen | — | FP/RP changes; unlocks a Mars PA |
| Claude — Cross | En route to castle | Before Mars quest | FP change |
| Claude — Mars | Bench | Before Lacour Tournament, after Salva PA | FP/RP changes |
| Claude — Central City | Main square | After final Fienal visit | RP change |
| Claude & Opera — North City | Synard Home | Ernest not in party | Large FP/RP changes for Claude/Opera/Rena |
| Claude — Giveaway | College | RP≥10 with Claude, highest among females | FP/RP change |
| Ernest & Noel — North City | Synard Home | — | FP/RP changes; unlocks lore dialogue |
| Noel — Central City | Inn, 5th floor | — | RP/FP change |
| Noel — Giveaway | His house | — | Small FP decrease |
| Opera — Arlia (1)/(2) | General store / Elder's balcony | (2) repeats until Ernest recruited | FP changes; (2) determines whether Ernest joins or Opera leaves |
| Opera — Salva | Weapon store | — | FP change |
| Opera — Herlie | Outside Eleanor's house | Have "Seventh Ray" weapon | No mechanical change |
| Precis — Arlia | Mayor's house, 2nd floor | — | FP increase |
| Precis — Salva | Jam Shop | — | FP increase |
| Precis — Mars | Tool shop | Before Lacour Castle visit | FP change; unlocks a Giveaway PA |
| Precis — Linga (1)/(2) | Her house area | (1) needs Bowman not in party | (1) recruits Precis; (2) gives a Meteorite |
| Precis — North City | Center square | FP≥8 | FP/RP increase |
| Precis — Giveaway | Various | Chose recruit option in Mars PA | Hide-and-seek minigame; reward is a Nuclear Bomb |
| Precis — Armlock | Mirage's study | Mid-story window | No mechanical change |
| Filia — Clik | Fountain | Before Clik destroyed | Pickpocket target (Mischief item); unlocks a later Central City PA |
| Filia — Central City | City Hall | Late-game save point reached, Clik PA seen | Disables a boss's "Limiter"; awards Israfil's Tear |
| Little Girl — Hilton | Outside Skill Guild | — | FP changes for whichever party members are present |
| Old Woman — Lacour | West Lacour | Before Linga quest | Fetch-quest; rewards a Star Ruby and Rainbow Diamond |
| Three-Eyed Man — Cross | North of entrance | Before Lacour boat | Required to eventually recruit Opera/Ernest |
| Vendor — Linga | Outside university | — | Optional purchase (loses Fol, gains a book) |
| Yul — Herlie (1)/(2) | Various | Chained | Optional boss fight (Zand, 6,000 HP); outcome affects RP and a later encounter |

## PA list — Claude's route

| PA | Location | Requirement | Effect (mechanical only) |
|---|---|---|---|
| Ashton — Arlia | Item shop | 2000+ Fol | Choice: gain Salamander Helmet (costs 75% of Fol) or no change |
| Ashton — Salva | Salva Drift entrance | Gyoro/Ururun quest done | FP/RP increase |
| Ashton & Precis — Cross | West end of town | 100+ Fol | Item (Music Box + Fol) or FP/RP changes depending on choice |
| Ashton — Mars | East side of town | — | FP change (varies by choice) |
| Ashton — Armlock | Outside restaurant | — | FP/RP changes |
| Ashton & Precis — Fun City | Battle Stadium | FP>8, Ashton knows "Sword Dance" | Precis learns "Holoholograph" |
| Bowman — Arlia/Salva/Cross | Various | — | FP changes (Cross variant: none) |
| Bowman — Herlie (1)/(2)/(3) | Eleanor's house area | Chained; (2) needs Metox Plant | FP increases; unlocks Linga PA and Metox search |
| Bowman — Linga (1)/(2) | His store / library | Chained on Arlia/Herlie choices | FP change; (2) unlocks Lassguss Mountain Metox search |
| Celine — Arlia | Item shop | — | RP increase; can yield a Talisman item |
| Celine — Salva | Jam store | After Clik destroyed | FP changes, branches into a follow-up scene |
| Celine & Rena — Cross | East alley | After Clik destroyed, before Mars quest | FP changes (all negative or neutral) |
| Celine — Mars | Celine's house | Celine not in party, Bowman in party | No EL change; unlocks a Holy Ring purchase |
| Celine — Hilton | Inn, left side | — | FP/RP decrease |
| Celine — North City | Inn | Before finishing 4 Fields | FP/RP changes, one branch gives a large RP/FP boost |
| Chisato — Central City (1)/(2) | Newspaper office | Chained; needs prior Rayfus dialogue | Advances a side quest |
| Chisato — North City | "Blue Flask" item shop | Chisato's RP>10 for Claude | FP/RP changes |
| Chisato — Giveaway | University library | Not all 4 Fields finished | No mechanical change |
| Ernest — Giveaway | University classroom | — | FP change |
| Leon — Armlock | Mirage's house | — | FP/RP increase |
| Leon — Fun City | Bar | Leon's FP>8, Cooking Master side game done | FP increase; unlocks a follow-up RP scene with any female party member |
| Noel — Giveaway | His house | — | Small FP decrease |
| Opera — Arlia | Elder's balcony | Repeats until Ernest recruited | Determines whether Ernest joins or Opera leaves |
| Opera — Salva | Weapon store | — | FP/RP changes |
| Opera — Central City | Bar | Ernest not in party | FP/RP changes (multiple branches) |
| Opera — North City | Synard Home | Ernest not in party | Large FP/RP increase |
| Rena & Precis — Arlia | In front of Rena's house | After Lacour Tournament | RP changes (three-way branch) |
| Precis — Cross | West end of town | — | Item (Weighty Rings/All-Purpose Knife/Aphrodisiac) + RP changes |
| Precis — Salva | Jam Shop | — | Unlocks a Linga PA |
| Precis — Mars (1)/(2) | Tool shop / west end | Chained | FP changes; (1) unlocks a Giveaway PA |
| Precis — Linga (1)/(2) | Pharmacy area / her house | (1) needs Bowman not in party | (1) recruits Precis; (2) FP/RP change |
| Precis — North City | Front square | After final Fienal visit | Large FP/RP changes |
| Precis — Giveaway | Various | Chose recruit option in Mars PA | Hide-and-seek minigame; reward is a Nuclear Bomb |
| Precis — Armlock (1)/(2) | Bar 2nd floor / Mirage's study | Chained | FP/RP changes |
| Rena — Arlia | Her room | Route/story-progress gated | RP change |
| Rena — Salva (1)/(2) | Southern screen / jewelry store | (2) needs King of Cross met | (1) flashback, no EL change; (2) item (Leaf Pendant) + FP/RP changes |
| Rena — Cross | Church | Either RP <9 | FP/RP decreases |
| Rena — Mars (1)/(2) | Various | Story-progress gated | FP/RP changes |
| Rena — Linga | Outside library | — | FP increase |
| Rena — Central City | Inn, 2nd floor | Before finishing 4 Fields | FP/RP changes (multi-branch) |
| Rena — North City | Library | — | No mechanical change |
| Rena — Armlock | Auto-triggers | Specific prior Ashton-PA choices | FP/RP changes |
| Rena — Fun City | Fortune teller | Rena's RP for Claude >10-12 | FP/RP changes (multi-branch) |
| Little Girl — Salva | Same as Rena's Salva PA | After King of Cross met | Party-wide FP change; one branch gives a Harmonica |
| Three-Eyed Man — Cross | North of entrance | Before Lacour boat | Required to eventually recruit Opera/Ernest |
| Chris — Hilton | By the boat | Celine not in party, before Linga quest | Can yield a ring item |
| Little Girl/Child — Hilton/Herlie/Lacour/Linga | Various | Chained across towns | FP changes; can trigger a fight (Lessassassins) yielding Neo Greaves/Core Plate |
| Filia — Clik/Central City | Fountain / City Hall | Chained | Pickpocket item (Mischief); later disables a boss's "Limiter" and awards Israfil's Tear |
| Old Woman — Lacour | West Lacour | Before Linga quest | Fetch-quest; rewards Star Ruby and Rainbow Diamond |
| Vendor — Linga | Outside university | — | Optional purchase (loses Fol, gains a book) |
| Marianna — Fun City | Battle Stadium | After first Fienal visit, before Mihne Cavern | Rewards Silver Cross and Slayer's Ring |

## Status

**VERIFIED (Engine Mechanics & Bytecode Tracing)**:
While individual PA branching conditions originate from compiled community play-throughs, the underlying VM execution engine is 100% verified via static disassembly and bytecode analysis in [docs/SO2-CHUNK1-MAPPING.md](SO2-CHUNK1-MAPPING.md):
- Resident script sub-dispatcher `80064F30` executes opcodes `0xFF10` / `0xFF90` (Matrix A / FP adjust) and `0xFF12` / `0xFF92` (Matrix B / RP adjust).
- Concretely verified in Disc 1 Scene 688 (Archive 3895, Fun City Bar: "Leon's Confession") where dialogue choices directly execute `0xFF10` to adjust mutual FP between Leon (ID 7) and Rena/Celine/Precis/Opera/Chisato by +3 or -2, modifying save Chunk 1 offsets `0x058` and `0x0E8`.
