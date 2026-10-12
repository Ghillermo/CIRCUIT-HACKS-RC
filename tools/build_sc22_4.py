"""Circuit Tracks 4486 — SC22.4 = SC22.3 + distinct pad colours and a new order of the toggle pads in the MIDI Preset view.

Bottom row, left to right: pad 25 free (CC editor later), pad 26 patch flip (stock colours), pad 27 oscillator source (green), pad 28 oscillator edit (the same green), pad 29 VCF / VCA mode (orange).
Everything else is SC22.3.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import vcf21  # noqa: E402
import build_sc22_3 as b223  # noqa: E402
import linein3  # noqa: E402
vcf21.use_colors()
vcf21.use_layout()
import build_sc06  # noqa: E402
build_sc06.PF_PAD = vcf21.PAD_FLIP        # the patch flip moves to pad 26 (index 25)

NAME = "SC22.4"

if __name__ == "__main__":
    linein3.main(NAME, b223.b22.b182.b18.b6.b5.build, b223.b22.b182.b18.b6.b5.s15, sys.argv[1:], extra=b223.b22.b214.b213.extra)
