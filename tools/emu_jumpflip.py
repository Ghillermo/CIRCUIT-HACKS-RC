"""SC51.6 / Beta 5.19 tests: tools/jumpflip.py (the jump sequencer's destinations in the patch flip mode), through the controller and the real LED task
(emu_jumpseq's harness).

    python tools/emu_jumpflip.py BUILD.bin manifest.json
  * MIDI 1's Preset view: pad 26 = patch flip (the stock's toggle): pads 17-24 = the eight tracks dim in their colours, MIDI 1's own dark; pads 9-16 dark;
  * pad 17 = step flip on Synth 1: the jump target, patch flip off, pad 17 bright, pad 26 blinks in its colour, pad 27 the engine's off colour;
  * pad 21 = Drum 1 instead; the own track's pad: nothing; the lit one again = patch flip, no target;
  * step flip, then pad 26 = all off: no target, no patch flip, pads 17-24 as before;
  * a target found while patch flip is on: step flip wins, patch flip goes off;
  * patch flip on, pads 9-16: nothing; the engine row (pad 27): pads 9-16 dark and they point at nothing.
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
import jumpflip as JF  # noqa: E402
import build_sc06 as S6  # noqa: E402
import modesel as MS  # noqa: E402

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
    PF = 25                                                                            # (pad 26: vcf21.use_layout sets build_sc06.PF_PAD in the builds)
    e.uc.mem_write(rec, bytes(3))
    e.btn(2); e.btn(8); at(10)
    f0 = X.frame(e)
    check(st() == 0, "MIDI 1's Preset view: neither flip mode")
    pad(PF); f = X.frame(e)
    want = [dim[k] if k != 2 else 0 for k in range(8)]
    check(st() == 1 and f[16:24] == want and f[8:16] == [0] * 8, f"pad 26: patch flip; pads 17-24 the tracks dim, MIDI 1 dark; pads 9-16 dark ({[hex(x) for x in f[16:24]]})")
    pad(16); f = X.frame(e)
    blink = lambda k: dim[k] if t[0] & 0x100 else bright[k]
    check(tail() == bytes([1, 0, J.SIG]) and st() == 2 and f[16] == bright[0] and f[PF] == blink(0) and f[MS.PAD] == JF.COL_OFF,
          f"pad 17: step flip on Synth 1, pad 26 in its colour, pad 27 off ({tail().hex()}, {f[PF]:#x}, {f[MS.PAD]:#x})")
    at(256); f1 = X.frame(e); at(256); f2 = X.frame(e)
    check({f1[PF], f2[PF]} == {bright[0], dim[0]}, f"pad 26 blinks, 256 ms each ({f1[PF]:#x}, {f2[PF]:#x})")
    pad(20); f = X.frame(e)
    check(tail() == bytes([5, 0, J.SIG]) and f[20] == bright[4] and f[16] == dim[0], f"pad 21: Drum 1 instead ({tail().hex()})")
    pad(18); check(tail() == bytes([5, 0, J.SIG]), "MIDI 1's own pad: nothing")
    pad(20); f = X.frame(e)
    check(tail()[0] == 0 and st() == 1 and f[16:24] == want, f"the lit one again: patch flip, no target ({tail().hex()}, {st()})")
    pad(20); pad(PF); f = X.frame(e)
    check(tail()[0] == 0 and st() == 0 and f[16:24] == f0[16:24], f"step flip, then pad 26: all off, pads 17-24 as before ({tail().hex()}, {st()})")
    pad(PF); pad(8); check(st() == 1 and tail()[0] == 0, "patch flip: pad 9 does nothing")
    pad(PF)
    pad(PF); check(st() == 1, "patch flip on")
    e.uc.mem_write(rec, bytes([5, 0, J.SIG])); at(10); X.frame(e); e.uc.mem_write(rec, bytes(3)); at(10); X.frame(e)
    check(st() == 0, f"a target written while patch flip is on (a project's): step flip wins, patch flip off ({st()})")
    pad(MS.PAD); f = X.frame(e)
    check(e.r8(MS.RAM) == 1 and f[8:16] == [0] * 8, f"the engine row: pads 9-16 dark ({[hex(x) for x in f[8:16]]})")
    pad(8); check(tail()[0] == 0, "the engine row's pad 9: no pointing")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} JUMPFLIP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
