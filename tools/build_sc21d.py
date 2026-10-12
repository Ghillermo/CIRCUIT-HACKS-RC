"""Circuit Tracks 4486 — SC21D (DIAGNOSTIC) = SC20D.1 with the capture meter replaced by a DSP probe and an NRPN monitor (tools/probe21_dsp.py, tools/probe21.py).

Reads only (plus a write -> read back -> restore of a pattern at P:$3800 and above, interrupts masked, see probe21_dsp.py): what is in the DSP program memory above the end of
our code, the shared memory, the OMR and the inter-core status, and the last CC / NRPN received on the MIDI input.  Open the synth source view (Synth 1 / 2 pressed twice) and read
the pads 9-24 (four 4-second pages: facts, OMR, last NRPN, last CC), see firmware/sc21d/PRUEBA.md.  Use with a test project; nothing is saved.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import persist19  # noqa: E402
persist19.FIX_LOCK = True            # before persist19.install builds the code (main time)
import build_sc19_1 as b191  # noqa: E402  (applies the SC19 / SC19.1 options)
import build_sc16  # noqa: E402
import linein3  # noqa: E402
import srcview  # noqa: E402
import probe21  # noqa: E402
import probe21_dsp  # noqa: E402
linein3.N_MODES = 7                  # as SC20D: modes 0-4 + delay / reverb return
b191.b182.b18.b6.b5.s15.N_MODES = 7
linein3.FX_GAIN_SHIFT = 3
linein3.METER = True                 # the SC20D capture (its words Y:$3B00..$3B02 stay unused)
srcview.METER = True                 # rows 2 / 3 of the source view belong to the display of the probe
probe21_dsp.install_dsp(build_sc16)

NAME = "SC21D"
b182 = b191.b182


def extra(img, report):
    b191.extra(img, report)
    st = (Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    def text(addr, n): return "|".join(b182.b18.sc.disasm(bytes(st[addr - b182.b18.BASE:addr - b182.b18.BASE + n]), addr))
    probe21_dsp.patch_dsp(img, report)
    ext = (len(img) + b182.b18.BASE + 3) & ~3
    labels, code = probe21.install(img, report, ext, text)
    report["probe21"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, yr=hex(probe21.YR), tail=hex(probe21.TAIL),
                             listing=b182.b18.sc.disasm(bytes(code), ext))


if __name__ == "__main__":
    linein3.main(NAME, b182.b18.b6.b5.build, b182.b18.b6.b5.s15, sys.argv[1:], extra=extra)
