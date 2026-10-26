"""SC47.5 ARM test (fmeng.use_wcache, poly.use_v4): the DSP traffic of FM poly (every DSP write / read is an SPI transaction that waits for the DSP;
the user, 2026-10-26: «tengo la sensación de que el clock se vuelve inestable al usar FM poly»), the new build against the previous one.

    python tools/emu_fmspi.py NEW.bin NEW_manifest.json PREV.bin PREV_manifest.json      (PREV = SC47.4 / Beta 3.31)

emu_poly3's harness (the whole DSP service chain from its head, a tick a ms), MIDI 1 in FM poly, a short release: the writes / reads in the tick of
a 4-note chord, while it is held (64 ms), let go (64 ms), silent (64 ms), and the same chord 2 s later; the new build's must be far fewer.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_LR, UC_ARM_REG_PC
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
import emu_poly as EP  # noqa: E402
import poly as P  # noqa: E402
import modmx as MX  # noqa: E402
import modesel as MS  # noqa: E402
import mpatch as MP  # noqa: E402
import build_sc14 as S14  # noqa: E402
import fmeng as F  # noqa: E402
MGR = T.MGR


def run(img, man):
    R = man["report"]
    P.adopt(R)                                                                        # (SC47.6: the six-record layout)
    e = T.EL(img)
    vl = {k: int(v, 16) for k, v in R["vcf20"]["labels"].items()}
    sl = {k: int(v, 16) for k, v in R["sc06"]["labels"].items()}
    pl = {k: int(v, 16) for k, v in R["poly"]["labels"].items()}
    def skip(uc): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    for ad in (sl["c_non"], sl["c_noff"], EP.STOCK_TX_ON, EP.STOCK_TX_OFF, EP.REC_GATE):
        e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: skip(uc), begin=ad, end=ad)
    n = {"w": 0, "r": 0}
    def w(uc, a, s, d): n["w"] += 1; skip(uc)
    e.uc.hook_add(UC_HOOK_CODE, w, begin=P.DSP_WRITE, end=P.DSP_WRITE)
    def rd(uc, a, s, d): n["r"] += 1; uc.reg_write(UC_ARM_REG_R0, 0x300000 << 8); skip(uc)
    e.uc.hook_add(UC_HOOK_CODE, rd, begin=0x08029344, end=0x08029344)
    e.at(100000); e.transport(0)
    for _ in range(30): e.at(e.t + 40); e.call(vl["c_vtick"], maxins=3_000_000)
    head = MP.bw_target(bytearray(img), S14.SVC_HOOK, 0x08010000)
    def tick(k=1):
        for _ in range(k): e.at(e.t + 1); e.call(head, maxins=8_000_000)
    non, noff = e.r32(MX.NOTE_VT) & ~1, e.r32(MX.NOTE_VT + 4) & ~1
    on = lambda nt, v=100: e.call(non, EP.TXOBJ, 2, nt, v, maxins=8_000_000)
    off = lambda nt: e.call(noff, EP.TXOBJ, 2, nt, 0, maxins=8_000_000)
    e.uc.mem_write(MS.RAM, bytes(8)); e.btn(2); e.btn(8); e.pad(26); e.pad(F.ROWPAD); e.pad(26)
    if "c_vmset" in pl: e.call(pl["c_vmset"], 0, 3, maxins=1_000_000)
    else:
        for _ in range(2): e.set_p0(e.r32(MGR + 0xC), 1); e.pad(P.PAD29); e.set_p0(e.r32(MGR + 0xC), 0)
    e.uc.mem_write(F.FMR + F.B0 + F.P_REL, bytes([0]))
    tick(70)
    def count(fn, k):
        n["w"] = n["r"] = 0; fn(); tick(k); return n["w"], n["r"]
    chord = count(lambda: [on(x) for x in (60, 64, 67, 71)], 1)
    after = count(lambda: None, 1)
    held = count(lambda: None, 64)
    rel = count(lambda: [off(x) for x in (60, 64, 67, 71)], 64)
    idle = count(lambda: None, 64)
    tick(2000)                                                                        # 2 s later: the same chord again
    chord2 = count(lambda: [on(x) for x in (60, 64, 67, 71)], 1)
    del e; gc.collect()
    return dict(chord=chord, after=after, held=held, rel=rel, idle=idle, chord2=chord2)


def main(img, man, prev, pman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    a, b = run(img, man), run(prev, pman)
    for k, lab in (("chord", "the chord's tick"), ("after", "the next tick"), ("held", "held, 64 ticks"), ("rel", "let go, 64 ticks"), ("idle", "silent, 64 ticks"), ("chord2", "the chord 2 s later")):
        print(f"      {lab:18s} new {a[k][0]:5d} writes {a[k][1]:4d} reads   previous {b[k][0]:5d} writes {b[k][1]:4d} reads")
    check(a["chord2"][0] * 3 <= b["chord2"][0], "a chord (not the first since power-up): at most a third of the writes")
    check(a["held"][0] * 4 <= b["held"][0] and a["held"][1] * 3 <= b["held"][1] * 2, "held: at most a quarter of the writes, two thirds of the reads")
    check(a["idle"][0] * 2 <= b["idle"][0] + 2, "silent: at most half the writes")
    print(f"{man.get('marker', '?')} FMSPI RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    x = sys.argv
    sys.exit(1 if main(Path(x[1]).read_bytes(), json.loads(Path(x[2]).read_text()), Path(x[3]).read_bytes(), json.loads(Path(x[4]).read_text())) else 0)
