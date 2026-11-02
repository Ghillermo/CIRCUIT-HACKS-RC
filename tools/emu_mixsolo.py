"""SC50.5 / Beta 5.8: solo in the Mixer (mixsolo), through the controller and the real LED task:
  * pad 16 held + pad 1: only Synth 1 sounds; + pad 3 as well: Synth 1 and MIDI 1; pad 16 let go: the mutes stay; pad 1 alone toggles as always;
  * pad 16 again + pad 6: the choice starts anew;
  * pad 16 dim, bright while held; with Shift it is the repeats' row; on Master FX it is not ours;
  * the Gater's depth, GOFF read from the MIX table the other way round (build_sc17.use_nogoff): within 0.1 % of the old table.

    python tools/emu_mixsolo.py NEW.bin NEW_manifest.json
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_cscale as ECS  # noqa: E402
import emu_sc46_3 as T  # noqa: E402
import build_sc17 as S  # noqa: E402
import mixsolo as M  # noqa: E402
import qmute as Q  # noqa: E402

MGR = ECS.MGR
PARAM_GET = 0x0803542C


class P(ECS.EC):
    def __init__(self, img, man):
        super().__init__(bytearray(img), {k: int(v, 16) for k, v in man["report"]["cscale"]["labels"].items()})
        self.at(100000); self.transport(0)
    press = T.E.press; release = T.E.release; tap = T.E.tap
    def muted(self):
        v = Q.MIX_VIEW; base, k = self.r32(v + 0x68), self.r32(v + 0x60)
        return [self.r8(self.r0(PARAM_GET, self.r32(base + k * t), 0)) for t in range(8)]


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = P(img, man); e.btn(14)
    check(e.muted() == [0] * 8, f"the Mixer: nothing muted ({e.muted()})")
    d0 = e.frame()[M.PAD_SOLO] & 0xFF
    e.press(M.PAD_SOLO); d1 = e.frame()[M.PAD_SOLO] & 0xFF
    check(d0 == M.COL_DIM and d1 == M.COL_ON, f"pad 16 dim, bright held ({d0:#x}, {d1:#x})")
    e.tap(0); a = e.muted()
    check(a == [0, 1, 1, 1, 1, 1, 1, 1], f"pad 16 + pad 1: only Synth 1 ({a})")
    e.tap(2); b = e.muted()
    check(b == [0, 1, 0, 1, 1, 1, 1, 1], f"+ pad 3: Synth 1 and MIDI 1 ({b})")
    e.release(M.PAD_SOLO); c = e.muted()
    check(c == b, f"pad 16 let go: the mutes stay ({c})")
    e.tap(1); c2 = e.muted()
    check(c2 == [0, 0, 0, 1, 1, 1, 1, 1], f"pad 2 alone: the stock's toggle ({c2})")
    e.press(M.PAD_SOLO); e.tap(5); d = e.muted(); e.release(M.PAD_SOLO)
    check(d == [1, 1, 1, 1, 1, 0, 1, 1], f"pad 16 again + pad 6: the choice anew ({d})")
    fs = e.frame(shift=True)[M.PAD_SOLO] & 0xFF
    check(fs != M.COL_DIM, f"with Shift: the repeats' row ({fs:#x})")
    e.btn(14); f = e.frame()[M.PAD_SOLO] & 0xFF; m0 = e.muted()
    e.press(M.PAD_SOLO); e.press(0); m1 = e.muted(); e.release(0); e.release(M.PAD_SOLO)
    check(m0 == m1 and f != M.COL_ON, f"Master FX: its pads ({f:#x})")
    del e; gc.collect()
    t = S.tables()
    w = max(abs(t["GOFF"][k] - t["MIX"][127 - k]) for k in range(128))
    check(w < 0.0011 * (1 << 23) and t["MIX"][0] == 0, f"GOFF from MIX the other way round: at most {100 * w / (1 << 23):.2f} %")
    print(f"{man.get('marker', '?')} MIXSOLO RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
