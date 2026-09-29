#!/usr/bin/env python3
"""PS1 memory card / save converter.

Card formats (read + write unless noted):
  raw   .mcd .mcr .mc .mem .bin .srm .ps1   131072-byte card image
  gme   .gme                                DexDrive, 0xF40-byte header + card
  vgs   .vgs                                Virtual Game Station, 0x40 header + card
  vmp   .vmp                                PSP virtual card - READ ONLY (write needs Sony signing keys)
Single saves:
  mcs   .mcs                                128-byte directory frame + save blocks

Commands:
  convert   card -> card in another format (default)
  list      show the saves on a card
  extract   card -> one .mcs per save
  import    .mcs saves -> a card (created if it does not exist)

  voice     Star Ocean 2 Voice Collection audit, merger & unlocker
  so2-edit  Star Ocean 2 save editor (SP, Talents, Skills, Fol)

No arguments opens a small window instead.
"""
import argparse, hashlib, os, shutil, struct, subprocess, sys, time, unicodedata
from pathlib import Path

CARD = 131072
BLOCK = 8192
FRAME = 128
GME_HDR = 0xF40
VGS_HDR = 0x40
RAW_EXT = {"mcd", "mcr", "mc", "mem", "bin", "srm", "ps1"}


class SaveError(Exception):
    pass


# ---------------------------------------------------------------- detection
def load_card(path):
    """Return (format_name, 131072-byte card). Detects by content, not extension."""
    b = open(path, "rb").read()
    if b[:11] == b"123-456-STD":
        off, fmt = GME_HDR, "gme"
    elif b[:4] == b"VgsM":
        off, fmt = VGS_HDR, "vgs"
    elif b[:4] == b"\x00PMV":
        hdr = struct.unpack_from("<I", b, 4)[0]
        off, fmt = (hdr if 0x40 <= hdr <= 0x400 else 0x80), "vmp"
    elif b[:2] == b"MC":
        off, fmt = 0, "raw"
    elif len(b) > GME_HDR + 2 and b[GME_HDR:GME_HDR + 2] == b"MC":
        off, fmt = GME_HDR, "gme"  # GME written by a tool that left the signature blank
    else:
        raise SaveError("not a recognised PS1 memory card (no MC header)")
    body = b[off:off + CARD]
    if body[:2] != b"MC":
        raise SaveError("card data does not start with an MC header")
    # single-block/partial exports are legal: pad with zeros to a full card
    return fmt, body.ljust(CARD, b"\0")


def frame_checksum(fr):
    x = 0
    for v in fr[:127]:
        x ^= v
    return x


# ------------------------------------------------------------------ writers
def to_gme(card):
    h = bytearray(GME_HDR)
    h[0:11] = b"123-456-STD"
    h[0x12] = 0x01
    h[0x14] = 0x01
    h[0x15] = 0x4D
    for i in range(1, 16):                       # mirror the directory state bytes
        h[0x15 + i] = card[i * FRAME]
    for i in range(15):
        h[0x26 + i] = 0xFF
    return bytes(h) + card


def to_vgs(card):
    h = bytearray(VGS_HDR)
    h[0:4] = b"VgsM"
    h[4] = h[8] = h[12] = 1
    return bytes(h) + card


def encode(card, fmt):
    if fmt == "raw":
        return card
    if fmt == "gme":
        return to_gme(card)
    if fmt == "vgs":
        return to_vgs(card)
    if fmt == "vmp":
        raise SaveError("VMP output is not supported (PSP requires a signed header)")
    raise SaveError(f"unknown format {fmt}")


def target_for(name):
    """'mcd' -> ('raw','.mcd'), 'gme' -> ('gme','.gme')."""
    n = name.lower().lstrip(".")
    if n in RAW_EXT or n == "raw":
        return "raw", ".mcd" if n == "raw" else "." + n
    if n in ("gme", "vgs", "vmp"):
        return n, "." + n
    raise SaveError(f"unknown target format '{name}'")


# ---------------------------------------------------------------- directory
def directory(card):
    """List slots 1..15 as dicts."""
    out = []
    for slot in range(1, 16):
        fr = card[slot * FRAME:(slot + 1) * FRAME]
        state = fr[0]
        size = struct.unpack_from("<I", fr, 4)[0]
        nxt = struct.unpack_from("<H", fr, 8)[0]
        name = fr[10:31].split(b"\0")[0].decode("ascii", "replace")
        out.append(dict(slot=slot, state=state, size=size, next=nxt, name=name, frame=bytes(fr)))
    return out


def chains(card):
    """Yield (first_slot_dict, [slot numbers in order]) for every save."""
    d = {e["slot"]: e for e in directory(card)}
    for e in d.values():
        if e["state"] == 0x51:
            order, cur, seen = [e["slot"]], e, {e["slot"]}
            while cur["next"] != 0xFFFF and cur["next"] + 1 in d and cur["next"] + 1 not in seen:
                nxt = cur["next"] + 1            # stored link is 0-based
                order.append(nxt)
                seen.add(nxt)
                cur = d[nxt]
            yield e, order


def save_title(card, slot):
    """Readable save title (Shift-JIS, full-width -> ASCII), e.g. 'SO2 02 23:07 Claude LV255'."""
    raw = card[slot * BLOCK + 4: slot * BLOCK + 68].split(b"\0")[0]
    try:
        return unicodedata.normalize("NFKC", raw.decode("shift_jis")).strip()
    except UnicodeDecodeError:
        return raw.decode("ascii", "replace").strip()


def do_list(path):
    fmt, card = load_card(path)
    print(f"{path}  [{fmt}]")
    n = 0
    for first, order in chains(card):
        n += 1
        print(f"  slot {first['slot']:>2}  {first['name']:<22} {len(order)} block(s)  {save_title(card, first['slot'])}")
    used = sum(1 for e in directory(card) if e["state"] in (0x51, 0x52, 0x53))
    print(f"  {n} save(s), {used}/15 blocks used")


def do_extract(path, outdir):
    fmt, card = load_card(path)
    os.makedirs(outdir, exist_ok=True)
    written = []
    for first, order in chains(card):
        fr = bytearray(first["frame"])
        struct.pack_into("<H", fr, 8, 0xFFFF)
        fr[127] = frame_checksum(fr)
        data = b"".join(card[s * BLOCK:(s + 1) * BLOCK] for s in order)
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in first["name"])
        p = os.path.join(outdir, f"{safe}.mcs")
        open(p, "wb").write(bytes(fr) + data)
        written.append(p)
        print("  wrote", p)
    return written


def do_import(mcs_paths, card_path, fmt=None):
    if os.path.exists(card_path):
        cfmt, card = load_card(card_path)
        fmt = fmt or cfmt
    else:
        card = bytes(format_card())
        fmt = fmt or target_for(os.path.splitext(card_path)[1])[0]
    card = bytearray(card)
    for p in mcs_paths:
        for sv in read_saves(p):
            if has_name(bytes(card), sv.name):
                raise SaveError(f"{os.path.basename(p)}: '{sv.name}' already exists on {os.path.basename(card_path)}")
            print(f"  imported {os.path.basename(p)} -> slot(s) {place_save(card, sv)}")
    open(card_path, "wb").write(encode(fix_card_checksums(bytes(card)), fmt))
    print("  wrote", card_path)


# ------------------------------------------------------ save management
class Save:
    """One save (1..n blocks) lifted off a card or an .mcs file."""
    def __init__(self, name, frame, data, src="", title=""):
        self.name, self.frame, self.data, self.src, self.title = name, bytes(frame), bytes(data), src, title

    @property
    def blocks(self):
        return len(self.data) // BLOCK

    @property
    def key(self):
        return hashlib.md5(self.data).hexdigest()


def format_card():
    """A freshly formatted, empty card (bad-sector table + header mirror included)."""
    c = bytearray(CARD)
    c[0:2] = b"MC"
    for i in range(1, 16):
        c[i * FRAME] = 0xA0
        c[i * FRAME + 8:i * FRAME + 10] = b"\xFF\xFF"
    for i in range(16, 36):
        c[i * FRAME:i * FRAME + 4] = b"\xFF\xFF\xFF\xFF"
        c[i * FRAME + 8:i * FRAME + 10] = b"\xFF\xFF"
    return bytearray(fix_card_checksums(bytes(c)))


def fix_card_checksums(card):
    card = bytearray(card)
    for i in range(36):
        card[i * FRAME + 127] = frame_checksum(card[i * FRAME:(i + 1) * FRAME])
    card[63 * FRAME:64 * FRAME] = card[0:FRAME]      # write-test frame mirrors the header frame
    return bytes(card)


def read_saves(path):
    b = open(path, "rb").read()
    if b[:1] == b"Q" and len(b) >= FRAME + BLOCK and (len(b) - FRAME) % BLOCK == 0:     # .mcs single save
        name = b[10:31].split(b"\0")[0].decode("ascii", "replace")
        return [Save(name, b[:FRAME], b[FRAME:], path)]
    fmt, card = load_card(path)
    out = []
    for first, order in chains(card):
        data = b"".join(card[s * BLOCK:(s + 1) * BLOCK] for s in order)
        out.append(Save(first["name"], first["frame"], data, path, save_title(card, first["slot"])))
    return out


def so2_sign(d):
    """Recompute Star Ocean 2's two header checksums in a save block (bytearray, edited in place).
    Zero A (u32 @0x210), B (u32 @0x214), and the marker (u16 @0x218).
    B = sum(d[:C]), C = u16 @0x21A (end of data).
    A = sum(d[0x200:0x280]) including the newly computed B.
    Restore the marker afterward. See docs/SO2-CHECKSUM-INVESTIGATION.md."""
    c = struct.unpack_from("<H", d, 0x21A)[0]
    marker = d[0x218:0x21A]
    d[0x210:0x21A] = b"\0" * 10
    struct.pack_into("<I", d, 0x214, sum(d[:c]))
    struct.pack_into("<I", d, 0x210, sum(d[0x200:0x280]))
    d[0x218:0x21A] = marker
    return d


def so2_valid(data):
    """True if a save block's stored checksums match the rules above."""
    return bytes(so2_sign(bytearray(data))) == bytes(data)


def card_saves(card):
    return [(first, order) for first, order in chains(card)]


def free_slots(card):
    return [e["slot"] for e in directory(card) if e["state"] == 0xA0]


def has_name(card, name):
    return any(first["name"] == name for first, _ in chains(card))


def place_save(card, save):
    """Write a save into the first free block(s) of a bytearray card. Returns the slots used."""
    free = free_slots(card)
    n = save.blocks
    if len(free) < n:
        raise SaveError(f"not enough free blocks ({n} needed, {len(free)} free)")
    use = free[:n]
    for i, slot in enumerate(use):
        fr = bytearray(FRAME)
        if i == 0:
            fr[:] = save.frame
            fr[0] = 0x51
            struct.pack_into("<I", fr, 4, BLOCK * n)
        else:
            fr[0] = 0x53 if i == n - 1 else 0x52
        struct.pack_into("<H", fr, 8, (use[i + 1] - 1) if i < n - 1 else 0xFFFF)
        fr[127] = frame_checksum(fr)
        card[slot * FRAME:(slot + 1) * FRAME] = fr
        card[slot * BLOCK:(slot + 1) * BLOCK] = save.data[i * BLOCK:(i + 1) * BLOCK]
    return use


def delete_save(card, first_slot):
    """Free every block of the save that starts at first_slot."""
    for first, order in chains(bytes(card)):
        if first["slot"] == first_slot:
            for slot in order:
                fr = bytearray(FRAME)
                fr[0] = 0xA0
                fr[8:10] = b"\xFF\xFF"
                fr[127] = frame_checksum(fr)
                card[slot * FRAME:(slot + 1) * FRAME] = fr
                card[slot * BLOCK:(slot + 1) * BLOCK] = bytes(BLOCK)
            return
    raise SaveError("no save starts in that slot")


def rename_save(card, first_slot, new_name):
    if len(new_name) > 20:
        raise SaveError("save names are at most 20 characters")
    for first, order in chains(bytes(card)):
        if first["slot"] == first_slot:
            if new_name != first["name"] and has_name(bytes(card), new_name):
                raise SaveError(f"'{new_name}' already exists on this card")
            fr = bytearray(card[first_slot * FRAME:(first_slot + 1) * FRAME])
            fr[10:31] = new_name.encode("ascii").ljust(21, b"\0")
            fr[127] = frame_checksum(fr)
            card[first_slot * FRAME:(first_slot + 1) * FRAME] = fr
            return
    raise SaveError("no save starts in that slot")


def suggest_names(card, name):
    """Names like the given one but with the trailing slot number free on this card."""
    stem = name[:-2] if name[-2:].isdigit() else name
    used = {f["name"] for f, _ in chains(bytes(card))}
    return [f"{stem}{n:02d}" for n in range(1, 16) if f"{stem}{n:02d}" not in used]


def combine(inputs, outdir, base, ext=".mcd", fmt="raw"):
    """Merge every save from every input into as few cards as needed (no name clashes,
    exact duplicates dropped). Returns (list of card paths, report lines)."""
    saves, seen, report = [], {}, []
    for p in inputs:
        for sv in read_saves(p):
            if sv.key in seen:
                report.append(f"skipped duplicate: {sv.name} '{sv.title}' from {os.path.basename(p)} (same as {seen[sv.key]})")
                continue
            seen[sv.key] = os.path.basename(p)
            saves.append(sv)
    cards = []                                            # (bytearray, [placed])
    for sv in saves:
        for card, placed in cards:
            if not has_name(bytes(card), sv.name) and len(free_slots(bytes(card))) >= sv.blocks:
                place_save(card, sv); placed.append(sv); break
        else:
            card = format_card(); place_save(card, sv); cards.append((card, [sv]))
    os.makedirs(outdir, exist_ok=True)
    paths = []
    for i, (card, placed) in enumerate(cards, 1):
        path = os.path.join(outdir, f"{base}_{i}{ext}")
        open(path, "wb").write(encode(fix_card_checksums(bytes(card)), fmt))
        paths.append(path)
        for sv in placed:
            report.append(f"card {i}: {sv.name[-7:]}  {sv.title or '(untitled)'}  <- {os.path.basename(sv.src)}")
    return paths, report


def duckstation_running():
    try:
        # Filter server-side (Windows only returns matching rows) instead of dumping every
        # process and scanning the text here - much cheaper for a check that runs on a timer.
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq duckstation*", "/FO", "CSV", "/NH"],
                              capture_output=True, text=True).stdout.lower()
        return "duckstation" in out
    except OSError:
        return False


def install_cards(card_paths, card_dir, game, force=False):
    """Copy cards in as '<game>_1.mcd', '<game>_2.mcd' (existing files are backed up first)."""
    if duckstation_running() and not force:
        raise SaveError("DuckStation is running - close it first (it would overwrite the cards on exit)")
    os.makedirs(card_dir, exist_ok=True)
    done = []
    for i, src in enumerate(card_paths, 1):
        fmt, card = load_card(src)
        dest = os.path.join(card_dir, f"{game}_{i}.mcd")
        if os.path.exists(dest):
            bak = os.path.join(card_dir, "cards", "_backup")
            os.makedirs(bak, exist_ok=True)
            shutil.copy2(dest, os.path.join(bak, f"{game}_{i}.{time.strftime('%Y%m%d-%H%M%S')}.mcd"))
        open(dest, "wb").write(fix_card_checksums(card))
        done.append(dest)
    return done


# -------------------------------------------------------------- convert
def convert_file(src, fmt, ext, outdir=None, overwrite=False):
    sfmt, card = load_card(src)
    base = os.path.splitext(os.path.basename(src))[0]
    dest = os.path.join(outdir or os.path.dirname(os.path.abspath(src)), base + ext)
    if os.path.abspath(dest) == os.path.abspath(src) and not overwrite:
        raise SaveError("output would overwrite the source file (use --out)")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "wb").write(encode(card, fmt))
    return sfmt, dest


def expand(paths):
    out = []
    for p in paths:
        if os.path.isdir(p):
            for f in sorted(os.listdir(p)):
                fp = os.path.join(p, f)
                if os.path.isfile(fp) and os.path.splitext(f)[1].lower() in (
                        ".gme", ".vgs", ".vmp", ".mcd", ".mcr", ".mc", ".mem", ".bin", ".srm", ".ps1"):
                    out.append(fp)
        else:
            out.append(p)
    return out


DEFAULT_CARD_DIR = r"C:\CodeTesting\StarOcean2\SaveGames"
DEFAULT_GAME = "Star Ocean - The Second Story (USA)"
PLAY_BAT = r"C:\CodeTesting\StarOcean2\tools\play_so2.bat"


def backup_file(path, card_dir=DEFAULT_CARD_DIR):
    """Copy an existing card aside (cards\\_backup) before it is overwritten. Returns the backup path."""
    if not os.path.exists(path):
        return None
    bak = os.path.join(card_dir, "cards", "_backup")
    os.makedirs(bak, exist_ok=True)
    base, ext = os.path.splitext(os.path.basename(path))
    dest = os.path.join(bak, f"{base}.{time.strftime('%Y%m%d-%H%M%S')}{ext}")
    shutil.copy2(path, dest)
    return dest


def apply_pending(tmp, dest):
    """Wait for DuckStation to exit, then replace dest with the prepared card in tmp (dest is backed up)."""
    while duckstation_running():
        time.sleep(2)
    time.sleep(3)
    backup_file(dest)
    shutil.copyfile(tmp, dest)
    os.remove(tmp)


def do_so2_voice(card_path, slot=None, unlock=None, merge=False, out=None):
    from tools.so2_voice_collection import analyze_card, patch_slot_voice_collection, merge_memory_card_voices
    card_p = Path(card_path)
    out_p = Path(out) if out else None
    if merge:
        merge_memory_card_voices(card_p, out_p)
    elif unlock is not None:
        target_slot = slot or 1
        patch_slot_voice_collection(card_p, target_slot, percent=unlock, out_path=out_p)
    else:
        card_report = analyze_card(card_p)
        print("=" * 65)
        print(f"STAR OCEAN 2 - VOICE COLLECTION AUDIT: {card_p.name}")
        print("=" * 65)
        for s, report in sorted(card_report.items()):
            print(f"\n--- Save Slot {s} --- [Total: {report['total_unlocked']}/{report['max_voices']} ({report['percent']}%) ]")
            for c in report["characters"]:
                print(f"  {c['character']:10s}: {c['unlocked']:3d} / {c['max']:3d} ({c['percent']:5.1f}%)")


def do_so2_edit(card_path, slot=1, fol=None, sp=None, talents=False, skills=False, out=None):
    import scripts.so2_fol as so2_codec
    card_p = Path(card_path)
    cfmt, card_bytes = load_card(card_p)
    card = bytearray(card_bytes)

    base = slot * BLOCK
    block = bytearray(card[base : base + BLOCK])
    if block[0x200:0x20A] != b"STAR OCEAN":
        raise SaveError(f"Slot {slot} is not a valid Star Ocean 2 save")

    dec = bytearray(so2_codec.state(block))

    # Apply Fol
    if fol is not None:
        if not 0 <= fol <= so2_codec.MAX_FOL:
            raise SaveError(f"Fol must be between 0 and {so2_codec.MAX_FOL}")
        struct.pack_into("<I", dec, so2_codec.FOL, fol)
        print(f"  Slot {slot}: Fol set to {fol:,}")

    # Apply Party Member modifications (Secondary array: 0x4A0 + slot * 0xD0)
    if sp is not None or talents:
        for c_slot in range(8):
            sec_base = 0x4A0 + c_slot * 0xD0
            name = dec[sec_base + 0x24 : sec_base + 0x2C].split(b"\x00")[0].decode("ascii", "replace")
            if name:
                if sp is not None:
                    clamped_sp = max(0, min(sp, 999))
                    struct.pack_into("<H", dec, sec_base + 0x1A, clamped_sp)
                if talents:
                    struct.pack_into("<H", dec, sec_base + 0x20, 0x03FF)
                print(f"  Party Member '{name}': SP={struct.unpack_from('<H', dec, sec_base + 0x1A)[0]}, Talents=0x{struct.unpack_from('<H', dec, sec_base + 0x20)[0]:04X}")

    # Apply Skill Shop Tiers
    if skills:
        dec[0x1A3F] |= 0xF0
        dec[0x1A40] = 0xFF
        print(f"  Unlocked all 12 Skill Shop Tiers party-wide (Knowledge, Sensibility, Technique, Combat)")

    # Re-encode and sign
    compressed = so2_codec.encode(dec)
    end = so2_codec.STREAM + 2 + len(compressed)
    if end > len(block):
        raise SaveError("edited data exceeds one block")

    result = bytearray(block)
    struct.pack_into("<H", result, so2_codec.STREAM, len(compressed))
    result[so2_codec.STREAM + 2 : end] = compressed
    struct.pack_into("<H", result, 0x21A, end)
    so2_sign(result)

    if not so2_valid(result):
        raise SaveError("signature verification failed after edit")

    card[base : base + BLOCK] = result
    out_card = encode(fix_card_checksums(bytes(card)), cfmt)
    dest_path = Path(out) if out else card_p
    dest_path.write_bytes(out_card)
    print(f"Successfully saved edited card to {dest_path}")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    if len(sys.argv) == 1:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts"))
        import savemanager
        return savemanager.run()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    cb = sub.add_parser("combine", help="merge saves from many cards/.mcs files into as few cards as needed")
    cb.add_argument("files", nargs="+")
    cb.add_argument("--out", required=True, help="folder for the resulting cards")
    cb.add_argument("--base", default="combined", help="output name; cards are <base>_1, <base>_2, ...")
    cb.add_argument("--to", default="mcd")
    cb.add_argument("--install", action="store_true", help="also install the first two cards for DuckStation")
    cb.add_argument("--dir", default=DEFAULT_CARD_DIR, help="DuckStation card folder (for --install)")
    cb.add_argument("--game", default=DEFAULT_GAME, help="game card name (for --install)")
    ap_ = sub.add_parser("apply-pending", help="(internal) after DuckStation exits, replace a card with a prepared file")
    ap_.add_argument("tmp")
    ap_.add_argument("dest")
    ins = sub.add_parser("install", help="install cards as DuckStation card 1 (and 2)")
    ins.add_argument("cards", nargs="+", help="one or two card files")
    ins.add_argument("--dir", default=DEFAULT_CARD_DIR)
    ins.add_argument("--game", default=DEFAULT_GAME)
    ins.add_argument("--force", action="store_true", help="install even if DuckStation is running")
    c = sub.add_parser("convert", help="convert card files to another card format")
    c.add_argument("files", nargs="+")
    c.add_argument("--to", default="mcd", help="mcd|mcr|mc|mem|bin|srm|gme|vgs (default mcd)")
    c.add_argument("--out", help="output folder (default: next to each source)")
    l = sub.add_parser("list", help="show saves on cards")
    l.add_argument("files", nargs="+")
    e = sub.add_parser("extract", help="write each save on a card to a .mcs file")
    e.add_argument("file")
    e.add_argument("--out", default=".")
    i = sub.add_parser("import", help="import .mcs saves into a card")
    i.add_argument("card")
    i.add_argument("saves", nargs="+")

    vc = sub.add_parser("voice", help="Star Ocean 2 Voice Collection audit, merger & unlocker")
    vc.add_argument("card", help="memory card file")
    vc.add_argument("--slot", type=int, default=None, help="target slot (1..15)")
    vc.add_argument("--unlock", type=float, default=None, help="unlock voices up to percent (e.g. 100)")
    vc.add_argument("--merge", action="store_true", help="merge voice collection across all slots on card")
    vc.add_argument("--out", help="output card path")

    ed = sub.add_parser("so2-edit", help="Star Ocean 2 save editor (SP, Talents, Skills, Fol)")
    ed.add_argument("card", help="memory card file")
    ed.add_argument("--slot", type=int, default=1, help="target save slot (1..15, default 1)")
    ed.add_argument("--fol", type=int, default=None, help="set Fol (0..999,999,999)")
    ed.add_argument("--sp", type=int, default=None, help="set SP for all active party members (0..999)")
    ed.add_argument("--talents", action="store_true", help="unlock all 10 talents for all active party members")
    ed.add_argument("--skills", action="store_true", help="unlock all 12 Skill Shop tiers party-wide")
    ed.add_argument("--out", help="output card path (default overwrites target slot safely)")

    if sys.argv[1] not in ("convert", "list", "extract", "import", "combine", "install", "apply-pending", "voice", "so2-edit", "-h", "--help"):
        sys.argv.insert(1, "convert")            # bare file arguments = convert
    a = ap.parse_args()
    try:
        if a.cmd == "voice":
            do_so2_voice(a.card, a.slot, a.unlock, a.merge, a.out)
            return 0
        if a.cmd == "so2-edit":
            do_so2_edit(a.card, a.slot, a.fol, a.sp, a.talents, a.skills, a.out)
            return 0
        if a.cmd == "apply-pending":
            apply_pending(a.tmp, a.dest)
            return 0
        if a.cmd == "combine":
            fmt, ext = target_for(a.to)
            paths, report = combine(expand(a.files), a.out, a.base, ext, fmt)
            print("\n".join(report))
            print(f"{len(paths)} card(s) written to {a.out}")
            if a.install:
                for d in install_cards(paths[:2], a.dir, a.game):
                    print("installed", d)
            return 0
        if a.cmd == "install":
            for d in install_cards(a.cards[:2], a.dir, a.game, a.force):
                print("installed", d)
            return 0
        if a.cmd == "convert":
            fmt, ext = target_for(a.to)
            bad = 0
            for f in expand(a.files):
                try:
                    sfmt, dest = convert_file(f, fmt, ext, a.out)
                    print(f"OK   {f} [{sfmt}] -> {dest}")
                except (SaveError, OSError) as ex:
                    bad += 1
                    print(f"FAIL {f}: {ex}")
            return 1 if bad else 0
        if a.cmd == "list":
            for f in expand(a.files):
                do_list(f)
        elif a.cmd == "extract":
            do_extract(a.file, a.out)
        elif a.cmd == "import":
            do_import(a.saves, a.card)
        else:
            ap.print_help()
    except SaveError as ex:
        print("error:", ex)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
