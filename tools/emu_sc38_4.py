"""SC38.4 ARM tests (live RAM dump, the real routes): the armed capture starts on the transport's own start (build_sc17.use_armplay2).

    python tools/emu_sc38_4.py SC38.4.bin SC38.4_manifest.json SC38.3.bin SC38.3_manifest.json
The harness is emu_sc17_6's (no stand-in for SET_TICKS: the stock's runs, as in the Play handler on the device):
  * stopped, Shift + pad 32 of Master FX: armed; Play (the controller, button 17): the stock starts the transport with SET_TICKS(engine, 0) from
    0x0802BD3C and the capture starts right there (latched, recording; the next Master FX tick sends STATE 1);
  * Play again (stop) and a new arm: nothing starts while stopped;
  * the previous build: Play leaves it armed (it waited for c_smtick to see the ticks store at 0, which the device's first tick beats).
SC38.2's emu_sc38_2 still covers the end on the bar line (tick 96) and the arm while playing.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc36 as T36  # noqa: E402,F401  (configures build_sc17 as SC36)
import build_sc17 as B  # noqa: E402
import sampler_dsp as SD  # noqa: E402
from emu_sc17_6 import ES, MGR, TICK  # noqa: E402


def run(img, man):
    x = ES(img, man); x.grid()
    x.uc.mem_write(x.blk + B.S_JF, b"\0\0"); x.w32(x.blk + B.S_SMT, 0)
    rec = lambda: bool(x.blkb(B.S_JF)[0] & B.SMB_REC)
    smt = lambda: x.r32(x.blk + B.S_SMT)
    play = lambda: (x.call(0x08033320, MGR, 17, maxins=5_000_000), x.call(0x0803381A, MGR, 17, maxins=5_000_000))
    def ftick(ms):
        x.w32(TICK, ms); x.dw.clear(); x.call(x.L["c_fxtick"], maxins=2_000_000); return list(x.dw)
    out = {}
    x.pad(B.SMP_REC, shift=True); x.rel(B.SMP_REC)
    out["armed"] = (smt(), rec())
    play(); out["play"] = (rec(), smt()); out["state"] = (SD.STATE, 1) in ftick(20000)
    play(); out["stop"] = (rec(), smt())                                          # stopping: the capture goes on (c_sptick ends it on its bar)
    x.uc.mem_write(x.blk + B.S_JF, b"\0\0"); x.w32(x.blk + B.S_SMT, 0)
    x.pad(B.SMP_REC, shift=True); x.rel(B.SMP_REC); ftick(20100)
    out["idle"] = (rec(), smt())
    del x; gc.collect()
    return out


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    o = run(img, man)
    check(o["armed"] == (B.SMT_ARM, False), f"stopped, Shift + pad 32: armed ({o['armed'][0]:#x})")
    check(o["play"][0] and o["play"][1] == B.SMT_ARM | B.SMT_LATCH and o["state"],
          f"Play: the stock's start (SET_TICKS(engine, 0) from 0x0802BD3C) starts the capture: recording, its bar running ({o['play'][1]:#x}), STATE 1 at the next tick")
    check(o["idle"] == (False, B.SMT_ARM), f"armed again while stopped: nothing starts ({o['idle'][1]:#x})")
    q = run(prev, prev_man)
    check(not q["play"][0] and q["play"][1] == B.SMT_ARM, f"SC38.3: Play leaves it armed ({q['play'][1]:#x})")
    print("SC38.4 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
