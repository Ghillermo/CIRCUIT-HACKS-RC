"""S715D3 (diagnostic, 2026-11-20): who puts a play position >= 32 in a track's playing store?

S715D2's DWT watch caught the 5.63 / 5.64 corruption on the device (scene stress run, seed 1, 1 756 s): the writer of 0x20043610 is the stock
0x0804E736 (strh at 0x0804E750: a drum view's per-step flags halfword [this + 0x6C + 2 step] |= / &= bit), called by the listener 0x0804EB70 of
the playing store (Drum 4's view object 0x200433C4, [this + 0x18] = the engine's playing store of track 7, 0x200391F0) with the store's p1 (the
step) = 240: 0x200433C4 + 0x6C + 2 x 240 = 0x20043610.  The store was committed by the stock advance (0x0802C90C -> 0x0802CB3C -> the commit at
0x0802CA02); the advance writes the step only at 0x0802CE46 / 0x0802CE4A (strb r5), from a masked step (& 31) on every path but the pattern
change, which takes the new pattern's first / last step straight from its settings (0x0803C6D6 of [sp + 1], the pattern our c_pcnext / c_pmnext
chose at 0x0802CD4A).  All 64 patterns' settings read sane afterwards: the 240 is transient (an out-of-range pattern number, or a hook's step).

  * c_stc in place of the advance's bl 0x080354FA at 0x0802CE46 (the step's write copy; r5 = the step about to be written): r5 >= 32 = a capture
    (tag 4) with the advance's frame live ([sp] track, [sp + 1] the new pattern, [sp + 2] the chain's last, [sp + 4] the settings halfword,
    [sp + 8] the store, the stacked args: scene change, scene), then r5 &= 31 and on (the corruption does not happen).
  * c_stl in place of the listener's bl 0x0804E736 at 0x0804EB8E: an index >= 32 from any other writer = a capture (tag 5) and no call.
  * c_stcap(r0 tag, r1 value, r2 the hooked caller's SP): only when no record is frozen; the black box frozen (state 0x85, as patscan), then
    STK1 = tag, value, the caller's r4..r11, 344 B of the caller's stack; STK2 (176 B) = the loaded record's tail + 64 (patchain's running state,
    64 B), the ITCM 0x0E00 (scrules' current chains, 32 B), patmut's RAM (32 B), the engine 0x20038EC0 + 0xC0 (48 B: + 0xC4 + 4 t, the pending
    first / last of each track).
Code in dspz's first gap."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import Asm, adds_imm8, b_cond, b_w, bl, cmp_imm, h, ldr_imm, ldrb_imm, lsls_imm, lsrs_imm, mov_reg, movs_imm, movt, movw, pop_list, push_list, raw, str_imm  # noqa: E402

ADV_SITE, PARAM_WPTR = 0x0802CE46, 0x080354FA
LST_SITE, FLAGS_SET = 0x0804EB8E, 0x0804E736
PATMUT_RAM, SESSION_OBJ, TAIL, ITCM_SC, ENGINE = 0x200472C0, 0x2003D71C, 0x27024, 0x00000E00, 0x20038EC0
STATE = 0x85
TAG_ADV, TAG_LST = 4, 5


def arm_code(base, L, bb):
    a = Asm(base)
    E = a.emit
    def imm32(r, v): E(movw, r, v & 0xFFFF); E(movt, r, (v >> 16) & 0xFFFF)
    def cpy(dst, src_setup, n):                                       # c_bbcpy(r0 dst, r1 src, r2 n): checked reads, clobbers r0-r3
        imm32(0, dst); src_setup(); E(movw, 2, n); E(bl, L["c_bbcpy"])

    # ---- c_stc (the advance: r0 = the playing store, r1 = 1, r5 = the step)
    a.label("c_stc")
    E(cmp_imm, 5, 32); E(b_cond, "tc_go", "lo")
    E(push_list, [0, 1], lr=True)
    E(movs_imm, 0, TAG_ADV); E(mov_reg, 1, 5); E(raw, h(0xAA03))                  # add r2, sp, #12: the advance's SP
    E(bl, "c_stcap")
    E(lsls_imm, 5, 5, 27); E(lsrs_imm, 5, 5, 27)
    E(pop_list, [0, 1, 2]); E(mov_reg, 14, 2)
    a.label("tc_go"); E(b_w, PARAM_WPTR)

    # ---- c_stl (the listener 0x0804EB70: r0 = the view, r1 = the step, r2 = the bit, r3 = set)
    a.label("c_stl")
    E(cmp_imm, 1, 32); E(b_cond, "tl_go", "lo")
    E(raw, h(0xB500))                                                             # push {lr}
    E(movs_imm, 0, TAG_LST); E(raw, h(0xAA01))                                   # add r2, sp, #4
    E(bl, "c_stcap")
    E(raw, h(0xBD00))                                                             # pop {pc}
    a.label("tl_go"); E(b_w, FLAGS_SET)

    # ---- c_stcap(r0 tag, r1 value, r2 the caller's SP)
    a.label("c_stcap")
    E(push_list, [4, 5, 6, 7], lr=True)                                          # [sp] .. [sp + 12] = the caller's r4..r7
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2)
    imm32(0, bb.BB); E(ldrb_imm, 1, 0, bb.O.ST); E(lsls_imm, 1, 1, 31); E(b_cond, "cp_x", "mi")
    E(movs_imm, 0, STATE); E(bl, L["c_bbfrz"])
    imm32(7, bb.BB + bb.O.STK1)
    E(str_imm, 4, 7, 0); E(str_imm, 5, 7, 4)
    for i in range(4):
        E(raw, h(0x9800 | i)); E(str_imm, 0, 7, 8 + 4 * i)                       # ldr r0, [sp, #4 i]
    for i, r in enumerate((8, 9, 10, 11)):
        E(mov_reg, 0, r); E(str_imm, 0, 7, 24 + 4 * i)
    cpy(bb.BB + bb.O.STK1 + 40, lambda: E(mov_reg, 1, 6), bb.N_STK1 - 40)
    S2 = bb.BB + bb.O.STK2
    imm32(1, SESSION_OBJ); E(ldr_imm, 1, 1, 0x14); E(cmp_imm, 1, 0); E(b_cond, "cp_t", "eq")
    imm32(0, TAIL + 64); E(raw, h(0x1809))                                        # adds r1, r1, r0
    a.label("cp_t")
    imm32(0, S2); E(movw, 2, 64); E(bl, L["c_bbcpy"])                        # (a null record: c_bbcpy writes zeros)
    imm32(0, S2 + 64); imm32(1, ITCM_SC); E(movs_imm, 2, 8)                     # the ITCM: a plain word loop (c_bbcpy checks RAM ranges)
    a.label("cp_i"); E(ldr_imm, 3, 1, 0); E(str_imm, 3, 0, 0); E(adds_imm8, 0, 4); E(adds_imm8, 1, 4); E(raw, h(0x3A01)); E(b_cond, "cp_i", "ne")   # subs r2, #1
    cpy(S2 + 96, lambda: imm32(1, PATMUT_RAM), 32)
    cpy(S2 + 128, lambda: imm32(1, ENGINE + 0xC0), bb.N_STK2 - 128)
    a.label("cp_x")
    E(pop_list, [4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """Appended at the end (dspz.add moves it into the gap)."""
    import ct_fw
    import blackbox as bb
    from fxdiag import bl_target
    BASE = ct_fw.APP_BASE
    assert bl_target(img, ADV_SITE, BASE) == PARAM_WPTR and bl_target(img, LST_SITE, BASE) == FLAGS_SET
    assert bb.N_STK1 == 384 and bb.N_STK2 == 176
    L = {k: int(report["blackbox"]["labels"][k], 16) for k in ("c_bbcpy", "c_bbfrz")}
    code, labels = arm_code(base_addr, L, bb)
    img += code
    while len(img) % 4:
        img += bytes([0xFF])
    img[ADV_SITE - BASE:ADV_SITE - BASE + 4] = bl(ADV_SITE, labels["c_stc"])
    img[LST_SITE - BASE:LST_SITE - BASE + 4] = bl(LST_SITE, labels["c_stl"])
    report["stepcatch"] = dict(arm_start=hex(base_addr), labels={k: hex(v) for k, v in labels.items()})
    return labels, code, {}


def decode(raw_rec, bb):
    """The capture in a record (bbread): None when STK1 holds no stepcatch tag."""
    s1, s2 = raw_rec[bb.O.STK1:bb.O.STK1 + 384], raw_rec[bb.O.STK2:bb.O.STK2 + 176]
    tag, val = struct.unpack_from("<2I", s1)
    if tag not in (TAG_ADV, TAG_LST):
        return None
    regs = struct.unpack_from("<8I", s1, 8)
    stk = s1[40:]
    out = dict(where="advance 0x0802CE46" if tag == TAG_ADV else "listener 0x0804EB8E", value=val,
               r4_r11=[hex(x) for x in regs], stack=stk.hex())
    if tag == TAG_ADV:
        out.update(track=stk[0], new_pattern=stk[1], chain_last=stk[2], settings_last=stk[4], settings_first=stk[5],
                   store=hex(struct.unpack_from("<I", stk, 8)[0]), r8_first=hex(regs[4]), sb=hex(regs[5]),
                   scene_change=stk[0x44], scene=struct.unpack_from("<I", stk, 0x48)[0])
    out.update(tail64=s2[:64].hex(), itcm_e00=s2[64:96].hex(), patmut=s2[96:128].hex(), engine_c0=s2[128:].hex())
    return out
