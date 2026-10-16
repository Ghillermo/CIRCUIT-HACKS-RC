"""SC41.7 ARM tests: K3 of the drums split (persist19 / nrpn28 use_k3split), through the controller's knob route (0x08033848).

    python tools/emu_k3split.py NEW.bin NEW_manifest.json PREVIOUS.bin PREVIOUS_manifest.json
  * K3: below the decay's maximum the stock decay exactly as the previous build (the same parameter writes); right past 127 = our attack (no stock write); left:
    the attack back to 0 first (no stock write), then the stock decay;
  * Shift + K3: left = the start moves in, right = the start back to 0 first, then the cut; left again: the cut back first; limited to 120; no stock write
    (the previous build: the stock decay);
  * the block in the record's tail: "DRX1", its sum, 3 bytes per drum; Clear + K3 right: ours to 0;
  * the DSP service tick: the extended values and AINC (C / A^2, limited), STARTF = S << 16, ENDC = E << 16 in the drum's block;
  * a load without the block: zeros + the old start nibble (S = 2 s); with the block: kept; a new project: zeros;
  * the K3 LED: the attack in white with its brightness, else the stock decay; with Shift the start in the drum's colour, the cut in white;
  * NRPN: out LSB 14 / 10 / 13 on a turn; in: LSB 13 sets the cut.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc19_8 import EW  # noqa: E402
from emu_sc19 import OBJ  # noqa: E402
from emu_sc19_6 import DCODE  # noqa: E402
from emu_sc35 import MGR  # noqa: E402
import persist19 as P  # noqa: E402
import drums2_dsp as DD  # noqa: E402

C = round(DD.NFR * 2 ** 23 * 127 ** 2 / (DD.FS * P.K3_ATK_MAX))


def ainc(a): return 0 if a == 0 else min(0x7FFFFF, C // (a * a))


class EK(EW):
    def __init__(self, image, man):
        super().__init__(image, man)
        self.k3 = {k: int(v, 16) for k, v in man["report"]["persist19"]["labels"].items() if k.startswith("c_k3")}
    def k3blk(self): return self.r32(OBJ + 0x14) + P.K3_TAIL + P.K3_OFF
    def k3raw(self): return bytes(self.uc.mem_read(self.k3blk(), 17))
    def get(self, d, which):
        self.call(self.k3["c_k3get"], d, which); return self.uc.reg_read(UC_ARM_REG_R0)
    def ase(self, d): return tuple(self.get(d, w) for w in range(3))
    def decay(self, d): return self.macro(d, 1)
    def setflags(self, v):
        self.call(int(self.man["report"]["sc17"]["labels"]["c_gfst"], 16)); b = self.uc.reg_read(UC_ARM_REG_R0)
        self.uc.mem_write(b + P.FLAGS, bytes([v]))
    def clear(self, d, on):
        st = self.r32(self.mh(d) + 0x1C); self.call(0x080354FA, st, 0); p = self.uc.reg_read(UC_ARM_REG_R0)
        self.uc.mem_write(p, bytes([(self.r8(p) | 1) if on else (self.r8(p) & ~1)])); self.call(0x080353C0, st)


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    gc.collect(); n = EK(img, man); n.man = man
    gc.collect(); o = EW(prev, prev_man)
    n.uc.mem_write(n.k3blk(), bytes(17))                                               # a project without our block
    d = 1
    for x in (n, o): x.sel(d)
    check(n.ase(d) == (0, 0, 0), f"no block: attack, start, cut = 0 ({n.ase(d)})")
    # ---- K3: the decay below its maximum = the stock's, exactly
    while n.decay(d) > 100:                                                          # (inside the stock range in both builds: no start nibble, no attack)
        for x in (n, o): x.knob19(2, -3)
    ws = [(n.turn(2, 3), o.turn(2, 3)) for _ in range(6)]
    check(all(a == b and a for a, b in ws) and n.ase(d) == (0, 0, 0), f"K3 right below the maximum: the stock decay writes, as the previous build ({ws[0][0]})")
    while n.decay(d) < 127: n.knob19(2, 5)                                         # (a turn that reaches 127 stays in the stock range)
    dmax = n.decay(d)
    w1 = n.turn(2, 4); a1 = n.ase(d)
    w2 = n.turn(2, 10); a2 = n.ase(d)
    check(dmax == 127 and w1 == [] and a1 == (4, 0, 0) and w2 == [] and a2 == (14, 0, 0), f"K3 right past the decay's maximum ({dmax}): the attack 4, 14, no stock write ({w1}, {w2})")
    for _ in range(40): n.knob19(2, 5)
    check(n.ase(d)[0] == 127, f"the attack stops at 127 ({n.ase(d)})")
    w3 = n.turn(2, -100); a3 = n.ase(d); w4 = n.turn(2, -30); a4 = n.ase(d); w5 = n.turn(2, -3)
    check(w3 == [] and a3 == (27, 0, 0) and w4 == [] and a4 == (0, 0, 0) and w5 and n.decay(d) == 124, f"K3 left: the attack back to 0 first ({a3}, {a4}), no stock write; then the decay ({n.decay(d)})")
    # ---- Shift + K3: start / cut
    seq = []
    for delta in (-10, 4, 10, 5, -2, -5, -3, -200):
        w = n.turn(2, delta, shift=True); seq.append((n.ase(d)[1:], w))
    want = [(10, 0), (6, 0), (0, 0), (0, 5), (0, 3), (0, 0), (3, 0), (120, 0)]
    check([s for s, _ in seq] == want and all(w == [] for _, w in seq), f"Shift + K3: start / cut {[s for s, _ in seq]} (want {want}), no stock write")
    for _ in range(4): n.turn(2, 100, shift=True)
    check(n.ase(d)[1:] == (0, 120), f"Shift + K3 right: the start back to 0, then the cut up to 120 ({n.ase(d)[1:]})")
    ow = o.turn(2, 3, shift=True)
    check(ow != [], f"the previous build: Shift + K3 = the stock decay ({ow})")
    # ---- the block
    raw = n.k3raw()
    check(raw[:4] == b"DRX1" and raw[5 + 3 * d:8 + 3 * d] == bytes([0, 0, 120]) and raw[4] == (sum(raw[5:17]) ^ 0x5A) & 0xFF,
          f"the block in the record's tail: {raw.hex()}")
    # ---- the tick: DSP words
    n.turn(2, -120, shift=True); n.turn(2, -40, shift=True)                         # cut 0, start 40
    for _ in range(30): n.knob19(2, 5)
    for _ in range(9): n.knob19(2, 1)                                                 # attack 9
    msgs = n.drain()
    flat = [m for ms in msgs for m in ms]
    blk = DD.DB + DD.STRIDE * d
    got = {a - blk: v for c_, v, a in flat if blk <= a < blk + DD.STRIDE}
    A, S, Ecut = n.ase(d)
    check(got.get(DD.AINC) == ainc(A) and got.get(DD.STARTF) == S << 16 and got.get(DD.ENDC) == Ecut << 16 and DD.EXT in got,
          f"the tick: AINC {got.get(DD.AINC, 0):#x} (A {A}: {ainc(A):#x}), STARTF {got.get(DD.STARTF, 0):#x}, ENDC {got.get(DD.ENDC, 0):#x} with the extended values")
    check(ainc(1) == 0x7FFFFF and abs(ainc(127) - 2 ** 23 * DD.NFR / DD.FS / P.K3_ATK_MAX) < 2, f"the attack's increment: A 1 = {ainc(1):#x} (one block), A 127 = {ainc(127):#x} per block (~{P.K3_ATK_MAX:.1f} s)")
    # ---- Clear + K3 right
    before = n.ase(d); dk0 = n.decay(d)
    n.clear(d, True); w = n.turn(2, 3); n.clear(d, False)
    check(before != (0, 0, 0) and n.ase(d) == (0, 0, 0), f"Clear + K3 right: ours to 0 ({before} -> {n.ase(d)}); the stock's Clear: decay {dk0} -> {n.decay(d)}, writes {w}")
    # ---- load / new project
    n.turn(2, -20, shift=True)                                                       # start 20 in the block
    n.setflags(P.F_RESYNC); n.drain()
    check(n.ase(d) == (0, 20, 0), f"a load with the block: kept ({n.ase(d)})")
    n.uc.mem_write(n.k3blk(), bytes(17))
    sig = (n.xm(P.XM_SIG) & 7) | P.SIG << 3; n.setxm(P.XM_SIG, sig); n.setrec(P.XM_SIG, sig)          # (a project saved with our XMEM signature)
    for i in (P.XM_DRUMS + 27, P.XM_DRUMS + 27 + 2):                                 # drum 4: the start nibble 5 (bits 0 / 2 = bit 7 of its bytes 0 / 2), store and record
        n.setxm(i, n.xm(i) | 0x80); n.setrec(i, n.rec(i) | 0x80)
    n.setflags(P.F_RESYNC); n.drain()
    check(n.k3raw()[:4] == b"DRX1" and n.ase(3) == (0, 10, 0) and n.ase(d) == (0, 0, 0), f"a load without the block: the old start nibble 5 -> S 10 ({n.ase(3)}), the rest 0")
    n.turn(2, -30, shift=True)
    n.setflags(P.F_RESYNC | P.F_NEW); n.drain()
    check(all(n.ase(x) == (0, 0, 0) for x in range(4)), "a new project: zeros")
    # ---- LEDs
    n.track(4 + d)
    for _ in range(30): n.knob19(2, 5)
    n.call(n.k3["c_k3put"], d, 0, 0)
    for _ in range(50): n.knob19(2, 1)
    f = n.frame()
    n.set_p0(n.r32(MGR + 0xC), 1); fs0 = n.frame(); n.set_p0(n.r32(MGR + 0xC), 0)
    n.turn(2, -30, shift=True)
    n.set_p0(n.r32(MGR + 0xC), 1); fs1 = n.frame(); n.set_p0(n.r32(MGR + 0xC), 0)
    n.turn(2, 100, shift=True); n.turn(2, 25, shift=True)
    n.set_p0(n.r32(MGR + 0xC), 1); fs2 = n.frame(); n.set_p0(n.r32(MGR + 0xC), 0)
    for _ in range(80): n.knob19(2, -1)
    f0 = n.frame()
    check(f[62] == P.K3_COL_WHITE | (50 + 2) << 8 and fs0[62] == P.K3_COL_WHITE | 2 << 8 and fs1[62] == DCODE[d] | (30 + 2) << 8 and fs2[62] == P.K3_COL_WHITE | (25 + 2) << 8
          and f0[62] >> 8 < 2, f"the K3 LED: attack 50 {f[62]:#x}, Shift neutral {fs0[62]:#x}, start 30 {fs1[62]:#x}, cut 25 {fs2[62]:#x}, no attack = the stock's {f0[62]:#x}")
    # ---- NRPN
    for _ in range(30): n.knob19(2, 5)
    n.call(n.k3["c_k3put"], d, 0, 0)
    n.ev.clear(); n.knob19(2, 7)
    cc = [bytes.fromhex(x[1][:6]) for x in n.ev if x[0] == "ext"]
    nr = [(c[1], c[2]) for c in cc if c[0] & 0xF0 == 0xB0]
    check((99, 5 + d) in nr and (98, 14) in nr and (6, 7) in nr, f"NRPN out: MSB {5 + d}, LSB 14 (attack), value 7 ({nr})")
    n.call(int(man["report"]["nrpn28"]["labels"]["c_nset"], 16), d, 13, 44)
    check(n.ase(d)[2] == 44, f"NRPN in: LSB 13 = the cut 44 ({n.ase(d)})")
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
