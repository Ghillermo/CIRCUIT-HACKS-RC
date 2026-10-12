"""Circuit Tracks 4486 — SC34.1 = SC34 with the captured-sample buffer moved out of the pack sample memory (sampler_dsp.HIGH):
  * SC35D2: the pack samples are loaded back to back from Y:$580000 (limit $E80000), so SC33 / SC34's capture at $600000 and the replacement slots from $640000
    overwrote pack samples; SC35D3: $E80000-$FFFFFF is real memory (no mirror) that nothing writes;
  * the capture goes to Y:$E80000 and the 8 replacement slots to $EA8800..$FEC7FF;
  * corrections asked on 2026-10-08: a loop (mode loop, or Shift + the pad) plays only while the pad is held (build_sc17.use_loophold + sampler_dsp.HOLD); start =
    end (nothing to play) no longer kills a held / looping playback: it goes silent and comes back when start != end again.
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

NAME = "SC34.1"


def extra(img, report):
    b33.extra(img, report)
    ext = (len(img) + 0x08010000 + 3) & ~3
    labels, code, prev = drumrep.install(img, report, ext)
    report["drumrep"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, **prev,
                             listing=b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.sc.disasm(bytes(code), ext))


if __name__ == "__main__":
    b5 = b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
