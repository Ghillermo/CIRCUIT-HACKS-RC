"""SC46 (the user, 2026-10-21: «Cuando un proyecto se guarda, debería conservar su parche inicial» = «The MIDI 1 / 2 own synth: each project should
save its sound and bring it back when loaded (today it is global)»): the own synth of MIDI 1 / 2 saved with the project and brought back by its load.

The own engine keeps its state in the global settings (vcf21, since SC20): a project load leaves the sound of the one before.  A project now carries
both tracks' patches in the own-synth patch format of mpatch (the padding image its save writes: CTM1 + codes + the matrix + page 4 + FM, the first
124 bytes, psave.XLEN), in bytes 8..39 of the settings of MIDI 1 / 2's patterns 0..4 (the stock reads bytes 0..3; patchain / playmode 4..7; free on
note tracks in every session of the copy but 02_Shadow Child's, which holds garbage there: hence the signature, the index and the sum): each 32-byte
block = 0xC6, track << 4 | block, 30 bytes of the 124 + a 16-bit sum (5 blocks, 150 bytes).  Pattern t of track MIDI 1 / 2 = record + 0x1A27C +
0xCA8 (8 t + p), its settings + 0x380.
  * mpatch's IO is redirected while VS (this module's flag) = 1 + track: mp_io (the shared read / write of c_mpr / c_mpw) copies between the shared
    buffer and IMG[track] (offset - 340 - 512 x 7: slot 0xFF), c_mpsz returns 64 KB (no record is created): mpatch's own save (c_mpsave(t, 0xFF):
    its gather and every wrapped one, modmx, p4dest, fmeng) and load (c_mpload(t, 0xFF): its apply and theirs) run untouched on RAM; the slot
    cache's "last" / "read again" bytes (c_mpc + 6 / 7) are kept around the calls (the slots' LEDs do not change);
  * the LED task (a call in front of the chain at packio.LED_CALLS): every 256 ms, both tracks' state gathered into IMG (the shared buffer's lock is
    taken there, as mpatch's refresh does); after a project load (the end of the stock's apply, P19.LOAD_END: a flag), once, the project's blocks
    read and applied (a project without them: nothing, the sound stays), then gathered again; not before 3 s after power-up (vcf21 / engsave first);
  * the save (the bl at P19.SAVE_CALL, in front of the others): IMG written into the 10 blocks of the RAM record, then the stock's save; nothing
    when IMG was not gathered since the last load (the blocks loaded stay).  No lock there: the save may run with the shared buffer taken.
RAM: modmx.MXR + 0x300 (16 B: VS, pending, valid, the time, a signature: without it every reader takes them as 0) + 0x310 / 0x3C0 (IMG, 176 B each).  In the hole (no card: mpatch's IO goes to RAM).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, ldrb_reg, lsls_imm, lsrs_imm, mov_reg,  # noqa: E402
                   movs_imm, movt, movw, muls, pop_list, push_list, raw, str_imm, strb_imm, strb_reg, subs_imm8, subs_reg)
import packio as PK  # noqa: E402
import mpatch as MP  # noqa: E402
import modmx as MX  # noqa: E402
import persist19 as P19  # noqa: E402
import fxdiag as FD  # noqa: E402
import vcf21 as V  # noqa: E402

STR = MX.MXR + 0x300                  # + 0 VS (0 / 1 + track), + 1 pending (a load to apply), + 2 valid (IMG gathered since the load), + 4 the time
O_VS, O_PEND, O_VALID, O_T, O_SIG = 0, 1, 2, 4, 8
STSIG = 0x314E5359                   # "YSN1": the RAM is not cleared at power-up
IMG0, IMG_SZ = MX.MXR + 0x310, 0xB0   # IMG[t] = IMG0 + 0xB0 t (the padding's first 176 bytes)
NB, BLEN = 124, 30                    # bytes kept (psave.XLEN), data bytes a block
NBLK = 5                              # 5 x 30 = 150 >= 124 + the sum
SIG = 0xC6
SESSION_OBJ = 0x2003D71C
AREA, PSIZE, SET, BYTE0 = 0x1A27C, 0xCA8, 0x380, 8    # MIDI 1's pattern 0 in the record; a note pattern; its settings; our first byte
SLOT = 0xFF                           # the virtual slot: bank 31, record 7
REL = MP.OFF + 512 * (SLOT & 7)       # an mp_io offset - REL = the offset in IMG
EVERY, BOOT_MS = 256, 3000
INV = V.INV
MPIO_OLD, MPSZ_OLD = bytes.fromhex("88b06f46"), bytes.fromhex("30b584b0")   # sub sp, #32; mov r7, sp / push {r4, r5, lr}; sub sp, #16


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def bl_enc(at, target): return bl(at, target)


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    zc = [0]
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def now(rd): imm32(rd, V.HAL_TICK); E(ldr_imm, rd, rd, 0)
    def bc(target, cond):
        zc[0] += 1; n = f"_y{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)
    def img(rd, rt):                                                                 # rd = IMG0 + 0xB0 x rt
        E(movs_imm, rd, IMG_SZ); E(muls, rd, rt); imm32(3, IMG0); E(adds_reg, rd, rd, 3)

    # ---- c_ysio (mp_io's head: r4 = the read / write, r0 bank, r1 offset, r2 buffer, r3 length; c_mpr / c_mpw pushed r4-r7, lr)
    a.label("c_ysio")
    imm32(5, STR); E(ldr_imm, 6, 5, O_SIG); imm32(7, STSIG); E(cmp_reg, 6, 7); E(b_cond, "yi_old", "ne")
    E(ldrb_imm, 5, 5, O_VS); E(cmp_imm, 5, 0); E(b_cond, "yi_go", "ne")
    a.label("yi_old")
    E(raw, MPIO_OLD); E(b_w, L["mp_io"] + 4)
    a.label("yi_go")
    E(subs_imm8, 5, 1); E(movs_imm, 6, IMG_SZ); E(muls, 6, 5); imm32(5, IMG0); E(adds_reg, 6, 6, 5)   # r6 = IMG[t]
    imm32(5, REL); E(subs_reg, 1, 1, 5); E(adds_reg, 6, 6, 1)                       # r6 = IMG[t] + the offset in the padding
    E(movs_imm, 1, 0)
    imm32(5, PK.WRITE | 1); E(cmp_reg, 4, 5); E(b_cond, "yi_r", "ne")
    a.label("yi_w"); E(cmp_reg, 1, 3); E(b_cond, "yi_x", "hs"); E(ldrb_reg, 0, 2, 1); E(strb_reg, 0, 6, 1); E(adds_imm8, 1, 1); E(b, "yi_w")
    a.label("yi_r"); E(cmp_reg, 1, 3); E(b_cond, "yi_x", "hs"); E(ldrb_reg, 0, 6, 1); E(strb_reg, 0, 2, 1); E(adds_imm8, 1, 1); E(b, "yi_r")
    a.label("yi_x"); E(movs_imm, 0, 0); E(pop_list, [4, 5, 6, 7], pc=True)          # r0 = 0 (done), r1 = the length

    # ---- c_yssz (c_mpsz's head: r0 = bank) -> the bank's size; 64 KB for the virtual slot
    a.label("c_yssz")
    imm32(1, STR); E(ldr_imm, 2, 1, O_SIG); imm32(3, STSIG); E(cmp_reg, 2, 3); E(b_cond, "yz_old", "ne")
    E(ldrb_imm, 1, 1, O_VS); E(cmp_imm, 1, 0); E(b_cond, "yz_v", "ne")
    a.label("yz_old")
    E(raw, MPSZ_OLD); E(b_w, L["c_mpsz"] + 4)
    a.label("yz_v"); E(movs_imm, 0, 1); E(lsls_imm, 0, 0, 16); E(raw, h(0x4770))

    # ---- c_ysst() -> r0 = STR, set up (zeros + the signature) at the first use; clobbers r1, r2
    a.label("c_ysst")
    imm32(0, STR); E(ldr_imm, 1, 0, O_SIG); imm32(2, STSIG); E(cmp_reg, 1, 2); E(b_cond, "yt_x", "eq")
    E(movs_imm, 1, 0); E(str_imm, 1, 0, 0); E(str_imm, 1, 0, O_T); E(str_imm, 2, 0, O_SIG)
    a.label("yt_x"); E(raw, h(0x4770))

    # ---- c_ysrun(r0 = track, r1 = 0 gather / 1 apply): mpatch's save / load of the virtual slot, the slot cache's bytes 6 / 7 kept
    a.label("c_ysrun")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, L["c_mpc"]); E(mov_reg, 7, 0); E(movs_imm, 6, 0)
    E(cmp_imm, 7, 0); E(b_cond, "yr_n", "eq"); E(ldrb_imm, 6, 7, 6); E(ldrb_imm, 0, 7, 7); E(lsls_imm, 0, 0, 8); E(raw, h(0x4306))   # orrs r6, r0
    a.label("yr_n")
    imm32(0, STR); E(mov_reg, 1, 4); E(adds_imm8, 1, 1); E(strb_imm, 1, 0, O_VS)
    E(mov_reg, 0, 4); E(movs_imm, 1, SLOT)
    E(cmp_imm, 5, 0); E(b_cond, "yr_a", "ne"); E(bl, L["c_mpsave"]); E(b, "yr_d")
    a.label("yr_a"); E(bl, L["c_mpload"])
    a.label("yr_d")
    imm32(0, STR); E(movs_imm, 1, 0); E(strb_imm, 1, 0, O_VS)
    E(cmp_imm, 7, 0); E(b_cond, "yr_x", "eq"); E(strb_imm, 6, 7, 6); E(lsrs_imm, 6, 6, 8); E(strb_imm, 6, 7, 7)
    a.label("yr_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_ysblk(r0 = track, r1 = block) -> r0 = the 32 bytes in the RAM record (0: no record); clobbers r1-r3
    a.label("c_ysblk")
    imm32(2, SESSION_OBJ); E(ldr_imm, 2, 2, 0x14); E(cmp_imm, 2, 0); E(b_cond, "yb_0", "eq")
    E(lsls_imm, 0, 0, 3); E(adds_reg, 0, 0, 1); imm32(1, PSIZE); E(muls, 0, 1)
    imm32(1, AREA + SET + BYTE0); E(adds_reg, 0, 0, 1); E(adds_reg, 0, 0, 2); E(raw, h(0x4770))
    a.label("yb_0"); E(movs_imm, 0, 0); E(raw, h(0x4770))

    # ---- c_yssum(r0 = IMG[t]) -> r0 = 0x5AC6 + the 124 bytes, 16 bits; clobbers r1, r2
    a.label("c_yssum")
    E(movs_imm, 1, 0); imm32(2, 0x5AC6)
    a.label("ys_l"); E(raw, h(0x5C43)); E(adds_reg, 2, 2, 3); E(adds_imm8, 1, 1); E(cmp_imm, 1, NB); E(b_cond, "ys_l", "lo")   # ldrb r3, [r0, r1]
    E(lsls_imm, 0, 2, 16); E(lsrs_imm, 0, 0, 16); E(raw, h(0x4770))

    # ---- c_ysput(r0 = track): IMG[t] (+ its sum) into the record's 5 blocks
    a.label("c_ysput")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0)
    img(5, 4)
    E(mov_reg, 0, 5); E(bl, "c_yssum"); E(movs_imm, 1, NB); E(strb_reg, 0, 5, 1); E(lsrs_imm, 0, 0, 8); E(adds_imm8, 1, 1); E(strb_reg, 0, 5, 1)
    E(movs_imm, 6, 0)                                                                 # r6 = the block
    a.label("yp_b")
    E(mov_reg, 0, 4); E(mov_reg, 1, 6); E(bl, "c_ysblk"); E(cmp_imm, 0, 0); E(b_cond, "yp_x", "eq"); E(mov_reg, 7, 0)
    E(movs_imm, 0, SIG); E(strb_imm, 0, 7, 0); E(lsls_imm, 0, 4, 4); E(raw, h(0x4330)); E(strb_imm, 0, 7, 1)   # orrs r0, r6
    E(movs_imm, 0, BLEN); E(muls, 0, 6); E(adds_reg, 0, 0, 5); E(movs_imm, 1, 0)       # r0 = IMG + 30 k
    a.label("yp_c"); E(ldrb_reg, 2, 0, 1); E(adds_imm8, 1, 2); E(strb_reg, 2, 7, 1); E(subs_imm8, 1, 1); E(cmp_imm, 1, BLEN); E(b_cond, "yp_c", "lo")
    E(adds_imm8, 6, 1); E(cmp_imm, 6, NBLK); E(b_cond, "yp_b", "lo")
    a.label("yp_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_ysget(r0 = track) -> r0 = 1 when the record's 5 blocks hold a patch (then in IMG[t]), else 0
    a.label("c_ysget")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0)
    img(5, 4); E(movs_imm, 6, 0)
    a.label("yg_b")
    E(mov_reg, 0, 4); E(mov_reg, 1, 6); E(bl, "c_ysblk"); E(cmp_imm, 0, 0); E(b_cond, "yg_0", "eq"); E(mov_reg, 7, 0)
    E(ldrb_imm, 0, 7, 0); E(cmp_imm, 0, SIG); E(b_cond, "yg_0", "ne")
    E(ldrb_imm, 0, 7, 1); E(lsls_imm, 1, 4, 4); E(raw, h(0x4331)); E(cmp_reg, 0, 1); E(b_cond, "yg_0", "ne")    # orrs r1, r6
    E(movs_imm, 0, BLEN); E(muls, 0, 6); E(adds_reg, 0, 0, 5); E(movs_imm, 1, 0)
    a.label("yg_c"); E(adds_imm8, 1, 2); E(ldrb_reg, 2, 7, 1); E(subs_imm8, 1, 2); E(strb_reg, 2, 0, 1); E(adds_imm8, 1, 1); E(cmp_imm, 1, BLEN); E(b_cond, "yg_c", "lo")
    E(adds_imm8, 6, 1); E(cmp_imm, 6, NBLK); E(b_cond, "yg_b", "lo")
    E(mov_reg, 0, 5); E(bl, "c_yssum"); E(movs_imm, 1, NB); E(ldrb_reg, 2, 5, 1); E(adds_imm8, 1, 1); E(ldrb_reg, 3, 5, 1); E(lsls_imm, 3, 3, 8)
    E(raw, h(0x431A)); E(cmp_reg, 0, 2); E(b_cond, "yg_0", "ne")                     # orrs r2, r3
    E(movs_imm, 0, 1); E(pop_list, [4, 5, 6, 7], pc=True)
    a.label("yg_0"); E(movs_imm, 0, 0); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_ysled (the LED task's call: ctrl, frame): the chain, then the restore after a load / the gather every 256 ms
    a.label("c_ysled")
    E(push_list, [4, 5, 6], lr=True)
    E(bl, prev["ledtask"])
    E(bl, "c_ysst"); E(mov_reg, 4, 0)
    now(0); imm32(1, BOOT_MS); E(cmp_reg, 0, 1); bc("yl_x", "lo")
    E(ldrb_imm, 0, 4, O_PEND); E(cmp_imm, 0, 0); E(b_cond, "yl_g", "eq")
    E(movs_imm, 0, 0); E(strb_imm, 0, 4, O_PEND); E(movs_imm, 5, 0)
    a.label("yl_rt")
    E(mov_reg, 0, 5); E(bl, "c_ysget"); E(cmp_imm, 0, 0); E(b_cond, "yl_rn", "eq")
    E(mov_reg, 0, 5); E(movs_imm, 1, 1); E(bl, "c_ysrun")
    a.label("yl_rn"); E(adds_imm8, 5, 1); E(cmp_imm, 5, 2); E(b_cond, "yl_rt", "lo")
    E(b, "yl_do")                                                                     # gathered at once
    a.label("yl_g")
    E(ldr_imm, 1, 4, O_T); now(0); E(subs_reg, 0, 0, 1); imm32(1, EVERY); E(cmp_reg, 0, 1); bc("yl_x", "lo")
    a.label("yl_do")
    now(0); E(str_imm, 0, 4, O_T)
    E(movs_imm, 0, 0); E(movs_imm, 1, 0); E(bl, "c_ysrun"); E(movs_imm, 0, 1); E(movs_imm, 1, 0); E(bl, "c_ysrun")
    E(movs_imm, 0, 1); E(strb_imm, 0, 4, O_VALID)
    a.label("yl_x"); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_yssave (the bl to the stock save): IMG into the record (when gathered since the load), then the chain
    a.label("c_yssave")
    E(raw, h(0xE92D) + h(0x500F))                                                    # push.w {r0-r3, ip, lr}
    E(bl, "c_ysst"); E(ldrb_imm, 0, 0, O_VALID); E(cmp_imm, 0, 0); E(b_cond, "ys_n", "eq")
    E(movs_imm, 0, 0); E(bl, "c_ysput"); E(movs_imm, 0, 1); E(bl, "c_ysput")
    a.label("ys_n"); E(raw, popw([0, 1, 2, 3, 12], lr=True)); E(b_w, prev["save"])

    # ---- c_ysload (the end of the stock's apply: a load, a new project, power-up): a restore pending, IMG not valid
    a.label("c_ysload")
    E(raw, h(0xE92D) + h(0x500F))
    E(bl, "c_ysst"); E(movs_imm, 1, 1); E(strb_imm, 1, 0, O_PEND); E(movs_imm, 1, 0); E(strb_imm, 1, 0, O_VALID); E(strb_imm, 1, 0, O_VS)
    E(raw, popw([0, 1, 2, 3, 12], lr=True)); E(b_w, prev["load"])
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the heads of mpatch's mp_io / c_mpsz, the LED task's calls, the save call and the end of a load."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = {k: lab("mpatch", k) for k in ("mp_io", "c_mpsz", "c_mpc", "c_mpload", "c_mpsave")}
    prev = dict(ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE), save=FD.bl_target(img, P19.SAVE_CALL, BASE),
                load=MP.bw_target(img, P19.LOAD_END, BASE))
    assert FD.bl_target(img, PK.LED_CALLS[1], BASE) == prev["ledtask"]
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert IMG0 + 2 * IMG_SZ <= MX.MXR + 0x480 and NB + 2 <= NBLK * BLEN
    for at, old, lb in ((L["mp_io"], MPIO_OLD, "c_ysio"), (L["c_mpsz"], MPSZ_OLD, "c_yssz")):
        assert bytes(img[at - BASE:at - BASE + 4]) == old, hex(at)
        img[at - BASE:at - BASE + 4] = b_w(at, labels[lb])
    for c in PK.LED_CALLS: img[c - BASE:c - BASE + 4] = bl(c, labels["c_ysled"])
    img[P19.SAVE_CALL - BASE:P19.SAVE_CALL - BASE + 4] = bl(P19.SAVE_CALL, labels["c_yssave"])
    img[P19.LOAD_END - BASE:P19.LOAD_END - BASE + 4] = b_w(P19.LOAD_END, labels["c_ysload"])
    return labels, code, prev
