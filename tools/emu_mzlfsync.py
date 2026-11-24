"""Alpha 7.41 test (morphz.use_lfsync): the morph LFO rate K3 bipolar, through c_mzlfo itself.
    python tools/emu_mzlfsync.py firmware/a7.41
  * right (v >= 0): free, the old curve at rate v x 7 / 4 (v = 63: rate 110, ~75 % of the old top speed);
  * left (v < 0), playing: the phase = (the global tick mod d) x 65536 / d, d = (4 or 6) << (i >> 1), i = (-v - 1) >> 2;
  * left, stopped: the phase advances 26214 x BPM x dt / (1000 d) a call."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R5
import emu_sc48_8 as S
import morphz as M
PARAM_GET = 0x0803542C


def main(a):
    d = Path(a[0]); img = next(d.glob("*.bin")).read_bytes(); man = json.loads((d / "manifest.json").read_text())
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = S.ET(img, man)
    LFO = int(man["report"]["morphz"]["labels"]["c_mzlfo"], 16)
    PH = 0x2006E000                                                            # a scratch phase
    def p0(store):
        e.call(PARAM_GET, store, 0); return e.uc.reg_read(UC_ARM_REG_R0)
    def lfo(v, dt=10, ph=0):
        e.uc.mem_write(PH, (ph & 0xFFFF).to_bytes(2, "little")); e.uc.reg_write(UC_ARM_REG_R5, dt)
        e.call(LFO, PH, v & 0xFF); return e.uc.reg_read(UC_ARM_REG_R0), e.uc.reg_read(UC_ARM_REG_R1)
    old = lambda r, dt: (((r + 1) ** 2 + 16) * dt) >> 4
    for v in (0, 20, 63):
        ph, w = lfo(v, 10, 1000)
        check(ph == (1000 + old(v * 7 // 4, 10)) & 0xFFFF, f"free v {v}: the phase {ph} (rate {v * 7 // 4})")
    check(old(110, 1) * 100 // old(127, 1) in range(70, 80), f"the top: {old(110, 1)} / {old(127, 1)} of the old top speed")
    tr = p0(M.TRANSPORT); tick_at = p0(e.r32(M.ENG + 0x90))
    bpm = e.r8(p0(M.TEMPO))
    for playing in (1, 0):
        e.uc.mem_write(tr, bytes([playing]))
        for v, i in ((-1, 0), (-5, 1), (-9, 2), (-64, 15)):
            dv = (6 if i & 1 else 4) << (i >> 1)
            if playing:
                for tick in (0, 3, 7, 1000):
                    e.w32(tick_at, tick)
                    ph, w = lfo(v, 10, 0x1234)
                    check(ph == ((tick % dv) << 16) // dv, f"synced v {v} (d {dv}), playing, tick {tick}: the phase {ph}")
            else:
                ph, w = lfo(v, 50, 100)
                check(ph == (100 + 26214 * bpm * 50 // (1000 * dv)) & 0xFFFF, f"synced v {v} (d {dv}), stopped ({bpm} BPM): the phase {ph}")
    print("MZLFSYNC RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
