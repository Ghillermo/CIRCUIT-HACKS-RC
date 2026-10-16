"""Circuit Tracks 4486 - SC41.5 = SC41.4 + tools/pgmch.py: the program changes of the project on a listen channel and an output channel chosen in the Setup view (pads 29 / 30, then a channel pad; 16 by default), those received sent again on the output channel (the user, 2026-10-14) + tools/setupfix.py: Synth 1 / 2 can be chosen in the Setup view again."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc41_4 as B  # noqa: E402
import linein3  # noqa: E402
import pgmch  # noqa: E402
import setupfix  # noqa: E402

NAME = "SC41.5"

def add(img, report, name, mod):
    import build_shared_channels as sc
    ext = (len(img) + 0x08010000 + 3) & ~3
    labels, code, prev = mod.install(img, report, ext)
    report[name] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, prev={k: hex(v) for k, v in prev.items()},
                        listing=sc.disasm(bytes(code), ext))


def extra(img, report):
    B.extra(img, report)
    add(img, report, "setupfix", setupfix)
    add(img, report, "pgmch", pgmch)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
