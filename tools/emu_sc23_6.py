"""SC23.6 ARM tests: the type knobs through the real controller routes (knob 0x08033848, LED frame 0x08033B3E).

    python tools/emu_sc23_6.py SC23.6.bin SC23.6_manifest.json
  * FX type (Shift + K8, code 13) and filter type (Shift + K5, code 16): plain 0..127 knobs, one click = one step, clamped at both ends (no wrap-around), 7 zones of ~18 clicks (the zone is
    t = 7 p >> 7); the value that goes to the DSP is p itself; Shift + K7 (FXMOD) has no function;
  * the LEDs of the three type knobs (FX type, filter type, waveform): colour = the mode (TCOL_*), brightness = the parameter inside the mode (the morph / the follow), the other knobs as before;
  * the waveform (page B, K7): the morph position as before, zones 42 apart, clamped; Clear + a knob puts the type back to its default (zone 0, parameter 0).
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc23_5 as T5  # noqa: E402,F401  (applies the SC23.x options)
import emu_sc22_4 as T4  # noqa: E402
import vcf21_dsp as VD  # noqa: E402
V = T4.V
V.use_typezones()
E20, MGR = T4.E20, T4.MGR


def led(code, p):
    """the expected halfword of a type knob with the stored value p"""
    if code == 19:
        t, m = 0, p
        while m >= 42: m -= 42; t += 1
        f, col = m * 3, V.TCOL_WV[t]
    else:
        t, f = (7 * p) >> 7, (7 * p) & 127
        col = (V.TCOL_FX if code == 13 else V.TCOL_FT)[t]
    return col | ((V.TZ_MINB + ((f * (127 - V.TZ_MINB)) >> 7) + 2) << 8)


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["vcf20"]["labels"].items()}
    DU = man["marker"] in ("SC24", "SC25", "SC26", "SC27", "SC28", "SC29", "SC30", "SC31", "SC32", "SC33", "SC34")
    if DU: V.use_pads2(); V.use_edv2(); V.use_saveled(); V.use_dualui()
    if man["marker"] in ("SC26", "SC27", "SC28", "SC29", "SC30", "SC31", "SC32", "SC33", "SC34"): V.SIG_VAL = 0xB0                                    # SC26: the step-drummer bytes, the state of SC25 is kept                                                 # SC24: the knob page lives in RT_TAG (bits 1-2), the signature and the code 14 default changed
    gc.collect(); e = E20(img, man)
    for _ in range(30): e.vtick()
    check(e.tailb(V.O_SIG) == V.SIG_VAL, f"signature {V.SIG_VAL:#x} (the saved state of the older build is dropped): {e.tailb(V.O_SIG):#x}")
    e.call(L["c_vset"], 0, 1); e.vtick(); e.btn(2); e.track(2)
    HELD = lambda: e.set_p0(e.r32(MGR + 0xC), 1)
    FREE = lambda: e.set_p0(e.r32(MGR + 0xC), 0)

    def shifted_frame():
        HELD(); fr = e.frame(); FREE(); return fr

    # ---- FX type: Shift + K8
    check(e.val(0, 13) == 0 and e.val(0, 14) == V.DEFAULTS[13], f"defaults: FX type 0, code 14 = {V.DEFAULTS[13]}")
    seen = []
    for i in range(1, 128):
        e.knob_raw(7, 1, True)
        if e.val(0, 13) != i: break
        seen.append(((7 * i) >> 7))
    check(e.val(0, 13) == 127 and len(seen) == 127, f"127 clicks of +1 reach 127 one step at a time ({e.val(0, 13)})")
    zone_len = [seen.count(t) for t in range(7)]
    check(all(18 <= n <= 19 for n in zone_len[1:6]) and zone_len[0] == 18 and sum(zone_len) == 127, f"clicks per zone: {zone_len} (about 18 each)")
    e.knob_raw(7, 1, True); e.knob_raw(7, 20, True)
    check(e.val(0, 13) == 127, "clamped at the top: no wrap-around to the first type")
    e.knob_raw(7, -200, True)
    check(e.val(0, 13) == 0, "a big turn down stops at 0")
    e.knob_raw(7, -1, True); e.knob_raw(7, -1, True)
    check(e.val(0, 13) == 0, "clamped at the bottom: no wrap-around to the last type")
    # ---- Shift + K7: no function
    before = bytes(e.tail())
    e.knob_raw(6, 5, True)
    check(bytes(e.tail()) == before, "Shift + K7 (FXMOD in SC23.5) does nothing now")
    fs = shifted_frame()
    check((fs[66] >> 8) == 2, f"and its LED is dark (brightness field {fs[66] >> 8})")
    # ---- LEDs of the FX type
    for p in (0, 17, 18, 19, 36, 60, 100, 126, 127):
        e.knob_raw(7, -200, True); e.knob_raw(7, p, True)
        fs = shifted_frame()
        check(e.val(0, 13) == p and fs[67] == led(13, p), f"FX type p = {p}: zone {(7 * p) >> 7}, colour {fs[67] & 0xFF:#x} (expected {led(13, p) & 0xFF:#x}), brightness {(fs[67] >> 8) - 2} (expected {(led(13, p) >> 8) - 2})")
    cols = [led(13, (z * 128 + 6) // 7) & 0xFF for z in range(7)]
    check(len(set(cols)) == 7, f"seven different colours for the seven FX types {[hex(c) for c in cols]}")
    # the plain layer is untouched by it
    fp = e.frame()
    byt = [e.tailb(V.O_PAR + c) for c in range(16)]
    ok = all(((fp[60 + k] >> 8) - 2) == T4.level(0, V.KNOB_CODES[k], byt[V.KNOB_CODES[k] - 1]) and (fp[60 + k] & 0xFF) == V.COL_TRACK[0] for k in range(8))
    check(ok, "the plain layer (K1..K8) keeps the track colour and the brightness of the values")

    # ---- filter type: Shift + K5
    e.knob_raw(4, -200, True)
    for i in range(1, 128):
        e.knob_raw(4, 1, True)
    check(e.val(0, 16) == 127, "filter type: 127 clicks reach 127")
    e.knob_raw(4, 1, True); check(e.val(0, 16) == 127, "no wrap-around at the top")
    e.knob_raw(4, -200, True); e.knob_raw(4, -1, True); check(e.val(0, 16) == 0, "no wrap-around at the bottom")
    for p in (0, 18, 19, 36, 60, 100, 127):
        e.knob_raw(4, -200, True); e.knob_raw(4, p, True)
        fs = shifted_frame()
        check(e.val(0, 16) == p and fs[64] == led(16, p), f"filter type p = {p}: zone {(7 * p) >> 7}, colour {fs[64] & 0xFF:#x}, brightness {(fs[64] >> 8) - 2} (follow = {(7 * p) & 127})")
    cols = [led(16, (z * 128 + 6) // 7) & 0xFF for z in range(7)]
    check(len(set(cols)) == 7, f"seven different colours for the seven filter types {[hex(c) for c in cols]}")

    # ---- what goes to the DSP is p (the DSP derives zone and parameter)
    e.knob_raw(7, -200, True); e.knob_raw(7, 77, True); e.knob_raw(4, -200, True); e.knob_raw(4, 33, True)
    sent = []
    for _ in range(60):
        for w, ad in e.vtick():
            if ad == VD.VB0: sent.append(((w >> 16) & 0x1F, w & 0xFFFF))
    last = {c: v for c, v in sent}
    check(last.get(13) == 77 and last.get(16) == 33, f"the mailbox gets p as it is: code 13 = {last.get(13)}, code 16 = {last.get(16)}")

    # ---- the waveform, page B, K7
    def page_b(on):
        if DU: e.uc.mem_write(V.TAIL + V.O_RT + V.RT_TAG, bytes([(e.rt(0, V.RT_TAG) & ~6) | (2 if on else 0)]))
        else: e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.tailb(V.O_FLAGS) | 0x10 if on else e.tailb(V.O_FLAGS) & ~0x10]))
    page_b(True)
    check(e.val(0, 19) == 0, f"WAVE default 0 (sine) {e.val(0, 19)}")
    for m in (0, 8, 41, 42, 50, 83, 84, 100, 125, 126):
        e.knob_raw(6, -200); e.knob_raw(6, m)
        fr = e.frame()
        check(e.val(0, 19) == m and fr[66] == led(19, m), f"WAVE m = {m}: colour {fr[66] & 0xFF:#x}, brightness {(fr[66] >> 8) - 2} (expected {led(19, m) & 0xFF:#x}, {(led(19, m) >> 8) - 2})")
    e.knob_raw(6, 500); check(e.val(0, 19) == 127, "WAVE clamps at 127 (no wrap-around)")
    e.knob_raw(6, -500); e.knob_raw(6, -1); check(e.val(0, 19) == 0, "and at 0")
    check(len({V.TCOL_WV[t] for t in range(4)}) == 4, "four colours for the four waves")
    page_b(False)

    # ---- Clear + the knob: the type goes back to zone 0, parameter 0 (both layers)
    clr_dn = lambda: e.call(0x08033320, MGR, 23, maxins=900000)
    clr_up = lambda: e.call(0x0803381A, MGR, 23, maxins=900000)
    e.knob_raw(7, -200, True); e.knob_raw(7, 90, True); e.knob_raw(7, 4)                       # FX type 90, FXAMT +4
    check(e.val(0, 13) == 90, "FX type 90")
    clr_dn(); e.knob_raw(7, 1); clr_up()
    check(e.val(0, 13) == 0 and e.val(0, 9) == V.DEFAULTS[8], f"Clear + K8: FX type back to 0 ({e.val(0, 13)}) and FXAMT to {V.DEFAULTS[8]} ({e.val(0, 9)})")
    print("SC23.6 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
