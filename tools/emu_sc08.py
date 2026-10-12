"""Emulation tests for SC08 (chromatic drum Preset view) on the live RAM dump."""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE, Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS
from unicorn.arm_const import *

sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc05 import E  # noqa: E402

MGR, CONT = 0x20040B10, 0x20040DB8
VIEWS = [0x20042D14, 0x20042DF4, 0x20042ED4, 0x20042FB4]       # drum 1..4 Preset views
DP_VT = 0x0805ABBC
PALETTE = 0x08056464
SCALE_OBJ, ROOT_PTR = 0x2003FA8C, 0x2003FA94
MASKS = (0x00441108, 0x00221088, 0x00421108, 0x00441110, 0x00421088, 0x00221108, 0x00241108, 0x00421024,
         0x00490124, 0x00491124, 0x00240908, 0x00420908, 0x00220890, 0x00240910, 0x00448888, 0x00000000)


def model(mask, root, pad):
    iv = [n for n in range(12) if (mask >> (2 * n)) & 3 == 0]
    N = len(iv); rb = 3 - pad // 8; col = pad % 8
    if N == 12:
        black = rb & 1; octv = (rb >> 1) - 1
        semis = ([None, 1, 3, None, 6, 8, 10, None] if black else [0, 2, 4, 5, 7, 9, 11, 12])[col]
        if semis is None:
            return 0xFF, 0
        isroot = semis in (0, 12)
    else:
        d = (rb - 1) * N + col
        octv, idx = divmod(d, N)
        semis = iv[idx]; isroot = idx == 0
    v = max(0, min(127, 64 + root + octv * 12 + semis))
    return v, int(isroot)


class E8(E):
    def pal(self, idx):
        return struct.unpack("<H", self.uc.mem_read(PALETTE + 2 * idx, 2))[0]

    def leds(self, view):
        return list(struct.unpack("<32H", bytes(self.uc.mem_read(self.r32(self.r32(view + 4)), 64))))

    def setflag(self, view, on):
        b = self.r8(view + 0x51) & ~1 | (1 if on else 0)
        self.uc.mem_write(view + 0x51, bytes([b, 0]))      # +0x52 = SC11 bias (0)

    def set_scale(self, mask, root):
        self.w32(SCALE_OBJ + 4, mask); self.uc.mem_write(ROOT_PTR, bytes([root]))

    def store_p0(self, st):
        self.call(0x0803542C, st, 0); return self.r8(self.uc.reg_read(UC_ARM_REG_R0))

    def set_p0(self, st, v):
        self.call(0x080354FA, st, 0); self.uc.mem_write(self.uc.reg_read(UC_ARM_REG_R0), bytes([v]))
        self.call(0x080353C0, st)


def main(stock, img, labels):
    fails = 0
    def check(c, m):
        nonlocal fails
        if not c: fails += 1; print("FAIL:", m)
        else: print("ok  :", m)

    # 0) constructor patch: strh.w r0,[r5,#0x50] with r0 = 1 -> +0x50 = 1, +0x51 = 0
    uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)
    uc.mem_map(0x08000000, 0x80000); uc.mem_write(0x08010000, img); uc.mem_map(0x20000000, 0x10000)
    uc.mem_write(0x20000050, b"\x77\x55\x66\x44"); uc.reg_write(UC_ARM_REG_R5, 0x20000000); uc.reg_write(UC_ARM_REG_R0, 1)
    uc.emu_start(0x0804D89C | 1, 0x0804D8A0)
    check(bytes(uc.mem_read(0x20000050, 4)) == b"\x01\x00\x66\x44", f"constructor zeroes flag byte: {bytes(uc.mem_read(0x20000050, 4)).hex()}")
    for v in VIEWS:
        check(E8(stock).r32(v) == DP_VT, f"drum Preset view {v:#x} vtable")

    # 1) c_scale + c_padval vs model, several scales/roots
    e = E8(img); ctx = 0x20060200
    e.call(labels["c_scale"], VIEWS[0], ctx)
    check(e.uc.reg_read(UC_ARM_REG_R0) == 0 and bytes(e.uc.mem_read(ctx, 9)) == bytes([0, 7, 0, 2, 3, 5, 7, 8, 10]),
          f"scale context from dump (C natural minor): {bytes(e.uc.mem_read(ctx, 9)).hex()}")
    bad = []
    for si, mask in enumerate(MASKS):
        for root in (0, 5, 11):
            e = E8(img); e.set_scale(mask, root)
            e.call(labels["c_scale"], VIEWS[1], ctx)
            if e.uc.reg_read(UC_ARM_REG_R0):
                bad.append((si, root, "scale fail")); continue
            for pad in range(32):
                e.call(labels["c_padval"], ctx, pad)
                got = (e.uc.reg_read(UC_ARM_REG_R0), e.uc.reg_read(UC_ARM_REG_R1))
                if got != model(mask, root, pad):
                    bad.append((si, root, pad, got, model(mask, root, pad)))
    check(not bad, f"pad -> pitch for 16 scales x 3 roots x 32 pads ({len(bad)} mismatches) {bad[:3]}")
    e = E8(img); e.set_scale(MASKS[1], 0)
    print("     C major, rows top->bottom:", [[model(MASKS[1], 0, r * 8 + c)[0] - 64 for c in range(8)] for r in range(4)])
    print("     chromatic, rows top->bottom:", [[(lambda v: None if v[0] == 0xFF else v[0] - 64)(model(0, 0, r * 8 + c)) for c in range(8)] for r in range(4)])
    # sanity guard: wrong sequencer vtable -> fail, no crash
    e = E8(img); e.w32(e.r32(VIEWS[0] + 0xC) + 0x3C, 0x12345678)
    e.call(labels["c_scale"], VIEWS[0], ctx)
    check(e.uc.reg_read(UC_ARM_REG_R0) == 1, "c_scale refuses an unexpected object layout")

    # 2) pad press in chromatic mode: Pitch param set (id 40 for drum 1) + stock Preset note, recorded while recording
    def press(image, view, pad, flag, rec=False):
        e = E8(image); e.recording(rec); e.setflag(view, flag); log = []
        def h(uc, a, s, d):
            if a == 0x08031A98: log.append(("param", uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2)))
            elif a == 0x0804E0BA: log.append(("note_on", uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2)))
            elif a == 0x0804D934: log.append(("stock_pad",))
            elif a == 0x0802E62C: log.append(("rec_param_gate",))
        e.uc.hook_add(UC_HOOK_CODE, h)
        p0 = e.store_p0(e.r32(view + 0x2C))
        fn = struct.unpack("<I", bytes(e.uc.mem_read(DP_VT, 4)))[0]
        e.ev.clear(); e.call(fn & ~1, view, pad, 100)
        return log, list(e.ev), p0, e.store_p0(e.r32(view + 0x2C))
    for d, view in enumerate(VIEWS):
        log, ev, s0, s1 = press(img, view, 0x13, True)
        exp = model(MASKS[0], 0, 0x13)[0]
        params = [x for x in log if x[0] == "param"]
        check(params == [("param", 40 + 5 * d, exp)] and ("note_on", 0x13, 100) in log and ("stock_pad",) not in log
              and s0 == s1, f"drum {d+1} chromatic pad 0x13 -> Pitch id {40+5*d} = {exp} + hit, sample unchanged ({s0}) {log}")
    log, ev, _, _ = press(img, VIEWS[0], 0x13, True, rec=True)
    check(("rec_param_gate",) in log, f"recording: Pitch goes through the automation recorder {log}")
    log, ev, _, _ = press(img, VIEWS[2], 3, False)
    log_s, ev_s, _, _ = press(stock, VIEWS[2], 3, False)
    check(log == log_s and ev == ev_s and ("stock_pad",) in log, f"flag off: identical to stock {log}")
    ee = E8(img); ee.set_scale(0, 0); ee.setflag(VIEWS[0], True); hits = []
    ee.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: hits.append(a) if a in (0x08031A98, 0x0804E0BA) else None)
    ee.call(labels["c_dpad"], VIEWS[0], 0, 100)           # chromatic black row, col 0 = unused
    check(hits == [], f"chromatic gap pad does nothing {hits}")

    # 3) LEDs via get-LEDs dispatcher
    for flag in (True, False):
        e_s = E8(stock); before = e_s.leds(VIEWS[0])
        e = E8(img); e.setflag(VIEWS[0], flag)
        e.call(0x0804758C, VIEWS[0]); ret = e.uc.reg_read(UC_ARM_REG_R0)
        got = e.leds(VIEWS[0])
        if flag:
            base = struct.unpack("<H", bytes(e.uc.mem_read(VIEWS[0] + 0x26, 2)))[0]
            exp = [0 if model(MASKS[0], 0, p)[0] == 0xFF else e.pal(base if model(MASKS[0], 0, p)[1] else base + 2) for p in range(32)]
            check(got == exp and ret == e.r32(e.r32(VIEWS[0] + 4)), f"chromatic LEDs painted (root {e.pal(base):#x}, scale {e.pal(base+2):#x})")
        else:
            check(got == before, "flag off: LEDs untouched")

    # 4) Shift + Preset on the controller
    def shift_preset(image, track_btn, btn=8, shift=True, times=1):
        e = E8(image)
        for v in VIEWS: e.setflag(v, False)          # as after an SC08 boot (constructor zeroes the flag)
        e.call(0x08033320, MGR, track_btn, maxins=600000)
        if shift: e.set_p0(e.r32(MGR + 0xC), 1)
        for _ in range(times):
            e.call(0x08033320, MGR, btn, maxins=600000)
        return e
    e = shift_preset(img, 4)
    check(e.r8(VIEWS[0] + 0x51) & 1 == 1 and e.r8(CONT + 0x18C) == 0, f"Shift+Preset on Drum 1: chromatic on, Preset view (mode {e.r8(CONT + 0x18C)})")
    check(all(e.r8(v + 0x51) & 1 == 0 for v in VIEWS[1:]), "other drums unchanged")
    e2 = shift_preset(img, 4, times=2); dump = E8(stock).leds(VIEWS[0])
    check(e2.r8(VIEWS[0] + 0x51) & 1 == 0 and e2.leds(VIEWS[0]) == dump, "second Shift+Preset: off, stock colours repainted (= dump)")
    e = shift_preset(img, 6)
    check(e.r8(VIEWS[2] + 0x51) & 1 == 1, "Shift+Preset on Drum 3")
    es, e7 = shift_preset(stock, 0), shift_preset(img, 0)
    check(e7.r8(CONT + 0x18C) == es.r8(CONT + 0x18C) and all(e7.r8(v + 0x51) & 1 == 0 for v in VIEWS),
          f"Shift+Preset on Synth 1: same as stock (mode {es.r8(CONT + 0x18C)}), no flags")
    es, e7 = shift_preset(stock, 4, shift=False), shift_preset(img, 4, shift=False)
    check(e7.r8(CONT + 0x18C) == es.r8(CONT + 0x18C) == 0 and e7.r8(VIEWS[0] + 0x51) & 1 == 0,
          "Preset without Shift: stock")
    for btn in (10, 9, 13):          # Shift + Velocity / Note / other view button: same as stock
        es, e7 = shift_preset(stock, 4, btn=btn), shift_preset(img, 4, btn=btn)
        st = es.r32(es.r32(0x200069E4)); st = es.r32(st + 0x54)
        es.call(0x0803542C, st, 2); a = es.r32(es.uc.reg_read(UC_ARM_REG_R0))
        e7.call(0x0803542C, st, 2); b = e7.r32(e7.uc.reg_read(UC_ARM_REG_R0))
        check(a == b and es.r8(CONT + 0x18C) == e7.r8(CONT + 0x18C) and es.r32(MGR + 0x6C) == e7.r32(MGR + 0x6C),
              f"Shift + button {btn}: same as stock")
    print("SC08 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    man = json.loads(Path(sys.argv[3]).read_text())
    labels = {k: int(v, 16) for k, v in man["report"]["sc08"]["labels"].items()}
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), Path(sys.argv[2]).read_bytes(), labels) else 0)
