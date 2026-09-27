"""Regression checks against extracted game instructions, not a live load test."""
from pathlib import Path
import struct
import unittest

import saveconv
import so2_fol
import so2_party
from tools.so2_party_mips import Machine, initial_records
from tools.verify_so2_fol import run_codec

ROOT = Path(__file__).resolve().parents[1]


class PartyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code = so2_party.DEFAULT_CODE.read_bytes()

    def machine(self, ids=()):
        m = Machine(self.code)
        m.put(0x8007527c, struct.pack('<I', 0x80100000))
        m.put(0x80075280, struct.pack('<I', 0x80110000))
        for i, cid in enumerate(ids):
            a, b = initial_records(self.code, abs(cid)) if cid else (bytes(96), bytes(208))
            m.put(0x80100000 + 96*i, a)
            m.put(0x80110000 + 208*i, b)
            m.put(0x80100000 + 96*i, struct.pack('<h', cid))
        return m

    def recruit(self, m, cid):
        # Explicitly stub the two runtime graphics/task refresh calls only.
        m.run(0x80069008, (0, cid-1),
              {0x8007972c: lambda m, r: None, 0x8004358c: lambda m, r: None})

    def test_all_initializers_identity_and_names(self):
        names = ['Claude','Rena','Celine','Bowman','Dias','Precis','Ashton','Leon',
                 'Opera','Ernest','Noel','Chisato']
        for cid, name in enumerate(names, 1):
            a, b = initial_records(self.code, cid)
            self.assertEqual(struct.unpack_from('<h', a)[0], cid)
            self.assertEqual(b[0x24:0x2c].split(b'\0')[0].decode(), name)
            self.assertLessEqual(int.from_bytes(b[0x20:0x24], 'little'), 0x3ff)

    def test_name_only_edit_does_not_activate_or_change_identity(self):
        m = self.machine([1, 2, 3])
        m.put(0x80110000 + 208*2 + 0x24, b'Opera\0\0\0')
        m.run(0x800331c8, (2,))
        self.assertEqual(m.run(0x800337a4), 3)
        m.put(0x80110000 + 208*6, bytes(m.memory[0x110000:0x1100d0]))
        m.run(0x800331c8, (6,))
        self.assertEqual(m.run(0x800337a4), 0)

    def test_equipment_mask_uses_id(self):
        m = self.machine([3, 9])
        m.put(0x80120000, struct.pack('<I', 0x80120100))
        m.put(0x80120100, struct.pack('<H', 1 << 8))  # item usable by Opera
        m.run(0x800331c8, (0,))
        self.assertEqual(m.run(0x8003ba74, (0x80120000, 1)), 0)
        m.run(0x800331c8, (1,))
        self.assertEqual(m.run(0x8003ba74, (0x80120000, 1)), 1 << 8)

    def test_recruit_initializes_both_records_first_free(self):
        m = self.machine([1, 2])
        before = bytes(m.memory)
        self.recruit(m, 9)
        a, b = initial_records(self.code, 9)
        self.assertEqual(m.memory[0x1000c0:0x100120], a)
        self.assertEqual(m.memory[0x1101a0:0x110270], b)
        self.assertEqual(m.memory[0x100000:0x1000c0], before[0x100000:0x1000c0])
        self.assertEqual(m.run(0x800692a0, (0, 8)), 2)

    def test_remove_and_rejoin_preserve_records(self):
        m = self.machine([1, 2, 3, 4, 9])
        a, b = bytes(m.memory[0x100180:0x1001e0]), bytes(m.memory[0x110340:0x110410])
        m.run(0x80069200, (0, 8))
        self.assertEqual(struct.unpack_from('<h', m.memory, 0x100180)[0], -9)
        self.assertEqual(m.run(0x800692a0, (0, 8)), 0xffffffff)
        self.recruit(m, 9)
        self.assertEqual(m.memory[0x100180:0x1001e0], a)
        self.assertEqual(m.memory[0x110340:0x110410], b)

    def test_recruit_preserves_displaced_negative_pair(self):
        m = self.machine([1, 2, -3])
        a = bytes(m.memory[0x1000c0:0x100120])
        b = bytes(m.memory[0x1101a0:0x110270])
        self.recruit(m, 9)
        self.assertEqual(struct.unpack_from('<h', m.memory, 0x1000c0)[0], 9)
        self.assertEqual(m.memory[0x100120:0x100180], a)
        self.assertEqual(m.memory[0x110270:0x110340], b)

    def test_full_positive_party_is_unchanged(self):
        m = self.machine([1, 2, 3, 4, 5, 6, 7, 8])
        before = bytes(m.memory[0x100000:0x110680])
        self.recruit(m, 9)
        self.assertEqual(m.memory[0x100000:0x110680], before)

    def test_save_candidate_matches_actual_codec_and_limits_edits(self):
        _, card = saveconv.load_card(ROOT / 'artifacts/so2-fol/fol-5000-candidate.mcd')
        first, order = next((f, o) for f, o in saveconv.chains(card) if f['name'].endswith('S13'))
        start = order[0] * saveconv.BLOCK
        old = card[start:start + saveconv.BLOCK]
        new, slot = so2_party.add_member(old, 9, self.code)
        self.assertEqual(slot, 2)
        self.assertTrue(saveconv.so2_valid(new))
        overlay = (ROOT / 'artifacts/so2-fol/disc-code/code-2998-lba-36213.bin').read_bytes()
        end = struct.unpack_from('<H', new, 0x21a)[0]
        decoded = so2_fol.state(new)
        self.assertEqual(run_codec(overlay, new[0x380:end]), decoded)
        self.assertEqual(run_codec(overlay, decoded, encode=True), new[0x380:end])
        for i, (a, b) in enumerate(zip(so2_fol.state(old), decoded)):
            if a != b:
                self.assertTrue(0x260 <= i < 0x2c0 or 0x640 <= i < 0x710)
        with self.assertRaises(saveconv.SaveError): so2_party.add_member(new, 9, self.code)
        with self.assertRaises(saveconv.SaveError): so2_party.add_member(old, 9, self.code, slot=0)


if __name__ == '__main__':
    unittest.main()
