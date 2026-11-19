"""Alpha 7.06 (the 2026-11-14 bug hunt's XL-9; the user, 2026-11-18: «Do xlanes»): the extra lanes' LED-task work gets its own DSP window.

Every DSP external-memory transfer goes through the sampler's block copy (CPSRC / CPDST / CPLEN, checked and set under the DSP service semaphore:
two tasks never start a copy at the same time) and a 64-word window in core 0's Y (packio.WIN = Y:$3B40): a read = copy into the window, sleep
until it is done, read the window word by word; a write = the window written word by word, then a copy out of it.  Between those two halves the
task sleeps, and the other task could use the same window: the LED task (xlanes: c_xlsave, c_xlload, c_xlrel, c_xlflush, c_xlfill) against the
main loop (Components' session writes: c_xlhold / c_xlback; packio's sample swaps and WAV saves; drum replacement).  One task then read or wrote
the other's words: wrong lane data in the ITCM, in the card file or in a held Components tail (rare; no crash).

Now the LED task's five functions use WIN2 = Y:$3B80..$3BBF (unused: sentinels there stay put through emu_sc43_9_dsp's whole engine traffic, 300
blocks, on Alpha 7.05; the stock's free area X / Y $3339-$3BFF); the main loop keeps WIN.  No lock, no waiting, no timing change.
Done after the build, on xlanes' code in place (same size; the window's address is a literal shared with c_xlhold / c_xlback in the compacted
code, so the calls are redirected, not the constants): in those five functions bl DSP_READ -> c_xrd2 (a read of Y:WIN + k reads Y:WIN2 + k),
bl c_copy -> c_xcw2 (= c_copy2(src, WIN2, n)), bl c_ywin -> c_xyw2 (c_ywin into WIN2), bl c_copy2 -> c_xcs2 (WIN as source / destination ->
WIN2); the four helpers in a dspz gap or at the image's end."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldrh_reg, lsls_imm, mov_reg, movs_imm, movw, pop_list, push_list, subs_reg  # noqa: E402
import packio as PK  # noqa: E402

WIN2 = 0x3B80
LED_FUNCS = ("c_xlsave", "c_xlload", "c_xlrel", "c_xlflush", "c_xlfill")
# per function: the calls redirected (DSP_READ, c_copy, c_ywin, c_copy2)
EXPECT = dict(c_xlsave=(1, 1, 0, 0), c_xlload=(0, 0, 1, 1), c_xlrel=(0, 0, 1, 1), c_xlflush=(0, 0, 1, 1), c_xlfill=(1, 1, 0, 0))


def arm_code(base, L):
    """(the window's address is a literal shared with the main loop's functions in the compacted build: the calls are redirected instead)"""
    a = Asm(base)
    E = a.emit
    a.label("c_xcw2")                                    # c_copy(r0 = Y source, r1 = n) -> c_copy2(r0, WIN2, r1)
    E(mov_reg, 2, 1); E(movw, 1, WIN2); E(b_w, L["c_copy2"])
    a.label("c_xcs2")                                    # c_copy2(r0, r1, r2) with WIN as source or destination -> WIN2
    E(movw, 3, PK.WIN); E(cmp_reg, 0, 3); E(b_cond, "xs_1", "ne"); E(adds_imm8, 0, WIN2 - PK.WIN)
    a.label("xs_1"); E(cmp_reg, 1, 3); E(b_cond, "xs_2", "ne"); E(adds_imm8, 1, WIN2 - PK.WIN)
    a.label("xs_2"); E(b_w, L["c_copy2"])
    a.label("c_xrd2")                                    # DSP_READ(r0, r1): Y:WIN + k -> Y:WIN2 + k
    E(movw, 3, 0x8000 | PK.WIN); E(subs_reg, 3, 1, 3); E(cmp_imm, 3, PK.NW); E(b_cond, "xr_1", "hs"); E(adds_imm8, 1, WIN2 - PK.WIN)
    a.label("xr_1"); E(b_w, PK.DSP_READ)
    a.label("c_xyw2")                                    # c_ywin(r0 = 16-bit words, r1 = n <= NW) into WIN2 (the semaphore held by the caller)
    E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(movs_imm, 6, 0)
    a.label("xy_l")
    E(cmp_reg, 6, 5); E(b_cond, "xy_x", "hs")
    E(lsls_imm, 2, 6, 1); E(ldrh_reg, 1, 4, 2); E(lsls_imm, 1, 1, 16)
    E(movw, 2, 0x8000 | WIN2); E(adds_reg, 2, 2, 6); E(movs_imm, 0, 0); E(bl, PK.DSP_WRITE)
    E(adds_imm8, 6, 1); E(b, "xy_l")
    a.label("xy_x"); E(pop_list, [4, 5, 6], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    import ct_fw
    import fxdiag as FD
    BASE = ct_fw.APP_BASE
    xl = {k: int(v, 16) for k, v in report["xlanes"]["labels"].items()}
    pk = {k: int(v, 16) for k, v in report["packio"]["labels"].items()}
    assert PK.WIN == 0x3B40 and PK.NW == 64
    starts = sorted(v & ~1 for k, v in xl.items() if k.startswith("c_"))
    code, labels = arm_code(base_addr, dict(c_copy2=pk["c_copy2"]))
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    done = {}
    redir = {PK.DSP_READ: "c_xrd2", pk["c_copy"] & ~1: "c_xcw2", pk["c_ywin"] & ~1: "c_xyw2", pk["c_copy2"] & ~1: "c_xcs2"}
    order = [PK.DSP_READ, pk["c_copy"] & ~1, pk["c_ywin"] & ~1, pk["c_copy2"] & ~1]
    for fn in LED_FUNCS:
        lo = xl[fn] & ~1
        hi = next(s_ for s_ in starts if s_ > lo)
        n = [0, 0, 0, 0]
        for at in range(lo, hi - 2, 2):
            o = at - BASE
            h1, h2 = struct.unpack_from("<HH", img, o)
            if h1 & 0xF800 == 0xF000 and h2 & 0xD000 == 0xD000:
                t = FD.bl_target(img, at, BASE)
                if t in redir:
                    n[order.index(t)] += 1; img[o:o + 4] = bl(at, labels[redir[t]])
        assert tuple(n) == EXPECT[fn], (fn, n)
        done[fn] = n
    return labels, code, dict(win2=WIN2)
