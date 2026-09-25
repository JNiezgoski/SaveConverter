import struct
import unittest

from saveconv import so2_sign, so2_valid


class ChecksumTests(unittest.TestCase):
    def block(self):
        d = bytearray(8192)
        d[:4] = b"SC\x13\x01"
        d[0x200:0x210] = b"STAR OCEAN 03/01\0"
        struct.pack_into("<HH", d, 0x218, 0x5555, 0x400)
        d[0x280] = 3  # Early-save boundary byte; late saves often have 255.
        d[0x39A] = 40
        return d

    def test_known_byte_sum(self):
        d = self.block()
        # Header signature sums to 979; PS1 prefix sums to 170.
        # B = 170 + 979 + C's byte sum (4) + 3 + 40 = 1196.
        # A = 979 + 4 + B's byte sum (0xAC + 4) = 1159.
        so2_sign(d)
        self.assertEqual(struct.unpack_from("<II", d, 0x210), (1159, 1196))
        self.assertEqual(d[0x218:0x21A], b"UU")
        self.assertTrue(so2_valid(d))

    def test_boundary_is_excluded_from_a_but_included_in_b(self):
        d = so2_sign(self.block())
        a, b = struct.unpack_from("<II", d, 0x210)
        d[0x280] += 1
        so2_sign(d)
        self.assertEqual(struct.unpack_from("<II", d, 0x210), (a + 1, b + 1))

    def test_ps1_prefix_is_included_in_b(self):
        d = so2_sign(self.block())
        a, b = struct.unpack_from("<II", d, 0x210)
        d[2] += 1
        so2_sign(d)
        self.assertEqual(struct.unpack_from("<II", d, 0x210), (a + 1, b + 1))

    def test_a_is_a_full_word_and_trailing_bytes_are_ignored(self):
        d = so2_sign(self.block())
        expected = bytes(d)
        d[0x212:0x214] = b"\x01\x02"
        self.assertFalse(so2_valid(d))
        so2_sign(d)
        self.assertEqual(bytes(d), expected)
        d[0x400] = 255
        self.assertTrue(so2_valid(d))

    def test_fol_change_requires_new_a_even_outside_header(self):
        d = so2_sign(self.block())
        a, b = struct.unpack_from("<II", d, 0x210)
        d[0x39A] += 1
        struct.pack_into("<I", d, 0x214, b + 1)
        self.assertFalse(so2_valid(d))
        so2_sign(d)
        self.assertEqual(struct.unpack_from("<II", d, 0x210), (a + 1, b + 1))


if __name__ == "__main__":
    unittest.main()
