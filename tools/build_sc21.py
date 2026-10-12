"""Circuit Tracks 4486 — SC21 = SC20.1 with the VCF / VCA mode redone (tools/vcf21.py ARM, tools/vcf21_dsp.py DSP).

Controls (plain / Shift): K1 attack / sustain, K2 release / decay, K3 envelope -> VCA / LFO -> VCA, K4 envelope -> filter / LFO -> filter, K5 filter (bipolar) / filter type
(DJ, band-pass, notch, tilt EQ), K6 resonance / gain (64 = x1, 0 = closed, above: up to +18 dB with saturation), K7 LFO rate (reverse sawtooth only) / FX parameter,
K8 FX amount / FX type (soft, hard, fold, wavefold).  Key tracking (to the filter) and velocity (to the VCA) are always on.  Everything else is SC20.1.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import persist19  # noqa: E402
import build_sc08  # noqa: E402
import build_sc12  # noqa: E402
persist19.CLEAR = True
build_sc08.ROWS3 = True
build_sc12.SWAP = True
import build_sc17  # noqa: E402
build_sc17.SP_PLAY = True
build_sc17.JMP_ON, build_sc17.JMP_OFF = 0x2D, 0x2E
import build_sc19_9 as b199  # noqa: E402
import build_sc16  # noqa: E402
import linein3  # noqa: E402
import vcf21  # noqa: E402
import vcf21_dsp  # noqa: E402
vcf21_dsp.install_dsp(build_sc16)

NAME = "SC21"
b182 = b199.b182


def extra(img, report):
    b199.b198.b197.b196.b195.b191.extra(img, report)
    st = (Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    def text(addr, n): return "|".join(b182.b18.sc.disasm(bytes(st[addr - b182.b18.BASE:addr - b182.b18.BASE + n]), addr))
    vcf21_dsp.patch_dsp(img, report)
    ext = (len(img) + b182.b18.BASE + 3) & ~3
    labels, code = vcf21.install(img, report, ext, text)
    report["vcf20"] = dict(version=21, arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, listing=b182.b18.sc.disasm(bytes(code), ext),
                           tail=hex(vcf21.TAIL), vb0=hex(vcf21_dsp.VB0), ratelimit=vcf21.RATE_MS if vcf21.RATELIMIT else 0)


if __name__ == "__main__":
    linein3.main(NAME, b182.b18.b6.b5.build, b182.b18.b6.b5.s15, sys.argv[1:], extra=extra)
