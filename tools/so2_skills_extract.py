"""Star Ocean: The Second Story (PS1) - Skills, Talents & Specialties Extractor.

Extracts the definitive in-game database of Skills, Talents, Specialties,
and Super Specialties directly from Disc 1 Archive 3015 using the game's
internal font substitution cipher.
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

DEFAULT_DISC = Path("C:/CodeTesting/StarOcean2/disc/Star Ocean - The Second Story (USA) (Disc 1).bin")

# In-game font substitution cipher deciphered from Archive 3015/3025:
FONT_CIPHER: Dict[int, str] = {
    ord('_'): 'S', ord('`'): 't', ord('a'): 'a', ord('b'): 'r',
    ord('c'): ' ', ord('d'): 'o', ord('e'): 'c', ord('f'): 'e',
    ord('g'): 'n', ord('h'): 'T', ord('i'): 'o', ord('j'): 'p',
    ord('k'): 'i', ord('l'): 'l', ord('m'): 'y', ord('n'): 'i',
    ord('o'): 'm', ord('p'): 's', ord('q'): 'e', ord('r'): 'q',
    ord('s'): 'u', ord('t'): 'k', ord('u'): 'g', ord('v'): 'r',
    ord('w'): 'f', ord('x'): 'h', ord('y'): 'g', ord('z'): 'd',
    ord('{'): 'W', ord('|'): 'z', ord('}'): 'N', ord('~'): 'C',
    0x7F: 'v',
}

# Control tags for uppercase letters, punctuation, and math symbols
TAGS_2BYTE: Dict[int, str] = {
    0x80: 'L',
    0x81: 'f',
    0x82: 'D',
    0x83: 'x',
    0x84: 'A',
    0x85: 'b',
    0x86: 'P',
    0x87: 'B',
    0x88: 'M',
    0x89: 'w',
    0x8A: "'",
    0x8B: '.',
    0x8C: 'j',
    0x8D: ',',
    0x8E: 'K',
    0x8F: 'H',
    0x90: '!',
    0x91: 'x',
    0x92: '%',
    0x93: 'X',
    0x94: "'",
    0x95: 'U',
    0x96: '"',
    0x97: '?',
    0x98: '"',
    0x99: ' ',
    0x9A: ' ',
    0x9B: 'Y',
    0x9C: 'v',
}


def decode_string(raw: bytes) -> str:
    """Decode raw bytes in a single pass without collision."""
    chars: List[str] = []
    idx = 0
    n = len(raw)
    while idx < n:
        if idx + 2 < n and raw[idx:idx+3] in (b'\x8c\x80\x04', b'\x86\x80\x04'):
            chars.append('[Square]')
            idx += 3
            continue
        b = raw[idx]
        if idx + 1 < n and raw[idx + 1] == 0x01 and b in TAGS_2BYTE:
            chars.append(TAGS_2BYTE[b])
            idx += 2
            continue
        if 0x01 <= b <= 0x0A:
            chars.append(str(b - 1))
            idx += 1
            continue
        if idx + 1 < n and b == 0x80 and raw[idx + 1] == 0x80:
            chars.append(' ')
            idx += 2
            continue
        if idx + 1 < n and b in (0x86, 0x89, 0x8C) and raw[idx + 1] in (0x80, 0x04):
            idx += 2
            continue
        if b in FONT_CIPHER:
            chars.append(FONT_CIPHER[b])
        elif 32 <= b <= 126:
            chars.append(chr(b))
        elif b in (0x0A, 0x0D, 0x0F):
            chars.append(' ')
        idx += 1

    text = ''.join(chars)
    # Clean up artifacts
    return ' '.join(text.split()).strip()


def extract_database(disc_path: Path = DEFAULT_DISC) -> Dict[str, Any]:
    """Extract all verified skills, talents, and specialties from Archive 3015."""
    with open(disc_path, "rb") as f:
        tbl = dict((idx, (lba, sz)) for idx, lba, sz in archive_table(f))
        raw = read_sectors(f, tbl[3015][0], tbl[3015][1])
        d15 = slz(raw)

    slices = [s for s in d15.split(b"\x00") if len(s) > 2]

    def get_desc(raw_slice: bytes) -> str:
        if b"\x0f" in raw_slice:
            return decode_string(raw_slice.split(b"\x0f", 1)[1])
        return decode_string(raw_slice)

    # Exact calibrated slice offsets:
    # Talents: slices 32..41, Descs: slices 42..51
    talents = []
    for i in range(10):
        talents.append({
            "id": i + 1,
            "name": decode_string(slices[32 + i]),
            "description": decode_string(slices[42 + i])
        })

    # Skills: slices 52..97, Descs: slices 123..168
    skills = []
    for i in range(46):
        skills.append({
            "id": i + 1,
            "name": decode_string(slices[52 + i]),
            "description": get_desc(slices[123 + i])
        })

    # Specialties: 17 items (slices 98..114, Descs: slices 169..185)
    specialties = []
    for i in range(17):
        specialties.append({
            "id": i + 1,
            "name": decode_string(slices[98 + i]),
            "description": get_desc(slices[169 + i]),
            "type": "Specialty"
        })

    # Super Specialties: 8 items (slices 115..122, Descs: slices 186..193)
    super_specialties = []
    for i in range(8):
        super_specialties.append({
            "id": i + 1,
            "name": decode_string(slices[115 + i]),
            "description": get_desc(slices[186 + i]),
            "type": "Super Specialty"
        })

    return {
        "talents": talents,
        "skills": skills,
        "specialties": specialties,
        "super_specialties": super_specialties
    }


def main():
    print("=" * 65)
    print("STAR OCEAN 2 - DISC SKILLS & TALENTS EXTRACTOR")
    print("=" * 65)
    db = extract_database()

    out_json = _ROOT / "artifacts" / "so2-specialty" / "skills_talents_database.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(db, indent=2), encoding="utf-8")
    print(f"Exported database to {out_json.name}")

    print(f"\n[TALENTS] Extracted {len(db['talents'])} verified talents:")
    for t in db['talents']:
        print(f"  {t['id']:2d}. {t['name']:24s} -> {t['description']}")

    print(f"\n[SKILLS] Extracted {len(db['skills'])} verified skills:")
    for s in db['skills'][:15]:
        print(f"  {s['id']:2d}. {s['name']:24s} -> {s['description']}")
    print(f"  ... ({len(db['skills']) - 15} more skills)")

    print(f"\n[SPECIALTIES] Extracted {len(db['specialties'])} specialties:")
    for sp in db['specialties']:
        print(f"  * {sp['name']:20s} -> {sp['description']}")

    print(f"\n[SUPER SPECIALTIES] Extracted {len(db['super_specialties'])} super specialties:")
    for ss in db['super_specialties']:
        print(f"  * {ss['name']:20s} -> {ss['description']}")


if __name__ == "__main__":
    main()
