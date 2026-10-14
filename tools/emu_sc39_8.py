"""SC39.8 ARM tests (live RAM dump, the real routes: the controller's buttons and pads; the project's parameters through the stock getter; the DSP
words on the harness's model): the delay throw of Digitise (tools/throw.py).

    python tools/emu_sc39_8.py SC39.8.bin SC39.8_manifest.json SC39.7.bin SC39.7_manifest.json
  * the Master FX view; the eight delay sends set to different values;
  * pad 4 (Digitise) pressed: the eight sends = K3; the reverb sends untouched; the effect itself on (held); the DSP semaphore balanced;
  * the pad let go: the eight sends back to what they were;
  * K3 = 0: no throw; Shift + pad 4 (the latch): no throw; a tap on the latched effect: no throw;
  * the view left with the pad held (no release): the next button puts the sends back;
  * K3's default is 100; the previous build: pad 4 never touches the sends.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc35 import E35, MGR  # noqa: E402
import build_sc17 as S  # noqa: E402
import throw as TH  # noqa: E402

B = 0x08010000
ORIG = [5, 17, 0, 127, 64, 33, 90, 1]


class E8(E35):
    def setup(self, man):
        self.L8 = {k: int(v, 16) for k, v in man["report"]["sc17"]["labels"].items()}
    def get(self, i): self.call(TH.GETTER, TH.SEND_TYPE, i); return self.uc.reg_read(UC_ARM_REG_R0) & 0xFF
    def put(self, i, v):
        this = self.r32(self.r32(self.r32(TH.CTX) + 0x10)); self.call(TH.PARAM_SET, this + 4, TH.SEND_TYPE, i, v, maxins=3_000_000)
    def dly(self): return [self.get(TH.DELAY0 + i) for i in range(8)]
    def rev(self): return [self.get(i) for i in range(8)]
    def blk8(self): self.call(self.L8["c_gfst"]); return self.uc.reg_read(UC_ARM_REG_R0)


def run(img, man, new):
    e = E8(img, man); e.setup(man); o = {}
    e.grid(); blk = e.blk8()
    o["k3"] = e.r8(blk + TH.K_THROW)
    for i, v in enumerate(ORIG): e.put(TH.DELAY0 + i, v)
    rv = e.rev(); o["set"] = e.dly()
    e.uc.mem_write(blk + TH.K_THROW, bytes([100]))
    e.pad(TH.PAD_DIG); o["on"] = (e.dly(), e.rev() == rv, e.r8(blk + S.S_HELD) >> TH.PAD_DIG & 1, e.sem, e.x.get(TH.FLAG))
    e.rel(TH.PAD_DIG); o["off"] = (e.dly(), e.rev() == rv, e.r8(blk + S.S_HELD) >> TH.PAD_DIG & 1, e.sem, e.x.get(TH.FLAG))
    if not new:
        del e; gc.collect(); return o
    e.uc.mem_write(blk + TH.K_THROW, bytes([37])); e.pad(TH.PAD_DIG); a = e.dly(); e.rel(TH.PAD_DIG); o["k37"] = (a, e.dly())
    e.uc.mem_write(blk + TH.K_THROW, bytes([0])); e.pad(TH.PAD_DIG); a = e.dly(); e.rel(TH.PAD_DIG); o["k0"] = (a, e.dly())
    e.uc.mem_write(blk + TH.K_THROW, bytes([100]))
    e.pad(TH.PAD_DIG, shift=True); a = e.dly(); lat = e.r8(blk + S.S_LATCH) >> TH.PAD_DIG & 1; e.rel(TH.PAD_DIG)
    e.pad(TH.PAD_DIG); b_ = e.dly(); lat2 = e.r8(blk + S.S_LATCH) >> TH.PAD_DIG & 1; e.rel(TH.PAD_DIG)
    o["latch"] = (a, lat, b_, lat2, e.dly())
    e.pad(TH.PAD_DIG); a = e.dly(); e.btn(9); o["left"] = (a, e.dly(), e.x.get(TH.FLAG), e.sem)      # another view, the pad never released
    del e; gc.collect()
    return o


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["throw"]["labels"].items()}
    w = lambda a: struct.unpack_from("<I", img, a - B)[0]
    from thumb import b_w
    check(w(S.MIX2["MIX_VT"]) == L["c_thpress"] | 1 and w(S.MIX2["MIX_VT"] + 4) == L["c_threl"] | 1 and bytes(img[TH.BTN_ENTRY - B:TH.BTN_ENTRY - B + 4]) == b_w(TH.BTN_ENTRY, L["c_thbtn"]),
          "the hooks: slots 0 / 1 of the Mixer view, the head of the button chain")
    o = run(img, man, True)
    check(o["k3"] == 100 and o["set"] == ORIG, f"the Master FX view; K3 of Digitise starts at {o['k3']}; the delay sends set ({o['set']})")
    d, rv, held, sem, flag = o["on"]
    check(d == [100] * 8 and rv and held == 1 and sem == 0 and flag == TH.MAGIC, f"pad 4 held: the eight delay sends at K3 ({d}); the reverb sends untouched; Digitise on; the semaphore balanced")
    d, rv, held, sem, flag = o["off"]
    check(d == ORIG and rv and held == 0 and sem == 0 and flag == 0, f"let go: the sends back ({d})")
    check(o["k37"] == ([37] * 8, ORIG), "K3 = 37: the throw at 37")
    check(o["k0"] == (ORIG, ORIG), "K3 = 0: no throw")
    a, lat, b_, lat2, end = o["latch"]
    check(a == ORIG and lat == 1 and b_ == ORIG and lat2 == 0 and end == ORIG, "Shift + pad 4 (the latch) and the tap that switches it off: no throw")
    a, b_, flag, sem = o["left"]
    check(a == [100] * 8 and b_ == ORIG and flag == 0 and sem == 0, "the view left with the pad held: the button press puts the sends back")
    gc.collect(); q = run(prev, prev_man, False)
    check(q["on"][0] == ORIG and q["off"][0] == ORIG and q["k3"] == 0, "the previous build: pad 4 never touches the sends (K3 was 0 and did nothing)")
    print("SC39.8 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
