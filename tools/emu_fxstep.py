"""Alpha 7.08 (tools/fxstep.py): the Master FX step sequencer, through the controller (pads, Clear) and the real LED task.
  * Master FX view: pad 1 held + step pad 3 = Gater on step 3; pad 26 held + step 5 = its slot; pad 7 held + step 1 = the sample; pads 2 + 4 held
    + step 3 = added (Gater, Auto-Filter, Digitise);
  * Clear + an empty step 8 = muted; an FX on a muted step = the mute off; Clear + a step with FX = empty;
  * a step pad alone = the song pointer as before (the held step);
  * the LEDs: a step with FX in its first pad's colour, a muted step red;
  * playing, the step cached at 3: c_fxsq (now c_fqsq) = the slot / mute bits, every c_fsqfx call + the top effects; the sample's start + gate
    entering step 1, its gate off leaving it; stopped: nothing;
  * the save writes the block (MIDI 1's pattern 8, settings + 8) with its signature, the load reads it back; a garbage block (0xFF) = empty;
  * the engine row's pad 31 (the old FX sequencer) is a branch past it.

    python tools/emu_fxstep.py BUILD.bin manifest.json
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_mixsolo as EM  # noqa: E402
import fxstep as F  # noqa: E402
import build_sc17 as S  # noqa: E402
import build_sc14 as s14  # noqa: E402
import unicorn.arm_const as A  # noqa: E402


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    R = man["report"]
    lab = {k: int(v, 16) for k, v in R["fxstep"]["labels"].items()}
    s17 = {k: int(v, 16) for k, v in R["sc17"]["labels"].items()}
    e = EM.P(img, man); e.btn(14); e.btn(14)
    MGR = EM.MGR
    check(e.r0(s17["c_gact"]) != 0, "the Master FX view is showing")
    def mask(s): return struct.unpack("<H", bytes(e.uc.mem_read(F.FXS + F.O_M + 2 * s, 2)))[0]
    def clear(on): e.set_p0(e.r32(e.r32(MGR + 0x20) + 0xC), 1 if on else 0)
    def hold_tap(pads, step):
        for p in pads: e.press(p)
        e.tap(8 + step)
        for p in pads: e.release(p)
    e.r0(lab["c_fqst"])
    for s in range(16): e.uc.mem_write(F.FXS + F.O_M + 2 * s, b"\0\0")
    # ---- assigning
    hold_tap([0], 2); check(mask(2) == 0x0001, f"pad 1 held + step 3: the Gater ({mask(2):#06x})")
    hold_tap([25], 4); check(mask(4) == 0x0100, f"pad 26 held + step 5: its slot ({mask(4):#06x})")
    hold_tap([6], 0); check(mask(0) == 0x0040, f"pad 7 held + step 1: the sample ({mask(0):#06x})")
    hold_tap([1, 3], 2); check(mask(2) == 0x000B, f"pads 2 + 4 held + step 3: added ({mask(2):#06x})")
    clear(True); e.tap(8 + 7); clear(False); check(mask(7) == 0x8000, f"Clear + empty step 8: muted ({mask(7):#06x})")
    hold_tap([4], 7); check(mask(7) == 0x0010, f"pad 5 held + the muted step: the Phaser, mute off ({mask(7):#06x})")
    clear(True); e.tap(8 + 7); clear(False); check(mask(7) == 0, f"Clear + a step with FX: empty ({mask(7):#06x})")
    clear(True); e.tap(8 + 9); clear(False); clear(True); e.tap(8 + 9); clear(False)
    check(mask(9) == 0, f"Clear + a muted step: empty ({mask(9):#06x})")
    clear(True); e.tap(8 + 9); clear(False)
    def dup(on): e.set_p0(e.r32(e.r32(MGR + 0x20) + 0xC), 2 if on else 0)
    dup(True); e.tap(8 + 13); dup(False); check(mask(13) == F.RANDOM, f"Duplicate + empty step 14: random ({mask(13):#06x})")
    hold_tap([0], 14); hold_tap([4], 14); hold_tap([25], 14); dup(True); e.tap(8 + 14); dup(False)
    check(mask(14) == F.RANDOM | 0x0111, f"step 15: Gater, Phaser, pad 26, then Duplicate: random among them ({mask(14):#06x})")
    clear(True); e.tap(8 + 15); clear(False); dup(True); e.tap(8 + 15); dup(False)
    check(mask(15) == F.RANDOM, f"Duplicate + a muted step: random, the mute off ({mask(15):#06x})")
    dup(True); e.tap(8 + 15); dup(False); check(mask(15) == 0, f"Duplicate again: random off ({mask(15):#06x})")
    st = e.r0(s17["c_gfst"]) - S.GFX_OFF
    e.press(8 + 11); h1 = e.r8(st + 23); e.release(8 + 11); h2 = e.r8(st + 23)
    check(h1 == 12 and h2 == 0 and mask(11) == 0, f"a step pad alone: the song pointer's held step ({h1}, then {h2})")
    # ---- LEDs
    f = e.frame()
    if man.get("marker") != "A7.08":                                   # (use_smpcol) the sample's step in its yellow
        check(f[8 + 0] & 0xFF == S.SMP_ON, f"LEDs: step 1 (the sample) yellow ({f[8]:#x})")
    else: print(f"info: step 1 (the sample) = {f[8]:#x} (7.08: pad 7's LED is drawn later)")
    check(f[8 + 13] & 0xFF == F.COL_RAND, f"LEDs: random step 14 violet ({f[21]:#x})")
    check(f[8 + 2] == f[0] and f[8 + 9] & 0xFF == F.COL_MUTE and f[8 + 4] == f[25], f"LEDs: step 3 = pad 1's ({f[10]:#x} / {f[0]:#x}), step 10 red ({f[17]:#x}), step 5 = pad 26's ({f[12]:#x})")
    # ---- playing
    blk = e.r0(s17["c_gfst"])
    def at_step(s):
        t = e.r32(s14.TICK) >> 6
        e.uc.mem_write(st + S.GFX_OFF + S.S_SPS, struct.pack("<I", ((t & 0xFFFFFF) << 8) | s))
    def call4(fn):
        e.uc.reg_write(A.UC_ARM_REG_R4, blk); return e.r0(fn)
    e.transport(1)
    at_step(2); sq = call4(lab["c_fqsq"]); fx = call4(lab["c_fqfx"])
    check(sq & 0xBF == 0 and fx & 0x0B == 0x0B, f"playing step 3: c_fxsq no slots ({sq:#x}), c_fsqfx + Gater, AF, Digitise ({fx:#x})")
    at_step(4); sq = call4(lab["c_fqsq"]); check(sq == 0x01, f"step 5: c_fxsq = the slot of pad 26 ({sq:#x})")
    at_step(9); sq = call4(lab["c_fqsq"]); check(sq == 0x80, f"step 10: c_fxsq = mute ({sq:#x})")
    picks = set(); seen = set()
    for k in range(40):
        at_step(14); a_ = call4(lab["c_fqcur"]); at_step(13); b_ = call4(lab["c_fqcur"]); a2 = call4(lab["c_fqcur"])
        picks.add(a_); seen.add(b_)
        if k == 0: check(a2 == b_, f"a random step plays the same pick for its whole step ({b_:#x}, {a2:#x})")
    check(picks == {0x01, 0x10, 0x100}, f"random step 15 picks among its FX: {sorted(hex(x) for x in picks)}")
    check(seen <= {1, 2, 4, 8, 16, 32} and len(seen) >= 4, f"empty random step 14 picks top effects: {sorted(hex(x) for x in seen)}")
    jf0 = e.r8(blk + S.S_JF)
    at_step(0); call4(lab["c_fqsq"]); jf1 = e.r8(blk + S.S_JF)
    at_step(1); call4(lab["c_fqsq"]); jf2 = e.r8(blk + S.S_JF)
    check(jf1 & 0x30 == F.SMP_START and jf1 & S.SMB_GATE and not jf2 & S.SMB_GATE,
          f"the sample: start + gate entering step 1 ({jf0:#x} -> {jf1:#x}), the gate off leaving it ({jf2:#x})")
    for fn in ("c_fqsq", "c_fqfx"): call4(s17["c_smtick"]) if False else None
    e.transport(0); at_step(2); sq = call4(lab["c_fqsq"]); fx = call4(lab["c_fqfx"]); fs = call4(s17["c_fsqfx"])
    check(sq == 0 and fx == fs, f"stopped: nothing ({sq:#x}, {fx:#x})")
    # ---- save / load
    rec = e.r32(F.PS.SESSION_OBJ + 0x14); b0 = rec + F.BLK
    e.uc.reg_write(A.UC_ARM_REG_SP, 0x2004FF00); e.uc.emu_start(lab["c_fqsave"] | 1, lab["sv_x"] + 4, count=20000)
    bb = bytes(e.uc.mem_read(b0, 32))
    want = bytes(((m & 0x7F) | (i & 1) << 7) for i, m in enumerate(mask(s) for s in range(16))) + \
        bytes((((m >> 8) & 0x3F) | (m >> 15) << 6 | ((m >> 14) & 1) << 7) for i, m in enumerate(mask(s) for s in range(16)))
    check(bb == want, f"save: the block in MIDI 1's pattern 8 ({bb.hex()})")
    saved = [mask(s) for s in range(16)]
    for s in range(16): e.uc.mem_write(F.FXS + F.O_M + 2 * s, b"\x55\x55")
    e.uc.reg_write(A.UC_ARM_REG_SP, 0x2004FF00); e.uc.emu_start(lab["c_fqload"] | 1, lab["lo_x"] + 4, count=20000)
    back = [mask(s) for s in range(16)]
    check(back == saved, f"load: the masks back ({[hex(m) for m in back if m]})")
    e.uc.mem_write(b0, b"\xFF" * 32)
    e.uc.reg_write(A.UC_ARM_REG_SP, 0x2004FF00); e.uc.emu_start(lab["c_fqload"] | 1, lab["lo_x"] + 4, count=20000)
    check(all(mask(s) == 0 for s in range(16)), "load of a garbage block (0xFF): empty")
    # ---- the engine row's pad 31
    p = R["fxstep"]["prev"]
    if "cmp_at" in p:                                                  # modesel's code there: a branch past it
        ca = int(p["cmp_at"], 16); w = struct.unpack("<H", bytes(e.uc.mem_read(ca, 2)))[0]
        check(w >> 11 == 0x1C, f"modesel: pad 31 skipped ({w:#06x} at {ca:#x})")
    else:                                                              # (vcf21.use_nofsq) the old sequencer's code out
        vl = R["vcf20"]["labels"]
        check("c_fsqbits" not in vl and "c_fsq" not in vl and "sp_nf" not in R["modesel"]["labels"], "the old FX sequencer's code is out (vcf21, modesel)")
    print(f"{man.get('marker', '?')} FXSTEP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
