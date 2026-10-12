"""SC19.1 fuzz: random controller input (buttons with and without Shift, pads, pad releases, knobs) on SC19 and SC19.1 side by side.

    python tools/emu_sc19_fuzz.py SC19.bin SC19.manifest SC19.1.bin SC19.1.manifest [seeds] [steps]

Every step goes through the real controller routes (button 0x08033320 + release 0x0803381A, pad 0x08033282, pad release 0x080332FE, knob
0x08033848).  Checks, per step:
  * no emulation fault (unmapped access, invalid instruction) and no run-away (the call budget is not exhausted) on either image;
  * the SC19.1 flag implies the Preset view of a synth (index 0 or 9) and a synth track;
  * with the flag clear, the controller state (index, track, mode, view) of SC19.1 equals SC19's, except right after a second Synth press
    (SC19 gets the translated Preset tap), and the per-synth modes only differ when the open view changed them.
"""
from __future__ import annotations
import gc, json, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn import UcError  # noqa: E402
import emu_sc19_1 as T  # noqa: E402
from emu_sc08 import MGR  # noqa: E402

BUDGET = 900000


def main(img0, man0, img1, man1, seeds, steps):
    bad = 0
    for seed in range(seeds):
        rnd = random.Random(seed)
        x = T.E191(img1, man1); y = T.E191(img0, man0)
        flag = False; log = []
        for n in range(steps):
            kind = rnd.choice(["btn", "btn", "btn", "pad", "pad", "knob", "shbtn"])
            try:
                if kind in ("btn", "shbtn"):
                    b = rnd.choice([0, 0, 1, 1, 2, 3, 4, 5, 8, 13, 14, 15, 16, 17, 19, 20, 21, 22, 23, 24, 25, 26] if kind == "btn" else [9, 10, 11, 12, 13, 15, 19, 20, 22, 23, 24, 25, 26, 0, 1, 8, 14, 21])
                    sh = kind == "shbtn"
                    log.append((kind, b))
                    if flag and not (b == 27):
                        x.btn(b, sh); y.btn(b, sh); flag = False
                    elif b in (0, 1) and not sh and y.cur() == 9 * b + 1:
                        x.btn(b, sh); y.btn(8); flag = True
                    else:
                        x.btn(b, sh); y.btn(b, sh)
                elif kind == "pad":
                    p = rnd.randrange(32); log.append(("pad", p))
                    sp = x.padr(p)
                    if not flag: y.padr(p)
                    x.call(0x080332FE, MGR, p, maxins=BUDGET)
                    if not flag: y.call(0x080332FE, MGR, p, maxins=BUDGET)
                    if flag and sp: bad += 1; print("   stock press leaked through the open view", seed, log[-3:], sp)
                else:
                    k = rnd.randrange(8); d = rnd.choice([-3, -1, 1, 2, 5]); log.append(("knob", k, d))
                    x.call(0x08033848, MGR, k, d, maxins=BUDGET); y.call(0x08033848, MGR, k, d, maxins=BUDGET)
            except UcError as e:
                bad += 1; print("   EMULATION FAULT", seed, n, log[-4:], e); break
            if bool(x.flag()) != flag:
                bad += 1; print("   flag differs from the model", seed, n, log[-4:], x.flag(), flag); break
            if x.flag() and not (x.cur() in (0, 9) and x.trk() in (0, 1)):
                bad += 1; print("   flag set outside a synth Preset view", seed, n, log[-4:], x.shape()); break
            if x.shape() != y.shape():
                bad += 1; print("   controller state differs", seed, n, log[-4:], x.shape(), y.shape()); break
        else:
            print(f"seed {seed}: {steps} steps ok")
        del x, y; gc.collect()
    print("FUZZ", "ALL PASS" if not bad else f"{bad} problems")
    return bad


if __name__ == "__main__":
    a = sys.argv
    img0 = Path(a[1]).read_bytes(); man0 = json.loads(Path(a[2]).read_text())
    img1 = Path(a[3]).read_bytes(); man1 = json.loads(Path(a[4]).read_text())
    sys.exit(1 if main(img0, man0, img1, man1, int(a[5]) if len(a) > 5 else 4, int(a[6]) if len(a) > 6 else 40) else 0)
