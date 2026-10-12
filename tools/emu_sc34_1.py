"""SC34.1 tests: SC34 with sampler_dsp.HIGH (the capture at Y:$E80000, the 8 replacement slots from $EA8800) and the loop held (sampler_dsp.HOLD +
build_sc17.use_loophold).

    python tools/emu_sc34_1.py SC34.1.bin SC34.1_manifest.json
Runs SC34's DSP tests (emu_sc34_dsp, which runs SC33's: the image's code = code() with HIGH / HOLD, and the replacement) and ARM tests (emu_sc34, with the
loophold checks: Shift + a slot / pad 7 = loop with the gate held, released = gate and loop dropped, no toggle-off) on the SC34.1 image; then
  * HOLD on the interpreter: a loop (mode 2 / forced) stops when the gate drops, a one-shot goes on; start = end parks a held loop / gate playback (silent, at S)
    and it plays again from S once start != end; a one-shot with start = end stops;
  * the addresses in the image: the record / play base is $E80000, the slot table = $EA8800 + k * $28800 (k < 8, the last one ends at $FEC800 < $1000000),
    and no address of the pack sample memory ($580000..$E7FFFF) is left in the sampler code.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import sampler_dsp as S  # noqa: E402
S.HIGH = True
S.HOLD = True
import emu_sc34_dsp  # noqa: E402
import emu_sc34  # noqa: E402
emu_sc34.B.use_loophold()
from dsp_session import dsp_program  # noqa: E402
from dspemu import run  # noqa: E402
import masterfx_dsp as G  # noqa: E402

AT, DRV, TB, TMAX, NF = 0x1000, 0x2000, 0x40000, 0x400, 58


def hold_tests(check):
    """sampler_dsp.HOLD on the interpreter (the V34 code with the buffer at TB)."""
    w, _ = S.code(AT, TB, TMAX, v34=True, slot0=0x41000)
    P = [0] * 0x4000; P[AT:AT + len(w)] = w
    T_ = G.T
    def setx(addr, v): return T_("move #>$%x,x0" % (v & 0xFFFFFF), "move x0,x:>$%x" % addr)
    LENP = 300
    ramp = [(i + 1) * 0x100 for i in range(LENP)]
    def play(steps, sf=0, ef=0x7FFFFF, mode=0, cmd=1, state=2):
        drv = setx(S.SF, sf) + setx(S.EF, ef) + setx(S.INCI, 1) + setx(S.INCF, 0) + setx(S.MODE, mode) + setx(S.CMD, cmd) + setx(S.STATE, state)
        for st in steps: drv += [0x0BF080, AT] if st == "call" else st
        drv += [0x00000C]
        P2 = list(P); P2[DRV:DRV + len(drv)] = drv
        r, _ = run(P2, DRV, mem=[('x', 0x3A, [NF]), ('y', TB, ramp), ('x', S.LEN, [LENP]), ('x', S.PREV, [0]), ('x', S.MAGIC_AT, [S.MAGIC]),
                                 ('x', G.BUF, [0] * 2 * NF)], maxins=3_000_000, dumps=[('x', S.SMB, 0x20), ('x', G.BUF, 2 * NF)])
        return (lambda k: r[('x', S.SMB)][k - S.SMB]), r[('x', G.BUF)][0::2]
    sfx, efx = int(0.1 * 0x800000), int(0.3 * 0x800000)
    S0, E0 = (LENP * sfx) >> 23, (LENP * efx) >> 23
    st, _ = play(["call", "call", setx(S.STATE, 0), "call"], sf=sfx, ef=efx, mode=2)
    check(st(S.PLAY) == 0, "HOLD: a loop (mode 2) stops when the pad is released")
    st, _ = play(["call", "call", setx(S.STATE, 0), "call"], sf=sfx, ef=efx, mode=0, cmd=2)
    check(st(S.PLAY) == 0, "HOLD: a forced loop (Shift) stops when the pad is released")
    st, _ = play(["call", setx(S.STATE, 0), "call"], mode=0)
    check(st(S.PLAY) == 1, "HOLD: a one-shot goes on after the release")
    for mode, cmd, what in ((2, 1, "loop"), (1, 1, "gate"), (0, 2, "forced loop")):
        st, out = play(["call", "call"], sf=sfx, ef=sfx, mode=mode, cmd=cmd)
        check(st(S.PLAY) == cmd and out == [0] * NF and st(S.PI) == TB + S0, f"HOLD, start = end ({what}): still playing, silent, parked at S (PI = S + {st(S.PI) - TB - S0})")
        st, out = play(["call", "call", setx(S.EF, efx), "call"], sf=sfx, ef=sfx, mode=mode, cmd=cmd)
        want = [ramp[S0 + (i % (E0 - S0))] for i in range(NF)] if mode != 1 else ramp[S0:S0 + NF]
        check(st(S.PLAY) == cmd and out == want, f"HOLD, start = end, then end moved ({what}): plays again from S")
    st, out = play(["call"], sf=sfx, ef=sfx, mode=0)
    check(st(S.PLAY) == 0, "HOLD, start = end, one-shot: stops")


def main(img, man):
    fails = emu_sc34_dsp.main(img, man)
    gc.collect()
    fails += emu_sc34.main(img, man)
    gc.collect()
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    check(man["report"]["sc17"].get("loophold") is True, "manifest: loophold")
    hold_tests(check)
    dl = {k: int(v, 16) for k, v in man["report"]["sc16"]["dsp_labels"].items()}
    sp = dsp_program(img); P0 = [int.from_bytes(sp[i:i + 3], 'big') for i in range(0, len(sp), 3)]
    w, _ = S.code(dl["smp_post"], v34=True)
    blk = P0[dl["smp_post"]:dl["smp_post"] + len(w)]
    slots = [S.HIGH_SLOT0 + k * S.MAXLEN for k in range(S.SLOTN)]
    check(blk == w, "the image's sampler code = code(HIGH)")
    check(blk.count(S.HIGH_BASE) >= 3 and all(blk.count(a) == 1 for a in slots) and slots[-1] + S.MAXLEN <= 0x1000000,
          f"base $E80000 ({blk.count(S.HIGH_BASE)} uses), slots {', '.join('$%X' % a for a in slots)}, the last ends at ${slots[-1] + S.MAXLEN:X}")
    S.HIGH = False
    wlow, _ = S.code(dl["smp_post"], v34=True)                                  # the same code with SC34's addresses
    S.HIGH = True
    old = {S.BASE} | {S.SLOT0 + k * S.MAXLEN for k in range(S.SLOTN)}
    diff = [(o, n) for o, n in zip(wlow, w) if o != n]
    check(len(wlow) == len(w) and diff and all(o in old and not 0x580000 <= n < 0xE80000 for o, n in diff) and sum(o in old for o in wlow) == len(diff),
          f"only the {len(diff)} buffer addresses differ from the same code at SC34's addresses, every one moved out of the pack sample memory ($580000..$E7FFFF)")
    check(len(P0) <= 0x4000, f"the DSP program ends at P:${len(P0):x}")
    print("SC34.1 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
