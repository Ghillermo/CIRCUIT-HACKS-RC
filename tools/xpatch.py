"""SC40.7 (the user, 2026-10-14: «patches entre packs, mismo lenguaje de atajos que samples y sinte»): the own-synth patches of MIDI 1 / 2
(tools/mpatch.py: 64 slots per pack, in the padding of the pack's synth patch records) copied from one pack to another on the device.

Use, as with the samples and the synth patches (tools/packio.py): in the Preset view of MIDI 1 / 2, Duplicate + slot A (it blinks: tools/psave.py)
remembers that patch; load another pack; Duplicate + slot B there = A's patch (its 44 bytes and its name, 64 bytes of the padding) is written into
B.  Within one pack Duplicate + A + B still exchanges the two (psave).  With a patch of another pack remembered and the slots on the screen, the
Duplicate button is yellow: Duplicate + pad pastes.  A stays remembered (several slots can take it) until another A is chosen.

How: a hook in front of psave's pad handler.  After psave marks an A, the clip word X:PCLIPW of the DSP (the one of the synth patches' copy; it
survives releasing Duplicate, other views and loading a pack) gets 0xA7 << 16 | pack << 8 | slot.  Duplicate + a slot pad with a clip of another
pack: 64 bytes read from A's bank of that pack (the stock's content API with the pack by number, in the shared buffer under its lock), the storage
task put back on the loaded pack (packio.c_resel), and written into B's record by mpatch's writer when A holds a patch ("CTM1") and B's record
is in its bank.  It writes to the SD card: not for the "S" builds.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, add_sp_imm, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldr_sp, ldrb_imm, lsls_imm, lsrs_imm,  # noqa: E402
                   mov_reg, movs_imm, movt, movw, orrs_reg, pop_list, push_list, raw, h, str_imm, strb_imm, strh_reg, sub_sp_imm, subs_imm8)
import packio as PK  # noqa: E402
import mpatch as MP  # noqa: E402
import psave as PS  # noqa: E402
import sampler_dsp as SD  # noqa: E402

XMAGIC = 0xA7                         # the clip of an own-synth patch (packio's: 0xA5 a sample, 0xA6 a synth patch)
XLEN = PS.XLEN
MGR = PS.MGR
LED_DUP, COL_WAIT = 56, 0x2D
INV = dict(eq="ne", ne="eq", lo="hs", hs="lo", hi="ls", ls="hi")


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    zc = [0]
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def bc(target, cond):
        zc[0] += 1; n = f"_x{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)
    def pad_ofs(rd, rs):                                                              # rd = 512 x (slot % 8) + 340; clobbers r3
        E(lsls_imm, rd, rs, 29); E(lsrs_imm, rd, rd, 20); imm32(3, MP.OFF); E(adds_reg, rd, rd, 3)

    # ---- c_xqclip() -> r0 = the clip of an own-synth patch (XMAGIC << 16 | pack << 8 | slot), 0 = none; clobbers r1-r3
    a.label("c_xqclip")
    E(push_list, [4], lr=True); E(sub_sp_imm, 8)
    E(mov_reg, 0, 13); E(bl, L["c_take"]); imm32(0, SD.PCLIPW); E(bl, L["c_xr"]); E(mov_reg, 4, 0)
    E(mov_reg, 0, 13); E(bl, L["c_give"])
    E(lsrs_imm, 0, 4, 16); E(cmp_imm, 0, XMAGIC); E(b_cond, "qc_ok", "eq"); E(movs_imm, 4, 0)
    a.label("qc_ok"); E(mov_reg, 0, 4); E(add_sp_imm, 8); E(pop_list, [4], pc=True)

    # ---- c_xqcopy (r0 = the pack of A, r1 = slot A, r2 = slot B of the loaded pack): A's own-synth patch written into B
    a.label("c_xqcopy")
    E(push_list, [4, 5, 6, 7], lr=True); E(sub_sp_imm, 36)
    E(mov_reg, 4, 1); E(mov_reg, 5, 2); E(mov_reg, 6, 0)
    E(movs_imm, 0, 5); E(bl, PK.BUF_LOCK)
    E(mov_reg, 7, 13)
    E(movs_imm, 0, PK.KIND_PATCH); E(str_imm, 0, 7, 16); E(lsrs_imm, 0, 4, 3); E(str_imm, 0, 7, 20); E(str_imm, 6, 7, 24)
    E(movs_imm, 0, 0); E(str_imm, 0, 7, 0); E(str_imm, 0, 7, 4); E(str_imm, 0, 7, 12)
    E(mov_reg, 0, 7); E(adds_imm8, 0, 12); E(str_imm, 0, 7, 8)
    pad_ofs(1, 4); E(mov_reg, 0, 7); E(adds_imm8, 0, 16); imm32(2, PK.BUF); E(movs_imm, 3, XLEN); E(bl, PK.READ)
    E(mov_reg, 4, 0)                                                                  # r4 = the status of the read
    E(bl, L["c_curpack"]); E(bl, L["c_resel"])                                         # the storage task back on the loaded pack
    E(cmp_imm, 4, 0); bc("qx_u", "ne"); E(ldr_imm, 0, 7, 12); E(cmp_imm, 0, XLEN); bc("qx_u", "ne")
    imm32(0, PK.BUF); E(ldr_imm, 0, 0, 0); imm32(1, MP.MAGIC4); E(cmp_reg, 0, 1); bc("qx_u", "ne")     # A holds no patch
    E(lsrs_imm, 0, 5, 3); E(bl, L["c_mpsz"]); E(mov_reg, 6, 0)
    pad_ofs(1, 5); E(cmp_reg, 6, 1); bc("qx_u", "lo")                                 # B's record is not in its bank
    E(lsrs_imm, 0, 5, 3); imm32(2, PK.BUF); E(movs_imm, 3, XLEN); E(bl, L["c_mpw"])
    E(bl, L["c_mpc"]); E(cmp_imm, 0, 0); E(b_cond, "qx_u", "eq"); E(movs_imm, 1, 0xFF); E(strb_imm, 1, 0, 7)     # the slots' bits read again
    a.label("qx_u"); E(bl, PK.BUF_UNLOCK)
    E(add_sp_imm, 36); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_xqpad (the template view's slot 0: view, pad, velocity), in front of psave's: Duplicate + a slot with a patch of another pack
    #      remembered = it is written there; else psave's, and what it marks as A becomes the clip
    a.label("c_xqpad")
    E(cmp_imm, 1, 8); bc("xq_f", "lo"); E(cmp_imm, 1, 23); bc("xq_f", "hi")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1)
    E(bl, L["c_mpon"]); E(cmp_imm, 0, 0xFF); bc("xq_c", "eq")
    imm32(0, MGR); E(ldr_imm, 0, 0, 0x20); E(ldr_imm, 0, 0, 0xC); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 6, 0, 0)
    E(movs_imm, 0, 3); E(ands_reg, 6, 0); E(cmp_imm, 6, 2); bc("xq_c", "ne")           # Duplicate alone
    E(bl, L["c_mpc"]); E(cmp_imm, 0, 0); bc("xq_c", "eq")
    E(ldrb_imm, 0, 0, 3); E(lsls_imm, 0, 0, 4); E(subs_imm8, 5, 8); E(adds_reg, 5, 5, 0)            # r5 = the slot
    E(bl, "c_xqclip"); E(mov_reg, 7, 0); E(cmp_imm, 7, 0); E(b_cond, "xq_m", "eq")
    E(bl, L["c_curpack"]); E(lsrs_imm, 1, 7, 8); E(lsls_imm, 1, 1, 24); E(lsrs_imm, 1, 1, 24); E(cmp_reg, 1, 0); E(b_cond, "xq_m", "eq")
    E(mov_reg, 0, 1); E(lsls_imm, 1, 7, 24); E(lsrs_imm, 1, 1, 24); E(mov_reg, 2, 5); E(bl, "c_xqcopy")
    E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("xq_m")                                                                   # this pack: psave's; its A is the clip from now on
    E(ldr_sp, 0, 0); E(ldr_sp, 1, 4); E(ldr_sp, 2, 8); E(bl, prev["xpad"])
    E(bl, L["c_psst"]); E(cmp_imm, 0, 0); E(b_cond, "xq_e", "eq")
    E(ldrb_imm, 1, 0, 2); E(cmp_imm, 1, PS.K_DUP); E(b_cond, "xq_e", "ne")
    E(ldrb_imm, 1, 0, 1); E(cmp_imm, 1, 0x80); E(b_cond, "xq_e", "lo")
    E(movs_imm, 2, 0x7F); E(ands_reg, 1, 2); E(ldrb_imm, 2, 0, 3); E(lsls_imm, 2, 2, 8); E(orrs_reg, 1, 2)
    E(movs_imm, 2, XMAGIC); E(lsls_imm, 2, 2, 16); E(orrs_reg, 1, 2); E(mov_reg, 0, 1); E(bl, L["c_psetclip"])
    a.label("xq_e"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("xq_c"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True))
    a.label("xq_f"); E(b_w, prev["xpad"])

    # ---- c_xqledtask (the LED task calls: ctrl, frame): the chain; the own-synth slots on the screen and a patch of another pack remembered:
    #      the Duplicate button yellow
    a.label("c_xqledtask")
    E(push_list, [3, 4, 5], lr=True)
    E(mov_reg, 5, 1); E(bl, prev["ledtask"])
    E(bl, L["c_mpon"]); E(cmp_imm, 0, 0xFF); E(b_cond, "ql_x", "eq")
    E(bl, "c_xqclip"); E(mov_reg, 4, 0); E(cmp_imm, 4, 0); E(b_cond, "ql_x", "eq")
    E(bl, L["c_curpack"]); E(lsrs_imm, 1, 4, 8); E(lsls_imm, 1, 1, 24); E(lsrs_imm, 1, 1, 24); E(cmp_reg, 1, 0); E(b_cond, "ql_x", "eq")
    E(movs_imm, 0, 2 * LED_DUP); E(movs_imm, 1, COL_WAIT); E(strh_reg, 1, 5, 0)
    a.label("ql_x"); E(pop_list, [3, 4, 5], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the template view's pad slot (in front of psave's), the two LED task calls."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a: struct.unpack_from("<I", img, a - BASE)[0]
    lab = lambda sec, n: int(report[sec]["labels"][n], 16)
    L = {n: lab("packio", n) for n in ("c_take", "c_give", "c_xr", "c_curpack", "c_resel", "c_psetclip")}
    L.update({n: lab("mpatch", n) for n in ("c_mpc", "c_mpon", "c_mpsz", "c_mpw")}); L["c_psst"] = lab("psave", "c_psst")
    prev = dict(xpad=u(MP.TMPL_VT) & ~1, ledtask=lab("patchain", "c_pcledtask"))
    assert prev["xpad"] == lab("psave", "c_psxpad"), hex(prev["xpad"])
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    struct.pack_into("<I", img, MP.TMPL_VT - BASE, labels["c_xqpad"] | 1)
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_xqledtask"])
    return labels, code, prev
