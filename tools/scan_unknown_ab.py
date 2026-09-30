"""Scan SO2 memory card save files and report Unknown A/B stat triplets.

Decodes every party primary array across memory card (.mcd) files, reporting:
- Slot index and Character Name (and Character ID)
- Level (+0x26)
- Unknown A triplet (+0x4E, +0x50, +0x52): (Base, Intermediate, Effective)
- Unknown B triplet (+0x54, +0x56, +0x58): (Base, Intermediate, Effective)
- Classification state:
    * Flat (X, X, X): unmodified recruitment baseline
    * Zeroed (X, 0, 0): base set, runtime fields zeroed (unrecruited/benched init)
    * Diverged (+2) (X, X+2, X+2): intermediate and effective incremented by 2
    * Other (X, Y, Z): other runtime/equipment variation

Usage:
    python tools/scan_unknown_ab.py [PATH_OR_DIR]
"""

import argparse
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))

import saveconv
import so2_codec

NAMES = {
    1: 'Claude',
    2: 'Rena',
    3: 'Celine',
    4: 'Bowman',
    5: 'Dias',
    6: 'Precis',
    7: 'Ashton',
    8: 'Leon',
    9: 'Opera',
    10: 'Ernest',
    11: 'Noel',
    12: 'Chisato',
}

PRIMARY_OFFSET = 0x1A0
RECORD_SIZE = 0x60


def classify_triplet(t):
    base, inter, eff = t
    if base == inter == eff:
        return f'Flat ({base},{inter},{eff})'
    if inter == 0 and eff == 0:
        return f'Zeroed ({base},0,0)'
    if inter == base + 2 and eff == base + 2:
        return f'Diverged (+2) ({base},{inter},{eff})'
    diff1 = inter - base
    diff2 = eff - base
    sign1 = f'+{diff1}' if diff1 >= 0 else str(diff1)
    sign2 = f'+{diff2}' if diff2 >= 0 else str(diff2)
    return f'Diverged ({sign1},{sign2}) ({base},{inter},{eff})'


def scan_file(path: Path):
    try:
        _, card = saveconv.load_card(path)
    except Exception as e:
        return []

    results = []
    for f, order in saveconv.chains(card):
        fname = f['name']
        if not fname.startswith('BASCUS'):
            continue
        block = card[order[0] * saveconv.BLOCK : (order[0] + 1) * saveconv.BLOCK]
        try:
            st = so2_codec.state(block)
        except Exception:
            continue

        members = []
        for slot in range(8):
            base_off = PRIMARY_OFFSET + slot * RECORD_SIZE
            cid = struct.unpack_from('<h', st, base_off)[0]
            if cid == 0:
                continue
            name = NAMES.get(abs(cid), f'ID_{cid}')
            lvl = struct.unpack_from('<H', st, base_off + 0x26)[0]
            a_triplet = struct.unpack_from('<HHH', st, base_off + 0x4E)
            b_triplet = struct.unpack_from('<HHH', st, base_off + 0x54)
            members.append({
                'slot': slot,
                'cid': cid,
                'name': name,
                'level': lvl,
                'a': a_triplet,
                'a_state': classify_triplet(a_triplet),
                'b': b_triplet,
                'b_state': classify_triplet(b_triplet),
            })

        results.append({
            'card': path.name,
            'save_title': fname,
            'members': members,
        })
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        'target',
        nargs='?',
        default=str(Path(r'C:\CodeTesting\StarOcean2\SaveGames')),
        help='Target .mcd file or directory containing saves (default: C:\\CodeTesting\\StarOcean2\\SaveGames)',
    )
    args = parser.parse_args()

    target_path = Path(args.target)
    if target_path.is_file():
        files = [target_path]
    elif target_path.is_dir():
        files = sorted(target_path.glob('**/*.mcd'))
    else:
        print(f'Error: Target path not found: {target_path}', file=sys.stderr)
        sys.exit(1)

    total_saves = 0
    for p in files:
        file_results = scan_file(p)
        if not file_results:
            continue
        for res in file_results:
            total_saves += 1
            print(f"=== {res['card']} | {res['save_title']} ===")
            for m in res['members']:
                status = 'Active' if m['cid'] > 0 else 'Benched'
                print(
                    f"  Slot {m['slot']}: {m['name']:7s} (ID={m['cid']:3d}, {status:7s}) Lv {m['level']:3d} | "
                    f"A: {m['a_state']:26s} | B: {m['b_state']:26s}"
                )
            print()

    print(f'Scan completed: {total_saves} valid save blocks parsed across {len(files)} files.')


if __name__ == '__main__':
    main()
