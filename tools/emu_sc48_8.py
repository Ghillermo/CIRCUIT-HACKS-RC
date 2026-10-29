"""SC48.8 / Beta 3.44 ARM tests: tools/trigled.py (Shift = the track buttons white while their gate is on) and autorel.use_v2() (the de-automation
view: yellow only on the steps with automation; Shift + a yellow step = its values until Shift is let go), through the controller, the real LED
task, the stock's note path down to the transmitter and the stock's step preview route.

    python tools/emu_sc48_8.py SC48.8.bin SC48.8_manifest.json [SC48.7.bin SC48.7_manifest.json]
  * trigled: Shift and nothing sounding = the eight track buttons dark (as the stock); a MIDI 1 pad held = MIDI 1's button white with Shift, its own
    colour without, dark again when the pad is let go; Drum 1 / Drum 4 pads held (notes 60 / 65 on track 16) = Drum 1's / Drum 4's buttons,
    each going dark with its own note-off; a drum note-on with velocity 0 = off; MIDI 1's sequencer (the player's per-tick calls): white while
    its note sounds, dark after its note-off; Synth 1: its sounding-notes store with a note in it = white (the synth's sound path does not run
    in emulation: the store is written here as the note dispatcher writes it);
  * autorel v2, MIDI 1's Velocity view with Shift: the step pads keep the stock's colours, step 5 (lane 4 automated) yellow, step 7 (marked, with
    automation) red; Shift + pad 5 = no mark, the lane played through the stock's lane target (id 0x17, 90), its value before kept; Shift still
    held = nothing more; Shift let go = the value before played back, nothing kept; Shift + pad 7 (marked) = unmarked; Shift + pad 8 (no
    automation) = marked; the own engine on: the preview through c_vapply, back the same way; Synth 1: the macro of lane 3 moves to the step's
    value and comes back;
  * the previous build (if given): Shift = every step pad yellow (what the user saw).
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_LR, UC_ARM_REG_PC
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
import autorel as AR  # noqa: E402
import trigled as TG  # noqa: E402
import arp as A  # noqa: E402
import emu_arp as EAm  # noqa: E402
import emu_sc40_8 as T8  # noqa: E402
import emu_lazysave as LZ  # noqa: E402
import packio as PK  # noqa: E402

V = T4.V
MGR = X.MGR
TX = 0x20011334


def chord(units, n=8): return EAm.chord_steps(units, n)


class ET(T8.E8):
    """emu_arp's harness with the note path running down to the transmitter (the DSP writes run: skipping them, as EP does, drops the drums'
    note-ons before the transmitter), the recorder's gate, sleep and a wait on the DSP skipped; the mod's card reads / the DSP semaphore answered
    as in emu_lazysave's"""
    def __init__(self, img, man):
        super().__init__(img, man, {k: int(v, 16) for k, v in man["report"]["patchain"]["labels"].items()})
        def skip(uc, a, s_, d): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        for f in (V.REC_GATE, 0x0801BE78, 0x08029A00): self.uc.hook_add(UC_HOOK_CODE, skip, begin=f, end=f)
        def fail(uc, a, s_, d): uc.reg_write(UC_ARM_REG_R0, 0xFFFFFFFF); skip(uc, a, s_, d)
        for f in LZ.SD_OPS: self.uc.hook_add(UC_HOOK_CODE, fail, begin=f, end=f)
        def zero(uc, a, s_, d): uc.reg_write(UC_ARM_REG_R0, 0); skip(uc, a, s_, d)
        for f in (PK.SEM_TAKE, PK.SEM_GIVE, PK.DSP_READ): self.uc.hook_add(UC_HOOK_CODE, zero, begin=f, end=f)
    btn = LZ.EL.btn
    def shift(self, on): self.set_p0(self.r32(MGR + 0xC), 1 if on else 0)
    def transport(self, on): EAm.EA.setp(self, A.TRANSPORT, 0, bytes([on]))


def trig_part(img, man, check):
    e = ET(img, man)
    L = {k: int(v, 16) for k, v in man["report"]["trigled"]["labels"].items()}
    btns = lambda shift: (e.shift(shift), X.frame(e)[32:40], e.shift(False))[1]
    hold = lambda q: e.call(PRESS, MGR, q, 100, maxins=8_000_000)
    let = lambda q: e.call(RELEASE, MGR, q, maxins=8_000_000)
    e.btn(2); e.btn(9)
    b0 = btns(True)
    check(b0 == [0] * 8, f"Shift, nothing sounding: the track buttons dark ({[hex(x) for x in b0]})")
    hold(20); bs = btns(True); bn = btns(False)
    check(bs == [0, 0, TG.WHITE, 0, 0, 0, 0, 0] and bn[2] != TG.WHITE, f"a MIDI 1 pad held: with Shift MIDI 1 white ({[hex(x) for x in bs]}), without its own ({bn[2]:#x})")
    let(20); bs = btns(True)
    check(bs == [0] * 8, f"let go: dark again ({[hex(x) for x in bs]})")
    e.btn(4); e.btn(9)
    hold(28); b1 = btns(True); hold(24); b2 = btns(True); let(28); b3 = btns(True); let(24); b4 = btns(True)
    check(b1[4:] == [TG.WHITE, 0, 0, 0] and b2[4:] == [TG.WHITE, 0, 0, TG.WHITE] and b3[4:] == [0, 0, 0, TG.WHITE] and b4 == [0] * 8,
          f"Drum 1 / Drum 4 pads held and let go one by one: {[x[4:] for x in (b1, b2, b3, b4)]}")
    e.call(L["c_tgon"], TX, 0x10, 62, 100, maxins=2_000_000); b5 = btns(True)
    e.call(L["c_tgon"], TX, 0x10, 62, 0, maxins=2_000_000); b6 = btns(True)
    check(b5[5] == TG.WHITE and b6 == [0] * 8, f"Drum 2's note-on, then one with velocity 0: white, dark ({b5[5]:#x}, {b6[5]:#x})")
    # MIDI 1's sequencer: a note at step 0, 2 steps long
    e.call(int(man["report"]["vcf20"]["labels"]["c_sdpat"], 16), 0, maxins=1_000_000)               # MIDI 1's pattern (c_sdpat: MIDI 1 = 0)
    e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0), chord([(60, 12, 0, 100)]))
    e.transport(1)
    P = A.PLAYER0 + A.PLAYER_SZ * 2; st = e.r32(A.ENG + 0x30 + 4 * 2)
    seen = []
    for s in range(4):
        EAm.EA.setp(e, st, 1, bytes([s]))
        for k in range(6):
            EAm.EA.setp(e, st, 2, struct.pack("<I", k))
            e.call(EAm.TICK_BUILD, P, maxins=3_000_000); e.call(EAm.TICK_PLAY, P, maxins=3_000_000)
        seen.append(btns(True)[2])
    e.transport(0)
    check(seen == [TG.WHITE, TG.WHITE, 0, 0], f"MIDI 1's sequencer, a note 2 steps long: steps 0-3 = {[hex(x) for x in seen]}")
    # Synth 1: its sounding-notes store
    st0 = e.r32(TG.VIEW0 + TG.NOTES_OFF)
    e.call(TG.STORE_READ, st0); rp = e.uc.reg_read(UC_ARM_REG_R0)
    old = bytes(e.uc.mem_read(rp, 20)); e.uc.mem_write(rp, bytes(7) + b"\x10" + bytes(12)); b7 = btns(True)
    e.uc.mem_write(rp, old); b8 = btns(True)
    check(b7 == [TG.WHITE] + [0] * 7 and b8 == [0] * 8, f"Synth 1, note 60 in its sounding-notes store: white, then dark ({b7[0]:#x}, {b8[0]:#x})")
    del e; gc.collect()


def deauto_part(img, man, check, previous=False):
    e = X.EP(img, man)
    R = man["report"]
    pat = lambda t: e.r0(int(R["vcf20"]["labels"]["c_sdpat"], 16), (t + 2) % 4)
    b3 = lambda t, s: e.r8(pat(t) + 28 * s + 3)
    def lane(t, k, s, v): e.uc.mem_write(pat(t) + 0x3A8 + 192 * k + 6 * s, bytes([v]) * 6)
    def mark(t, s): a = pat(t) + 28 * s + 3; e.uc.mem_write(a, bytes([e.r8(a) | 0x80]))
    for t in (0, 2):
        for k in range(8):
            for s in range(32): lane(t, k, s, 0xFF)
    e.btn(2); e.btn(10)
    sh = lambda: (e.shift(True), X.frame(e)[:16], e.shift(False))[1]
    s0 = sh(); n0 = X.frame(e)[:16]
    lane(2, 4, 4, 90); lane(2, 1, 6, 30); mark(2, 6)
    s1 = sh()
    if previous:
        check(s1 == [AR.COL_AV] * 6 + [AR.COL_MARK] + [AR.COL_AV] * 9, f"the previous build: Shift = every step pad yellow, the mark red ({[hex(x) for x in s1]})")
        del e; gc.collect(); return
    check(AR.COL_AV not in s0, f"Shift, no automation: no yellow, the stock's colours ({[hex(x) for x in s0]}; without Shift {[hex(x) for x in n0]})")
    check(s1[4] == AR.COL_AV and s1[6] == AR.COL_MARK and all(s1[j] == s0[j] for j in range(16) if j not in (4, 6)),
          f"step 5 automated yellow, step 7 marked red, the rest as before ({[hex(x) for x in s1]})")
    sets, apps = [], []
    if "autorel" in R.get("hole", {}).get("blocks", {}): lo, hi = (int(x, 16) for x in R["hole"]["blocks"]["autorel"][:2])
    else: lo = int(R["autorel"]["arm_start"], 16); hi = max(int(v, 16) for v in R["autorel"]["labels"].values()) + 0x100   # (SC49.1: at the end)
    def lset(uc, a, s_, d):                                                         # autorel's calls (not the stock's own nested one behind it)
        if lo <= uc.reg_read(UC_ARM_REG_LR) & ~1 < hi: sets.append((uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2)))
    e.uc.hook_add(UC_HOOK_CODE, lset, begin=AR.LANE_SET, end=AR.LANE_SET)
    def vap(uc, a, s_, d): apps.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2))); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, vap, begin=e.vl["c_vapply"], end=e.vl["c_vapply"])
    ms = lambda: e.r8(e.r0(0x0803542C, e.r32(e.r32(AR.MACRO_OBJ + 0x2C) + 4 * 2), 4))
    base = ms()
    e.shift(True); e.pad(4); X.frame(e)
    pend, kept = e.r32(AR.PVR + 4), e.r8(AR.PVR + 8 + 8 * 2 + 4)
    check(not b3(2, 4) & 0x80 and sets == [(0x18, 90)] and pend == 1 << 20 and kept == base,
          f"MIDI 1, Shift + pad 5: no mark ({b3(2, 4):#x}), lane 5 played ({[(hex(i), v) for i, v in sets]}), its value before kept ({pend:#x}, {kept} = {base})")
    ms1 = ms(); sets.clear(); X.frame(e)
    check(sets == [], f"Shift still held: nothing more ({sets}); the macro store's p[4] = {ms1}")
    e.shift(False); X.frame(e)
    check(sets == [(0x18, base)] and e.r32(AR.PVR + 4) == 0, f"Shift let go: the value before back ({[(hex(i), v) for i, v in sets]}), nothing kept")
    sets.clear()
    e.shift(True); e.pad(6); e.pad(7); e.shift(False); X.frame(e)
    check(not b3(2, 6) & 0x80 and b3(2, 7) & 0x80 and sets == [], f"Shift + pad 7 (marked) = unmarked ({b3(2, 6):#x}), Shift + pad 8 (no automation) = marked ({b3(2, 7):#x}), nothing played")
    # the own engine on: through c_vapply
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05]))
    row = bytes(e.uc.mem_read(e.r0(e.vl["c_vrow"], 0), 8)); code = row[4]
    u0 = e.r0(e.vl["c_vtou"], code, e.val(0, code) & 0xFFFFFFFF)
    e.shift(True); e.pad(4); X.frame(e); a1 = list(apps); e.shift(False); X.frame(e)
    check(a1 == [(0, 4, 90)] and apps == [(0, 4, 90), (0, 4, u0)] and sets == [],
          f"MIDI 1 with the own engine on: c_vapply (track 0, lane 4, 90), then the value before ({u0}): {apps}; the stock's lane target untouched ({sets})")
    # Synth 1: the macro moves and comes back
    e.btn(0); e.btn(10); lane(0, 3, 2, 77)
    g = lambda: e.r0(V.GETTER, 0, 174 + 17 * 3)
    kp = g(); sets.clear()
    e.shift(True); e.pad(2); X.frame(e); g1 = g(); e.shift(False); X.frame(e); g2 = g()
    check(sets == [(3, 77), (3, kp)] and g1 == 77 and g2 == kp, f"Synth 1, Shift + pad 3: macro 4 {kp} -> {g1} -> {g2} (lane target {sets})")
    del e; gc.collect()


def main(img, man, prev=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    trig_part(img, man, check)
    deauto_part(img, man, check)
    if prev: deauto_part(prev[0], prev[1], check, previous=True)
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    prev = (Path(a[2]).read_bytes(), json.loads(Path(a[3]).read_text())) if len(a) >= 4 else None
    sys.exit(1 if main(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text()), prev) else 0)
