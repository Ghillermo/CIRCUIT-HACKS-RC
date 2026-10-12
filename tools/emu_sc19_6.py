"""SC19.6 ARM tests: the new drum knobs (K1 / K3 / K5 / K7) show their value as LED brightness (persist19.KNOB_LEVELS).

    python tools/emu_sc19_6.py STOCK.bin SC19.5.bin SC19.6.bin SC19.5_manifest.json SC19.6_manifest.json
Real routes: the LED frame comes from the stock tail of the controller's store listener at 0x08033B3E (the patched call to the LED task, the drum macro handler's
slot 7 = c_mhleds19, the track-view container copy), the 69 LED halfwords are read from [[ctrl + 0x90]] and then converted by the STOCK colour converter 0x0803423C
(with the hook), the way the refresh does; the expected colours are computed from the RGB table the stock code uses (RAM 0x20003804) and its brightness formula
(0x080475A6: byte * (b * 0x1CC + 0x1A00) >> 16, b = 0..127).
  * the image differs from SC19.5 only in the version block, the macro handler's slot 7, the converter's knob loop (a bl) and the appended code;
  * K1 / K3 / K5 / K7: the halfword = drum colour | (brightness + 2) << 8; brightness from the saved values (unipolar = value, bipolar = twice the distance from the centre,
    filter mode 0 / 32 / 64 / 96 / 127); with Shift held, the Shift layer's values; K2 / K4 / K6 / K8 and the other 61 LEDs as SC19.5;
  * converted: K1 / K3 / K5 / K7 = the drum colour scaled as the stock scales a dynamic knob (equal to the stock K2 / K4 with the same value, also in the dim mode);
  * every other view (synth / MIDI tracks, Mixer, FX, Master FX, power-up view) converts to exactly the same 69 colours as SC19.5.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc19 import E19, MGR  # noqa: E402
from emu_sc05 import STOP  # noqa: E402
from emu_sc08 import CONT  # noqa: E402
import persist19 as P  # noqa: E402
import thumb  # noqa: E402

BASE = 0x08010000
TAIL = 0x08033B3E
SEL_TRACK = 0x188
RGB_TABLE = 0x20003804
CONV = 0x0803423C
DEST, OUT = 0x2006D000, 0x2006D400
PLAIN = {0: 7, 2: 2, 4: 3, 6: 5}
SHIFT = {0: 1, 2: 8, 4: 4, 6: 9}
UNI = (2, 6, 8)
DCODE = [0x45, 0x2D, 0x49, 0x4D]


def level(code, byte):
    """expected brightness of a saved byte (the model of c_lvl)"""
    v = byte & 0x7F
    if code == 9: return min(127, min(v & 7, 4) * 32)
    if code in UNI: return v
    s = v - 128 if v >= 64 else v
    return (-s - 1) * 2 if s < 0 else s * 2


def scale(rgb, b):
    f = b * 0x1CC + 0x1A00
    return tuple((c * f) >> 16 for c in rgb)


class E196(E19):
    def frame(self):
        self.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1))
        self.uc.reg_write(UC_ARM_REG_R4, MGR)
        self.call(TAIL, maxins=5_000_000)
        return list(struct.unpack("<69H", bytes(self.uc.mem_read(self.r32(self.r32(MGR + 0x90)), 138))))
    def track(self, t): self.set_p0(self.r32(CONT + SEL_TRACK), t)
    def conv(self, out):
        """the stock converter on a frame: 69 RGB words"""
        self.uc.mem_write(OUT, struct.pack("<69H", *out)); self.uc.mem_write(DEST, bytes(69 * 4))
        self.call(CONV, MGR, DEST, OUT, maxins=2_000_000)
        return list(struct.unpack("<69I", bytes(self.uc.mem_read(DEST, 69 * 4))))
    def rgb(self, code):
        w = self.r32(RGB_TABLE + 4 * code); return (w & 0xFF, (w >> 8) & 0xFF, (w >> 16) & 0xFF)
    def led_cell(self, n, i):
        """address of the byte the converter reads for a dynamic code: store n of [ctrl + 0x198 + 4n], element i"""
        self.call(0x0803542C, self.r32(MGR + 0x198 + 4 * n), i); return self.uc.reg_read(UC_ARM_REG_R0)
    def dim(self, on):
        self.call(0x0803542C, self.r32(MGR + 0x78), 2); p = self.uc.reg_read(UC_ARM_REG_R0)
        w = self.r32(p); self.uc.mem_write(p, struct.pack("<I", (w | 1 << 10) if on else (w & ~(1 << 10))))
    def setcode(self, d, code, byte): self.setxm(P.XM_DRUMS + 9 * d + code - 1, byte)


def unpack(w): return (w & 0xFF, (w >> 8) & 0xFF, (w >> 16) & 0xFF)


def main(stock, s195, img, man5, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    rep = man["report"]
    L = {k: int(v, 16) for k, v in rep["persist19"]["labels"].items()}
    check(rep["persist19"].get("knob_levels") is True and "knob_levels" not in man5["report"]["persist19"], "manifest: knob_levels on (SC19.6), off in SC19.5")
    # ---- installation: SC19.5 -> SC19.6
    n = min(len(s195), len(img))
    diff = [i for i in range(n) if s195[i] != img[i]]
    end5 = len(s195)
    hook = bytes(img[P.LED_CONV_HOOK - BASE:P.LED_CONV_HOOK - BASE + 4])
    check(hook == thumb.bl(P.LED_CONV_HOOK, L["c_ledhook"]) and bytes(s195[P.LED_CONV_HOOK - BASE:P.LED_CONV_HOOK - BASE + 4]) == P.LED_CONV_BYTES,
          "0x080342B0: ldrh r7, [r6] ; movs r4, #0xff  ->  bl c_ledhook")
    check(struct.unpack_from("<I", img, P.MH_SLOT7 - BASE)[0] == L["c_mhleds19"] | 1, "drum macro handler slot 7 -> c_mhleds19")
    ext5 = int(man5["report"]["sc18"]["labels"]["c_mh"], 16) & ~0xFFF               # everything the builders append starts after the stock code (0x0805B000 is above it)
    stock_diff = sorted({(BASE + i) & ~3 for i in diff if BASE + i < 0x0805B000})
    import srcview as SV
    moved = (0x08033320, SV.SP_VT + 4 * SV.SLOT_PAD, SV.SP_VT + 4 * SV.SLOT_LEDS)            # the source view's code moved up by the new code in front of it: its three pointers
    check(all(a in (0x080342B0, P.MH_SLOT7) + moved or 0x080101E8 <= a < 0x08010200 for a in stock_diff),
          f"inside the stock image SC19.6 differs from SC19.5 only at the hook, the slot, the source view's three pointers and the version block {[hex(a) for a in stock_diff]}")
    check(0x20044E58 - int(rep["sc17"]["sc14_state"], 16) == 220, "RAM reservation unchanged (220 bytes)")

    # ---- the frame of each drum
    gc.collect(); e = E196(img, man); gc.collect(); r = E196(s195, man5)
    vals = {7: [0x6C, 0x1E, 0x40, 0x00, 0x3F], 2: [0x64, 0x00, 0x7F, 0x20, 0x01], 3: [0x7B, 0x05, 0x40, 0x3F, 0x00], 5: [0x28, 0x58, 0x00, 0x7F, 0x41],
            1: [0x14, 0x60, 0x00, 0x3F, 0x41], 8: [0x10, 0x7F, 0x00, 0x01, 0x50], 4: [0x7F, 0x03, 0x5E, 0x00, 0x40], 9: [0, 1, 2, 3, 4]}
    for d in range(4):
        e.track(4 + d); r.track(4 + d)
        for step in range(5):
            for code, vs in vals.items():
                b = vs[step] | (0x80 if (step + code) % 2 else 0)               # bit 7 = an extended value of another knob: must not matter
                e.setcode(d, code, b)
            for shift in (False, True):
                if shift: e.set_p0(e.r32(MGR + 0xC), 1); r.set_p0(r.r32(MGR + 0xC), 1)
                fe, fr = e.frame(), r.frame()
                if shift: e.set_p0(e.r32(MGR + 0xC), 0); r.set_p0(r.r32(MGR + 0xC), 0)
                codes = SHIFT if shift else PLAIN
                want = {60 + k: DCODE[d] | ((level(c, vals[c][step] | (0x80 if (step + c) % 2 else 0)) + 2) << 8) for k, c in codes.items()}
                good = all(fe[i] == w for i, w in want.items())
                same = all(fe[i] == fr[i] for i in range(69) if i not in want)
                check(good and same and all((fr[i] & 0xFF) == DCODE[d] for i in want),
                      f"drum {d + 1}, step {step}{', Shift' if shift else ''}: K1/K3/K5/K7 = {[hex(fe[i]) for i in sorted(want)]}"
                      + ("" if good else f" want {[hex(want[i]) for i in sorted(want)]}") + ("" if same else " (other LEDs differ from SC19.5)"))
    # ---- converted colours
    d = 1; e.track(4 + d); r.track(4 + d)
    for dim in (False, True):
        e.dim(dim); r.dim(dim)
        for code, byte in ((2, 100), (2, 0), (2, 127), (7, 0x6C), (7, 0x1E), (3, 0x7B), (5, 0x28)):
            e.setcode(d, code, byte)
            f = e.frame(); w = e.conv(f)
            k = {v: kk for kk, v in PLAIN.items()}[code]
            b = level(code, byte)
            exp = scale(e.rgb(DCODE[d]), b >> 1 if dim else b)
            check(unpack(w[60 + k]) == exp, f"drum 2{' dim' if dim else ''}: code {code} byte {byte:#04x} -> brightness {b} -> RGB {unpack(w[60 + k])} (want {exp})")
        # same value on a stock knob: K2 (store 5 element 0) = the K3 look
        e.setcode(d, 2, 100)
        e.uc.mem_write(e.led_cell(4 + d, 0), bytes([100]))
        f = e.frame(); w = e.conv(f)
        check(unpack(w[61]) == unpack(w[62]) and unpack(w[62]) == scale(e.rgb(DCODE[d]), 100 >> 1 if dim else 100),
              f"drum 2{' dim' if dim else ''}: K3 = 100 looks exactly like the stock K2 = 100 {unpack(w[61])}")
    e.dim(False); r.dim(False)
    # ---- every other view converts as SC19.5
    for name, setup in (("Synth 1", lambda x: x.track(0)), ("Synth 2", lambda x: x.track(1)), ("MIDI 1", lambda x: x.track(2)), ("MIDI 2", lambda x: x.track(3)),
                        ("Mixer", lambda x: x.btn(14)), ("FX view", lambda x: x.btn(15)), ("power-up view", lambda x: None)):
        gc.collect(); a, b = E196(s195, man5), E196(img, man)
        setup(a); setup(b)
        wa, wb = a.conv(a.frame()), b.conv(b.frame())
        check(wa == wb, f"{name}: the 69 converted colours = SC19.5")
    # ---- Shift press / release refresh the LEDs (so the Shift layer shows without touching a knob)
    gc.collect(); x = E196(img, man); x.track(4)
    calls = []
    def hh(uc, a, s, d_): calls.append(a)
    x.uc.hook_add(UC_HOOK_CODE, hh, begin=0x08034196, end=0x08034196)
    x.call(0x08033320, MGR, 27, maxins=900000); n1 = len(calls)
    x.call(0x0803381A, MGR, 27, maxins=900000); n2 = len(calls) - n1
    print(f"     LED task calls inside the Shift press: {n1}, release: {n2} (informative)")
    print("SC19.6 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), Path(a[2]).read_bytes(), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text()), json.loads(Path(a[5]).read_text())) else 0)
