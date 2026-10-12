"""SC38.7 ARM tests (live RAM dump, the real routes: the MIDI 1 Preset view's pads and knobs, the Clear button, the DSP service tick): Clear + pad 27 = every
value of the track's engine back to its default (vcf21.use_resetall).

    python tools/emu_sc38_7.py SC38.7.bin SC38.7_manifest.json SC38.6.bin SC38.6_manifest.json
  * MIDI 1 with the oscillator: values changed on the VCA-VCF page, OSC1 (with and without Shift) and OSC2 (volatile codes);
  * Clear + pad 27: codes 1..26 = DEFAULTS, codes 27..34 = DEFAULTS_V2, the engine (mode on, oscillator source, signature) unchanged, the values go to the
    DSP again (mailbox), the settings saved;
  * pad 27 without Clear: the engine steps on as before (VA-drum);
  * the previous build: Clear + pad 27 steps the engine and keeps the values.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc36 as T36  # noqa: E402  (configures vcf21 as SC36)
import vcf21_dsp as VD  # noqa: E402
from emu_sc17_6 import MGR  # noqa: E402

V, E20 = T36.V, T36.E20


def run(img, man):
    e = E20(img, man)
    for _ in range(30): e.vtick()
    pad = lambda p: (e.padr(p), e.rel(p))
    def gval(code, t=0):
        e.call(e.vl["c_vvaddr"], t, code); return struct.unpack("b", bytes([e.r8(e.uc.reg_read(UC_ARM_REG_R0))]))[0]
    def mbox(n=60):
        got = {}
        for _ in range(n):
            for w, ad in e.vtick():
                if ad == VD.VB0: got[(w >> 16) & 0x7F] = w & 0xFFFF
        return got
    clear = lambda on: e.call(0x08033320 if on else 0x0803381A, MGR, 23, maxins=900000)
    e.btn(2); e.track(2); e.btn(8)
    pad(V.PAD_OSC); pad(V.PAD_OSC); mbox()                                       # line in -> the oscillator
    out = {"engine0": (e.tailb(V.O_FLAGS), e.tailb(V.O_SIG))}
    for pg, knobs in ((0, (0, 2, 5)), (1, (0, 3, 6)), (2, (0, 1, 4))):          # the page row: VCA-VCF, OSC1, OSC2
        pad(pg); mbox(5)
        for k in knobs: e.knob_raw(k, 23); e.knob_raw(k, 11, shift=True)
    mbox(10)
    out["before"] = [gval(c) for c in range(1, 35)]
    e.saves.clear(); clear(True); pad(V.PAD_OSC); clear(False)
    out["after"] = [gval(c) for c in range(1, 35)]
    out["engine1"] = (e.tailb(V.O_FLAGS), e.tailb(V.O_SIG)); out["saved"] = bool(e.saves)
    out["sent"] = mbox(120)
    pad(V.PAD_OSC); mbox(); out["engine2"] = (e.tailb(V.O_FLAGS), e.tailb(V.O_SIG))
    del e; gc.collect()
    return out


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    o = run(img, man)
    want = [((v + 128) & 0xFF) - 128 for v in V.DEFAULTS] + [((v + 128) & 0xFF) - 128 for v in V.DEFAULTS_V2]
    changed = [c for c in range(1, 35) if o["before"][c - 1] != want[c - 1]]
    check(len(changed) >= 8, f"values changed on the three pages ({len(changed)} codes off their default: {changed})")
    bad = [(c, o["after"][c - 1], want[c - 1]) for c in range(1, 35) if o["after"][c - 1] != want[c - 1]]
    check(not bad, f"Clear + pad 27: every code 1..34 back to its default ({bad})")
    check(o["engine1"] == o["engine0"] and o["saved"], f"the engine kept (flags / signature {o['engine0']} -> {o['engine1']}), the settings saved")
    sent = o["sent"]
    check(len([k for k in sent if 1 <= k <= 16 or 22 <= k <= 31]) >= 20, f"the values go to the DSP again ({len(sent)} mailbox codes)")
    check(o["engine2"][1] != o["engine1"][1], f"pad 27 without Clear: the engine steps on (signature {o['engine1'][1]:#x} -> {o['engine2'][1]:#x})")
    q = run(prev, prev_man)
    check(q["engine1"] != q["engine0"] and q["after"] == q["before"], f"SC38.6: Clear + pad 27 stepped the engine ({q['engine0']} -> {q['engine1']}), the values kept")
    print("SC38.7 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
