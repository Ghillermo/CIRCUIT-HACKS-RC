"""SC31 ARM tests: the step-drummer keeps the notes of the pattern (vcf21.use_keepnote), MIDI 1 and Synth 1, through the real routes
(pads 0x08033282 / release 0x0803381A, knobs 0x08033848, buttons 0x08033320):

    python tools/emu_sc31.py SC31.bin SC31_manifest.json
  * opening the view: every step keeps the pitch of its first note (moved to unit 0, one note per step), not the tonic;
  * a new note (velocity page on an empty pair, Shift + step): the note of its pair, else of the nearest earlier note, else the tonic;
  * the audition plays the note of the step (its pair / the nearest earlier note) and its note-off finds the same note; a Shift + tap or a velocity of 0
    while a step is auditioned ends the audition first.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_LR, UC_ARM_REG_PC
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc27 as T27  # noqa: E402,F401  (applies the SC25..SC27 options)
import emu_sc22_4 as T4  # noqa: E402
V = T4.V
E20, MGR, TMPL, SYN = T4.E20, T4.MGR, T4.TMPL, T27.SYN
EMPTY = bytes([0, 0, 0, 0x60])


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["vcf20"]["labels"].items()}
    s6 = {k: int(v, 16) for k, v in man["report"]["sc06"]["labels"].items()}
    check("c_sdnnote" in L, "c_sdnnote is in the image")
    gc.collect(); e = E20(img, man)
    inj = []
    def hk(uc, a, s, d):
        inj.append(bytes(uc.mem_read(uc.reg_read(UC_ARM_REG_R0), 3))); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, hk, begin=s6["c_inject"], end=s6["c_inject"])
    for _ in range(30): e.vtick()
    def eng(tr, idx):                                                             # tr: 0 / 1 MIDI, 2 / 3 synth
        e.call(0x0803542C, e.r32(V.ENGINE + 0x30 + 4 * ((tr + 2) & 3)), idx); return e.uc.reg_read(UC_ARM_REG_R0)
    def base(tr): return e.r32(e.r32(V.REC_GATE_OBJ + 0xC + 4 * ((tr + 2) & 3)) + 0x48)
    pat = lambda tr: base(tr) + 0xCA8 * (e.r8(eng(tr, 0)) & 7)
    step = lambda tr, s: bytes(e.uc.mem_read(pat(tr) + 28 * s, 28))
    def setstep(tr, s, mask, *units):
        e.uc.mem_write(pat(tr) + 28 * s, bytes(bytearray([mask, 7, 0, 0]) + b"".join(bytes(u) for u in units) + EMPTY * (6 - len(units))))
    def clearpat(tr):
        for s in range(32): setstep(tr, s, 0)
        e.uc.mem_write(pat(tr) + 0x3A8, bytes([0xFF] * (192 * 8)))
    e.call(L["c_sdtonic"]); tonic = e.uc.reg_read(UC_ARM_REG_R0)
    note = lambda n, ln, mic, vel: bytes([1, 7, 0, 0, n, ln, mic, vel]) + EMPTY * 5
    none = bytes([0, 7, 0, 0]) + EMPTY * 6
    pad = lambda p: (e.padr(p), e.rel(p))
    def spad(p):
        e.set_p0(e.r32(MGR + 0xC), 1); e.padr(p); e.rel(p); e.set_p0(e.r32(MGR + 0xC), 0)
    btn = lambda b: e.call(0x08033320, MGR, b, maxins=900000)
    ons = lambda: [n[3] for n in e.notes if n[0] == s6["c_non"] and n[2] == 2]
    offs = lambda: [n[3] for n in e.notes if n[0] == s6["c_noff"] and n[2] == 2]

    # ================================================================ MIDI 1
    clearpat(0)
    setstep(0, 0, 1, (60, 6, 0, 100)); setstep(0, 3, 3, (64, 12, 0, 90), (67, 12, 0, 80)); setstep(0, 5, 2, (0, 0, 0, 0x60), (72, 3, 2, 70))
    e.btn(2); e.track(2); e.btn(8)
    pad(V.PAD_OSC); pad(V.PAD_OSC)
    for _ in range(40): e.vtick()
    pad(V.PAD_SD)
    check(step(0, 0) == note(60, 6, 0, 100) and step(0, 3) == note(64, 12, 0, 90) and step(0, 5) == note(72, 3, 2, 70) and step(0, 1) == none,
          f"MIDI 1, the view opens: each step keeps its first note (60, 64, 72), not the tonic {tonic}: {step(0, 0)[:8].hex()} {step(0, 3)[:12].hex()} {step(0, 5)[:12].hex()}")
    btn(19)                                                                       # the velocity page
    e.knob_raw(1, -127)
    check(step(0, 2) == none and step(0, 3) == none, "K2 to 0: the notes of the pair are removed")
    e.knob_raw(1, 30)
    check(step(0, 2) == note(60, V.SD_LEN, 0, 30), f"K2 +30: a new note with the note of the nearest earlier step (60): {step(0, 2)[:8].hex()}")
    e.knob_raw(3, 50)
    check(step(0, 6) == note(72, V.SD_LEN, 0, 50), f"K4 +50 on an empty pair: the nearest earlier note (72, step 6): {step(0, 6)[:8].hex()}")
    btn(20)
    spad(7)
    check(step(0, 7) == note(72, V.SD_LEN, 0, 50), f"Shift + pad 8: the note of its pair (72): {step(0, 7)[:8].hex()}")
    spad(7)
    setstep(0, 6, 1, (65, 6, 0, 50))
    spad(9)
    check(step(0, 9)[4] == 65, f"Shift + pad 10 (an empty pair): the nearest earlier note (65): {step(0, 9)[4]}")
    spad(9)
    for s in range(32): setstep(0, s, 0)
    spad(12)
    check(step(0, 12)[4] == tonic, f"no note anywhere: the tonic ({step(0, 12)[4]})")
    # the audition
    clearpat(0); setstep(0, 0, 1, (60, 6, 0, 100)); setstep(0, 5, 1, (72, 6, 0, 80))
    e.notes.clear(); e.padr(5)
    check(ons() == [72], f"a tap on pad 6 (step 6, note 72): the note-on of 72 ({ons()})")
    e.rel(5)
    check(offs() == [72], f"the release: the note-off of 72 ({offs()})")
    e.notes.clear(); e.padr(2); e.rel(2)
    check(ons() == [60] and offs() == [60], f"a step of an empty pair: the nearest earlier note (60) on and off ({ons()}, {offs()})")
    e.notes.clear(); e.padr(5)
    e.set_p0(e.r32(MGR + 0xC), 1); e.padr(5); e.rel(5); e.set_p0(e.r32(MGR + 0xC), 0)     # Shift + the same pad while it is held: its note goes
    check(step(0, 5) == none and offs() == [72], f"Shift + tap while auditioned: the audition ends first with the note-off of 72 ({offs()})")
    e.rel(5)
    check(offs() == [72] and len(ons()) == 1, f"the release afterwards: nothing more ({ons()}, {offs()})")
    pad(V.PAD_SD)                                                                  # close the view

    # ================================================================ Synth 1
    clearpat(2); setstep(2, 0, 1, (60, 6, 0, 100)); setstep(2, 3, 3, (64, 12, 0, 90), (67, 12, 0, 80))
    e.btn(0); e.track(0)
    if not e.flag(): e.btn(0)
    c = e.padr(V.PAD_SD); e.rel(V.PAD_SD)
    check(c == [] and step(2, 0) == note(60, 6, 0, 100) and step(2, 3) == note(64, 12, 0, 90) and step(2, 1) == none,
          f"Synth 1, the view opens: the notes are kept (60, 64): {step(2, 0)[:8].hex()} {step(2, 3)[:12].hex()}")
    btn(19); e.knob_raw(4, 40); btn(20)
    check(step(2, 8) == note(64, V.SD_LEN, 0, 40), f"K5 +40 on an empty pair: the nearest earlier note (64): {step(2, 8)[:8].hex()}")
    chan = e.r8(e.r32(V.TXOBJ + 0xC))
    inj.clear(); e.padr(3)
    check(inj == [bytes([0x90 | chan, 64, 90])], f"a tap on pad 4: an internal note-on of 64 with the velocity of the step ({[x.hex() for x in inj]})")
    e.rel(3)
    check(inj[1:] == [bytes([0x80 | chan, 64, 0])], f"the release: the note-off of 64 ({[x.hex() for x in inj[1:]]})")
    inj.clear(); e.padr(1); e.rel(1)
    check([x[1] for x in inj] == [60, 60], f"step 2 (pair of step 1): the note of the pair (60) ({[x.hex() for x in inj]})")
    print("SC31 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
