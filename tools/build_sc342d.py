"""Circuit Tracks 4486 — SC342D (DIAGNOSTIC) = SC34.2 + the remote SysEx diagnostics (tools/rdiag.py with DELETE and DSPX), driven from the PC with
tools/ctremote.py: everything SC35D9 offers (ping, ARM memory, SD item info / read / write / delete) plus the DSP: command 3 reads internal X / Y words, command
8 reads the DSP's external Y memory (the captured sample at Y:$E80000) through the sampler's own block copy into the Y window $3B40.  The way to test the
capture -> SD path of SC35 with the real SC34.2 sampler.  Ping version = $35D8 + 1 + 0x10.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc34_2 as b342  # noqa: E402  (configures sampler_dsp / build_sc17 as SC34.2)
import rdiag  # noqa: E402
import linein3  # noqa: E402
rdiag.DELETE = True
rdiag.DSPX = True

NAME = "SC342D"
b33 = b342.b33


def extra(img, report):
    b342.extra(img, report)
    ext = (len(img) + 0x08010000 + 3) & ~3
    labels, code = rdiag.install(img, report, ext)
    report["rdiag"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()},
                           listing=b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.sc.disasm(bytes(code), ext))


if __name__ == "__main__":
    b5 = b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
