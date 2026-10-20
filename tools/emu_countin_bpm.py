"""SC44.8 / RC2.03 test (countin.use_bpm0): the count-in follows the project's tempo (p0 of 0x20011404), not p1.

    python tools/emu_countin_bpm.py NEW.bin NEW_manifest.json [PREV.bin PREV_manifest.json]
  * p0 = 100 BPM, p1 = 120: the four clicks 600 ms apart (one at once, at 600, 1200, 1800), the transport starts after 2400 ms;
  * the previous build (if given): the clicks 500 ms apart (it read p1).
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_countin import EC, TICK  # noqa: E402
import countin as CI  # noqa: E402


def clicks(img, man):
    e = EC(img, man)
    for i, v in ((0, 100), (1, 120)):
        for fn in (CI.PARAM_WPTR, 0x0803542C):
            e.call(fn, CI.TEMPO, i, maxins=200000); e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0), bytes([v]))
    e.w32(TICK, 100000); e.set_state(2); e.btn(16)
    e.clicks.clear(); e.w32(TICK, 200000); e.btn(CI.ID_PLAY)
    out = []
    for t in range(0, 2600, 50):
        e.w32(TICK, 200000 + t); e.frame(); out.append((t, len(e.clicks), e.playing()))
    del e; gc.collect()
    first = {}
    for t, n, _ in out:
        first.setdefault(n, t)
    start = next((t for t, _, p in out if p), None)
    return [first.get(k) for k in (1, 2, 3, 4)], start


def main(img, man, prev=None, pman=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    c, st = clicks(img, man)
    check(c == [0, 600, 1200, 1800] and st == 2400, f"p0 = 100 BPM, p1 = 120: clicks at {c} ms, the transport at {st} ms (600 ms a beat)")
    if prev:
        c, st = clicks(prev, pman)
        check(c == [0, 500, 1000, 1500], f"the previous build: clicks at {c} ms (it read p1, 120 BPM)")
    print("count-in BPM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text()),
                       *((Path(a[2]).read_bytes(), json.loads(Path(a[3]).read_text())) if len(a) > 2 else ())) else 0)
