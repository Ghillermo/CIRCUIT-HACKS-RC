"""SC39.6 (the user, 2026-10-12: «copiar proyectos (sessions) completos entre packs» … «adelante»): a project copied to another slot, of the same
pack or of another one, from the Projects view.

Use (the Projects view; stock ignores Duplicate there: its held-button mask, slot 8 of the view, only lets Clear in, and Duplicate + pad was a
plain pad):
  * Duplicate + pad A (a slot with a project) = A is the source: it blinks yellow in its pack; Duplicate + A again forgets it;
  * with a source, Duplicate + pad B (in this pack or, after loading another pack, in that one) = the project is copied into B.  An empty B is
    written at once; a B that holds a project blinks white first and Duplicate + B again within ~5 s writes; the slot of the loaded project is
    never written.  B stays yellow (the colour of what came from another place) until the view state is lost; the source stays, for more copies.
The copy is the file itself (Sessions/NN_SESSION.ncs, kind 2 of the content API, 160 780 bytes) read and written in 4 KB pieces through the stock's
shared buffer under its lock, each item naming its pack by number; then the storage task is put back on the loaded pack (packio.c_resel).  The
stock keeps its own list of the slots in use: a copied project shows in yellow from this code, and loads as any other (the stock reads the file).
State (no new RAM): 8 bytes of the Master FX block's idle LED buffer after psave's (c_gst() + 132):
    [0] tag  [1] 0x80 | session A  [2] its pack  [3] 0x80 | the B asked about  [4..5] the time of the question  [6] 0x80 | the last B  [7] its pack
It survives a pack change; it is lost when the Master FX view is opened (that buffer is its own then) or the power goes.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, ldrb_w, ldrh_imm, lsls_imm, lsrs_imm,  # noqa: E402
                   mov_reg, movs_imm, movt, movw, orrs_reg, pop_list, push_list, raw, h, str_imm, strb_imm, strh_imm, strh_reg, subs_reg, sub_sp_imm,
                   add_sp_imm, tst_reg)
import packio as PK  # noqa: E402
import vcf21 as V  # noqa: E402
import psave as PS  # noqa: E402

PROJ_VT = 0x0805A71C                  # the Projects view: slot 0 pads, slot 8 the held buttons it accepts ([view + 0x36] = its page, [view + 0x20] param 8 = the loaded project)
MGR = PS.MGR
KIND_SESS = 2
CHUNK_SHIFT = 12                      # 4 KB pieces (the shared buffer)
ST_OFF, MAGIC = PS.ST_OFF + 8, 0xC3
LIFE = PS.LIFE
COL_SRC = PK.YELLOW                   # the source blinks, the copy is steady
COL_ASK = 0x01
INV8 = V.INV


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    zc = [0]
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def bc(target, cond):
        zc[0] += 1; n = f"_k{zc[0]}"
        E(b_cond, n, INV8[cond]); E(b, target); a.label(n)
    def tick(rd): imm32(rd, PK.HAL_TICK); E(ldr_imm, rd, rd, 0); E(lsrs_imm, rd, rd, 8); E(lsls_imm, rd, rd, 16); E(lsrs_imm, rd, rd, 16)
    BX_LR = h(0x4770)

    # ---- c_scst() -> r0 = the state (tag written when the bytes were someone else's: nothing kept), 0 without the block; clobbers r1-r3
    a.label("c_scst")
    E(push_list, [4], lr=True)
    E(bl, L["c_gst"]); E(cmp_imm, 0, 0); E(b_cond, "st_x", "eq")
    E(adds_imm8, 0, ST_OFF)
    E(ldrb_imm, 1, 0, 0); E(cmp_imm, 1, MAGIC); E(b_cond, "st_x", "eq")
    E(movs_imm, 1, MAGIC); E(strb_imm, 1, 0, 0); E(movs_imm, 1, 0); E(strb_imm, 1, 0, 1); E(strb_imm, 1, 0, 3); E(strb_imm, 1, 0, 6)
    a.label("st_x"); E(pop_list, [4], pc=True)

    # ---- c_scon() -> r0 = the Projects view when it is on the screen, else 0; clobbers r1, r2
    a.label("c_scon")
    imm32(0, MGR); E(ldr_imm, 0, 0, 0x6C); E(cmp_imm, 0, 0); E(b_cond, "on_n", "eq")
    E(ldr_imm, 1, 0, 0); imm32(2, PROJ_VT); E(cmp_reg, 1, 2); E(b_cond, "on_n", "ne"); E(raw, BX_LR)
    a.label("on_n"); E(movs_imm, 0, 0); E(raw, BX_LR)

    # ---- c_scsize(r0 = session, r1 = pack) -> r0 = the size of its file (0: no project there)
    a.label("c_scsize")
    E(push_list, [4], lr=True); E(sub_sp_imm, 16)
    E(movs_imm, 2, KIND_SESS); E(raw, h(0x9200)); E(raw, h(0x9001)); E(raw, h(0x9102))          # str r2 / r0 / r1, [sp, #0 / 4 / 8]
    E(mov_reg, 0, 13); E(bl, PK.SIZE)
    E(add_sp_imm, 16); E(pop_list, [4], pc=True)

    # ---- c_sccopy(r0 = session A, r1 = its pack, r2 = session B, r3 = its pack) -> r0 = status (0 = copied): the file in 4 KB pieces
    #      frame r7: [0] cb [4] ctx [8] &done [12] done [16..27] item A [28..39] item B [40] size [44] offset
    a.label("c_sccopy")
    E(push_list, [3, 4, 5, 6, 7], lr=True); E(sub_sp_imm, 48); E(mov_reg, 7, 13)
    E(str_imm, 0, 7, 20); E(str_imm, 1, 7, 24); E(str_imm, 2, 7, 32); E(str_imm, 3, 7, 36)
    E(movs_imm, 0, KIND_SESS); E(str_imm, 0, 7, 16); E(str_imm, 0, 7, 28)
    E(movs_imm, 0, 0); E(str_imm, 0, 7, 44)
    E(mov_reg, 0, 7); E(adds_imm8, 0, 16); E(bl, PK.SIZE); E(str_imm, 0, 7, 40); E(cmp_imm, 0, 0); E(b_cond, "cp_go", "ne")
    E(movs_imm, 0, 8); E(add_sp_imm, 48); E(pop_list, [3, 4, 5, 6, 7], pc=True)
    a.label("cp_go")
    E(movs_imm, 0, 5); E(bl, PK.BUF_LOCK)
    a.label("cp_l")
    E(ldr_imm, 4, 7, 44); E(ldr_imm, 5, 7, 40); E(cmp_reg, 4, 5); bc("cp_ok", "hs")
    E(subs_reg, 5, 5, 4); E(movs_imm, 6, 1); E(lsls_imm, 6, 6, CHUNK_SHIFT); E(cmp_reg, 5, 6); E(b_cond, "cp_n", "ls"); E(mov_reg, 5, 6)
    a.label("cp_n")                                                                   # r4 = the offset, r5 = the bytes of this piece
    for fn, item in ((PK.READ, 16), (PK.WRITE, 28)):
        E(movs_imm, 0, 0); E(str_imm, 0, 7, 0); E(str_imm, 0, 7, 4); E(str_imm, 0, 7, 12)
        E(mov_reg, 0, 7); E(adds_imm8, 0, 12); E(str_imm, 0, 7, 8)
        E(mov_reg, 0, 7); E(adds_imm8, 0, item); E(mov_reg, 1, 4); imm32(2, PK.BUF); E(mov_reg, 3, 5); E(bl, fn)
        E(cmp_imm, 0, 0); bc("cp_f", "ne")
        if fn == PK.READ: E(ldr_imm, 0, 7, 12); E(cmp_reg, 0, 5); bc("cp_f8", "ne")
    E(adds_reg, 4, 4, 5); E(str_imm, 4, 7, 44); E(b, "cp_l")
    a.label("cp_ok"); E(movs_imm, 6, 0); E(b, "cp_u")
    a.label("cp_f8"); E(movs_imm, 0, 8)
    a.label("cp_f"); E(mov_reg, 6, 0)
    a.label("cp_u")
    E(bl, PK.BUF_UNLOCK)
    E(bl, L["c_curpack"]); E(bl, L["c_resel"])
    E(mov_reg, 0, 6); E(add_sp_imm, 48); E(pop_list, [3, 4, 5, 6, 7], pc=True)

    # ---- c_scpad (the Projects view's slot 0: view, pad, velocity): Duplicate held = the source, then the copies
    a.label("c_scpad")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(cmp_imm, 5, 32); bc("sp_f", "hs")
    imm32(0, MGR); E(ldr_imm, 0, 0, 0x20); E(ldr_imm, 0, 0, 0xC); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 6, 0, 0)
    E(movs_imm, 0, 2); E(tst_reg, 6, 0); bc("sp_f", "eq")
    E(bl, "c_scst"); E(mov_reg, 7, 0); E(cmp_imm, 7, 0); bc("sp_f", "eq")
    E(ldrb_w, 0, 4, 0x36); E(lsls_imm, 0, 0, 5); E(adds_reg, 5, 5, 0)                 # r5 = the session
    E(cmp_imm, 5, 64); bc("sp_e", "hs")
    E(bl, L["c_curpack"]); E(mov_reg, 6, 0)                                           # r6 = the loaded pack
    E(ldrb_imm, 0, 7, 1); E(movs_imm, 1, 0x80); E(tst_reg, 0, 1); bc("sp_src", "eq")
    E(movs_imm, 1, 0x7F); E(ands_reg, 0, 1); E(ldrb_imm, 1, 7, 2)
    E(cmp_reg, 1, 6); E(b_cond, "sp_paste", "ne"); E(cmp_reg, 0, 5); E(b_cond, "sp_paste", "ne")
    E(movs_imm, 0, 0); E(strb_imm, 0, 7, 1); E(strb_imm, 0, 7, 3); E(b, "sp_e")       # the source again: forgotten
    a.label("sp_paste")
    E(ldr_imm, 0, 4, 0x20); E(movs_imm, 1, 8); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_reg, 0, 5); bc("sp_e", "eq")   # never the loaded project
    E(mov_reg, 0, 5); E(mov_reg, 1, 6); E(bl, "c_scsize"); E(cmp_imm, 0, 0); E(b_cond, "sp_go", "eq")
    E(movs_imm, 0, 0x80); E(orrs_reg, 0, 5); E(ldrb_imm, 1, 7, 3); E(cmp_reg, 1, 0); E(b_cond, "sp_ask", "ne")
    tick(0); E(ldrh_imm, 1, 7, 4); E(subs_reg, 0, 0, 1); E(lsls_imm, 0, 0, 16); E(lsrs_imm, 0, 0, 16); E(cmp_imm, 0, LIFE); E(b_cond, "sp_ask", "hs")
    a.label("sp_go")
    E(movs_imm, 0, 0); E(strb_imm, 0, 7, 3)
    E(ldrb_imm, 0, 7, 1); E(movs_imm, 1, 0x7F); E(ands_reg, 0, 1); E(ldrb_imm, 1, 7, 2); E(mov_reg, 2, 5); E(mov_reg, 3, 6); E(bl, "c_sccopy")
    E(cmp_imm, 0, 0); bc("sp_e", "ne")
    E(movs_imm, 0, 0x80); E(orrs_reg, 0, 5); E(strb_imm, 0, 7, 6); E(strb_imm, 6, 7, 7); E(b, "sp_e")
    a.label("sp_ask")
    E(movs_imm, 0, 0x80); E(orrs_reg, 0, 5); E(strb_imm, 0, 7, 3); tick(0); E(strh_imm, 0, 7, 4); E(b, "sp_e")
    a.label("sp_src")
    E(mov_reg, 0, 5); E(mov_reg, 1, 6); E(bl, "c_scsize"); E(cmp_imm, 0, 0); E(b_cond, "sp_e", "eq")     # an empty slot is no source
    E(movs_imm, 0, 0x80); E(orrs_reg, 0, 5); E(strb_imm, 0, 7, 1); E(strb_imm, 6, 7, 2); E(movs_imm, 0, 0); E(strb_imm, 0, 7, 3)
    a.label("sp_e"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("sp_f"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["pad"])

    # ---- c_scmask (the view's slot 8): the held buttons it accepts + Duplicate
    a.label("c_scmask")
    E(push_list, [4], lr=True); E(bl, prev["mask"]); E(movs_imm, 1, 2); E(orrs_reg, 0, 1); E(pop_list, [4], pc=True)

    # ---- c_scput(r0 = 0x80 | session or 0, r1 = colour; r4 = the view, r5 = the frame): that pad of the page shown; clobbers r0, r2, r3
    a.label("c_scput")
    E(movs_imm, 2, 0x80); E(tst_reg, 0, 2); E(b_cond, "pt_x", "eq")
    E(movs_imm, 2, 0x7F); E(ands_reg, 0, 2); E(lsrs_imm, 2, 0, 5); E(ldrb_w, 3, 4, 0x36); E(cmp_reg, 2, 3); E(b_cond, "pt_x", "ne")
    E(movs_imm, 2, 31); E(ands_reg, 0, 2); E(lsls_imm, 0, 0, 1); E(strh_reg, 1, 5, 0)
    a.label("pt_x"); E(raw, BX_LR)

    # ---- c_scledtask (the LED task calls: ctrl, frame): the chain, then on the frame: the copy steady yellow, the source blinking yellow, the question white
    a.label("c_scledtask")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1); E(bl, prev["ledtask"])
    E(bl, "c_scon"); E(mov_reg, 4, 0); E(cmp_imm, 4, 0); bc("lt_x", "eq")
    E(bl, "c_scst"); E(mov_reg, 7, 0); E(cmp_imm, 7, 0); bc("lt_x", "eq")
    E(bl, L["c_curpack"]); E(mov_reg, 6, 0)
    E(ldrb_imm, 0, 7, 7); E(cmp_reg, 0, 6); E(b_cond, "lt_a", "ne")
    E(ldrb_imm, 0, 7, 6); E(movs_imm, 1, COL_SRC); E(bl, "c_scput")
    a.label("lt_a")
    imm32(0, PK.HAL_TICK); E(ldr_imm, 0, 0, 0); E(lsrs_imm, 0, 0, 7); E(movs_imm, 1, 1); E(ands_reg, 0, 1); E(mov_reg, 3, 0)
    E(ldrb_imm, 0, 7, 2); E(cmp_reg, 0, 6); E(b_cond, "lt_q", "ne")
    E(movs_imm, 1, COL_SRC); E(cmp_imm, 3, 0); E(b_cond, "lt_a1", "eq"); E(movs_imm, 1, 0)
    a.label("lt_a1"); E(push_list, [3]); E(ldrb_imm, 0, 7, 1); E(bl, "c_scput"); E(pop_list, [3])
    a.label("lt_q")
    E(ldrb_imm, 0, 7, 3); E(cmp_imm, 0, 0); E(b_cond, "lt_x", "eq")
    E(push_list, [3]); tick(0); E(pop_list, [3]); E(ldrh_imm, 1, 7, 4); E(subs_reg, 0, 0, 1); E(lsls_imm, 0, 0, 16); E(lsrs_imm, 0, 0, 16); E(cmp_imm, 0, LIFE); E(b_cond, "lt_q1", "lo")
    E(movs_imm, 0, 0); E(strb_imm, 0, 7, 3); E(b, "lt_x")
    a.label("lt_q1")
    E(movs_imm, 1, COL_ASK); E(cmp_imm, 3, 0); E(b_cond, "lt_q2", "eq"); E(movs_imm, 1, 0)
    a.label("lt_q2"); E(ldrb_imm, 0, 7, 3); E(bl, "c_scput")
    a.label("lt_x"); E(pop_list, [3, 4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the Projects view's slots 0 / 8 and the two LED task calls."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a: struct.unpack_from("<I", img, a - BASE)[0]
    lab = lambda sec, n: int(report[sec]["labels"][n], 16)
    L = dict(c_gst=lab("sc14", "c_gst"), c_curpack=lab("packio", "c_curpack"), c_resel=lab("packio", "c_resel"))
    prev = dict(pad=u(PROJ_VT) & ~1, mask=u(PROJ_VT + 32) & ~1, ledtask=lab("macroed", "c_mcledtask"))
    assert prev["pad"] == 0x08044FF6 and prev["mask"] == 0x080454A2, prev
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    struct.pack_into("<I", img, PROJ_VT - BASE, labels["c_scpad"] | 1)
    struct.pack_into("<I", img, PROJ_VT + 32 - BASE, labels["c_scmask"] | 1)
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_scledtask"])
    return labels, code, prev
