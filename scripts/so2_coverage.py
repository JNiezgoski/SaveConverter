"""Star Ocean 2 decoded-save-state coverage map: what fraction of the 0x1B88-byte
decoded body is understood, region by region.

This is a static knowledge map (facts from docs/SAVE-FORMAT.md and the other
docs/SO2-*.md investigation files), not a per-save byte scanner - it doesn't read
a card. Update RANGES below whenever a new finding narrows an "unknown" range,
then rerun to regenerate the numbers and JSON.

Confidence tiers (deliberately coarser than the per-field VERIFIED/LIKELY/OPEN
tags used in the docs, since this is a coverage overview, not a field reference):
  mapped    - real field(s) with a known decoded offset, confirmed by the game's
              own code and/or in-game testing (may still have open sub-details)
  partial   - location and general shape known, but content/purpose not fully
              pinned down (e.g. two unnamed stat triplets, opaque-but-nonzero bytes);
              also covers bytes exhaustively proven to hold NO references anywhere
              (disc scripts, overlays, resident code) - a real, checked negative
              result, distinct from a byte nobody has looked at yet (see "unknown")
  runtime   - understood to be non-persistent scratch/integrity data, not real
              save content (serializer zeroes and rebuilds it on load)
  unknown   - not examined, or examined and found to hold no established meaning

Total decoded body: 0x1B88 = 7,048 bytes, assembled from 5 chunks with distinct
live-RAM sources (see docs/SAVE-FORMAT.md and SO2-MAP-LOCATION-CHECK.md).
"""
import json
import os

TOTAL = 0x1B88

# (start, end, label, tier, note)  -- end is exclusive. Non-overlapping by construction
# (checked at the bottom). Keep ranges in ascending order for readability.
RANGES = [
    # ---- chunk 1 (0x000-0x1A0): mostly unmapped; scattered Options/Fol/disc fields ----
    (0x00, 0x10, "Key customization: 8x u16 button masks", "mapped", "docs/SO2-OPTIONS-MENU-INVESTIGATION.md"),
    (0x18, 0x1C, "Fol (money), u32", "mapped", "docs/SO2-FOL-INVESTIGATION.md"),
    (0x30, 0x40, "Message window corner colors, 4x u32 0x00BBGGRR", "mapped", "docs/SO2-OPTIONS-MENU-INVESTIGATION.md"),
    (0x44, 0x45, "Sound output (Surround/Stereo/Monaural)", "mapped", "docs/SO2-OPTIONS-MENU-INVESTIGATION.md"),
    (0x46, 0x47, "Vibration on/off", "mapped", "docs/SO2-OPTIONS-MENU-INVESTIGATION.md"),
    (0x49, 0x4A, "Targeting mode", "mapped", "docs/SO2-OPTIONS-MENU-INVESTIGATION.md"),
    (0x4A, 0x4B, "Camera work", "mapped", "docs/SO2-OPTIONS-MENU-INVESTIGATION.md"),
    (0x4B, 0x4C, "Combat motion mode", "mapped", "docs/SO2-OPTIONS-MENU-INVESTIGATION.md"),
    (0x4C, 0x4D, "Required disc (0=Disc1, 1=Disc2)", "mapped", "docs/SO2-DISC-AND-PSYNARD-CHECK.md"),

    # ---- chunk 1, 2026-09-27 pass: 329 new bytes, chiefly two 12x12 matrices ----
    (0x10, 0x14, "Clock-derived word (menu clock/60, save-preview time-style)", "mapped", "docs/SO2-CHUNK1-MAPPING.md"),
    (0x14, 0x18, "Event counter (script-adjustable, zero-floored)", "mapped", "docs/SO2-CHUNK1-MAPPING.md"),
    (0x20, 0x24, "Menu-operation counter (increments on save-menu completion)", "mapped", "docs/SO2-CHUNK1-MAPPING.md"),
    (0x24, 0x28, "Save-preparation counter", "mapped", "docs/SO2-CHUNK1-MAPPING.md"),
    (0x28, 0x2C, "Companion conditional menu-operation counter", "mapped", "docs/SO2-CHUNK1-MAPPING.md"),
    (0x42, 0x43, "Non-default lead-name flag, rename selector 0", "mapped", "docs/SO2-CHUNK1-MAPPING.md"),
    (0x43, 0x44, "Non-default lead-name flag, rename selector 1", "mapped", "docs/SO2-CHUNK1-MAPPING.md"),
    (0x45, 0x46, "Route/lead selector", "mapped", "docs/SO2-CHUNK1-MAPPING.md"),
    (0x54, 0x58, "Menu clock-throttle marker", "mapped", "docs/SO2-CHUNK1-MAPPING.md"),
    (0x58, 0xE8, "Matrix A (Friendship Points): 12x12 character-pair values, 0..15", "mapped", "docs/SO2-CHUNK1-MAPPING.md"),
    (0xE8, 0x178, "Matrix B (Romance/Affection Points): 12x12 character-pair values, 0..15", "mapped", "docs/SO2-CHUNK1-MAPPING.md"),
    (0x178, 0x17A, "Signed completion/result code (script-consumed)", "mapped", "docs/SO2-CHUNK1-MAPPING.md"),
    (0x184, 0x188, "Two signed percentage stat modifiers", "mapped", "docs/SO2-CHUNK1-MAPPING.md"),
    (0x198, 0x1A0, "Two saved save-menu selection words", "mapped", "docs/SO2-CHUNK1-MAPPING.md"),

    # ---- party primary array (0x1A0-0x4A0): 8 slots x 0x60, per-slot map is a stated aggregate ----
    # 66/96 bytes named, 12 bytes two unnamed halfword triplets, 18 bytes opaque - per slot,
    # expressed here as three aggregate sub-ranges per slot rather than exact named byte
    # positions (the source doc gives the aggregate counts, not a clean single offset list).
    *[(0x1A0 + slot * 0x60 + 0x00, 0x1A0 + slot * 0x60 + 0x42, f"Party primary slot {slot}: named fields (ID, EXP, HP/MP/level, STR/CON/AGL/DEX/INT/GUTS)", "mapped", "docs/SO2-PARTY-MEMBER-INVESTIGATION.md") for slot in range(8)],
    *[(0x1A0 + slot * 0x60 + 0x42, 0x1A0 + slot * 0x60 + 0x4E, f"Party primary slot {slot}: unnamed stat triplets (+4E/+50/+52, +54/+56/+58 relative)", "partial", "docs/SO2-PARTY-MEMBER-INVESTIGATION.md") for slot in range(8)],
    *[(0x1A0 + slot * 0x60 + 0x4E, 0x1A0 + slot * 0x60 + 0x60, f"Party primary slot {slot}: opaque bytes (nonzero, no established meaning)", "unknown", "docs/SO2-PARTY-MEMBER-INVESTIGATION.md") for slot in range(8)],

    # ---- party secondary array (0x4A0-0xB20): 8 slots x 0xD0 (208 bytes) ----
    # Full 208-byte map resolved (2026-09-27): LUC/STM triplets (+0..B), equipment 7xu16 (+C..19),
    # SP u16 (+1A..1B), padding (+1C..1F), talent mask u32 (+20..23), name 20 bytes ASCII (+24..37),
    # combat strategy / tactic / battle-mode bytes (+38..3B), 32 availability bytes (+3C..5B),
    # skill sentinel (+5C), 46 skill levels (+5D..8A), padding (+8B), 32 usage/proficiency
    # halfwords (+8C..CB), and 4 quick-assign ability IDs (+CC..CF).
    *[(0x4A0 + slot * 0xD0 + 0x00, 0x4A0 + slot * 0xD0 + 0x0C, f"Party secondary slot {slot}: LUC/STM triplets", "mapped", "docs/SO2-PARTY-MEMBER-INVESTIGATION.md") for slot in range(8)],
    *[(0x4A0 + slot * 0xD0 + 0x0C, 0x4A0 + slot * 0xD0 + 0x1A, f"Party secondary slot {slot}: 7x equipment u16", "mapped", "docs/SO2-PARTY-MEMBER-INVESTIGATION.md") for slot in range(8)],
    *[(0x4A0 + slot * 0xD0 + 0x1A, 0x4A0 + slot * 0xD0 + 0x1C, f"Party secondary slot {slot}: SP (Skill Points) u16 (0..999)", "mapped", "docs/SO2-PARTY-MEMBER-INVESTIGATION.md") for slot in range(8)],
    *[(0x4A0 + slot * 0xD0 + 0x1C, 0x4A0 + slot * 0xD0 + 0x20, f"Party secondary slot {slot}: zero padding / alignment", "mapped", "docs/SO2-PARTY-MEMBER-INVESTIGATION.md") for slot in range(8)],
    *[(0x4A0 + slot * 0xD0 + 0x20, 0x4A0 + slot * 0xD0 + 0x24, f"Party secondary slot {slot}: talent mask u32 word", "mapped", "docs/SO2-PARTY-MEMBER-INVESTIGATION.md") for slot in range(8)],
    *[(0x4A0 + slot * 0xD0 + 0x24, 0x4A0 + slot * 0xD0 + 0x38, f"Party secondary slot {slot}: character name (20 bytes ASCII)", "mapped", "docs/SO2-PARTY-MEMBER-INVESTIGATION.md") for slot in range(8)],
    *[(0x4A0 + slot * 0xD0 + 0x38, 0x4A0 + slot * 0xD0 + 0x3C, f"Party secondary slot {slot}: combat strategy, backup tactic, auto flags, 4-ability flag", "mapped", "docs/SO2-PARTY-MEMBER-INVESTIGATION.md") for slot in range(8)],
    *[(0x4A0 + slot * 0xD0 + 0x3C, 0x4A0 + slot * 0xD0 + 0x5C, f"Party secondary slot {slot}: 32 battle-ability availability bytes", "mapped", "docs/SO2-SPECIAL-ATTACK-LIST-CHECK.md") for slot in range(8)],
    *[(0x4A0 + slot * 0xD0 + 0x5C, 0x4A0 + slot * 0xD0 + 0x5D, f"Party secondary slot {slot}: skill 0 sentinel byte (0x00)", "mapped", "docs/SO2-PARTY-MEMBER-INVESTIGATION.md") for slot in range(8)],
    *[(0x4A0 + slot * 0xD0 + 0x5D, 0x4A0 + slot * 0xD0 + 0x8B, f"Party secondary slot {slot}: 46 skill levels (1 byte each)", "mapped", "docs/SO2-PARTY-MEMBER-INVESTIGATION.md") for slot in range(8)],
    *[(0x4A0 + slot * 0xD0 + 0x8B, 0x4A0 + slot * 0xD0 + 0x8C, f"Party secondary slot {slot}: struct alignment padding (0x00)", "mapped", "docs/SO2-PARTY-MEMBER-INVESTIGATION.md") for slot in range(8)],
    *[(0x4A0 + slot * 0xD0 + 0x8C, 0x4A0 + slot * 0xD0 + 0xCC, f"Party secondary slot {slot}: 32 battle-ability usage counts / proficiencies (32xu16)", "mapped", "docs/SO2-SPECIAL-ATTACK-LIST-CHECK.md") for slot in range(8)],
    *[(0x4A0 + slot * 0xD0 + 0xCC, 0x4A0 + slot * 0xD0 + 0xD0, f"Party secondary slot {slot}: battle-ability quick-assign (4 IDs)", "mapped", "docs/SO2-SPECIAL-ATTACK-LIST-CHECK.md") for slot in range(8)],

    # ---- inventory + adjacent bookkeeping (0xB20-0x1744) ----
    (0xB20, 0x1320, "Inventory: fixed 1,024-slot u16 array", "mapped", "docs/SO2-INVENTORY-ADD-INVESTIGATION.md"),
    (0x1320, 0x1340, "16 recently-touched inventory IDs", "mapped", "docs/SAVE-FORMAT.md"),
    (0x1340, 0x1744, "Runtime integrity bytes - zeroed by serializer, rebuilt on load (not persistent save content)", "runtime", "docs/SAVE-FORMAT.md"),

    # ---- chunk 5 (0x1748-0x1B88): mostly unmapped; scattered map/state fields ----
    (0x1750, 0x175C, "Player position X/Y/Z, signed i32 20.12 fixed-point", "mapped", "docs/SO2-MAP-LOCATION-CHECK.md"),
    (0x1760, 0x1762, "Facing, signed i16", "mapped", "docs/SO2-MAP-LOCATION-CHECK.md"),
    (0x1762, 0x1764, "Scene selector (the real location/archive-selection key)", "mapped", "docs/SO2-MAP-TERRAIN-INVESTIGATION.md"),
    (0x1769, 0x176A, "Saved sprite drawing-order value (formerly miscalled 'area ID')", "mapped", "docs/SO2-MAP-LOCATION-CHECK.md"),
    (0x176C, 0x176D, "Controlled-object table index", "mapped", "docs/SO2-PARTY-MEMBER-INVESTIGATION.md"),
    (0x1860, 0x1861, "Message speed", "mapped", "docs/SO2-OPTIONS-MENU-INVESTIGATION.md"),
    (0x1880, 0x1881, "Byte that changes on real area-entry transitions; role unexplained", "partial", "docs/SO2-MAP-LOCATION-CHECK.md"),
    (0x19B4, 0x19B8, "Psynard parking bank A: X", "mapped", "docs/SO2-DISC-AND-PSYNARD-CHECK.md"),
    (0x19B8, 0x19BC, "Psynard parking bank A: Z", "mapped", "docs/SO2-DISC-AND-PSYNARD-CHECK.md"),
    (0x19BC, 0x19C0, "Psynard parking bank B: X", "mapped", "docs/SO2-DISC-AND-PSYNARD-CHECK.md"),
    (0x19C0, 0x19C4, "Psynard parking bank B: Z", "mapped", "docs/SO2-DISC-AND-PSYNARD-CHECK.md"),
    (0x19D4, 0x19D8, "Psynard parking bank A: Y", "mapped", "docs/SO2-DISC-AND-PSYNARD-CHECK.md"),
    (0x19D8, 0x19DC, "Psynard parking bank B: Y", "mapped", "docs/SO2-DISC-AND-PSYNARD-CHECK.md"),
    (0x19E8, 0x19E9, "Global flags region start - located, contents unexplored", "partial", "docs/SAVE-FORMAT.md"),
    (0x1A3F, 0x1A41, "Specialty unlock bitmask (12 tiers, Knowledge/Sensibility/Technique/Combat x3)", "mapped", "docs/SO2-SPECIALTY-INVESTIGATION.md"),
    (0x1A45, 0x1A46, "Byte next to the specialty bitmask that changes on area entry; role unexplained", "partial", "docs/SO2-MAP-LOCATION-CHECK.md"),
    (0x1B58, 0x1B88, "48-byte region proven required for cross-area teleport; internal structure not decoded", "partial", "docs/SO2-MAP-LOCATION-CHECK.md"),

    # ---- chunk 5, 2026-09-27 pass: 494 new bytes, names/clocks/deliveries/object-14/global bitmap ----
    (0x1748, 0x174C, "Route-initialized word combined with success counter by save overlay; visible result not identified", "partial", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x1764, 0x1766, "Resource/sequence selector, -1 sentinel (audio-track interpretation plausible, unresolved)", "partial", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x1766, 0x1768, "Saved scene-view parameter (angle/axis name unresolved)", "partial", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x1770, 0x1860, "12 character-name slots, 20 bytes each", "mapped", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x18C8, 0x1988, "48 saved clock-snapshot words", "mapped", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x198C, 0x1990, "Completion counter (u32)", "mapped", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x1990, 0x1992, "Script-additive counter (u16)", "mapped", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x1992, 0x1994, "Attempt counter for script RNG test (u16)", "mapped", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x1994, 0x1996, "Success counter for script RNG test (u16)", "mapped", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x1998, 0x19AC, "Ten packed pending delivery entries (item ID + quantity)", "mapped", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x19AC, 0x19AE, "Menu return request code", "partial", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x19AE, 0x19B0, "Two signed menu modifiers (exact setting unresolved)", "partial", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x19B0, 0x19B4, "Object-14 saved X", "mapped", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x19C4, 0x19C6, "Psynard parking drawing-order companion (bank A)", "mapped", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x19C6, 0x19C8, "Psynard parking drawing-order companion (bank B)", "mapped", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x19C8, 0x19D0, "Eight saved absolute character IDs (party-slot order)", "mapped", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x19D0, 0x19D1, "Menu-selected delivery variant byte", "partial", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x19D2, 0x19D4, "Object-14 saved orientation parameter", "mapped", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x19DC, 0x19E0, "Deferred delivery clock marker", "mapped", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x19E0, 0x19E4, "Object-14 saved Y", "mapped", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x19E4, 0x19E8, "Object-14 saved Z", "mapped", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x19E9, 0x19EA, "Global flags byte: independent travel/state bits (not a single enum)", "partial", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x19EA, 0x19EB, "Global flags byte: object-14/overlay-state bits", "partial", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x19EB, 0x19F5, "Global flags bitmap: confirmed silent across scene scripts (resident/overlay travel & menu bits)", "partial", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x19F5, 0x1A28, "Global flags bitmap (Range A): prologue, Lacour tournament, Linga herbs, Nede arrival", "partial", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x1A28, 0x1A2E, "Global flags bitmap (Range A): Nede arrival, Four Fields quest, Ten Wise Men raid", "partial", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x1A2E, 0x1A31, "Global flags bitmap: confirmed silent (zero references across disc scripts and resident binary)", "partial", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x1A31, 0x1A33, "Global flags bitmap (Range A): ocean rescue, Eluria ID card, Field of Intelligence card barrier", "partial", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x1A33, 0x1A39, "Global flags bitmap: confirmed silent (zero references across disc scripts and resident binary)", "partial", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x1A39, 0x1A3F, "Global flags bitmap (Range A): Lacour Front Line encampment, hospital triage, Energy Stone weapon", "partial", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x1A41, 0x1A45, "Skill Guild tiers & shop learned bits, Magical Rasp flag (0x2DB), specialty UI state", "mapped", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x1A46, 0x1A47, "Global flags byte tested by two text/UI readers; assignment unresolved", "partial", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x1A47, 0x1A49, "Global flags bitmap (Range B): early event milestone flags", "partial", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x1A49, 0x1A55, "Global flags bitmap: confirmed silent (zero references across disc scripts and resident binary)", "partial", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x1A55, 0x1A56, "Global flags bitmap (Range B): Battle Stadium simulation program", "partial", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x1A56, 0x1A57, "Global flags bitmap: confirmed silent (zero references across disc scripts and resident binary)", "partial", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x1A57, 0x1A65, "Global flags bitmap (Range B): Arlia village tour & Cave of Trials riddles", "partial", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x1A65, 0x1B07, "Global flags bitmap: confirmed silent (zero references across disc scripts and resident binary)", "partial", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x1B07, 0x1B0D, "Global flags bitmap (Range B): late/post-game milestones, Eluria ID card, Fun City, Cave of Trials bosses", "partial", "docs/SO2-CHUNK5-MAPPING.md"),
    (0x1B0D, 0x1B58, "Global flags bitmap: confirmed silent (zero references across disc scripts and resident binary)", "partial", "docs/SO2-CHUNK5-MAPPING.md"),
]


def build_map():
    lab = [("unmapped", "unknown", "")] * TOTAL
    for a, b, name, tier, note in RANGES:
        for i in range(a, min(b, TOTAL)):
            lab[i] = (name, tier, note)
    return lab


def runs(lab):
    out, a = [], 0
    for i in range(1, len(lab) + 1):
        if i == len(lab) or lab[i] != lab[a]:
            out.append((a, i, lab[a]))
            a = i
    return out


REGIONS = [
    ("Chunk 1 (options/misc)", 0x000, 0x1A0),
    ("Party primary array (8 slots)", 0x1A0, 0x4A0),
    ("Party secondary array (8 slots)", 0x4A0, 0xB20),
    ("Inventory + bookkeeping", 0xB20, 0x1744),
    ("Chunk 5 (map/state/misc)", 0x1748, 0x1B88),
]


def main():
    lab = build_map()
    tot = {}
    for _, _, (name, tier, note) in runs(lab):
        pass
    tier_bytes = {}
    for name, tier, note in lab:
        tier_bytes[tier] = tier_bytes.get(tier, 0) + 1

    print(f"DECODED SAVE-STATE COVERAGE ({TOTAL} bytes total)\n")
    for tier in ("mapped", "partial", "runtime", "unknown"):
        n = tier_bytes.get(tier, 0)
        print(f"  {tier:8s} {n:5d} bytes  ({100*n/TOTAL:5.1f}%)")
    print()

    region_data = []
    print("BY REGION:")
    for label, a, b in REGIONS:
        seg = lab[a:b]
        seg_tot = {}
        for name, tier, note in seg:
            seg_tot[tier] = seg_tot.get(tier, 0) + 1
        n = b - a
        mapped_pct = 100 * seg_tot.get("mapped", 0) / n
        print(f"  {label:34s} {n:5d} bytes | mapped {mapped_pct:5.1f}% | "
              + " ".join(f"{t}={seg_tot.get(t,0)}" for t in ("mapped", "partial", "runtime", "unknown") if seg_tot.get(t)))
        region_data.append({
            "label": label, "start": a, "end": b, "size": n,
            "tiers": {t: seg_tot.get(t, 0) for t in ("mapped", "partial", "runtime", "unknown")},
        })

    out_json = {
        "total_bytes": TOTAL,
        "tier_totals": tier_bytes,
        "regions": region_data,
        "runs": [{"start": a, "end": b, "label": name, "tier": tier, "note": note}
                 for a, b, (name, tier, note) in runs(lab)],
    }
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "so2_coverage.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_json, f, indent=2)
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
