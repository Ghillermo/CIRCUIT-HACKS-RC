"""Circuit Tracks 4486 - RC0.9.2 (files and marker R0902) = RC0.9.1 + tools/setupfix.py: Synth 1 / 2 can be chosen in the Setup view again (srcview's «second press» took them for Preset there)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_r0901 as B  # noqa: E402
import linein3  # noqa: E402
import setupfix  # noqa: E402

NAME = "R0902"


def extra(img, report):
    import build_shared_channels as sc
    B.extra(img, report)
    ext = (len(img) + 0x08010000 + 3) & ~3
    labels, code, prev = setupfix.install(img, report, ext)
    report["setupfix"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, prev={k: hex(v) for k, v in prev.items()},
                              listing=sc.disasm(bytes(code), ext))


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
