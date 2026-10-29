"""SC49.2 (lanex): the drums' extra lane in the spare bits of each step.

    python tools/emu_lanex.py BUILD.bin manifest.json [PREVIOUS.bin PREVIOUS_manifest.json]

Through the controller and the drum players' step (emu_lazysave's harness):
  * the hit test (0x0804AA08) with probability 3 and every spare bit set: random & 7 = 0..3 hit, 4..7 not (the previous build: all hit);
  * the stock's add / remove of a hit (0x0804EC18 / 0x0804EC3E) on a step whose spare bits are set: kept (the previous build: lost);
  * playback of Drum 1's step: a chromatic code (no block = the chromatic pitch) = the step's S active, the pitch word written once; lane 0's
    chromatic step wins over the extra lane; a code lane (resonance) = the drum's saved resonance set;
  * Record held + K6 = Drum 1's lane carries the resonance (the value untouched), Record's state back; Record held + Shift + K1 = the pitch
    envelope; Record held + a chromatic pad = the chromatic pitch (S untouched);
  * recording (playing, Record): K6 turned = the code at the playing step; a chromatic pad = the extra lane's code, lane 0 untouched;
  * quantize (Shift + Play's c_qzhit): a hit moves alone, every step keeps its code;
  * Clear + K6 to the left = the lane erased in the playing pattern;
  * Record held + step 5 in the Note view with the resonance at 30 = code 31 on step 5;
  * LEDs: Record held, the resonance's knob (K6) white; with the chromatic pitch, Preset white / dark by the 256 ms clock.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import dpitch as DP  # noqa: E402
import lanex as LX  # noqa: E402

MGR = T.MGR
HIT, ADD, REM, STEP, DSP_W = 0x0804AA08, 0x0804EC18, 0x0804EC3E, 0x0804A714, 0x080292F8
FAKE = 0x2006E000


def lab(man, m, k): return int(man["report"][m]["labels"][k], 16)


def common(e):
    r0 = lambda fn, *a: (e.call(fn, *a, maxins=4_000_000), e.uc.reg_read(UC_ARM_REG_R0))[1]
    def setp(store, k, v, n=1):
        for fn in (0x080354FA, 0x0803542C): e.uc.mem_write(r0(fn, store, k), v.to_bytes(n, "little"))
    getp = lambda store, k: e.r8(r0(0x0803542C, store, k))
    eng = lambda d=0: e.r32(DP.ENG + 0x30 + 4 * (4 + d))
    base = lambda d=0: e.r32(DP.DP0 + DP.DP_SZ * d + 0x48) + DP.PAT_SZ * getp(eng(d), 0)
    return r0, setp, getp, eng, base


def stock_part(img, man):
    """the hit test and the stock's add / remove of a hit (no lanex labels needed)"""
    o = {}
    e = T.EL(img); e.at(300000); e.transport(0)
    r0, setp, getp, eng, base = common(e)
    e.btn(4); X.frame(e)
    b = base()
    e.uc.mem_write(b + 0, bytes([100])); e.uc.mem_write(b + 0x20, bytes([3 | 0xF8])); e.uc.mem_write(b + 0x60, bytes([1 | 0xC0]))
    o["hits"] = [r0(HIT, b, 0, 0, r) for r in range(8)]
    store = e.r32(e.r32(0x200438DC + 0xC))
    for k, v in ((0, 0), (8, 0xF8F8F8F8), (16, 0xC0C0C0C0)): setp(store, k, v, 4)     # steps 0-3: no hit, the spare bits set
    e.uc.mem_write(FAKE, bytes(16)); e.w32(FAKE + 0xC, store)
    e.call(ADD, FAKE, 2, maxins=4_000_000)
    wr = lambda k: e.r8(r0(0x080354FA, store, k) + 2)                     # the write copy (the setters' side; the read copy follows on commit)
    o["add"] = (wr(0), wr(8), wr(16))
    e.call(REM, FAKE, 2, maxins=4_000_000)
    o["rem"] = (wr(0), wr(8), wr(16))
    del e; gc.collect()
    return o


def lane_part(img, man):
    o = {}
    e = T.EL(img); e.at(300000); e.transport(0)
    r0, setp, getp, eng, base = common(e)
    L = lambda k: lab(man, "lanex", k)
    knob = lambda k, d: e.call(0x08033848, MGR, k, d & 0xFFFFFFFF, maxins=8_000_000)
    def shift(on): e.set_p0(e.r32(MGR + 0xC), 1 if on else 0)
    rec_down = lambda: e.call(0x08033320, MGR, 16, maxins=8_000_000)
    rec_up = lambda: e.call(0x0803381A, MGR, 16, maxins=8_000_000)
    p1 = lambda: getp(DP.TRANSPORT, 1)
    code_at = lambda st, d=0: r0(L("c_xlrd"), base(d), st)
    asg = lambda d=0: r0(L("c_xlasg"), d)
    res = lambda: r0(lab(man, "persist19", "c_dget"), 0, 6) & 0x7F
    S = lambda: r0(lab(man, "dpitch", "c_dpnow"), 0)
    dsp = []
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: dsp.append((uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2))), begin=DSP_W, end=DSP_W)
    e.btn(4); X.frame(e)
    o["view"] = e.r8(MGR + 0x152)
    b = base()
    for st in range(32): e.call(L("c_xlwr"), 0, st, 0, b, maxins=4_000_000)
    e.uc.mem_write(b + 0xA8, bytes([0xFF]) * 192)
    # ---- quantize (Shift + Play's c_qzhit): the hit moves alone, each step keeps its code
    qz = lab(man, "quant", "c_qzhit")
    def setstep(st, v, pr, fl, mi): e.uc.mem_write(b + st, bytes([v])); e.uc.mem_write(b + 0x20 + st, bytes([pr])); e.uc.mem_write(b + 0x40 + st, bytes([fl])); e.uc.mem_write(b + 0x60 + st, bytes([mi]))
    getstep = lambda st: tuple(e.r8(b + o_ + st) for o_ in (0, 0x20, 0x40, 0x60))
    setstep(3, 90, 5 | (0x0A << 3), 7, (1 << 4) | (2 << 6)); setstep(4, 0, 7 | (0x13 << 3), 0xFF, 1 << 6)
    c3, c4 = code_at(3), code_at(4); e.call(qz, b, 3, 4, maxins=4_000_000)
    o["qz_move"] = (c3, c4, code_at(3), code_at(4), getstep(3), getstep(4))
    setstep(6, 80, 7 | (0x05 << 3), 0xFF, (1 << 1) | (3 << 6)); c6 = code_at(6); e.call(qz, b, 6, 7, maxins=4_000_000)
    o["qz_zero"] = (c6, code_at(6), getstep(6))
    for st in (3, 4, 6, 7): setstep(st, 0, 7, 0xFF, 0)
    # ---- playback
    def step(st):
        store = e.r32(DP.DP0 + 8)
        setp(store, 0, getp(eng(), 0)); setp(store, 1, st); setp(store, 2, 0, 4)
        dsp.clear(); e.call(STEP, DP.DP0, maxins=8_000_000)
        tail = e.r32(DP.SESSION_OBJ + 0x14) + DP.TAIL
        return [v for v, a_ in dsp if a_ == DP.PITCH_X], e.r8(tail + DP.O_ACT) & 1, e.r8(tail + DP.O_EFF)
    o["asg0"] = asg()
    e.call(L("c_xlwr"), 0, 9, 71, b, maxins=4_000_000)
    o["code9"] = code_at(9)
    o["play9"] = step(9)
    e.call(L("c_xlwr"), 0, 10, 71, b, maxins=4_000_000); e.uc.mem_write(b + 0xA8 + 6 * 10, bytes([0x80 | 60]) * 6)
    o["play10"] = step(10)
    e.call(L("c_xlset"), 0, 6, maxins=4_000_000)
    e.call(L("c_xlwr"), 0, 12, 101, b, maxins=4_000_000)
    r_before = res(); step(12); o["play12"] = (r_before, res())
    # ---- assign
    e.call(L("c_xlset"), 0, 0, maxins=4_000_000)
    r_before = res(); q0 = p1(); rec_down(); knob(5, 3); rec_up()
    o["as_k6"] = (asg(), r_before, res(), q0, p1())
    rec_down(); shift(True); knob(0, 2); shift(False); rec_up()
    o["as_sk1"] = asg()
    e.btn(8); X.frame(e); e.btn(8); X.frame(e)
    dv = r0(lab(man, "sc11", "c_dview"), 0)
    o["chrom"] = (e.r8(MGR + 0x152), e.r8(dv + 0x51) & 1)
    s0 = S(); rec_down(); e.pad(10); rec_up()
    o["as_pad"] = (asg(), s0, S())
    # ---- recording: a chromatic pad at step 5
    setp(DP.TRANSPORT, 0, 1); setp(DP.TRANSPORT, 1, 1); setp(eng(), 1, 5)
    e.pad(10)
    o["rec_pad"] = (code_at(5), S(), bytes(e.uc.mem_read(b + 0xA8 + 30, 6)).hex())
    setp(DP.TRANSPORT, 1, 0); setp(DP.TRANSPORT, 0, 0)
    e.btn(4); X.frame(e)
    if e.r8(MGR + 0x152) != o["view"]: e.btn(4); X.frame(e)
    # ---- recording: K6 at step 7
    e.call(L("c_xlset"), 0, 6, maxins=4_000_000)
    setp(DP.TRANSPORT, 0, 1); setp(DP.TRANSPORT, 1, 1); setp(eng(), 1, 7)
    knob(5, 5)
    o["rec_k6"] = (code_at(7), res())
    setp(DP.TRANSPORT, 1, 0); setp(DP.TRANSPORT, 0, 0)
    # ---- Clear + K6 left
    clr = lambda on: e.call(0x08033320 if on else 0x0803381A, MGR, 23, maxins=8_000_000)
    n_before = sum(1 for st in range(32) if code_at(st))
    clr(True); knob(5, -1); clr(False)
    o["clr"] = (n_before, [st for st in range(32) if code_at(st)])
    # ---- snapshot: resonance 30, Record held + pad 5
    e.call(lab(man, "persist19", "c_dput"), 0, 6, 30, maxins=4_000_000)
    e.call(lab(man, "drumarp", "c_dapat"), 0, maxins=4_000_000); dp = e.uc.reg_read(UC_ARM_REG_R0)
    sb = e.r32(DP.DP0 + 0x48) + DP.PAT_SZ * dp
    rec_down(); e.pad(4); rec_up()
    o["snap"] = (e.r8(MGR + 0x152), r0(L("c_xlrd"), sb, 4))
    # ---- LEDs: K6 white while Record is held; the chromatic pitch = Preset blinking
    mh = r0(lab(man, "sc18", "c_mh"), 0)
    slot7 = e.r32(LX.MH_SLOT7) & ~1
    rec_down(); buf = r0(slot7, mh); o["kled"] = struct.unpack_from("<H", e.uc.mem_read(buf + 10, 2))[0]; rec_up()
    buf = r0(slot7, mh); o["kled_off"] = struct.unpack_from("<H", e.uc.mem_read(buf + 10, 2))[0]
    e.call(L("c_xlset"), 0, 0, maxins=4_000_000)
    frames = []
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: frames.append(uc.reg_read(UC_ARM_REG_R1)), begin=lab(man, "lanexb", "c_xlled"), end=lab(man, "lanexb", "c_xlled"))
    blink = []
    rec_down()
    for t in (300000, 300256):
        e.at(t); frames.clear(); e.leds()
        blink.append(struct.unpack_from("<H", e.uc.mem_read(frames[-1] + 2 * LX.LED_PRESET, 2))[0] if frames else None)
    rec_up()
    o["blink"] = blink
    del e; gc.collect()
    return o


def main(img, man, prev=None, pman=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    s = stock_part(Path(img).read_bytes(), man)
    check(s["hits"] == [1, 1, 1, 1, 0, 0, 0, 0], f"the hit test, probability 3 + the spare bits: random 0..3 hit, 4..7 not ({s['hits']})")
    check(s["add"] == (0x60, 0xFF, 0xC1), f"a hit added on a step with the spare bits: velocity 0x60, probability 7 | 0xF8, micro steps 1 | 0xC0 ({[hex(x) for x in s['add']]})")
    check(s["rem"] == (0, 0xFF, 0xC0), f"the hit removed: the spare bits kept ({[hex(x) for x in s['rem']]})")
    o = lane_part(Path(img).read_bytes(), man)
    check(o["asg0"] == 0 and o["code9"] == 71, f"no block: the chromatic pitch ({o['asg0']}); a code written and read back ({o['code9']})")
    c3, c4, c3b, c4b, s3, s4 = o["qz_move"]
    check((c3b, c4b) == (c3, c4) and s4[:3] == (90, 5 | (0x13 << 3), 7) and s4[3] & 0x3F == 1 and s3[0] == 0 and s3[2] == 0xFF and s3[3] & 0x3F == 0,
          f"quantize, a hit on micro step 4 of step 4 moved to step 5: the codes stay ({c3}, {c4} -> {c3b}, {c4b}), step 4 {s3}, step 5 {s4}")
    check(o["qz_zero"][0] == o["qz_zero"][1] and o["qz_zero"][2][3] & 0x3F == 1, f"quantize, a hit on micro step 1 of step 7 to micro step 0: its code stays ({o['qz_zero']})")
    w, act, eff = o["play9"]
    check(len(w) == 1 and act == 1 and eff == 70, f"step 9 (code 71): the step's S 70 active ({act}, {eff}), the pitch word written once ({[hex(x) for x in w]})")
    check(o["play10"][2] == 60, f"step 10: lane 0's chromatic step (60) wins over the extra lane ({o['play10']})")
    check(o["play12"][1] == 100, f"step 12, the lane on the resonance (code 101): the resonance {o['play12'][0]} -> {o['play12'][1]}")
    a, rb, ra, q0, q1 = o["as_k6"]
    check(a == 6 and rb == ra and q0 == q1, f"Record held + K6: the lane carries the resonance ({a}), its value untouched ({rb} -> {ra}), Record as it was ({q0} / {q1})")
    check(o["as_sk1"] == 1, f"Record held + Shift + K1: the pitch envelope ({o['as_sk1']})")
    check(o["chrom"][1] == 1 and o["as_pad"][0] == 0 and o["as_pad"][1] == o["as_pad"][2],
          f"chromatic view ({o['chrom']}), Record held + a pad: the chromatic pitch ({o['as_pad'][0]}), S untouched ({o['as_pad'][1]} -> {o['as_pad'][2]})")
    c5, s5, l0 = o["rec_pad"]
    check(c5 == min(s5, 126) + 1 and l0 == "ff" * 6, f"recording, a chromatic pad at step 5: code {c5} = S {s5} + 1, lane 0 untouched ({l0})")
    check(o["rec_k6"][0] == o["rec_k6"][1] + 1, f"recording, K6 at step 7: code {o['rec_k6'][0]} = the resonance {o['rec_k6'][1]} + 1")
    check(o["clr"][0] > 0 and o["clr"][1] == [], f"Clear + K6 left: the lane erased ({o['clr'][0]} steps -> {o['clr'][1]})")
    check(o["snap"][1] == 31, f"Record held + step 5 (view {o['snap'][0]}), the resonance 30: code {o['snap'][1]}")
    check(o["kled"] == LX.KNOB_WHITE and o["kled_off"] != LX.KNOB_WHITE, f"Record held: K6 white ({o['kled']:#x}), without Record its own ({o['kled_off']:#x})")
    check(o["blink"] in ([1, 0], [0, 1]), f"the chromatic pitch, Record held: Preset white / dark by the clock ({o['blink']})")
    if prev:
        p = stock_part(Path(prev).read_bytes(), pman)
        check(p["hits"] == [1] * 8 and p["add"][1] != 0xFF, f"the previous build: every random hits ({p['hits']}), the add loses the spare bits ({[hex(x) for x in p['add']]})")
    print(f"{Path(img).stem} LANEX RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text()), a[2] if len(a) > 2 else None,
                       json.loads(Path(a[3]).read_text()) if len(a) > 3 else None) else 0)
