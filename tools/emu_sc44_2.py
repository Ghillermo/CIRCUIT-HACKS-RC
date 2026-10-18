"""SC44.2 ARM tests (tools/modmx.py: the mod matrix of the own synth), through the controller, the real LED task, the whole DSP service chain (the
matrix's tick is its head) and the note vtable's head:
  * MIDI 1's engine on, its Preset view: pad 6 = knob page 6 (vcf21's 5), its LED light blue (bright on the page);
  * K1 (velocity) turned: a slow knob (2 clicks a step); to FILT at full amount = 5 zones in: its LED the VCA / VCF page's orange at full brightness;
    the overlay: pad 1 and pad 13 (FILT = K5 of page 1) bright, the page's other parameters dim; a press on pads 9-24 swallowed while it shows, the
    pads back after it;
  * a note with velocity 127 / 32: FILT goes to the DSP + 126 / + 31 (clamped to 63 / 31), the stored value untouched;
  * K4 (LFO 2) on RES at full amount: RES moves through the DSP while the ticks run;
  * Shift + K4: the shape's colour (triangle green; + 32 clicks: saw yellow);
  * Clear + K1: the source off, FILT back to its stored value; Clear + pad 6: every source off;
  * sample mode: K3 (random) on code 25 = sample numbers in -1..63;
  * the patch: gathering writes "MX", the positions and the parameters at padding + 64; applying a patch with them restores them; without them the
    matrix is off.

    python tools/emu_sc44_2.py SC44.2.bin SC44.2_manifest.json
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R5, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402  (its import sets vcf21's options)
import mpatch as MP  # noqa: E402
import packio as PK  # noqa: E402
import modmx as MX  # noqa: E402

V = T4.V
MGR = X.MGR
CLEAR = 23


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = X.EP(img, man)
    ml = {k: int(v, 16) for k, v in man["report"]["modmx"]["labels"].items()}
    mp = {k: int(v, 16) for k, v in man["report"]["modmx"]["prev"].items()}
    pl = {k: int(v, 16) for k, v in man["report"]["mpatch"]["labels"].items()}
    dw = []
    def w(uc, a, s, d): dw.append((uc.reg_read(UC_ARM_REG_R1) >> 8, uc.reg_read(UC_ARM_REG_R2)))
    e.uc.hook_add(UC_HOOK_CODE, w, begin=0x080292F8, end=0x080292F8)
    prevpad = []
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: prevpad.append(uc.reg_read(UC_ARM_REG_R1)), begin=mp["pad"], end=mp["pad"])
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05]))
    def tick(n=1, step=40):
        for _ in range(n): e.at(e.t + step); e.call(ml["c_mxtick"], maxins=6_000_000)
    tick(10)
    blk = MX.MXR + MX.T0
    pos = lambda k, t=0: struct.unpack_from("<H", bytes(e.uc.mem_read(MX.MXR + MX.T0 + MX.TS * t + 2 * k, 2)))[0]
    sent = lambda code: [struct.unpack("<h", struct.pack("<H", v & 0xFFFF))[0] for v, a in dw if a == V.VB0 and (v >> 16) & 0x7F == code]
    nd = mp["pmax"] // MX.ZONE                                                      # the image's own tables (this process's vcf21 options are older)
    dcode = bytes(e.uc.mem_read(ml["t_dcode"], nd)); rflat = bytes(e.uc.mem_read(ml["t_rows"], 80))
    rows = [tuple(rflat[16 * k:16 * k + 16]) for k in range(5)]
    zone = {c: z for z, c in enumerate(dcode)}
    e.btn(2); e.btn(8)
    e.pad(5); f = X.frame(e)
    pg = e.r0(e.vl["c_vpage"], 0)
    check(pg == MX.PAGE and f[5] == MX.COL_MX[0], f"pad 6: page {pg} (the matrix = {MX.PAGE}), its LED {f[5]:#x}")
    check(MX.MXR <= 0x2004FE00 - 0x1000 and e.r32(MX.MXR) == MX.SIG, f"the RAM set up at {MX.MXR:#x} (signature {e.r32(MX.MXR):#x})")
    # K1 to FILT at full amount: 2 clicks a step
    target = zone[1] * MX.ZONE + MX.ZONE
    e.knob(0, 1); p1 = pos(0)
    e.knob(0, 1); p2 = pos(0)
    for _ in range(2 * target - 2): e.knob(0, 1)
    pf = pos(0); f = X.frame(e)
    check(p1 == 0 and p2 == 1 and pf == target, f"K1: one click nothing ({p1}), two = one step ({p2}); {2 * target} clicks = FILT full ({pf} = {target})")
    col = V.COL_PAGE[0]
    check(f[60] == (8 * 16 - 1 + 2) << 8 | col[0], f"K1's LED: the VCA / VCF page's colour, full brightness ({f[60]:#x})")
    ov = f[8:24]
    exp = [0] * 16
    for i, c in enumerate(rows[0]):
        if c and c != 14: exp[i] = col[1]
    exp[rows[0].index(1)] = col[0]
    check(ov == exp and f[0] == col[0], f"the overlay: pad 1 bright ({f[0]:#x}), pads 9-24 = page 1, FILT bright ({[hex(x) for x in ov]})")
    n0 = len(prevpad); e.pad(12); sw = len(prevpad) == n0
    e.at(e.t + 2000); tick(1); f2 = X.frame(e); e.pad(6); back = len(prevpad) > n0
    check(sw and f2[12] != col[0] and back, f"a press under the overlay swallowed ({sw}); after it the pads are the patches' again ({f2[12]:#x}), presses go on ({back})")
    # a note: FILT through the matrix
    st0 = e.val(0, 1)
    non = e.r32(MX.NOTE_VT) & ~1
    for vel, want in ((127, min(63, st0 + 126)), (32, min(63, st0 + (32 * 16 * 127 >> 11)))):
        dw.clear(); e.call(non, 0x20011334, 2, 60, vel, maxins=4_000_000); tick(12, 4)
        got = sent(1)
        check(got and got[-1] == want and e.val(0, 1) == st0, f"note velocity {vel}: FILT to the DSP {got[-1:]} (stored {st0} + offset = {want}), stored still {e.val(0, 1)}")
    # K4 (LFO 2) on RES, full
    for _ in range(2 * (zone[2] * MX.ZONE + MX.ZONE)): e.knob(3, 1)
    dw.clear(); tick(60, 20)
    rs = sent(2)
    check(len(set(rs)) >= 5 and max(rs) > 60, f"K4 = LFO 2 on RES: RES to the DSP moves ({len(rs)} messages, {len(set(rs))} values, max {max(rs) if rs else None})")
    # Shift + K4: the shape
    e.shift(True); f = X.frame(e); c0 = f[63] & 0xFF
    for _ in range(32): e.knob(3, 1)
    f = X.frame(e); c1 = f[63] & 0xFF; e.shift(False)
    lc = bytes(e.uc.mem_read(ml["t_zcol"], 2))                                          # (the image's colours: modmx.use_v2 changes them)
    check(c0 == lc[0] and c1 == lc[1], f"Shift + K4: triangle {c0:#x}, + 32 clicks: saw {c1:#x}")
    # Clear + K1: off, FILT back
    e.call(0x08033320, MGR, CLEAR, maxins=8_000_000)
    dw.clear(); e.knob(0, 1); tick(12, 4)
    e.call(0x0803381A, MGR, CLEAR, maxins=8_000_000)
    got = sent(1)
    check(pos(0) == 0 and got and got[-1] == st0, f"Clear + K1: off ({pos(0)}), FILT to the DSP back to {got[-1:]} (stored {st0})")
    # the patch: gather / apply
    for _ in range(2 * (zone[3] * MX.ZONE + 5)): e.knob(4, 1)
    p4, p5 = pos(3), pos(4)
    e.call(pl["c_mpgather"], 0, maxins=4_000_000)
    e.call(ml["c_mxgath"], 0, maxins=4_000_000)
    buf = bytes(e.uc.mem_read(PK.BUF + 64, 24))
    check(buf[:3] == b"MX\x01" and struct.unpack_from("<8H", buf, 3)[3:5] == (p4, p5), f"gather: {buf[:3]} the positions {struct.unpack_from('<8H', buf, 3)}")
    # apply: the stock read of the 24 bytes answered from our buffer
    keep = bytes(buf)
    def rd(uc, a, s, d):
        uc.mem_write(uc.reg_read(UC_ARM_REG_R2), keep); uc.reg_write(UC_ARM_REG_R0, 0); uc.reg_write(UC_ARM_REG_R1, 24)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    hk = e.uc.hook_add(UC_HOOK_CODE, rd, begin=pl["c_mpr"], end=pl["c_mpr"])
    for k in range(8): e.call(ml["c_mxset"], 0, k, 0, maxins=2_000_000)
    e.uc.reg_write(UC_ARM_REG_R5, 3)
    e.call(ml["c_mxappl"], 0, maxins=8_000_000)
    ok1 = (pos(3), pos(4)) == (p4, p5)
    keep = bytes(24)
    e.uc.reg_write(UC_ARM_REG_R5, 3); e.call(ml["c_mxappl"], 0, maxins=8_000_000)
    ok2 = all(pos(k) == 0 for k in range(8))
    e.uc.hook_del(hk)
    check(ok1 and ok2, f"apply: a patch with a matrix restores it ({ok1}); one without leaves it off ({ok2})")
    # Clear + pad 6
    e.pad(5)
    for _ in range(4): e.knob(0, 1)
    p0 = pos(0)
    e.call(0x08033320, MGR, CLEAR, maxins=8_000_000); e.pad(5); e.call(0x0803381A, MGR, CLEAR, maxins=8_000_000)
    check(p0 == 2 and all(pos(k) == 0 for k in range(8)), f"Clear + pad 6: every source off (K1 was {p0}) ({[pos(k) for k in range(8)]})")
    # sample mode: code 25 (the sample number) clamped to -1..63
    for _ in range(3): e.pad(26)
    sm = e.r0(e.vl["c_vsmode"], 0)
    e.pad(5)
    for _ in range(2 * (zone[25] * MX.ZONE + MX.ZONE)): e.knob(2, 1)
    got = []
    for n in range(8):
        dw.clear(); e.call(non, 0x20011334, 2, 60 + n, 100, maxins=4_000_000); tick(12, 4)
        got += [v for v, a_ in dw if a_ == V.VB0 and (v >> 16) & 0x7F == 30]
    vals = [struct.unpack("<h", struct.pack("<H", v & 0xFFFF))[0] for v in got]
    check(sm == 1 and vals and all(-1 <= v <= 63 for v in vals) and len(set(vals)) > 1, f"sample mode ({sm}): K3 random on code 25 = the sample number in -1..63 ({sorted(set(vals))})")
    del e; gc.collect()
    split_part(img, man, check)
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


def split_part(img, man, check):
    """split4: any two note tracks, the one held first on pads 1-16"""
    from emu_sc35 import E35
    from emu_sc17_6 import PRESS, RELEASE
    import split4 as S4, srcview as SV
    gc.collect()
    e = E35(img, man)
    CT = 0x20040DB8
    gst = int(man["report"]["sc14"]["labels"]["c_gst"], 16)
    press = lambda i: e.call(0x08033320, MGR, i, maxins=8_000_000)
    release = lambda i: e.call(0x0803381A, MGR, i, maxins=8_000_000)
    pad = lambda q: e.call(PRESS, MGR, q, 100, maxins=8_000_000)
    rel = lambda q: e.call(RELEASE, MGR, q, maxins=8_000_000)
    def nv(t): e.call(0x08043A84, CT, t, 1); return e.uc.reg_read(UC_ARM_REG_R0)
    ni = {e.r32(nv(t) + 0x18): t for t in range(4)}
    fns = {}
    for o in ni:
        vt = e.r32(o)
        fns.setdefault(e.r32(vt) & ~1, "on"); fns.setdefault(e.r32(vt + 4) & ~1, "off")
    notes = []
    def hk(uc, a, s_, d):
        o = uc.reg_read(UC_ARM_REG_R0)
        if o in ni: notes.append((fns[a], ni[o], uc.reg_read(UC_ARM_REG_R1)))
    for f in fns: e.uc.hook_add(UC_HOOK_CODE, hk, begin=f, end=f)
    def window(t):
        v = nv(t); e.call(e.r32(e.r32(v) + 28) & ~1, v, maxins=900000)
        return list(struct.unpack("<16H", bytes(e.uc.mem_read(e.uc.reg_read(UC_ARM_REG_R0), 32))))
    def frame():
        e.call(0x08034196, MGR, 0x2006E000, maxins=8_000_000); return list(struct.unpack("<32H", bytes(e.uc.mem_read(0x2006E000, 64))))
    def direct(t, q):
        v = nv(t); notes.clear()
        e.call(e.r32(e.r32(v)) & ~1, v, q, 100, maxins=5_000_000); e.call(e.r32(e.r32(v) + 4) & ~1, v, q, maxins=5_000_000)
        n = [x[2] for x in notes if x[0] == "on" and x[1] == t]; notes.clear(); return n[0] if n else None
    on = lambda: e.r8(S4.SPR + S4.O_ON) if e.r32(S4.SPR) == S4.SIG else 0
    sv_split = lambda: (e.call(gst), e.r8(e.uc.reg_read(UC_ARM_REG_R0) + 20) & SV.F_SPLIT)[1]
    for a_, b_ in ((2, 0), (0, 3), (3, 1)):
        want = (direct(a_, 18), direct(b_, 20))
        press(a_); release(a_); press(9); release(9)
        press(a_); press(b_)
        st = (on(), e.r8(S4.SPR + S4.O_TOP), e.r8(S4.SPR + S4.O_BOT))
        notes.clear(); pad(2); pad(20); ons = list(notes); notes.clear(); rel(2); rel(20); offs = list(notes)
        f = frame(); w = (window(a_), window(b_))
        check(st == (1, a_, b_) and not sv_split(), f"track {a_} held + track {b_}: the split on ({st}), srcview's own not ({sv_split()})")
        check(ons == [("on", a_, want[0]), ("on", b_, want[1])] and offs == [("off", a_, want[0]), ("off", b_, want[1])],
              f"pad 3 = track {a_}'s note {want[0]}, pad 21 = track {b_}'s {want[1]} ({ons}); the releases on the track that played ({offs})")
        check(f[:16] == w[0] and f[16:] == w[1], f"the LEDs: pads 1-16 = track {a_}'s keys, 17-32 = track {b_}'s")
        release(b_); release(a_)
        press(17); release(17); still = on()
        press(a_); release(a_); single = on()
        e.call(gst); srcf = e.r8(e.uc.reg_read(UC_ARM_REG_R0) + 20)
        check(still == 1 and single == 0 and not srcf & (SV.F_SRC | SV.F_SPLIT), f"Play leaves it on ({still}); a single track button ends it ({single}), no source view, srcview's flags clear ({srcf:#x})")
    press(4); press(0); drum = on(); release(0); release(4)
    check(drum == 0, f"Drum 1 held + Synth 1: no split ({drum})")
    del e; gc.collect()


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
