"""Circuit Tracks 4486 — SC17.5 = SC17.4 + delay / reverb returns as synth sources + FX view keys.

  * Synth Preset view, Shift + pad 30 / 31: the synth's noise source = delay / reverb return (linein3.py).
  * FX view: Octave UP = knobs are the delay sends, Octave DOWN = knobs are the reverb sends;
    button 16 = reset (all sends 0, master filter centred, Master FX off)  (fxkeys.py).
SC17.4 and everything before it are unchanged (tools/verify_builds.py).
"""
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ct_fw  # noqa: E402
import build_sc17 as s17  # noqa: E402
import build_sc15 as s15  # noqa: E402
import build_sc16 as s16  # noqa: E402
import build_shared_channels as sc  # noqa: E402
import linein3  # noqa: E402
import fxkeys  # noqa: E402
from thumb import b_w  # noqa: E402

BASE = ct_fw.APP_BASE
NAME = "SC17.5"

s17.use_mixer14()
s17.use_full_leds()
linein3.install(s15, s16)


def build(stock: bytes, listing: Path):
    img17, report = s17.build(stock, listing)
    img = bytearray(img17)
    def text(addr, n):
        return "|".join(sc.disasm(bytes(stock[addr - BASE:addr - BASE + n]), addr))
    for hook, _, want in fxkeys.hooks():
        assert text(hook, 4) == want, (hex(hook), text(hook, 4))
        assert bytes(img[hook - BASE:hook - BASE + 4]) == bytes(stock[hook - BASE:hook - BASE + 4]), hex(hook)
    assert text(fxkeys.BTN_EXIT, 2) == "pop {r0, r4, r5, pc}", text(fxkeys.BTN_EXIT, 2)
    assert text(fxkeys.BTN_DOWN_BACK, 2) == text(fxkeys.BTN_UP_BACK, 2) == text(fxkeys.BTN_PAIR_BACK, 2) == "cmp r0, r1"
    if fxkeys.CLEAR_RESET: assert text(fxkeys.BTN_CLEAR_BACK, 2) == "ldr r2, [r0]", text(fxkeys.BTN_CLEAR_BACK, 2)
    c_gst = int(report["sc14"]["labels"]["c_gst"], 16)
    c_gfst = int(report["sc17"]["labels"]["c_gfst"], 16)
    ext = (len(img) + BASE + 3) & ~3
    c_shift = int(report["sc15"]["labels"]["c_shift"], 16)
    code, labels = fxkeys.arm_code(ext, c_gst, c_gfst, c_shift)
    img += b"\xFF" * (ext - BASE - len(img)) + code
    while len(img) % 4:
        img += b"\xFF"
    assert len(img) <= 0x70000
    for hook, lab, _ in fxkeys.hooks():
        img[hook - BASE:hook - BASE + 4] = b_w(hook, labels[lab])
    report["fxkeys"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, listing=sc.disasm(bytes(code), ext),
                            hooks={hex(h): lab for h, lab, _ in fxkeys.hooks()}, clear_reset=fxkeys.CLEAR_RESET, page_btn=fxkeys.PAGE_BTN)
    return bytes(img), report


if __name__ == "__main__":
    linein3.main(NAME, build, s15, sys.argv[1:])
