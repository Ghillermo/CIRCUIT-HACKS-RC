"""Circuit Tracks 4486 — SC40.1 = SC40 + tools/sckn.py (the user, 2026-10-12): in the Sidechain view K1..K4 = attack, hold, decay and depth of the
side-chain of the note track chosen last there."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc40 as B  # noqa: E402  (configures everything as SC40)
import sckn  # noqa: E402
import linein3  # noqa: E402

NAME = "SC40.1"


def extra(img, report):
    B.extra(img, report)
    ext = (len(img) + 0x08010000 + 3) & ~3
    labels, code, prev = sckn.install(img, report, ext)
    import build_shared_channels as sc
    report["sckn"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, prev={k: hex(v) for k, v in prev.items()},
                          listing=sc.disasm(bytes(code[4:]), ext + 4))


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
