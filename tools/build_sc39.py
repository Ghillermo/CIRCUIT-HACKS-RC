"""Circuit Tracks 4486 — SC39 = SC38.9 + tools/mutate39.py (the user, 2026-10-11 / 12): random-mutate, row 4 of the stock probability view (pads 25-32, peach)
sets a per-step chance of the step's notes moving an octave and / or to another note of the scale when they play (written into the step while recording);
+ packio.use_pmode2() (the user, 2026-10-12: «el color purple se muestra parpadeando en vez de fijo»): glide patches in steady colour codes."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc38_9 as B  # noqa: E402  (configures everything as SC38.9)
import mutate39  # noqa: E402
import packio  # noqa: E402
import linein3  # noqa: E402
packio.use_pmode2()

NAME = "SC39"


def extra(img, report):
    B.extra(img, report)
    ext = (len(img) + 0x08010000 + 3) & ~3
    labels, code = mutate39.install(img, report, ext)
    import build_shared_channels as sc
    report["mutate39"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, listing=sc.disasm(bytes(code), ext))


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
