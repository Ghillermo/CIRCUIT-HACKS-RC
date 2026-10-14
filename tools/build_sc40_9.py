"""Circuit Tracks 4486 - SC40.9 = SC40.8 + (the user, 2026-10-14, after SC39.7-SC40.8 on the unit):
  * patchain.use_v3(): one chain mode for the whole project, remembered by every scene; Clear of a pattern also clears its play order;
  * playmode.use_drums(): Nudge and the fractal / deconstructed orders on the drum tracks;
  * tools/fxsess.py: the 20 top-row knobs of Master FX and the compressor's attack / release saved with the project; the compressor on K7 / K8
    of the Sidechain view (out of the Setup view); Record in the Setup view = the internal MIDI routes are recorded;
  * persist19.GFX_SESSION: the slot assignments of Master FX loaded from every project that has them;
  * vcf21.use_engfix() / build_sc17.use_engfix(): the step-drummer, the FX sequencer, the stretch and the armed capture read their own track;
  * vcf21.use_fxseq4(): the selector knob of the FX sequencer three times slower."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc40_8 as B  # noqa: E402  (configures everything as SC40.8)
import build_sc17  # noqa: E402
import fxsess  # noqa: E402
import linein3  # noqa: E402
import patchain  # noqa: E402
import persist19  # noqa: E402
import playmode  # noqa: E402
import vcf21  # noqa: E402

NAME = "SC40.9"
patchain.use_v3()
playmode.use_drums()
vcf21.use_engfix()
vcf21.use_fxseq4()
build_sc17.use_engfix()
persist19.GFX_GLOBAL, persist19.GFX_SESSION = False, True


def extra(img, report):
    B.extra(img, report)
    ext = (len(img) + 0x08010000 + 3) & ~3
    labels, code, prev = fxsess.install(img, report, ext)
    import build_shared_channels as sc
    report["fxsess"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, prev={k: (hex(v) if isinstance(v, int) else v) for k, v in prev.items()},
                            listing=sc.disasm(bytes(code), ext))


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
