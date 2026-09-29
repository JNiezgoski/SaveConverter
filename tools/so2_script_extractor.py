"""Star Ocean: The Second Story (PS1) - Dialogue & Scene Script Extractor.

Extracts dialogue strings and decompiles scene script headers/opcodes from
multi-part town and dungeon archives (Archives 3207..4154) across Disc 1 and Disc 2.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct
import sys
from typing import Any, Dict, List, Tuple

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from tools.so2_disc_code import archive_table, read_sectors, slz

DEFAULT_DISC1 = Path("C:/CodeTesting/StarOcean2/disc/Star Ocean - The Second Story (USA) (Disc 1).bin")
DEFAULT_DISC2 = Path("C:/CodeTesting/StarOcean2/disc/Star Ocean - The Second Story (USA) (Disc 2).bin")
OUT_BASE = _ROOT / "artifacts" / "so2-scripts"


def decode_so2_dialogue(raw_bytes: bytes) -> str:
    """Decode 16-bit tri-Ace dialogue script text encoding."""
    chars: List[str] = []
    i = 0
    n = len(raw_bytes)
    while i < n - 1:
        code = struct.unpack_from("<H", raw_bytes, i)[0]
        i += 2
        if code == 0:
            break
        # Standard Latin uppercase
        if 0x01B6 <= code <= 0x01CF:
            chars.append(chr(code - 0x01B6 + ord("A")))
        # Standard Latin lowercase
        elif 0x01D0 <= code <= 0x01E9:
            chars.append(chr(code - 0x01D0 + ord("a")))
        # Digits 0-9
        elif 0x01AA <= code <= 0x01B3:
            chars.append(chr(code - 0x01AA + ord("0")))
        # Alternate glyph set uppercase
        elif 0x02B6 <= code <= 0x02CF:
            chars.append(chr(code - 0x02B6 + ord("A")))
        # Alternate glyph set lowercase
        elif 0x02D0 <= code <= 0x02E9:
            chars.append(chr(code - 0x02D0 + ord("a")))
        # Punctuation & whitespace
        elif code in (0x0185, 0x0285, 0x0113, 0x0200):
            chars.append(" ")
        elif code in (0x0183, 0x0283):
            chars.append(".")
        elif code in (0x0184, 0x0284):
            chars.append(",")
        elif code in (0x0186, 0x0286):
            chars.append("'")
        elif code in (0x0187, 0x0287):
            chars.append("?")
        elif code in (0x0188, 0x0288):
            chars.append("!")
        elif code == 0x01B5:
            chars.append("-")
        elif code in (0x0189, 0x018A, 0x0289, 0x028A):
            chars.append('"')
        elif code in (0x018B, 0x028B):
            chars.append(":")
        elif code in (0x018C, 0x028C):
            chars.append(";")
        elif (code >> 8) == 0x80 or (code & 0xFF00) == 0:
            # Control formatting code
            continue

    text = "".join(chars)
    return " ".join(text.split()).strip()


def extract_scene_script(disc_path: Path, archive_id: int) -> Tuple[bytes | None, List[str]]:
    """Extract and parse script bytecode payload and message strings."""
    with open(disc_path, "rb") as f:
        tbl = dict((idx, (lba, sz)) for idx, lba, sz in archive_table(f))
        if archive_id not in tbl:
            return None, []
        lba, sz = tbl[archive_id]
        raw = read_sectors(f, lba, sz)

    if len(raw) < 12:
        return None, []
    num_parts = struct.unpack_from("<I", raw)[0]
    if not (2 <= num_parts <= 15):
        return None, []

    script_data = None
    for p in range(num_parts):
        tag, offset = struct.unpack_from("<II", raw, 4 + 8 * p)
        if tag == 1 and offset < len(raw):
            try:
                script_data = slz(raw[offset:])
                break
            except Exception:
                pass

    if not script_data or len(script_data) < 0x20:
        return None, []

    word0 = struct.unpack_from("<I", script_data, 0)[0]
    num_msgs = struct.unpack_from("<I", script_data, 0x0C)[0]
    if num_msgs == 0 or num_msgs > 1000 or word0 + 0x1C + num_msgs * 2 > len(script_data):
        return script_data, []

    msg_table = word0 + 0x1C
    text_base = msg_table + num_msgs * 2
    msgs: List[str] = []
    for m in range(num_msgs):
        off = struct.unpack_from("<H", script_data, msg_table + m * 2)[0]
        if text_base + off < len(script_data):
            raw_text = script_data[text_base + off : text_base + off + 800]
            txt = decode_so2_dialogue(raw_text)
            if txt and not txt.startswith("MONEY") and "999999999FOL" not in txt and len(txt) > 3:
                msgs.append(txt)

    return script_data, msgs


def scan_all_scenes(disc_path: Path, disc_num: int = 1) -> Dict[str, Any]:
    """Extract all scene dialogue from candidate archives."""
    OUT_BASE.mkdir(parents=True, exist_ok=True)
    catalog: Dict[str, Any] = {
        "disc": disc_num,
        "total_archives": 0,
        "scenes": {}
    }

    with open(disc_path, "rb") as f:
        tbl = dict((idx, (lba, sz)) for idx, lba, sz in archive_table(f))

    print(f"Scanning Disc {disc_num} scene archives (3207..4154)...")
    for arch in sorted(tbl.keys()):
        if not (3207 <= arch <= 4154):
            continue
        try:
            script_data, msgs = extract_scene_script(disc_path, arch)
            if script_data and msgs:
                word0 = struct.unpack_from("<I", script_data, 0)[0]
                catalog["scenes"][str(arch)] = {
                    "archive_id": arch,
                    "scene_index": arch - 3207,
                    "bytecode_size": word0,
                    "total_script_size": len(script_data),
                    "message_count": len(msgs),
                    "first_message": msgs[0][:120],
                    "sample_messages": msgs[:5]
                }
                print(f"  [+] Arc {arch} (Scene {arch - 3207:03d}): {len(msgs):2d} msgs | \"{msgs[0][:60]}\"")
        except Exception:
            continue

    catalog["total_archives"] = len(catalog["scenes"])
    out_file = OUT_BASE / f"disc{disc_num}_scenes_catalog.json"
    out_file.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    print(f"\nExtracted {len(catalog['scenes'])} scenes with dialogue to {out_file.name}")
    return catalog


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract SO2 PS1 dialogue scripts.")
    parser.add_argument("--disc", type=int, default=1, choices=[1, 2], help="Disc number (1 or 2)")
    parser.add_argument("--archive", type=int, default=None, help="Extract specific archive")
    args = parser.parse_args()

    disc_path = DEFAULT_DISC1 if args.disc == 1 else DEFAULT_DISC2
    if args.archive is not None:
        data, msgs = extract_scene_script(disc_path, args.archive)
        print(f"Archive {args.archive}: Bytecode {len(data) if data else 0} bytes, {len(msgs)} messages:")
        for i, m in enumerate(msgs):
            print(f"  [{i:02d}]: {m}")
    else:
        scan_all_scenes(disc_path, args.disc)


if __name__ == "__main__":
    main()
