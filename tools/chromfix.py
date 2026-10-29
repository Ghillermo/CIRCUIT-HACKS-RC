"""SC49.7 / Beta 5.0 / RC4.02 (the user, 2026-10-29: «i m having trouble recording chromatic sample notes from the pads»; «chromatic drums
still dont record automation right. either they stay on the same note or have their notes switched»; chosen: «Hit + pitch», steps without a
pitch: «Knob pitch»; «fix the quantize too»): a chromatic pad recorded while playing = a hit with its pitch.

The chromatic view (a drum's Preset view in chromatic mode, SC08 / SC11) plays the drum through the stock's audition of the Preset view, which
the stock never records: with Record, dpitch's c_dppad (lane 0, 0x80 | S) and lanex's c_xlplane (the extra lane, its code) wrote only the pitch,
at the step the engine had (ENG + 0x30 + 4 (4 + d) p1).  The hits came from elsewhere: a pitch landed on the hit of another step or on a step
with none, and the steps without one played the last pad's S («the same note»).  Now (c_cfnear, in place of the step both read) the press also
records its hit, as the stock records a drum pad of the Note view: at the step that plays, its micro step = the engine's tick p2 × 6 / the ticks a
step of the pattern's sync rate (0x0805B8B8), at most 5; on an empty step the pad's velocity (the chromatic handler's, in r6 when it calls
c_dppad) and probability 7 (bits 3-7 kept: lanex's lane); the drum's edit store synced (drumarp's c_dasync).  The pitch goes to that step.
Quantize (Shift + Play, quant's c_qzhit): a hit moved to the next step leaves its pitch behind; now (c_cfqz, around each call) the chromatic pitch
moves with it: the extra lane's code (lanex, the drum on the chromatic pitch) when the next step has none, and lane 0's six 0x80 | S bytes when the
next step's lane 0 is empty.
RAM: modmx.MXR + 0x2150: + 2 the step handed to dpitch.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, bl, cmp_imm, cmp_reg, h, ldr_imm, ldr_sp, ldrb_imm, ldrb_reg, ldrb_w, lsls_imm,  # noqa: E402
                   lsrs_imm, mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list, raw, strb_imm, strb_reg, strb_w, subs_imm8, subs_reg)
from build_sc14 import udiv  # noqa: E402
import modmx as MX  # noqa: E402

RAM = MX.MXR + 0x2150
DP0, DP_SZ, PAT_SZ = 0x20040810, 0x90, 0x6A8
ENG, PARAM_GET, TPS = 0x20038EC0, 0x0803542C, 0x0805B8B8
RET = h(0x4770)
def negs(rd, rm): return h(0x4240 | rm << 3 | rd)


def arm_code(base, L, lanex):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)

    # ---- c_cfnear(r0 = drum; r6 = the pad's velocity) -> r0 = the base of the pattern it plays, r1 = the step that plays, its hit recorded there
    #      (the micro step of the press; on an empty step the velocity and probability 7); clobbers r2, r3
    a.label("c_cfnear")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0)                                                            # [sp + 8] = the velocity
    E(adds_imm8, 0, 4); E(lsls_imm, 0, 0, 2); imm32(1, ENG + 0x30); E(adds_reg, 0, 0, 1); E(ldr_imm, 5, 0, 0)          # r5 = the store
    E(mov_reg, 0, 5); E(movs_imm, 1, 2); E(bl, PARAM_GET); E(ldrb_imm, 6, 0, 0)                                     # r6 = the tick
    E(mov_reg, 0, 5); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 7, 0, 0)                                     # r7 = the pattern
    E(mov_reg, 0, 5); E(movs_imm, 1, 1); E(bl, PARAM_GET); E(ldrb_imm, 5, 0, 0)                                     # r5 = the step
    imm32(0, DP0); E(movs_imm, 1, DP_SZ); E(muls, 1, 4); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, 0x48)
    E(movw, 1, PAT_SZ); E(muls, 7, 1); E(adds_reg, 7, 7, 0)                                                          # r7 = the base
    E(ldrb_w, 0, 7, 0x82); E(cmp_imm, 0, 7); E(b_cond, "cn_r", "ls"); E(movs_imm, 0, 3)
    a.label("cn_r"); E(lsls_imm, 0, 0, 2); imm32(1, TPS)
    E(adds_reg, 1, 1, 0); E(ldr_imm, 1, 1, 0); E(movs_imm, 0, 6); E(muls, 0, 6); E(raw, udiv(6, 0, 1))          # r6 = the micro step
    E(cmp_imm, 6, 5); E(b_cond, "cn_m", "ls"); E(movs_imm, 6, 5)
    a.label("cn_m"); E(cmp_imm, 5, 31); E(b_cond, "cn_x", "hi")
    E(adds_reg, 1, 7, 5); E(ldrb_imm, 0, 1, 0); E(cmp_imm, 0, 0); E(b_cond, "cn_h", "ne")                          # an empty step:
    E(ldr_sp, 0, 8); E(cmp_imm, 0, 0); E(b_cond, "cn_v", "ne"); E(movs_imm, 0, 100)
    a.label("cn_v"); E(cmp_imm, 0, 127); E(b_cond, "cn_w", "ls"); E(movs_imm, 0, 127)
    a.label("cn_w"); E(strb_imm, 0, 1, 0)                                                                         # the velocity,
    E(ldrb_w, 0, 1, 0x20); E(lsrs_imm, 0, 0, 3); E(lsls_imm, 0, 0, 3); E(adds_imm8, 0, 7); E(strb_w, 0, 1, 0x20)  # probability 7
    a.label("cn_h"); E(ldrb_w, 0, 1, 0x60); E(movs_imm, 2, 1); E(raw, h(0x40B2)); E(orrs_reg, 0, 2); E(strb_w, 0, 1, 0x60)   # lsls r2, r6: the micro step
    imm32(0, DP0); E(movs_imm, 1, DP_SZ); E(muls, 1, 4); E(adds_reg, 0, 0, 1); E(mov_reg, 1, 5); E(mov_reg, 2, 7); E(bl, L["c_dasync"])
    a.label("cn_x"); E(mov_reg, 0, 7); E(mov_reg, 1, 5); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_cfp1 (dpitch's c_dppad, in place of the bl PARAM_GET(store, 1) of the playing step; r4 = the drum) -> r0 = a byte holding the step
    a.label("c_cfp1")
    E(push_list, [], lr=True); E(mov_reg, 0, 4); E(bl, "c_cfnear"); imm32(0, RAM + 2); E(strb_imm, 1, 0, 0); E(pop_list, [], pc=True)

    # ---- c_cfqz (quant's c_qzdo, around its c_qzhit(base, step, the next step or 0xFF)): a hit moved, its chromatic pitch with it
    a.label("c_cfqz")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True); E(ldrb_reg, 4, 0, 1)                                            # r4 = the hit before
    E(bl, L["c_qzhit"])
    E(ldr_sp, 0, 0); E(ldr_sp, 1, 4); E(ldr_sp, 2, 8)
    E(cmp_imm, 2, 0xFF); E(b_cond, "qz_x", "eq"); E(cmp_imm, 4, 0); E(b_cond, "qz_x", "eq")
    E(ldrb_reg, 3, 0, 1); E(cmp_imm, 3, 0); E(b_cond, "qz_x", "ne")                                               # the hit stayed
    if lanex:
        E(movs_imm, 4, 0)                                                                                           # r4 = the drum of the base
        a.label("qz_d"); imm32(3, DP0); E(movs_imm, 5, DP_SZ); E(muls, 5, 4); E(adds_reg, 3, 3, 5); E(ldr_imm, 3, 3, 0x48)
        E(subs_reg, 5, 0, 3); E(movw, 6, 8 * PAT_SZ); E(cmp_reg, 5, 6); E(b_cond, "qz_f", "lo")
        E(adds_imm8, 4, 1); E(cmp_imm, 4, 4); E(b_cond, "qz_d", "lo"); E(b, "qz_l")
        a.label("qz_f"); E(mov_reg, 0, 4); E(bl, L["c_xlasg"]); E(cmp_imm, 0, 0); E(b_cond, "qz_l", "ne")              # the chromatic pitch
        E(ldr_sp, 0, 0); E(ldr_sp, 1, 4); E(bl, L["c_xlrd"]); E(mov_reg, 5, 0); E(cmp_imm, 5, 0); E(b_cond, "qz_l", "eq")
        E(ldr_sp, 0, 0); E(ldr_sp, 1, 8); E(bl, L["c_xlrd"]); E(cmp_imm, 0, 0); E(b_cond, "qz_l", "ne")
        E(mov_reg, 0, 4); E(ldr_sp, 1, 8); E(mov_reg, 2, 5); E(ldr_sp, 3, 0); E(bl, L["c_xlwr"])
        E(mov_reg, 0, 4); E(ldr_sp, 1, 4); E(movs_imm, 2, 0); E(ldr_sp, 3, 0); E(bl, L["c_xlwr"])
        a.label("qz_l")
    E(ldr_sp, 0, 0); E(ldr_sp, 1, 4); E(movs_imm, 2, 6); E(muls, 1, 2); E(adds_reg, 1, 1, 0); E(adds_imm8, 1, 0xA8)   # lane 0 of the step
    E(ldr_sp, 2, 8); E(movs_imm, 3, 6); E(muls, 2, 3); E(adds_reg, 2, 2, 0); E(adds_imm8, 2, 0xA8)                    # and of the next
    E(ldrb_imm, 3, 1, 0); E(cmp_imm, 3, 0x80); E(b_cond, "qz_x", "lo"); E(cmp_imm, 3, 0xFF); E(b_cond, "qz_x", "eq")
    E(ldrb_imm, 3, 2, 0); E(cmp_imm, 3, 0xFF); E(b_cond, "qz_x", "ne")
    E(movs_imm, 3, 0)
    a.label("qz_c"); E(ldrb_reg, 4, 1, 3); E(strb_reg, 4, 2, 3); E(movs_imm, 4, 0xFF); E(strb_reg, 4, 1, 3)
    E(adds_imm8, 3, 1); E(cmp_imm, 3, 6); E(b_cond, "qz_c", "lo")
    a.label("qz_x"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """At the image's end: dpitch's step read in c_dppad, lanex's in c_xlplane (when there), quant's call of c_qzhit."""
    import ct_fw
    import hole
    BASE = ct_fw.APP_BASE
    rd = lambda at, n: bytes(img[at - BASE:at - BASE + n])
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    lanex = "lanex" in report
    L = dict(c_qzhit=lab("quant", "c_qzhit"), c_dasync=lab("drumarp", "c_dasync"))
    if lanex:
        L.update({k: lab("lanex", k) for k in ("c_xlasg", "c_xlrd", "c_xlwr", "c_xlbase", "c_xlplane")})
    pad = lab("dpitch", "c_dppad")
    dp = [x for x in range(pad, pad + 0x100, 2) if rd(x, 2) == h(0x2101) and rd(x + 2, 4) == bl(x + 2, PARAM_GET)
          and rd(x + 6, 2) == h(0x7800) and rd(x + 8, 2) == h(0xBC02)]
    assert len(dp) == 1, [hex(x) for x in dp]
    qz = [x for x in range(lab("quant", "c_qzdo"), lab("quant", "c_qzdo") + 0x200, 2) if rd(x, 4) == bl(x, L["c_qzhit"])]
    assert len(qz) == 1, [hex(x) for x in qz]
    xl = []
    if lanex:
        xl = [x for x in range(L["c_xlplane"], L["c_xlplane"] + 0x40, 2) if rd(x, 4) == bl(x, L["c_xlbase"])]
        assert len(xl) == 1, [hex(x) for x in xl]
    code, labels = arm_code(base_addr, L, lanex)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000, f"chromfix: the image is full ({len(img):#x})"
    def put(at, data): img[at - BASE:at - BASE + len(data)] = data
    put(dp[0] + 2, bl(dp[0] + 2, labels["c_cfp1"])); hole.rehash(img, report, dp[0] + 2)
    put(qz[0], bl(qz[0], labels["c_cfqz"])); hole.rehash(img, report, qz[0])
    for x in xl:
        put(x, bl(x, labels["c_cfnear"])); hole.rehash(img, report, x)
    return labels, code, dict(dpitch=dp[0] + 2, quant=qz[0], lanex=xl[0] if xl else 0)
