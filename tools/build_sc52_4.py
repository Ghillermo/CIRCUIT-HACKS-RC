"""Circuit Tracks 4486 - SC52.4 = SC52.3 + the two oscillators re-laid out and cleaner (the user, 2026-11-06): vcf21.use_osc4 (OSC 2's page K1 ratio,
K2 fine, K3 wave, K4 shape, K5 FM, K6 ring, K7 sync / bitwise, K8 mix; OSC 1's page pitch / fine / wave / shape and the modulations), FM with its
centre (right OSC 2 -> OSC 1, left OSC 1 -> OSC 2, the ends 50 / 50), vcf21_dsp.use_osc4 (hard sync with its sweep, the polyBLEP with FM, the FM
curve, the bitwise smoothing, OSC 2's ratio in poly), tools/oscmod.py (LFO / env -> FM, RING, MIX on OSC 1's K5 / K6 / K8) and tools/autolane.py
(a knob without a lane, recording: the first empty lane takes it)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc52_3 as S  # noqa: E402
import linein3  # noqa: E402

NAME = "SC52.4"
B = S.B


IN_HOLE = False                              # SC52.6: oscmod and autolane in the hole (3.8 KB free there)


def at_end(img, report, name, mod):
    """an ARM module at the image's end (the dspz gaps are full)"""
    import ct_fw
    import build_shared_channels as sc
    base = ct_fw.APP_BASE + ((len(img) + 3) & ~3)
    n0 = len(img)
    labels, code, prev = mod.install(img, report, base)
    assert len(img) <= 0x70000, f"{name}: the image is full ({len(img):#x})"
    report[name] = dict(arm_start=hex(base), labels={k: hex(v) for k, v in labels.items()}, prev={k: hex(v) for k, v in prev.items()},
                        listing=sc.disasm(bytes(code), base))
    return labels


def extra(img, report):
    S.extra(img, report)
    import oscmod
    import autolane
    import dspz
    import hole
    if IN_HOLE: hole.add(img, report, "oscmod", oscmod)         # (SC52.6) the old DSP blocks' hole: room at the image's end for what grows
    else: at_end(img, report, "oscmod", oscmod)
    dspz.add(img, report, "oscmod2", oscmod.Patch)            # the patch's part
    if IN_HOLE: hole.add(img, report, "autolane", autolane)
    else: dspz.add(img, report, "autolane", autolane)


import vcf21  # noqa: E402
vcf21.use_osc4()
import vcf21_dsp  # noqa: E402
vcf21_dsp.use_osc4()
import psave  # noqa: E402
import xpatch  # noqa: E402
psave.XLEN = xpatch.XLEN = 171               # + oscmod's block (padding + 163..170)
import wtui  # noqa: E402
wtui.PJ_N = wtui.REC_N + 8                   # the project's block carries oscmod's too
import engsave  # noqa: E402
engsave.SIG = 0xE8                           # FM's centre moved: the saved state of an older firmware is not taken (the defaults)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
