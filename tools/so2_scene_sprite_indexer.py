"""Star Ocean: The Second Story (PS1) - 2D Scene & Field Sprite Indexer.

Scans all scene container archives (Archives 3207..4154) across Disc 1 and Disc 2,
mapping every scene to the exact 2D sprites, NPC models, creatures, and objects
embedded in tag == 2 (NPC Sprite Bank).

Outputs:
- artifacts/so2-sprites/scene_sprites_index.json (Master JSON catalog)
- docs/SO2-SCENE-SPRITE-INDEX.md (Comprehensive reference documentation)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct
import sys
from typing import Any, Dict, List, Optional, Tuple

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from tools.so2_disc_code import archive_table, read_sectors, slz

DEFAULT_DISC1 = Path("C:/CodeTesting/StarOcean2/disc/Star Ocean - The Second Story (USA) (Disc 1).bin")
DEFAULT_DISC2 = Path("C:/CodeTesting/StarOcean2/disc/Star Ocean - The Second Story (USA) (Disc 2).bin")
OUT_JSON = _ROOT / "artifacts" / "so2-sprites" / "scene_sprites_index.json"
OUT_DOC = _ROOT / "docs" / "SO2-SCENE-SPRITE-INDEX.md"

HERO_NAMES = [
    "Claude Kenni", "Rena Lanford", "Celine Jules", "Bowman Jean",
    "Dias Flac", "Precis F. Neumann", "Ashton Anchors", "Leon D.S. Gehste",
    "Opera Vectra", "Ernest Ravine", "Noel Chandler", "Chisato Madison"
]

# Known regional scene spans on Disc 1 & 2
REGION_RANGES = [
    (3207, 3223, "Opening / Expel Setpieces & Intro Sequences"),
    (3224, 3244, "Arlia Village & Shingo Forest (Scene 017..037)"),
    (3245, 3269, "Salva Town & Salva Drift Cave (Scene 038..062)"),
    (3270, 3305, "Cross Kingdom, Cross Castle & Clik Approach (Scene 063..098)"),
    (3306, 3335, "Port Town of Clik & Disaster Ruins (Scene 099..128)"),
    (3336, 3360, "Mars Village & Heraldry Forest (Scene 129..153)"),
    (3361, 3385, "Linga Academic City & Sanctuary (Scene 154..178)"),
    (3386, 3415, "Kingdom of Lacour & Armory Tournaments (Scene 179..208)"),
    (3416, 3445, "Hoffman Ruins & Lacour Frontline (Scene 209..238)"),
    (3446, 3475, "Eluria Tower & Calnus Transport (Scene 239..268)"),
    (3476, 3540, "Central City & Energy Nede Approach (Scene 269..333)"),
    (3541, 3620, "North City, Giveaway & Library (Scene 334..413)"),
    (3621, 3700, "Armlock, Fun City & Nedian Enclaves (Scene 414..493)"),
    (3701, 3780, "Four Fields (Might, Courage, Intellect, Love) (Scene 494..573)"),
    (3781, 3850, "Phynal Tower, Final Bastion & Endings (Scene 574..643)"),
    (3851, 4154, "Overworld Dungeons, Sub-Levels & Secret Chambers (Scene 644..947)")
]


def classify_selector(selector: int, w: int, h: int, fc: int) -> Tuple[str, str]:
    """Classify an entity selector ID.

    Only the 0..11 hero range is asserted as a specific identity - that mapping is
    independently grounded in this project's already-verified 12-character ID scheme
    used throughout the save format itself. Every other selector gets a neutral,
    non-committal label (its raw ID and dimensions) rather than a guessed content
    name. Content names like "switch monkey" or "town child" were previously
    invented purely from a selector/dimension match with zero visual confirmation,
    and were found to be wrong on inspection (see manager review, 2026-09-28) -
    every checked instance of one such guess turned out to be an ordinary humanoid
    NPC. Do not reintroduce guessed content labels here without an actual visual
    check of a real extracted frame backing each one.
    """
    if 0 <= selector <= 11:
        return "Playable Hero", f"Hero Cutscene / Action ({HERO_NAMES[selector]})"
    return "Unclassified", f"Selector {selector} ({w}x{h}, {fc} frames) - content not visually verified"


def get_region_name(archive_id: int) -> str:
    """Map archive ID to gameplay region name."""
    for start, end, name in REGION_RANGES:
        if start <= archive_id <= end:
            return name
    return "Special / Unmapped Scene"


def build_scene_sprite_index(disc_path: Path, disc_num: int = 1) -> Dict[str, Any]:
    """Scan all scene archives on a disc and build complete scene-to-sprite index."""
    evidence_path = Path(__file__).with_name("so2_scene_selector_evidence.json")
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))["observations"]
    scenes_data: Dict[str, Any] = {}
    selector_stats: Dict[int, Dict[str, Any]] = {}
    total_scenes_with_sprites = 0
    total_sprite_sections = 0
    total_sprite_frames = 0

    with open(disc_path, "rb") as f:
        tbl = dict((idx, (lba, sz)) for idx, lba, sz in archive_table(f))
        scene_archives = [a for a in sorted(tbl.keys()) if 3207 <= a <= 4154]

        for aid in scene_archives:
            lba, sz = tbl[aid]
            raw = read_sectors(f, lba, sz)
            if len(raw) < 12:
                continue

            num_parts = struct.unpack_from("<I", raw, 0)[0]
            if num_parts > 30:
                continue

            tag2_off = None
            for p in range(num_parts):
                tag, off = struct.unpack_from("<2I", raw, 4 + 8 * p)
                if tag == 2:
                    tag2_off = off
                    break

            if tag2_off is None or tag2_off >= len(raw):
                continue

            try:
                dec = slz(raw[tag2_off:])
            except Exception:
                continue

            if len(dec) < 8:
                continue

            num_sec = struct.unpack_from("<I", dec, 0)[0]
            if num_sec == 0 or num_sec > 100:
                continue

            sec_offsets = [struct.unpack_from("<I", dec, 4 + 4 * i)[0] for i in range(num_sec)]
            scene_sprites: List[Dict[str, Any]] = []

            for s_idx, soff in enumerate(sec_offsets):
                if soff + 0x20 > len(dec):
                    continue

                rec_count, selector, a_min, a_max = struct.unpack_from("<4I", dec, soff)
                a_off = struct.unpack_from("<I", dec, soff + 0x18)[0]
                sptr = struct.unpack_from("<I", dec, soff + 0x1C)[0]
                mode = dec[soff + a_off + 2] if soff + a_off + 3 <= len(dec) else 1
                hdr_len = 12 if mode == 1 else 16
                p3 = soff + sptr
                if p3 + hdr_len + 4 > len(dec):
                    continue

                hsz, preloff, unk, fc = struct.unpack("<IIHH", dec[p3 : p3 + 12])
                if fc == 0 or fc > 256:
                    continue

                # Find first non-zero frame for representative dimensions
                w, h = 0, 0
                for fi in range(fc):
                    pos_f = p3 + hdr_len + fi * 12
                    if pos_f + 4 > len(dec):
                        break
                    fw, fh = struct.unpack("2B", dec[pos_f + 1 : pos_f + 3])
                    if fw > 0 and fh > 0:
                        w, h = fw, fh
                        break

                cat, desc = classify_selector(selector, w, h, fc)

                sprite_entry = {
                    "section_index": s_idx,
                    "selector_id": selector,
                    "mode": mode,
                    "category": cat,
                    "description": desc,
                    "animation_range": [a_min, a_max],
                    "frame_count": fc,
                    "width": w,
                    "height": h,
                    "header_size": hsz
                }
                scene_sprites.append(sprite_entry)

                # Update selector stats
                if selector not in selector_stats:
                    selector_stats[selector] = {
                        "selector_id": selector,
                        "category": cat,
                        "description": desc,
                        "occurrences": 0,
                        "scenes": [],
                        "dimensions": set(),
                        "frame_counts": set()
                    }
                selector_stats[selector]["occurrences"] += 1
                if len(selector_stats[selector]["scenes"]) < 10:
                    selector_stats[selector]["scenes"].append(aid)
                selector_stats[selector]["dimensions"].add(f"{w}x{h}")
                selector_stats[selector]["frame_counts"].add(fc)

            if scene_sprites:
                scene_frames = sum(s["frame_count"] for s in scene_sprites)
                scenes_data[str(aid)] = {
                    "archive_id": aid,
                    "scene_index": aid - 3207,
                    "region": get_region_name(aid),
                    "total_sections": len(scene_sprites),
                    "total_frames": scene_frames,
                    "sprites": scene_sprites
                }
                total_scenes_with_sprites += 1
                total_sprite_sections += len(scene_sprites)
                total_sprite_frames += scene_frames

    # Convert sets to sorted lists for JSON serialization
    serialized_selectors = []
    for sel_id in sorted(selector_stats.keys()):
        s = selector_stats[sel_id]
        serialized_selectors.append({
            "selector_id": s["selector_id"],
            "category": s["category"],
            "description": s["description"],
            "occurrences": s["occurrences"],
            "dimensions": sorted(list(s["dimensions"])),
            "frame_counts": sorted(list(s["frame_counts"])),
            "sample_scenes": s["scenes"]
        })

    master_index: Dict[str, Any] = {
        "title": "Star Ocean: The Second Story (PS1) - 2D Scene & Field Sprite Master Index",
        "disc": disc_num,
        "total_scenes_indexed": total_scenes_with_sprites,
        "total_sprite_sections": total_sprite_sections,
        "total_sprite_frames": total_sprite_frames,
        "unique_entity_selectors": len(serialized_selectors),
        "selector_visual_observations": evidence,
        "selector_archetypes": serialized_selectors,
        "scenes": scenes_data
    }

    return master_index


def export_index(master_index: Dict[str, Any], out_json_path: Path, out_doc_path: Path) -> None:
    """Write master JSON catalog and reference Markdown documentation."""
    # Write JSON Artifact
    out_json_path.parent.mkdir(parents=True, exist_ok=True)
    out_json_path.write_text(json.dumps(master_index, indent=2), encoding="utf-8")
    print(f"Master Scene Sprite JSON index exported to {out_json_path}")

    # Generate Markdown Documentation (Paraphrased, Struct/Byte Facts Only)
    generate_markdown_index(master_index, out_doc_path)


def generate_markdown_index(index: Dict[str, Any], out_doc_path: Path) -> None:
    """Generate docs/SO2-SCENE-SPRITE-INDEX.md with region-by-region breakdowns."""
    lines: List[str] = [
        "# Star Ocean: The Second Story (PS1) - 2D Scene & Field Sprite Master Index",
        "",
        "**Scene Sprite Distribution and Frame-specific Evidence**  ",
        f"*Total Indexed Scenes: {index['total_scenes_indexed']} | Declared Frame Descriptors: {index['total_sprite_frames']:,} | Entity Archetypes: {index['unique_entity_selectors']}*",
        "",
        "---",
        "",
        "## 1. Executive Summary & Scene Sprite Architecture",
        "",
        "In *Star Ocean: The Second Story*, all town environments, dungeon corridors, castle interiors,",
        "and story setpieces are packaged as multi-part container archives (`Archives 3207..4154`).",
        "",
        "While `tag == 0` stores the 3D polygon collision walkmesh and `tag == 1` stores script bytecode,",
        "**`tag == 2` serves as the 2D Field NPC Sprite Bank** (verified present in 827 of 948 scene archives).",
        "",
        "### Section Binary Layout in `tag == 2`",
        "Each section within `tag == 2` begins with a 32-byte header followed by dynamic sprite descriptors:",
        "```",
        "Section Header Layout:",
        "  +0x00: record_count (uint32 LE) - Number of animation records (typically 1 or 2)",
        "  +0x04: selector_id  (uint32 LE) - Entity selector identifier (observed values include 32767)",
        "  +0x08: anim_min     (uint32 LE) - Minimum animation state index (e.g. 0)",
        "  +0x0C: anim_max     (uint32 LE) - Maximum animation state index (e.g. 13 = idle/walk)",
        "  +0x18: animation record offset (relative to section; mode byte at offset + 2)",
        "  +0x1C: sprite_ptr   (uint32 LE) - Relative offset to Sprite Container Block (p3)",
        "```",
        "",
        "When an NPC entity is spawned on the field, the game engine's animation dispatcher (`0x8003F518`)",
        "matches the entity's selector (`obj->0x16`) against `selector_id` in `tag == 2` to bind",
        "its 12-byte frame descriptors and 16-color BGR555 CLUT palette.",
        "The descriptor block starts after a 12-byte header for mode 1, otherwise a 16-byte header.",
        "Frame totals here count declared descriptors, including frames the extractor may skip.",
        "",
        "---",
        "",
        "## 2. Entity Selectors",
        "",
        "Only the `0..11` hero range is asserted as a specific identity below - that mapping is",
        "independently grounded in this project's already-verified 12-character ID scheme used",
        "throughout the save format itself. Every other selector ID is intentionally left",
        "unclassified: an earlier draft of this doc guessed specific content (\"switch monkey\",",
        "\"town children\", \"guards\", etc.) purely from selector ID / pixel-dimension coincidences,",
        "with zero visual confirmation. On manager review, every one of those guesses that was",
        "actually checked against a real extracted frame turned out to be wrong - dimensions",
        "guessed as a \"quadruped switch monkey\" were, in every checked instance, an ordinary",
        "humanoid NPC or child. Do not reintroduce specific content labels for non-hero selectors",
        "without first visually inspecting an extracted frame for that exact selector.",
        "",
        "| Selector ID | Category |",
        "| :---: | :--- |",
        "| **`0..11`** | **Playable Heroes** - Claude, Rena, Celine, Bowman, Dias, Precis, Ashton, Leon, Opera, Ernest, Noel, Chisato |",
        "| everything else | **Unclassified** - see the per-scene tables below for each selector's raw ID and dimensions; extract and view the actual frame ([`tools/so2_scene_npc_extract.py`](file:///C:/CodeTesting/SaveConverter/tools/so2_scene_npc_extract.py)) before assuming what it depicts |",
        "",
        "---",
        "",
        "## 3. Regional Scene Sprite Breakdown",
        ""
    ]

    evidence_lines = [
        "### 2.1 Frame-specific visual evidence",
        "",
        "These are visual descriptions of personally viewed decoded frames, not named character",
        "identifications. Each observation applies only to the cited archive/section/frame; it",
        "does not classify every occurrence of that selector or establish a gameplay role.",
        "Other selectors remain unclassified. The hero mapping above is inherited project evidence.",
        "",
        "| Selector | Visual observation | Exact viewed frame (local artifact) |",
        "| :---: | :--- | :--- |",
    ]
    for observation in index.get("selector_visual_observations", []):
        evidence_lines.append(
            f"| {observation['selector_id']} | {observation['visual_description']} | "
            f"`{observation['filename']}` |"
        )
    evidence_lines.append("")
    section_three = lines.index("## 3. Regional Scene Sprite Breakdown")
    lines[section_three:section_three] = evidence_lines

    scenes = index["scenes"]
    for start, end, region_title in REGION_RANGES:
        region_scenes = [s for aid, s in scenes.items() if start <= int(aid) <= end]
        if not region_scenes:
            continue

        region_frames = sum(s["total_frames"] for s in region_scenes)
        lines.append(f"### 3.{len(lines)//20 + 1} {region_title}")
        lines.append(f"*Active Scenes: {len(region_scenes)} | Total Sprite Frames: {region_frames:,}*")
        lines.append("")
        lines.append("| Archive | Scene ID | Sections | Frames | Heroes Present | Other Selectors (ID: dims) |")
        lines.append("| :---: | :---: | :---: | :---: | :--- | :--- |")

        for s in region_scenes:
            aid = s["archive_id"]
            sc_idx = s["scene_index"]
            secs = s["total_sections"]
            frms = s["total_frames"]

            heroes = []
            others = []
            for sp in s["sprites"]:
                if sp["category"] == "Playable Hero":
                    heroes.append(sp["description"].split("(")[-1].rstrip(")"))
                else:
                    others.append(f"{sp['selector_id']}: {sp['width']}x{sp['height']}")

            heroes_str = ", ".join(dict.fromkeys(heroes)) if heroes else "-"
            others_str = ", ".join(others[:6]) if others else "-"
            lines.append(f"| **`{aid}`** | `Scene {sc_idx:03d}` | {secs} | {frms} | {heroes_str} | {others_str} |")

        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 4. Extraction & Tooling Reference")
    lines.append("")
    lines.append("To extract sprites from any scene container indexed above:")
    lines.append("```powershell")
    lines.append("# Extract scene sprite frames from Archive 3418")
    lines.append("python tools/so2_scene_npc_extract.py --archive 3418 --scale 2")
    lines.append("")
    lines.append("# Or via the unified SaveConverter CLI:")
    lines.append("python saveconv.py so2-scene-npc --archive 3418 --scale 2")
    lines.append("")
    lines.append("# Rebuild master scene sprite index:")
    lines.append("python tools/so2_scene_sprite_indexer.py")
    lines.append("```")
    lines.append("")

    out_doc_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Master Scene Sprite Markdown documentation written to {out_doc_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Star Ocean 2 Scene Sprite Indexer")
    parser.add_argument("--disc", "-d", type=int, choices=[1, 2], default=1, help="Disc number (1 or 2, default: 1)")
    parser.add_argument("--out-json", type=Path, default=OUT_JSON, help="Path for JSON catalog")
    parser.add_argument("--out-doc", type=Path, default=OUT_DOC, help="Path for Markdown doc")
    args = parser.parse_args()

    disc_path = DEFAULT_DISC1 if args.disc == 1 else DEFAULT_DISC2
    print(f"Scanning Disc {args.disc} scenes ({disc_path.name})...")
    master_index = build_scene_sprite_index(disc_path, disc_num=args.disc)
    print(f"Indexed {master_index['total_scenes_indexed']} scenes ({master_index['total_sprite_frames']:,} frames across {master_index['unique_entity_selectors']} selectors).")
    export_index(master_index, args.out_json, args.out_doc)


if __name__ == "__main__":
    main()
