"""SC48 ARM tests (fmeng.use_starters): the FM's instrument starters on pad 8, through the controller and the real LED task (MIDI 1's Preset
view, FM on):
  * pad 8 dim white with FM on; pad 8 held: bright, B_P7 = 2, pads 9-24 = the 16 starters in their families' colours (dim: the track has none
    of their values);
  * pad 8 + pad 9 + i: every FM parameter = starter i, the tonic while held (a new FM note); its pad bright now; Shift + pad: no sound;
  * pad 8 let go: B_P7 = 0, the pads back;
  * pad 7 held: the algorithms as before (pad 7 + pad 17 = only the algorithm: the kick, the other values kept).

    python tools/emu_fmstart.py SC48.bin SC48_manifest.json
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402  (its import sets vcf21's options)
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
import fmeng as F  # noqa: E402

MGR = X.MGR


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = X.EP(Path(img).read_bytes(), man)
    blk = F.FMR + F.B0
    par = lambda i: e.r8(blk + i)
    press = lambda q: e.call(PRESS, MGR, q, 100, maxins=8_000_000)
    release = lambda q: e.call(RELEASE, MGR, q, maxins=8_000_000)
    e.btn(2); e.btn(8); e.pad(26); e.pad(F.ROWPAD)
    check(par(F.B_ON) == 1, "row pad 24: FM on")
    f = X.frame(e)
    check(f[F.PADNO + 1] & 0xFF == 0x02, f"pad 8 dim white with FM on ({f[F.PADNO + 1]:#x})")
    fB = X.frame(e)
    press(F.PADNO + 1); f = X.frame(e)
    dims = [F.ST_FAM[F.ST_OF[i]][1] for i in range(16)]
    check(par(F.B_P7) == 2 and f[F.PADNO + 1] & 0xFF == 0x01 and f[8:24] == dims,
          f"pad 8 held: bright, the starters on pads 9-24 ({[hex(x) for x in f[8:24]]})")
    n0 = len(e.ons); e.uc.mem_write(blk + F.B_NEW, b"\0")
    press(8); f = X.frame(e)
    want = list(F.STARTERS[0][1])
    check([par(i) for i in range(16)] == want and len(e.ons) == n0 + 1 and e.ons[-1][0] == "on" and par(F.B_NEW) == 1,
          f"pad 8 + pad 9: the piano's every parameter, the tonic on ({[par(i) for i in range(16)]})")
    check(f[8] & 0xFF == F.ST_FAM["keys"][0] and f[9] & 0xFF == F.ST_FAM["keys"][1], f"its pad bright, the others dim ({f[8]:#x}, {f[9]:#x})")
    release(8)
    check(e.ons[-1][0] == "off", "pad 9 let go: the tonic off")
    ok = True
    for i in range(1, 16):
        press(8 + i); release(8 + i)
        ok &= [par(k) for k in range(16)] == list(F.STARTERS[i][1])
    check(ok, "every pad 9-24: its starter's values")
    n1 = len(e.ons)
    e.shift(True); press(18); e.shift(False); release(18)
    check([par(i) for i in range(16)] == list(F.STARTERS[10][1]) and len(e.ons) == n1, f"Shift + pad 19: the flute without sound ({e.ons[n1:]})")
    release(F.PADNO + 1); f = X.frame(e)
    check(par(F.B_P7) == 0 and f[8:24] == fB[8:24], "pad 8 let go: the pads back")
    before = [par(i) for i in range(16)]
    press(F.PADNO); f = X.frame(e)
    famw = [F.FAMC[F.ALGS[i]["fam"]][1] for i in range(16)]
    check(par(F.B_P7) == 1 and [x & 0xFF for x in f[8:24]] != dims, f"pad 7 held: the algorithms ({[hex(x) for x in f[8:24]]})")
    press(16); release(16); release(F.PADNO)
    after = [par(i) for i in range(16)]
    check(after[F.P_ALG] == 8 << 3 and after[:F.P_ALG] == before[:F.P_ALG] and after[F.P_ALG + 1:] == before[F.P_ALG + 1:],
          f"pad 7 + pad 17: only the algorithm (the kick), the other values kept")
    del e; gc.collect()
    print(f"{Path(img).stem} RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text())) else 0)
