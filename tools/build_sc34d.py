"""Circuit Tracks 4486 — SC34D (DIAGNOSTIC) = SC34 + our own small file next to each session on the SD card (tools/sidecar34.py).

Saving a session also writes "<NN>_SC34D.bin" next to "<NN>_SESSION.ncs" (16 bytes: "SC34DTST", saves, loads); loading one counts a load in it.  Through the stock file
class, in the stock storage task, after the stock has closed its file; the stock files are not touched.  Check with the card in a PC (see firmware/sc34d/PRUEBA.md).
It decides how SC35 saves the captured sample with the project.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc34 as b34  # noqa: E402
import sidecar34  # noqa: E402
import linein3  # noqa: E402

NAME = "SC34D"


def extra(img, report):
    b34.extra(img, report)
    ext = (len(img) + 0x08010000 + 3) & ~3
    labels, code = sidecar34.install(img, report, ext)
    report["sidecar34"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()},
                               listing=b34.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.sc.disasm(bytes(code), ext))


if __name__ == "__main__":
    b5 = b34.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
