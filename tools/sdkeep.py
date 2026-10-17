"""SC43.7 (the user, 2026-10-17: «en sinte 1 y 2 step-drummer … volver a pulsar synth1 desactiva la vista step-drummer. Comportamiento deseado: al
volver a la vista de synth1, se muestra el step-drummer»): the step-drummer of Synth 1 / 2 comes back with its synth.

The stock / the mod: the step-drummer view of a synth lives inside its source view (srcview: the Preset view with F_SRC, bit 2 of c_gst() + 20),
open while vcf21's F_SDOPEN (O_FLAGS bit 4) is set; vcf21's c_vbtn clears F_SDOPEN on every Synth button, so pressing the synth again (its track
view, or from elsewhere) never showed it again.

Ours: the record's tail + 177 = 0xC0 | the synth whose step-drummer view was on the screen last (1 / 2, 0 none) | a pending return << 2:
  * the LED task (after the chain): while F_SDOPEN is set and a synth's step-drummer view is on the screen (vcf21's c_sdscr = 2 / 3), that synth is
    kept; F_SDOPEN clear (closed with its pad 30) = none;
  * the button chain's head: Synth s pressed while F_SDOPEN is set and s is the kept synth = a pending return (the chain then runs as always);
  * the LED task, with a return pending: the synth's track view on the screen ([ctrl + 0x152] = 9 s + 1) = a tap on Preset, then F_SRC and
    F_SDOPEN; its Preset view (9 s) = F_SRC and F_SDOPEN; anything else = nothing.  Any other value of the byte = none.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, ldrb_w, lsls_imm, lsrs_imm,  # noqa: E402
                   mov_reg, movs_imm, movt, movw, orrs_reg, pop_list, push_list, raw, strb_imm, ands_reg, subs_imm8)
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402
import mpatch as MP  # noqa: E402
import srcview as SV  # noqa: E402
import build_sc15 as S15  # noqa: E402

MGR, S_CUR = 0x20040B10, 0x152
SESSION_OBJ, TAIL, O_K, TAG = 0x2003D71C, 0x27024, 177, 0xC0
F_SDOPEN = 0x10                                                    # vcf21's O_FLAGS bit 4


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    RET = h(0x4770)

    # ---- c_skb() -> r0 = the byte's address, or 0; clobbers r1
    a.label("c_skb")
    imm32(0, SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); E(cmp_imm, 0, 0); E(b_cond, "kb_x", "eq")
    imm32(1, TAIL + O_K); E(adds_reg, 0, 0, 1)
    a.label("kb_x"); E(raw, RET)

    # ---- c_skv(r0 = the address) -> r0 = the byte's 4 low bits (0 when the tag is not ours); clobbers r1
    a.label("c_skv")
    E(ldrb_imm, 1, 0, 0); E(lsrs_imm, 0, 1, 4); E(cmp_imm, 0, TAG >> 4); E(b_cond, "kv_0", "ne")
    E(movs_imm, 0, 15); E(ands_reg, 0, 1); E(raw, RET)
    a.label("kv_0"); E(movs_imm, 0, 0); E(raw, RET)

    # ---- c_skbtn (the button chain's head: ctrl, id): Synth s with its step-drummer kept = a pending return; then the chain
    a.label("c_skbtn")
    E(cmp_imm, 1, 1); E(b_cond, "kt_f", "hi")
    E(push_list, [0, 1, 4, 5], lr=True); E(mov_reg, 5, 1)
    E(movs_imm, 0, F_SDOPEN); E(bl, L["c_sdflag"]); E(cmp_imm, 0, 0); E(b_cond, "kt_p", "eq")
    E(bl, "c_skb"); E(cmp_imm, 0, 0); E(b_cond, "kt_p", "eq"); E(mov_reg, 4, 0)
    E(bl, "c_skv"); E(movs_imm, 1, 3); E(ands_reg, 1, 0); E(subs_imm8, 1, 1); E(cmp_reg, 1, 5); E(b_cond, "kt_p", "ne")
    E(lsls_imm, 1, 5, 2); E(adds_imm8, 1, 4); E(orrs_reg, 0, 1); E(movs_imm, 1, TAG); E(orrs_reg, 0, 1); E(strb_imm, 0, 4, 0)   # pending = s + 1
    a.label("kt_p"); E(raw, popw([0, 1, 4, 5], lr=True))
    a.label("kt_f"); E(b_w, prev["btn"])

    # ---- c_skled (the LED task calls: ctrl, frame): the chain; then the pending return, or the synth to keep
    a.label("c_skled")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(bl, prev["ledtask"])
    E(bl, "c_skb"); E(cmp_imm, 0, 0); E(b_cond, "kl_x", "eq"); E(mov_reg, 4, 0)
    E(bl, "c_skv"); E(mov_reg, 5, 0)                                                # r5 = the low bits
    E(lsrs_imm, 6, 5, 2); E(cmp_imm, 6, 0); E(b_cond, "kl_keep", "eq")
    E(subs_imm8, 6, 1)                                                              # r6 = the synth to bring back
    imm32(0, MGR); E(ldrb_w, 7, 0, S_CUR); E(lsls_imm, 1, 6, 3); E(adds_reg, 1, 1, 6)   # r1 = 9 s
    E(cmp_reg, 7, 1); E(b_cond, "kl_pr", "eq"); E(adds_imm8, 1, 1); E(cmp_reg, 7, 1); E(b_cond, "kl_clr", "ne")
    imm32(0, MGR); E(movs_imm, 1, SV.ID_PRESET); E(bl, SV.BTN)                       # its track view: a tap on Preset
    imm32(0, MGR); E(movs_imm, 1, SV.ID_PRESET); E(bl, SV.BTN_REL)
    a.label("kl_pr")                                                                # its Preset view: the source view with the step-drummer
    E(bl, L["c_gst"]); E(cmp_imm, 0, 0); E(b_cond, "kl_clr", "eq")
    E(adds_imm8, 0, S15.S_PAINT); E(movs_imm, 1, SV.F_SRC); E(movs_imm, 2, 0); E(bl, L["c_rmw"])
    E(movs_imm, 0, F_SDOPEN); E(movs_imm, 1, 1); E(bl, L["c_sdfset"])
    a.label("kl_clr"); E(movs_imm, 0, 3); E(ands_reg, 5, 0); E(movs_imm, 0, TAG); E(orrs_reg, 0, 5); E(strb_imm, 0, 4, 0); E(b, "kl_x")   # the pending return done
    a.label("kl_keep")                                                              # no return pending: the synth whose step-drummer is on the screen
    E(movs_imm, 0, F_SDOPEN); E(bl, L["c_sdflag"]); E(movs_imm, 5, 0); E(cmp_imm, 0, 0); E(b_cond, "kl_w", "eq")
    E(movs_imm, 0, 3); E(ands_reg, 5, 0)
    E(bl, L["c_sdscr"]); E(cmp_imm, 0, 2); E(b_cond, "kl_w0", "lo"); E(cmp_imm, 0, 3); E(b_cond, "kl_w0", "hi")
    E(subs_imm8, 0, 1); E(mov_reg, 5, 0)
    a.label("kl_w0")
    E(bl, "c_skb"); E(mov_reg, 4, 0); E(bl, "c_skv"); E(cmp_imm, 5, 0); E(b_cond, "kl_w", "ne"); E(movs_imm, 1, 3); E(ands_reg, 0, 1); E(mov_reg, 5, 0)   # (none on the screen: kept)
    a.label("kl_w"); E(movs_imm, 0, TAG); E(orrs_reg, 0, 5); E(strb_imm, 0, 4, 0)
    a.label("kl_x"); E(pop_list, [3, 4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the head of the button chain, the LED task calls."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    lv = report["vcf20"]["labels"]
    L = dict(c_sdflag=int(lv["c_sdflag"], 16), c_sdfset=int(lv["c_sdfset"], 16), c_sdscr=int(lv["c_sdscr"], 16),
             c_gst=int(report["sc14"]["labels"]["c_gst"], 16), c_rmw=int(report["srcview"]["labels"]["c_rmw"], 16))
    prev = dict(btn=MP.bw_target(img, MP.BTN_ENTRY, BASE), ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    img[MP.BTN_ENTRY - BASE:MP.BTN_ENTRY - BASE + 4] = b_w(MP.BTN_ENTRY, labels["c_skbtn"])
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_skled"])
    return labels, code, prev
