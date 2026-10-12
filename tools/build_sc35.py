"""Circuit Tracks 4486 — SC35 = SC34.2 + the pack's samples on the SD card (tools/packio.py, the user's design of 2026-10-09):
  * Save (the project) also writes every drum sample replaced by a capture (Shift + pad twice, SC34) into the pack as PCM/NN_PCM.wav, if it fits;
  * drum Preset view: Duplicate held + pad A + pad B = the two samples swapped (files and the sample table);
  * packs view: Clear held + a pad = that pack asked, Clear again within ~5 s = the pack deleted (never the current one; reuse its slot after a restart);
  * build_sc17.SMP_SAVEBIT: a new capture into a slot clears its "saved" bit (X:$3D1E);
  * the remote diagnostics (tools/rdiag.py, with DSPX; no delete) stay in, for tests driven from the PC (tools/ctremote.py).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc34_2 as b342  # noqa: E402  (configures sampler_dsp / build_sc17 as SC34.2)
import build_sc17  # noqa: E402
import packio  # noqa: E402
import rdiag  # noqa: E402
import linein3  # noqa: E402
build_sc17.SMP_SAVEBIT = True
rdiag.DSPX = True

NAME = "SC35"
b33 = b342.b33


def extra(img, report):
    b342.extra(img, report)
    dis = b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.sc.disasm
    ext = (len(img) + 0x08010000 + 3) & ~3
    labels, code, prev = packio.install(img, report, ext)
    report["packio"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, prev={k: hex(v) for k, v in prev.items()},
                            listing=dis(bytes(code), ext))
    ext = (len(img) + 0x08010000 + 3) & ~3
    labels, code = rdiag.install(img, report, ext)
    report["rdiag"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, listing=dis(bytes(code), ext))


if __name__ == "__main__":
    b5 = b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
