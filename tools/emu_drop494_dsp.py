"""SC49.4 DSP tests (masterfx_dsp.use_novinyl, drums2_dsp.use_nocomb) against SC49.3, on the dsp56kEmu interpreter.

    python tools/emu_drop494_dsp.py SC49.4.bin SC49.4_manifest.json SC49.3.bin SC49.3_manifest.json
  * drums, dstage: no filter / LP / HP / band-pass / notch, ring mod, tremolo: the output and the drum's block identical to SC49.3;
  * drums, dctl: the mailbox's filter mode 0 / 1 / 2 / 4 as before, 3 (the comb's) = 4 (the tilt EQ); SC49.3 kept 3;
  * Master FX with Digitise on: the output identical to SC49.3; X:VN_ST..+3 (Digitise's envelope start since SC39.9) kept, where SC49.3 zeroed them;
  * the program is shorter (P words), the stack no deeper.
"""
from __future__ import annotations
import json, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
from emu_masterfx_dsp import s24, u24  # noqa: E402
import drums2_dsp as DD  # noqa: E402
import masterfx_dsp as G  # noqa: E402

N = 32
VOICE_R3, BUF, SC16_BLK = 0x1E8D, 0x2C02, 0x3A10


def T(*l): return G.T(*l)


def prog(img):
    sp = dsp_program(img)
    return [int.from_bytes(sp[i:i + 3], 'big') for i in range(0, len(sp), 3)]


def main(img, man, prev, pman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    P, Pp = prog(img), prog(prev)
    dl = {k: int(v, 16) for k, v in man["report"]["sc16"]["dsp_labels"].items()}
    dp = {k: int(v, 16) for k, v in pman["report"]["sc16"]["dsp_labels"].items()}
    check(len(P) < len(Pp), f"the program: ${len(P):x} words (SC49.3: ${len(Pp):x}, {len(Pp) - len(P)} fewer); no vin / fl_comb / TCOMB "
          f"({[k for k in ('vin', 'fl_comb', 'TCOMB') if k in dl]})")
    rnd = random.Random(494)
    sig = lambda amp=0x300000: [u24(rnd.randrange(-amp, amp)) for _ in range(N)]
    common = [('x', 0x3A, [N]), ('x', 0x39, [5]), ('x', SC16_BLK, [0] * 36), ('x', 0x1ED6, [0x9F, 0xA3, VOICE_R3])]
    def call(Pr, addr, mem, dumps, regs=()):
        res, ran = run(Pr, addr, mem=common + mem, dumps=dumps, regs_code=list(regs))
        assert 'pc=00' in ran, ran
        return res
    blk = lambda vals: [('x', DD.DB, [vals.get(i, 0) & 0xFFFFFF for i in range(DD.STRIDE)])]
    def stage(Pr, addr, vals, buf):
        return call(Pr, addr, blk(vals) + [('x', BUF, buf), ('x', VOICE_R3, [0x3B00, 0xF0, 0x400000, 0, 0, 0, 1, 0x500000] + [0] * 10),
                                           ('x', 0xA3, [0, 0x10000, 0, 0, 0x123456])],
                    [('x', BUF, N), ('x', DD.DB, DD.STRIDE)])
    # ---- drums, dstage
    cases = [({}, "no filter"), ({DD.RMF: 40, DD.RMA: 127, DD.RC: DD.q24(0.9)}, "ring mod"),
             ({DD.FMODE: 1, DD.FF: 0x180000, DD.FQ: 0x300000, DD.LOW: 0x010000, DD.BAND: 0xFF0000}, "LP"),
             ({DD.FMODE: 2, DD.FF: 0x180000, DD.FQ: 0x300000, DD.LOW: 0x010000, DD.BAND: 0xFF0000}, "HP"),
             ({DD.FMODE: 3, DD.FF: 0x180000, DD.FQ: 0x300000, DD.LOW: 0x010000, DD.BAND: 0xFF0000}, "band-pass"),
             ({DD.FMODE: 4, DD.FF: 0x180000, DD.FQ: 0x300000, DD.LOW: 0x010000, DD.BAND: 0xFF0000}, "notch"),
             ({DD.LFO: 10, DD.TG: 0x7FFFFF, DD.TGN: 0x300000}, "tremolo")]
    for vals, name in cases:
        buf = sig()
        r, rp = stage(P, dl["dstage"], vals, buf), stage(Pp, dp["dstage"], vals, buf)
        check(r[('x', BUF)] == rp[('x', BUF)] and r[('x', DD.DB)] == rp[('x', DD.DB)], f"drums, {name}: output and block identical to SC49.3")
    # ---- drums, dctl: the mailbox's filter mode
    def mb(tag, code, v): return (tag << 23) | (code << 16) | (v & 0xFFFF)
    def ctl(Pr, addr, vals):
        voice = [0x3B00, 0xF0, 0x400000, 0, 0, 0, 0, 0] + [0] * 10
        r = call(Pr, addr, blk(vals) + [('x', 0xA3, [0, 0x10000, 0, 0, 0]), ('x', 0x9F, [0]), ('x', VOICE_R3, voice)],
                 [('x', DD.DB, DD.STRIDE)], regs=T("move #>$9f,r1", "move #>$a3,r2", "move #>$%x,r3" % VOICE_R3))
        return r[('x', DD.DB)]
    got, gotp = [], []
    for v in range(5):
        got.append(ctl(P, dl["dctl"], {DD.MB: mb(1, 9, v), DD.FSEL: 1})[DD.FSEL])
        gotp.append(ctl(Pp, dp["dctl"], {DD.MB: mb(1, 9, v), DD.FSEL: 1})[DD.FSEL])
    check(got == [0, 1, 2, 4, 4] and gotp == [0, 1, 2, 3, 4], f"filter mode 0..4 by the mailbox: {got} (SC49.3: {gotp}): the comb's 3 = the tilt EQ")
    b, bp = ctl(P, dl["dctl"], {DD.FSEL: 4, DD.EC: 10}), ctl(Pp, dp["dctl"], {DD.FSEL: 4, DD.EC: 10})
    check(b[DD.FMODE] == bp[DD.FMODE] and b[DD.FF] == bp[DD.FF], f"the tilt EQ's set-up as SC49.3 (FMODE {b[DD.FMODE]}, FF {b[DD.FF]:#x})")
    # ---- Master FX: Digitise on
    def fx(Pr, addr):
        mem = [('x', G.FX_ON, [1 << G.B_DIG]), ('x', G.BUF, sig()), ('x', G.VN_ST, [0x123456, 0x234567, 0x345678, 0x456789])]
        for k, v in ((G.DG_CNT, 1), (G.DG_N, 4), (G.DG_MASK, 0xFFF000)): mem.append(('x', k, [v]))
        return call(Pr, addr, mem, [('x', G.BUF, 2 * 0x3A), ('x', G.VN_ST, 4)])
    rnd = random.Random(7); r = fx(P, dl["fx_hook"]); rnd = random.Random(7); rp = fx(Pp, dp["fx_hook"])
    check(r[('x', G.BUF)] == rp[('x', G.BUF)], "Master FX, Digitise on: the output identical to SC49.3")
    check(r[('x', G.VN_ST)] == [0x123456, 0x234567, 0x345678, 0x456789] and rp[('x', G.VN_ST)] == [0, 0, 0, 0],
          f"X:VN_ST..+3 (Digitise's envelope start) kept ({[hex(x) for x in r[('x', G.VN_ST)]]}); SC49.3 zeroed them ({rp[('x', G.VN_ST)]})")
    print(f"{man.get('marker', '?')} DROP494 DSP RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text()), Path(a[2]).read_bytes(), json.loads(Path(a[3]).read_text())) else 0)
