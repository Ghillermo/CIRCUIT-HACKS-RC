"""Circuit Tracks 4486 — SC39.5 = SC39.4 + tools/typeleds.py (the user, 2026-10-12: the type knobs show their type as a colour: the drums' filter
mode and distortion type, the granular note mode) + steady colours where an animated code was used as a steady one (the dim white 0x03 of the
"nothing to clear" pad 8 of Master FX and of the unassigned slots: 0x02)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc39_4 as B  # noqa: E402  (configures everything as SC39.4)
import build_sc17 as S17  # noqa: E402
import packio as PK  # noqa: E402
import typeleds  # noqa: E402
import linein3  # noqa: E402

NAME = "SC39.5"
S17.CLR_DIM = 0x02                    # 0x03 pulses on the device (docs/NOTAS.md, the animated codes)
PK.CLR_DIM = 0x02


def extra(img, report):
    B.extra(img, report)
    ext = (len(img) + 0x08010000 + 3) & ~3
    labels, code, prev = typeleds.install(img, report, ext)
    import build_shared_channels as sc
    report["typeleds"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, prev={k: hex(v) for k, v in prev.items()},
                              listing=sc.disasm(bytes(code[12:]), ext + 12))


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
