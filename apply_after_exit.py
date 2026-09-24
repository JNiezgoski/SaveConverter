"""One-off job: wait for DuckStation to exit, then
   1) delete the Shaf 15:33 and 28:12 saves from live card 1 (if present),
   2) move every save from live card 2 onto card 1, leaving card 2 empty.
Cards are backed up first; a log is written next to the backups."""
import os, shutil, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import saveconv as s

DIR = s.DEFAULT_CARD_DIR
P1 = os.path.join(DIR, f"{s.DEFAULT_GAME}_1.mcd")
P2 = os.path.join(DIR, f"{s.DEFAULT_GAME}_2.mcd")
BAK = os.path.join(DIR, "cards", "_backup")
os.makedirs(BAK, exist_ok=True)
LOG = os.path.join(BAK, "apply_after_exit.log")


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")


log("waiting for DuckStation to exit...")
while s.duckstation_running():
    time.sleep(2)
time.sleep(3)                      # let it finish flushing its cards
stamp = time.strftime("%Y%m%d-%H%M%S")
for p in (P1, P2):
    shutil.copy2(p, os.path.join(BAK, os.path.basename(p).replace(".mcd", f".before-move-{stamp}.mcd")))
log("backed up both cards")

c1 = bytearray(s.load_card(P1)[1])
c2 = bytearray(s.load_card(P2)[1])

for first, order in s.chains(bytes(c1)):                       # 1) drop the two duplicate Shaf saves
    t = s.save_title(bytes(c1), first["slot"])
    if "15:33" in t or "28:12" in t:
        s.delete_save(c1, first["slot"])
        log(f"deleted from card 1: {first['name']} '{t}'")

moved = []                                                     # 2) move card 2 -> card 1
for first, order in s.chains(bytes(c2)):
    data = b"".join(bytes(c2)[x * s.BLOCK:(x + 1) * s.BLOCK] for x in order)
    sv = s.Save(first["name"], first["frame"], data, P2, s.save_title(bytes(c2), first["slot"]))
    if s.has_name(bytes(c1), sv.name):
        log(f"SKIPPED (name already on card 1): {sv.name} '{sv.title}' - left on card 2")
        continue
    try:
        s.place_save(c1, sv)
    except s.SaveError as e:
        log(f"SKIPPED ({e}): {sv.name} '{sv.title}'")
        continue
    moved.append((first["slot"], sv))
    log(f"moved to card 1: {sv.name} '{sv.title}'")
for slot, sv in moved:
    s.delete_save(c2, slot)

open(P1, "wb").write(s.fix_card_checksums(bytes(c1)))
open(P2, "wb").write(s.fix_card_checksums(bytes(c2)))
log("done. card 1 now: " + "; ".join(f"{f['name'][-3:]} {s.save_title(bytes(c1), f['slot'])}" for f, _ in s.chains(bytes(c1))))
log("card 2 now: " + ("; ".join(f"{f['name'][-3:]} {s.save_title(bytes(c2), f['slot'])}" for f, _ in s.chains(bytes(c2))) or "empty"))
