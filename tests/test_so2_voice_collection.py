import os
from pathlib import Path
import tempfile
import unittest

from saveconv import so2_sign, so2_valid
from tools.so2_voice_collection import (
    CHARACTERS,
    TOTAL_VOICES,
    analyze_card,
    build_unlock_bitfield,
    merge_memory_card_voices,
    parse_voice_bitfield,
    patch_slot_voice_collection,
)


class VoiceCollectionTests(unittest.TestCase):
    def test_voice_collection_census(self):
        self.assertEqual(sum(q for _, q in CHARACTERS), 1278)
        self.assertEqual(TOTAL_VOICES, 1278)

    def test_parse_and_build_bitfield(self):
        # 100% unlock
        all_bits = build_unlock_bitfield(100.0)
        self.assertEqual(len(all_bits), 160)
        stats100 = parse_voice_bitfield(all_bits)
        self.assertEqual(stats100["total_unlocked"], 1278)
        self.assertEqual(stats100["percent"], 100.0)

        # 50% unlock
        half_bits = build_unlock_bitfield(50.0)
        stats50 = parse_voice_bitfield(half_bits)
        self.assertAlmostEqual(stats50["percent"], 50.0, delta=1.0)
        self.assertGreaterEqual(stats50["total_unlocked"], 638)

    def test_card_audit_merge_and_patch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            card_path = Path(tmpdir) / "test_card.mcd"
            card = bytearray(131072)

            # Slot 1: Claude voices
            block1 = bytearray(8192)
            block1[:4] = b"SC\x13\x01"
            block1[0x200:0x210] = b"STAR OCEAN 03/01\0"
            block1[0x218:0x21A] = b"UU"
            block1[0x280] = 0xFF
            block1[0x281] = 0x03
            so2_sign(block1)
            card[0x2000:0x4000] = block1

            # Slot 2: Rena voices
            block2 = bytearray(8192)
            block2[:4] = b"SC\x13\x01"
            block2[0x200:0x210] = b"STAR OCEAN 03/01\0"
            block2[0x218:0x21A] = b"UU"
            block2[0x28C] = 0x80
            block2[0x28D] = 0x7F
            so2_sign(block2)
            card[0x4000:0x6000] = block2

            card_path.write_bytes(card)

            # Audit
            audit = analyze_card(card_path)
            self.assertEqual(len(audit), 2)
            self.assertEqual(audit[1]["total_unlocked"], 10)
            self.assertEqual(audit[2]["total_unlocked"], 8)

            # Merge
            merge_memory_card_voices(card_path)
            merged_audit = analyze_card(card_path)
            self.assertEqual(merged_audit[1]["total_unlocked"], 18)
            self.assertEqual(merged_audit[2]["total_unlocked"], 18)

            # Re-read card to verify checksums
            updated_card = card_path.read_bytes()
            self.assertTrue(so2_valid(updated_card[0x2000:0x4000]))
            self.assertTrue(so2_valid(updated_card[0x4000:0x6000]))

            # Patch slot 1 to 100%
            patch_slot_voice_collection(card_path, slot=1, percent=100.0)
            patched_audit = analyze_card(card_path)
            self.assertEqual(patched_audit[1]["total_unlocked"], 1278)
            final_card = card_path.read_bytes()
            self.assertTrue(so2_valid(final_card[0x2000:0x4000]))


if __name__ == "__main__":
    unittest.main()
