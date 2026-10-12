"""SC34 DSP tests: the captured sample with V34 (sampler_dsp: the state through r2 with the one-word x:(r2+d) form, M2 / M5 linear, CMD 4 = replace a drum sample).

    python tools/emu_sc34_dsp.py [SC34.bin SC34_manifest.json]
  * every SC33 test again on the V34 code (record, play forward / reverse, pitch, loop, gate, stop, first call);
  * CMD 4 with REPN = n: the sample table entry X:$1D8D + 4 n = (the slot, LEN - 2), its third word (the base increment) untouched; the capture is copied into the
    slot (CHUNK words per block: a 3000-word capture takes 3 blocks); the next CMD 4 uses the next slot (8, round robin); nothing recorded = nothing changes;
  * r2, M2, M4, M5 as found.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import sampler_dsp as S  # noqa: E402
S.V34 = True
import emu_sc33_dsp as T33  # noqa: E402
from dspemu import run  # noqa: E402
import masterfx_dsp as G  # noqa: E402

AT, DRV = 0x1000, 0x2000
TB, TMAX, TSLOT = 0x40000, 0xC00, 0x50000
STAB = S.SAMPLE_TAB


def T_(*l): return G.T(*l)


def main(img=None, man=None):
    fails = T33.main(img, man)
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    w, lab = S.code(AT, TB, TMAX, v34=True, slot0=TSLOT)
    P = [0] * 0x4000
    P[AT:AT + len(w)] = w
    def setx(addr, v): return T_("move #>$%x,x0" % (v & 0xFFFFFF), "move x0,x:>$%x" % addr)
    def go(steps, mem=(), dumps=()):
        drv = T_("move #>$111,r2", "move #>$222,m2", "move #>$333,m4", "move #>$444,m5")
        for st in steps: drv += [0x0BF080, AT] if st == "call" else st
        drv += T_("move r2,x:>$3c00", "move m2,x:>$3c01", "move m4,x:>$3c02", "move m5,x:>$3c03") + [0x00000C]
        P2 = list(P); P2[DRV:DRV + len(drv)] = drv
        return run(P2, DRV, mem=[('x', 0x3A, [58]), ('x', S.MAGIC_AT, [S.MAGIC])] + list(mem), maxins=5_000_000,
                   dumps=[('x', S.SMB, 0x20), ('x', 0x3C00, 4), ('x', STAB, 4 * 12)] + list(dumps))
    st = lambda r, k: r[('x', S.SMB)][k - S.SMB]
    LENP = 3000
    cap = [((i * 37) & 0xFFFF) << 8 for i in range(LENP)]
    tab = [0x111000 + i for i in range(4 * 12)]
    base = [('y', TB, cap), ('x', S.LEN, [LENP]), ('x', STAB, tab)]
    r, ran = go([setx(S.REPN, 5), setx(S.CMD, 4), "call"], mem=base, dumps=[('y', TSLOT, LENP)])
    t = r[('x', STAB)]
    check(t[20:23] == [TSLOT, LENP - 2, tab[22]] and t[:20] == tab[:20] and t[24:] == tab[24:], f"CMD 4, sample 5: entry = (slot 0, LEN - 2), the base increment kept {[hex(x) for x in t[20:24]]} ({ran})")
    check(st(r, S.CMD) == 0 and st(r, S.REPK) == 1 and st(r, S.CPLEN) == LENP - S.CHUNK, f"CMD cleared, next slot 1, {st(r, S.CPLEN)} words left to copy")
    check(r[('y', TSLOT)][:S.CHUNK] == cap[:S.CHUNK] and r[('y', TSLOT)][S.CHUNK] == 0, "the first block copied CHUNK words")
    r, _ = go([setx(S.REPN, 5), setx(S.CMD, 4), "call", "call", "call", "call"], mem=base, dumps=[('y', TSLOT, LENP)])
    check(r[('y', TSLOT)] == cap and st(r, S.CPLEN) == 0, "three more blocks: the whole capture is in the slot, the copy ends")
    r, _ = go([setx(S.REPN, 5), setx(S.CMD, 4), "call", setx(S.REPN, 9), setx(S.CMD, 4), "call"], mem=base)
    t = r[('x', STAB)]
    check(t[36:38] == [TSLOT + TMAX, LENP - 2] and t[20] == TSLOT and st(r, S.REPK) == 2, f"a second replacement (sample 9) takes slot 1 {[hex(x) for x in t[36:38]]}")
    r, _ = go([setx(S.REPK, 7), setx(S.REPN, 1), setx(S.CMD, 4), "call"], mem=base)
    check(r[('x', STAB)][4] == TSLOT + 7 * TMAX and st(r, S.REPK) == 0, "slot 7, then back to slot 0")
    r, _ = go([setx(S.REPN, 5), setx(S.CMD, 4), "call"], mem=[('x', S.LEN, [0]), ('x', STAB, tab)])
    check(r[('x', STAB)] == tab and st(r, S.CPLEN) == 0, "nothing recorded: the table is not touched")
    check(r[('x', 0x3C00)] == [0x111, 0x222, 0x333, 0x444], f"r2, M2, M4, M5 as found {[hex(x) for x in r[('x', 0x3C00)]]}")
    w0, _ = S.code(AT, v34=False, hold=False)
    check(len(w0) == 315, "without V34 the code is SC33's (315 words)")
    print("SC34 DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    if len(a) > 2: sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
    sys.exit(1 if main() else 0)
