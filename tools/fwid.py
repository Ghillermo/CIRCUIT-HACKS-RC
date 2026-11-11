"""Firmware identity (SC56.2 / Beta 5.47 on; the user, 2026-11-11: «In the app, if the device is stock / an unknown custom build, support only
stock-compatible features» -> «Version query»): the device answers a private SysEx with the 6-byte marker of the build it runs, so the SD apps can
tell a Hacks build from the stock firmware (whose identity reply, F0 7E .. 01 64 00 00 01 01 23 06, every build shares: 23 06 = build 4486).

Request  F0 7D 43 54 00 seq 00 00 00 00 00 00 00 F7          (14 bytes: cmd 0, padded so the reply fits in the request's own buffer)
Reply    F0 7D 43 54 40 seq 01 m0 m1 m2 m3 m4 m5 F7          (01 = this format; m = the marker of the version block, image offset 0x1E8, & 0x7F,
                                                              0 after a short name: «B5.47\\0»)
No answer = the stock firmware or a build older than this one.  The same entry as tools/rdiag.py (the incoming SysEx dispatcher 0x0801EB30, its
first 4 bytes -> b.w c_fwin); with rdiag installed first (diagnostic builds), anything not ours goes on to rdiag's c_rdin.  The stock answers
nothing to manufacturer 7D, and rdiag has no command 0 for a request of this length (it swallows requests shorter than its PAD).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, ldr_imm, ldrb_imm, lsls_imm, lsrs_imm, mov_reg, movs_imm, movt, movw,  # noqa: E402
                   pop_list, push_list, raw, h, strb_imm, add_sp_imm, sub_sp_imm)
import rdiag as RD  # noqa: E402

SIG = RD.SIG
CMD, FORMAT, LEN = 0x00, 0x01, 14
MARK_ADDR = 0x08010000 + 0x1E8                    # build_shared_channels.MARK_OFF in the app image
INV = {"eq": "ne", "ne": "eq", "lo": "hs", "hs": "lo"}


def arm_code(base, router_ptr, cont):
    a = Asm(base)
    zc = [0]

    def bc(target, cond):
        zc[0] += 1; n = f"_f{zc[0]}"
        a.emit(b_cond, n, INV[cond]); a.emit(b, target); a.label(n)

    def imm32(rd, v): a.emit(movw, rd, v & 0xFFFF); a.emit(movt, rd, v >> 16)

    # ---- c_fwin: the hooked entry (r0 = port, r1 = msg {buf, len}, r2)
    a.label("c_fwin")                                                          # 8 words pushed: sp stays 8-aligned for the router
    a.emit(push_list, [0, 1, 2, 3, 4, 5, 6], lr=True)
    a.emit(ldr_imm, 4, 1, 0); a.emit(ldr_imm, 5, 1, 4)                          # r4 = buf, r5 = len
    a.emit(cmp_imm, 5, LEN); bc("fw_fwd", "ne")
    for i, v in enumerate(SIG + (CMD,)):
        a.emit(ldrb_imm, 3, 4, i); a.emit(cmp_imm, 3, v); bc("fw_fwd", "ne")
    a.emit(mov_reg, 6, 0)                                                      # r6 = port
    a.emit(movs_imm, 3, 0x40 | CMD); a.emit(strb_imm, 3, 4, 4)
    a.emit(movs_imm, 3, FORMAT); a.emit(strb_imm, 3, 4, 6)
    imm32(2, MARK_ADDR)
    for k in range(6):
        a.emit(ldrb_imm, 3, 2, k); a.emit(lsls_imm, 3, 3, 25); a.emit(lsrs_imm, 3, 3, 25); a.emit(strb_imm, 3, 4, 7 + k)
    a.emit(movs_imm, 3, 0xF7); a.emit(strb_imm, 3, 4, LEN - 1)
    a.emit(sub_sp_imm, 8); a.emit(raw, h(0x9400)); a.emit(movs_imm, 3, LEN); a.emit(raw, h(0x9301))     # str r4, [sp]; str r3, [sp, #4]
    imm32(0, router_ptr); a.emit(ldr_imm, 0, 0, 0)                             # r0 = the router
    a.emit(movs_imm, 1, 1); a.emit(raw, h(0x40B1))                             # lsls r1, r6 -> mask = 1 << port
    a.emit(raw, h(0xAA00))                                                     # add r2, sp, #0 -> &{buf, len}
    a.emit(bl, RD.ROUTER)
    a.emit(add_sp_imm, 8)
    a.emit(pop_list, [0, 1, 2, 3, 4, 5, 6], pc=True)                              # swallowed
    a.label("fw_fwd")
    a.emit(raw, RD.popw([0, 1, 2, 3, 4, 5, 6], lr=True))
    if cont is None:
        a.emit(raw, RD.PROLOGUE); a.emit(b_w, RD.HOOK_CONT)
    else:
        a.emit(b_w, cont)                                                      # rdiag's entry (diagnostic builds)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the first 4 bytes of the incoming SysEx dispatcher -> b.w c_fwin (after rdiag if it is there)."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    cur = bytes(img[RD.HOOK - BASE:RD.HOOK - BASE + 4])
    if cur == RD.PROLOGUE:
        cont = None
    else:
        cont = int(report["rdiag"]["labels"]["c_rdin"], 16)
        assert cur == RD.b_w(RD.HOOK, cont), cur.hex()
    router_ptr = struct.unpack_from("<I", img, RD.ROUTER_LIT - BASE)[0]
    code, labels = arm_code(base_addr, router_ptr, cont)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000 or base_addr < 0x0805CDDC or "dspz" in report
    img[RD.HOOK - BASE:RD.HOOK - BASE + 4] = b_w(RD.HOOK, labels["c_fwin"])
    return labels, code, dict(cont=cont or RD.HOOK_CONT)
