"""Inventory behavior checked against extracted game instructions."""
from pathlib import Path
import random
import struct
import unittest

import saveconv
import so2_fol
import so2_inventory as inv
from tools.so2_inventory_evidence import serialize
from tools.verify_so2_fol import run_codec

ROOT = Path(__file__).resolve().parents[1]


class InventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code = inv.DEFAULT_CODE.read_bytes()
        cls.overlay = (ROOT / 'artifacts/so2-fol/disc-code/code-2998-lba-36213.bin').read_bytes()

    def chunk(self, entries=()):
        data = bytearray(inv.SIZE)
        for slot, item, count in entries:
            struct.pack_into('<H', data, slot*2, item | count << 10)
        return data

    def test_first_hole_without_sorting_shifting_or_terminator(self):
        data = self.chunk([(0, 900, 2), (2, 1, 3), (1023, 700, 4)])
        result, slot = inv.execute_add(self.code, data, 364, 20)
        self.assertEqual(slot, 1)
        self.assertEqual(struct.unpack_from('<H', result, 2)[0], 0xd16c)
        self.assertEqual(result[4:0x800], data[4:0x800])
        self.assertEqual(struct.unpack_from('<H', result, 0x800)[0], 364)

    def test_existing_type_after_hole_is_updated_not_duplicated(self):
        data = self.chunk([(900, 364, 1)])
        result, slot = inv.execute_add(self.code, data, 364, 19)
        self.assertEqual(slot, 900)
        self.assertEqual(result[:1800], data[:1800])
        with self.assertRaises(saveconv.SaveError):
            inv.execute_add(self.code, result, 364, 1)

    def test_zero_count_stale_id_is_vacant_and_mark_bit_is_separate(self):
        data = self.chunk()
        struct.pack_into('<H', data, 0, 0x8000 | 100)
        for marked in (0, 1):
            result, slot = inv.execute_add(self.code, data, 364, 20, marked)
            self.assertEqual(slot, 0)
            self.assertEqual(struct.unpack_from('<H', result)[0], 0x516c | marked << 15)

    def test_recent_list_promote_truncate_and_reset(self):
        for recent, flag in [(list(range(1, 17)), 0), ([1, 2, 364]+list(range(4, 17)), 0),
                             (list(range(1, 17)), 1)]:
            data = self.chunk()
            struct.pack_into('<16H', data, inv.RECENT, *recent)
            data[inv.FLAG] = flag
            result, _ = inv.execute_add(self.code, data, 364, 1)
            actual = list(struct.unpack_from('<16H', result, inv.RECENT))
            expected = [364] + ([0]*15 if flag else [i for i in recent if i != 364][:15])
            self.assertEqual(actual, expected)
            self.assertEqual(result[inv.FLAG], 0)

    def test_integrity_formula_and_validator_against_instructions(self):
        m = inv.loaded_machine(self.code, self.chunk())
        rng = random.Random(41)
        for _ in range(100):
            slot, word, nonce = rng.randrange(1024), rng.randrange(65536), rng.randrange(16)
            m.put(inv.RAM + 2*slot, struct.pack('<H', word))
            actual = m.run(0x8003c8a0, (inv.RAM, slot, nonce))
            self.assertEqual(actual, inv.integrity(word, slot, nonce))
            m.put(inv.RAM + inv.CACHE + slot, bytes([actual]))
            self.assertEqual(m.run(0x8003c928, (inv.RAM, slot)), 1)
            m.put(inv.RAM + inv.CACHE + slot, bytes([actual ^ 1]))
            self.assertEqual(m.run(0x8003c928, (inv.RAM, slot)), 0)

    def test_removal_clears_fixed_word_and_next_add_reuses_hole(self):
        data = self.chunk([(0, 364, 20), (1, 385, 1)])
        m = inv.loaded_machine(self.code, data)
        m.run(0x8003c798, (inv.RAM, 0, 20))
        self.assertEqual(m.memory[0x100000:0x100004], b'\0\0' + data[2:4])
        self.assertEqual(m.run(0x8003c928, (inv.RAM, 0)), 1)
        self.assertEqual(m.run(0x8003c594, (inv.RAM, 100, 1, 1)), 1)
        self.assertEqual(struct.unpack_from('<H', m.memory, 0x100000)[0], 0x8464)
        self.assertEqual(m.memory[0x100002:0x100004], data[2:4])
        self.assertEqual(so2_fol.encode(bytes(10)), b'\0\0\x08')

    def test_capacity_and_overflow_game_paths(self):
        data = self.chunk([(i, i+1, 1) for i in range(1023)])
        # Low-level routine accepts all 1024 physical slots. Fill with duplicate
        # IDs only for this capacity branch test; editor rejects such input.
        struct.pack_into('<H', data, 2046, 1 | 1 << 10)
        m = inv.loaded_machine(self.code, data)
        # All valid IDs are present; request a raw out-of-domain ID to reach
        # the full/no-match path, without exposing that argument through CLI.
        self.assertEqual(m.run(0x8003c594, (inv.RAM, 1024, 1, 1)), 0)
        self.assertEqual(m.memory[0x100000:0x100800], data[:0x800])
        m = inv.loaded_machine(self.code, self.chunk([(0, 364, 20)]))
        self.assertEqual(m.run(0x8003c594, (inv.RAM, 364, 1, 1)), 0)
        self.assertEqual(struct.unpack_from('<H', m.memory, 0x100000)[0], 0x516c)

    def test_random_sparse_states_match_independent_prediction(self):
        rng = random.Random(17)
        for _ in range(20):
            ids = rng.sample([i for i in range(1, 1024) if i != 364], 50)
            slots = rng.sample(range(1024), 50)
            data = self.chunk([(s, i, rng.randrange(1, 21)) for s, i in zip(slots, ids)])
            struct.pack_into('<16H', data, inv.RECENT, *ids[:16])
            inv.execute_add(self.code, data, 364, rng.randrange(1, 21))

    def test_invalid_sources_fail_closed(self):
        for item, count in [(0, 1), (1024, 1), (364, 0), (364, 21), (364, -1)]:
            with self.assertRaises(saveconv.SaveError):
                inv.execute_add(self.code, self.chunk(), item, count)
        data = self.chunk([(0, 364, 1), (2, 364, 2)])
        with self.assertRaises(saveconv.SaveError): inv.execute_add(self.code, data, 385, 1)
        data = self.chunk()
        data[inv.CACHE] = 1
        with self.assertRaises(saveconv.SaveError): inv.execute_add(self.code, data, 364, 1)

    def test_real_candidate_entire_serializer_and_preservation(self):
        old = (ROOT / 'artifacts/so2-inventory/source-live-card-20260926.mcd').read_bytes()
        candidate = (ROOT / 'artifacts/so2-inventory/seraphic-garb-20-S15-candidate.mcd').read_bytes()
        _, order = next((f, o) for f, o in saveconv.chains(old) if f['name'].endswith('S15'))
        start = order[0]*8192
        block = old[start:start+8192]
        new, slot = inv.add_item(block, 364, 20, self.code)
        self.assertEqual(candidate, old[:start]+new+old[start+8192:])
        self.assertEqual(slot, 119)
        before, after = so2_fol.state(block), so2_fol.state(new)
        self.assertEqual([i for i, (a, b) in enumerate(zip(before, after)) if a != b], [0xc0e, 0xc0f])
        self.assertEqual(struct.unpack_from('<H', after, 0xb20+70*2)[0], 0x5181)
        self.assertTrue(saveconv.so2_valid(new))
        end = struct.unpack_from('<H', new, 0x21a)[0]
        self.assertEqual(run_codec(self.overlay, new[0x380:end]), after)
        self.assertEqual(run_codec(self.overlay, after, encode=True), new[0x380:end])
        self.assertEqual(serialize(self.code, self.overlay, after), new[0x380:end])
        serialize(self.code, self.overlay, after, load=True)
        bad = bytearray(block)
        bad[0x214] ^= 1
        with self.assertRaises(saveconv.SaveError): inv.add_item(bad, 364, 1, self.code)


if __name__ == '__main__':
    unittest.main()
