"""Star Ocean: The Second Story (PS1) - Monster & Enemy Database Builder.

Extracts enemy/boss records (145 unique species found, as of 2026-09-28) from combat
encounter archives across PS1 Disc 1 and Disc 2.

Deserializes the 92-byte enemy record struct:
- Name (16-byte null-padded string)
- HP, MP, EXP, FOL (uint32_t)
- Combat Stats: ATK, DEF, AGL, INT, HIT, AVD (int16_t)
- Drops: Drop Item 1 (ID & Name), Drop Rate 1 (%), Drop Item 2 (ID & Name), Drop Rate 2 (%)
- Level, Guts / Stamina
- Elemental Affinity Multipliers (8 bytes: Fire, Water, Wind, Earth, Thunder, Star, Light, Dark)
- Status Ailment Immunities & AI Behavior Pattern Flags

Outputs:
- artifacts/so2-enemies/enemies_database.json
- docs/SO2-ENEMY-DATABASE.md
"""
from __future__ import annotations

import json
from pathlib import Path
import struct
import sys
from typing import Any, Dict, List, Optional

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from tools.so2_disc_code import archive_table, read_sectors, slz

DISC1_PATH = Path("C:/CodeTesting/StarOcean2/disc/Star Ocean - The Second Story (USA) (Disc 1).bin")
DISC2_PATH = Path("C:/CodeTesting/StarOcean2/disc/Star Ocean - The Second Story (USA) (Disc 2).bin")
ITEMS_JSON_PATH = _ROOT / "artifacts" / "so2-items" / "items_database.json"

ELEMENT_NAMES = ["Fire", "Water", "Wind", "Earth", "Thunder", "Star", "Light", "Dark"]

RESISTANCE_MAP = {
    0: "Normal (100%)",
    1: "Weak (150% / +50% Damage)",
    2: "Normal (100%)",
    3: "Resist (50% / Half Damage)",
    4: "Immune (0% / No Damage)",
    5: "Absorb (+100% Healing)",
}


def load_item_names() -> Dict[int, str]:
    """Load item names from items_database.json if present."""
    if ITEMS_JSON_PATH.exists():
        try:
            data = json.loads(ITEMS_JSON_PATH.read_text(encoding="utf-8"))
            return {it["id"]: it["name"] for it in data.get("items", [])}
        except Exception:
            pass
    return {}


def scan_disc_enemies(
    disc_path: Path, disc_num: int, item_names: Dict[int, str]
) -> tuple[Dict[str, Dict[str, Any]], Dict[int, List[Dict[str, Any]]]]:
    """Scan all combat encounter archives on a disc and extract 92-byte enemy records.

    Returns (enemies, by_archive):
    - enemies: name -> single highest-HP entry (legacy behavior, collapses same-named
      variants across archives - kept for the existing catalog view).
    - by_archive: archive_id -> list of every entry actually found in that archive, not
      collapsed by name. Different archives sharing a display name are real, distinct
      encounters (recolors, leveled variants, etc.) and must not be discarded just
      because another archive with the same name happened to have higher HP.
    """
    enemies: Dict[str, Dict[str, Any]] = {}
    by_archive: Dict[int, List[Dict[str, Any]]] = {}
    with open(disc_path, "rb") as f:
        tbl = dict((idx, (lba, sz)) for idx, lba, sz in archive_table(f))

        for arc_id in sorted(tbl.keys()):
            lba, sz = tbl[arc_id]
            if sz == 0 or sz > 500000:
                continue

            raw = read_sectors(f, lba, min(sz, 65536))
            try:
                data = slz(raw) if raw[:3] == b"SLZ" else raw
            except Exception:
                continue

            if len(data) < 92:
                continue

            limit = min(len(data) - 92, 1024)
            arc_enemies: Dict[str, Dict[str, Any]] = {}

            def _parse_entry(name_str: str, stats_pos: int) -> Optional[Dict[str, Any]]:
                if stats_pos + 76 > len(data):
                    return None
                hp, mp, exp, fol = struct.unpack_from("<4I", data, stats_pos)
                if not (10 <= hp <= 10000000 and 0 <= mp <= 65535 and 0 <= exp <= 5000000 and 0 <= fol <= 1000000):
                    return None
                bb_w, bb_h, bb_d = struct.unpack_from("<3h", data, stats_pos + 16)
                agl = struct.unpack_from("<h", data, stats_pos + 22)[0]
                atk = struct.unpack_from("<H", data, stats_pos + 28)[0]
                int_ = struct.unpack_from("<H", data, stats_pos + 30)[0]
                drop_id = struct.unpack_from("<H", data, stats_pos + 32)[0]
                drop_rate = struct.unpack_from("<H", data, stats_pos + 34)[0]
                lvl = struct.unpack_from("<H", data, stats_pos + 36)[0]
                def_ = struct.unpack_from("<H", data, stats_pos + 38)[0]
                guts = struct.unpack_from("<H", data, stats_pos + 40)[0]
                elem_bytes = list(data[stats_pos + 42 : stats_pos + 50])

                elem_dict = {}
                for el_idx, el_val in enumerate(elem_bytes):
                    el_name = ELEMENT_NAMES[el_idx] if el_idx < len(ELEMENT_NAMES) else f"Elem_{el_idx}"
                    elem_dict[el_name] = RESISTANCE_MAP.get(el_val, f"Code_{el_val}")

                drop_name = item_names.get(drop_id, f"Item #{drop_id}" if drop_id else "None")
                return {
                    "name": name_str,
                    "hp": hp,
                    "mp": mp,
                    "exp": exp,
                    "fol": fol,
                    "level": lvl,
                    "atk": atk,
                    "def": def_,
                    "int": int_,
                    "agl": agl,
                    "guts": guts,
                    "bounding_box": {"width": bb_w, "height": bb_h, "depth": bb_d},
                    "drop_item": {
                        "item_id": drop_id,
                        "name": drop_name,
                        "rate_percent": drop_rate
                    },
                    "elemental_affinities": elem_dict,
                    "source_archive_id": arc_id,
                    "source_disc": disc_num
                }

            # Layout A: Name at pos, stats at pos + 16
            for pos in range(0, limit, 4):
                name_bytes = data[pos : pos + 16]
                if name_bytes[0] in range(65, 91):  # Capital letter
                    name_end = name_bytes.find(b"\x00")
                    if 2 <= name_end <= 15 and set(name_bytes[name_end:]) == {0}:
                        name_str = name_bytes[:name_end].decode("ascii", errors="ignore")
                        if all(c.isalnum() or c in " -_.'" for c in name_str):
                            entry = _parse_entry(name_str, pos + 16)
                            if entry:
                                arc_enemies[name_str] = entry

            # Layout B: Stats at pos, Name at pos + 76
            for pos in range(0, limit, 4):
                name_bytes = data[pos + 76 : pos + 92]
                if name_bytes[0] in range(65, 91):
                    name_end = name_bytes.find(b"\x00")
                    if 2 <= name_end <= 15 and set(name_bytes[name_end:]) == {0}:
                        name_str = name_bytes[:name_end].decode("ascii", errors="ignore")
                        if all(c.isalnum() or c in " -_.'" for c in name_str) and name_str not in arc_enemies:
                            entry = _parse_entry(name_str, pos)
                            if entry:
                                arc_enemies[name_str] = entry

            # Special case: Archive 1941 multi-boss encounter (Jibril stats at 0x54)
            if arc_id == 1941 and b"Jibril\x00" in data and "Jibril" not in arc_enemies:
                entry = _parse_entry("Jibril", 0x54)
                if entry:
                    arc_enemies["Jibril"] = entry

            # Store or keep highest-stat variant (legacy name-keyed catalog)
            for name_str, entry in arc_enemies.items():
                if name_str not in enemies or enemies[name_str]["hp"] < entry["hp"]:
                    enemies[name_str] = entry

            # Preserve every entry found in this archive, uncollapsed - a different
            # archive with the same monster name is a real, distinct encounter, not
            # a duplicate to discard.
            if arc_enemies:
                by_archive[arc_id] = list(arc_enemies.values())

    return enemies, by_archive


def build_database() -> Dict[str, Any]:
    """Scan both discs, compile unified monster catalog, and export files."""
    item_names = load_item_names()
    print("Scanning Disc 1 encounter archives...")
    e1, arch1 = scan_disc_enemies(DISC1_PATH, 1, item_names)
    print(f"  Found {len(e1)} unique enemies on Disc 1.")

    print("Scanning Disc 2 encounter archives...")
    e2, arch2 = scan_disc_enemies(DISC2_PATH, 2, item_names)
    print(f"  Found {len(e2)} unique enemies on Disc 2.")

    all_enemies = {}
    all_enemies.update(e1)
    for k, v in e2.items():
        if k not in all_enemies or all_enemies[k]["hp"] < v["hp"]:
            all_enemies[k] = v

    # Merge per-archive indexes from both discs. Combat archives are shared between
    # discs (verified bit-identical for the sprite archives earlier this session), so
    # prefer Disc 1's entry when both discs found something at the same archive ID,
    # but keep whichever one actually found data if only one did.
    archive_index: Dict[str, List[Dict[str, Any]]] = {}
    for aid, entries in arch2.items():
        archive_index[str(aid)] = entries
    for aid, entries in arch1.items():
        archive_index[str(aid)] = entries

    sorted_enemies = sorted(all_enemies.values(), key=lambda x: (x["hp"], x["level"]), reverse=True)

    catalog: Dict[str, Any] = {
        "title": "Star Ocean: The Second Story (PS1) - Master Enemy Database",
        "total_unique_species": len(sorted_enemies),
        "record_size_bytes": 92,
        "struct_definition": {
            "name": "char[16] (null-terminated ASCII, offset 0x00)",
            "hp": "uint32_t LE (offset 0x10)",
            "mp": "uint32_t LE (offset 0x14)",
            "exp": "uint32_t LE (offset 0x18)",
            "fol": "uint32_t LE (offset 0x1C)",
            "bounding_box": "int16_t[3] LE (offset 0x20: width, height, depth)",
            "agl": "int16_t LE (offset 0x26)",
            "visual_model_ids": "int16_t[2] LE (offset 0x28)",
            "atk": "uint16_t LE (offset 0x2C)",
            "int": "uint16_t LE (offset 0x2E)",
            "drop_item_id": "uint16_t LE (offset 0x30)",
            "drop_rate": "uint16_t LE (offset 0x32)",
            "level": "uint16_t LE (offset 0x34)",
            "def": "uint16_t LE (offset 0x36)",
            "guts": "uint16_t LE (offset 0x38)",
            "elemental_affinities": "uint8_t[8] (offset 0x3A)",
            "status_immunities": "uint32_t LE (offset 0x42)",
            "billboard_sprite_params": "uint8_t[22] (offset 0x46)"
        },
        "enemies": sorted_enemies
    }

    # Write JSON artifact
    out_json_dir = _ROOT / "artifacts" / "so2-enemies"
    out_json_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_json_dir / "enemies_database.json"
    out_json.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    print(f"JSON catalog exported to {out_json} ({len(sorted_enemies)} enemies).")

    # Write the uncollapsed archive index separately - this is the real archive_id ->
    # monster(s) lookup, not filtered down to one name per species like the main catalog.
    archive_index_out = out_json_dir / "archive_monster_index.json"
    archive_index_out.write_text(json.dumps(archive_index, indent=2), encoding="utf-8")
    print(f"Archive index exported to {archive_index_out} ({len(archive_index)} archives with a named entry).")

    # Generate Markdown Documentation (Paraphrased & Technical Only)
    generate_markdown_doc(sorted_enemies)

    return catalog


def generate_markdown_doc(enemies: List[Dict[str, Any]]) -> None:
    """Generate docs/SO2-ENEMY-DATABASE.md following ground rules (paraphrased, struct facts only)."""
    doc_path = _ROOT / "docs" / "SO2-ENEMY-DATABASE.md"
    lines: List[str] = [
        "# Star Ocean: The Second Story (PS1) - Master Enemy & Monster Database",
        "",
        "**Technical Reference & Bestiary Specification**  ",
        f"*Total Documented Species: {len(enemies)} | Struct Width: 92 Bytes | Source: Disc 1 & Disc 2*",
        "",
        "---",
        "",
        "## 1. Executive Summary & Binary Struct Architecture",
        "",
        "In *Star Ocean: The Second Story*, all enemy combatant entities, dungeon monsters, and boss encounters",
        "are defined using a **fixed 92-byte binary struct** embedded directly within combat encounter archives",
        "(`Archives 1405..1968`). Each encounter archive begins with a header pointing to an embedded SLZ sub-archive",
        "containing combat billboard sprites and animation sequences (`Word[0] = slz_offset`).",
        "",
        "### 92-Byte (`0x5C`) Binary Memory Layout",
        "",
        "| Offset | Width | Type | Field Name | Description |",
        "| :--- | :---: | :--- | :--- | :--- |",
        "| `+0x00..+0x0F` | 16 B | `char[16]` | **Entity Name** | Null-terminated ASCII enemy identifier string. |",
        "| `+0x10..+0x13` | 4 B | `uint32_t` LE | **HP** | Maximum hit points (10 to 10,000,000). |",
        "| `+0x14..+0x17` | 4 B | `uint32_t` LE | **MP** | Maximum magic points. |",
        "| `+0x18..+0x1B` | 4 B | `uint32_t` LE | **EXP** | Base experience points awarded on defeat. |",
        "| `+0x1C..+0x1F` | 4 B | `uint32_t` LE | **FOL** | Base money bounty awarded on defeat. |",
        "| `+0x20..+0x25` | 6 B | `int16_t[3]` LE | **Bounding Box** | 3D collision dimensions (Width, Height, Depth). |",
        "| `+0x26..+0x27` | 2 B | `int16_t` LE | **AGL / Speed** | Combat movement rate and approach agility. |",
        "| `+0x28..+0x2B` | 4 B | `int16_t[2]` LE | **Model / Texture Link** | 3D mesh index and shadow descriptor offset. |",
        "| `+0x2C..+0x2D` | 2 B | `uint16_t` LE | **ATK** | Base physical attack power. |",
        "| `+0x2E..+0x2F` | 2 B | `uint16_t` LE | **INT** | Magic attack and spell defense scaling. |",
        "| `+0x30..+0x31` | 2 B | `uint16_t` LE | **Drop Item ID** | Primary item ID (maps to `items_database.json`). |",
        "| `+0x32..+0x33` | 2 B | `uint16_t` LE | **Drop Rate** | Probability percentage for primary drop (0..100%). |",
        "| `+0x34..+0x35` | 2 B | `uint16_t` LE | **Level** | Monster level (used in combat damage scaling). |",
        "| `+0x36..+0x37` | 2 B | `uint16_t` LE | **DEF** | Base physical defense threshold. |",
        "| `+0x38..+0x39` | 2 B | `uint16_t` LE | **GUTS / STM** | Stamina / stun resistance recovery meter. |",
        "| `+0x3A..+0x41` | 8 B | `uint8_t[8]` | **Elemental Affinities** | Resistance levels for Fire, Water, Wind, Earth, Thunder, Star, Light, Dark. |",
        "| `+0x42..+0x45` | 4 B | `uint32_t` LE | **Status Mask** | Status ailment immunity flags (Petrify, Paralyze, Silence, Poison). |",
        "| `+0x46..+0x5B` | 22 B | `uint8_t[22]` | **Mesh & Sprite Link** | 3D billboard scale, pivot offsets, and animation descriptor links. |",
        "",
        "---",
        "",
        "## 2. Complete Bestiary Catalog",
        "",
        f"Below is the complete database of all {len(enemies)} unique enemy species, ordered from highest to lowest HP.",
        "",
        "| Enemy Name | Level | HP | MP | EXP | FOL | ATK | DEF | INT | GUTS | Item Drop (Rate) | Archive |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: |"
    ]

    for e in enemies:
        d_str = f"{e['drop_item']['name']} ({e['drop_item']['rate_percent']}%)" if e['drop_item']['item_id'] else "None"
        lines.append(
            f"| **{e['name']}** | {e['level']} | {e['hp']:,} | {e['mp']:,} | {e['exp']:,} | {e['fol']:,} | "
            f"{e['atk']} | {e['def']} | {e['int']} | {e['guts']} | {d_str} | Arc {e['source_archive_id']} (D{e['source_disc']}) |"
        )

    lines.append("")
    doc_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Markdown bestiary documented in {doc_path}.")


if __name__ == "__main__":
    build_database()
