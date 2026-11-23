"""Alpha 7.29 test (novasec.use_v2) through the controller (Shift / Clear / Duplicate really held) and the LED task, on Synth 1's alt page:
  * Shift + pad 1 = Macros 2 (pad 1 in vcf21.NS_COL); pad 1 = Macros again;
  * OSC 1, Duplicate + K1 (semitones, macro destination 7) = the first macro whose slot 1 had no depth gets destination 7, start 0, end 127, full
    depth; Duplicate + K1 again = nothing more (already on a macro);
  * OSC 1, Duplicate + K3 (wave: not a macro destination) = the first extra knob = that row, the block in Synth 1's patterns' bytes 38 / 39 valid;
  * Macros 2, K1 turned = the wave moves (a list: 4 events a wave); its LED lit, an unassigned knob's dark;
  * Clear + that macro's knob on Macros = its slot 1's depth back to 0 (64); Clear + K1 on Macros 2 = the extra knob freed.
  * (7.30, novasec.use_fix) the block in bytes 4 / 5: a Duplicate leaves fm8store's bytes 8..39 alone, and fm8store's project put (c_fsprj)
    leaves the block valid (7.29: bytes 38 / 39 = the FM's, the block lost at every save).
    python tools/emu_novasec2.py firmware/a7.30
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn.arm_const import UC_ARM_REG_R0
import emu_sc48_8 as S
import emu_sc42_6 as X
import arp as A
import novasec as N
import vcf21 as V

MGR, GETTER = S.MGR, 0x08036192
PRESS, RELEASE, KNOB, BTN, BTN_UP = 0x08033282, 0x080332FE, 0x08033848, 0x08033320, 0x0803381A
ID_CLEAR, ID_DUP = 23, 24


def main(a):
    d = Path(a[0]); img = next(d.glob("*.bin")).read_bytes(); man = json.loads((d / "manifest.json").read_text())
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    fix = "t_dupv" in man["report"]["novasec"]["labels"]
    if fix: N.use_fix()
    e = S.ET(img, man)
    t = [500000]
    def at(ms): t[0] += ms; e.w32(A.HAL_TICK, t[0])
    def frame(): at(20); X.frame(e); return X.frame(e)
    def pad(q, shift=False):
        if shift: e.set_p0(e.r32(MGR + 0xC), 1)
        e.call(PRESS, MGR, q, 100, maxins=8_000_000); e.call(RELEASE, MGR, q, maxins=8_000_000)
        if shift: e.set_p0(e.r32(MGR + 0xC), 0)
        frame()
    def knob(k, dl, n=1, held=None):
        if held is not None: e.call(BTN, MGR, held, maxins=8_000_000)
        for _ in range(n): e.call(KNOB, MGR, k, dl & 0xFFFFFFFF, maxins=8_000_000)
        if held is not None: e.call(BTN_UP, MGR, held, maxins=8_000_000)
        frame()
    def get(p): e.call(GETTER, 0, p, maxins=400_000); return e.uc.reg_read(UC_ARM_REG_R0) & 0xFF
    gst = int(man["report"]["sc14"]["labels"]["c_gst"], 16)
    def alt():
        e.call(gst, maxins=100_000); g = e.uc.reg_read(UC_ARM_REG_R0)
        return g and e.r8(g + N.S_PAINT) & N.F_SRC and e.r8(MGR + 0x152) == 0
    def xblock():
        rec = e.r32(N.SESSION + 0x14)
        return [e.r8(rec + N.SYN_AREA + N.PSIZE * (k >> 1) + N.PSET + N.XB + (k & 1)) for k in range(10)]
    at(0)
    for _ in range(5):
        if alt(): break
        e.btn(0); frame()
    check(alt(), "Synth 1's alt page reached")
    pad(0, shift=True); f = frame()
    check(f[0] == V.NS_COL, f"Shift + pad 1 = Macros 2 (pad 1 {f[0]:#x})")
    pad(0); f = frame()
    check(f[0] != V.NS_COL, "pad 1 = Macros again")
    depth = lambda m: get(N.MAC0 + 17 * m + 3)
    m0 = 2
    knob(m0, -1, held=ID_CLEAR)
    check(depth(m0) == 64, f"Clear + K{m0 + 1} on Macros: macro {m0 + 1}'s slot 1 freed (depth 0 = 64: {depth(m0)})")
    free = [m for m in range(8) if depth(m) == 64]
    pad(1)                                                                                  # OSC 1
    knob(0, 1, held=ID_DUP)
    mf = free[0]
    check(get(N.MAC0 + 17 * mf) == 7 and get(N.MAC0 + 17 * mf + 1) == 0 and get(N.MAC0 + 17 * mf + 2) == 127 and depth(mf) == 127,
          f"Duplicate + K1 (semitones): the first free macro ({mf + 1}) = destination 7, 0..127, full depth ({[get(N.MAC0 + 17 * mf + k) for k in range(4)]})")
    xb0 = xblock(); knob(0, 1, held=ID_DUP)
    check(xblock() == xb0 and [m for m in range(8) if depth(m) == 64] == [m for m in free if m != mf], "Duplicate + K1 again: nothing more")
    def fmbytes():
        rec = e.r32(N.SESSION + 0x14)
        return [bytes(e.uc.mem_read(rec + N.SYN_AREA + N.PSIZE * p + N.PSET + 8, 32)) for p in range(8)]
    fm0 = fmbytes()
    knob(2, 1, held=ID_DUP); xb = xblock()
    if fix: check(fmbytes() == fm0, "the Duplicate left fm8store's bytes 8..39 alone")
    check(xb[0] == N.XSIG and xb[2] == 6 and xb[3:10] == [0xFF] * 7 and xb[1] == (sum(xb[2:10]) ^ 0xA5) & 0xFF,
          f"Duplicate + K3 (wave, no free macro left): extra knob 1 = row 6, the block valid ({xb})")
    if fix:
        fsprj = int(man["report"]["fm8"]["labels"]["c_fsprj"], 16)
        e.call(fsprj, 0, 0, maxins=2_000_000)
        xb2 = xblock()
        check(xb2 == xb and fmbytes() != fm0, f"fm8store's project put (Synth 1's FM block written) left the extra knobs' block valid ({xb2[:4]})")
    pad(0, shift=True)
    w0 = get(6); knob(0, 1, 3); w1 = get(6); knob(0, 1, 1); w2 = get(6); f = frame()
    check(w1 == w0 and w2 == min(w0 + 1, 29), f"Macros 2, K1 = the wave (4 events a wave: {w0}, {w1}, {w2})")
    check(f[60] & 0xFF == V.NS_COL and f[61] == 0, f"its LED lit, K2's dark ({f[60]:#x}, {f[61]:#x})")
    knob(0, -1, held=ID_CLEAR); xb = xblock()
    check(xb[2] == 0xFF and xb[0] == N.XSIG and xb[1] == (sum(xb[2:10]) ^ 0xA5) & 0xFF, f"Clear + K1 on Macros 2: the extra knob freed ({xb[:4]})")
    print("NOVASEC2 RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
