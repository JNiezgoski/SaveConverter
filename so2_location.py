"""Star Ocean 2 location viewer/namer/teleporter, backed by a small growing database.

Reads the confirmed area-entry fields from decoded save state (see
docs/SO2-MAP-LOCATION-CHECK.md): X/Y/Z entrance-relative position, facing,
area ID, and sub-index (distinct entrances into the same area, e.g. front
door vs. back door). This is entrance-point data (where you last warped in),
not a live free-roam coordinate - a save made right after entering an area
will read close to (0, 0, 0).

There is no complete area-ID -> name/coordinate table extractable from the
disc (see the investigation doc for what was tried and ruled out) - the
game itself only populates this data in RAM as areas are actually visited.

CAVEAT (2026-09-27, docs/SO2-MAP-TERRAIN-INVESTIGATION.md pass 3): decoded
area_id (0x1769) is NOT proven to be a unique location key - real saves show
the same area_id value with clearly different underlying scenes. Every
sighting now also records a "scene" value (decoded 0x1762) as extra context;
area_id remains the database's grouping key for now since re-keying on an
unconfirmed hypothesis would be premature, but don't treat two sightings
under the same area_id as definitely the same place until scene is checked
too.
So this tool builds a real database organically: every time you run `show`,
whatever area/sub-index that save is sitting at gets recorded - including
the full byte ranges confirmed necessary for a working cross-area teleport
(see the 2026-09-27 "cross-area teleport SOLVED" section of the
investigation doc) - and `name` lets you attach a real name once you know
it. Once an area has a recorded reference, `teleport` can send any other
save there, verified in-game to work correctly and to touch nothing else in
the save. Data lives in area_data.json next to this file.

Usage:
  python so2_location.py show [box]                      print + record every save's location (default box 1)
  python so2_location.py name <area_id> "<Name>"         record a name for an area ID
  python so2_location.py list                             print every named area so far
  python so2_location.py map                              dump every recorded area+sub-index, named or not
  python so2_location.py map-html [out.html]              write a small-multiples HTML visualization
  python so2_location.py teleport <box> <save> <area_id> --sub N --out <new card>
                                                            warp <save> (by name suffix) to a recorded area
"""
import argparse
import json
import os
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import saveconv as s
import so2_fol as fol

X, Y, Z = 0x1750, 0x1754, 0x1758
FACING = 0x1760
AREA_ID = 0x1769
SUB_INDEX = 0x176C
# 2026-09-27 terrain investigation, pass 3 (docs/SO2-MAP-TERRAIN-INVESTIGATION.md):
# AREA_ID is NOT a unique location key - real saves show the same AREA_ID value
# with clearly different underlying locations. The real scene/location selector
# traced through the terrain-loading code lives here instead. Recorded from now
# on as extra context on every sighting so real data can settle which field (or
# combination) actually distinguishes places - not yet used as a database key.
SCENE = 0x1762
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "area_data.json")

# Confirmed by a full-decoded-state diff of a real area transition (outside Linga
# -> inside Linga, 2026-09-27): copying exactly these ranges from a real save of
# the target area onto any other save produces a working in-game teleport, with
# zero unexpected changes anywhere else in the save. See the investigation doc's
# "cross-area teleport SOLVED" section for the evidence.
TELEPORT_RANGES = [
    (0x1750, 0x1765),   # position/facing block
    (0x1769, 0x176A),   # area id byte
    (0x1880, 0x1881),   # small counter-like byte, changes on real area entry
    (0x1A45, 0x1A46),   # byte next to the specialty-unlock bitmask, changes on entry
    (0x1B58, 0x1B88),   # 48-byte region, previously assumed unused; actually active
]


def load_db():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_db(db):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")


def read_location(decoded):
    x, y, z = struct.unpack_from("<iii", decoded, X)
    facing = struct.unpack_from("<h", decoded, FACING)[0]
    area_id = decoded[AREA_ID]
    sub_index = decoded[SUB_INDEX]
    scene = struct.unpack_from("<h", decoded, SCENE)[0]
    return {
        "x": x / 4096, "y": y / 4096, "z": z / 4096,
        "facing": facing, "area_id": area_id, "sub_index": sub_index,
        "scene": scene,
    }


def capture_teleport_ref(decoded):
    """Hex-encode exactly the bytes TELEPORT_RANGES covers, in order."""
    return "".join(decoded[a:b].hex() for a, b in TELEPORT_RANGES)


def apply_teleport_ref(decoded, ref_hex):
    """Write a captured reference back into a decoded buffer, in place."""
    ref = bytes.fromhex(ref_hex)
    pos = 0
    for a, b in TELEPORT_RANGES:
        n = b - a
        decoded[a:b] = ref[pos:pos + n]
        pos += n


def record_sighting(db, decoded, loc, save_name, save_title):
    """Upsert an area entry. Keeps the FIRST observed coordinates/reference for
    a given sub-index (they should be constant - it's a fixed entrance point),
    but always adds any new sub-index seen. Never touches an existing name."""
    area = db.setdefault(str(loc["area_id"]), {"name": None, "sightings": {}})
    key = str(loc["sub_index"])
    if key not in area["sightings"]:
        area["sightings"][key] = {
            "x": round(loc["x"], 2), "y": round(loc["y"], 2), "z": round(loc["z"], 2),
            "facing": loc["facing"], "scene": loc["scene"],
            "first_seen_save": save_name, "first_seen_title": save_title,
            "recorded": time.strftime("%Y-%m-%d %H:%M:%S"),
            "teleport_ref": capture_teleport_ref(decoded),
        }
        return True
    return False


def show(box):
    path = os.path.join(s.DEFAULT_CARD_DIR, f"{s.DEFAULT_GAME}_{box}.mcd")
    db = load_db()
    changed = False
    for sv in s.read_saves(path):
        decoded = fol.state(sv.data)
        loc = read_location(decoded)
        is_new = record_sighting(db, decoded, loc, sv.name, sv.title)
        changed = changed or is_new
        area = db[str(loc["area_id"])]
        name = area["name"] or "(unnamed)"
        print(f"{sv.name}  {sv.title}")
        print(f"  area {loc['area_id']} sub {loc['sub_index']} scene {loc['scene']}: {name}" + ("  [new sighting recorded]" if is_new else ""))
        print(f"  pos ({loc['x']:.2f}, {loc['y']:.2f}, {loc['z']:.2f})  facing {loc['facing']}")
    if changed:
        save_db(db)


def name_area(area_id, label):
    db = load_db()
    area = db.setdefault(str(area_id), {"name": None, "sightings": {}})
    area["name"] = label
    save_db(db)
    print(f"area {area_id} -> {label}")


def list_names():
    db = load_db()
    named = {aid: a for aid, a in db.items() if a.get("name")}
    if not named:
        print("no areas named yet")
        return
    for area_id in sorted(named, key=int):
        print(f"{area_id}: {named[area_id]['name']}")


def show_map():
    db = load_db()
    if not db:
        print("no areas recorded yet - run 'show' on a save first")
        return
    total_sub = sum(len(a["sightings"]) for a in db.values())
    print(f"{len(db)} area(s), {total_sub} entrance point(s) recorded (of 194 possible areas)\n")
    for area_id in sorted(db, key=int):
        area = db[area_id]
        label = area["name"] or "(unnamed)"
        print(f"area {area_id}: {label}")
        for sub_index in sorted(area["sightings"], key=int):
            sight = area["sightings"][sub_index]
            scene = sight.get("scene", "?")
            print(f"    sub {sub_index} scene {scene}: ({sight['x']}, {sight['y']}, {sight['z']}) facing {sight['facing']}"
                  f"  first seen: {sight['first_seen_title']}")


def teleport(box, save_suffix, area_id, sub_index, out_path):
    db = load_db()
    area = db.get(str(area_id))
    if not area or str(sub_index) not in area.get("sightings", {}):
        raise s.SaveError(f"no recorded reference for area {area_id} sub {sub_index} - "
                           f"'show' a save sitting there first")
    ref_hex = area["sightings"][str(sub_index)]["teleport_ref"]

    path = os.path.join(s.DEFAULT_CARD_DIR, f"{s.DEFAULT_GAME}_{box}.mcd")
    found = [sv for sv in s.read_saves(path) if sv.name.endswith(save_suffix)]
    if len(found) != 1:
        raise s.SaveError("save suffix must identify exactly one save")
    sv = found[0]

    decoded = bytearray(fol.state(sv.data))
    apply_teleport_ref(decoded, ref_hex)

    compressed = fol.encode(bytes(decoded))
    end = fol.STREAM + 2 + len(compressed)
    if end > s.BLOCK:
        raise s.SaveError("edited data does not fit one block")

    block = bytearray(sv.data)
    struct.pack_into("<H", block, fol.STREAM, len(compressed))
    block[fol.STREAM + 2:end] = compressed
    struct.pack_into("<H", block, 0x21A, end)
    s.so2_sign(block)

    if fol.state(bytes(block)) != bytes(decoded) or not s.so2_valid(bytes(block)):
        raise s.SaveError("round-trip/checksum verification failed")

    with open(out_path, "xb") as f:
        f.write(block)
    name = area["name"] or f"area {area_id}"
    print(f"{sv.name}: teleported to {name} (sub {sub_index}); wrote {out_path}")
    print("Verified round-trip + checksum. NOT loaded in-game by this run.")


def build_map_html(out_path):
    """Small-multiples overhead view: one mini scatter per area, showing that
    area's own entrance points relative to EACH OTHER only. Areas are not
    positioned relative to one another - each has its own local origin - so
    this deliberately does not draw one shared map (see docs/SO2-MAP-LOCATION-CHECK.md)."""
    db = load_db()
    cards = []
    for area_id in sorted(db, key=int):
        area = db[area_id]
        label = area["name"] or f"Area {area_id} (unnamed)"
        pts = area["sightings"]
        if not pts:
            continue
        xs = [p["x"] for p in pts.values()]
        zs = [p["z"] for p in pts.values()]
        pad = max(1.0, (max(xs) - min(xs)), (max(zs) - min(zs))) * 0.3 + 0.5
        x0, x1 = min(xs) - pad, max(xs) + pad
        z0, z1 = min(zs) - pad, max(zs) + pad
        w = h = 220
        def sx(x): return 16 + (x - x0) / (x1 - x0) * (w - 32)
        def sz(z): return 16 + (z - z0) / (z1 - z0) * (h - 32)
        dots = []
        for sub_index, p in sorted(pts.items(), key=lambda kv: int(kv[0])):
            cx, cz = sx(p["x"]), sz(p["z"])
            dots.append(
                f'<circle cx="{cx:.1f}" cy="{cz:.1f}" r="7" class="dot"/>'
                f'<circle cx="{cx:.1f}" cy="{cz:.1f}" r="7" class="dot-ring"/>'
                f'<text x="{cx:.1f}" y="{cz - 12:.1f}" class="dot-label">sub {sub_index}</text>'
                f'<title>sub {sub_index}: ({p["x"]}, {p["y"]}, {p["z"]}) facing {p["facing"]}\n'
                f'first seen: {p["first_seen_title"]}</title>'
            )
        cards.append(f'''
      <div class="card">
        <div class="card-title">{label}</div>
        <div class="card-sub">area {area_id} · {len(pts)} entrance{"s" if len(pts) != 1 else ""} recorded</div>
        <svg viewBox="0 0 {w} {h}" class="plot" role="img" aria-label="entrance layout for {label}">
          {''.join(dots)}
        </svg>
      </div>''')

    total_sub = sum(len(a["sightings"]) for a in db.values())
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SO2 Area Map</title>
<style>
  :root {{
    --surface-1: #fcfcfb; --page: #f9f9f7; --ink: #0b0b0b; --ink-2: #52514e; --ink-muted: #898781;
    --grid: #e1e0d9; --border: rgba(11,11,11,0.10); --accent: #2a78d6; --accent-ring: #fcfcfb;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      --surface-1: #1a1a19; --page: #0d0d0d; --ink: #ffffff; --ink-2: #c3c2b7; --ink-muted: #898781;
      --grid: #2c2c2a; --border: rgba(255,255,255,0.10); --accent: #3987e5; --accent-ring: #1a1a19;
    }}
  }}
  :root[data-theme="dark"] {{
    --surface-1: #1a1a19; --page: #0d0d0d; --ink: #ffffff; --ink-2: #c3c2b7; --ink-muted: #898781;
    --grid: #2c2c2a; --border: rgba(255,255,255,0.10); --accent: #3987e5; --accent-ring: #1a1a19;
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--page); color: var(--ink); font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }}
  .wrap {{ max-width: 1000px; margin: 0 auto; padding: 40px 20px 80px; }}
  h1 {{ font-size: 1.5rem; font-weight: 700; margin: 0 0 6px; }}
  .sub {{ color: var(--ink-2); font-size: 0.9rem; margin: 0 0 8px; max-width: 68ch; line-height: 1.5; }}
  .caveat {{ color: var(--ink-muted); font-size: 0.8rem; margin: 0 0 28px; max-width: 68ch; line-height: 1.5;
             padding: 10px 14px; background: var(--surface-1); border: 1px solid var(--border); border-radius: 8px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 16px; }}
  .card {{ background: var(--surface-1); border: 1px solid var(--border); border-radius: 12px; padding: 14px; }}
  .card-title {{ font-weight: 600; font-size: 0.95rem; margin-bottom: 2px; }}
  .card-sub {{ color: var(--ink-muted); font-size: 0.75rem; margin-bottom: 10px; }}
  .plot {{ width: 100%; height: auto; background:
    repeating-linear-gradient(0deg, transparent, transparent 21px, var(--grid) 21px, var(--grid) 22px),
    repeating-linear-gradient(90deg, transparent, transparent 21px, var(--grid) 21px, var(--grid) 22px);
    border-radius: 6px; }}
  .dot {{ fill: var(--accent); }}
  .dot-ring {{ fill: none; stroke: var(--accent-ring); stroke-width: 2; }}
  .dot-label {{ fill: var(--ink-2); font-size: 9px; text-anchor: middle; }}
  .empty {{ color: var(--ink-muted); font-size: 0.9rem; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Area Map</h1>
  <p class="sub">{len(db)} area{"s" if len(db) != 1 else ""} recorded, {total_sub} entrance point{"s" if total_sub != 1 else ""} total (of 194 possible areas). Generated by <code>so2_location.py map-html</code> from area_data.json.</p>
  <p class="caveat">Each card is its own local coordinate space - an area's entrances are positioned correctly <b>relative to each other</b>, but different areas are NOT positioned relative to one another (no shared world origin was found in the save data). This is why there's no single combined map.</p>
  <div class="grid">
    {"".join(cards) if cards else '<p class="empty">No areas recorded yet - run \'python so2_location.py show\' on a save first.</p>'}
  </div>
</div>
</body>
</html>
'''
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"wrote {out_path}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sh = sub.add_parser("show", help="print + record every save's location")
    sh.add_argument("box", nargs="?", type=int, default=1)
    nm = sub.add_parser("name", help="record a name for an area ID")
    nm.add_argument("area_id", type=int)
    nm.add_argument("label")
    sub.add_parser("list", help="print every named area so far")
    sub.add_parser("map", help="dump every recorded area+sub-index, named or not")
    mh = sub.add_parser("map-html", help="write a small-multiples HTML visualization")
    mh.add_argument("out", nargs="?", default="area_map.html")
    tp = sub.add_parser("teleport", help="warp a save to a recorded area (writes a NEW card file)")
    tp.add_argument("box", type=int)
    tp.add_argument("save", help="save name suffix, e.g. S05")
    tp.add_argument("area_id", type=int)
    tp.add_argument("--sub", type=int, default=1, help="sub-index/entrance (default 1)")
    tp.add_argument("--out", required=True, help="new card file to write (never overwrites the source)")
    args = p.parse_args()

    if args.cmd == "show":
        show(args.box)
    elif args.cmd == "name":
        name_area(args.area_id, args.label)
    elif args.cmd == "list":
        list_names()
    elif args.cmd == "map":
        show_map()
    elif args.cmd == "map-html":
        build_map_html(args.out)
    elif args.cmd == "teleport":
        teleport(args.box, args.save, args.area_id, args.sub, args.out)


if __name__ == "__main__":
    main()
