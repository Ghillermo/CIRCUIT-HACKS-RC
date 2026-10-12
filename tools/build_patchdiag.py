"""Circuit Tracks 4486 — PATCHD (DIAGNOSTIC, «patchdiag») = SC38.9 + the remote SysEx diagnostics (tools/rdiag.py: ping, ARM memory, SD item info / read / write, DSP reads
(DSPX, read-only, as SC342D); no delete), driven from the PC with tools/ctremote.py and tools/padtest.py: is the 172-byte padding after every synth patch (Patches/NN_PATCHBANK.cpb,
records of 512 bytes) kept by the stock patch saves, the pack loads and a power cycle?  Ping version = $35D8 + $10 (DSPX).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc38_9 as B  # noqa: E402  (configures everything as SC38.9)
import rdiag  # noqa: E402
import linein3  # noqa: E402
rdiag.DSPX = True                    # explicit (an earlier builder of the chain already sets it at import)
rdiag.DELETE = False

NAME = "PATCHD"


def extra(img, report):
    B.extra(img, report)
    ext = (len(img) + 0x08010000 + 3) & ~3
    labels, code = rdiag.install(img, report, ext)
    import build_shared_channels as sc
    report["rdiag"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, listing=sc.disasm(bytes(code), ext))


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
