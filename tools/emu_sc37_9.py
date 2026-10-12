"""SC37.9 ARM tests (live RAM dump, the real routes): the stock blue of Clear + knob on the drums (persist19.use_blue7) and Clear + knob in Master FX
(build_sc17.use_gclear).

    python tools/emu_sc37_9.py SC37.9.bin SC37.9_manifest.json
  * drums (Drum 1's view, the Clear button and the knobs through the controller): Clear + K2 (ours) right = the stock blue 0x07, whose RGB is the one
    the original firmware shows for its own Clear + knob right (emulated on the stock image); K3 (stock-routed) left x 40 = red 0x53, right x 40 = blue 0x07;
  * Master FX (Mixer twice): the Gater selected, K1 and K2 moved; Clear + K1 right = 80 (its default), K1 LED blue, K2 LED red; Clear + K2 left = no change;
    Clear released = the normal LEDs; the Glitch (pad 31): Clear + K1 right = 127; the sample (pad 7): Clear + K1 right = raw 0 (no transposition).
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R4
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc20_1 as T20  # noqa: E402
import emu_sc19_6 as S  # noqa: E402
from emu_sc05 import STOP  # noqa: E402
from emu_sc08 import E8, CONT  # noqa: E402
import build_sc17 as B  # noqa: E402

MGR = S.MGR
un = lambda w: (w & 0xFF, (w >> 8) & 0xFF, (w >> 16) & 0xFF)


def stock_blue_rgb():
    """the original firmware: Drum 1, Clear + K4 right x 40 -> (code, RGB of the knob LED)"""
    img = (Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    e = E8(img)
    e.set_p0(e.r32(CONT + 0x188), 4); e.call(0x08033320, MGR, 4, maxins=900000); e.call(0x0803381A, MGR, 4, maxins=900000)
    e.call(0x08033320, MGR, 23, maxins=900000)
    for _ in range(40): e.call(0x08033848, MGR, 3, 1, maxins=900000)
    e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR)
    e.call(S.TAIL, maxins=5_000_000)
    fr = list(struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138))))
    e.uc.mem_write(S.OUT, struct.pack("<69H", *fr)); e.uc.mem_write(S.DEST, bytes(69 * 4))
    e.call(S.CONV, MGR, S.DEST, S.OUT, maxins=2_000_000)
    rgb = struct.unpack("<69I", bytes(e.uc.mem_read(S.DEST, 69 * 4)))[63]
    del e; gc.collect()
    return fr[63], un(rgb)


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    # ---- drums
    code0, rgb0 = stock_blue_rgb()
    check(code0 == 0x07, f"the original firmware, Clear + knob right: code {code0:#x}, RGB (B, G, R) {rgb0}")
    n = T20.E201(img, man); n.btn(4)
    n.clear(False); n.turn(1, 0); n.clear(True); n.turn(1, 1)
    fr = n.frame(); rgb = un(n.conv(fr)[61])
    check(fr[61] == 0x07 and rgb == rgb0, f"Drum 1, Clear + K2 (ours) right: code {fr[61]:#x}, RGB {rgb} = the original's blue")
    n.clear(False); n.turn(2, 0); n.clear(True)
    for _ in range(40): n.turn(2, -1)
    left = n.knobs()[2]
    for _ in range(40): n.turn(2, 1)
    right = n.knobs()[2]
    check(left == 0x53 and right == 0x07, f"K3 (stock-routed) left x 40 red {left:#x}, right x 40 blue {right:#x}")
    n.clear(False); del n; gc.collect()
    # ---- Master FX
    import emu_sc36 as T36
    x = T36.T34.E7(img, man); x.grid()
    clear = lambda on: x.call(0x08033320 if on else 0x0803381A, MGR, 23, maxins=900000)
    knob = lambda k, d: x.call(0x08033848, MGR, k, d & 0xFFFFFFFF, maxins=900000)
    x.pad(0); x.rel(0)
    check(x.blkb(B.S_SEL)[0] == 0, "Master FX: pad 1 selects the Gater")
    knob(0, 10); knob(1, -5)
    k0, k1 = x.knobs(0)[:2]
    check(k0 != B.DEFAULTS[0][0] and k1 != B.DEFAULTS[0][1], f"K1 / K2 moved ({k0}, {k1})")
    clear(True); knob(0, 1)
    g = x.gleds()
    check(x.knobs(0)[0] == B.DEFAULTS[0][0] and g[34] == B.GCLR_BLUE and g[35] == B.GCLR_RED,
          f"Clear + K1 right: K1 = {x.knobs(0)[0]} (default {B.DEFAULTS[0][0]}), K1 LED blue {g[34]:#x}, K2 (not at its default) red {g[35]:#x}")
    knob(1, -3)
    check(x.knobs(0)[1] == k1, f"Clear + K2 left: unchanged ({x.knobs(0)[1]})")
    clear(False); g = x.gleds()
    check(g[34] not in (B.GCLR_BLUE, B.GCLR_RED) and g[35] not in (B.GCLR_BLUE, B.GCLR_RED), f"Clear released: the normal knob LEDs ({g[34]:#x}, {g[35]:#x})")
    KG = B.S_SLOT + 4 * B.GL_SLOT
    x.pad(B.GL_PAD); x.rel(B.GL_PAD); knob(0, -20)
    v = x.blkb(KG)[0] & 0x7F
    clear(True); knob(0, 1); clear(False)
    check(v != B.GL_DEF[0] and x.blkb(KG)[0] & 0x7F == B.GL_DEF[0], f"the Glitch: K1 {v} -> Clear + right {x.blkb(KG)[0] & 0x7F} (normal speed)")
    KB = B.S_SLOT + 4 * B.SMP_SLOT
    x.pad(B.SMP_PAD); x.rel(B.SMP_PAD)
    if x.blkb(B.S_SEL)[0] == B.SMP_SEL:
        knob(0, 10); v = x.blkb(KB)[0] & 0x7F
        clear(True); knob(0, 1); clear(False)
        check(v != 0 and x.blkb(KB)[0] & 0x7F == 0, f"the sample: K1 raw {v} -> Clear + right {x.blkb(KB)[0] & 0x7F} (no transposition)")
    else:
        check(False, f"pad 7 should select the sample (S_SEL {x.blkb(B.S_SEL)[0]})")
    print("SC37.9 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
