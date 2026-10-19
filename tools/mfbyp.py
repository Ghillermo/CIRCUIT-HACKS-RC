"""SC44.5 (the user, 2026-10-19: «add shift25 on FX view: master filter disable/enable»): in the FX view, Shift + pad 25 switches the master filter
off and on again.

  * off: its position (project parameter 0x21 idx 0, read by the getter 0x08036192) is kept in our RAM and the filter goes to the centre (64 =
    no filter, as fxkeys' reset), through the stock listener 0x08034D92: the DSP's own smoothing takes it there, no click;
  * on: the position comes back;
  * the filter knob moved while it is off (or a project with another position loaded): the filter is simply on again from there (the state
    clears when the parameter is not 64 any more; nothing waits hidden);
  * LEDs (the LED task chain, after the stock frame): while off, the filter knob's LED (68) red in every view (the indicator of the mode); in the
    FX view with Shift, pad 25 yellow (available, the Shift convention) or red (off).  Without Shift pad 25 is the stock's "FX off".
How: the head of slot 0 of the FX view's class (s14.FX_VT: SC17's c_f_press / SC14's c_fxpress behind it): pad index 24 with Shift and the FX view
on the screen ([ctrl + 0x6C] = [ctrl + 0x44]) is ours, the rest goes on; the LED task calls.  State: MFB (our RAM after split4's, see
modmx.MXR): "MFB1" while off + the kept position; no signature = on (the RAM holds the power-up pattern)."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, mov_reg, movs_imm, movt, movw,  # noqa: E402
                   pop_list, push_list, str_imm, strb_imm, strh_imm, strh_reg, raw)
import fxkeys as K  # noqa: E402
import fxdiag as FD  # noqa: E402
import packio as PK  # noqa: E402
import build_sc14 as S14  # noqa: E402
import modmx as MX  # noqa: E402

MFB = MX.MXR + 0xE0                   # 0x200450E0: [0] "MFB1" while off, [4] the kept position
SIG = 0x3142464D
PAD, LED_FILT = 24, 68                # pad 25; the filter knob's LED in the frame
CENTRE, RED, YELLOW = 64, 0x53, 0x2D
MGR = 0x20040B10
# SC44.6 (use_hold; the user, 2026-10-19: «cuando se desactiva el filtro con s25, mantener desactivado aunque se mueva. Recuperar posición actual
# del filtro al togglear s25 otra vez»): the project parameter is never touched; while off, the two places that read it for the DSP's X:$CF (the
# stock master group 0x08028F40, SC14's Auto-Filter restore) read the centre instead; the knob, MIDI or a project still move the parameter (and
# its LED shows it), so switching on again gives the filter's current position; each toggle resends the group with the stock MARK_DIRTY (from
# the pad press, the UI task: not the DSP service tick).
HOLD = False
GROUP_GET = 0x08028F46                # bl GETTER(0x21, 0) of the stock master group
MARK_DIRTY = 0x0803BDCC


def use_hold():
    global HOLD
    HOLD = True


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)

    # ---- c_mfon() -> r0 = 1 while the filter is off; clobbers r1
    a.label("c_mfon")
    imm32(0, MFB); E(ldr_imm, 0, 0, 0); imm32(1, SIG); E(cmp_reg, 0, 1); E(b_cond, "mo_1", "eq")    # (movs sets the flags: after the branch)
    E(movs_imm, 0, 0); E(raw, h(0x4770))
    a.label("mo_1"); E(movs_imm, 0, 1); E(raw, h(0x4770))

    # ---- c_mfset(r0 = the position): the master filter there, through the stock listener; clobbers r0-r3
    a.label("c_mfset")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    imm32(0, K.CTX); E(ldr_imm, 0, 0, 0); E(ldr_imm, 0, 0, 0x10); E(ldr_imm, 0, 0, 0)
    E(adds_imm8, 0, 4); E(movs_imm, 1, 0x21); E(movs_imm, 2, 0); E(mov_reg, 3, 4); E(bl, K.PARAM_SET)
    E(pop_list, [4], pc=True)

    # ---- c_mftog(): off -> on (the kept position back), on -> off (kept, the centre); clobbers r0-r3
    a.label("c_mftog")
    if HOLD:
        E(push_list, [4], lr=True)
        E(bl, "c_mfon"); imm32(4, MFB); imm32(1, SIG); E(cmp_imm, 0, 0); E(b_cond, "mt_set", "eq"); E(movs_imm, 1, 0)
        a.label("mt_set"); E(str_imm, 1, 4, 0)
        E(movs_imm, 0, 0x21); E(movs_imm, 1, 0); E(bl, MARK_DIRTY); E(pop_list, [4], pc=True)
        # ---- c_mfget (instead of the two bl GETTER(0x21, 0) for X:$CF): the position, or the centre while off
        a.label("c_mfget")
        E(push_list, [4], lr=True); E(bl, K.GETTER); E(mov_reg, 4, 0); E(bl, "c_mfon"); E(cmp_imm, 0, 0); E(mov_reg, 0, 4)
        E(b_cond, "mg_x", "eq"); E(movs_imm, 0, CENTRE)
        a.label("mg_x"); E(pop_list, [4], pc=True)
    else:
     E(push_list, [4], lr=True)
     E(bl, "c_mfon"); E(cmp_imm, 0, 0); E(b_cond, "mt_off", "eq")
     imm32(4, MFB); E(ldrb_imm, 0, 4, 4); E(movs_imm, 1, 0); E(str_imm, 1, 4, 0)       # on again
     E(bl, "c_mfset"); E(pop_list, [4], pc=True)
     a.label("mt_off")
     E(movs_imm, 0, 0x21); E(movs_imm, 1, 0); E(bl, K.GETTER)                           # r0 = the position
     imm32(4, MFB); E(strb_imm, 0, 4, 4); imm32(1, SIG); E(str_imm, 1, 4, 0)
     E(movs_imm, 0, CENTRE); E(bl, "c_mfset"); E(pop_list, [4], pc=True)

    # ---- c_mfpress (slot 0 of the FX view's class: view, pad, velocity): Shift + pad 25 with the FX view on the screen
    a.label("c_mfpress")
    E(push_list, [0, 1, 2, 3, 4], lr=True)
    E(cmp_imm, 1, PAD); E(b_cond, "mp_prev", "ne")
    imm32(4, MGR); E(ldr_imm, 0, 4, K.CTRL_VIEW); E(ldr_imm, 1, 4, K.CTRL_FX); E(cmp_reg, 0, 1); E(b_cond, "mp_prev", "ne")
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "mp_prev", "eq")
    E(bl, "c_mftog")
    E(pop_list, [0, 1, 2, 3, 4], pc=True)
    a.label("mp_prev"); E(raw, popw([0, 1, 2, 3, 4], lr=True)); E(b_w, prev["press"])

    # ---- c_mfledtask (the LED task calls: ctrl, frame): the chain, then our LEDs
    a.label("c_mfledtask")
    E(push_list, [4, 5, 6], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(bl, prev["ledtask"])
    E(bl, "c_mfon"); E(mov_reg, 6, 0); E(cmp_imm, 6, 0); E(b_cond, "ml_fx", "eq")
    if not HOLD:
        E(movs_imm, 0, 0x21); E(movs_imm, 1, 0); E(bl, K.GETTER); E(cmp_imm, 0, CENTRE); E(b_cond, "ml_red", "eq")
        imm32(0, MFB); E(movs_imm, 1, 0); E(str_imm, 1, 0, 0); E(movs_imm, 6, 0); E(b, "ml_fx")   # the knob moved: on again
    a.label("ml_red")
    E(movw, 0, (100 + 2) << 8 | RED); E(movw, 1, 2 * LED_FILT); E(strh_reg, 0, 5, 1)
    a.label("ml_fx")                                                                    # the FX view with Shift: pad 25
    E(ldr_imm, 0, 4, K.CTRL_VIEW); E(cmp_imm, 0, 0); E(b_cond, "ml_x", "eq")
    E(ldr_imm, 1, 4, K.CTRL_FX); E(cmp_reg, 0, 1); E(b_cond, "ml_x", "ne")
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "ml_x", "eq")
    E(movs_imm, 0, YELLOW); E(cmp_imm, 6, 0); E(b_cond, "ml_p", "eq"); E(movs_imm, 0, RED)
    a.label("ml_p"); E(strh_imm, 0, 5, 2 * PAD)
    a.label("ml_x"); E(pop_list, [4, 5, 6], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the head of the FX view's slot 0, the LED task calls."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    L = dict(c_shift=int(report["sc15"]["labels"]["c_shift"], 16))
    prev = dict(press=u(S14.FX_VT) & ~1, ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    assert MFB + 8 <= 0x2004FE00 - 0x1000
    struct.pack_into("<I", img, S14.FX_VT - BASE, labels["c_mfpress"] | 1)
    if HOLD:
        sites = [GROUP_GET]
        o = int(report["sc14"]["labels"]["gt_f_off"], 16)
        sites += [x for x in range(o, o + 24, 2) if bytes(img[x - BASE:x - BASE + 4]) == bl(x, K.GETTER)][:1]
        assert len(sites) == 2, sites
        for x in sites:
            assert bytes(img[x - BASE:x - BASE + 4]) == bl(x, K.GETTER), hex(x)
            img[x - BASE:x - BASE + 4] = bl(x, labels["c_mfget"])
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_mfledtask"])
    return labels, code, prev
