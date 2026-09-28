"""Star Ocean 2 save anatomy: label EVERY byte of one 8,192-byte save block and write a map to the desktop.

Status codes:  S standard PS1 memory-card format   V verified in the game (writes proven)   R decoded/read, write not proven
               U unknown - not understood            N noise/padding (ignored by the game)
Usage:  python scripts/so2_anatomy.py [box 1|2]     (default box 1 of Slot 1)   -> C:\\Users\\Josh\\Desktop\\StarOcean2-Save-Anatomy-Map.txt
Regenerate it whenever we learn something: move the byte range from U to V/R in the LAYERS code below."""
import glob, os, re, struct, sys

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)
sys.path.insert(0, os.path.dirname(_here))
import saveconv as s
import so2_refill_sp as r

D = s.DEFAULT_CARD_DIR
OUT = r"C:\Users\Josh\Desktop\StarOcean2-Save-Anatomy-Map.txt"
R = lambda d, o: struct.unpack_from("<H", d, o)[0]


def paint(lab, a, b, name, st):
    for i in range(max(a, 0), min(b, len(lab))):
        lab[i] = (name, st)


def annotate(d):
    C = R(d, 0x21A)
    lab = [("unknown", "U")] * len(d)
    # ---- PS1 card header and standard parts ----
    paint(lab, 0x000, 0x002, "PS1 save magic 'SC'", "S"); paint(lab, 0x002, 0x003, "icon display flag", "S"); paint(lab, 0x003, 0x004, "block count", "S")
    paint(lab, 0x004, 0x044, "title (Shift-JIS, shown in memory-card menu)", "S"); paint(lab, 0x044, 0x060, "reserved (zeros)", "S")
    paint(lab, 0x060, 0x080, "icon palette (16 colours)", "S"); paint(lab, 0x080, 0x200, "icon frames (3 x 128 bytes)", "S")
    # ---- game header ----
    paint(lab, 0x200, 0x210, "signature 'STAR OCEAN 03/01' (NOT the box number)", "R")
    paint(lab, 0x210, 0x212, "checksum A (sum 0x206..0x280)", "V"); paint(lab, 0x214, 0x218, "checksum B (sum 4..C)", "V")
    paint(lab, 0x21A, 0x21C, "C = end-of-data offset", "V"); paint(lab, 0x21C, 0x21E, "playtime minutes", "V"); paint(lab, 0x220, 0x222, "battle count", "V")
    for i in range(8):
        paint(lab, 0x234 + 4*i, 0x236 + 4*i, f"party list slot {i+1}: character ID", "V"); paint(lab, 0x236 + 4*i, 0x238 + 4*i, f"party list slot {i+1}: level (load screen)", "V")
    paint(lab, 0x382, 0x384, "button: confirm (0x40 = X)", "V"); paint(lab, 0x384, 0x386, "button: cancel (0x20 = Circle)", "V")
    paint(lab, 0x386, 0x388, "button: menu (0x10 = Triangle)", "V"); paint(lab, 0x388, 0x38A, "button: 4th (0x80 = Square)", "V")
    paint(lab, 0x392, 0x394, "playtime minutes (copy)", "V"); paint(lab, 0x397, 0x399, "battle count (copy)", "V"); paint(lab, 0x39C, 0x39F, "Fol (money), 3 bytes LE", "V")
    # ---- party records ----
    qs = [q for q in range(0x4f0, 0x900) if R(d, q) == R(d, q+5) == R(d, q+10) and 20 <= R(d, q) <= 9999 and d[q+2:q+5] == b"\0\0\0" and d[q+7:q+10] == b"\0\0\0"]
    qs = [q for q in qs if not any(0 < q - o < 5 for o in qs)][:8]
    for k, q in enumerate(qs, 1):
        sh = 0 if d[q+12:q+15] == b"\0\0\0" else -1
        hdr = next((q - kk for kk in range(0x0a, 0x22) if d[q-kk] in (1, 3, 5, 9) and 1 <= d[q-kk+1] <= 12 and d[q-kk+2:q-kk+5] == b"\0\0\0"), None)
        if hdr: paint(lab, hdr, hdr + 1, f"record {k}: class byte", "R"); paint(lab, hdr + 1, hdr + 2, f"record {k}: character ID", "V"); paint(lab, hdr + 2, hdr + 5, f"record {k}: 00 00 00", "R")
        paint(lab, q - 4, q, f"record {k}: EXP (u32)", "R")
        paint(lab, q, q + 15, f"record {k}: HP x3 (cur/max/base)", "V"); paint(lab, q + 15 + sh, q + 21 + sh, f"record {k}: MP x3", "V")
        paint(lab, q + 21 + sh, q + 25 + sh, f"record {k}: level x2", "V")
        for j, nm in enumerate(("STR", "CON", "AGL", "DEX", "INT")): paint(lab, q + 25 + sh + 6*j, q + 31 + sh + 6*j, f"record {k}: {nm} x3", "V")
        paint(lab, q + 55 + sh, q + 59 + sh, f"record {k}: unknown pair", "U"); paint(lab, q + 59 + sh, q + 61 + sh, f"record {k}: GUTS", "R")
    # ---- name entries ----
    for k, n in enumerate(r.NAMES, 1):
        p = r.find(d, n)
        if not p: continue
        c1 = d[p - 1] == 1
        if c1: paint(lab, p - 9, p - 4, f"{n.decode()}: SP block [SP][00 00][marker]", "V"); paint(lab, p - 4, p - 2, f"{n.decode()}: talent mask u16", "V"); paint(lab, p - 2, p, f"{n.decode()}: trailer (00 01)", "R")
        else: paint(lab, p - 11, p - 5, f"{n.decode()}: SP block [pfx][SP][00 00][marker]", "V"); paint(lab, p - 5, p - 3, f"{n.decode()}: talent mask u16", "V"); paint(lab, p - 3, p, f"{n.decode()}: trailer (00 00 00)", "R")
        paint(lab, p, p + len(n), f"{n.decode()}: NAME (ASCII)", "R"); paint(lab, p + len(n), p + len(n) + 3, f"{n.decode()}: 00 00 + pad byte (20-len)", "R")
        a = p + len(n) + 3; sk = None
        for i in range(a, a + 80):
            j = i
            while j < len(d) and d[j] <= 10: j += 1
            if j - i >= 46: sk = i; break
        if sk:
            paint(lab, a, sk - 3, f"{n.decode()}: flag run (33-flag zero-compressed array)", "U"); paint(lab, sk - 3, sk, f"{n.decode()}: '00 00 tag' (run + tag = 33)", "R")
            paint(lab, sk, sk + 46, f"{n.decode()}: 46 skill levels (all = 10)", "V")
        cand = [j for j in range(p - 64, p - 16) if R(d, j) == R(d, j+2) and R(d, j+6) == R(d, j+8) and 0 < R(d, j) <= 999 and 0 < R(d, j+6) <= 999
                and R(d, j+4) >= R(d, j) and R(d, j+10) >= R(d, j+6) and R(d, j+4) <= 999 and R(d, j+10) <= 999 and R(d, j+4) != 0]
        if len(cand) == 1: paint(lab, cand[0], cand[0] + 6, f"{n.decode()}: LUC (base,base,effective)", "R"); paint(lab, cand[0] + 6, cand[0] + 12, f"{n.decode()}: STM (base,base,effective)", "R")
    # ---- default name table + tail ----
    t = d.find(b"Crawd\x00\x00", 0xf00)
    if t > 0:
        e = d.find(b"Chisato\x00\x00", t); e = e + 10 if e > 0 else t + 100
        paint(lab, t, e, "default character name table (12 names)", "R")
    paint(lab, C, len(d), "noise after C (uninitialised buffer, ignored by the game)", "N")
    return lab, C


def runs(lab):
    out, a = [], 0
    for i in range(1, len(lab) + 1):
        if i == len(lab) or lab[i] != lab[a]: out.append((a, i, lab[a])); a = i
    return out


def main():
    box = "S0" + (sys.argv[1] if len(sys.argv) > 1 else "1")
    path = os.path.join(D, f"{s.DEFAULT_GAME}_1.mcd")
    sv = [x for x in s.read_saves(path) if x.name.endswith(box)][0]
    d = sv.data
    others = [x.data for x in s.read_saves(path) if x.name != sv.name]
    for f in sorted(glob.glob(os.path.join(D, "cards", "_backup", "card1-before-all12-*.mcd")))[:1]:
        others += [x.data for x in s.read_saves(f)]
    lab, C = annotate(d)
    L = []
    L.append(f"STAR OCEAN 2 - SAVE ANATOMY MAP (every byte of one 8,192-byte block)   source: Slot 1 {box}  {sv.title}   C = {hex(C)}")
    L.append("Status:  S standard PS1 format | V verified in game (writes proven) | R decoded/read, write not proven | U UNKNOWN | N noise")
    L.append("Generated by C:\\CodeTesting\\SaveConverter\\so2_anatomy.py - rerun after each new finding.\n")
    tot = {}
    for a, b, (nm, st) in runs(lab): tot[st] = tot.get(st, 0) + (b - a)
    L.append("BYTES BY STATUS: " + "   ".join(f"{k} = {v} ({100*v//len(d)}%)" for k, v in sorted(tot.items())))
    dat = C - 0x200; kn = sum(1 for i in range(0x200, C) if lab[i][1] in "VR"); unk = sum(1 for i in range(0x200, C) if lab[i][1] == "U")
    L.append(f"GAME-DATA AREA 0x200..{hex(C)} ({dat} bytes): decoded {kn} ({100*kn//dat}%), UNKNOWN {unk} ({100*unk//dat}%)\n")
    L.append("REGION SUMMARY (game-data area)")
    for label, a, b in (("0x200-0x233 game header", 0x200, 0x234), ("0x234-0x253 party list", 0x234, 0x254), ("0x254-0x37F unmapped block", 0x254, 0x380),
                        ("0x380-0x4FF options / Fol / state", 0x380, 0x500), ("0x500-0x82F party records", 0x500, 0x830), ("0x830-0xEFF character name entries", 0x830, 0xF00),
                        (f"0xF00-{hex(C)} name table / tail", 0xF00, C)):
        b = min(b, C); ln = b - a; k = sum(1 for i in range(a, b) if lab[i][1] in "VR"); u = sum(1 for i in range(a, b) if lab[i][1] == "U")
        dyn = sum(1 for i in range(a, b) if any(i < len(o) and o[i] != d[i] for o in others))
        L.append(f"   {label:40s} {ln:5d} bytes | decoded {100*k//max(ln,1):3d}% | unknown {100*u//max(ln,1):3d}% | bytes that change between our {len(others)+1} saves: {dyn}")
    L.append("\nEVERY RUN OF BYTES (offset range, size, status, what it is):")
    for a, b, (nm, st) in runs(lab):
        L.append(f"  {a:#06x}-{b-1:#06x} {b-a:5d}  [{st}]  {nm}")
    L.append("\nUNKNOWN RUNS - HEX WITH CHANGE MARKERS (line 2 of each pair: '^' = this byte differs in at least one other save of ours, '.' = identical in all)")
    for a, b, (nm, st) in runs(lab):
        if st != "U" or b - a < 2 or a >= C: continue
        L.append(f"\n  {a:#06x}-{b-1:#06x} ({b-a} bytes)  {nm}")
        for i in range(a, b, 32):
            seg = d[i:min(i + 32, b)]
            L.append(f"    {i:#06x}  " + " ".join(f"{v:02x}" for v in seg))
            L.append("            " + " ".join(" ^" if any(j < len(o) and o[j] != d[j] for o in others) else " ." for j in range(i, i + len(seg))))
    with open(OUT, "w", encoding="utf-8") as f: f.write("\n".join(L) + "\n")
    print("\n".join(L[:14])); print("... written to", OUT, f"({len(L)} lines)")


if __name__ == "__main__":
    main()
