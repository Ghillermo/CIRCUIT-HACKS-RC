"""SC34 ARM tests (build_sc17.use_sampler2, tools/drumrep.py), through the real routes (controller buttons 0x08033320, pads 0x08033282 / release 0x080332FE,
the view slots, Master FX's DSP service tick c_fxtick) on the live RAM dump.

    python tools/emu_sc34.py SC34.bin SC34_manifest.json
  * Master FX: pad 7 held + bottom pad 27 assigns the sample to slot 1 with a copy of its knobs; pad 31 is still a slot (assign the Gater); pad 32 is the record pad;
  * a slot of the sample: its knobs are loaded, the sample starts (command 1, gate), lit while held; released: the gate drops; Shift: command 2 (loop);
  * the FX view: the sample's slot in yellow, pad 32 red; pad 32 records there (held / tap); a held recording goes on in the FX view;
  * K2 of the sample: yellow / green / blue by mode;
  * drum Preset view (Drum 1 + Preset): Shift + pad 4 = asked (blinking, bits 1-7 of +0x51), Shift + pad 4 again = confirmed (S_SMT bits 23-29 = 4), the tick sends
    REPN 3 and CMD 4; a pad without Shift cancels a question and selects as stock; a question on page 2 is sample 35; the chromatic keyboard is left alone.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc17_7 import E7  # noqa: E402
from emu_sc17_6 import TICK, MGR  # noqa: E402
import build_sc17 as B  # noqa: E402
import sampler_dsp as SD  # noqa: E402
import drumrep as DR  # noqa: E402
B.use_jump(hold=True, white=True); B.CLR_ON, B.CLR_DIM = 0x01, 0x03; B.JMP_ON, B.JMP_OFF = 0x2D, 0x2E
B.use_spcache(); B.CLR_COPY = True; B.use_sp_norm(); B.use_sp2(); B.KNOB_BRIGHT = True; B.CLEARPAD = True; B.CLEAR_SP = True; B.use_sampler(); B.use_sampler2()

KB = B.S_SLOT + 4 * B.SMP_SLOT
DVIEWS = [0x20042D14, 0x20042DF4, 0x20042ED4, 0x20042FB4]
FXV = 0x200443B4


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    check(man["report"]["sc17"].get("sampler2") is True and "drumrep" in man["report"], "manifest: sampler2, drumrep")
    def fresh():
        gc.collect(); x = E7(img, man); x.grid(); x.setsp(); x.uc.mem_write(x.blk + B.S_JF, b"\0\0"); x.w32(x.blk + B.S_SMT, 0)
        x.uc.mem_write(x.blk + B.S_SLOT, bytes(28)); return x
    jf = lambda x: x.blkb(B.S_JF)[0]
    smt = lambda x: x.r32(x.blk + B.S_SMT)
    stype = lambda x, j: (lambda b: None if not b[3] >> 7 else (b[0] >> 7 | (b[1] >> 7) << 1 | (b[2] >> 7) << 2))(x.blkb(B.S_SLOT + 4 * j, 4))
    def ftick(x, ms):
        x.w32(TICK, ms); x.dw.clear(); x.call(x.L["c_fxtick"], maxins=2_000_000); return list(x.dw)
    view = lambda x: x.r32(MGR + B.CTRL_VIEW)
    # ---- Master FX: assign the sample to slot 1 (pad 27)
    x = fresh()
    x.uc.mem_write(x.blk + KB, bytes([10, 90, 20, 30]))
    x.pad(B.SMP_PAD); x.pad(26); x.rel(26); x.rel(B.SMP_PAD)
    check(stype(x, 1) == B.SMP_SEL and [v & 0x7F for v in x.blkb(B.S_SLOT + 4, 4)] == [10, 90, 20, 30], f"pad 7 held + pad 27: slot 1 = the sample with its knobs {list(x.blkb(B.S_SLOT + 4, 4))}")
    x.pad(0); x.pad(30); x.rel(30); x.rel(0)
    check(stype(x, 5) == 0, "pad 31 is still a slot: pad 1 held + pad 31 = the Gater")
    x.pad(31); x.rel(31)
    check(stype(x, 6) is None, "pad 32 is not a slot")
    ftick(x, 1000)
    # ---- play the sample's slot
    x.uc.mem_write(x.blk + KB, bytes([1, 2, 3, 4])); x.uc.mem_write(x.blk + B.S_JF, b"\0")
    x.pad(26)
    check(x.blkb(B.S_SEL)[0] == B.SMP_SEL and list(x.blkb(KB, 4)) == [10, 90, 20, 30] and jf(x) & 0x3F == 0x10 | B.SMB_GATE and x.blkb(B.S_SLOTH)[0] & 2,
          f"slot pad 27: the sample selected, its knobs loaded {list(x.blkb(KB, 4))}, start + gate, held ({jf(x):#x})")
    g = x.gleds()
    check(g[26] == B.SMP_ON, f"pad 27 bright yellow while held ({g[26]:#x})")
    x.rel(26)
    check(not jf(x) & B.SMB_GATE and not x.blkb(B.S_SLOTH)[0] & 2, "released: gate and hold dropped")
    w = dict(ftick(x, 1100))
    check(w.get(SD.CMD) == 1 and w.get(SD.MODE) == (90 * 3) >> 7, f"tick: the slot's parameters (mode {(90 * 3) >> 7}) and CMD 1")
    check(x.gleds()[26] == B.SMP_DIM, "released: dim yellow")
    if B.SMP_HOLD:                                                              # SC34.1: the loop plays only while held
        x.pad(26, shift=True)
        check(jf(x) & (B.SMB_LOOP | B.SMB_GATE | 0x30) == B.SMB_LOOP | B.SMB_GATE | 0x20 and x.blkb(B.S_SLOTH)[0] & 2 and x.gleds()[26] == B.SMP_ON,
              f"Shift + the slot (loophold): loop (command 2) with the gate held, slot held, lit ({jf(x):#x})")
        x.rel(26)
        check(jf(x) & (B.SMB_LOOP | B.SMB_GATE | 0x30) == 0x20 and not x.blkb(B.S_SLOTH)[0] & 2, f"released: gate and loop dropped ({jf(x):#x})")
        ftick(x, 1200)
        x.pad(26, shift=True); ftick(x, 1250); x.pad(26, shift=True)
        check(jf(x) & (B.SMB_LOOP | B.SMB_GATE | 0x30) == B.SMB_LOOP | B.SMB_GATE | 0x20, f"Shift + the slot again: a new loop, no toggle-off ({jf(x):#x})")
        x.rel(26); ftick(x, 1300)
        x.pad(B.SMP_PAD, shift=True)
        check(jf(x) & (B.SMB_LOOP | B.SMB_GATE | 0x30) == B.SMB_LOOP | B.SMB_GATE | 0x20, f"Shift + pad 7 (loophold): loop with the gate held ({jf(x):#x})")
        x.rel(B.SMP_PAD)
        check(not jf(x) & (B.SMB_LOOP | B.SMB_GATE), f"pad 7 released: gate and loop dropped ({jf(x):#x})")
        ftick(x, 1350)
    else:
        x.pad(26, shift=True); x.rel(26)
        check(jf(x) & (B.SMB_LOOP | 0x30) == B.SMB_LOOP | 0x20, f"Shift + the slot: loop (command 2) ({jf(x):#x})")
        ftick(x, 1200)
    # ---- K2 colour by mode
    for raw_m, col in ((0, B.MODE_COL[0]), (60, B.MODE_COL[1]), (127, B.MODE_COL[2])):
        x.uc.mem_write(x.blk + KB + 1, bytes([raw_m])); x.uc.mem_write(x.blk + B.S_SEL, bytes([B.SMP_SEL]))
        g = x.gleds()[35]
        check(g & 0xFF == col and g >> 8 == 129, f"K2 = {raw_m}: colour {g & 0xFF:#x} (want {col:#x}), full brightness")
    # ---- the FX view
    x.btn(15)
    check(view(x) == FXV, "the FX view is showing")
    g = x.fxleds()
    check(g[26] == B.SMP_DIM and g[31] == B.REC_DIM, f"FX view: the sample's slot dim yellow, pad 32 dim red ({g[26]:#x}, {g[31]:#x})")
    x.uc.mem_write(x.blk + B.S_JF, b"\0"); x.w32(x.blk + B.S_SMT, 0)
    x.w32(TICK, 5000); x.pad(31)
    check(jf(x) & B.SMB_REC, "FX view pad 32: recording")
    w = ftick(x, 5900)
    check(jf(x) & B.SMB_REC and (SD.STATE, 1) in w, "a held recording goes on in the FX view (STATE 1 sent)")
    check(x.fxleds()[31] == B.REC_ON, "pad 32 bright red")
    x.w32(TICK, 6000); x.rel(31)
    check(not jf(x) & B.SMB_REC, "released after 1 s: stops")
    x.w32(TICK, 7000); x.pad(31); x.w32(TICK, 7050); x.rel(31)
    check(jf(x) & B.SMB_REC and smt(x) & B.SMT_LATCH, "a tap: latched")
    x.pad(31); x.rel(31)
    check(not jf(x) & B.SMB_REC, "the next press stops it")
    x.pad(26); x.rel(26)
    check(jf(x) & 0x30 == 0x10, "the sample's slot plays from the FX view too")
    # ---- drum replacement
    gc.collect(); y = E7(img, man)
    y.uc.mem_write(y.blk + B.S_JF, b"\0"); y.w32(y.blk + B.S_SMT, 0)
    from emu_sc08 import CONT
    from unicorn.arm_const import UC_ARM_REG_R0 as R0
    y.set_p0(y.r32(CONT + 0x188), 4); y.btn(4); y.btn(8)                         # Drum 1 selected, its Preset view
    dv = DVIEWS[0]                                                                # (the controller's view is the track container; the pads go to its Preset subview)
    check(y.r32(dv) == DR.DP_VT, f"Drum 1's Preset view ({dv:#x})")
    y.uc.mem_write(dv + 0x51, b"\0")
    y.pad(3, shift=True); y.rel(3)
    check(y.r8(dv + 0x51) == (3 + 1) << 1 and smt(y) == 0, f"Shift + pad 4: asked ({y.r8(dv + 0x51):#x})")
    def dleds(): y.call(y.r32(DR.DP_VT + 0x1C), dv, maxins=900000); p = y.uc.reg_read(R0); return list(struct.unpack("<32H", bytes(y.uc.mem_read(p, 64))))
    y.w32(TICK, 0x100); a1 = dleds()[3]; y.w32(TICK, 0x000); a0 = dleds()[3]
    check({a0, a1} == {DR.BLINK_ON, DR.BLINK_OFF}, f"pad 4 blinks ({a0:#x} / {a1:#x})")
    y.pad(3, shift=True); y.rel(3)
    check(y.r8(dv + 0x51) == 0 and smt(y) >> 23 == 4, f"Shift + pad 4 again: confirmed, request 4 ({smt(y):#x})")
    w = ftick(y, 2000)
    w = [x for x in w if not (B.SMP_SAVEBIT and x[0] == SD.SMB + 0x1E)]                # (SC35: then the saved bit of the slot)
    check(w[-2:] == [(SD.REPN, 3), (SD.CMD, 4)] and smt(y) >> 23 == 0, f"the tick sends REPN 3, CMD 4 {[(hex(a), v) for a, v in w if a >= SD.SMB]}")
    y.pad(5, shift=True); y.rel(5); y.pad(6, shift=True); y.rel(6)
    check(y.r8(dv + 0x51) == (6 + 1) << 1, "Shift + another pad: the question moves")
    from unicorn import UC_HOOK_CODE
    from unicorn.arm_const import UC_ARM_REG_R1 as R1
    prev = int(man["report"]["drumrep"]["prev_pad"], 16); seen = []
    hk = y.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s_, d: seen.append((uc.reg_read(R0), uc.reg_read(R1))), begin=prev, end=prev)
    y.pad(9); y.rel(9)
    y.uc.hook_del(hk)
    check(y.r8(dv + 0x51) == 0 and smt(y) >> 23 == 0, "a pad without Shift: no question, nothing requested")
    check((dv, 9) in seen, f"and the pad goes on to the previous handler (the stock selection) {[(hex(v), p_) for v, p_ in seen]}")
    pg = y.r32(dv + 0x20)
    for bb in (y.r32(pg + 0xC), y.r32(pg + 0x10)): y.uc.mem_write(bb, bytes([1]))   # page 2 (both buffers of the store)
    y.pad(3, shift=True); y.rel(3)
    check(y.r8(dv + 0x51) == (35 + 1) << 1, f"page 2: pad 4 = sample 35 ({(y.r8(dv + 0x51) >> 1) - 1})")
    y.uc.mem_write(dv + 0x51, b"\x01")
    y.pad(3, shift=True); y.rel(3)
    check(y.r8(dv + 0x51) == 1, "chromatic keyboard: nothing asked")
    print("SC34 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
