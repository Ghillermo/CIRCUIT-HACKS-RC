"""Circuit Tracks 4486 - S557D (DIAGNOSTIC; the user, 2026-11-13: more automation lanes for the own synth need ~3.2 KB of RAM and the ARM has none
free: is the DSP's external Y $337000-$33FFFF still untouched?) = Beta 5.57 + rdiag (DSPX: the PC reads external Y with tools/dspsnap.py) in the
dspz gap, in front of the black box on the SysEx entry (rdiag takes every F0 7D 43 54 message: the black box and the firmware query do not answer
over USB in this build).  See firmware/s557d/PRUEBA.md."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc57_2 as S  # noqa: E402
import linein3  # noqa: E402
import morphz  # noqa: E402
import tabpack  # noqa: E402

NAME = "S557D"
import rdiag  # noqa: E402
rdiag.DSPX = True
rdiag.DELETE = False


class _RD:
    @staticmethod
    def install(img, report, base):
        """rdiag in front of the black box: its 'not ours' path (pop, the stock's prologue, b.w HOOK_CONT) goes to c_bbsx instead."""
        import ct_fw
        from thumb import b_w
        BASE = ct_fw.APP_BASE
        H = rdiag.HOOK
        bb = int(report["blackbox"]["labels"]["c_bbsx"], 16)
        assert bytes(img[H - BASE:H - BASE + 4]) == b_w(H, bb)
        img[H - BASE:H - BASE + 4] = rdiag.PROLOGUE
        n0 = len(img)
        labels, code = rdiag.install(img, report, base)
        seg = bytes(code); k = seg.find(rdiag.PROLOGUE)
        at = base + k
        assert k >= 0 and seg.find(rdiag.PROLOGUE, k + 1) < 0 and seg[k + 4:k + 8] == b_w(at + 4, rdiag.HOOK_CONT)
        new = b_w(at, bb) + bytes.fromhex("00bf00bf")
        img[n0 + k:n0 + k + 8] = new                                             # (the code sits at the end until dspz.add moves it)
        code = bytearray(code); code[k:k + 8] = new
        return labels, bytes(code), {}


def extra(img, report):
    import dspz
    S.extra(img, report)
    dspz.add(img, report, "rdiag", _RD)
B = S.B


if __name__ == "__main__":
    tabpack.use()
    import patmut
    patmut.use_v2()
    S.S.S.S.S.S.S.S.S.S.S.S.S.room()
    S.S.S.S.S.S.S.S.S.S.S.S.cpu()
    morphz.use_four()
    morphz.use_slow()
    morphz.use_rrfix()
    morphz.use_newstop()
    morphz.use_fastatk()
    import fmmap
    fmmap.use_lrram()
    patmut.use_lrram()
    import knobhold
    knobhold.use_freeze()
    import blackbox
    blackbox.use_v2()
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
