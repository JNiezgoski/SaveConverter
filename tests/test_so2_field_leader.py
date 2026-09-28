"""Unit tests for SO2 field leader graphics consumer and party streaming."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.so2_party_mips import Machine

ENTRY_2576 = ROOT / 'artifacts/so2-options-menu/entry-2576.bin'
RAM_DISC1 = ROOT / 'artifacts/so2-options-menu/ram-disc1.bin'
RAM_DISC2 = ROOT / 'artifacts/so2-options-menu/ram-disc2.bin'


class FieldLeaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code = ENTRY_2576.read_bytes()
        cls.ram1 = RAM_DISC1.read_bytes()
        cls.ram2 = RAM_DISC2.read_bytes()

    def test_graphics_consumer_lookup_disc1(self):
        """Entry 3117 in Disc 1 RAM has selectors 0..3 (Claude, Rena, Celine, Bowman)."""
        m = Machine(self.code)
        m.put(0x8007585C, self.ram1[0x7585C : 0x7585C + 16 * 12])
        m.put(0x800E5AB0, self.ram1[0x0E5AB0 : 0x0E5AB0 + 0x192B8])

        # Test selectors 0..3 resolve to valid subblocks; selector 4 (Dias) is NULL because Dias not in 3117.
        self.assertEqual(m.run(0x80042E4C, [13, 0]), 0x800E5AC4)
        self.assertEqual(m.run(0x80042E4C, [13, 1]), 0x800EF010)
        self.assertEqual(m.run(0x80042E4C, [13, 2]), 0x800F87D0)
        self.assertEqual(m.run(0x80042E4C, [13, 3]), 0x800FBB5C)
        self.assertEqual(m.run(0x80042E4C, [13, 4]), 0x00000000)

    def test_graphics_consumer_lookup_dias_disc2(self):
        """Entry 3125 in Disc 2 RAM has selectors 0..4 including Dias (sel 4)."""
        m = Machine(self.code)
        m.put(0x8007585C, self.ram2[0x7585C : 0x7585C + 16 * 12])
        m.put(0x800E5AB0, self.ram2[0x0E5AB0 : 0x0E5AB0 + 0x1C630])

        # Selector 4 resolves to Dias's animation subblock at 0x800fed6c.
        dias_ptr = m.run(0x80042E4C, [13, 4])
        self.assertEqual(dias_ptr, 0x800FED6C)
        # Verify Dias subblock header and selector record in RAM
        sub_off = dias_ptr - 0x80000000
        n_rec = struct.unpack_from('<I', self.ram2, sub_off)[0]
        self.assertEqual(n_rec, 2)
        rec0 = struct.unpack_from('<IIIIIII', self.ram2, sub_off + 4)
        self.assertEqual(rec0[0], 4)  # word0 = selector 4 (Dias)
        self.assertEqual(rec0[1], 0)  # anim sub-type
        self.assertEqual(rec0[2], 13) # anim_min = 13 (idle/walk)

    def test_party_bitmask_and_archive_selection(self):
        """Verify 80061BD0 generates party bitmask and maps to archive entries."""
        primary_addr = 0x801E0000
        m = Machine(self.code)

        def eval_party(ids):
            m.put(primary_addr, b'\x00' * 0x300)
            for i, cid in enumerate(ids):
                m.put(primary_addr + i * 0x60, struct.pack('<h', cid))

            def hook_res(m, r):
                r[2] = primary_addr if r[5] == 3 else 0

            mask = m.run(0x80061BD0, hooks={0x80012108: hook_res})
            g1_entry = 3111 + 2 * ((mask >> 2) & 0x1F)
            return mask, g1_entry

        # Claude (1) + Rena (2) -> mask 0b11 = 3 -> Group 1 Entry 3111
        mask, entry = eval_party([1, 2])
        self.assertEqual(mask, 3)
        self.assertEqual(entry, 3111)

        # Claude + Rena + Celine (3) -> mask 0b111 = 7 -> Entry 3113
        mask, entry = eval_party([1, 2, 3])
        self.assertEqual(mask, 7)
        self.assertEqual(entry, 3113)

        # Claude + Rena + Dias (5) -> mask = (1<<0)|(1<<1)|(1<<4) = 19 -> Entry 3119
        mask, entry = eval_party([1, 2, 5])
        self.assertEqual(mask, 19)
        self.assertEqual(entry, 3119)

        # Claude + Rena + Celine + Bowman + Dias -> mask 31 -> Entry 3125
        mask, entry = eval_party([1, 2, 3, 4, 5])
        self.assertEqual(mask, 31)
        self.assertEqual(entry, 3125)


if __name__ == '__main__':
    unittest.main()
