"""SC33 ARM tests: real-time recording in the step-drummer (vcf21.use_rtrec), MIDI 1 and Synth 1, through the real routes (pads 0x08033282 / release 0x0803381A,
buttons 0x08033320), on the live RAM dump.

    python tools/emu_sc33_sd.py SC33.bin SC33_manifest.json
  * not recording (or the count-in): a step pad only auditions, the pattern does not change;
  * recording (the transport store 0x20011034: params 0 / 1 set, 2 clear): the pad's note and velocity (those of its audition) go into the step that plays (engine
    param 1) with the micro step = tick in the step (param 2) x 6 / ticks per step (6 by default; 12 with the sync index 5), one note per step (it replaces);
    the pad still auditions; Shift + pad is unchanged (adds / removes the note of the pad's own step).
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_LR, UC_ARM_REG_PC
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc27 as T27  # noqa: E402,F401  (applies the SC25..SC27 options)
import emu_sc22_4 as T4  # noqa: E402
V = T4.V
E20, MGR = T4.E20, T4.MGR
EMPTY = bytes([0, 0, 0, 0x60])
PLAY_STORE = 0x20011034


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["vcf20"]["labels"].items()}
    s6 = {k: int(v, 16) for k, v in man["report"]["sc06"]["labels"].items()}
    check("c_sdrtrec" in L, "c_sdrtrec is in the image")
    gc.collect(); e = E20(img, man)
    inj = []
    def hk(uc, a, s, d):
        inj.append(bytes(uc.mem_read(uc.reg_read(UC_ARM_REG_R0), 3))); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, hk, begin=s6["c_inject"], end=s6["c_inject"])
    for _ in range(30): e.vtick()
    def store(tr): return e.r32(V.ENGINE + 0x30 + 4 * ((tr + 2) & 3))
    def eng(tr, idx):
        e.call(0x0803542C, store(tr), idx); return e.uc.reg_read(UC_ARM_REG_R0)
    def seteng(tr, idx, v):                                                       # both buffers of the store
        st = store(tr); p = eng(tr, idx); b0, b1 = e.r32(st + 0xC), e.r32(st + 0x10)
        for bb in (b0, b1): e.uc.mem_write(bb + (p - (b0 if b0 <= p < b0 + 0x40 else b1)), bytes([v]))
    def transport(play, rec, countin=0):
        for bb in (e.r32(PLAY_STORE + 0xC), e.r32(PLAY_STORE + 0x10)):
            e.w32(bb + 0, play); e.w32(bb + 4, rec); e.w32(bb + 8, countin)
    def base(tr): return e.r32(e.r32(V.REC_GATE_OBJ + 0xC + 4 * ((tr + 2) & 3)) + 0x48)
    pat = lambda tr: base(tr) + 0xCA8 * (e.r8(eng(tr, 0)) & 7)
    step = lambda tr, s: bytes(e.uc.mem_read(pat(tr) + 28 * s, 28))
    def setstep(tr, s, mask, *units):
        e.uc.mem_write(pat(tr) + 28 * s, bytes(bytearray([mask, 7, 0, 0]) + b"".join(bytes(u) for u in units) + EMPTY * (6 - len(units))))
    def clearpat(tr):
        for s in range(32): setstep(tr, s, 0)
        e.uc.mem_write(pat(tr) + 0x3A8, bytes([0xFF] * (192 * 8)))
    note = lambda n, ln, mic, vel: bytes([1, 7, 0, 0, n, ln, mic, vel]) + EMPTY * 5
    none = bytes([0, 7, 0, 0]) + EMPTY * 6
    pad = lambda p: (e.padr(p), e.rel(p))
    def spad(p):
        e.set_p0(e.r32(MGR + 0xC), 1); e.padr(p); e.rel(p); e.set_p0(e.r32(MGR + 0xC), 0)
    ons = lambda: [n[3] for n in e.notes if n[0] == s6["c_non"] and n[2] == 2]

    for tr, name in ((0, "MIDI 1"), (2, "Synth 1")):
        clearpat(tr); setstep(tr, 0, 1, (60, 6, 0, 100)); setstep(tr, 5, 1, (72, 6, 0, 80))
        if tr == 0:
            e.btn(2); e.track(2); e.btn(8)
            pad(V.PAD_OSC); pad(V.PAD_OSC)
            for _ in range(40): e.vtick()
            pad(V.PAD_SD)
        else:
            e.btn(0); e.track(0)
            if not e.flag(): e.btn(0)
            pad(V.PAD_SD)
        seteng(tr, 1, 10); seteng(tr, 2, 3)
        check(e.r8(eng(tr, 1)) == 10 and e.r8(eng(tr, 2)) == 3, f"{name}: the step that plays = 10, tick 3")
        transport(1, 0)
        e.notes.clear(); inj.clear(); pad(5)
        check(step(tr, 10) == none and (ons() == [72] if tr == 0 else [x[1] for x in inj][:1] == [72]), f"{name}: playing, not recording: pad 6 only auditions (72)")
        transport(1, 1, 1)
        pad(5)
        check(step(tr, 10) == none, f"{name}: count-in: nothing recorded")
        transport(1, 1, 0)
        e.notes.clear(); inj.clear(); pad(5)
        check(step(tr, 10) == note(72, V.SD_LEN, 3, 80), f"{name}: recording: pad 6 writes note 72, velocity 80, micro step 3 into step 11 ({step(tr, 10)[:8].hex()})")
        check(ons() == [72] if tr == 0 else [x[1] for x in inj][:1] == [72], f"{name}: and still auditions")
        seteng(tr, 1, 12); seteng(tr, 2, 0); pad(0)
        check(step(tr, 12) == note(60, V.SD_LEN, 0, 100), f"{name}: pad 1 at step 13, tick 0: note 60, micro step 0 ({step(tr, 12)[:8].hex()})")
        setstep(tr, 12, 3, (50, 6, 0, 40), (52, 6, 0, 40)); pad(5)
        check(step(tr, 12) == note(72, V.SD_LEN, 0, 80), f"{name}: a step with a chord: replaced by the one note ({step(tr, 12)[:12].hex()})")
        e.uc.mem_write(pat(tr) + 0x382, bytes([5])); seteng(tr, 1, 14); seteng(tr, 2, 9); pad(0)
        check(step(tr, 14)[6] == 4, f"{name}: 12 ticks per step, tick 9: micro step 4 ({step(tr, 14)[6]})")
        e.uc.mem_write(pat(tr) + 0x382, bytes([3]))
        spad(3)
        check(step(tr, 3)[0] == 1 and step(tr, 14)[0] == 1, f"{name}: Shift + pad 4 still adds the note of its own step")
        transport(0, 0)
        pad(V.PAD_SD)
    print("SC33 STEP-DRUMMER RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
