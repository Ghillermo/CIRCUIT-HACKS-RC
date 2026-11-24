"""Alpha 7.49 (vcf21.use_famcol): the own synth's knob LEDs in their parameter family's colour (envelope pink, LFO violet, VCA yellow, VCF gold,
FX lemon), both layers; the type knobs keep their per-type colours; the oscillator knobs the track's.
    python tools/emu_famcol.py firmware/a7.49"""
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402  (its import sets vcf21's options)
import vcf21 as V  # noqa: E402


def main(d):
    img = next(Path(d).glob("*.bin")).read_bytes(); man = json.loads((Path(d) / "manifest.json").read_text())
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = X.EP(img, man)
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05]))
    e.btn(2); e.btn(8)
    F = {0: "-", V.FAM_ENV: "env", V.FAM_LFO: "lfo", V.FAM_VCA: "vca", V.FAM_VCF: "vcf", V.FAM_FX: "fx", V.COL_TRACK[0]: "track"}
    def knobs(shift=False):
        if shift: e.shift(True)
        f = X.frame(e)
        if shift: e.shift(False)
        return [F.get(f[60 + k] & 0xFF, hex(f[60 + k] & 0xFF)) for k in range(8)]
    for pg, want, wsh in ((0, ["env", "env", "env", "env", "vcf", "vcf", "lfo", "fx"], ["env", "env", "lfo", "lfo", None, "vca", "track", None]),
                          (4, ["env", "env", "env", "env", "lfo", "lfo", "lfo", "lfo"], ["env", "env", "env", "env", "lfo", "lfo", "env", None])):
        e.r0(e.vl["c_vsetpage"], 0, pg)
        k, ks = knobs(), knobs(True)
        check(k == want, f"page {pg + 1}: {k}")
        check(all(w is None or w == g for w, g in zip(wsh, ks)), f"page {pg + 1} with Shift: {ks} (type knobs free: {[i for i, w in enumerate(wsh) if w is None]})")
    e.r0(e.vl["c_vsetpage"], 0, 1); k = knobs()
    check(k.count("track") >= 3, f"OSC 1 page: the oscillator knobs in the track's colour ({k})")
    del e; gc.collect()
    print(f"{man.get('marker')} FAMCOL RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1]) else 0)
