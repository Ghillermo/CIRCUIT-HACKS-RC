"""Circuit Tracks 4486 — SC18 = SC17.8 + chromatic drum pitch recorded only on its step + drum knob controls.

See tools/drums18.py.  Everything up to SC17.8 is unchanged (tools/verify_builds.py).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ct_fw  # noqa: E402
import build_sc17_6 as b6  # noqa: E402
import build_sc17 as s17  # noqa: E402
import build_shared_channels as sc  # noqa: E402
import linein3  # noqa: E402
import drums18  # noqa: E402

BASE = ct_fw.APP_BASE
NAME = "SC18"
s17.use_songptr()
s17.use_clearpad()
linein3.FX_GAIN_SHIFT = 3
import build_sc16 as s16  # noqa: E402
drums18.install_dsp(s16)
s16.CODE_P_END = 0x3800               # SC18: the program grows past $3000 (core-0 program RAM is >= 16K words with MS = 1)


def extra(img, report):
    stock = Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin"
    st = stock.read_bytes()
    def text(addr, n): return "|".join(sc.disasm(bytes(st[addr - BASE:addr - BASE + n]), addr))
    ext = (len(img) + BASE + 3) & ~3
    labels, code = drums18.install_arm(img, report, ext, text)
    drums18.patch_dsp(img, report)
    DD = s16.DRUMS_DD
    dl = report["sc16"]["dsp_labels"]
    report["sc18"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()},
                          listing=sc.disasm(bytes(code), ext), dsp_block=hex(DD.DB), dsp_stride=DD.STRIDE,
                          dsp_labels={k: dl[k] for k in ("dctl", "dtrig", "dstage", "TEXP", "TLFO", "TF", "TCR", "TATK", "TDEC", "TCOMB") if k in dl})


if __name__ == "__main__":
    linein3.main(NAME, b6.b5.build, b6.b5.s15, sys.argv[1:], extra=extra)
