"""SC33 ARM tests: the captured sample in Master FX (build_sc17.use_sampler), through the real routes (controller pads 0x08033282 / release 0x080332FE,
the Mixer view's knob and LED slots, Master FX's DSP service tick c_fxtick, the hooked sequencer tick) on the live RAM dump.

    python tools/emu_sc33.py SC33.bin SC33_manifest.json
  * pad 7: selects the sample, start command + gate; release drops the gate; Shift + pad 7 = forced loop on (command 2) / off (command 3);
  * the knobs with the sample selected: its 4 bytes (slot of pad 32), real values (pitch = raw ^ 64, end = 127 - raw), clamped, the 20 effect bytes untouched;
  * the tick: the state word on change, the parameters (INCI / INCF from the pitch table, SF / EF fractions, MODE 0..2) and the command, once;
  * pad 32: held = records while held; short press = latched, the next press stops; Shift = armed: the recording starts on a bar line (tick % 96 = 0) and ends on
    the next one; leaving the view ends only a held recording;
  * pad 8: stop command, no latch / arm, recording off; LEDs: pad 7 yellow dim / bright, pad 32 red dim / bright / blinking when armed, the sample's knobs;
  * pad 6 is still Vinyl, and the Vinyl T0 word (the record state) is not written when Vinyl starts.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc17_7 import E7  # noqa: E402
from emu_sc17_6 import ES, TICK, MGR  # noqa: E402
import build_sc17 as B  # noqa: E402
import sampler_dsp as SD  # noqa: E402
B.use_jump(hold=True, white=True); B.CLR_ON, B.CLR_DIM = 0x01, 0x03; B.JMP_ON, B.JMP_OFF = 0x2D, 0x2E
B.use_spcache(); B.CLR_COPY = True; B.use_sp_norm(); B.use_sp2(); B.KNOB_BRIGHT = True; B.CLEARPAD = True; B.CLEAR_SP = True; B.use_sampler()

KB = B.S_SLOT + 4 * B.SMP_SLOT


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    check(man["report"]["sc17"].get("sampler") is True, "manifest: sampler")
    def fresh():
        gc.collect(); x = E7(img, man); x.grid(); x.setsp(); x.uc.mem_write(x.blk + B.S_JF, b"\0\0"); x.w32(x.blk + B.S_SMT, 0)
        x.uc.mem_write(x.blk + KB, bytes(4)); return x
    jf = lambda x: x.blkb(B.S_JF)[0]
    smt = lambda x: x.r32(x.blk + B.S_SMT)
    def ftick(x, ms):
        x.w32(TICK, ms); x.dw.clear(); x.call(x.L["c_fxtick"], maxins=2_000_000); return list(x.dw)
    def knob(x, k, d): x.call(x.r32(B.MIX_VT + 16), B.MIXER if hasattr(B, "MIXER") else 0x200447D4, k, d & 0xFFFFFFFF, maxins=900000)
    MIXV = 0x200447D4
    def knob(x, k, d): x.call(x.r32(B.MIX_VT + 16), MIXV, k, d & 0xFFFFFFFF, maxins=900000)
    x = fresh()
    # ---- pad 7
    x.pad(B.SMP_PAD)
    check(x.blkb(B.S_SEL)[0] == B.SMP_SEL and jf(x) & 0x3F == (0x10 | B.SMB_GATE), f"pad 7: the sample selected, start + gate ({jf(x):#x})")
    x.rel(B.SMP_PAD)
    check(jf(x) & 0x3F == 0x10, f"released: the gate drops, the command stays pending ({jf(x):#x})")
    w = ftick(x, 1000)
    d = dict(w)
    check(d.get(SD.CMD) == 1 and SD.INCI in d and d[SD.INCI] == 1 and d[SD.INCF] == 0 and d[SD.SF] == 0 and d[SD.EF] == 0x7FFFFF and d[SD.MODE] == 0,
          f"tick: the parameters (zero bytes = pitch 0, start 0, end 127, one-shot) then CMD 1 {[(hex(a), hex(v)) for a, v in w if a >= SD.SMB]}")
    check([a for a, v in w if a >= SD.SMB][-1] == SD.CMD and jf(x) & 0x38 == 0, "the command is the last write; pending and dirty cleared")
    w = ftick(x, 1010)
    check([a for a, v in w if a >= SD.SMB] == [], "next tick: nothing to send")
    x.pad(B.SMP_PAD, shift=True); x.rel(B.SMP_PAD)
    check(jf(x) & (B.SMB_LOOP | 0x30) == B.SMB_LOOP | 0x20, f"Shift + pad 7: forced loop, command 2 ({jf(x):#x})")
    ftick(x, 1020)
    x.pad(B.SMP_PAD, shift=True); x.rel(B.SMP_PAD)
    check(jf(x) & (B.SMB_LOOP | 0x30) == 0x30, f"again: loop off, command 3 (stop) ({jf(x):#x})")
    ftick(x, 1030)
    # ---- knobs
    before = x.blkb(B.S_KNOB, 20)
    knob(x, 0, 12); knob(x, 3, -27); knob(x, 1, 50); knob(x, 2, 200)
    raw = x.blkb(KB, 4)
    check(raw[0] == (64 + 12) ^ 64 and raw[3] == 127 - 100 and raw[1] == 50 and raw[2] == 127 and x.blkb(B.S_KNOB, 20) == before,
          f"knobs: pitch 76, end 100, mode 50, start clamped 127; the effect bytes untouched {list(raw)}")
    knob(x, 0, -100)
    check(x.blkb(KB, 1)[0] == 0 ^ 64, "pitch clamped at 0")
    knob(x, 0, 76)
    w = dict(ftick(x, 1040))
    rate = B.tables()["SMPI"][76]
    check(w.get(SD.INCI) == rate >> 16 and w.get(SD.INCF) == (rate & 0xFFFF) << 8 and w.get(SD.MODE) == 1 and w.get(SD.SF) == 0x7FFFFF
          and w.get(SD.EF) == (100 * 0x7FFFFF) // 127 and SD.CMD not in w, f"dirty: parameters resent (pitch 76 = +4.5 st, gate mode), no command {[(hex(a), hex(v)) for a, v in w.items() if a >= SD.SMB]}")
    g = x.gleds()
    check([v & 0xFF for v in g[34:38]] == [B.SMP_ON] * 4 and [v >> 8 for v in g[34:38]] == [78, 52, 129, 102] and g[38:42] == [0] * 4,
          f"knob LEDs: the sample's colour, brightness = value + 2 {[hex(v) for v in g[34:42]]}")
    x.pad(4); x.rel(4)
    knob(x, 0, 5)
    check(x.blkb(B.S_SEL)[0] == 4 and x.blkb(KB, 1)[0] == 76 ^ 64 and x.blkb(B.S_KNOB, 20) != before, "another effect selected: the knobs are its own again")
    # ---- pad 32
    x = fresh()
    x.w32(TICK, 5000); x.pad(B.SMP_REC)
    check(jf(x) & B.SMB_REC and smt(x) == 5000, f"pad 32: recording, time stamp {smt(x)}")
    w = ftick(x, 5001)
    check((SD.STATE, 1) in w and jf(x) >> 6 == 1, "tick: STATE 1 sent")
    x.w32(TICK, 5800); x.rel(B.SMP_REC)
    check(not jf(x) & B.SMB_REC, "held 800 ms then released: the recording ends")
    check((SD.STATE, 0) in ftick(x, 5801), "tick: STATE 0")
    x.w32(TICK, 9000); x.pad(B.SMP_REC); x.w32(TICK, 9100); x.rel(B.SMP_REC)
    check(jf(x) & B.SMB_REC and smt(x) & B.SMT_LATCH, f"a 100 ms press: latched, still recording ({smt(x):#x})")
    ftick(x, 9200)
    x.gact_off = None
    x.w32(TICK, 12000); x.pad(B.SMP_REC); x.rel(B.SMP_REC)
    check(not jf(x) & B.SMB_REC and smt(x) == 0, "the next press stops it")
    # armed
    x.pad(B.SMP_REC, shift=True); x.rel(B.SMP_REC)
    check(smt(x) == B.SMT_ARM and not jf(x) & B.SMB_REC, f"Shift + pad 32: armed, not recording ({smt(x):#x})")
    x.w32(TICK, 0x100); a1 = x.gleds()[31]; x.w32(TICK, 0x000); a0 = x.gleds()[31]
    check({a0, a1} == {B.REC_ON, B.REC_DIM}, f"armed: pad 32 blinks ({a0:#x} / {a1:#x})")
    # the stock tick body needs the pattern data the RAM dump lacks at the pattern end (tick 96 = 16 steps; it fails on SC32 too): here the tick enters by the
    # real route (0x0802C418 -> c_sptick) and, where c_sptick goes back to the stock body (TICK_BACK, after its push.w {r4-r8, lr}), the test advances the
    # ticks store by one and returns to the caller
    from unicorn import UC_HOOK_CODE
    from unicorn.arm_const import UC_ARM_REG_SP, UC_ARM_REG_PC
    from emu_sc17_7 import ENGINE
    tst = x.r32(ENGINE + 0x90); tb = (x.r32(tst + 0xC), x.r32(tst + 0x10))
    def body(uc, a, s, d):                                                        # (no nested emulation inside a hook: the ticks words directly)
        t = max(x.r32(tb[0]), x.r32(tb[1])) + 1
        for bb in tb: x.w32(bb, t)
        sp = uc.reg_read(UC_ARM_REG_SP); lr = x.r32(sp + 20)
        uc.reg_write(UC_ARM_REG_SP, sp + 24); uc.reg_write(UC_ARM_REG_PC, lr | 1)
    x.uc.hook_add(UC_HOOK_CODE, body, begin=B.TICK_BACK, end=B.TICK_BACK)
    x.set_ticks(90); x.tick(4)
    check(not jf(x) & B.SMB_REC, "inside the bar: still waiting")
    x.tick(2)
    check(jf(x) & B.SMB_REC and smt(x) == B.SMT_ARM | B.SMT_LATCH, f"bar line (tick 96): recording ({smt(x):#x})")
    check(x.gleds()[31] == B.REC_ON, "pad 32 bright while recording")
    x.tick(95)
    check(jf(x) & B.SMB_REC, "the whole bar")
    x.tick(1)
    check(not jf(x) & B.SMB_REC and smt(x) == 0, f"next bar line: the recording ends, disarmed ({smt(x):#x})")
    x.pad(B.SMP_REC, shift=True); x.rel(B.SMP_REC); x.pad(B.SMP_REC, shift=True); x.rel(B.SMP_REC)
    check(smt(x) == 0, "Shift + pad 32 twice: disarmed")
    # leaving the view
    x.w32(TICK, 20000); x.pad(B.SMP_REC)
    x.btn(14)                                                                     # Mixer -> the stock Mixer view
    ftick(x, 20010)
    check(not jf(x) & B.SMB_REC, "a held recording ends when the view is left")
    x.btn(14)
    x.w32(TICK, 30000); x.pad(B.SMP_REC); x.w32(TICK, 30050); x.rel(B.SMP_REC); x.btn(14); ftick(x, 30100)
    check(jf(x) & B.SMB_REC, "a latched one goes on")
    x.btn(14)
    # ---- pad 8
    x.pad(B.SMP_PAD, shift=True); x.rel(B.SMP_PAD)
    x.pad(7); x.rel(7)
    check(jf(x) & (0x30 | B.SMB_LOOP | B.SMB_REC) == 0x30 and smt(x) == 0, f"pad 8: stop command, loop / recording / latch off ({jf(x):#x}, {smt(x):#x})")
    # ---- LEDs and pad 6
    x = fresh()
    g = x.gleds()
    check(g[B.SMP_PAD] == B.SMP_DIM and g[B.SMP_REC] == B.REC_DIM, f"idle: pad 7 dim yellow, pad 32 dim red ({g[6]:#x}, {g[31]:#x})")
    x.pad(B.SMP_PAD); g = x.gleds()
    check(g[B.SMP_PAD] == B.SMP_ON, "pad 7 held: bright")
    x.rel(B.SMP_PAD)
    t0 = x.r32(x.blk + B.S_T0 + 16)
    x.pad(5); w = dict(ftick(x, 77777)); x.rel(5)
    check(x.r32(x.blk + B.S_T0 + 16) == t0, "Vinyl started: its T0 word (the record state) is not written")
    import masterfx_dsp as G
    check(w.get(G.FX_ON, 0) & (1 << G.B_VN), f"pad 6 is still Vinyl (FX_ON {w.get(G.FX_ON, 0):#x})")
    print("SC33 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
