"""Circuit Tracks 4486 - SC44.9 = SC44.8 + vcf21.use_p4dest() + tools/p4dest.py in the hole (the user, 2026-10-19: «permite reasignar los destinos
de la vista de secuenciables (mismo layout que mod matrix)», «guardados por parche»): knob page 4 of the own engine of MIDI 1 / 2 (the 8 automation
lanes) with its destinations per track: Shift + K1..K8 = the knob's destination (the matrix's list and page colours; a slow knob; Clear held, then
Shift + knob = the default), the lanes record and play the destination; saved with the own-synth patches at padding + 88 (psave.XLEN = 100); and
tools/recinst.py («Add a shortcut to "record instance" into the sequencers … the parameters that differ from the init»; «Hold record + step»,
«Reasignar carriles»): Record held + a step pad of MIDI 1 / 2 = the engine's values that differ from their defaults written into that step's lanes
(a differing parameter without a lane takes one whose parameter does not differ, cleared first)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc44_8 as B  # noqa: E402
import vcf21  # noqa: E402
import p4dest  # noqa: E402
vcf21.use_p4dest(p4dest.RAM)
import psave  # noqa: E402
import xpatch  # noqa: E402
psave.XLEN = xpatch.XLEN = 100                       # the exchange / the copy between packs carry the destinations (padding + 88..99)
import recinst  # noqa: E402
import hole  # noqa: E402
import lfosync  # noqa: E402
import linein3  # noqa: E402

NAME = "SC44.9"


def extra(img, report):
    B.B.extra(img, report)
    hole.add(img, report, "lfosync", lfosync)
    hole.add(img, report, "p4dest", p4dest)
    hole.add(img, report, "recinst", recinst)
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
