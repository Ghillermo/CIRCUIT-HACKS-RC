"""Circuit Tracks 4486 - R211SD (DIAGNOSTIC) = RC2.11S + tools/rdiag.py in the hole, driven from the PC with tools/ctremote.py (info / read /
dump / scan / write / put / del / delpack).  The user, 2026-10-28: «I'm unable to write to slot 0 (internal memory) with Components, I think this
happened after some experimental build corrupted it»; «wont read or write on components, other packs work fine»: list and read what pack 0 holds
through the same storage calls Components uses, find the item that fails, then repair it with the user's go-ahead.  In the hole the tool's calls
return below MOD_START, so rodisk (all packs, as in every S build) lets them through: only what is sent from the PC writes; every other write of
the mod stays refused.  See firmware/r211sd/PRUEBA.md."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import rdiag  # noqa: E402
rdiag.DELETE = True
rdiag.DEL_PACK = True
import build_r211s as B  # noqa: E402
import linein3  # noqa: E402

NAME = "R211SD"


class _RD:                                          # hole.add wants (labels, code, prev)
    @staticmethod
    def install(img, report, base):
        labels, code = rdiag.install(img, report, base)
        return labels, code, {}


def extra(img, report):
    import hole
    B.extra(img, report)
    hole.add(img, report, "rdiag", _RD)
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
