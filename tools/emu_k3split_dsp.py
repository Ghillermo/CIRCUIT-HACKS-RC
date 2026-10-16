"""SC41.7 drum DSP tests (drums2_dsp.use_k3split: amp attack, start, cut), on the dsp56kEmu interpreter with the real core-0 programs.

    python tools/emu_k3split_dsp.py NEW.bin NEW_manifest.json PREVIOUS.bin PREVIOUS_manifest.json
  * the program ends below P:$4000;
  * dtrig: AINC = STARTF = ENDC = 0 -> the block, the voice and the position exactly the previous build's; STARTF = 2 s << 16 = the previous build's start nibble s;
    ENDC = E << 16 -> the length L - L x E / 128; AINC != 0 -> AENV, TG, TGN = 0 (else untouched);
  * dctl: AINC = 0 -> TGN as the previous build (with and without the tremolo); AINC != 0 -> AENV += AINC (limited to 1), TGN = the tremolo's gain x AENV;
  * dstage: TGN = 1 -> no gain stage (as before without LFO); TGN < 1 -> the ramp TG -> TGN (bit-exact model), with or without LFO; the tremolo as before;
  * whole core, four hits through the ARM: every new word 0 -> the mix buffers, the drum blocks and the voices exactly the previous build's; with an attack
    the hit starts silent and grows; with a cut the voice ends sooner; the stack no deeper.
"""
from __future__ import annotations
import json, math, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import Session, dsp_program  # noqa: E402
from emu_masterfx_dsp import Acc, s24, u24  # noqa: E402
from emu_sc18_dsp import m_trem  # noqa: E402
import drums2_dsp as DD  # noqa: E402
import masterfx_dsp as G  # noqa: E402

N = 32
VOICE_R3 = 0x1E8D
BUF = 0x2C02
SC16_BLK = 0x3A10
TRAMP = 0x3FF8                                 # the 8 free words (7 used)


def T(*l): return G.T(*l)


def main(img, man, prev, pman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    dl = {k: int(v, 16) for k, v in man["report"]["sc16"]["dsp_labels"].items()}
    dp = {k: int(v, 16) for k, v in pman["report"]["sc16"]["dsp_labels"].items()}
    sp, spp = dsp_program(img), dsp_program(prev)
    P0 = [int.from_bytes(sp[i:i + 3], 'big') for i in range(0, len(sp), 3)]
    Pp = [int.from_bytes(spp[i:i + 3], 'big') for i in range(0, len(spp), 3)]
    check(len(P0) <= TRAMP, f"program ends at P:${len(P0):x} (previous ${len(Pp):x}; the trampoline at ${TRAMP:x})")
    rnd = random.Random(417)
    sig = lambda amp=0x300000: [u24(rnd.randrange(-amp, amp)) for _ in range(N)]
    blk = lambda vals: [('x', DD.DB, [vals.get(i, 0) & 0xFFFFFF for i in range(DD.STRIDE)])]
    common = [('x', 0x3A, [N]), ('x', 0x39, [5]), ('x', SC16_BLK, [0] * 36), ('x', 0x1ED6, [0x9F, 0xA3, VOICE_R3])]
    regs = T("move #>$9f,r1", "move #>$a3,r2", "move #>$%x,r3" % VOICE_R3)
    def call(P, addr, mem, dumps, rg=()):
        res, ran = run(P, addr, mem=common + mem, dumps=dumps, regs_code=list(rg))
        assert 'pc=00' in ran, ran
        return res
    # ---- dtrig
    def trig(P, labels, vals, inc=0x200000, length=0x1000):
        tr = [0x0BF080, labels["dtrig"]] + T("move a1,x:>$3b10", "move a0,x:>$3b11") + [0x00000C]
        P1 = P + [0] * (TRAMP - len(P)) + tr
        r = call(P1, TRAMP, blk(vals) + [('x', VOICE_R3, [0x3B00, length] + [0] * 16)], [('x', DD.DB, DD.STRIDE), ('x', VOICE_R3, 18), ('x', 0x3B10, 2)],
                 rg=regs + T("move #>$%x,a" % inc))
        return r[('x', DD.DB)], r[('x', VOICE_R3)], r[('x', 0x3B10)]
    base = {DD.PE: 0, DD.TG: 0x123456, DD.TGN: 0x234567}
    bn, vn, pn = trig(P0, dl, base); bp, vp, pp = trig(Pp, dp, base)
    check(bn == bp and vn == vp and pn == pp, "dtrig, every new word 0: the block, the voice and the position exactly the previous build's")
    for s in (1, 8, 15):
        bn, vn, pn = trig(P0, dl, {DD.STARTF: (2 * s) << 16}); bp, vp, pp = trig(Pp, dp, {DD.EXT: s})
        check(pn == pp and vn[1] == vp[1], f"start S = {2 * s}: the previous build's start nibble {s} (position {pn[0]:#x}:{pn[1]:#x})")
    for e, L in ((64, 0x1000), (1, 0x1000), (120, 0x3000)):
        bn, vn, pn = trig(P0, dl, {DD.ENDC: e << 16}, length=L)
        want = L - (L * e + 127) // 128
        check(abs(vn[1] - want) <= 1 and pn == [0, 0], f"cut E = {e}: length {vn[1]:#x} of {L:#x} (~{want:#x}), position 0")
    bn, vn, pn = trig(P0, dl, {DD.AINC: 0x1000, DD.AENV: 0x7FFFFF, DD.TG: 0x7FFFFF, DD.TGN: 0x7FFFFF})
    check(bn[DD.AENV] == 0 and bn[DD.TG] == 0 and bn[DD.TGN] == 0, "dtrig with an attack: AENV, TG, TGN = 0 (the hit starts silent)")
    bn, vn, pn = trig(P0, dl, {DD.AENV: 0x400000, DD.TG: 0x7FFFFF, DD.TGN: 0x7FFFFF})
    check(bn[DD.AENV] == 0x400000 and bn[DD.TG] == 0x7FFFFF and bn[DD.TGN] == 0x7FFFFF, "dtrig without an attack: AENV, TG, TGN untouched")
    # ---- dctl
    def ctl(P, labels, vals):
        r = call(P, labels["dctl"], blk(vals) + [('x', 0xA3, [0, 0x10000, 0, 0, 0]), ('x', 0x9F, [0]), ('x', VOICE_R3, [0x3B00, 0xF0, 0x400000, 0, 0, 0, 0, 0] + [0] * 10)],
                 [('x', DD.DB, DD.STRIDE)], rg=regs)
        return r[('x', DD.DB)]
    for lfo in (0, 30, -20):
        v = {DD.LFO: lfo, DD.TRI: 0x400000, DD.PH: 0x400000, DD.LSPD: -64}
        check(ctl(P0, dl, v)[DD.TGN] == ctl(Pp, dp, v)[DD.TGN], f"dctl, no attack, LFO {lfo}: TGN as the previous build")
    for aenv, ainc, lfo in ((0, 0x100000, 0), (0x200000, 0x100000, 0), (0x7F0000, 0x100000, 0), (0x200000, 0x100000, 30)):
        v = {DD.AENV: aenv, DD.AINC: ainc, DD.LFO: lfo, DD.TRI: 0x400000, DD.PH: 0x400000, DD.LSPD: -64}
        b = ctl(P0, dl, v); g = ctl(Pp, dp, {k: x for k, x in v.items() if k not in (DD.AENV, DD.AINC)})[DD.TGN]
        ae = min(0x7FFFFF, aenv + ainc)
        check(b[DD.AENV] == ae and b[DD.TGN] == Acc().mpy(ae, g).lim(), f"dctl, attack: AENV {aenv:#x} + {ainc:#x} -> {b[DD.AENV]:#x}, TGN = gain {g:#x} x AENV = {b[DD.TGN]:#x} (LFO {lfo})")
    # ---- dstage
    def stage(P, labels, vals, buf):
        r = call(P, labels["dstage"], blk(vals) + [('x', BUF, buf), ('x', VOICE_R3, [0x3B00, 0xF0, 0x400000, 0, 0, 0, 1, 0x500000] + [0] * 10),
                                                    ('x', 0xA3, [0, 0x10000, 0, 0, 0x123456])], [('x', BUF, N), ('x', DD.DB, DD.STRIDE)])
        return r[('x', BUF)], r[('x', DD.DB)]
    buf = sig()
    for vals, name in (({}, "all off"), ({DD.TG: 0x7FFFFF, DD.TGN: 0x7FFFFF}, "gains 1, no LFO"), ({DD.LFO: 30, DD.TG: 0x7FFFFF, DD.TGN: 0x300000}, "tremolo"),
                       ({DD.LFO: 30, DD.TG: 0x100000, DD.TGN: 0x600000}, "tremolo rising")):
        vals = {**{DD.TG: 0x7FFFFF, DD.TGN: 0x7FFFFF}, **vals} if name == "all off" else vals
        on, bn = stage(P0, dl, vals, buf); op, bp = stage(Pp, dp, vals, buf)
        check(on == op and bn[:46] == bp[:46], f"dstage, {name}: output and block as the previous build")
    for tg, tgn in ((0, 0x080000), (0x200000, 0x300000)):
        on, bn = stage(P0, dl, {DD.TG: tg, DD.TGN: tgn}, buf)
        check(on == m_trem(buf, tg, tgn) and bn[DD.TG] == tgn, f"dstage, attack (no LFO): the ramp {tg:#x} -> {tgn:#x} bit-exact, TG updated")
    # ---- whole core
    def session(image, vals, blocks=24, spmax=False):
        s = Session(image)
        for d in range(4): s.capture(f'hit{d}', 0x08051B54, d, 100)
        extra = [('x', 0xA4 + 10 * d, 0x10000) for d in range(4)] + [('x', 0xA5 + 10 * d, 0x7FFFFF) for d in range(4)]
        for k in range(64): extra += [('x', 0x1D8D + 4 * k, 0x3B00), ('x', 0x1D8E + 4 * k, 0x400), ('x', 0x1D8F + 4 * k, 0x8000)]
        for i in range(0x100): extra.append(('y', 0x3B00 + i, u24(int(0x400000 * math.sin(i * 0.2)))))
        for (d, off), val in vals.items(): extra.append(('x', DD.DB + DD.STRIDE * d + off, val & 0xFFFFFF))
        res, rans = s.run(blocks=blocks, per_block=False, extra=extra, spmax=spmax,
                          dumps=[('x', DD.DB, 4 * DD.STRIDE), ('x', VOICE_R3, 4 * 18), ('x', 0x2E70, 3 * 0x40), ('x', 0xEB, 0x70)])
        return {(sp_, a): v for sp_, a, v in res}, rans
    spm = lambda rans: int([x for x in rans if x.startswith('SPMAX')][0].split()[1])
    Rn, rn = session(img, {}, spmax=True); Rp, rp = session(prev, {}, spmax=True)
    same = any(Rn[('x', VOICE_R3)]) and Rn[('x', VOICE_R3)] == Rp[('x', VOICE_R3)] \
        and all(Rn[('x', DD.DB)][d * DD.STRIDE:d * DD.STRIDE + 46] == Rp[('x', DD.DB)][d * DD.STRIDE:d * DD.STRIDE + 46] for d in range(4))
    check(same, "whole core, four hits, every new word 0: voices and drum blocks exactly the previous build's")
    check(spm(rn) <= spm(rp), f"stack depth {spm(rn)} <= the previous build's {spm(rp)}")
    Ra, ra = session(img, {(d, DD.AINC): 0x40000 for d in range(4)}, blocks=6)
    bk = lambda d: Ra[('x', DD.DB)][d * DD.STRIDE:(d + 1) * DD.STRIDE]
    ok = all(bk(d)[DD.BASE] != 0 and 0 < bk(d)[DD.AENV] < 6 * 0x40000 and 0 < bk(d)[DD.TG] < 0x7FFFFF for d in range(4))
    check(ok, f"whole core, an attack (AINC 0x40000): the hits reset AENV (below 6 blocks' worth) and the gain grows from 0 "
              f"(AENV {[hex(bk(d)[DD.AENV]) for d in range(4)]}, TG {[hex(bk(d)[DD.TG]) for d in range(4)]})")
    Rc, _ = session(img, {(d, DD.ENDC): 100 << 16 for d in range(4)}, blocks=12)
    act = lambda R: [R[('x', VOICE_R3)][18 * d + 6] for d in range(4)]
    Rf, _ = session(img, {}, blocks=12)
    check(all(a == 0 for a in act(Rc)) and any(a != 0 for a in act(Rf)), f"whole core, a cut of 100 / 128: the voices end sooner ({act(Rc)} vs {act(Rf)})")
    print(f"{man.get('marker', '?')} DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
