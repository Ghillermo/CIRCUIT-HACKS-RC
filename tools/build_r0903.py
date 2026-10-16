"""Circuit Tracks 4486 - RC0.9.3 (files and marker R0903) = RC0.9.2 + the settings save of the mod deferred to the transport stopped (tools/lazysave.py): the stutter of the delay while turning the MIDI engine's knobs / toggling its modes (the user, 2026-10-15)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_r0902 as B  # noqa: E402
import linein3  # noqa: E402
import lazysave  # noqa: E402

NAME = "R0903"


def extra(img, report):
    import build_shared_channels as sc
    B.extra(img, report)
    ext = (len(img) + 0x08010000 + 3) & ~3
    labels, code, prev = lazysave.install(img, report, ext)
    report["lazysave"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, prev={k: hex(v) for k, v in prev.items()},
                              listing=sc.disasm(bytes(code), ext))


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
