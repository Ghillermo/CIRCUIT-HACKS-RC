"""RC4.12 / Beta 5.61 tests (capkeep.py): a latched / armed capture of Master FX's sample goes on through a project load.

    python tools/emu_capkeep.py NEW.bin NEW_manifest.json PREV.bin PREV_manifest.json

The capture through the real route (Master FX, pad 32 short = latched, Shift + pad 32 = armed; the Master FX tick sends the DSP's STATE); the load's
reset = what c_rs calls (checked in the image: c_ckeep in the new build, c_clrall / c_lcclr in the previous one), with r0 = the Master FX block.
  * latched: after the reset the recording bit, the latch and its press time are kept, the next tick sends no STATE 0 (the previous build: off, STATE 0);
  * armed: still armed (the previous build: disarmed);
  * held (pad 32 still down, not latched): ends at the reset, as before;
  * pad 8 (everything off) still stops a latched capture;
  * (RC4.14 / Beta 5.63, capkeep.use_resend) a restart that keeps the RAM: a latched capture, the DSP reloaded (its STATE back to 0: nothing
    recorded), the boot's load through c_ckeep: the next ticks send STATE 1 once (before: never, pad 32 showed a capture that recorded nothing).
    A normal load sends STATE 1 again too (the DSP already at 1: no edge).
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc34 as T34  # noqa: E402  (configures build_sc17 as SC34)
import build_sc17 as B  # noqa: E402
import sampler_dsp as SD  # noqa: E402
from emu_sc17_6 import TICK  # noqa: E402
from thumb import bl as bl_enc  # noqa: E402


def reset_fn(x, man):
    """the function c_rs calls for the load's reset (the one call of c_ckeep / c_lcclr / c_clrall between c_rs and rs_x)"""
    rep = man["report"]
    lab = lambda m, k: int(rep[m]["labels"][k], 16)
    cands = [lab("sc17", "c_clrall")] + ([lab("loopcarry", "c_lcclr")] if "loopcarry" in rep else []) + ([lab("capkeep", "c_ckeep")] if "capkeep" in rep else [])
    rs, rx = lab("persist19", "c_rs"), lab("persist19", "rs_x")
    hits = [t for a in range(rs, rx, 2) for t in cands if bytes(x.uc.mem_read(a, 4)) == bl_enc(a, t)]
    assert len(hits) == 1, hits
    return hits[0]


def run(img, man):
    out = {}
    def fresh():
        gc.collect(); x = T34.E7(img, man); x.grid(); x.setsp(); x.uc.mem_write(x.blk + B.S_JF, b"\0\0"); x.w32(x.blk + B.S_SMT, 0); return x
    def ftick(x, ms):
        x.w32(TICK, ms); x.dw.clear(); x.call(x.L["c_fxtick"], maxins=2_000_000); return dict(x.dw)
    jf = lambda x: x.blkb(B.S_JF)[0]
    smt = lambda x: x.r32(x.blk + B.S_SMT)
    x = fresh(); fn = reset_fn(x, man); out["fn"] = "capkeep" if "capkeep" in man["report"] and fn == int(man["report"]["capkeep"]["labels"]["c_ckeep"], 16) else hex(fn)
    # latched
    x.w32(TICK, 1000); x.pad(B.SMP_REC); x.w32(TICK, 1050); x.rel(B.SMP_REC)
    w0 = ftick(x, 1060); s0 = smt(x)
    out["latched_before"] = (jf(x) & B.SMB_REC, s0 >> 30, w0.get(SD.STATE))
    x.call(fn, x.blk, maxins=3_000_000)
    w1 = ftick(x, 1070)
    out["latched_after"] = (jf(x) & B.SMB_REC, smt(x) >> 30, smt(x) == s0, w1.get(SD.STATE), w1.get(SD.CMD))
    # armed
    x = fresh(); fn = reset_fn(x, man)
    x.w32(TICK, 2000); x.pad(B.SMP_REC, shift=True); x.rel(B.SMP_REC); ftick(x, 2010); s0 = smt(x)
    out["armed_before"] = s0 >> 30
    x.call(fn, x.blk, maxins=3_000_000); ftick(x, 2020)
    out["armed_after"] = (smt(x) >> 30, smt(x) == s0)
    # held, not latched
    x = fresh(); fn = reset_fn(x, man)
    x.w32(TICK, 3000); x.pad(B.SMP_REC); ftick(x, 3010)
    out["held_before"] = (jf(x) & B.SMB_REC, smt(x) >> 30)
    x.call(fn, x.blk, maxins=3_000_000); w = ftick(x, 3020)
    out["held_after"] = (jf(x) & B.SMB_REC, w.get(SD.STATE))
    x.rel(B.SMP_REC)
    # pad 8 still stops a latched capture
    x = fresh()
    x.w32(TICK, 4000); x.pad(B.SMP_REC); x.w32(TICK, 4050); x.rel(B.SMP_REC); ftick(x, 4060)
    x.pad(7); x.rel(7); w = ftick(x, 4070)
    out["pad8"] = (jf(x) & B.SMB_REC, smt(x) >> 30, w.get(SD.STATE))
    # a restart keeping the RAM: latched, the DSP reloaded (nothing the ARM sees), the boot's load, then the ticks
    x = fresh(); fn = reset_fn(x, man)
    x.w32(TICK, 5000); x.pad(B.SMP_REC); x.w32(TICK, 5050); x.rel(B.SMP_REC); ftick(x, 5060)
    ftick(x, 5070)                                                                      # a boot tick before the load: nothing new to send
    x.call(fn, x.blk, maxins=3_000_000)
    out["restart"] = [ftick(x, 5080 + 10 * i).get(SD.STATE) for i in range(5)]
    del x; gc.collect()
    return out


def main(img, man, prev, pman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    n, o = run(img, man), run(prev, pman)
    print("      new ", n); print("      prev", o)
    check(n["fn"] == "capkeep", f"c_rs calls c_ckeep ({n['fn']})")
    check(n["latched_before"] == (1, 1, 1) and o["latched_before"] == (1, 1, 1), f"pad 32 short: latched, STATE 1 sent ({n['latched_before']})")
    check(n["latched_after"][:3] == (1, 1, True) and n["latched_after"][3] in (None, 1), f"latched through the reset: recording, latch and press time kept, no STATE 0 ({n['latched_after']})")
    check(o["latched_after"][0] == 0 and o["latched_after"][3] == 0, f"the previous build: the capture stopped (STATE 0) ({o['latched_after']})")
    check(n["armed_before"] == 2 and n["armed_after"] == (2, True), f"armed through the reset: still armed ({n['armed_after']})")
    check(o["armed_after"][0] == 0, f"the previous build: disarmed ({o['armed_after']})")
    check(n["held_before"] == (1, 0) and n["held_after"] == o["held_after"] and n["held_after"][0] == 0, f"held (not latched): ends at the reset as before ({n['held_after']})")
    check(n["pad8"] == o["pad8"] and n["pad8"][0] == 0 and n["pad8"][1] == 0, f"pad 8: stops a latched capture as before ({n['pad8']})")
    check(n["restart"].count(1) == 1 and 0 not in n["restart"] and n["restart"][0] == 1,
          f"a restart keeping the RAM: the boot's load resends STATE 1 once ({n['restart']})")
    print(f"{man.get('marker', '?')} CAPKEEP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a_ = [Path(p) for p in sys.argv[1:5]]
    sys.exit(1 if main(a_[0].read_bytes(), json.loads(a_[1].read_text()), a_[2].read_bytes(), json.loads(a_[3].read_text())) else 0)
