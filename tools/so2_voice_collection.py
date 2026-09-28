"""Star Ocean: The Second Story (PS1) - Voice Collection Analyzer & Unlocker.

Reverse-engineered Voice Collection architecture:
- Total Voices: Exactly 1,278 voices across 12 characters.
- Storage: 160 bytes (1,280 bits) located at uncompressed save header offset 0x0280..0x031F.
- RAM Location: 0x8009C138 (S + 0x1A0).
- Save Merging: The game reads this uncompressed header across all 15 memory card blocks
  and bitwise-ORs them into the global voice collection buffer on boot / Voice Collection menu.

Character Voice Counts (derived from Archives 3028..3039 word 1):
  1. Claude (ID 1)  : 103 voices (Bits 0..102)
  2. Rena (ID 2)    : 114 voices (Bits 103..216)
  3. Celine (ID 3)  : 104 voices (Bits 217..320)
  4. Bowman (ID 4)  : 104 voices (Bits 321..424)
  5. Dias (ID 5)    : 104 voices (Bits 425..528)
  6. Precis (ID 6)  : 108 voices (Bits 529..636)
  7. Ashton (ID 7)  : 116 voices (Bits 637..752)
  8. Leon (ID 8)    :  96 voices (Bits 753..848)
  9. Opera (ID 9)   : 112 voices (Bits 849..960)
 10. Ernest (ID 10) : 104 voices (Bits 961..1064)
 11. Noel (ID 11)   : 108 voices (Bits 1065..1172)
 12. Chisato (ID 12): 108 voices (Bits 1173..1280)
 Total: 1,278 voices
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import struct
import sys
from typing import Any, Dict, List, Optional, Tuple

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "scripts"))
import saveconv

VOICE_HEADER_OFFSET = 0x0280
VOICE_BYTE_LEN = 160  # 160 bytes = 1,280 bits

CHARACTERS: List[Tuple[str, int]] = [
    ("Claude", 103),
    ("Rena", 114),
    ("Celine", 104),
    ("Bowman", 104),
    ("Dias", 104),
    ("Precis", 108),
    ("Ashton", 116),
    ("Leon", 96),
    ("Opera", 112),
    ("Ernest", 104),
    ("Noel", 108),
    ("Chisato", 105),  # 108 combat entries minus 3 unused trailer indices = 105 voices
]
TOTAL_VOICES = sum(c[1] for c in CHARACTERS)  # 1278


def parse_voice_bitfield(data160: bytes) -> Dict[str, Any]:
    """Parse 160-byte bitmask into per-character unlocked voice statistics."""
    bits: List[int] = []
    for b in data160:
        for bit in range(8):
            bits.append((b >> bit) & 1)

    char_stats = []
    bit_cursor = 0
    total_unlocked = 0

    for name, max_count in CHARACTERS:
        char_bits = bits[bit_cursor : bit_cursor + max_count]
        unlocked = sum(char_bits)
        total_unlocked += unlocked
        char_stats.append({
            "character": name,
            "unlocked": unlocked,
            "max": max_count,
            "percent": round((unlocked / max_count) * 100, 1),
            "bits": char_bits
        })
        bit_cursor += max_count

    return {
        "total_unlocked": total_unlocked,
        "max_voices": TOTAL_VOICES,
        "percent": round((total_unlocked / TOTAL_VOICES) * 100, 1),
        "characters": char_stats
    }


def analyze_card(card_path: Path) -> Dict[int, Dict[str, Any]]:
    """Scan all 15 slots in a memory card file and report Voice Collection status."""
    data = card_path.read_bytes()
    results = {}
    for slot in range(1, 16):
        base = slot * saveconv.BLOCK
        block = data[base : base + saveconv.BLOCK]
        if len(block) >= 0x380 and block[0x200:0x20A] == b"STAR OCEAN":
            v_bytes = block[VOICE_HEADER_OFFSET : VOICE_HEADER_OFFSET + VOICE_BYTE_LEN]
            results[slot] = parse_voice_bitfield(v_bytes)
    return results


def build_unlock_bitfield(percent: float = 100.0) -> bytes:
    """Generate a 160-byte bitfield with up to the given percentage of voices unlocked."""
    bits = [0] * (VOICE_BYTE_LEN * 8)
    bit_cursor = 0
    target_ratio = min(max(percent / 100.0, 0.0), 1.0)

    for name, max_count in CHARACTERS:
        count_to_unlock = int(round(max_count * target_ratio))
        for i in range(count_to_unlock):
            bits[bit_cursor + i] = 1
        bit_cursor += max_count

    # Pack bits to 160 bytes
    out = bytearray(VOICE_BYTE_LEN)
    for byte_idx in range(VOICE_BYTE_LEN):
        val = 0
        for bit_idx in range(8):
            if bits[byte_idx * 8 + bit_idx]:
                val |= (1 << bit_idx)
        out[byte_idx] = val
    return bytes(out)


def patch_slot_voice_collection(
    card_path: Path,
    slot: int,
    percent: float = 100.0,
    out_path: Optional[Path] = None
) -> bool:
    """Patch the Voice Collection bitfield in a specific save slot and resign checksums."""
    data = bytearray(card_path.read_bytes())
    base = slot * saveconv.BLOCK
    block = bytearray(data[base : base + saveconv.BLOCK])
    if block[0x200:0x20A] != b"STAR OCEAN":
        print(f"Error: Slot {slot} is not a valid Star Ocean save.")
        return False

    v_bitfield = build_unlock_bitfield(percent)
    block[VOICE_HEADER_OFFSET : VOICE_HEADER_OFFSET + VOICE_BYTE_LEN] = v_bitfield

    # Re-calculate checksums A and B
    saveconv.so2_sign(block)

    data[base : base + saveconv.BLOCK] = block
    dst = out_path or card_path
    dst.write_bytes(data)
    print(f"Patched Slot {slot} with {percent}% Voice Collection -> Saved to {dst.name}")
    return True


def merge_memory_card_voices(card_path: Path, out_path: Optional[Path] = None) -> bytes:
    """Merge Voice Collection bitfields across all save slots on a card and write to all slots."""
    data = bytearray(card_path.read_bytes())
    merged_bitfield = bytearray(VOICE_BYTE_LEN)
    active_slots = []

    for slot in range(1, 16):
        base = slot * saveconv.BLOCK
        block = data[base : base + saveconv.BLOCK]
        if block[0x200:0x20A] == b"STAR OCEAN":
            active_slots.append(slot)
            v_bytes = block[VOICE_HEADER_OFFSET : VOICE_HEADER_OFFSET + VOICE_BYTE_LEN]
            for i in range(VOICE_BYTE_LEN):
                merged_bitfield[i] |= v_bytes[i]

    print(f"Found {len(active_slots)} save slots: {active_slots}")
    merged_stats = parse_voice_bitfield(bytes(merged_bitfield))
    print(f"Merged Voice Collection: {merged_stats['total_unlocked']} / {TOTAL_VOICES} ({merged_stats['percent']}%)")

    # Apply merged bitfield back to all active save slots
    for slot in active_slots:
        base = slot * saveconv.BLOCK
        block = bytearray(data[base : base + saveconv.BLOCK])
        block[VOICE_HEADER_OFFSET : VOICE_HEADER_OFFSET + VOICE_BYTE_LEN] = merged_bitfield
        saveconv.so2_sign(block)
        data[base : base + saveconv.BLOCK] = block

    dst = out_path or card_path
    dst.write_bytes(data)
    print(f"Updated all {len(active_slots)} save slots with unified Voice Collection on {dst.name}")
    return bytes(merged_bitfield)


def main():
    parser = argparse.ArgumentParser(description="Star Ocean 2 Voice Collection Tool")
    parser.add_argument("card", type=Path, help="Path to .mcd / .mcr memory card")
    parser.add_argument("--slot", type=int, default=None, help="Target specific save slot (1..15)")
    parser.add_argument("--unlock", type=float, default=None, help="Unlock target percentage (e.g. 50, 75, 100)")
    parser.add_argument("--merge", action="store_true", help="Merge voice collections across all slots")
    parser.add_argument("--out", type=Path, default=None, help="Output memory card path")

    args = parser.parse_args()
    if not args.card.exists():
        print(f"Error: Card file {args.card} does not exist.")
        return

    if args.merge:
        merge_memory_card_voices(args.card, args.out)
        return

    if args.unlock is not None:
        slot = args.slot or 1
        patch_slot_voice_collection(args.card, slot, percent=args.unlock, out_path=args.out)
        return

    # Default: Audit and print report
    card_report = analyze_card(args.card)
    print("=" * 65)
    print(f"STAR OCEAN 2 - VOICE COLLECTION AUDIT: {args.card.name}")
    print("=" * 65)
    for slot, report in sorted(card_report.items()):
        print(f"\n--- Save Slot {slot} --- [Total: {report['total_unlocked']}/{report['max_voices']} ({report['percent']}%) ]")
        for c in report["characters"]:
            print(f"  {c['character']:10s}: {c['unlocked']:3d} / {c['max']:3d} ({c['percent']:5.1f}%)")


if __name__ == "__main__":
    main()
