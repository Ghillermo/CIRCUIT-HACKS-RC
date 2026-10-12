"""Circuit Tracks 4486 — SC36.1 = SC36 + (the user, 2026-10-09):
  * build_sc17.use_glitch2(): the Glitch can be assigned to the other bottom pads of Master FX like any effect (pad 31 held + a bottom pad), with a copy of K1..K4;
  * vcf21.use_fxseq2(): the FX step sequencer picks the bottom row (pair value 0 = nothing, 1..6 = the slots of pads 26..31, one value per knob turn) and its knobs
    show the colour of the slot they pick;
  * no remote diagnostics (tools/rdiag.py, the hook on the incoming SysEx): nothing of ours on the USB protocol (the user, 2026-10-09).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc36 as B  # noqa: E402  (configures everything as SC36)
import build_sc17  # noqa: E402
import vcf21  # noqa: E402
import linein3  # noqa: E402
import packio  # noqa: E402
import granular_dsp  # noqa: E402
build_sc17.use_glitch2()
vcf21.use_fxseq2()

NAME = "SC36.1"


def extra(img, report):
    """SC35's extra without rdiag (packio stays), then the core-1 block of SC36."""
    B.B.b342.extra(img, report)
    dis = B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.sc.disasm
    ext = (len(img) + 0x08010000 + 3) & ~3
    labels, code, prev = packio.install(img, report, ext)
    report["packio"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, prev={k: hex(v) for k, v in prev.items()},
                            listing=dis(bytes(code), ext))
    report["granular"] = granular_dsp.patch_core1(img)


if __name__ == "__main__":
    b5 = B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
