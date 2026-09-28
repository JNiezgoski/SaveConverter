"""PS1 Save Manager - two memory cards side by side.

Open any card (.mcd/.mcr/.gme/.vgs/.vmp/...), copy/move/rename/delete saves between them,
import/export single saves (.mcs), combine many cards into as few as needed, convert formats,
and install two cards as DuckStation's card 1 / card 2.
"""
import os
import struct
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import saveconv as s

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = ImageTk = None

CARD_TYPES = [("Memory cards / saves", "*.mcd *.mcr *.mc *.mem *.bin *.srm *.ps1 *.gme *.vgs *.vmp *.mcs"),
              ("All files", "*.*")]
CARD_EXTS = (".mcd", ".mcr", ".mc", ".mem", ".srm", ".gme", ".vgs", ".vmp")


def save_icon(card, slot, scale=2):
    """First animation frame of a save's icon as a Tk image (or None)."""
    if Image is None:
        return None
    blk = bytes(card)[slot * s.BLOCK:(slot + 1) * s.BLOCK]
    if blk[:2] != b"SC" or not 0x11 <= blk[2] <= 0x13:
        return None
    pal = struct.unpack("<16H", blk[0x60:0x80])
    px = blk[0x80:0x100]
    im = Image.new("RGBA", (16, 16))
    for i in range(256):
        v = (px[i // 2] >> 4) if i & 1 else (px[i // 2] & 0x0F)
        c = pal[v]
        if c == 0:
            im.putpixel((i % 16, i // 16), (0, 0, 0, 0))
        else:
            r, g, b = c & 31, (c >> 5) & 31, (c >> 10) & 31
            im.putpixel((i % 16, i // 16), (r * 255 // 31, g * 255 // 31, b * 255 // 31, 255))
    return ImageTk.PhotoImage(im.resize((16 * scale, 16 * scale), Image.NEAREST))


def library_cards(app):
    """(label, path) for every card found in the usual places, with a one-line summary of its saves."""
    d = app.dir.get()
    places = [d, os.path.join(d, "cards", "combined"), os.path.join(d, "cards", "spares")]
    out, seen = [], set()
    for folder in places:
        if not os.path.isdir(folder):
            continue
        for f in sorted(os.listdir(folder)):
            p = os.path.join(folder, f)
            if os.path.splitext(f)[1].lower() not in CARD_EXTS or p in seen or not os.path.isfile(p):
                continue
            seen.add(p)
            try:
                summary = ", ".join(sv.title.replace("SO2 ", "") for sv in s.read_saves(p)) or "empty"
            except (s.SaveError, OSError):
                continue
            tag = os.path.basename(folder) if folder != d else "live"
            out.append((f"[{tag}] {f}  -  {summary}", p))
    return out


class Panel:
    def __init__(self, app, parent, title):
        self.app, self.name = app, title
        self.card, self.path, self.fmt, self.dirty = None, None, "raw", False
        self.history, self.icons = [], []
        self.frame = ttk.LabelFrame(parent, text=title)
        self.pathvar = tk.StringVar(value="(no card loaded)")
        ttk.Label(self.frame, textvariable=self.pathvar, wraplength=400, foreground="#555").pack(anchor="w", padx=6, pady=(4, 2))
        bar = ttk.Frame(self.frame)
        bar.pack(fill="x", padx=6)
        mb = ttk.Menubutton(bar, text="Library ▾")
        mb.menu = tk.Menu(mb, tearoff=0, postcommand=lambda: self.build_library(mb.menu))
        mb["menu"] = mb.menu
        mb.pack(side="left", padx=(0, 4))
        for text, cmd in (("Open...", self.open), ("New blank", self.new), ("Save", self.save), ("Save as...", self.save_as), ("Undo", self.undo)):
            ttk.Button(bar, text=text, command=cmd).pack(side="left", padx=(0, 4))
        cols = ("name", "title", "blk")
        self.tree = ttk.Treeview(self.frame, columns=cols, show="tree headings", selectmode="extended", height=9)
        self.tree.heading("#0", text="")
        self.tree.column("#0", width=48, stretch=False, anchor="center")
        for c, w, t in (("name", 150, "Save name"), ("title", 200, "Title"), ("blk", 40, "Blk")):
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="w" if c != "blk" else "center")
        self.tree.pack(fill="both", expand=True, padx=6, pady=6)
        self.status = tk.StringVar()
        ttk.Label(self.frame, textvariable=self.status).pack(anchor="w", padx=6)
        bar2 = ttk.Frame(self.frame)
        bar2.pack(fill="x", padx=6, pady=6)
        for text, cmd in (("Delete", self.delete), ("Rename...", self.rename), ("Export .mcs", self.export), ("Import...", self.import_)):
            ttk.Button(bar2, text=text, command=cmd).pack(side="left", padx=(0, 4))

    # ---- undo
    def snapshot(self):
        if self.card is not None:
            self.history.append((bytes(self.card), self.dirty))
            del self.history[:-30]

    def undo(self):
        if not self.history:
            return messagebox.showinfo("Undo", "Nothing to undo.")
        data, dirty = self.history.pop()
        self.card, self.dirty = bytearray(data), dirty
        self.refresh()

    # ---- state
    def load(self, path):
        fmt, card = s.load_card(path)
        self.card, self.path, self.fmt, self.dirty = bytearray(card), path, fmt, False
        self.history.clear()
        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        self.icons = []
        if self.card is None:
            self.pathvar.set("(no card loaded)")
            self.status.set("")
            return
        b = bytes(self.card)
        for first, order in s.chains(b):
            img = save_icon(b, first["slot"])
            kw = {}
            if img is not None:
                self.icons.append(img)
                kw["image"] = img
            self.tree.insert("", "end", iid=str(first["slot"]), **kw,
                             values=(first["name"], s.save_title(b, first["slot"]), len(order)))
        free = len(s.free_slots(b))
        mark = "  *unsaved changes*" if self.dirty else ""
        self.pathvar.set(f"{self.path or '(new card)'}  [{self.fmt}]{mark}")
        self.status.set(f"{len(self.tree.get_children())} save(s), {free} of 15 blocks free")

    def need_card(self):
        if self.card is None:
            messagebox.showinfo("PS1 Save Manager", f"Open or create a card in {self.name} first.")
            return False
        return True

    def selected(self):
        return [int(i) for i in self.tree.selection()]

    # ---- card file actions
    def build_library(self, menu):
        menu.delete(0, "end")
        found = library_cards(self.app)
        if not found:
            menu.add_command(label="(no cards found)", state="disabled")
        for label, path in found:
            menu.add_command(label=label, command=lambda p=path: self.try_load(p))

    def open(self):
        p = filedialog.askopenfilename(title=f"Open card for {self.name}", filetypes=CARD_TYPES, initialdir=self.app.dir.get())
        if p:
            self.try_load(p)

    def try_load(self, p):
        if self.dirty and not messagebox.askyesno("Unsaved changes", f"{self.name} has unsaved changes. Discard them?"):
            return
        try:
            self.load(p)
        except (s.SaveError, OSError) as e:
            messagebox.showerror("Open card", f"{os.path.basename(p)}: {e}")

    def new(self):
        self.snapshot()
        self.card, self.path, self.fmt, self.dirty = s.format_card(), None, "raw", True
        self.refresh()

    def save(self):
        if not self.need_card():
            return
        if not self.path:
            return self.save_as()
        self.write(self.path, self.fmt)

    def save_as(self):
        if not self.need_card():
            return
        p = filedialog.asksaveasfilename(title="Save card as", defaultextension=".mcd", initialdir=self.app.dir.get(),
                                         filetypes=[("Raw card (.mcd)", "*.mcd"), ("Raw card (.mcr)", "*.mcr"),
                                                    ("DexDrive (.gme)", "*.gme"), ("VGS (.vgs)", "*.vgs")])
        if p:
            self.write(p, s.target_for(os.path.splitext(p)[1])[0])

    def write(self, path, fmt):
        try:
            data = s.encode(s.fix_card_checksums(bytes(self.card)), fmt)
        except s.SaveError as e:
            return messagebox.showerror("Save card", str(e))
        live = os.path.dirname(os.path.abspath(path)).lower() == os.path.abspath(self.app.dir.get()).lower()
        if live and s.duckstation_running():
            ans = messagebox.askyesnocancel(
                "DuckStation is open",
                "DuckStation keeps its cards in memory and would overwrite this one when it closes.\n\n"
                "Yes = save it automatically the moment DuckStation closes\nNo = cancel")
            if not ans:
                return
            tmp = os.path.join(tempfile.gettempdir(), "ps1sm_" + os.path.basename(path))
            open(tmp, "wb").write(data)
            exe = sys.executable.replace("python.exe", "pythonw.exe")
            subprocess.Popen([exe, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "saveconv.py"), "apply-pending", tmp, path])
            self.dirty = False
            self.refresh()
            return messagebox.showinfo("Queued", "Saved changes are waiting. They will be written (with a backup) as soon as DuckStation closes.")
        try:
            s.backup_file(path, self.app.dir.get())
            open(path, "wb").write(data)
        except (s.SaveError, OSError) as e:
            return messagebox.showerror("Save card", str(e))
        self.path, self.fmt, self.dirty = path, fmt, False
        self.refresh()

    # ---- save actions
    def delete(self):
        sel = self.selected()
        if not self.need_card() or not sel:
            return
        if messagebox.askyesno("Delete", f"Delete {len(sel)} save(s) from {self.name}? (Nothing is written until you press Save; Undo works.)"):
            self.snapshot()
            for slot in sel:
                s.delete_save(self.card, slot)
            self.dirty = True
            self.refresh()

    def rename(self):
        sel = self.selected()
        if not self.need_card() or len(sel) != 1:
            return messagebox.showinfo("Rename", "Select exactly one save.")
        cur = self.tree.item(str(sel[0]), "values")[0]
        free = s.suggest_names(bytes(self.card), cur)
        new = simpledialog.askstring("Rename save", f"New save name (free slot numbers on this card: {', '.join(n[-2:] for n in free) or 'none'}):",
                                     initialvalue=cur, parent=self.frame)
        if new and new != cur:
            self.snapshot()
            try:
                s.rename_save(self.card, sel[0], new.strip())
            except s.SaveError as e:
                self.history.pop()
                return messagebox.showerror("Rename", str(e))
            self.dirty = True
            self.refresh()

    def export(self):
        sel = self.selected()
        if not self.need_card() or not sel:
            return
        d = filedialog.askdirectory(title="Export .mcs files to")
        if not d:
            return
        n = 0
        for sv in self.saves(sel):
            fr = bytearray(sv.frame)
            struct.pack_into("<H", fr, 8, 0xFFFF)
            fr[127] = s.frame_checksum(fr)
            safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in sv.name)
            open(os.path.join(d, f"{safe}.mcs"), "wb").write(bytes(fr) + sv.data)
            n += 1
        messagebox.showinfo("Export", f"Exported {n} save(s) to {d}")

    def import_(self):
        if not self.need_card():
            return
        files = filedialog.askopenfilenames(title="Import saves (.mcs, or any card)", filetypes=CARD_TYPES, initialdir=self.app.dir.get())
        if not files:
            return
        self.snapshot()
        for p in files:
            try:
                for sv in s.read_saves(p):
                    self.put(sv)
            except (s.SaveError, OSError) as e:
                messagebox.showerror("Import", f"{os.path.basename(p)}: {e}")
                break
        self.refresh()

    def saves(self, slots):
        b = bytes(self.card)
        out = []
        for first, order in s.chains(b):
            if first["slot"] in slots:
                data = b"".join(b[x * s.BLOCK:(x + 1) * s.BLOCK] for x in order)
                out.append(s.Save(first["name"], first["frame"], data, self.path or "", s.save_title(b, first["slot"])))
        return out

    def put(self, sv):
        """Place a save on this card, resolving a name clash interactively. Returns False if cancelled."""
        b = bytes(self.card)
        if s.has_name(b, sv.name):
            free = s.suggest_names(b, sv.name)
            if not free:
                messagebox.showerror("Name clash", f"{self.name} already has '{sv.name}' and no free slot numbers.")
                return False
            new = simpledialog.askstring(
                "Name already exists",
                f"{self.name} already has '{sv.name}'.\nThe game finds saves by name, so this copy needs its own.\n"
                f"Free names: {', '.join(n[-3:] for n in free)}\nSave as:",
                initialvalue=free[0], parent=self.frame)
            if not new:
                return False
            fr = bytearray(sv.frame)
            fr[10:31] = new.strip().encode("ascii").ljust(21, b"\0")
            sv = s.Save(new.strip(), bytes(fr), sv.data, sv.src, sv.title)
        try:
            s.place_save(self.card, sv)
        except s.SaveError as e:
            messagebox.showerror("Copy", str(e))
            return False
        self.dirty = True
        return True


class App:
    def __init__(self, root):
        self.root = root
        root.title("PS1 Save Manager")
        root.geometry("1240x600")
        top = ttk.Frame(root)
        top.pack(fill="x", padx=8, pady=6)
        ttk.Label(top, text="DuckStation card folder:").pack(side="left")
        self.dir = tk.StringVar(value=s.DEFAULT_CARD_DIR)
        ttk.Entry(top, textvariable=self.dir, width=40).pack(side="left", padx=4)
        ttk.Label(top, text="Game:").pack(side="left", padx=(8, 0))
        self.game = tk.StringVar(value=s.DEFAULT_GAME)
        ttk.Entry(top, textvariable=self.game, width=32).pack(side="left", padx=4)
        self.ds_state = tk.StringVar()
        ttk.Label(top, textvariable=self.ds_state, foreground="#b45309").pack(side="right")
        top2 = ttk.Frame(root)
        top2.pack(fill="x", padx=8)
        for text, cmd in (("Load live cards", self.load_live), ("Combine files...", self.combine),
                          ("Convert files...", self.convert), ("Install A + B", self.install),
                          ("Install + Play", self.play)):
            ttk.Button(top2, text=text, command=cmd).pack(side="left", padx=(0, 6))
        body = ttk.Frame(root)
        body.pack(fill="both", expand=True, padx=8, pady=8)
        self.a, self.b = Panel(self, body, "Card A  (DuckStation slot 1)"), Panel(self, body, "Card B  (DuckStation slot 2)")
        self.a.frame.pack(side="left", fill="both", expand=True)
        mid = ttk.Frame(body)
        mid.pack(side="left", padx=8)
        for text, cmd in (("Copy  →", lambda: self.xfer(self.a, self.b, False)), ("←  Copy", lambda: self.xfer(self.b, self.a, False)),
                          ("Move  →", lambda: self.xfer(self.a, self.b, True)), ("←  Move", lambda: self.xfer(self.b, self.a, True))):
            ttk.Button(mid, text=text, width=10, command=cmd).pack(pady=6)
        self.b.frame.pack(side="left", fill="both", expand=True)
        ttk.Style().configure("Treeview", rowheight=36)
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.load_live(quiet=True)
        self.poll()

    def poll(self):
        # duckstation_running() shells out to tasklist, which is slow enough (100-500ms+) that
        # calling it synchronously here every 2s froze the whole UI on Tkinter's single thread -
        # that's the "slow and unresponsive all the time" symptom. Run the check off-thread and
        # only touch the StringVar (cheap) back on the main thread.
        def check():
            running = s.duckstation_running()
            self.root.after(0, lambda: self.ds_state.set(
                "DuckStation is running - live cards will be saved when it closes" if running else ""))
        threading.Thread(target=check, daemon=True).start()
        self.root.after(2000, self.poll)

    def live_path(self, n):
        return os.path.join(self.dir.get(), f"{self.game.get()}_{n}.mcd")

    def load_live(self, quiet=False):
        for n, panel in ((1, self.a), (2, self.b)):
            p = self.live_path(n)
            if os.path.exists(p):
                panel.try_load(p)
            elif not quiet:
                messagebox.showinfo("Load", f"Not found: {p}")

    def xfer(self, src, dst, move):
        sel = src.selected()
        if not (src.need_card() and dst.need_card()):
            return
        if not sel:
            return messagebox.showinfo("Copy", "Select one or more saves first.")
        dst.snapshot()
        if move:
            src.snapshot()
        done = []
        for sv in src.saves(sel):
            if dst.put(sv):
                done.append(sv)
        if move:
            for sv in done:
                first = next(f for f, _ in s.chains(bytes(src.card)) if f["name"] == sv.name and s.save_title(bytes(src.card), f["slot"]) == sv.title)
                s.delete_save(src.card, first["slot"])
            if done:
                src.dirty = True
        src.refresh()
        dst.refresh()

    def combine(self):
        files = filedialog.askopenfilenames(title="Pick every card / .mcs to merge", filetypes=CARD_TYPES, initialdir=self.dir.get())
        if not files:
            return
        out = filedialog.askdirectory(title="Where should the combined cards go?", initialdir=self.dir.get())
        if not out:
            return
        base = simpledialog.askstring("Combine", "Name for the result cards (adds _1, _2, ...):", initialvalue="combined")
        if not base:
            return
        try:
            paths, report = s.combine(list(files), out, base)
        except (s.SaveError, OSError) as e:
            return messagebox.showerror("Combine", str(e))
        messagebox.showinfo("Combined", "\n".join(report) + f"\n\n{len(paths)} card(s) written to\n{out}")
        if paths and messagebox.askyesno("Combine", "Load the first two into Card A and Card B?"):
            self.a.try_load(paths[0])
            if len(paths) > 1:
                self.b.try_load(paths[1])

    def convert(self):
        files = filedialog.askopenfilenames(title="Cards to convert", filetypes=CARD_TYPES, initialdir=self.dir.get())
        if not files:
            return
        to = simpledialog.askstring("Convert", "Convert to (mcd, mcr, mc, srm, bin, gme, vgs):", initialvalue="mcd")
        if not to:
            return
        try:
            fmt, ext = s.target_for(to)
        except s.SaveError as e:
            return messagebox.showerror("Convert", str(e))
        out = filedialog.askdirectory(title="Output folder (Cancel = next to each source)") or None
        lines = []
        for f in files:
            try:
                sfmt, dest = s.convert_file(f, fmt, ext, out)
                lines.append(f"OK   {os.path.basename(f)} [{sfmt}] -> {os.path.basename(dest)}")
            except (s.SaveError, OSError) as e:
                lines.append(f"FAIL {os.path.basename(f)}: {e}")
        messagebox.showinfo("Convert", "\n".join(lines))

    def install(self, quiet=False):
        for p, nm in ((self.a, "A"), (self.b, "B")):
            if p.card is not None and (p.dirty or not p.path):
                if messagebox.askyesno("Install", f"Card {nm} has unsaved changes. Save it first?"):
                    p.save()
                if p.dirty or not p.path:
                    return False
        paths = [p.path for p in (self.a, self.b) if p.card is not None and p.path]
        if not paths:
            messagebox.showinfo("Install", "Load at least Card A first.")
            return False
        try:
            done = s.install_cards(paths, self.dir.get(), self.game.get())
        except (s.SaveError, OSError) as e:
            messagebox.showerror("Install", str(e))
            return False
        if not quiet:
            messagebox.showinfo("Installed", "DuckStation will now use:\n" + "\n".join(done) +
                                "\n\n(Previous cards were backed up to cards\\_backup.)")
        return True

    def play(self):
        if self.install(quiet=True):
            if os.path.exists(s.PLAY_BAT):
                subprocess.Popen(["cmd", "/c", s.PLAY_BAT], creationflags=0x08000000)
            else:
                messagebox.showinfo("Play", "Cards installed. Launcher not found: " + s.PLAY_BAT)

    def close(self):
        if any(p.dirty for p in (self.a, self.b)) and not messagebox.askyesno("Quit", "There are unsaved changes. Quit anyway?"):
            return
        self.root.destroy()


def run():
    root = tk.Tk()
    App(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    run()
