"""Circuit Tracks 4486 — SC20 = SC19.9 + the VCF / VCA mode for the audio inputs of the MIDI tracks (tools/vcf20.py, tools/vcf20_dsp.py).

Pad 26 (right of the patch flip) of the Preset view of MIDI 1 / MIDI 2 turns the mode of the track on: its audio input (line input 1 / 2, or the reverb / delay return when the
Setup sends it to strip 3 / 4) goes through a bipolar VCF, drive + saturation and a VCA (ADSR by the gate of the track, LFO) before the mixer strip; the 8 knobs are the controls
(Shift = second layer); the track still sends its MIDI as always.  Everything else is SC19.9.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc19_9 as b199  # noqa: E402
import build_sc16  # noqa: E402
import linein3  # noqa: E402
import vcf20  # noqa: E402
import vcf20_dsp  # noqa: E402
vcf20_dsp.install_dsp(build_sc16)

NAME = "SC20"
b182 = b199.b182


def extra(img, report):
    b199.b198.b197.b196.b195.b191.extra(img, report)
    st = (Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    def text(addr, n): return "|".join(b182.b18.sc.disasm(bytes(st[addr - b182.b18.BASE:addr - b182.b18.BASE + n]), addr))
    vcf20_dsp.patch_dsp(img, report)
    ext = (len(img) + b182.b18.BASE + 3) & ~3
    labels, code = vcf20.install(img, report, ext, text)
    report["vcf20"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, listing=b182.b18.sc.disasm(bytes(code), ext),
                           tail=hex(vcf20.TAIL), vb0=hex(vcf20_dsp.VB0))


if __name__ == "__main__":
    linein3.main(NAME, b182.b18.b6.b5.build, b182.b18.b6.b5.s15, sys.argv[1:], extra=extra)
