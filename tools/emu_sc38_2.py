"""SC38.2 ARM tests (live RAM dump, the real routes: pad 32 of Master FX with Shift, the Master FX tick c_fxtick, the sequencer tick 0x0802C418 -> c_sptick):
a capture armed while stopped starts at Play and ends at the end of that bar (build_sc17.use_armplay).

    python tools/emu_sc38_2.py SC38.2.bin SC38.2_manifest.json SC38.1.bin SC38.1_manifest.json
  * armed, stopped (ticks 0): nothing; Play (the transport running, ticks still 0: the downbeat the stock plays outside the tick function): the Master FX
    tick starts the recording (latched, STATE 1 to the DSP); the bar's ticks 1..95: still recording; tick 96: ends, disarmed;
  * the previous build: at Play nothing, the recording starts at tick 96 (a bar late) - what the user saw;
  * armed while playing (ticks 500): nothing at once, the next bar line (576) starts it, as before.
The stock tick body needs pattern data the RAM dump lacks: as in emu_sc33.py the tick enters by the real route and the test advances the ticks store.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_SP, UC_ARM_REG_PC, UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc36 as T36  # noqa: E402  (configures build_sc17 as SC36)
import build_sc17 as B  # noqa: E402
import sampler_dsp as SD  # noqa: E402
from emu_sc17_6 import TICK  # noqa: E402
from emu_sc17_7 import ENGINE, engine_of  # noqa: E402


def run(img, man):
    x = T36.T34.E7(img, man); x.grid(); x.setsp()
    x.uc.mem_write(x.blk + B.S_JF, b"\0\0"); x.w32(x.blk + B.S_SMT, 0)
    out = {}
    rec = lambda: bool(x.blkb(B.S_JF)[0] & B.SMB_REC)
    smt = lambda: x.r32(x.blk + B.S_SMT)
    ms = [10000]
    def ftick():
        ms[0] += 1; x.w32(TICK, ms[0]); x.dw.clear(); x.call(x.L["c_fxtick"], maxins=2_000_000); return list(x.dw)
    def play(on):
        x.call(B.PARAM_GET, B.PLAY_STORE, 0); x.uc.mem_write(x.uc.reg_read(UC_ARM_REG_R0), bytes([1 if on else 0]))
    ENG_ = engine_of(img, man)                                                    # (the engine this build uses)
    tst = x.r32(ENG_ + 0x90); tb = (x.r32(tst + 0xC), x.r32(tst + 0x10))
    x.set_ticks = lambda t: [x.w32(bb, t & 0xFFFFFFFF) for bb in tb]                # (the ticks store of that engine)
    def body(uc, a, s, d):                                                        # the stock tick body: the ticks store + 1, back to the caller
        t = max(x.r32(tb[0]), x.r32(tb[1])) + 1
        for bb in tb: x.w32(bb, t)
        sp = uc.reg_read(UC_ARM_REG_SP); lr = x.r32(sp + 20)
        uc.reg_write(UC_ARM_REG_SP, sp + 24); uc.reg_write(UC_ARM_REG_PC, lr | 1)
    x.uc.hook_add(UC_HOOK_CODE, body, begin=B.TICK_BACK, end=B.TICK_BACK)
    def ticks(n):                                                                 # n sequencer ticks, a Master FX tick after each one
        for _ in range(n): x.call(B.TICK_FN, ENG_, maxins=5_000_000); ftick()
    # armed while stopped
    play(False); x.set_ticks(0)
    x.pad(B.SMP_REC, shift=True); x.rel(B.SMP_REC); ftick()
    out["armed"] = (smt(), rec())
    play(True); w = ftick()
    out["play"] = (rec(), smt(), (SD.STATE, 1) in w)
    ticks(95); out["bar"] = rec()
    ticks(1); out["end"] = (rec(), smt())
    if not out["play"][0]:                                                        # the previous build: when does it start
        out["late"] = rec()
    ticks(1); out["after"] = rec()
    # armed while playing
    x.set_ticks(500); x.pad(B.SMP_REC, shift=True); x.rel(B.SMP_REC); ftick()
    out["mid"] = (rec(), smt())
    x.set_ticks(570); ticks(5); out["mid_wait"] = rec()
    ticks(1); out["mid_bar"] = rec()
    del x; gc.collect()
    return out


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    o = run(img, man)
    check(o["armed"] == (B.SMT_ARM, False), f"Shift + pad 32 while stopped: armed, not recording ({o['armed'][0]:#x})")
    check(o["play"][0] and o["play"][1] == B.SMT_ARM | B.SMT_LATCH and o["play"][2],
          f"Play (ticks still 0): recording at once, its bar running ({o['play'][1]:#x}), STATE 1 to the DSP ({o['play'][2]})")
    check(o["bar"], "ticks 1..95: still recording")
    check(o["end"] == (False, 0), f"tick 96 (the end of the bar): the recording ends, disarmed ({o['end'][1]:#x})")
    check(not o["after"], "and it does not start again")
    check(o["mid"] == (False, B.SMT_ARM) and not o["mid_wait"] and o["mid_bar"],
          f"armed while playing (ticks 500): waits {o['mid']}, starts on the bar line 576 ({o['mid_bar']})")
    q = run(prev, prev_man)
    check(not q["play"][0] and q["end"][0], f"SC38.1: nothing at Play, the recording starts at tick 96, a bar late ({q['end'][0]})")
    print("SC38.2 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
