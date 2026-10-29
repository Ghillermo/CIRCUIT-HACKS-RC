"""SC49.7 DSP test (gentab): the core-0 tables built at DSP start, on the dsp56kEmu interpreter with the real core-0 program.

    python tools/emu_gentab_dsp.py BUILD.bin manifest.json [PREVIOUS.bin PREVIOUS_manifest.json]
  * P:$10B calls init2; init2 = the tables, then sc_init (r0 = $2028 on return, as before);
  * P:GEN_<table>.. after init2 = gentab.tables()'s generated tables (the DSP's arithmetic modelled word for word), each within its bound of the
    exact table: TINC / TEXP 1 LSB (the top octave exact), TLFO / TF 0.1 %, TDEC 32 LSB (the top octave exact), TATK 0.01 %;
  * the program ends before GEN_TATK; it is shorter than the previous build's (if given), which has the exact tables at its labels.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
import dsp56 as D  # noqa: E402
import gentab as G  # noqa: E402

TABS = ("TATK", "TDEC", "TF", "TINC", "TEXP", "TLFO")
BOUND = dict(TINC=("lsb", 1), TEXP=("lsb", 1), TLFO=("rel", 0.001), TF=("rel", 0.001), TDEC=("lsb", 32), TATK=("rel", 0.0001))
TOP = dict(TINC=117, TEXP=37, TDEC=52)                  # from here on the generated table = the exact one (the seeds)


def prog(img):
    sp = dsp_program(img)
    return [int.from_bytes(sp[i:i + 3], 'big') for i in range(0, len(sp), 3)]


def main(img, man, prev=None, pman=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    P = prog(img)
    dl = {k: int(v, 16) for k, v in man["report"]["sc16"]["dsp_labels"].items()}
    at = {k: getattr(G, "GEN_" + k) for k in TABS}
    n = {k: getattr(G, "N_" + k) for k in TABS}
    check(P[0x10B:0x10D] == D.jsr(dl["init2"]), f"P:$10B = jsr init2 (${dl['init2']:x})")
    check(len(P) <= G.GEN_TATK, f"the program ends at ${len(P):x}, before the tables (${G.GEN_TATK:x})")
    res, ran = run(P + [0] * (0x4000 - len(P)), dl["init2"], dumps=[('p', at[k], n[k]) for k in TABS], regs_code=[], maxins=400_000)
    check('pc=00' in ran, f"init2 returns ({ran[:80]})")
    tabs = G.tables()
    for k in TABS:
        exact, model = tabs[k]
        got = res[('p', at[k])]
        check(got == model, f"{k} as gentab.tables() models it ({sum(1 for a, b in zip(got, model) if a != b)} of {n[k]} words differ"
              + (f", first at {next(i for i, (a, b) in enumerate(zip(got, model)) if a != b)}: {got[next(i for i, (a, b) in enumerate(zip(got, model)) if a != b)]:#x} / "
                 f"{model[next(i for i, (a, b) in enumerate(zip(got, model)) if a != b)]:#x}" if got != model else "") + ")")
        kind, bnd = BOUND[k]
        err = max(abs(a - b) for a, b in zip(got, exact)) if kind == "lsb" else max(abs(a - b) / b for a, b in zip(got, exact) if b)
        top = k not in TOP or got[TOP[k]:] == exact[TOP[k]:]
        check(err <= bnd and top, f"{k} within {bnd}{' LSB' if kind == 'lsb' else ''} of the exact table ({err:.6g})" + (", its top octave exact" if k in TOP else ""))
    if prev:
        Pp = prog(Path(prev).read_bytes())
        dp = {k: int(v, 16) for k, v in pman["report"]["sc16"]["dsp_labels"].items()}
        check(all(Pp[dp[k]:dp[k] + n[k]] == tabs[k][0] for k in TABS), "the previous build: the exact tables in its program")
        check(len(Pp) - len(P) > 0, f"the program {len(Pp) - len(P)} words shorter than the previous build's (${len(Pp):x} -> ${len(P):x})")
    print(f"{man.get('name', 'build')} GENTAB DSP RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text()), a[2] if len(a) > 2 else None,
                       json.loads(Path(a[3]).read_text()) if len(a) > 3 else None) else 0)
