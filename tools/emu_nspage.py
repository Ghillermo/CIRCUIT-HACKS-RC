"""SC48.3 / Beta 3.40 (vcf21.use_nspage + p4dest / p4ovl use_ns): the non-sequenceable knob page of the own engine of MIDI 1 / 2 (Shift + pad 4),
through the controller and the real LED task (emu_p4dest's harness):
  * the second rows start at NS_DEF (both tracks), "NSD1";
  * MIDI 1's Preset view: Shift + pad 4 = knob page 8 (index 7), pad 4 white; pad 4 alone = page 4 again (pad 4 yellow with Shift there);
  * page 8, K1 alone moves code 5 (ATK), TUNE stays, nothing recorded (ATK is not a lane); Shift + K1: a slow knob through the matrix's list
    (DIV clicks a destination), page 4's row untouched; Shift: the knob LEDs = the destinations' page colours; the overlay (p4ovl) noted;
  * Clear held, then Shift + K1 = back to NS_DEF[0];
  * the patch: c_p4gath writes "P4" at padding + 88 and "NS", version 1, the 8 codes, the check at + 130; c_p4appl restores both (a patch without
    the NS block = NS_DEF); psave / xpatch move 142 bytes.

    python tools/emu_nspage.py SC48.3.bin SC48.3_manifest.json
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R5, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402  (its import sets vcf21's options)
import packio as PK  # noqa: E402
import mpatch as MP  # noqa: E402
import p4dest as P4  # noqa: E402
import p4ovl as PO  # noqa: E402

V = T4.V
MGR = X.MGR
CLEAR = 23
LANE_TAB = (17, 8, 15, 3, 1, 2, 11, 9)
NS_DEF = V.NS_DEF
NSRAM = 0x20045000 + 0x1B60


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = X.EP(img, man)
    R = man["report"]
    pl = {k: int(v, 16) for k, v in R["p4dest"]["labels"].items()}
    ml = {k: int(v, 16) for k, v in R["modmx"]["labels"].items()}
    nd = int(R["p4dest"]["prev"]["nd"], 16)
    dcode = bytes(e.uc.mem_read(ml["t_dcode"], nd)); dcol = bytes(e.uc.mem_read(ml["t_dcol"], nd))
    idx = {c: i for i, c in enumerate(dcode)}
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05]))
    row = lambda t=0: tuple(e.uc.mem_read(e.r0(e.vl["c_vrow"], t), 8))
    row2 = lambda t=0: tuple(e.uc.mem_read(e.r0(e.vl["c_vrow2"], t), 8))
    check(row2(0) == NS_DEF and row2(1) == NS_DEF and e.r32(NSRAM + 16) == V.NSSIG, f"the second rows start at NS_DEF ({row2(0)}, {row2(1)})")
    e.btn(2); e.btn(8)
    e.shift(True); e.pad(3); e.shift(False)
    pg = e.r0(e.vl["c_vpage"], 0); f = X.frame(e)
    check(pg == V.NS_PAGE and f[3] == V.NS_COL, f"Shift + pad 4: page {pg} (want {V.NS_PAGE}), pad 4 {f[3]:#x} (white)")
    e.pad(3); pg4 = e.r0(e.vl["c_vpage"], 0)
    e.shift(True); f4 = X.frame(e); e.shift(False)
    check(pg4 == P4.PAGE and f4[3] == V.NS_SHIFT, f"pad 4 alone: page 4 ({pg4}); with Shift pad 4 yellow ({f4[3]:#x})")
    e.shift(True); e.pad(3); e.shift(False)
    # K1 alone: ATK, not recorded
    a0, t0 = e.val(0, 5), e.val(0, 17)
    e.gates.clear(); e.knob(0, 3)
    a1, t1 = e.val(0, 5), e.val(0, 17)
    check(a1 != a0 and t1 == t0 and not e.gates, f"page 8, K1 moves ATK ({a0} -> {a1}), TUNE stays ({t0} -> {t1}), nothing recorded ({e.gates})")
    # Shift + K1: the destination
    p4row = row()
    e.shift(True)
    for _ in range(P4.DIV - 1): e.knob(0, 1)
    r1 = row2()[0]
    e.knob(0, 1); r2 = row2()[0]
    f = X.frame(e)
    exp = [(129 << 8) | dcol[idx[c]] for c in row2()]
    noted = (e.r8(PO.OVR), e.r8(PO.OVR + 1))
    e.shift(False)
    check(r1 == 5 and r2 == dcode[idx[5] + 1] and row() == p4row, f"Shift + K1: {P4.DIV - 1} clicks nothing ({r1}), {P4.DIV} = the next ({r2}); "
                                                                f"page 4's row untouched")
    check(f[60:68] == exp, f"Shift: the LEDs = the destinations' page colours ({[hex(x) for x in f[60:68]]})")
    check(noted == (0x00, PO.MARK), f"the overlay noted the knob (track 0, K1: {noted})")
    nc = row2()[0]
    v0 = e.val(0, nc); e.knob(0, 2)
    check(e.val(0, nc) != v0, f"K1 then moves code {nc} ({v0} -> {e.val(0, nc)})")
    # Clear, then Shift + K1: the default
    e.call(0x08033320, MGR, CLEAR, maxins=8_000_000); e.shift(True); e.knob(0, 1); e.shift(False); e.call(0x0803381A, MGR, CLEAR, maxins=8_000_000)
    check(row2()[0] == NS_DEF[0] and row2(1) == NS_DEF, f"Clear, then Shift + K1: back to {NS_DEF[0]} ({row2()[0]}); MIDI 2 untouched ({row2(1)})")
    # the patch
    e.shift(True)
    for _ in range(P4.DIV * 2): e.knob(4, 1)
    for _ in range(P4.DIV): e.knob(7, -1)
    e.shift(False)
    saved, saved4 = row2(), row()
    e.call(pl["c_p4gath"], 0, maxins=8_000_000)
    b4 = bytes(e.uc.mem_read(PK.BUF + P4.POFS, P4.PLEN)); bn = bytes(e.uc.mem_read(PK.BUF + P4.POFS2, P4.PLEN))
    sm = (0x5A + sum(bn[:11])) & 0xFF
    check(b4[:3] == b"P4\x01" and tuple(b4[3:11]) == saved4 and bn[:3] == b"NS\x01" and tuple(bn[3:11]) == saved and bn[11] == sm,
          f"gather: + 88 {b4.hex()}, + 130 {bn.hex()}")
    blocks = {MP.OFF + 64: bytes(24), MP.OFF + P4.POFS: b4, MP.OFF + P4.POFS2: bn}
    def rd(uc, a, s, d):
        n, off = uc.reg_read(UC_ARM_REG_R3), uc.reg_read(UC_ARM_REG_R1) & 511
        uc.mem_write(uc.reg_read(UC_ARM_REG_R2), blocks.get(off, bytes(n))[:n]); uc.reg_write(UC_ARM_REG_R0, 0); uc.reg_write(UC_ARM_REG_R1, n)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    mpr = int(R["mpatch"]["labels"]["c_mpr"], 16)
    hk = e.uc.hook_add(UC_HOOK_CODE, rd, begin=mpr, end=mpr)
    e.call(0x08033320, MGR, CLEAR, maxins=8_000_000); e.shift(True); e.knob(4, 1); e.shift(False); e.call(0x0803381A, MGR, CLEAR, maxins=8_000_000)
    mid = row2()
    e.uc.reg_write(UC_ARM_REG_R5, 11); e.call(pl["c_p4appl"], 0, maxins=8_000_000)
    ok1 = row2() == saved and mid != saved and row() == saved4
    blocks[MP.OFF + P4.POFS2] = bytes(12)
    e.uc.reg_write(UC_ARM_REG_R5, 11); e.call(pl["c_p4appl"], 0, maxins=8_000_000)
    ok2 = row2() == NS_DEF and row() == saved4
    e.uc.hook_del(hk)
    check(ok1 and ok2, f"apply: both blocks restored ({ok1}); without the NS block: NS_DEF, page 4's kept ({ok2})")
    ps, xp = R["psave"]["listing"], R["xpatch"]["listing"]
    check(any("#0x8e" in l for l in ps) and any("#0x8e" in l for l in xp), "psave / xpatch: 142 bytes of padding (movs #0x8e in their listings)")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} NSPAGE RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
