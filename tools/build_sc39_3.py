"""Circuit Tracks 4486 — SC39.3 = SC39.2 + tools/macroed.py (the user, 2026-10-12): the destinations of the synth macros edited on the device, in the source
view of Synth 1 / 2 (pad 32; a knob picks its macro; Octave steps slot / start / end / destination / depth; the pads show the number)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc39_2 as B  # noqa: E402  (configures everything as SC39.2)
import macroed  # noqa: E402
import linein3  # noqa: E402

NAME = "SC39.3"


def extra(img, report):
    B.extra(img, report)
    ext = (len(img) + 0x08010000 + 3) & ~3
    labels, code, prev = macroed.install(img, report, ext)
    import build_shared_channels as sc
    report["macroed"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, prev={k: hex(v) for k, v in prev.items()},
                             listing=sc.disasm(bytes(code[280:]), ext + 280))


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
