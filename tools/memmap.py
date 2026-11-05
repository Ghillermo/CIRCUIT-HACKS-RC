"""S514D / S514D2: the memory budget from the PC (the Circuit Tracks on USB with the diagnostic installed, the MIDI ports free).

    python tools/memmap.py start [STATE.json]     core 0's X / Y read whole (snapshot A), canaries written into the ARM RAM's unknown ranges
    (use the device a while: patterns, packs, projects, Sample Rec, FM / granular, Save, the SD app ...)
    python tools/memmap.py end [STATE.json]       snapshot B, the canaries checked, core 1's report read; the map printed (and STATE + .txt)

Core 0 (rdiag dspr): X and Y $0000-$7FFF in 64-word blocks: zero in both snapshots / the same non-zero / changed; a block equal to the one $2000 /
$4000 / $8000 below = a mirror (no memory there).  ARM RAM (rdiag rfill / rchk, address XOR KEY): RANGES, checked in 1 KB pieces (the ones whose
words all survived = unused); a range the firmware refuses (near the stack) is shrunk.  Core 1 (granular_dsp.use_memdiag, rdiag dspx of external
Y at MREP): its OMR, the write tests of P / X / Y, its 64-word blocks (changed since its first scan / never / all zero).
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ctremote as CR  # noqa: E402
import granular_dsp as GD  # noqa: E402

KEY = 0x6B1D2C3A
RANGES = [(0x20044E58, 0x20045000), (0x20047300, 0x20048000), (0x20048220, 0x20049000), (0x2004A3C0, 0x2004E000), (0x2004E000, 0x2004FF00)]
TOP = 0x8000                                   # core 0: X / Y read up to here


class Dev:
    def __init__(self):
        self.L = CR.Link()

    def dspr(self, space, addr, n):
        out = []
        while n > 0:
            k = min(n, CR.NR)
            d = CR.dec_dspr(self.L.ask(lambda s, a=addr, k=k: CR.req_dspr(s, space, a, k), 3))
            if d["status"]: raise SystemExit(f"dspr status {d['status']} at {addr:#x}")
            out += d["words"]; addr += k; n -= k
        return out

    def dspx(self, src, n):
        out = []
        while n > 0:
            k = min(n, CR.NX)
            d = CR.dec_dspx(self.L.ask(lambda s, a=src, k=k: CR.req_dspx(s, a, k), 8))
            if d["status"]: raise SystemExit(f"dspx status {d['status']} at {src:#x}")
            out += d["samples"]; src += k; n -= k
        return out

    def rfill(self, lo, n): return CR.dec_rchk(self.L.ask(lambda s: CR.req_rfill(s, lo, n, KEY), 16))["status"]

    def rchk(self, lo, n): return CR.dec_rchk(self.L.ask(lambda s: CR.req_rchk(s, lo, n, KEY), 17))

    def mem(self, lo, n):
        out = b""
        while n > 0:
            d = CR.dec_mem(self.L.ask(lambda s, a=lo, k=min(n, CR.NMAX): CR.req_mem(s, a, k), 2))
            if d["status"]: raise SystemExit(f"mem status {d['status']} at {lo:#x}")
            out += d["data"]; lo += len(d["data"]); n -= len(d["data"])
        return out


def snapshot(d):
    t0 = time.time(); snap = {}
    for sp, name in ((0, "x"), (1, "y")):
        snap[name] = d.dspr(sp, 0, TOP)
        print(f"  core 0 {name.upper()}: {TOP} words ({time.time() - t0:.0f} s)", flush=True)
    return snap


def start(state):
    d = Dev()
    ver = CR.dec_ping(d.L.ask(CR.req_ping, 1))["version"]
    if not ver & 0x800: raise SystemExit(f"version {ver:#x}: no RAMCK (install S514D / S514D2)")
    print("snapshot A of core 0 ..."); a = snapshot(d)
    filled = []
    for lo, hi in RANGES:
        while hi > lo and d.rfill(lo, hi - lo) == 3: hi -= 0x400                 # refused: near the stack
        if hi > lo: filled.append((lo, hi)); print(f"  canaries {lo:#x}-{hi:#x}")
    ram = {}
    for lo, hi in RANGES:                                                       # (the ranges not filled: read, to compare at the end)
        if not any(f[0] == lo for f in filled): ram[hex(lo)] = d.mem(lo, hi - lo).hex(); print(f"  read {lo:#x}-{hi:#x}")
    Path(state).write_text(json.dumps(dict(a=a, filled=filled, ram=ram, t=time.time())))
    d.L.close(); print(f"saved {state}: now use the device for a while, then: python tools/memmap.py end {state}")


def blocks(a, b, base_cmp):
    out = []
    for k in range(TOP // 64):
        wa, wb = a[64 * k:64 * k + 64], b[64 * k:64 * k + 64]
        mirror = any(64 * k >= m and wb == b[64 * k - m:64 * k - m + 64] and any(wb) for m in base_cmp)
        out.append("M" if mirror else "0" if not any(wa) and not any(wb) else "c" if wa != wb else "=")
    return out


def runs(marks, want, step=64):
    rs, cur = [], None
    for k, m in enumerate(marks + ["#"]):
        if m in want and cur is None: cur = k
        if m not in want and cur is not None: rs.append((cur * step, k * step - 1)); cur = None
    return rs


def end(state):
    st = json.loads(Path(state).read_text())
    d = Dev()
    lines = [f"memmap: {time.time() - st['t']:.0f} s between the two readings"]
    print("snapshot B of core 0 ..."); b = snapshot(d)
    for name in ("x", "y"):
        mk = blocks(st["a"][name], b[name], (0x2000, 0x4000, 0x6000))
        lines.append(f"core 0 {name.upper()}: zero both times {[f'${lo:04X}-${hi:04X}' for lo, hi in runs(mk, '0')]}")
        lines.append(f"core 0 {name.upper()}: changed {len(runs(mk, 'c'))} runs, constant {len(runs(mk, '='))} runs, mirror from {[f'${lo:04X}' for lo, _ in runs(mk, 'M')][:1]}")
        lines.append("  map (64 words a mark, 0 zero / = same / c changed / M mirror): " + "".join(mk))
    for lo, hi in st["filled"]:
        bad = []
        for p in range(lo, hi, 0x400):
            r = d.rchk(p, min(0x400, hi - p))
            if r["bad"]: bad.append((p, r["bad"]))
        free = runs(["b" if any(p == q for q, _ in bad) else "f" for p in range(lo, hi, 0x400)], "f", 0x400)
        lines.append(f"ARM RAM {lo:#x}-{hi:#x}: untouched {[f'{lo + a_:#x}-{lo + b_ + 1:#x}' for a_, b_ in free]}; written {[(hex(p), n) for p, n in bad]}")
    for lo_s, h0 in st.get("ram", {}).items():
        lo = int(lo_s, 16); b0 = bytes.fromhex(h0); b1 = d.mem(lo, len(b0))
        mk = ["0" if not any(b0[i:i + 1024]) and b0[i:i + 1024] == b1[i:i + 1024] else "=" if b0[i:i + 1024] == b1[i:i + 1024] else "c" for i in range(0, len(b0), 1024)]
        lines.append(f"ARM RAM {lo:#x}-{lo + len(b0):#x} (read twice, 1 KB a mark: 0 zero / = same / c changed): " + "".join(mk))
    rep = d.dspx(GD.MREP, 64 + 3 * (GD.M_XN + GD.M_YN))
    if rep[0] != 0xC1DD: lines.append(f"core 1: no report ({rep[0]:#x})")
    else:
        omr = rep[1] | (rep[2] << 8 & 0xFF0000)
        lines.append(f"core 1: OMR {omr:#08x} (MS = bit 7: {omr >> 7 & 1}), {rep[6]} scans")
        for i, sp in enumerate("pxy"):
            res = rep[8 + 16 * i:24 + 16 * i]
            lines.append(f"core 1 {sp.upper()} write tests: " + " ".join(f"${ad:04X}{'+' if r else '-'}" for ad, r in zip(GD.M_TESTS[sp], res)))
        bl = rep[64:]
        for name, k0, n in (("X", 0, GD.M_XN), ("Y", GD.M_XN, GD.M_YN)):
            mk = ["c" if bl[3 * k + 1] else "0" if not bl[3 * k + 2] else "=" for k in range(k0, k0 + n)]
            lines.append(f"core 1 {name}: zero, never changed {[f'${lo:04X}-${hi:04X}' for lo, hi in runs(mk, '0')]}")
            lines.append(f"  map: " + "".join(mk))
    d.L.close()
    txt = "\n".join(lines); print(txt)
    Path(state).with_suffix(".txt").write_text(txt + "\n")
    st["b"] = b; Path(state).write_text(json.dumps(st))


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] not in ("start", "end"): print(__doc__); sys.exit(0)
    (start if a[0] == "start" else end)(a[1] if len(a) > 1 else "memmap_state.json")
