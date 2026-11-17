"""Clear + Duplicate in a track view = the current pattern back as the card has it (the user, 2026-11-13: «On per-track views (note, velocity,
gate, pattern settings) clear+mutate restores current pattern to the one saved in the card. (avoid conflict with clear+mutate on pattern view,
which stops pattern mutate)»; chosen: «Ask first», «All track views»).

  * Clear held + Duplicate in any view of a track (Preset, Note, expanded Note, Velocity, Gate, Micro Step, Pattern Settings, Probability, the
    drums' chromatic view; not Sidechain) asks: Duplicate's LED (56) blinks white ~5 s; Clear + Duplicate again on the same track and pattern
    within that time = the pattern edited in that view read again from the loaded project's file (the Projects view's param 8, the loaded pack)
    and put back by the stock's own paste (0x0803D2B0 notes / 0x0803E2AA drums: the stores, the views, the engine's settings follow).
    Elsewhere (Patterns, Mixer, FX, Setup...) the press goes on as before (patmut: every pattern-mutate list ends).  Both presses swallowed.
  * What comes back: the steps, the 12 / 8 automation lanes, the pattern settings' bytes 0..7 (length, sync rate, direction, play order) and, on
    drums, bytes 8..39 (drumpat's per-step data; zeroed when the file has no 'DQ' mark: a factory pack has garbage there).  Kept: a note
    pattern's settings bytes 8..39 (project data there: fm8store, projsyn, stpair, wtui).  MIDI 1 / 2: their extra lanes' block too, by
    xlanes.use_reload() in the LED task right after.  Not restored: the arpeggiator's per-pattern settings in the record's tail.
  * Refused (Save's LED red 1.5 s): a new project never saved (the slot's file is another project's), a file shorter than the stock's 160 780 B,
    a read that fails, a save in flight or kept by the delayed save, the extra lanes busy (a load / save / reload pending).
RAM: xlanes' state (XLR, signed, zeroed at the first use): + 36 the track asked + 1, + 37 its pattern, + 38 when (u16, 256 ms), + 62 when a
refusal was shown (u16); 0x2004FAE0 (8 B): the LED head's LR and frame (the LED task's stack: nothing of ours on it while the chain runs)."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, ldrh_imm, lsls_imm, lsrs_imm,  # noqa: E402
                   mov_reg, movs_imm, movt, movw, orrs_reg, pop_list, push_list, raw, str_imm, strb_imm, strh_imm, sub_sp_imm, add_sp_imm,
                   subs_imm8, subs_reg, h, ldrb_w, strb_w)
import packio as PK  # noqa: E402
import mpatch as MP  # noqa: E402
import fxdiag as FD  # noqa: E402
import xlanes as XL  # noqa: E402
import savedefer as SDF  # noqa: E402

ID_DUP = 24
LIFE, FAILT = 20, 6                            # the question ~5 s, a refusal shown ~1.5 s (units of 256 ms)
O_T, O_P, O_AT, O_FAIL = 36, 37, 38, 62        # in XLR (free bytes there)
LRR = 0x2004FAE0                               # the LED head's LR and frame
NOBJ, NSTRIDE = 0x20039E50, 0x3A0              # the note tracks' pattern objects: [+ 0x24] p0 = the pattern edited
DOBJ, DSTRIDE = 0x2003ACD0, 0x4EC              # the drums' pattern objects: [+ 0x20] p0 = the pattern edited
PASTE_N, PASTE_D = 0x0803D2B0, 0x0803E2AA      # the stock's paste (object, source, pattern): the edited pattern = its stores told
NLEN, DLEN = 0xCA8, 0x6A8
N_SET, D_SET = 0x380, 0x80                     # the pattern settings in a note / drum pattern
DQ_AT, DQ = 0x27408, 0x5144                    # the record's tail + 996: drumpat's 'DQ' at + 998 (as a halfword at + 2)
SUB = 0x18C                                    # the tracks' container: the sub-view (7 = Sidechain)
COL_ASK, COL_NO = 0x01, 0x53
LED_DUP, LED_SAVE = 56, 57
COLW = 0x01                                    # (steady white; never an animated code)
assert O_AT % 2 == 0 and O_FAIL % 2 == 0


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def muls(rdn, rm): return h(0x4340 | rm << 3 | rdn)


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    zc = [0]
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    INV = {"eq": "ne", "ne": "eq", "hs": "lo", "lo": "hs", "cc": "cs", "cs": "cc"}
    def bc(target, cond):
        zc[0] += 1; n = f"_p{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)
    def bcs(target, cond): E(b_cond, target, cond)
    def now(rd):                                                                       # rd = (ms >> 8) & 0xFFFF (clobbers r0)
        E(bl, "c_prnow")
        if rd: E(mov_reg, rd, 0)
    def copyw(tag, n, zero=False):                                                     # r0 = dst, r1 = src (or r1 = 0 to zero), n words
        E(movs_imm, 2, n)
        a.label(f"cw_{tag}")
        if zero: E(str_imm, 1, 0, 0)
        else: E(ldr_imm, 3, 1, 0); E(str_imm, 3, 0, 0); E(adds_imm8, 1, 4)
        E(adds_imm8, 0, 4); E(subs_imm8, 2, 1); E(b_cond, f"cw_{tag}", "ne")

    # ---- c_prnow() -> r0 = (ms >> 8) & 0xFFFF
    a.label("c_prnow")
    imm32(0, PK.HAL_TICK); E(ldr_imm, 0, 0, 0); E(lsrs_imm, 0, 0, 8); E(raw, h(0xB280)); E(raw, h(0x4770))   # uxth r0, r0; bx lr

    # ---- c_probj(r0 = track) -> r0 = its pattern object (note tracks / drums); clobbers r1
    a.label("c_probj")
    E(cmp_imm, 0, 4); E(b_cond, "pj_d", "hs")
    E(movs_imm, 1, NSTRIDE >> 4); E(lsls_imm, 1, 1, 4); E(raw, muls(1, 0)); imm32(0, NOBJ); E(adds_reg, 0, 0, 1); E(raw, h(0x4770))
    a.label("pj_d")
    E(subs_imm8, 0, 4); imm32(1, DSTRIDE); E(raw, muls(1, 0)); imm32(0, DOBJ); E(adds_reg, 0, 0, 1); E(raw, h(0x4770))

    # ---- c_prbtn (the button press: ctrl, id): Clear + Duplicate in a track view = ask, then the pattern from the card
    a.label("c_prbtn")
    E(cmp_imm, 1, ID_DUP); E(b_cond, "pb_go", "eq"); E(b_w, prev["btn"])
    a.label("pb_go")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True); E(mov_reg, 4, 0)
    E(bl, L["c_pmheld"]); E(lsrs_imm, 0, 0, 1); bcs("pb_p", "cc")                         # Clear held
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); bcs("pb_p", "ne")
    E(ldr_imm, 0, 4, 0x6C); E(ldr_imm, 1, 4, 0x2C); E(cmp_reg, 0, 1); bcs("pb_p", "ne")      # the tracks' container on the screen
    E(ldrb_w, 0, 1, SUB); E(cmp_imm, 0, 7); bcs("pb_p", "eq")                          # ... not Sidechain
    E(bl, L["c_pmtp"]); E(mov_reg, 5, 0); E(cmp_imm, 5, 8); bcs("pb_p", "hs")               # r5 = the track
    E(bl, "c_probj"); E(mov_reg, 4, 0)                                                  # r4 = its pattern object (ctrl not needed now)
    E(movs_imm, 1, 0x24); E(cmp_imm, 5, 4); E(b_cond, "pb_e", "lo"); E(movs_imm, 1, 0x20)
    a.label("pb_e"); E(raw, h(0x5840))                                                   # ldr r0, [r0, r1]
    E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 6, 0, 0); E(cmp_imm, 6, 8); bcs("pb_p", "hs")   # r6 = the pattern edited
    E(bl, L["c_xlst"]); E(mov_reg, 7, 0)
    now(0)
    E(ldrb_w, 1, 7, O_T); E(mov_reg, 2, 5); E(adds_imm8, 2, 1); E(cmp_reg, 1, 2); E(b_cond, "pb_a", "ne")
    E(ldrb_w, 1, 7, O_P); E(cmp_reg, 1, 6); E(b_cond, "pb_a", "ne")
    E(ldrh_imm, 1, 7, O_AT); E(subs_reg, 1, 0, 1); E(lsls_imm, 1, 1, 16); E(lsrs_imm, 1, 1, 16); E(cmp_imm, 1, LIFE); E(b_cond, "pb_a", "hs")
    E(movs_imm, 1, 0); E(strb_w, 1, 7, O_T)                                            # confirmed
    E(bl, "c_prdo"); E(cmp_imm, 0, 0); E(b_cond, "pb_x", "eq")
    now(0); E(cmp_imm, 0, 0); E(b_cond, "pb_n", "ne"); E(movs_imm, 0, 1)                  # 0 = no refusal: use 1
    a.label("pb_n"); E(strh_imm, 0, 7, O_FAIL); E(b, "pb_x")
    a.label("pb_a")                                                                      # asked (again)
    E(strb_w, 2, 7, O_T); E(strb_w, 6, 7, O_P); E(strh_imm, 0, 7, O_AT); E(movs_imm, 1, 0); E(strh_imm, 1, 7, O_FAIL)
    a.label("pb_x"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)                        # swallowed
    a.label("pb_p"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["btn"])

    # ---- c_prdo(r4 = the pattern object, r5 = track, r6 = pattern, r7 = XLR) -> r0 = 0 done, 1 refused.  Frame r4 = sp (36 B): [0] cb 0
    # [4] ctx 0 [8] &done [12] done [16..27] the item [28] the pattern in RAM [32] the pattern object
    a.label("c_prdo")
    E(push_list, [4, 5, 6, 7], lr=True); E(sub_sp_imm, 36); E(mov_reg, 0, 4); E(mov_reg, 4, 13); E(str_imm, 0, 4, 32)
    E(ldrb_w, 0, 7, XL.O_NB); E(ldrb_imm, 1, 7, XL.O_FL); E(orrs_reg, 0, 1); E(ldrb_imm, 1, 7, XL.O_RQ); E(orrs_reg, 0, 1)
    E(cmp_imm, 0, 0); bc("do_f", "ne")                                                   # new, or the lanes busy
    imm32(0, SDF.RAM); E(ldr_imm, 1, 0, 0); imm32(2, SDF.SIG); E(cmp_reg, 1, 2); E(b_cond, "do_m", "ne")
    E(ldrb_imm, 1, 0, 4); E(cmp_imm, 1, 0); bc("do_f", "ne")                              # a save kept (delayed save; byte +4 only: +5 is never written)
    a.label("do_m")
    imm32(0, XL.SESSION_OBJ); E(ldr_imm, 0, 0, 0x64); E(movs_imm, 1, 1); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(cmp_imm, 0, 2); bc("do_f", "eq")                                                   # the manager busy (a save in flight)
    E(movs_imm, 0, 0)
    for o in range(0, 28, 4): E(str_imm, 0, 4, o)
    E(mov_reg, 0, 4); E(adds_imm8, 0, 12); E(str_imm, 0, 4, 8)                           # &done
    E(movs_imm, 0, XL.KIND_SES); E(str_imm, 0, 4, 16)
    imm32(0, XL.PROJ_OBJ + 0x20); E(ldr_imm, 0, 0, 0); E(movs_imm, 1, 8); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0); E(strb_imm, 0, 4, 20)
    E(bl, L["c_curpack"]); E(strb_imm, 0, 4, 24)
    E(mov_reg, 0, 4); E(adds_imm8, 0, 16); E(bl, PK.SIZE); imm32(1, XL.SZ0); E(cmp_reg, 0, 1); bc("do_f", "lo")
    E(movs_imm, 0, 5); E(bl, PK.BUF_LOCK)
    E(mov_reg, 0, 5); E(mov_reg, 1, 6); E(bl, L["c_pcrule"]); E(cmp_imm, 0, 0); bcs("do_u", "eq")
    E(subs_imm8, 0, 4)
    E(cmp_imm, 5, 4); E(b_cond, "do_s", "hs")
    E(movs_imm, 1, N_SET >> 4); E(lsls_imm, 1, 1, 4); E(subs_reg, 0, 0, 1); E(b, "do_t")
    a.label("do_s"); E(subs_imm8, 0, D_SET)
    a.label("do_t"); E(str_imm, 0, 4, 28)                                                  # the pattern in RAM
    imm32(1, XL.SESSION_OBJ); E(ldr_imm, 1, 1, 0x14); E(subs_reg, 1, 0, 1)                 # its offset in the file = in the record
    imm32(3, NLEN); E(cmp_imm, 5, 4); E(b_cond, "do_l", "lo"); imm32(3, DLEN)
    a.label("do_l")
    E(mov_reg, 0, 4); E(adds_imm8, 0, 16); imm32(2, PK.BUF); E(bl, PK.READ); E(cmp_imm, 0, 0); bcs("do_u", "ne")
    E(cmp_imm, 5, 4); E(b_cond, "do_dr", "hs")
    # a note pattern: its settings' bytes 8..39 stay (project data), then the paste
    imm32(2, N_SET + 8); E(ldr_imm, 1, 4, 28); E(adds_reg, 1, 1, 2); imm32(0, PK.BUF); E(adds_reg, 0, 0, 2); copyw("n", 8)
    E(ldr_imm, 0, 4, 32); imm32(1, PK.BUF); E(mov_reg, 2, 6); E(bl, PASTE_N)
    E(cmp_imm, 5, 2); E(b_cond, "do_ok", "lo")                                            # MIDI 1 / 2: their extra lanes' block too
    E(mov_reg, 0, 5); E(subs_imm8, 0, 2); E(lsls_imm, 0, 0, 3); E(adds_reg, 0, 0, 6); E(adds_imm8, 0, 1); E(strb_imm, 0, 7, XL.O_RQ)
    E(movs_imm, 0, 0); E(strb_imm, 0, 7, XL.O_TRY); E(b, "do_ok")
    a.label("do_dr")                                                                      # a drum pattern: drumpat's bytes only with 'DQ'
    E(mov_reg, 0, 4); E(adds_imm8, 0, 16); imm32(1, DQ_AT); imm32(2, PK.BUF + DLEN); E(movs_imm, 3, 4); E(bl, PK.READ); E(cmp_imm, 0, 0)
    bcs("do_u", "ne")
    imm32(0, PK.BUF + DLEN); E(ldrh_imm, 1, 0, 2); imm32(2, DQ); E(cmp_reg, 1, 2); E(b_cond, "do_q", "eq")
    imm32(0, PK.BUF + D_SET + 8); E(movs_imm, 1, 0); copyw("z", 8, zero=True)
    a.label("do_q")
    E(ldr_imm, 0, 4, 28); E(adds_imm8, 0, D_SET + 4); imm32(1, PK.BUF + D_SET + 4); copyw("d", 9)   # bytes 4..39: the paste skips them
    E(ldr_imm, 0, 4, 32); imm32(1, PK.BUF); E(mov_reg, 2, 6); E(bl, PASTE_D)
    a.label("do_ok"); E(bl, PK.BUF_UNLOCK); E(movs_imm, 0, 0); E(b, "do_x")
    a.label("do_u"); E(bl, PK.BUF_UNLOCK)
    a.label("do_f"); E(movs_imm, 0, 1)
    a.label("do_x"); E(add_sp_imm, 36); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_prled (the LED task's calls: ctrl, frame): the chain first with nothing on the stack; then the question (Duplicate blinks white)
    # and a refusal (Save red)
    a.label("c_prled")
    imm32(2, LRR); E(raw, h(0xF8C2) + h(0xE000)); E(str_imm, 1, 2, 4)                    # str.w lr, [r2]; str r1, [r2, #4]
    E(bl, prev["ledtask"])
    E(push_list, [4, 5])
    E(bl, L["c_xlst"]); E(mov_reg, 4, 0)
    imm32(0, LRR); E(ldr_imm, 5, 0, 4); E(adds_imm8, 5, 2 * LED_DUP)                    # r5 = Duplicate's LED in the frame
    now(1)
    E(ldrb_w, 0, 4, O_T); E(cmp_imm, 0, 0); E(b_cond, "pl_f", "eq")
    E(ldrh_imm, 0, 4, O_AT); E(subs_reg, 0, 1, 0); E(lsls_imm, 0, 0, 16); E(lsrs_imm, 0, 0, 16); E(cmp_imm, 0, LIFE); E(b_cond, "pl_b", "lo")
    E(movs_imm, 0, 0); E(strb_w, 0, 4, O_T); E(b, "pl_f")                                # the question expired
    a.label("pl_b")
    imm32(0, PK.HAL_TICK); E(ldr_imm, 0, 0, 0); E(lsls_imm, 0, 0, 24); E(lsrs_imm, 0, 0, 31)   # (ms >> 7) & 1
    E(movs_imm, 2, COL_ASK); E(cmp_imm, 0, 0); E(b_cond, "pl_w", "eq"); E(movs_imm, 2, 0)
    a.label("pl_w"); E(strh_imm, 2, 5, 0)
    a.label("pl_f")
    E(ldrh_imm, 0, 4, O_FAIL); E(cmp_imm, 0, 0); E(b_cond, "pl_x", "eq")
    E(subs_reg, 0, 1, 0); E(lsls_imm, 0, 0, 16); E(lsrs_imm, 0, 0, 16); E(cmp_imm, 0, FAILT); E(b_cond, "pl_c", "hs")
    E(movs_imm, 2, COL_NO); E(strh_imm, 2, 5, 2)
    E(b, "pl_x")
    a.label("pl_c"); E(movs_imm, 0, 0); E(strh_imm, 0, 4, O_FAIL)                         # the refusal shown: cleared (no return after 65536 units)
    a.label("pl_x"); E(pop_list, [4, 5])
    imm32(2, LRR); E(raw, h(0xF8D2) + h(0xF000))                                        # ldr.w pc, [r2]
    return a.assemble()


def install(img, report, base_addr):
    """Appended at the end (dspz.add moves it into the gap), after scrules' part B: the outermost heads of the button press and of the LED task."""
    import ct_fw
    from thumb import bl as bl_enc
    assert XL.RELOAD, "patrev needs xlanes.use_reload()"
    BASE = ct_fw.APP_BASE
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = dict(c_pmheld=lab("patmut", "c_pmheld"), c_shift=lab("sc15", "c_shift"), c_pmtp=lab("playmode", "c_pmtp"),
             c_pcrule=lab("patchain", "c_pcrule"), c_curpack=lab("packio", "c_curpack"), c_xlst=lab("xlanes", "c_xlst"))
    prev = dict(btn=MP.bw_target(img, MP.BTN_ENTRY, BASE), ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    assert prev["ledtask"] == int(report["scrules"]["io"]["labels"]["c_srled"], 16), prev
    code, labels = arm_code(base_addr, L, prev)
    img += code
    while len(img) % 4:
        img += bytes([0xFF])
    img[MP.BTN_ENTRY - BASE:MP.BTN_ENTRY - BASE + 4] = b_w(MP.BTN_ENTRY, labels["c_prbtn"])
    for c in PK.LED_CALLS:
        assert FD.bl_target(img, c, BASE) == prev["ledtask"], hex(c)
        img[c - BASE:c - BASE + 4] = bl_enc(c, labels["c_prled"])
    return labels, code, prev


GAP = False                                                   # SC57.8 / Beta 5.63 (use_gap)


def use_gap():
    """SC57.8 / Beta 5.63 (room for the bug hunt's fixes): patrev in dspz's first gap (dspz.add) instead of the image's end.  tabpack.use_fm2
    frees 1 152 B of raw tables in that gap and adds their 620 B of packed records to tabpack's blob at the end of the image, where only 24 B
    were free: patrev (736 B) moving the other way balances it (the end gains 116 B, the gap keeps 146 B after the fixes)."""
    global GAP
    GAP = True


def install_end(img, report):
    """At the end of the image (after scrules' part B), not in a dspz gap: the room the trims of SC57.5 free is there (use_gap: the first gap)."""
    import ct_fw
    if GAP:
        import dspz
        import patrev
        return dspz.add(img, report, "patrev", patrev)
    base = ct_fw.APP_BASE + len(img)
    labels, code, prev = install(img, report, base)
    report["patrev"] = dict(arm_start=hex(base), labels={k: hex(v) for k, v in labels.items()}, prev={k: hex(v) for k, v in prev.items()})
    return labels
