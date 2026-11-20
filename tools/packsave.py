"""Alpha 7.12 (the user, 2026-11-20: «how do we feel about saving the current pack to a new slot with save->target pad, just like stock Rhythm» ->
«2 and 3 are alright. do it»: the new pack is loaded afterwards, empty slots only): in the packs view (Shift + Projects), **Save, then an empty
pack pad** = the loaded pack duplicated there and the loaded project saved into the copy with its unsaved changes, then the new pack loaded (the
same project number).  The original pack is not touched.  A pad that holds a pack, the loaded one, the internal pack (pad 1) or the transport
running = nothing done, Save red 1.5 s.  While Save is armed in the packs view the empty pads light yellow (the Shift = yellow convention); while
the steps run Save is steady white and the packs view's pads are swallowed.

The stock (emulation + disassembly):
  * Save (button 25) arms a «save» state, the store [Projects view 0x20044324 + 0x2C] p0 = 1, that stays after the release (a Projects pad then
    saves there; Projects, Save again or a save ends it);
  * the packs view's Duplicate + an empty pad (0x08044006): 0x0803C68C([view + 0x20], pad, 0, 0), the target blinking ([view + 0x24], timer 9 of
    500 ms, 0x080440A1); the request reaches the pack manager (0x08030D8C): the copy itself (0x0803CD42) runs at once in the caller's thread, then
    0x08030EDC rescans the new pack and sets its colour in [view + 0x14] (0x2000FEC0, 0xFF = empty) when it is done;
  * one store 0x200111CC = [session manager 0x2003D71C + 0x60] = [packs view + 0x10] = [Projects view + 0x20]: p0 the loaded pack, p8 the loaded
    project; the project save 0x0802FDF8(manager, project, flag) posts the session with pack = its p0 read at that moment (flag = the byte at
    [Projects view + 0x30], as the Projects view's own «save in another slot»); [manager + 0x64] p1 = 2 while a save is in flight;
  * loading a pack: [packs view + 0x18] p0 = pack, commit; loading a project: 0x0803C68C([Projects view + 0xC], project | 0x40 when
    [Projects view + 0x1C] p0 = 0, 0, 0).
Ours:
  * c_pspad, the packs view's slot 0 in front of what was there: the checks, the stock's duplicate request and blink, then the state (step 1);
  * c_psled, the LED task's head (in front of what was there, nothing on the stack while it runs, issue #22): step 1 = the new pack's colour set
    (its rescan done) -> the save with p0 of 0x200111CC's read copy = the new pack for the length of the call (the stock save, and every hook of
    ours inside it that reads the loaded pack, write into the copy), then p0 back; step 2 = the save done -> the new pack loaded; step 3 = it is
    loaded -> the project number loaded again if the pack opened another; each step gives up after 30 s (Save red).  Then the LEDs.
  * the black box (Alpha 7.12, the user: «add to next», a false violet Save during a pack delete): a copy or a delete of a pack holds the panel's main
    loop for seconds and blackbox v2 took it for a lock-up (1.5 s) until the loop ran again; c_pspad and c_psmb (the held-buttons object's slot 2,
    in front of packio's c_mbp: the delete) put the black box's heartbeat to 0 first, which its stall check skips until the loop runs again.
RAM: 0x2004FBC0 (16 B: + 0 "PSV1", + 4 the step, + 5 the new pack, + 6 the old one, + 7 the project, + 8 the step's start, + 12 the red's start)
and 0x2004FBD0 (+ 0 the LED task's LR, + 4 its frame).  In the dspz gap.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, lsls_imm, mov_reg, movs_imm, movt, movw, pop_list,  # noqa: E402
                   push_list, raw, str_imm, strb_imm, strh_imm, subs_reg, adds_imm8, adds_reg)
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402

RAM, RAM2 = 0x2004FBC0, 0x2004FBD0
SIG = struct.unpack("<I", b"PSV1")[0]
O_ST, O_B, O_A, O_P, O_T, O_TF = 4, 5, 6, 7, 8, 12
PV, PJ, G, MGR = 0x20044128, 0x20044324, 0x2003D71C, 0x20040B10
GET, WPTR, COMMIT, SINK, TIMER, BLINK_CB = 0x0803542C, 0x080354FA, 0x080353C0, 0x0803C68C, 0x0803C432, 0x080440A1
SAVE_FN, TRANSPORT, HAL_TICK = 0x0802FDF8, 0x20011034, 0x2000081C
LED_SAVE, WHITE, RED, YELLOW = 57, PK.CLR_ON, 0x53, 0x2D
STEP_MS, RED_MS = 30000, 1500
BBONLY = False                                   # (Alpha 7.13, use_bbonly) the save feature discarded (the user: «we need the room»): only the black box fix
BB_NOW = None                                    # the black box's heartbeat (set by install when the build has the black box)


def use_bbonly():
    """Alpha 7.13 (the user, 2026-11-20: «Discard the new save feature, we need the room»): only the black box's fix is kept: a pad of the packs
    view (Duplicate + pad copies a pack in the caller's thread) and Clear of the held-buttons object (a delete) put the heartbeat to 0 first."""
    global BBONLY
    BBONLY = True


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def now(rd): imm32(rd, HAL_TICK); E(ldr_imm, rd, rd, 0)
    def get(st_reg, k):                          # r0 = the byte k of the store in st_reg (clobbers r0-r3)
        E(mov_reg, 0, st_reg); E(movs_imm, 1, k); E(bl, GET); E(ldrb_imm, 0, 0, 0)
    def bbzero():                                # the black box's heartbeat = 0: its stall check skips until the main loop runs again
        if BB_NOW is not None:
            imm32(0, BB_NOW); E(movs_imm, 1, 0); E(str_imm, 1, 0, 0)

    if BBONLY:                                   # ---- c_psmb / c_pspad: the heartbeat 0, then what was there (args kept)
        for lab, k in (("c_psmb", "mb"), ("c_pspad", "pad")):
            a.label(lab)
            if BB_NOW is not None:
                E(push_list, [0, 1, 2], lr=True); imm32(0, BB_NOW); E(movs_imm, 1, 0); E(str_imm, 1, 0, 0); E(raw, popw([0, 1, 2], lr=True))
            E(b_w, prev[k])
        return a.assemble()

    # ---- c_psram: r6 = RAM, cleared when its signature is not there (the RAM is not cleared at power-up)
    a.label("c_psram")
    imm32(6, RAM); E(ldr_imm, 0, 6, 0); imm32(1, SIG); E(cmp_reg, 0, 1); E(b_cond, "pr_x", "eq")
    E(str_imm, 1, 6, 0); E(movs_imm, 0, 0); E(str_imm, 0, 6, 4); E(str_imm, 0, 6, 8); E(str_imm, 0, 6, 12)
    a.label("pr_x"); E(raw, h(0x4770))

    # ---- c_psmb (held-buttons slot 2: obj, id): the heartbeat 0 when Clear is pressed (a delete may follow), then what was there
    a.label("c_psmb")
    if BB_NOW is not None:
        E(cmp_imm, 1, 23); E(b_cond, "pm_x", "ne")
        imm32(2, BB_NOW); E(movs_imm, 3, 0); E(str_imm, 3, 2, 0)
    a.label("pm_x"); E(b_w, prev["mb"])

    # ---- c_pspad (packs view slot 0: view, pad, vel)
    a.label("c_pspad")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    bbzero()
    E(bl, "c_psram")
    E(ldrb_imm, 0, 6, O_ST); E(cmp_imm, 0, 0); E(b_cond, "pp_eat", "ne")              # the steps running: every pad swallowed
    imm32(7, PJ); E(ldr_imm, 7, 7, 0x2C); get(7, 0); E(cmp_imm, 0, 0); E(b_cond, "pp_stk", "eq")   # Save not armed: as before
    E(ldr_imm, 0, 4, 0xC); E(movs_imm, 1, 0); E(bl, GET); E(ldrb_imm, 0, 0, 0); E(lsls_imm, 0, 0, 31); E(b_cond, "pp_stk", "pl")  # not ready
    E(mov_reg, 0, 7); E(movs_imm, 1, 0); E(bl, WPTR); E(movs_imm, 1, 0); E(strb_imm, 1, 0, 0); E(mov_reg, 0, 7); E(bl, COMMIT)  # Save disarmed
    E(cmp_imm, 5, 0); E(b_cond, "pp_red", "eq"); E(cmp_imm, 5, 32); E(b_cond, "pp_red", "hs")                 # the internal pack / not a pack
    imm32(0, TRANSPORT); E(movs_imm, 1, 0); E(bl, GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "pp_red", "ne")
    E(ldr_imm, 7, 4, 0x10); get(7, 0); E(strb_imm, 0, 6, O_A); E(cmp_reg, 0, 5); E(b_cond, "pp_red", "eq")   # the loaded pack
    get(7, 8); E(strb_imm, 0, 6, O_P)                                                                        # the loaded project
    E(ldr_imm, 0, 4, 0x14); E(mov_reg, 1, 5); E(bl, GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0xFF); E(b_cond, "pp_red", "ne")   # not empty
    E(ldr_imm, 0, 4, 0x20); E(mov_reg, 1, 5); E(movs_imm, 2, 0); E(movs_imm, 3, 0); E(bl, SINK)               # the stock's duplicate (the copy)
    E(strb_imm, 5, 6, O_B)
    E(raw, h(0xF884) + h(0x5024))                                                                           # strb.w r5, [r4, #0x24]: the blink
    E(movs_imm, 0, 9); E(movs_imm, 1, 0); E(movw, 2, 500); imm32(3, BLINK_CB); E(bl, TIMER)                 # ([sp] = the view, pushed r0)
    now(0); E(str_imm, 0, 6, O_T); E(movs_imm, 0, 1); E(strb_imm, 0, 6, O_ST)
    E(b, "pp_eat")
    a.label("pp_red"); now(0); E(str_imm, 0, 6, O_TF)
    a.label("pp_eat"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("pp_stk"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["pad"])

    # ---- c_psled (the LED task's calls: ctrl, frame)
    a.label("c_psled")
    imm32(2, RAM2); E(raw, h(0xF8C2) + h(0xE000)); E(str_imm, 1, 2, 4)                               # str.w lr, [r2]; str r1, [r2, #4]
    E(bl, prev["led"])
    E(push_list, [4, 5, 6, 7])
    E(bl, "c_psram")
    E(ldrb_imm, 5, 6, O_ST); E(cmp_imm, 5, 0); E(b_cond, "pl_led", "eq")
    now(0); E(ldr_imm, 1, 6, O_T); E(subs_reg, 0, 0, 1); imm32(1, STEP_MS); E(cmp_reg, 0, 1); E(b_cond, "pl_fail", "hs")
    imm32(7, G); E(ldr_imm, 7, 7, 0x64); get(7, 1); E(cmp_imm, 0, 2); E(b_cond, "pl_led", "eq")           # a save in flight: wait
    E(cmp_imm, 5, 1); E(b_cond, "pl_s2", "ne")
    # step 1: the new pack's colour set (its rescan done) -> the save into it
    imm32(7, PV); E(ldr_imm, 0, 7, 0x14); E(ldrb_imm, 1, 6, O_B); E(bl, GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0xFF); E(b_cond, "pl_led", "eq")
    E(ldr_imm, 0, 7, 0x10); E(movs_imm, 1, 0); E(bl, GET); E(ldrb_imm, 1, 6, O_B); E(strb_imm, 1, 0, 0)    # p0 (read copy) = the new pack
    imm32(0, PJ); E(ldr_imm, 0, 0, 0x30); E(ldrb_imm, 2, 0, 0); E(ldrb_imm, 1, 6, O_P); imm32(0, G); E(bl, SAVE_FN)
    imm32(7, PV); E(ldr_imm, 0, 7, 0x10); E(movs_imm, 1, 0); E(bl, GET); E(ldrb_imm, 1, 6, O_A); E(strb_imm, 1, 0, 0)    # p0 back
    E(movs_imm, 5, 2); E(b, "pl_next")
    a.label("pl_s2"); E(cmp_imm, 5, 2); E(b_cond, "pl_s3", "ne")
    # step 2: the save done -> the new pack loaded
    imm32(7, PV); E(ldr_imm, 7, 7, 0x18); E(mov_reg, 0, 7); E(movs_imm, 1, 0); E(bl, WPTR); E(ldrb_imm, 1, 6, O_B); E(strb_imm, 1, 0, 0)
    E(mov_reg, 0, 7); E(bl, COMMIT)
    E(movs_imm, 5, 3); E(b, "pl_next")
    # step 3: the new pack loaded -> its project the one that was saved
    a.label("pl_s3")
    imm32(7, PV); E(ldr_imm, 7, 7, 0x10); get(7, 0); E(ldrb_imm, 1, 6, O_B); E(cmp_reg, 0, 1); E(b_cond, "pl_led", "ne")
    get(7, 8); E(ldrb_imm, 5, 6, O_P); E(cmp_reg, 0, 5); E(b_cond, "pl_done", "eq")
    imm32(7, PJ); E(ldr_imm, 0, 7, 0x1C); E(movs_imm, 1, 0); E(bl, GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "pl_p", "ne")
    E(adds_imm8, 5, 0x40)
    a.label("pl_p"); E(ldr_imm, 0, 7, 0xC); E(mov_reg, 1, 5); E(movs_imm, 2, 0); E(movs_imm, 3, 0); E(bl, SINK)
    a.label("pl_done"); E(movs_imm, 5, 0); E(strb_imm, 5, 6, O_ST); E(b, "pl_led")
    a.label("pl_next"); E(strb_imm, 5, 6, O_ST); now(0); E(str_imm, 0, 6, O_T); E(b, "pl_led")
    a.label("pl_fail"); E(movs_imm, 0, 0); E(strb_imm, 0, 6, O_ST); now(0); E(str_imm, 0, 6, O_TF)
    # the LEDs: Save white while the steps run, red 1.5 s after a refusal; Save armed in the packs view: the empty pads yellow
    a.label("pl_led")
    imm32(4, RAM2); E(ldr_imm, 4, 4, 4)                                                                     # r4 = the frame
    E(ldrb_imm, 0, 6, O_ST); E(cmp_imm, 0, 0); E(b_cond, "pl_r", "eq")
    E(movs_imm, 0, WHITE); E(b, "pl_put")
    a.label("pl_r"); now(0); E(ldr_imm, 1, 6, O_TF); E(cmp_imm, 1, 0); E(b_cond, "pl_y", "eq"); E(subs_reg, 0, 0, 1); E(movw, 1, RED_MS); E(cmp_reg, 0, 1); E(b_cond, "pl_y", "hs")   # (TF 0 = never refused)
    E(movs_imm, 0, RED)
    a.label("pl_put"); E(movs_imm, 1, 2 * LED_SAVE); E(raw, h(0x5260))                                     # strh r0, [r4, r1]
    a.label("pl_y")
    imm32(0, MGR); E(ldr_imm, 0, 0, 0x6C); imm32(1, PV); E(cmp_reg, 0, 1); E(b_cond, "pl_x", "ne")
    E(ldrb_imm, 0, 6, O_ST); E(cmp_imm, 0, 0); E(b_cond, "pl_x", "ne")
    imm32(7, PJ); E(ldr_imm, 7, 7, 0x2C); get(7, 0); E(cmp_imm, 0, 0); E(b_cond, "pl_x", "eq")
    imm32(7, PV); E(ldr_imm, 7, 7, 0x14); E(movs_imm, 5, 1)
    a.label("pl_yl")
    E(mov_reg, 0, 7); E(mov_reg, 1, 5); E(bl, GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0xFF); E(b_cond, "pl_yn", "ne")
    E(lsls_imm, 1, 5, 1); E(movs_imm, 0, YELLOW); E(raw, h(0x5260))                                       # strh r0, [r4, r1]
    a.label("pl_yn"); E(adds_imm8, 5, 1); E(cmp_imm, 5, 32); E(b_cond, "pl_yl", "lo")
    a.label("pl_x")
    E(pop_list, [4, 5, 6, 7])
    imm32(2, RAM2); E(ldr_imm, 2, 2, 0); E(raw, h(0x4710))                                                 # bx r2
    return a.assemble()


def install(img, report, base_addr):
    import ct_fw
    global BB_NOW
    BASE = ct_fw.APP_BASE
    bl_enc = lambda at, to: bl(at, to)
    u = lambda ad: struct.unpack_from("<I", img, ad - BASE)[0]
    if "blackbox" in report:
        import blackbox as BX
        BB_NOW = BX.BB + BX.O.NOW
    prev = dict(pad=u(PK.PV_VT) & ~1, mb=u(PK.MB_VT + 8) & ~1, led=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    assert FD.bl_target(img, PK.LED_CALLS[1], BASE) == prev["led"]
    code, labels = arm_code(base_addr, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    struct.pack_into("<I", img, PK.PV_VT - BASE, labels["c_pspad"] | 1)
    struct.pack_into("<I", img, PK.MB_VT + 8 - BASE, labels["c_psmb"] | 1)
    if not BBONLY:
        for c in PK.LED_CALLS:
            img[c - BASE:c - BASE + 4] = bl_enc(c, labels["c_psled"])
    return labels, code, prev
