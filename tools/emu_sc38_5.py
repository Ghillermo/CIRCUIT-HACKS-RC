"""SC38.5 ARM tests (live RAM dump, the real routes of Master FX: pads 0x08033282 / release, the Master FX tick c_fxtick): Shift + pad 7 = a latched loop
(build_sc17.use_latch7).

    python tools/emu_sc38_5.py SC38.5.bin SC38.5_manifest.json SC38.4.bin SC38.4_manifest.json
  * Shift + pad 7: forced loop (command 2) with the gate; released: the gate stays (the DSP's HOLD only stops a loop when the gate drops); the tick sends
    STATE with the gate and CMD 2; leaving Master FX (another view): still latched; back, pad 7 (no Shift): stopped (gate and loop off, CMD 3), and its
    release changes nothing;
  * pad 7 alone: start with the gate, released: the gate drops (the modes as before);
  * Shift + pad 7 then pad 8: stopped, gate off;
  * a slot of the sample (pad 7 held + pad 27): Shift + the slot = latched; the slot again = stopped;
  * latched: an effect slot (pad 1 held + pad 28) pressed plays its effect, it is not reassigned to the sample (the gate stays on while latched);
  * the previous build: Shift + pad 7 released drops the gate and the loop (the held loop of SC34.1).
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc36 as T36  # noqa: E402  (configures build_sc17 as SC36)
import build_sc17 as B  # noqa: E402
import sampler_dsp as SD  # noqa: E402
from emu_sc17_6 import TICK  # noqa: E402


def run(img, man):
    x = T36.T34.E7(img, man); x.grid(); x.setsp()
    x.uc.mem_write(x.blk + B.S_JF, b"\0\0"); x.w32(x.blk + B.S_SMT, 0)
    jf = lambda: x.blkb(B.S_JF)[0]
    ms = [30000]
    def ftick():
        ms[0] += 10; x.w32(TICK, ms[0]); x.dw.clear(); x.call(x.L["c_fxtick"], maxins=2_000_000); return dict(x.dw)
    bits = lambda v: (bool(v & B.SMB_LOOP), bool(v & B.SMB_GATE), (v >> 4) & 3)
    out = {}
    x.pad(B.SMP_PAD, shift=True); out["sp"] = bits(jf()); x.rel(B.SMP_PAD); out["sp_rel"] = bits(jf())
    w = ftick(); out["tick"] = (w.get(SD.STATE), w.get(SD.CMD)); out["after_tick"] = bits(jf())
    x.btn(15); ftick(); out["away"] = bits(jf())                                  # the FX view: Master FX left
    x.grid(); x.pad(B.SMP_PAD); out["stop"] = bits(jf()); x.rel(B.SMP_PAD); out["stop_rel"] = bits(jf())
    w = ftick(); out["stop_tick"] = (w.get(SD.STATE), w.get(SD.CMD))
    x.pad(B.SMP_PAD); out["plain"] = bits(jf()); x.rel(B.SMP_PAD); out["plain_rel"] = bits(jf()); ftick()
    x.pad(B.SMP_PAD, shift=True); x.rel(B.SMP_PAD); ftick(); x.pad(7); x.rel(7); out["pad8"] = bits(jf()); ftick()
    # a slot of the sample: pad 7 held + pad 27
    x.pad(B.SMP_PAD); x.pad(26); x.rel(26); x.rel(B.SMP_PAD); ftick()
    x.uc.mem_write(x.blk + B.S_JF, b"\0"); ftick()
    x.pad(26, shift=True); x.rel(26); out["slot"] = bits(jf()); ftick()
    x.pad(26); x.rel(26); out["slot_stop"] = bits(jf()); ftick()
    # an effect slot while the loop is latched: it plays its effect, it is not taken for "pad 7 held + slot" (= assign the sample)
    stype = lambda j: (lambda b_: None if not b_[3] >> 7 else (b_[0] >> 7 | (b_[1] >> 7) << 1 | (b_[2] >> 7) << 2))(x.blkb(B.S_SLOT + 4 * j, 4))
    x.pad(0); x.pad(27); x.rel(27); x.rel(0); ftick(); t0 = stype(2)
    x.pad(B.SMP_PAD, shift=True); x.rel(B.SMP_PAD); ftick()
    x.pad(27); out["fx_slot"] = (t0, stype(2), bits(jf())); x.rel(27)
    del x; gc.collect()
    return out


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    o = run(img, man)
    check(o["sp"] == (True, True, 2) and o["sp_rel"] == (True, True, 2), f"Shift + pad 7: forced loop with the gate, CMD 2 {o['sp']}; released: still latched {o['sp_rel']}")
    check(o["tick"][1] == 2 and o["tick"][0] is not None and o["tick"][0] & 2 and o["after_tick"][:2] == (True, True),
          f"the tick: STATE {o['tick'][0]} (gate on), CMD {o['tick'][1]}; still latched {o['after_tick']}")
    check(o["away"][:2] == (True, True), f"Master FX left (the FX view): the loop goes on {o['away']}")
    check(o["stop"] == (False, False, 3) and o["stop_rel"] == (False, False, 3) and o["stop_tick"][1] == 3,
          f"pad 7 again: stopped {o['stop']} (CMD {o['stop_tick'][1]}); its release changes nothing {o['stop_rel']}")
    check(o["plain"] == (False, True, 1) and o["plain_rel"][:2] == (False, False), f"pad 7 alone: start with the gate {o['plain']}, released: the gate drops {o['plain_rel']}")
    check(o["pad8"][:2] == (False, False) and o["pad8"][2] == 3, f"Shift + pad 7, then pad 8: stopped, gate off {o['pad8']}")
    check(o["slot"][:2] == (True, True) and o["slot_stop"][:2] == (False, False) and o["slot_stop"][2] == 3,
          f"a slot of the sample: Shift + the slot latched {o['slot']}, the slot again stopped {o['slot_stop']}")
    t0, t1, lb = o["fx_slot"]
    check(t0 is not None and t1 == t0 and lb[:2] == (True, True), f"latched: an effect slot pressed keeps its effect ({t0} -> {t1}), the loop goes on {lb}")
    q = run(prev, prev_man)
    check(q["sp_rel"][:2] == (False, False), f"SC38.4: Shift + pad 7 released drops the gate and the loop {q['sp_rel']} (what the user saw)")
    print("SC38.5 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
