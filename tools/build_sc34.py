"""Circuit Tracks 4486 — SC34 = SC33 + the corrections asked on 2026-10-08:
  * the captured sample can be assigned to any bottom pad (26-31) of Master FX / the FX view like the other effects (pad 7 held + the pad), each slot with its own copy
    of pitch / mode / start / end; a slot of the sample plays it (gate while held, Shift = loop) (build_sc17.use_sampler2);
  * pad 32 records in the FX view too (pad 31 stays an assignable slot);
  * K2 of the sample shows the mode by colour: one-shot yellow, gate green, loop blue;
  * a drum sample can be replaced by the capture: drum Preset view, Shift + a pad (blinks: confirm?), Shift + the same pad again = confirmed (tools/drumrep.py;
    DSP: sampler_dsp.V34, CMD 4: the capture is copied into one of 8 slots and the sample table entry points at it); volatile.
Everything up to SC33 is unchanged (tools/verify_builds.py).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import sampler_dsp  # noqa: E402
sampler_dsp.V34 = True                # before build_sc33 installs the DSP code
import build_sc33 as b33  # noqa: E402
import build_sc17  # noqa: E402
import drumrep  # noqa: E402
import linein3  # noqa: E402
build_sc17.use_sampler2()

NAME = "SC34"


def extra(img, report):
    b33.extra(img, report)
    ext = (len(img) + 0x08010000 + 3) & ~3
    labels, code, prev = drumrep.install(img, report, ext)
    report["drumrep"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, **prev,
                             listing=b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.sc.disasm(bytes(code), ext))


if __name__ == "__main__":
    b5 = b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
