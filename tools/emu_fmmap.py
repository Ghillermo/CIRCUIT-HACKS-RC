"""SC56.3 tests (tools/fmmap.py: the FM page's algorithm map) through the controller and the real LED task:
  * a tap on pad 7 from another page = the FM page, the map not pinned (pads 9-16 = the operators); a tap on the FM page = the map pinned; again
    = off; held past ½ s = the map while held only; Shift + pad 7 = the algorithm list (as pad 7 held before), no map;
  * the map of all 56 algorithms = fmmap.layout (rows read modulator -> carrier, gaps between paths), each cell in the model's colour (ratio
    family, feedback violet, level steady / dim, the picked operator pulsing on every copy), pad 7 bright;
  * a tap on an operator picks it (B_SEL); Shift + operator = muted (dark; c_mmol gives level 0 while the map is fresh, the bl in fm8arm's
    operator loop); one held + another = a link: the custom algorithm (index 56, the spare bytes, c_fmalg's entry = fmmap.custom_entry), the
    layout frozen while held, the new one after; a link closing a loop refused; the same pair again = the link off.

    python tools/emu_fmmap.py SC56.3.bin manifest.json
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R2, UC_ARM_REG_R5, UC_ARM_REG_R8, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402  (its import sets vcf21's options)
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
import fmeng as FE  # noqa: E402
import fm8 as F  # noqa: E402
import fm8arm as A  # noqa: E402
import fmmap as M  # noqa: E402
from thumb import bl as bl_enc  # noqa: E402

MGR = X.MGR


def code_of(params, entry, o, sel, held, mute):
    if mute >> o & 1: return 0
    if entry[2] == o: fam, lev = 4, params[F.GLB + F.G_FB] >= 64
    else:
        p = F.OPB * o
        fam = 3 if params[p + F.O_MODE] else M.ratio_family(0, params[p + F.O_CRS], params[p + F.O_FINE])
        lev = params[p + F.O_OL] >= 50
    st, dm, pu = M.FAM[fam]
    if held:
        h_ = held - 1
        if o == h_: return pu
        if entry[8 + o] >> h_ & 1: return M.WHITE
        return st if entry[8 + h_] >> o & 1 else dm
    return pu if o == sel else st if lev else dm


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    if not F.ALG8: F.use_alg8()
    R = man["report"]
    fl = {k: int(v, 16) for k, v in R["fm8"]["labels"].items()}
    ml = {k: int(v, 16) for k, v in R["fmmap"]["labels"].items()}
    pv = {k: int(v, 16) for k, v in R["fmmap"]["prev"].items()}
    check(bytes(img[pv["olread"] - 0x08010000:pv["olread"] - 0x08010000 + 4]) == bl_enc(pv["olread"], ml["c_mmol"]), "the operator loop's level read = bl c_mmol")
    e = X.EP(img, man)
    e.w8 = lambda a_, v: e.uc.mem_write(a_, bytes([v & 0xFF]))
    def dread(uc, a, s, d): uc.reg_write(UC_ARM_REG_R0, 0); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, dread, begin=A.DSP_READ, end=A.DSP_READ)
    blk = A.FM8R + A.TB0
    par = lambda i: e.r8(blk + i)
    params = lambda: bytes(e.uc.mem_read(blk, F.PLEN))
    press = lambda q: e.call(PRESS, MGR, q, 100, maxins=8_000_000)
    release = lambda q: e.call(RELEASE, MGR, q, maxins=8_000_000)
    def tap(q, ms=100): press(q); e.at(e.t + ms); release(q); e.at(e.t + 50)
    lo = lambda f, a, b: [x & 0xFF for x in f[a:b]]
    def entry():
        return bytes(e.uc.mem_read(e.r0(fl["c_fmalg"], blk), 16))
    def want(sel=None, held=0, mute=0):
        en = entry(); g = M.layout(en)
        s = par(A.B_SEL) if sel is None else sel
        return g, [code_of(params(), en, c - 1, s, held, mute) if c else 0 for c in g]
    grid = lambda: list(e.uc.mem_read(M.FMAP + M.T0, 24))

    # ---- FM on (the engine row), the operator page
    e.btn(2); e.btn(8); e.pad(26); e.pad(FE.ROWPAD); e.pad(26)
    check(par(A.B_ON) == 1, "FM on")
    e.pad(0)                                                                          # another page
    tap(FE.PADNO); f = X.frame(e)
    check(e.r0(fl["c_fmpg"], 0) == 1 and e.r8(M.FMAP + M.T0 + M.O_MODE) == 0, "pad 7 from another page: the FM page, the map not pinned")
    ops = lo(f, 8, 16)
    check(any(ops), f"pads 9-16 = the operators ({[hex(x) for x in ops]})")

    # ---- the ratios: op 1 ratio 1, op 2 ratio 2.5 (coarse 2 fine 25), op 3 0.5, op 4 1.41, op 5 fixed, op 6 3; levels mixed
    for k, (crs, fine, mode, ol) in enumerate([(1, 0, 0, 99), (2, 25, 0, 80), (0, 0, 0, 40), (1, 41, 0, 70), (1, 0, 1, 60), (3, 0, 0, 20), (1, 0, 0, 99), (1, 0, 0, 99)]):
        p = blk + F.OPB * k
        e.w8(p + F.O_CRS, crs); e.w8(p + F.O_FINE, fine); e.w8(p + F.O_MODE, mode); e.w8(p + F.O_OL, ol)
    e.w8(blk + F.GLB + F.G_FB, 100)
    tap(FE.PADNO); f = X.frame(e)
    check(e.r8(M.FMAP + M.T0 + M.O_MODE) == 1, "a tap on the FM page: pinned")

    # ---- every algorithm
    bad = []
    for alg in range(F.NALG):
        e.w8(blk + F.GLB + F.G_ALG, alg); e.w8(blk + A.B_SEL, 0)
        f = X.frame(e); g, w = want()
        if grid() != g or lo(f, 8, 32) != w: bad.append((alg, grid(), g, [hex(x) for x in lo(f, 8, 32)], [hex(x) for x in w]))
    check(not bad, f"the 56 algorithms: layout and colours as the model ({len(bad)} wrong{'; first ' + str(bad[0]) if bad else ''})")
    check(f[6] & 0xFF == FE.COL_FM[0], f"pad 7 bright with the map ({f[6]:#x})")

    # ---- DX7 algorithm 1 (index 16): pick, mute
    e.w8(blk + F.GLB + F.G_ALG, 16); f = X.frame(e); g = grid()
    print("     DX7 1:", g)
    i3 = g.index(3); tap(8 + i3); f = X.frame(e)
    gg, w = want()
    check(par(A.B_SEL) == 2 and lo(f, 8, 32) == w, f"a tap on operator 3: picked, its copies pulse ({[hex(x) for x in lo(f, 8, 32)]})")
    e.shift(True); tap(8 + g.index(2)); e.shift(False); f = X.frame(e)
    mute = e.r8(M.FMAP + M.T0 + M.O_MUTE)
    gg, w = want(mute=mute)
    check(mute == 2 and lo(f, 8, 32) == w and f[8 + g.index(2)] & 0xFF == 0, f"Shift + operator 2: muted, dark ({mute:#x})")
    def mmol(k):
        e.uc.reg_write(UC_ARM_REG_R5, blk); e.uc.reg_write(UC_ARM_REG_R8, k)
        e.call(ml["c_mmol"], 0, blk + F.OPB * k, 0, 0, maxins=100_000); return e.uc.reg_read(UC_ARM_REG_R2)
    check((mmol(1), mmol(0)) == (0, 99), f"c_mmol: operator 2 level 0, operator 1 its level ({mmol(1)}, {mmol(0)})")
    e.at(e.t + 1000)
    check(mmol(1) == 80, f"c_mmol: the map not drawn for 1 s = not muted ({mmol(1)})")
    f = X.frame(e)
    check(e.r8(M.FMAP + M.T0 + M.O_MUTE) == 0, "the map drawn again after a while: nothing muted")

    # ---- a link: 2 (held) -> 3 (DX7 1: 2 -> 1, 6 -> 5 -> 4 -> 3)
    before = grid()
    press(8 + g.index(2)); e.at(e.t + 100); f = X.frame(e)
    gg, w = want(held=2)
    check(lo(f, 8, 32) == w, f"operator 2 held: pulse, its target (1) white, the rest dim ({[hex(x) for x in lo(f, 8, 32)]})")
    press(8 + g.index(3)); e.at(e.t + 50); f = X.frame(e)
    p = params()
    check(par(F.GLB + F.G_ALG) == F.NALG and p[F.GLB + M.G_CN] == 0xC6 and p[F.OPB * 2 + M.SPARE] == 0b1010 and grid() == before,
          f"2 held + 3: the custom algorithm (56, N 6), 3's sources = 2 and 4, the layout kept while held ({p[F.GLB + M.G_CN]:#x}, {p[F.OPB * 2 + M.SPARE]:#b})")
    en = entry()
    check(en == M.custom_entry(p) and en[1] == 0b101 and en[2] == en[3] == 5 and e.r8(blk + A.B_DIRTY) == 1,
          f"c_fmalg = the custom entry: carriers 1 and 3, feedback 6 -> 6 kept, dirty ({en.hex(' ')})")
    release(8 + g.index(3)); release(8 + g.index(2)); f = X.frame(e)
    gg, w = want()
    print("     custom:", grid())
    check(grid() == gg and lo(f, 8, 32) == w and gg[:8] == [0, 2, 1, 0, 6, 5, 4, 3] and gg[14:16] == [2, 3], f"let go: the new layout (_ 2 1 _ 6 5 4 3 / … 2 3) ({grid()})")
    # a loop: 3 -> 2 refused (2 now modulates 3)
    g = grid(); press(8 + g.index(3)); press(8 + g.index(2)); release(8 + g.index(2)); release(8 + g.index(3))
    check(params() == p, "3 held + 2: a loop, refused")
    # the same pair again: off
    press(8 + g.index(2)); press(8 + g.index(3)); release(8 + g.index(3)); release(8 + g.index(2)); X.frame(e)
    q = params()
    check(q[F.OPB * 2 + M.SPARE] == 0b1000 and entry()[1] == 0b101, f"2 held + 3 again: the link off, 1 and 3 carriers ({q[F.OPB * 2 + M.SPARE]:#b})")

    # ---- pad 7: tap = off, held = while held, Shift = the list
    tap(FE.PADNO); f = X.frame(e)
    check(e.r8(M.FMAP + M.T0 + M.O_MODE) == 0 and f[6] & 0xFF != FE.COL_FM[0], "a tap again: unpinned")
    press(FE.PADNO); e.at(e.t + 700); f = X.frame(e)
    gg, w = want()
    check(lo(f, 8, 32) == w, "pad 7 held: the map")
    release(FE.PADNO); f = X.frame(e)
    check(e.r8(M.FMAP + M.T0 + M.O_MODE) == 0 and lo(f, 8, 32) != w, "let go after 0.7 s: no map")
    e.shift(True); press(FE.PADNO); e.shift(False); f = X.frame(e)
    check(par(A.B_P7) == 1, f"Shift + pad 7: the algorithm list ({par(A.B_P7)})")
    release(FE.PADNO)
    print(f"{man['marker']} FMMAP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
