"""Star Ocean: The Second Story (PS1) - DuckStation Live Memory & Save-State Diff Tool.

Inspects DuckStation save states (.sav, Zstandard DUCC containers) and extracts
the uncompressed 2 MB PS1 Main RAM directly from the Bus device section.
Decodes the live Party Primary Array (stride 0x60, 96 bytes) and Secondary Array
(stride 0xD0, 208 bytes) via RAM pointers at [0x8007527C] and [0x80075280].

Enables controlled live-play testing without an emulator scripting console:
1. Human player creates save states in DuckStation before and after actions:
   - Before combat vs After attack
   - After taking damage / hit
   - After casting spell / killer move
   - After level-up
2. Tool computes exact byte-by-byte diffs across all 96 primary record bytes,
   identifying state changes in the unknown/opaque field ranges.

Usage:
  python tools/so2_live_memory_diff.py --list
  python tools/so2_live_memory_diff.py --inspect "C:/CodeTesting/StarOcean2/SaveGames/SCUS-94422_resume.sav"
  python tools/so2_live_memory_diff.py --diff "C:/CodeTesting/StarOcean2/SaveGames/SCUS-94422_10.sav" "C:/CodeTesting/StarOcean2/SaveGames/SCUS-94422_resume.sav"
"""
from __future__ import annotations

import argparse
from pathlib import Path
import struct
import sys
from typing import Any, Dict, List, Optional, Tuple
import zstandard

_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SAVES_DIR = Path("C:/CodeTesting/StarOcean2/SaveGames")

PRIMARY_FIELD_MAP: Dict[int, Tuple[str, int]] = {
    0x00: ("Character ID (Signed)", 2),
    0x02: ("Status Condition Flags", 1),
    0x03: ("Class / Combat Stance Code", 1),
    0x04: ("Unknown Header (+04..0F)", 12),
    0x10: ("EXP", 4),
    0x14: ("HP Base Max", 4),
    0x18: ("HP Adjusted Max", 4),
    0x1C: ("HP Current", 4),
    0x20: ("MP Base Max", 2),
    0x22: ("MP Adjusted Max", 2),
    0x24: ("MP Current", 2),
    0x26: ("Derived Level", 2),
    0x28: ("Base Level", 2),
    0x2A: ("STR Base", 2),
    0x2C: ("STR Intermediate", 2),
    0x2E: ("STR Final", 2),
    0x30: ("CON Base", 2),
    0x32: ("CON Intermediate", 2),
    0x34: ("CON Final", 2),
    0x36: ("AGL Base", 2),
    0x38: ("AGL Intermediate", 2),
    0x3A: ("AGL Final", 2),
    0x3C: ("DEX Base", 2),
    0x3E: ("DEX Intermediate", 2),
    0x40: ("DEX Final", 2),
    0x42: ("INT Base", 2),
    0x44: ("INT Intermediate", 2),
    0x46: ("INT Final", 2),
    0x48: ("GUTS Base", 2),
    0x4A: ("GUTS Intermediate", 2),
    0x4C: ("GUTS Final / Combat Meter", 2),
    0x4E: ("Unknown Stat A Base (+4E)", 2),
    0x50: ("Unknown Stat A Int (+50)", 2),
    0x52: ("Unknown Stat A Final (+52)", 2),
    0x54: ("Unknown Stat B Base (+54)", 2),
    0x56: ("Unknown Stat B Int (+56)", 2),
    0x58: ("Unknown Stat B Final (+58)", 2),
    0x5A: ("Battle Participation / Affection (+5A)", 2),
    0x5C: ("Unknown Tail Flags (+5C..5F)", 4),
}


def extract_ps1_ram_from_sav(sav_path: Path) -> Optional[bytes]:
    """Extract uncompressed 2 MB PS1 Main RAM from a DuckStation .sav state."""
    if not sav_path.exists():
        return None

    raw = sav_path.read_bytes()
    dctx = zstandard.ZstdDecompressor()
    idx = 0
    while True:
        pos = raw.find(b"\x28\xb5\x2f\xfd", idx)
        if pos == -1:
            break
        try:
            decomp = dctx.decompressobj().decompress(raw[pos:])
            if len(decomp) >= 0x200000:
                # Find Sony kernel marker at +0xB0BC
                sony_pos = decomp.find(b"Sony Computer Entertainment Inc.")
                if sony_pos >= 0:
                    ram_start = sony_pos - 0xB0BC
                    ram = decomp[ram_start : ram_start + 0x200000]
                    if len(ram) == 0x200000:
                        return ram
        except Exception:
            pass
        idx = pos + 4

    return None


def read_party_records(ram: bytes) -> Dict[str, Any]:
    """Parse Party Primary Array (0x60 stride) and Secondary Array (0xD0 stride)."""
    ptr_pri = struct.unpack_from("<I", ram, 0x7527C)[0]
    ptr_sec = struct.unpack_from("<I", ram, 0x75280)[0]

    party: List[Dict[str, Any]] = []
    if not (0x80000000 <= ptr_pri < 0x80200000 and 0x80000000 <= ptr_sec < 0x80200000):
        return {"primary_ptr": ptr_pri, "secondary_ptr": ptr_sec, "valid": False, "members": []}

    base_pri = ptr_pri & 0x1FFFFF
    base_sec = ptr_sec & 0x1FFFFF

    for slot in range(8):
        pri_off = base_pri + slot * 0x60
        sec_off = base_sec + slot * 0xD0

        cid = struct.unpack_from("<h", ram, pri_off)[0]
        if cid == 0:
            continue

        pri_bytes = ram[pri_off : pri_off + 0x60]
        sec_bytes = ram[sec_off : sec_off + 0xD0]

        name = sec_bytes[0x24:0x2C].split(b"\x00")[0].decode("ascii", errors="ignore")
        hp_cur = struct.unpack_from("<I", pri_bytes, 0x1C)[0]
        hp_max = struct.unpack_from("<I", pri_bytes, 0x14)[0]
        mp_cur = struct.unpack_from("<H", pri_bytes, 0x24)[0]
        mp_max = struct.unpack_from("<H", pri_bytes, 0x20)[0]
        lvl = struct.unpack_from("<H", pri_bytes, 0x28)[0]
        exp = struct.unpack_from("<I", pri_bytes, 0x10)[0]

        member: Dict[str, Any] = {
            "slot": slot,
            "character_id": cid,
            "name": name if name else f"Hero_{cid}",
            "level": lvl,
            "exp": exp,
            "hp_current": hp_cur,
            "hp_max": hp_max,
            "mp_current": mp_cur,
            "mp_max": mp_max,
            "str_base": struct.unpack_from("<H", pri_bytes, 0x2A)[0],
            "str_final": struct.unpack_from("<H", pri_bytes, 0x2E)[0],
            "con_base": struct.unpack_from("<H", pri_bytes, 0x30)[0],
            "con_final": struct.unpack_from("<H", pri_bytes, 0x34)[0],
            "agl_base": struct.unpack_from("<H", pri_bytes, 0x36)[0],
            "agl_final": struct.unpack_from("<H", pri_bytes, 0x3A)[0],
            "dex_base": struct.unpack_from("<H", pri_bytes, 0x3C)[0],
            "dex_final": struct.unpack_from("<H", pri_bytes, 0x40)[0],
            "int_base": struct.unpack_from("<H", pri_bytes, 0x42)[0],
            "int_final": struct.unpack_from("<H", pri_bytes, 0x46)[0],
            "guts_base": struct.unpack_from("<H", pri_bytes, 0x48)[0],
            "guts_final": struct.unpack_from("<H", pri_bytes, 0x4C)[0],
            "unknown_a_base": struct.unpack_from("<H", pri_bytes, 0x4E)[0],
            "unknown_b_base": struct.unpack_from("<H", pri_bytes, 0x54)[0],
            "battle_count": struct.unpack_from("<H", pri_bytes, 0x5A)[0],
            "primary_bytes": list(pri_bytes),
            "secondary_bytes": list(sec_bytes),
        }
        party.append(member)

    return {
        "primary_ptr": ptr_pri,
        "secondary_ptr": ptr_sec,
        "valid": True,
        "members": party
    }


def list_save_states(saves_dir: Path = DEFAULT_SAVES_DIR) -> None:
    """List all available DuckStation .sav files and summary of active party."""
    print(f"Scanning save states in: {saves_dir}")
    sav_files = sorted(saves_dir.glob("*.sav"))
    if not sav_files:
        print("  No .sav files found.")
        return

    for f in sav_files:
        ram = extract_ps1_ram_from_sav(f)
        if ram is None:
            print(f"  {f.name:<25} [Unreadable DUCC/RAM]")
            continue
        info = read_party_records(ram)
        if not info["valid"]:
            print(f"  {f.name:<25} [Invalid Pointers: Pri={info['primary_ptr']:#x}]")
            continue

        members = [f"{m['name']} (Lv{m['level']})" for m in info["members"]]
        print(f"  {f.name:<25} Party ({len(members)}): {', '.join(members)}")


def inspect_save_state(sav_path: Path) -> None:
    """Print full character sheet and 96-byte hex dump for all party members in state."""
    ram = extract_ps1_ram_from_sav(sav_path)
    if ram is None:
        print(f"Error: Unable to extract PS1 RAM from {sav_path}")
        return

    info = read_party_records(ram)
    if not info["valid"]:
        print(f"Error: Invalid party pointers in {sav_path} (Pri={info['primary_ptr']:#x})")
        return

    print(f"\n=======================================================")
    print(f" Save State Inspection: {sav_path.name}")
    print(f" Primary Array RAM:   {info['primary_ptr']:#010x}")
    print(f" Secondary Array RAM: {info['secondary_ptr']:#010x}")
    print(f" Active Party Members: {len(info['members'])}")
    print(f"=======================================================\n")

    for m in info["members"]:
        print(f"--- Slot {m['slot']}: {m['name']} (ID {m['character_id']}) ---")
        print(f"  Level: {m['level']} | EXP: {m['exp']:,} | Battle Count: {m['battle_count']}")
        print(f"  HP: {m['hp_current']} / {m['hp_max']} | MP: {m['mp_current']} / {m['mp_max']}")
        print(f"  STR: {m['str_base']} (Final: {m['str_final']}) | CON: {m['con_base']} (Final: {m['con_final']})")
        print(f"  AGL: {m['agl_base']} (Final: {m['agl_final']}) | DEX: {m['dex_base']} (Final: {m['dex_final']})")
        print(f"  INT: {m['int_base']} (Final: {m['int_final']}) | GUTS: {m['guts_base']} (Final: {m['guts_final']})")
        print(f"  Unknown A (+4E): {m['unknown_a_base']} | Unknown B (+54): {m['unknown_b_base']}")
        
        # Primary hex dump
        pbytes = bytes(m["primary_bytes"])
        print("  Primary Array (96 Bytes):")
        for row in range(0, 96, 16):
            chunk = pbytes[row : row + 16]
            hex_str = " ".join(f"{b:02x}" for b in chunk)
            print(f"    +{row:#04x}: {hex_str}")
        print()


def diff_save_states(sav1_path: Path, sav2_path: Path) -> None:
    """Compare two save states byte-for-byte across the Party Primary Array."""
    ram1 = extract_ps1_ram_from_sav(sav1_path)
    ram2 = extract_ps1_ram_from_sav(sav2_path)
    if ram1 is None or ram2 is None:
        print("Error: Could not extract RAM from one or both save states.")
        return

    info1 = read_party_records(ram1)
    info2 = read_party_records(ram2)

    print(f"\n=======================================================")
    print(f" Save State Primary Array Diff")
    print(f" State 1: {sav1_path.name}")
    print(f" State 2: {sav2_path.name}")
    print(f"=======================================================\n")

    m1_by_id = {m["character_id"]: m for m in info1["members"]}
    m2_by_id = {m["character_id"]: m for m in info2["members"]}

    all_ids = sorted(set(m1_by_id.keys()) | set(m2_by_id.keys()))

    total_diffs = 0
    for cid in all_ids:
        if cid not in m1_by_id:
            print(f"[+] Character ID {cid} ({m2_by_id[cid]['name']}) added in State 2.")
            continue
        if cid not in m2_by_id:
            print(f"[-] Character ID {cid} ({m1_by_id[cid]['name']}) removed in State 2.")
            continue

        c1 = m1_by_id[cid]
        c2 = m2_by_id[cid]
        b1 = c1["primary_bytes"]
        b2 = c2["primary_bytes"]

        diffs = []
        for i in range(96):
            if b1[i] != b2[i]:
                diffs.append((i, b1[i], b2[i]))

        if not diffs:
            print(f"Character {c1['name']} (ID {cid}): No primary array changes.")
            continue

        total_diffs += len(diffs)
        print(f"--- Character {c1['name']} (ID {cid}) [{len(diffs)} byte differences] ---")
        for b_idx, val1, val2 in diffs:
            flabel = "Unknown Byte"
            for off, (name, sz) in sorted(PRIMARY_FIELD_MAP.items()):
                if off <= b_idx < off + sz:
                    flabel = f"{name} (+{b_idx:#04x})"
                    break
            print(f"  Offset +{b_idx:#04x} [{flabel}]: {val1:#04x} ({val1}) -> {val2:#04x} ({val2})")
        print()

    print(f"Total modified bytes detected across party: {total_diffs}")


def main() -> None:
    parser = argparse.ArgumentParser(description="DuckStation SO2 Live Save-State Memory Diff Tool")
    parser.add_argument("--list", action="store_true", help="List all available DuckStation .sav states")
    parser.add_argument("--inspect", type=Path, help="Inspect a specific .sav state in detail")
    parser.add_argument("--diff", nargs=2, type=Path, metavar=("SAV1", "SAV2"), help="Diff two .sav states")
    args = parser.parse_args()

    if args.list:
        list_save_states()
    elif args.inspect:
        inspect_save_state(args.inspect)
    elif args.diff:
        diff_save_states(args.diff[0], args.diff[1])
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
