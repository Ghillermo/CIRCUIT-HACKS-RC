"""Circuit Tracks 4486 — SC38 = SC37.9 + tools/mixshift.py (the user, 2026-10-11): in the Mixer view, levels page, Shift + a knob right = that track's level
to 100, left = 0 (Shift + knob had no function of its own there; the pan page, Clear + knob and Master FX are left as they were)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc37_9 as B9  # noqa: E402  (configures everything as SC37.9)
import mixshift  # noqa: E402
import linein3  # noqa: E402

NAME = "SC38"


def extra(img, report):
    B9.extra(img, report)
    ext = (len(img) + 0x08010000 + 3) & ~3
    labels, code, prev = mixshift.install(img, report, ext)
    dis = B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.sc.disasm
    report["mixshift"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, prev=hex(prev), listing=dis(bytes(code), ext))


if __name__ == "__main__":
    b5 = B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
