"""Test of tools/padtest.py against a model of the SD card through the real rdiag protocol of tools/ctremote.py (requests and replies encoded as on the wire),
with the two stock patch saves as read in the code: an existing slot = its 340 bytes at 512 x slot (0x0802FC66); after the end of the bank = 0xFF from the
current end of the file, then the 340 bytes (0x0802FBCC).

    python tools/emu_padtest.py
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ctremote as CR  # noqa: E402
import padtest as PT  # noqa: E402


class Model:
    def __init__(self, banks):
        self.f = {b: bytearray(d) for b, d in banks.items()}
    def ask(self, make, cmd, timeout=0):
        m = make(1); p = list(m[6:-1])
        if cmd == 1: return CR.nib32(0x35E8) + CR.nib32(0)
        kind, idx, pack = p[0], p[1], p[2]
        f = self.f.get(idx)
        if cmd == 4: return CR.nib32(1 if f is not None else 0) + CR.nib32(len(f) if f is not None else 0)
        off = CR.un32(p[3:11]); n = p[11]
        if cmd == 5:
            d = bytes(f[off:off + n]) if f is not None else b""
            return CR.nib32(0) + CR.nib32(1) + CR.nibbytes(d)
        if cmd == 6:
            data = CR.unbytes(p[12:12 + 2 * n])
            if f is None: f = self.f[idx] = bytearray()
            if off > len(f): f += b"\x00" * (off - len(f))           # FatFs: a seek past the end leaves undefined bytes (0 here)
            f[off:off + n] = data
            return CR.nib32(0)
    def stock_save(self, bank, slot, name):
        f = self.f[bank]; r5 = 512 * slot; data = name.ljust(16, b"\0") + bytes(range(256)) * 2
        data = data[:340]
        if len(f) < r5: f += b"\xFF" * (r5 - len(f)); f[r5:r5 + 340] = data
        else: f[r5:r5 + 340] = data


def patch(name): return (name.ljust(16, b"\0") + bytes(324))[:340]


def main():
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    bank3 = b"".join(patch(b"P%d" % i) + b"\xFF" * 172 for i in range(3)) + patch(b"P3")        # 4 patches, the last without padding
    md = Model({3: bank3, 0: patch(b"solo")})
    dev = PT.Dev(md)
    rows = PT.scan(dev, out=lambda s: None)
    check(rows[3]["records"] == 4 and rows[3]["pads"] == "FFF-" and rows[0]["pads"] == "-" and rows[5]["exists"] == 0, f"scan: {rows[3]} {rows[0]} {rows[5]}")
    st = PT.do_mark(dev, 3, out=lambda s: None)
    check(st["marks"] == {"A": 0, "B": 3, "C": 4} and len(md.f[3]) == 512 * 5, f"marks A 0 / B 3 / C 4, the file = 5 full records ({len(md.f[3])})")
    check(bytes(md.f[3][512 * 4:512 * 4 + 340]) == b"\xFF" * 340, "record 4: 340 bytes of 0xFF (an empty slot for the stock)")
    check(bytes(md.f[3][:340]) == patch(b"P0") and bytes(md.f[3][512 * 3:512 * 3 + 340]) == patch(b"P3"), "the patches are untouched")
    check(all(v == "intact" for v in PT.do_check(dev, 3, out=lambda s: None).values()), "check: all intact")
    md.stock_save(3, 0, b"edit0"); md.stock_save(3, 4, b"new4")
    r = PT.do_check(dev, 3, out=lambda s: None)
    check(r == {"A": "intact", "B": "intact", "C": "intact"}, f"stock saves into record 0 and the empty record 4: the marks stay {r}")
    md.stock_save(3, 6, b"app6")
    r = PT.do_check(dev, 3, out=lambda s: None)
    check(r == {"A": "intact", "B": "intact", "C": "intact"} and len(md.f[3]) == 512 * 6 + 340 and bytes(md.f[3][512 * 5:512 * 5 + 340]) == b"\xFF" * 340,
          f"a stock save after the end (record 6): 0xFF from the end of the file, the marks stay {r}")
    PT.do_unmark(dev, 3, out=lambda s: None)
    check(bytes(md.f[3][340:380]) == b"\xFF" * 40 and PT.do_check(dev, 3, out=lambda s: None)["A"] == "all 0xFF", "unmark: 0xFF again")
    check(PT.plan(512 * 6 + 340)[0] is None and PT.plan(1000)[0] is None, "plan refuses 7 patches and a size that is not 512 n + 340")
    print("PADTEST RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    for f in Path(PT.HERE).glob("padtest_*.json"): f.unlink()
    return fails


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
