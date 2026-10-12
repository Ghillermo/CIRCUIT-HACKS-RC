"""Circuit Tracks 4486 — RC0.3S = RC0.2S + what SC37.6-SC38 add outside the SD card: drumrep.use_clearrep() (the drum replaced by the capture with
Clear + pad, SC37.6), persist19.use_blue7() (the stock blue of Clear + knob on the drums, SC37.9), build_sc17.use_gclear() (Clear + knob in Master FX,
SC37.9) and tools/mixshift.py (Mixer: Shift + knob right = level 100, left = 0, SC38).  The pack fixes of SC37.6-SC37.8 (import guard, source guard,
copies in place, the packs view LEDs) belong to the pack management (packio), which the safer builds leave out.  Marker "RC0.3S"."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_rc0_2s as B  # noqa: E402  (configures everything as RC0.2S)
import drumrep  # noqa: E402
import persist19  # noqa: E402
import build_sc17  # noqa: E402
import mixshift  # noqa: E402
import linein3  # noqa: E402
drumrep.use_clearrep()
persist19.use_blue7()
build_sc17.use_gclear()

NAME = "RC0.3S"


def extra(img, report):
    B.extra(img, report)
    ext = (len(img) + 0x08010000 + 3) & ~3
    labels, code, prev = mixshift.install(img, report, ext)
    dis = B.B.B.S.B36.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.sc.disasm
    report["mixshift"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, prev=hex(prev), listing=dis(bytes(code), ext))


if __name__ == "__main__":
    b5 = B.B.B.S.B36.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
