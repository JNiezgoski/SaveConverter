"""Star Ocean 2 (PS1) - Monster Archive -> Sprite File Database Builder.

Combines the enemy stat database (artifacts/so2-enemies/archive_monster_index.json)
with the actual extracted sprite files on disk
(artifacts/so2-monster-format/decoded/archive-<id>/block-<b>/bank-<k>/) into one
lookup: archive_id -> monster name(s) + every real sprite file found for it, with
each slice's real dimensions and pivot pulled from the extraction report.

Does not composite pieces (see docs/SO2-COMBAT-GRAPHICS-INVESTIGATION.md - this
format stores separate composable body-part pieces, not one image per pose) - this
just inventories what was actually extracted, honestly, file by file.

Output: artifacts/so2-monster-format/monster_sprite_database.json
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

_ROOT = Path(__file__).resolve().parents[1]
DECODED_DIR = _ROOT / "artifacts" / "so2-monster-format" / "decoded"
REPORT_PATH = DECODED_DIR / "report.json"
MONSTER_INDEX_PATH = _ROOT / "artifacts" / "so2-enemies" / "archive_monster_index.json"
OUT_PATH = _ROOT / "artifacts" / "so2-monster-format" / "monster_sprite_database.json"


def load_report_by_archive() -> Dict[int, Dict[str, Any]]:
    raw = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    entries = raw if isinstance(raw, list) else raw.get("archives", raw)
    by_archive: Dict[int, Dict[str, Any]] = {}
    for e in entries:
        aid = e.get("entry")
        if aid is not None:
            by_archive[aid] = e
    return by_archive


def build() -> None:
    monster_names = json.loads(MONSTER_INDEX_PATH.read_text(encoding="utf-8"))
    report_by_archive = load_report_by_archive()

    database: Dict[str, Any] = {
        "title": "Star Ocean 2 (PS1) - Monster Archive to Sprite File Database",
        "note": (
            "Each archive's slices are separate composable pieces (body, head, "
            "accent details), not one complete image per pose - see "
            "docs/SO2-COMBAT-GRAPHICS-INVESTIGATION.md. This inventories every real "
            "extracted file honestly; it does not composite pieces together."
        ),
        "archives": {}
    }

    archive_dirs = sorted(
        (p for p in DECODED_DIR.iterdir() if p.is_dir() and p.name.startswith("archive-")),
        key=lambda p: int(p.name.split("-")[1])
    )

    total_slices = 0
    for adir in archive_dirs:
        aid = int(adir.name.split("-")[1])
        report_entry = report_by_archive.get(aid)
        monsters = monster_names.get(str(aid), [])

        blocks_out: List[Dict[str, Any]] = []
        for bdir in sorted(p for p in adir.iterdir() if p.is_dir() and p.name.startswith("block-")):
            b_idx = int(bdir.name.split("-")[1])
            banks_out: List[Dict[str, Any]] = []
            for kdir in sorted(p for p in bdir.iterdir() if p.is_dir() and p.name.startswith("bank-")):
                k_idx = int(kdir.name.split("-")[1])

                # Pull real per-slice geometry from the report if available
                slice_geo = {}
                if report_entry:
                    for block in report_entry.get("blocks", []):
                        for bank in block.get("banks", []):
                            if bank.get("index") == k_idx:
                                for s in bank.get("slices", []):
                                    if s.get("status") == "decoded":
                                        u0, v0, u1, v1 = s["uv"]
                                        slice_geo[s["index"]] = {
                                            "width": u1 - u0,
                                            "height": v1 - v0,
                                            "pivot": s["pivot"],
                                            "palette_row": s["palette_row"],
                                        }

                slice_files = sorted(kdir.glob("slice-*.png"))
                slices_out = []
                for sf in slice_files:
                    idx = int(sf.stem.split("-")[1])
                    entry = {"index": idx, "file": str(sf.relative_to(_ROOT)).replace("\\", "/")}
                    if idx in slice_geo:
                        entry.update(slice_geo[idx])
                    slices_out.append(entry)
                    total_slices += 1

                contact = kdir / "contact.png"
                banks_out.append({
                    "bank_index": k_idx,
                    "contact_sheet": str(contact.relative_to(_ROOT)).replace("\\", "/") if contact.exists() else None,
                    "slice_count": len(slices_out),
                    "slices": slices_out,
                })
            blocks_out.append({"block_index": b_idx, "banks": banks_out})

        database["archives"][str(aid)] = {
            "archive_id": aid,
            "monsters": monsters,
            "blocks": blocks_out,
        }

    database["total_archives"] = len(archive_dirs)
    database["total_archives_with_monster_name"] = sum(1 for a in database["archives"].values() if a["monsters"])
    database["total_slice_files"] = total_slices

    OUT_PATH.write_text(json.dumps(database, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(f"  {database['total_archives']} archives, {database['total_archives_with_monster_name']} named, {total_slices} slice files indexed")


if __name__ == "__main__":
    build()
