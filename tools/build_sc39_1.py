"""Circuit Tracks 4486 — SC39.1 = SC39 + tools/mpatch.py (the user, 2026-10-12): patches of the MIDI tracks' own synth, 64 slots of the pack (rows 2-3 of the
Preset view of MIDI 1 / 2, four pages with Octave down / up; a pad loads, Duplicate + pad saves, Clear + pad empties), kept in the padding of the pack's
synth patches."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc39 as B  # noqa: E402  (configures everything as SC39)
import mpatch  # noqa: E402
import vcf21  # noqa: E402
import linein3  # noqa: E402
vcf21.use_resetview()
vcf21.use_grsrc()

NAME = "SC39.1"


def extra(img, report):
    B.extra(img, report)
    ext = (len(img) + 0x08010000 + 3) & ~3
    labels, code, prev = mpatch.install(img, report, ext)
    import build_shared_channels as sc
    report["mpatch"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, prev={k: hex(v) for k, v in prev.items()},
                            listing=sc.disasm(bytes(code), ext))


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
