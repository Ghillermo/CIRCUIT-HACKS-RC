"""SC52.9 / Beta 5.32 tests: tools/flipview.py (the flip view of the MIDI 1 / 2 Preset view), through the controller and the real LED task (emu_jumpflip's
harness).

    python tools/emu_flipview.py BUILD.bin manifest.json
  * pad 26 opens the view without changing the mode: pad 26 white, pad 17 (PGM seq) in pad 26's colour from before (off), pad 18 (step flip) dim in
    Synth 1's colour (no last target yet), pads 9-16 and 19-24 dark;
  * pad 17 = patch flip on (pad 17 in the stock toggle's on colour); again = off;
  * pad 18 = step flip on Synth 1 (the default; the engine goes off, as pad 26's patch flip did), pads 9-16 the tracks (MIDI 1 dark, Synth 1 bright); pad 12 = MIDI 2 as the target; the own pad nothing;
  * pad 18 again = off; pad 18 = step flip on MIDI 2 again (the last); pad 17 then = patch flip, the target gone;
  * pads 19-24: nothing; pad 26 closes the view (the mode stays); closed, pads 17-24 are not the destinations any more;
  * the view closes by itself when its LEDs are not asked for in 300 ms.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc48_8 as S  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import emu_sc17_6 as T6  # noqa: E402
import arp as A  # noqa: E402
import jumpseq as J  # noqa: E402
import flipview as FV  # noqa: E402

MGR, PRESS, RELEASE = S.MGR, T6.PRESS, T6.RELEASE


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = S.ET(img, man)
    R = man["report"]
    F = {k: int(v, 16) for k, v in R["jumpflip"]["labels"].items()}
    t = [500000]
    def at(ms): t[0] += ms; e.w32(A.HAL_TICK, t[0])
    at(0)
    rec = e.r32(J.SESSION_OBJ + 0x14) + J.TAIL + J.O_JS
    tail = lambda: bytes(e.uc.mem_read(rec, 3))
    pad = lambda q: (e.call(PRESS, MGR, q, 100, maxins=8_000_000), e.call(RELEASE, MGR, q, maxins=8_000_000), at(10))
    st = lambda: (e.call(F["c_jfst"], 0, maxins=2_000_000), e.uc.reg_read(UC_ARM_REG_R0))[1]
    pal = lambda i: struct.unpack_from("<H", img, J.PAL + 2 * i - 0x08010000)[0]
    bright, dim = [pal(1 + k) for k in range(8)], [pal(9 + k) for k in range(8)]
    PF = 25
    e.uc.mem_write(rec, bytes(3))
    e.btn(2); e.btn(8); at(10)
    f0 = X.frame(e)
    pf_off = f0[PF]
    import emu_sc22_4 as T4
    V = T4.V
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05])); at(10); X.frame(e)       # the engine on (the oscillator)
    pad(PF); f = X.frame(e)
    check(st() == 0 and f[PF] == FV.WHITE and f[16] == pf_off and f[17] == dim[0] and f[8:16] == [0] * 8 and f[18:24] == [0] * 6,
          f"pad 26: the view open, no mode ({f[PF]:#x}, 17 {f[16]:#x}, 18 {f[17]:#x}, {[hex(x) for x in f[8:24]]})")
    pad(16); f = X.frame(e)
    check(st() == 1 and f[16] != pf_off and f[16] != 0 and f[8:16] == [0] * 8, f"pad 17: patch flip (PGM seq) on, pad 17 lit ({f[16]:#x})")
    pad(16); f = X.frame(e)
    check(st() == 0 and f[16] == pf_off, f"pad 17 again: off ({st()})")
    pad(17); X.frame(e); at(10); f = X.frame(e)
    check(e.r8(V.TAIL + V.O_FLAGS) & 1 == 0, f"step flip turned the engine off, as pad 26 did ({e.r8(V.TAIL + V.O_FLAGS):#x})")
    want = [bright[0] if k == 0 else (0 if k == 2 else dim[k]) for k in range(8)]
    check(st() == 2 and tail() == bytes([1, 0, J.SIG]) and f[17] == bright[0] and f[8:16] == want,
          f"pad 18: step flip on Synth 1, row 2 the tracks ({tail().hex()}, {[hex(x) for x in f[8:16]]})")
    pad(11); f = X.frame(e)
    check(tail()[0] == 4 and f[11] == bright[3] and f[17] == bright[3], f"pad 12: MIDI 2 the target ({tail().hex()})")
    pad(10); check(tail()[0] == 4, "the own track's pad: nothing")
    pad(17); f = X.frame(e)
    check(st() == 0 and tail()[0] == 0 and f[17] == dim[3] and f[8:16] == [0] * 8, f"pad 18 again: off, pad 18 dim in MIDI 2's colour ({f[17]:#x})")
    pad(17); check(st() == 2 and tail()[0] == 4, f"pad 18: step flip on the last target, MIDI 2 ({tail().hex()})")
    pad(16); check(st() == 1 and tail()[0] == 0, f"pad 17 with step flip: patch flip, the target gone ({st()}, {tail().hex()})")
    pad(20); check(st() == 1, "pad 21: nothing")
    pad(PF); f = X.frame(e)
    check(st() == 1 and f[PF] != FV.WHITE and f[17] != dim[3] and f[17] != bright[3], f"pad 26: the view closed, patch flip stays ({f[PF]:#x}, {f[17]:#x})")
    pad(16); check(st() == 1, "closed: pad 17 is not the mode's")
    pad(PF); X.frame(e); at(400); f = X.frame(e)
    check(f[PF] != FV.WHITE, f"no LED call for 400 ms: the view closed by itself ({f[PF]:#x})")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} FLIPVIEW RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
