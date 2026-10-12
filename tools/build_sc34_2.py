"""Circuit Tracks 4486 — SC34.2 = SC34.1 + the phrase mode of the Master FX song pointer (build_sc17.use_sp3, the user, 2026-10-09):
  * Shift + a step (pads 9-24) = phrase mode, that step is the start (end = 16); in phrase mode a tap = the end (no retrigger), Shift + another step = a new
    start, Shift + the start or pad 9 (white) = off.  Outside phrase mode the SC32 song pointer is unchanged.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import sampler_dsp  # noqa: E402
sampler_dsp.V34 = True                # before build_sc33 installs the DSP code
sampler_dsp.HIGH = True
sampler_dsp.HOLD = True
import build_sc33 as b33  # noqa: E402
import build_sc17  # noqa: E402
import drumrep  # noqa: E402
import linein3  # noqa: E402
build_sc17.use_sampler2()
build_sc17.use_loophold()
build_sc17.use_sp3()

NAME = "SC34.2"


def extra(img, report):
    b33.extra(img, report)
    ext = (len(img) + 0x08010000 + 3) & ~3
    labels, code, prev = drumrep.install(img, report, ext)
    report["drumrep"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, **prev, **({"clearrep": True} if drumrep.CLEARREP else {}),
                             listing=b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.sc.disasm(bytes(code), ext))


if __name__ == "__main__":
    b5 = b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
