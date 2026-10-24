"""SC46.5 / Beta 3.22 (drums2_dsp.use_lfoscan): the drums' K7 to the left = a scan of the start point.  The real core-0 programs on the dsp56kEmu
interpreter, against the previous build (SC46.4):
  * the program ends at or below P:$3FF8 (the test trampoline above it);
  * dtrig with LFO >= 0 (0, 40): the block, the voice and the position exactly the previous build's (the phase reset, the tremolo side);
  * dtrig with LFO < 0 over L x E x S x LFO x the phase: PH and TRI not touched by the hit, CRC = 0, the length L - L x ENDC as before, the playback
    index 4 a1 + (a0 >> 22) = L x min(4 STARTF + (-LFO / 128)(1 - TRI), 15 / 16 - E / 128) within 4 samples, always below the cut;
  * dctl with LFO < 0: the pitch increment = the previous build's with LFO = 0 (no vibrato); with LFO > 0 the whole block as the previous build's;
  * whole core, four hits through the ARM: with K7 >= 0 the voices and the blocks the previous build's; with K7 < 0 two hits start at different
    places; the stack no deeper.

    python tools/emu_lfoscan_dsp.py NEW.bin NEW_manifest.json PREVIOUS.bin PREVIOUS_manifest.json
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import Session, dsp_program  # noqa: E402
from emu_masterfx_dsp import s24, u24  # noqa: E402
import drums2_dsp as DD  # noqa: E402
import masterfx_dsp as G  # noqa: E402

VOICE_R3 = 0x1E8D
SC16_BLK = 0x3A10
TRAMP = 0x3FF8


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
    check(len(P0) <= TRAMP, f"program ends at P:${len(P0):x} (previous ${len(Pp):x})")
    blk = lambda vals: [('x', DD.DB, [vals.get(i, 0) & 0xFFFFFF for i in range(DD.STRIDE)])]
    common = [('x', 0x3A, [32]), ('x', 0x39, [5]), ('x', SC16_BLK, [0] * 36), ('x', 0x1ED6, [0x9F, 0xA3, VOICE_R3])]
    regs = T("move #>$9f,r1", "move #>$a3,r2", "move #>$%x,r3" % VOICE_R3)
    def call(P, addr, mem, dumps, rg=()):
        res, ran = run(P, addr, mem=common + mem, dumps=dumps, regs_code=list(rg))
        assert 'pc=00' in ran, ran
        return res
    def trig(P, labels, vals, length=0x1000):
        tr = [0x0BF080, labels["dtrig"]] + T("move a1,x:>$3b10", "move a0,x:>$3b11") + [0x00000C]
        P1 = P + [0] * (TRAMP - len(P)) + tr
        r = call(P1, TRAMP, blk(vals) + [('x', VOICE_R3, [0x3B00, length] + [0] * 16)], [('x', DD.DB, DD.STRIDE), ('x', VOICE_R3, 18), ('x', 0x3B10, 2)],
                 rg=regs + T("move #>$200000,a"))
        return r[('x', DD.DB)], r[('x', VOICE_R3)], r[('x', 0x3B10)]
    # ---- dtrig, LFO >= 0: as before
    for lfo in (0, 40):
        v = {DD.LFO: lfo, DD.PH: 0x123456, DD.TRI: 0x654321, DD.STARTF: 16 << 14, DD.ENDC: 8 << 16}
        bn, vn, pn = trig(P0, dl, v); bp, vp, pp = trig(Pp, dp, v)
        check(bn == bp and vn == vp and pn == pp, f"dtrig, LFO {lfo}: the block, the voice and the position exactly the previous build's")
    # ---- dtrig, LFO < 0: the scan
    bad, n = [], 0
    for L in (0x1000, 0x7FFF):
        for E in (0, 60):
            for S in (0, 16, 64):
                for lfo in (-1, -32, -64):
                    for ph in (0x000000, 0x400000, 0x7FFFFF, 0x800000, 0xC00000):
                        tri = u24((abs(s24(ph)) * 2 - 0x800000) if abs(s24(ph)) < 0x800000 else 0x7FFFFF)
                        v = {DD.LFO: lfo, DD.PH: ph, DD.TRI: tri, DD.STARTF: S << 14, DD.ENDC: E << 16, DD.CRC: 0x111111}
                        bn, vn, pn = trig(P0, dl, v, length=L); n += 1
                        a1, a0 = pn[0], pn[1]
                        idx = 4 * s24(a1) + (a0 >> 22)
                        trif = s24(tri) / 0x800000
                        want = L * min(S / 128 + (-lfo / 128) * (1 - trif), 15 / 16 - E / 128)
                        cut = L - (L * E + 127) // 128
                        ok = bn[DD.PH] == ph and bn[DD.TRI] == tri and bn[DD.CRC] == 0 and abs(vn[1] - cut) <= 1 and abs(idx - want) <= 4 and idx < vn[1]
                        if not ok: bad.append((L, E, S, lfo, hex(ph), idx, round(want), vn[1], hex(bn[DD.PH])))
    check(not bad, f"dtrig, LFO < 0: {n} cases, the start = L x min(S/128 + (-LFO/128)(1 - TRI), 15/16 - E/128), below the cut, the phase running ({bad[:3]})")
    # ---- dctl
    def ctl(P, labels, vals):
        r = call(P, labels["dctl"], blk(vals) + [('x', 0xA3, [0, 0x10000, 0, 0, 0]), ('x', 0x9F, [0]), ('x', VOICE_R3, [0x3B00, 0xF0, 0x400000] + [0] * 15)],
                 [('x', DD.DB, DD.STRIDE), ('x', VOICE_R3, 18)], rg=regs)
        return r[('x', DD.DB)], r[('x', VOICE_R3)]
    base = {DD.BASE: 0x200000, DD.PE: 0, DD.ENV: 0x7FFFFF, DD.PH: 0x300000, DD.LSPD: 20}
    for lfo in (-20, -64):
        bn, vn = ctl(P0, dl, {**base, DD.LFO: lfo}); bp, vp = ctl(Pp, dp, {**base, DD.LFO: 0})
        check(vn[2] == vp[2], f"dctl, LFO {lfo}: the pitch increment as the previous build's without LFO ({vn[2]:#x} / {vp[2]:#x}: no vibrato)")
    bn, vn = ctl(P0, dl, {**base, DD.LFO: 30}); bp, vp = ctl(Pp, dp, {**base, DD.LFO: 30})
    check(bn == bp and vn == vp, "dctl, LFO 30 (tremolo): the block and the voice as the previous build's")
    # ---- whole core
    def session(image, lfo, blocks=24, spmax=False, sl=0x2000):
        s = Session(image)
        for d in range(4): s.capture(f'hit{d}', 0x08051B54, d, 100)
        extra = [('x', 0xA4 + 10 * d, 0x10000) for d in range(4)] + [('x', 0xA5 + 10 * d, 0x7FFFFF) for d in range(4)]
        for k in range(64): extra += [('x', 0x1D8D + 4 * k, 0x3B00), ('x', 0x1D8E + 4 * k, sl), ('x', 0x1D8F + 4 * k, 0x8000)]
        for i in range(0x100): extra.append(('y', 0x3B00 + i, u24(int(0x400000 * math.sin(i * 0.2)))))
        for d in range(4):
            extra += [('x', DD.DB + DD.STRIDE * d + DD.LFO, lfo & 0xFFFFFF), ('x', DD.DB + DD.STRIDE * d + DD.LSPD, 100)]
        res, rans = s.run(blocks=blocks, per_block=False, extra=extra, spmax=spmax, dumps=[('x', DD.DB, 4 * DD.STRIDE), ('x', VOICE_R3, 4 * 18)])
        return {(sp_, a): v for sp_, a, v in res}, rans
    spm = lambda rans: int([x for x in rans if x.startswith('SPMAX')][0].split()[1])
    Rn, rn = session(img, 20, spmax=True); Rp, rp = session(prev, 20, spmax=True)
    check(Rn[('x', VOICE_R3)] == Rp[('x', VOICE_R3)] and Rn[('x', DD.DB)] == Rp[('x', DD.DB)], "whole core, K7 right (tremolo): voices and drum blocks the previous build's")
    check(spm(rn) <= spm(rp), f"stack depth {spm(rn)} <= the previous build's {spm(rp)}")
    Ra, _ = session(img, -64, blocks=4); Rb, _ = session(img, -64, blocks=40)
    pa = [Ra[('x', VOICE_R3)][18 * d + 4] for d in range(4)]; pb = [Rb[('x', VOICE_R3)][18 * d + 4] for d in range(4)]
    check(any(x != 0 for x in pa + pb), f"whole core, K7 full left: the hits start into the sample ({[hex(x) for x in pa]})")
    print(f"{man.get('marker', '?')} DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
