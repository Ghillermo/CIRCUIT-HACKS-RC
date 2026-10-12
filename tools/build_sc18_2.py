"""Circuit Tracks 4486 — SC18.2 = SC18.1 + LEDs (tools/leds18.py):

  FX view: Octave UP / DOWN (delay / reverb sends) peach / cream, Duplicate (reset) light blue, "1-16 / 17-32" (master
  resonance step) light green;  drum knobs K1 / K3 / K5 / K7 (the new SC18.1 controls) lit in the drum's colour.
Everything up to SC18.1 is unchanged (tools/verify_builds.py).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import drums18  # noqa: E402
drums18.V2 = True
import build_sc17 as s17  # noqa: E402
s17.CLEAR_SP = True
import build_sc18 as b18  # noqa: E402
s17.use_jump()
import linein3  # noqa: E402
import leds18  # noqa: E402

NAME = "SC18.2"


def extra(img, report):
    b18.extra(img, report)
    st = (Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    def text(addr, n): return "|".join(b18.sc.disasm(bytes(st[addr - b18.BASE:addr - b18.BASE + n]), addr))
    ext = (len(img) + b18.BASE + 3) & ~3
    labels, code, dcodes = leds18.install(img, report, ext, text)
    report["leds18"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()},
                            listing=b18.sc.disasm(bytes(code), ext), drum_codes=[hex(c) for c in dcodes],
                            fx_leds={str(leds18.LED_OCT_UP): hex(leds18.PEACH), str(leds18.LED_OCT_DN): hex(leds18.CREAM),
                                     str(leds18.LED_DUP): hex(leds18.LIGHT_BLUE), str(leds18.LED_PAIR): hex(leds18.LIGHT_GREEN)})


if __name__ == "__main__":
    linein3.main(NAME, b18.b6.b5.build, b18.b6.b5.s15, sys.argv[1:], extra=extra)
