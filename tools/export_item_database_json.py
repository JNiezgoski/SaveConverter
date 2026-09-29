"""Star Ocean 2 (PS1) - Item Database JSON Exporter.

Extracts all 823 item records from Disc 1 Archive Entry 2 (48 bytes per record),
cross-references with item names, and exports complete structured data to
artifacts/so2-items/items_database.json.
"""
from __future__ import annotations

import json
from pathlib import Path
import struct
import sys
from typing import Any, Dict, List

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from tools.so2_disc_code import archive_table, read_sectors, slz

DISC_PATH = Path("C:/CodeTesting/StarOcean2/disc/Star Ocean - The Second Story (USA) (Disc 1).bin")
ITEM_IDS_PATH = Path("C:/CodeTesting/StarOcean2/item_ids.txt")
OUT_JSON_PATH = _ROOT / "artifacts" / "so2-items" / "items_database.json"

CHAR_NAMES = [
    "Claude", "Rena", "Celine", "Bowman", "Dias", "Precis",
    "Ashton", "Leon", "Opera", "Ernest", "Noel", "Chisato"
]

CATEGORY_NAMES = {
    0: "Consumable / Material / Food",
    1: "Weapon",
    8: "Body Armor",
    9: "Shield",
    10: "Helmet",
    11: "Boots / Greaves",
    12: "Accessory / Mineral"
}

USE_TYPE_NAMES = {
    0: "Passive / Material / Key Item",
    1: "Battle Only",
    2: "Camp / Menu Only",
    3: "Field & Battle Usable"
}

ELEMENT_NAMES = [
    "Earth", "Water", "Fire", "Wind", "Thunder",
    "Star", "Void", "Light", "Dark", "Physical"
]

RESIST_LEVELS = {
    0: "Neutral (100%)",
    1: "Weak (150%)",
    2: "Resist (50%)",
    3: "Immune (0%)",
    4: "Absorb (-100%)"
}


def load_names() -> Dict[int, str]:
    names = {}
    with open(ITEM_IDS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            code_str, name = line[:4], line[5:]
            iid = int(code_str, 16) - 0x5000
            names[iid] = name
    return names


def load_master_table(disc_path: Path = DISC_PATH) -> bytes:
    with open(disc_path, "rb") as f:
        entries = {eid: (lba, size) for eid, lba, size in archive_table(f)}
        lba, size = entries[2]
        raw = read_sectors(f, lba, size)
        decomp = slz(raw)
    return decomp


def export_database() -> Dict[str, Any]:
    names = load_names()
    master = load_master_table()
    total_capacity = len(master) // 48

    OUT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)

    items: List[Dict[str, Any]] = []

    for iid in range(1, 824):
        rec = master[(iid - 1) * 48 : iid * 48]
        mask = struct.unpack_from("<H", rec, 4)[0]
        cat = rec[0x2A]
        use_type = rec[0x29]

        equippable_by = [CHAR_NAMES[i] for i in range(12) if (mask & (1 << i))]
        if mask == 0x0FFF:
            equip_desc = "All Characters"
        elif mask == 0:
            equip_desc = "None"
        else:
            equip_desc = "/".join(equippable_by)

        elem_bytes = list(rec[0x1C:0x26])
        elemental_resistances = {
            ELEMENT_NAMES[i]: RESIST_LEVELS.get(elem_bytes[i], f"Unknown ({elem_bytes[i]})")
            for i in range(10)
        }

        item_dict = {
            "id": iid,
            "hex_id": f"0x{iid:03X}",
            "codebreaker_code": f"{0x5000 + iid:04X}",
            "name": names.get(iid, f"Item_{iid:03X}"),
            "category_id": cat,
            "category": CATEGORY_NAMES.get(cat, f"Unknown (0x{cat:02X})"),
            "usage_type_id": use_type,
            "usage_context": USE_TYPE_NAMES.get(use_type, f"Unknown ({use_type})"),
            "buy_price": struct.unpack_from("<I", rec, 0)[0],
            "sell_rate_percent": rec[0x2D],
            "equip_mask": mask,
            "equip_mask_hex": f"0x{mask:04X}",
            "equippable_by": equippable_by,
            "equip_description": equip_desc,
            "stats": {
                "atk": struct.unpack_from("<h", rec, 8)[0],
                "def": struct.unpack_from("<h", rec, 0x10)[0],
                "hit_crt": struct.unpack_from("<h", rec, 0x0C)[0],
                "avd": struct.unpack_from("<h", rec, 0x0E)[0],
                "mag_luc": struct.unpack_from("<h", rec, 0x12)[0],
                "str_agl": struct.unpack_from("<h", rec, 0x14)[0],
                "guts_stm": struct.unpack_from("<h", rec, 0x16)[0],
                "secondary": struct.unpack_from("<h", rec, 6)[0],
            },
            "recovery_value": rec[0x19],
            "proc_trigger_rate": rec[0x1A],
            "weapon_element_trail": rec[0x1B],
            "elemental_resistances": elemental_resistances,
            "status_ailment_mask": f"0x{struct.unpack_from('<H', rec, 0x26)[0]:04X}",
            "sub_type_id": rec[0x28],
            "resale_tier": rec[0x2B],
            "proc_id": rec[0x2C],
        }
        items.append(item_dict)

    database = {
        "title": "Star Ocean: The Second Story (PS1) Master Item Database",
        "disc": 1,
        "archive_entry": 2,
        "record_size_bytes": 48,
        "total_active_items": len(items),
        "total_slots_capacity": total_capacity,
        "categories": {cat_id: name for cat_id, name in CATEGORY_NAMES.items()},
        "items": items
    }

    OUT_JSON_PATH.write_text(json.dumps(database, indent=2), encoding="utf-8")
    print(f"Exported {len(items)} items to {OUT_JSON_PATH}")
    return database


if __name__ == "__main__":
    export_database()
