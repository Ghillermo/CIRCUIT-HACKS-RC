"""SC55.6 / Beta 5.41 / RC4.11 / RC4.11S (a fix; the user, 2026-11-09, S555D / S555D2 on the device: «play violet sometimes when loading new patches»,
«custom engine patches, not Nova», Play white = the sequencer's tick late while the mod read the card): loading an own-synth patch read the card
once for every part of the patch.  mpatch's c_mpload reads the patch (44 B of the padding), then c_mpapply's wrappers each read their own block
of the same record through c_mpr: modmx (the matrix), p4dest (page 4, the non-sequenceable page), fmeng / fm8ui (the FM), fm8store (the 8-operator
FM record, 224 B at 4096 + 512 (slot & 7)), smst, vmode, wtui, oscmod (two)... about twelve synchronous reads in the pad press, each through the
storage task, while the sequencer's clock waits.

Now c_mpload's head reads the slot's whole padding (172 B at 512 (slot & 7) + 340) and its FM record area (224 B at 4096 + 512 (slot & 7)) once
into RAM, and a head of mpatch's mp_io serves every read of that bank that falls inside one of the two (with the read's own status and length)
from the copy while the load runs; any other read (another bank, a write, a part outside, a copy whose read failed or came short) goes to the card
as before (the RCs, without the 8-operator FM, read the padding only: one read).  Slots 128+ (projsyn's virtual slot 0xFF, already in RAM) are left alone.  Two reads instead of about twelve.
RAM 0x2004EE00 (between the morph's, which ends at 0x2004EDBC, and 0x2004F400): + 0 ON (the word ON_SIG while a load runs: the RAM is not cleared
at power-up), + 4 slot, + 8 / 12 the padding's status / bytes read, + 16 / 20 the FM area's, + 32 the padding (172 B), + 208 the FM area (224 B).
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, ldrb_reg, lsls_imm, lsrs_imm, mov_reg,  # noqa: E402
                   movs_imm, movt, movw, pop_list, push_list, raw, str_imm, strb_reg, subs_imm8, subs_reg)
import mpatch as MP  # noqa: E402
import packio as PK  # noqa: E402

RAM = 0x2004EE00
ON_SIG = 0x4E41434C                      # "LCAN"
O_ON, O_SLOT, O_PST, O_PN, O_EST, O_EN, O_PAD, O_EXT = 0, 4, 8, 12, 16, 20, 32, 208
PADN, EXT0, EXTN = MP.LEN, 4096, 224
END = RAM + O_EXT + EXTN


def arm_code(base, prev, ext=True):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)

    # ---- c_lcload (c_mpload's head: r0 = track, r1 = slot): the slot's two areas into RAM, then the load with mp_io's head serving them
    a.label("c_lcload")
    E(push_list, [0, 1, 4, 5, 6], lr=True)
    imm32(4, RAM); E(movs_imm, 2, 0); E(str_imm, 2, 4, O_ON)
    E(cmp_imm, 1, 0x80); E(b_cond, "ld_go", "hs")
    E(str_imm, 1, 4, O_SLOT); E(mov_reg, 6, 1)
    E(lsls_imm, 5, 6, 29); E(lsrs_imm, 5, 5, 20)                                      # r5 = 512 (slot & 7)
    E(lsrs_imm, 0, 6, 3); E(movw, 1, MP.OFF); E(adds_reg, 1, 1, 5); imm32(2, RAM + O_PAD); E(movs_imm, 3, PADN); E(bl, prev["c_mpr"])
    E(str_imm, 0, 4, O_PST); E(str_imm, 1, 4, O_PN)
    if ext:                                                                            # (the 8-operator FM's record: builds with fm8store)
        E(lsrs_imm, 0, 6, 3); E(movs_imm, 1, 1); E(lsls_imm, 1, 1, 12); E(adds_reg, 1, 1, 5); imm32(2, RAM + O_EXT); E(movs_imm, 3, EXTN); E(bl, prev["c_mpr"])
        E(str_imm, 0, 4, O_EST); E(str_imm, 1, 4, O_EN)
    imm32(2, ON_SIG); E(str_imm, 2, 4, O_ON)
    a.label("ld_go")
    E(pop_list, [0, 1])
    E(bl, "c_lcload_t")
    imm32(4, RAM); E(movs_imm, 1, 0); E(str_imm, 1, 4, O_ON)
    E(pop_list, [4, 5, 6], pc=True)
    a.label("c_lcload_t"); E(raw, prev["load_old"]); E(b_w, prev["c_mpload"] + 4)

    # ---- c_lcio (mp_io's head: r4 = the read / write, r0 bank, r1 offset, r2 buffer, r3 length; c_mpr / c_mpw pushed r4-r7, lr; r5-r7 free)
    a.label("c_lcio")
    imm32(7, RAM); E(ldr_imm, 6, 7, O_ON); imm32(5, ON_SIG); E(cmp_reg, 6, 5); E(b_cond, "io_p", "ne")
    imm32(5, PK.READ | 1); E(cmp_reg, 4, 5); E(b_cond, "io_p", "ne")
    E(ldr_imm, 6, 7, O_SLOT); E(lsrs_imm, 5, 6, 3); E(cmp_reg, 0, 5); E(b_cond, "io_p", "ne")
    E(lsls_imm, 6, 6, 29); E(lsrs_imm, 6, 6, 20)                                      # r6 = 512 (slot & 7)
    for tag, start, st, n, src in (("p", MP.OFF, O_PST, O_PN, O_PAD), ("e", EXT0, O_EST, O_EN, O_EXT))[:2 if ext else 1]:
        E(ldr_imm, 5, 7, st); E(cmp_imm, 5, 0); E(b_cond, f"io_n{tag}", "ne")          # its read failed: the card
        E(movw, 5, start); E(adds_reg, 5, 5, 6); E(subs_reg, 5, 1, 5)                  # r5 = offset - the area's start (unsigned)
        E(adds_reg, 6, 5, 3)                                                            # r6 = its end (r5 huge when the offset is before the area)
        E(push_list, [0]); E(ldr_imm, 0, 7, n); E(cmp_reg, 6, 0); E(pop_list, [0]); E(b_cond, f"io_n{tag}", "hi")   # past the bytes read: the card
        imm32(6, RAM + src); E(adds_reg, 5, 5, 6); E(b, "io_cp")
        a.label(f"io_n{tag}")
        E(ldr_imm, 6, 7, O_SLOT); E(lsls_imm, 6, 6, 29); E(lsrs_imm, 6, 6, 20)
    a.label("io_p")
    if prev["io_bw"]: E(b_w, prev["io_next"])
    else: E(raw, prev["io_old"]); E(b_w, prev["mp_io"] + 4)
    a.label("io_cp")                                                                   # r5 = the source, r3 bytes to r2
    E(mov_reg, 6, 3)
    a.label("io_l"); E(subs_imm8, 6, 1); E(b_cond, "io_d", "mi"); E(ldrb_reg, 7, 5, 6); E(strb_reg, 7, 2, 6); E(b, "io_l")
    a.label("io_d"); E(movs_imm, 0, 0); E(mov_reg, 1, 3); E(pop_list, [4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (build_sc41_5.add); the heads of mpatch's c_mpload and mp_io."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    lab = lambda k: int(report["mpatch"]["labels"][k], 16)
    old = lambda a_: bytes(img[a_ - BASE:a_ - BASE + 4])
    ld, io = lab("c_mpload"), lab("mp_io")
    assert old(ld) == bytes.fromhex("70b50446"), old(ld).hex()
    nxt = MP.bw_target(img, io, BASE)
    prev = dict(c_mpr=lab("c_mpr"), c_mpload=ld, mp_io=io, load_old=old(ld), io_old=old(io), io_bw=nxt is not None, io_next=nxt or 0)
    ext = "fm8" in report                                                              # the RCs have no 8-operator FM record: the padding only
    code, labels = arm_code(base_addr, prev, ext)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000, hex(len(img))
    img[ld - BASE:ld - BASE + 4] = b_w(ld, labels["c_lcload"])
    img[io - BASE:io - BASE + 4] = b_w(io, labels["c_lcio"])
    import morphz
    assert morphz.NV_END <= RAM and END <= 0x2004F400
    return labels, code, {k: v for k, v in prev.items() if isinstance(v, int) and not isinstance(v, bool)}
