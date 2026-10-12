"""SC37.4 ARM tests (live RAM dump): the Setup toggles «reverb -> strip 3» (pad 22) / «delay -> strip 4» (pad 23) in their colours (build_sc10.use_retcols).

    python tools/emu_sc37_4.py SC37.4.bin SC37.3.bin
  * off / on of each bit: pad 22 cream 0x2A / 0x29, pad 23 peach 0x6B / 0x6A (SC37.3: both Synth 1's palette entries);
  * pressing pad 22 / 23 through the Setup view's pad slot still toggles bits 28 / 29.
"""
from __future__ import annotations
import gc, struct, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc10 import E10, SETUP  # noqa: E402


def leds(image, bits):
    e = E10(image); e.set_p2(e.p2() & ~(3 << 28) | bits << 28)
    e.call(0x0804758C, SETUP); buf = e.uc.reg_read(UC_ARM_REG_R0)
    out = struct.unpack("<2H", bytes(e.uc.mem_read(buf + 0x2A, 4)))
    del e; gc.collect()
    return out


def main(img, prev):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    for bits in (0, 1, 2, 3):
        l, o = leds(img, bits), leds(prev, bits)
        exp = (0x29 if bits & 1 else 0x2A, 0x6A if bits & 2 else 0x6B)
        check(l == exp, f"bits {bits}: pad 22 (reverb) {l[0]:#x}, pad 23 (delay) {l[1]:#x} (SC37.3: {o[0]:#x} / {o[1]:#x})")
    e = E10(img); pad_fn = struct.unpack("<I", bytes(e.uc.mem_read(0x0805A98C, 4)))[0] & ~1
    for pad, bit in ((0x15, 28), (0x16, 29)):
        p0 = e.p2(); e.call(pad_fn, SETUP, pad, 100); p1 = e.p2(); e.call(pad_fn, SETUP, pad, 100)
        check(p1 == p0 ^ (1 << bit) and e.p2() == p0, f"Setup pad {pad + 1}: bit {bit} toggles")
    print("SC37.4 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), Path(sys.argv[2]).read_bytes()) else 0)
