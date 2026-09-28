"""Star Ocean 2 equipment viewer/editor.

Equipment = 7 u16 item IDs stored right after each character's STM triple (weapon, armor, shield, helmet, greaves, accessory 1, accessory 2).
Item ID = CodeBreaker list code - 0x5000 (see C:\\CodeTesting\\StarOcean2\\item_ids.txt).

Usage:
  python scripts/so2_equip.py show   [box]                       list every character's equipment (default box 1)
  python scripts/so2_equip.py set    box Character slot "Item"   e.g. so2_equip.py set 3 Claude weapon "Eternal Sphere"   (DuckStation must be closed)
Slots: weapon armor shield helmet greaves acc1 acc2. Character names are the strings stored in the save (Claude is "Crawd")."""
import os, re, shutil, struct, sys, time

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)
sys.path.insert(0, os.path.dirname(_here))
import saveconv as s
import so2_refill_sp as r

SLOTS = ["weapon", "armor", "shield", "helmet", "greaves", "acc1", "acc2"]
R = lambda d, o: struct.unpack_from("<H", d, o)[0]


def item_table():
    names = {}
    for line in open(r"C:\CodeTesting\StarOcean2\item_ids.txt", encoding="utf-8"):
        m = re.match(r"^([0-9A-F]{4}) (.+)$", line.strip())
        if m:
            names[int(m.group(1), 16) - 0x5000] = re.sub(r"\s*\[.*\]$", "", re.sub(r"\s*\((Sword|Armor|Shield|Boot|Helment|Knuckles|Staff|Dual-Sword|Hand|Whip|Book|Gun|Kaleidoscope|weapon|strong)\)", "", m.group(2)))
    return names


def sp_block_start(d, p):
    """Leftmost byte of the SP block for the entry ending at name-offset p (see so2_refill_sp.py for the form rules).
    Equipment always sits immediately before this point, regardless of which SP form (zero/small/large) is in use."""
    c1 = d[p - 1] == 1
    if c1:
        if d[p - 2:p] == b"\x00\x01" and d[p - 7] == 0 and d[p - 6] == 0 and d[p - 5] in (2, 3):
            return p - 9                                     # class-1, small or large SP
        if d[p - 2:p] == b"\x00\x01" and d[p - 7] == 0 and d[p - 6] == 0:
            return p - 7                                     # class-1, zero SP (no number stored)
    else:
        if d[p - 3:p] == b"\0\0\0" and d[p - 8] == 0 and d[p - 7] == 0 and d[p - 6] in (2, 3):
            return p - 10                                    # class-0, small or large SP
        if d[p - 3:p] == b"\0\0\0" and d[p - 8] == 0 and d[p - 7] == 0:
            return p - 8                                     # class-0, zero SP
    return None


def equip_slots(d, name):
    """Returns (offset, slot_names) for one character. Full entries store 7 slots ending right at the SP block:
    [weapon, armor, shield, helmet, greaves, acc1, acc2]. Entries missing accessory 2 store only 6 slots, ordered
    [acc1, weapon, armor, shield, helmet, greaves], immediately followed by the SP block's own leading "00 00 <prefix>".
    That "00 00 <byte>" is NOT a special equipment marker - it's just the start of the SP block itself (see
    so2_refill_sp.py's format), so the byte is whatever that character's personal SP prefix happens to be (0x02 for
    most, but 0x05 for Noel in some saves, 0x0A for Chisato, etc). The old code only recognised literal 0x02, which
    silently misclassified any character whose prefix differs as a full 7-slot entry - the actual cause of Noel
    reading correctly in one save and not another (his prefix isn't 0x02 everywhere)."""
    p = r.find(d, name)
    if p is None:
        return None, None
    sp0 = sp_block_start(d, p)
    if sp0 is None:
        return None, None
    if d[sp0 - 3:sp0 - 1] == b"\0\0":
        return sp0 - 15, ["acc1", "weapon", "armor", "shield", "helmet", "greaves"]
    return sp0 - 14, ["weapon", "armor", "shield", "helmet", "greaves", "acc1", "acc2"]


def equip_offset(d, name):
    o, _ = equip_slots(d, name)
    return o


def show(box):
    path = os.path.join(s.DEFAULT_CARD_DIR, f"{s.DEFAULT_GAME}_1.mcd")
    names = item_table()
    sv = [x for x in s.read_saves(path) if x.name.endswith(f"S0{box}")][0]
    d = sv.data
    print(f"Slot 1 box {box}: {sv.title}")
    for n in r.NAMES:
        o, slots = equip_slots(d, n)
        if o is None:
            print(f"   {n.decode():8s} (equipment block not located)"); continue
        ids = [R(d, o + 2*k) for k in range(len(slots))]
        print(f"   {n.decode():8s} " + " | ".join(f"{sl}: {names.get(i, '#' + str(i))}" for sl, i in zip(slots, ids)))


def set_item(box, who, slot, item):
    path = os.path.join(s.DEFAULT_CARD_DIR, f"{s.DEFAULT_GAME}_1.mcd")
    if s.duckstation_running():
        sys.exit("DuckStation is running - close it first.")
    names = item_table()
    ids = [i for i, nm in names.items() if nm.lower() == item.lower()]
    if len(ids) != 1:
        sys.exit(f"item {item!r} matches {len(ids)} entries in item_ids.txt")
    sv = [x for x in s.read_saves(path) if x.name.endswith(f"S0{box}")][0]
    d = bytearray(sv.data)
    o = equip_offset(d, who.encode())
    if o is None:
        sys.exit("equipment block not located for that character")
    k = SLOTS.index(slot)
    print(f"{who} {slot}: {names.get(R(d, o + 2*k))} -> {names[ids[0]]}  (id {ids[0]})")
    struct.pack_into("<H", d, o + 2*k, ids[0])
    s.so2_sign(d)
    assert s.so2_valid(bytes(d))
    bak = os.path.join(s.DEFAULT_CARD_DIR, "cards", "_backup", f"card1-before-equip-{time.strftime('%Y%m%d-%H%M%S')}.mcd")
    shutil.copy2(path, bak)
    raw = bytearray(s.load_card(path)[1])
    slot_no = [f["slot"] for f, _ in s.chains(bytes(raw)) if f["name"] == sv.name][0]
    s.delete_save(raw, slot_no)
    s.place_save(raw, s.Save(sv.name, sv.frame, bytes(d), path, ""))
    open(path, "wb").write(s.fix_card_checksums(bytes(raw)))
    print("written. backup:", bak)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] == "show":
        show(a[1] if len(a) > 1 else "1")
    elif a[0] == "set" and len(a) == 5:
        set_item(a[1], a[2], a[3], a[4])
    else:
        print(__doc__)
