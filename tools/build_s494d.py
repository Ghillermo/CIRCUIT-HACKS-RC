"""Circuit Tracks 4486 - S494D (DIAGNOSTIC) = SC49.4 + tools/rdiag.py with DSPX / DSPW / ITCM / CORE1: what Arrhythmia (llcoolkm, MIT; its review in
RYTHM docs/PORTADO.md) found on the Circuit Rhythm, checked on the Tracks from the PC (tools/ctremote.py): the core's 16 KB of ITCM at address 0 (itfill /
itchk / mem: does anything write it?), DSP core 0 X:$4000-$5FFF (does it exist, is it a mirror, does the stock use it?) and core 1's memory through the
stock read / write with r0 = 1; tools/gatediag.py counts DSP host writes inside a PCM upload's bulk interval (RYTHM's dspgate, measured first).  SC49.4 because it has the flash free (SC50.6: 260 B).  See firmware/s494d/PRUEBA.md."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc49_4 as B  # noqa: E402
import rdiag  # noqa: E402
rdiag.DSPX = True
rdiag.DSPW = True
rdiag.DELETE = False
rdiag.ITCM = True
rdiag.CORE1 = True
import linein3  # noqa: E402

NAME = "S494D"


def extra(img, report):
    B.extra(img, report)
    import build_shared_channels as sc
    ext = (len(img) + 0x08010000 + 3) & ~3
    labels, code = rdiag.install(img, report, ext)
    report["rdiag"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, listing=sc.disasm(bytes(code), ext))
    import gatediag
    ext = (len(img) + 0x08010000 + 3) & ~3
    labels, code = gatediag.install(img, report, ext)
    report["gatediag"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, listing=sc.disasm(bytes(code), ext))


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
