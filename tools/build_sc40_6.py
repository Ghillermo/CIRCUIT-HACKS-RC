"""Circuit Tracks 4486 — SC40.6 = SC40.5 with patchain.use_v2() (the user, 2026-10-14): what Shift offers lights up yellow, the chain edit is shown on Octave up,
the scenes with rules and the tracks that run one are marked in the Mixer view, Shift + pads 9-16 there = the repeats of the current scene.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc40_4 as B  # noqa: E402  (configures everything as SC40.4)
import patchain  # noqa: E402
import linein3  # noqa: E402

NAME = "SC40.6"
patchain.use_v2()


def extra(img, report):
    B.extra(img, report)
    ext = (len(img) + 0x08010000 + 3) & ~3
    labels, code, prev = patchain.install(img, report, ext)
    import build_shared_channels as sc
    report["patchain"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, prev={k: hex(v) for k, v in prev.items()},
                          listing=sc.disasm(bytes(code), ext))


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
