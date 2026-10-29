"""SC48.9 (snapall): Record held + a step on Synth 1 / 2 and the drums.

    python tools/emu_snapall.py BUILD.bin manifest.json [PREVIOUS.bin PREVIOUS_manifest.json]

Through the controller (emu_lazysave's harness): the pack's patch read (mpatch.c_mpr) answered by the test with a record whose 8 macro positions
are 64 (the card is not emulated):
  * Synth 1, its track view: macros 2 and 5 at 100 / 20 (through the session setter), the others at 64; Record held + step pad 3 = lanes 2 and 5
    of step 3 hold 100 / 20 on their 6 micro steps, the other lanes untouched, the step's notes unchanged (the press swallowed); Record let go:
    the recording state as it was; page 2 (17-32): pad 3 = step 19;
  * Drum 1, its Note view: pitch 70 and EQ 64 (its default), decay / distortion default; Record held + pad 5 = lane 0 of step 5 = 70, lanes 1-3
    untouched; the step's hit unchanged;
  * without Record held: the pads do what they did (as the previous build);
  * the previous build: Record held + a Synth 1 step writes nothing.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import packio as PK  # noqa: E402
import drumarp as DA  # noqa: E402
import snapall as SA  # noqa: E402

MGR = T.MGR
PARAM_SET, CTX = 0x08034D92, 0x200069E4


def run(img, man):
    R = man["report"]
    e = T.EL(img); e.at(300000); e.transport(0)
    def skip(uc): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    mpr = int(R["mpatch"]["labels"]["c_mpr"], 16)
    def fake_mpr(uc, a, s, d):                                           # the record: macro positions 64
        buf, n = uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R3)
        rec = bytearray([0x40]) * n
        uc.mem_write(buf, bytes(rec)); uc.reg_write(UC_ARM_REG_R0, 0); skip(uc)
    e.uc.hook_add(UC_HOOK_CODE, fake_mpr, begin=mpr, end=mpr)
    for f in (PK.BUF_LOCK, PK.BUF_UNLOCK): e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: (uc.reg_write(UC_ARM_REG_R0, 0), skip(uc)), begin=f, end=f)
    this = e.r32(e.r32(e.r32(CTX) + 0x10))
    def setp(t, i, v): e.call(PARAM_SET, this + 4, t, i, v, maxins=4_000_000)
    sdpat = int(R["vcf20"]["labels"]["c_sdpat"], 16)
    def pat(track): e.call(sdpat, track); return e.uc.reg_read(UC_ARM_REG_R0)
    lane = lambda base, l, step: bytes(e.uc.mem_read(base + 0x3A8 + 192 * l + 6 * step, 6))
    rec_down = lambda: e.call(0x08033320, MGR, 16, maxins=8_000_000)
    rec_up = lambda: e.call(0x0803381A, MGR, 16, maxins=8_000_000)
    p1 = lambda: (e.call(0x0803542C, 0x20011034, 1), e.r8(e.uc.reg_read(UC_ARM_REG_R0)))[1]
    o = {}
    # ---- Synth 1
    for m in range(8): setp(0, 174 + 17 * m, 64)
    setp(0, 174 + 17 * 2, 100); setp(0, 174 + 17 * 5, 20)
    e.btn(0); X.frame(e)
    if e.r8(MGR + 0x152) != 1: e.btn(0); X.frame(e)
    o["syn_view"] = e.r8(MGR + 0x152)
    base = pat(2)
    for l in range(8): e.uc.mem_write(base + 0x3A8 + 192 * l, bytes([0xFF]) * 192)
    st3 = bytes(e.uc.mem_read(base + 28 * 2, 28))
    r0 = p1(); rec_down(); e.pad(2); rec_up()
    o["syn"] = [lane(base, l, 2) for l in range(8)]
    o["syn_step"] = bytes(e.uc.mem_read(base + 28 * 2, 28)) == st3
    o["syn_rec"] = (r0, p1())
    e.pad(2); o["syn_plain"] = bytes(e.uc.mem_read(base + 28 * 2, 28)) != st3        # without Record: the stock's step press (a note)
    # ---- Drum 1
    e.btn(4); X.frame(e)
    o["drum_view"] = e.r8(MGR + 0x152)
    e.call(int(R["sc18"]["labels"]["c_mh"], 16), 0); h_ = e.uc.reg_read(UC_ARM_REG_R0); st = e.r32(h_ + 0xC)
    for k, v in enumerate((70, 127, 0, 64)):
        for fn in (0x080354FA, 0x0803542C): e.call(fn, st, k); e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0), bytes([v]))
    e.call(int(R["drumarp"]["labels"]["c_dapat"], 16), 0); dp = e.uc.reg_read(UC_ARM_REG_R0)
    db = e.r32(DA.DP0 + 0x48) + 0x6A8 * dp
    for l in range(8): e.uc.mem_write(db + 0xA8 + 192 * l, bytes([0xFF]) * 192)
    v0 = e.r8(db + 4)
    rec_down(); e.pad(4); rec_up()
    o["drum"] = [bytes(e.uc.mem_read(db + 0xA8 + 192 * l + 6 * 4, 6)) for l in range(4)]
    o["drum_hit"] = e.r8(db + 4) == v0
    e.pad(4); o["drum_plain"] = e.r8(db + 4) != v0
    del e; gc.collect()
    return o


def main(img, man, prev=None, pman=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    o = run(Path(img).read_bytes(), man)
    want = [bytes([100]) * 6 if l == 2 else bytes([20]) * 6 if l == 5 else bytes([0xFF]) * 6 for l in range(8)]
    check(o["syn"] == want, f"Synth 1 (view {o['syn_view']}), Record + step 3: lanes 2 / 5 = 100 / 20, the others empty ({[x.hex() for x in o['syn']]})")
    check(o["syn_step"] and o["syn_rec"][0] == o["syn_rec"][1], f"the step's notes unchanged ({o['syn_step']}), recording as it was ({o['syn_rec']})")
    dwant = [bytes([70]) * 6] + [bytes([0xFF]) * 6] * 3
    check(o["drum"] == dwant, f"Drum 1 (view {o['drum_view']}), Record + step 5: lane 0 = 70, lanes 1-3 empty ({[x.hex() for x in o['drum']]})")
    check(o["drum_hit"] and o["drum_plain"], f"the step's hit unchanged ({o['drum_hit']}); without Record the stock's press ({o['drum_plain']})")
    if prev:
        p = run(Path(prev).read_bytes(), pman)
        check(all(x == bytes([0xFF]) * 6 for x in p["syn"]), f"the previous build: nothing written on Synth 1 ({[x.hex() for x in p['syn']]})")
        check(o["syn_plain"] == p["syn_plain"] and o["drum_plain"] == p["drum_plain"],
              f"without Record the step presses as the previous build (Synth 1 step changed: {o['syn_plain']} / {p['syn_plain']}, drum hit: {o['drum_plain']} / {p['drum_plain']})")
    print(f"{Path(img).stem} SNAPALL RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text()), a[2] if len(a) > 2 else None,
                       json.loads(Path(a[3]).read_text()) if len(a) > 3 else None) else 0)
