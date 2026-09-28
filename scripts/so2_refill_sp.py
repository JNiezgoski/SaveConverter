"""Refill Star Ocean 2 skill points (SP) to 999 for EVERY character in the chosen saves.

Only SP is written, then both checksums are recomputed. Backs up the card first and refuses to run while DuckStation is open
(DuckStation rewrites its memory cards on exit).

Usage:  python scripts/so2_refill_sp.py [card 1|2] [box ...]      e.g.  python scripts/so2_refill_sp.py 1 1 2      (default: card 1, boxes 1 2)

SP is stored in a block just before each character's talent mask (verified against game-written saves; see the desktop notes):
      [SP bytes][00 00][marker]      SP 0: no SP bytes, marker = 04/08/0B (character specific)     SP 1..255: 1 byte, marker 03
                                     SP >= 256: 2 bytes (lo hi), marker 02  -> one byte longer than the small form
  The game switches form by itself as SP crosses 0 / 256. This tool converts any form to the large form (999) by inserting bytes,
  shifting the rest of the block and growing C (0x21A). Entries it cannot recognise are left alone and reported."""
import os, re, shutil, struct, sys, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import saveconv as s

SP_MAX = 999
NAMES = [b"Crawd", b"Rena", b"Ashton", b"Dias", b"Opera", b"Ernest", b"Celine", b"Leon", b"Noel", b"Precis", b"Chisato", b"Bowman"]
ZERO_PREFIX = {0x08: 0x02, 0x0B: 0x05}          # class-0 zero-form marker -> prefix byte the game writes (Leon 08, Noel 0B)
R = lambda d, o: struct.unpack_from("<H", d, o)[0]
LARGE = lambda pfx: bytes([pfx, SP_MAX & 0xFF, SP_MAX >> 8, 0x00, 0x00, 0x02])


def find(d, n):
    m = re.search(re.escape(n) + rb"\x00\x00([\x00-\x20])", bytes(d[0x780:0xf00]))
    return 0x780 + m.start() if m else None


def grow(d, at, remove, insert):
    c = R(d, 0x21A)
    d[:] = (bytes(d[:at]) + insert + bytes(d[at + remove:]))[:8192]
    struct.pack_into("<H", d, 0x21A, c + len(insert) - remove)


def set_sp(d, n):
    p = find(d, n)
    if p is None:
        return None
    c1 = d[p - 1] == 1
    z = d[p - 3:p] == b"\0\0\0"
    if c1 and R(d, p - 9) >= 256 and d[p - 7] == 0 and d[p - 6] == 0 and d[p - 5] == 2:                # class-1 large
        struct.pack_into("<H", d, p - 9, SP_MAX); return "set"
    if c1 and d[p - 7] == 0 and d[p - 6] == 0 and d[p - 5] == 3 and d[p - 2:p] == b"\x00\x01":         # class-1 small
        grow(d, p - 9, 5, LARGE(d[p - 9])); return "converted from small (+1)"
    if c1 and d[p - 7] == 0 and d[p - 6] == 0 and d[p - 5] not in (2, 3) and d[p - 2:p] == b"\x00\x01":  # class-1 zero form [00 00][marker]
        return "SKIPPED zero form - get the game to write a small block first (level up once); direct conversion broke a save"
    if not c1 and z and d[p - 8] == 0 and d[p - 7] == 0 and d[p - 6] == 2:                             # class-0 large
        struct.pack_into("<H", d, p - 10, SP_MAX); return "set"
    if not c1 and z and d[p - 8] == 0 and d[p - 7] == 0 and d[p - 6] == 3:                             # class-0 small
        grow(d, p - 10, 5, LARGE(d[p - 10])); return "converted from small (+1)"
    if not c1 and z and d[p - 8] == 0 and d[p - 7] == 0 and d[p - 6] in ZERO_PREFIX:                   # class-0 zero form
        # proven in game (Noel 0B -> 05.., Leon 08 -> 02..): the game replaces the zero-form MARKER byte with <prefix><SP><00 00><marker>
        grow(d, p - 6, 1, LARGE(ZERO_PREFIX[d[p - 6]])); return "converted from zero (+5, marker replaced)"
    return "LEFT ALONE (layout not recognised): " + d[p - 16:p].hex(" ")


def refill(d):
    out = []
    for n in NAMES:
        r = set_sp(d, n)
        if r:
            out.append((n.decode(), r))
    s.so2_sign(d)
    assert s.so2_valid(bytes(d))
    return out


def main():
    args = sys.argv[1:]
    card = int(args[0]) if args else 1
    boxes = [f"S0{b}" for b in (args[1:] or ["1", "2"])]
    path = os.path.join(s.DEFAULT_CARD_DIR, f"{s.DEFAULT_GAME}_{card}.mcd")
    if s.duckstation_running():
        sys.exit("DuckStation is running - close it first (Yes on Confirm Exit, untick Save State For Resume).")
    bak = os.path.join(s.DEFAULT_CARD_DIR, "cards", "_backup", f"card{card}-before-refill-sp-{time.strftime('%Y%m%d-%H%M%S')}.mcd")
    shutil.copy2(path, bak)
    raw = bytearray(s.load_card(path)[1])
    for sv in s.read_saves(path):
        if sv.name[-3:] not in boxes:
            continue
        d = bytearray(sv.data)
        res = refill(d)
        slot = [f["slot"] for f, _ in s.chains(bytes(raw)) if f["name"] == sv.name][0]
        s.delete_save(raw, slot)
        s.place_save(raw, s.Save(sv.name, sv.frame, bytes(d), path, ""))
        print(f"{sv.name[-3:]} {sv.title}")
        for n, r in res:
            print(f"    {n:8s} {r}")
    open(path, "wb").write(s.fix_card_checksums(bytes(raw)))
    print("Backup:", bak)


if __name__ == "__main__":
    main()
