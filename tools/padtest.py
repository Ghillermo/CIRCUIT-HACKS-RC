"""PATCHD (firmware/patchdiag/) test of the padding of the synth patch records (Patches/NN_PATCHBANK.cpb: records of 512 bytes = 340 of patch + 172 of 0xFF padding; the last
record has no padding; an empty slot = past the end of the file or a record of 0xFF).  Needs PATCHD (firmware/patchdiag/) (tools/rdiag.py) and the Circuit Tracks on USB;
Windows (tools/ctremote.py).  Use a TEST PACK: mark / unmark write to its patch bank files.

    python tools/padtest.py scan [PACK]                       every bank of the pack: size, patches, and whether each padding is all 0xFF
    python tools/padtest.py mark BANK [PACK] --yes            writes three test marks of 40 bytes in the bank (see below)
    python tools/padtest.py check BANK [PACK]                 reads the marks back: intact / changed / gone
    python tools/padtest.py unmark BANK [PACK] --yes          0xFF over the marks again (the file stays as long as it got)

The three marks (bank b = patches 8b+1 .. 8b+8 of the pack; the bank needs 2..6 patches):
  A  in the padding of the FIRST record (a patch with a record after it): the normal case;
  B  in the padding of the LAST record (it has none: the file grows by 172 bytes to a full record);
  C  in a NEW record after the end (340 bytes of 0xFF = an empty slot for the stock, then the mark).
A mark = "CTPD" + bank + record + a 33-byte pattern + an 8-bit sum (40 bytes) at 512 x record + 340.  The state (sizes, records) is kept in padtest_BANK.json
next to this script, so check / unmark know where the marks are.  PACK defaults to 127 = the pack that is loaded.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ctremote as CR  # noqa: E402

KIND = 3                                  # Patches
REC, PATCH, PADN = 512, 340, 172
MARKN = 40
HERE = Path(__file__).resolve().parent


def mark_bytes(bank, rec):
    pat = bytes((0x5A ^ (bank * 16 + rec) ^ i * 7) & 0xFF for i in range(33))
    body = b"CTPD" + bytes([bank, rec]) + pat                    # 39 bytes + the 8-bit sum = MARKN
    return body + bytes([sum(body) & 0xFF])


class Dev:
    """the SD items through rdiag; `link` = ctremote.Link() (or a model with the same ask())."""
    def __init__(self, link, pack=0x7F):
        self.L, self.pack = link, pack

    def info(self, bank):
        d = CR.dec_info(self.L.ask(lambda s: CR.req_info(s, KIND, bank, self.pack), 4))
        return d["exists"], d["size"]

    def read(self, bank, off, n):
        out = b""
        while len(out) < n:
            k = min(CR.NMAX, n - len(out))
            d = CR.dec_read(self.L.ask(lambda s, o=off + len(out), k=k: CR.req_read(s, KIND, bank, o, k, self.pack), 5))
            if d["status"] or not d["done"]: raise SystemExit(f"read: status {d['status']} done {d['done']} (bank {bank} offset {off + len(out)})")
            out += d["data"]
            if len(d["data"]) < k: break
        return out

    def write(self, bank, off, data):
        for o in range(0, len(data), CR.NMAX):
            d = CR.dec_write(self.L.ask(lambda s, o=o: CR.req_write(s, KIND, bank, off + o, data[o:o + CR.NMAX], self.pack), 6))
            if d["status"]: raise SystemExit(f"write: status {d['status']} (bank {bank} offset {off + o})")


def scan(dev, out=print):
    rows = []
    for bank in range(16):
        ex, size = dev.info(bank)
        if not ex:
            out(f"bank {bank:2d}: no file"); rows.append(dict(bank=bank, exists=0)); continue
        n = (size + REC - 1) // REC
        pads = []
        for r in range(n):
            if size < REC * r + REC:
                pads.append("-"); continue                          # the last record: no padding
            p = dev.read(bank, REC * r + PATCH, PADN)
            pads.append("F" if p == b"\xFF" * PADN else ("M" if p[:4] == b"CTPD" else "x"))
        out(f"bank {bank:2d}: {size:5d} B, {n} records, padding {''.join(pads)}   (F = all 0xFF, M = a mark of ours, x = other data, - = none)")
        rows.append(dict(bank=bank, exists=1, size=size, records=n, pads="".join(pads)))
    return rows


def plan(size):
    """-> (records, marks {name: record}) for a bank of `size` bytes, or a reason"""
    n = (size + REC - 1) // REC
    if size != REC * (n - 1) + PATCH: return None, f"size {size} is not 512 x n + 340 (a bank written by something else?)"
    if not 2 <= n <= 6: return None, f"{n} patches: pick a bank with 2..6 patches"
    return n, {"A": 0, "B": n - 1, "C": n}


def do_mark(dev, bank, out=print):
    ex, size = dev.info(bank)
    if not ex: raise SystemExit(f"bank {bank}: no file")
    n, marks = plan(size)
    if n is None: raise SystemExit(f"bank {bank}: {marks}")
    if dev.read(bank, PATCH, PADN) != b"\xFF" * PADN: raise SystemExit(f"bank {bank}: the padding of record 0 is not all 0xFF: not touching it")
    dev.write(bank, REC * marks["A"] + PATCH, mark_bytes(bank, marks["A"]))
    dev.write(bank, REC * marks["B"] + PATCH, mark_bytes(bank, marks["B"]) + b"\xFF" * (PADN - MARKN))
    dev.write(bank, REC * marks["C"], b"\xFF" * PATCH + mark_bytes(bank, marks["C"]) + b"\xFF" * (PADN - MARKN))
    st = dict(bank=bank, pack=dev.pack, size_before=size, records_before=n, marks=marks, patch_c=None)
    (HERE / f"padtest_{bank}.json").write_text(json.dumps(st, indent=1))
    out(f"bank {bank}: marks A (record {marks['A']}), B (record {marks['B']}, the last one), C (new record {marks['C']}, empty for the stock); "
        f"size {size} -> {dev.info(bank)[1]}")
    return st


def do_check(dev, bank, out=print):
    st = json.loads((HERE / f"padtest_{bank}.json").read_text())
    ex, size = dev.info(bank)
    res = {}
    out(f"bank {bank}: size {size} (before the marks {st['size_before']})")
    for name, r in st["marks"].items():
        if size < REC * r + PATCH + MARKN:
            res[name] = "gone (the file is shorter)"; out(f"  {name} record {r}: {res[name]}"); continue
        got = dev.read(bank, REC * r + PATCH, MARKN)
        res[name] = "intact" if got == mark_bytes(bank, r) else ("all 0xFF" if got == b"\xFF" * MARKN else "changed: " + got[:12].hex(" "))
        patch = dev.read(bank, REC * r, 16)
        kind = "empty (0xFF)" if patch == b"\xFF" * 16 else "name " + repr(patch.split(b"\0")[0].decode("latin-1", "replace"))
        out(f"  {name} record {r}: mark {res[name]}; patch {kind}")
    return res


def do_unmark(dev, bank, out=print):
    st = json.loads((HERE / f"padtest_{bank}.json").read_text())
    ex, size = dev.info(bank)
    for name, r in st["marks"].items():
        if size >= REC * r + PATCH + MARKN: dev.write(bank, REC * r + PATCH, b"\xFF" * MARKN)
    out(f"bank {bank}: marks erased (0xFF); the file stays {size} bytes: record {st['marks']['C']} is an empty slot (0xFF) for the stock")


def main(argv):
    if not argv or argv[0] in ("-h", "--help"): print(__doc__); return 0
    cmd, yes = argv[0], "--yes" in argv
    a = [x for x in argv if x != "--yes"]
    if cmd in ("mark", "unmark") and not yes: raise SystemExit(f"{cmd} writes to the patch bank of the pack: add --yes (and use a test pack)")
    pack = int(a[2 if cmd != "scan" else 1], 0) if len(a) > (2 if cmd != "scan" else 1) else 0x7F
    L = CR.Link()
    try:
        dev = Dev(L, pack)
        print("ping", CR.dec_ping(L.ask(CR.req_ping, 1)))
        if cmd == "scan": scan(dev)
        elif cmd == "mark": do_mark(dev, int(a[1], 0))
        elif cmd == "check": do_check(dev, int(a[1], 0))
        elif cmd == "unmark": do_unmark(dev, int(a[1], 0))
        else: print(__doc__); return 1
    finally:
        L.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
