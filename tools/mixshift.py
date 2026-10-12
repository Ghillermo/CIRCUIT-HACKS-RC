"""SC38 (the user, 2026-10-11: «Nueva característica en el mixer: shift+derecha en un knob establece el canal a 100. Shift+izquierda lo pone a 0»): in the Mixer
view, on the levels page, Shift + a knob turned right = that track's level to 100, turned left = 0.

What it does not take from anyone (checked on the original firmware and on SC37.9, in emulation and in the code):
  * the stock Mixer knob handler (MIX_VT slot 4 = 0x080466C4) does not look at Shift: Shift + knob moved the level exactly as the plain knob;
    Clear + knob (left = delete the knob's automation, right = its default) is read from the view's own store [view + 0x74] and is left alone here;
  * the pan page (byte [view + 0xAD] = 1, Octave down in the Mixer view; Octave up = the levels page, 0x08033648 / 0x08033688) keeps the stock pan knobs;
  * Master FX (Mixer pressed twice, c_gact) has its own knobs (c_gknob) and is not touched;
  * nothing of the firmware used Shift + a Mixer knob (the chain: nrpn28.c_ngknob -> build_sc17.c_gknob -> the stock).
The level goes through the stock handler as a turn of (target - level): the same clamp, write, MIDI out and automation recording as a real turn.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, ldr_imm, ldrb_imm, lsls_imm, mov_reg, movs_imm, pop_list, push_list, raw, h,  # noqa: E402
                   subs_reg, ldrb_w)

MIX_VT = 0x0805A668                   # the Mixer view: slot 4 = its knobs
PARAM_GET = 0x0803542C
O_LEVELS, O_CLEAR, O_PAGE = 0x6C, 0x74, 0xAD   # the view: levels store, the held Clear store, the page (0 levels, 1 pans)
LEVEL_UP, LEVEL_DOWN = 100, 0


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    # ---- c_mxsh (view, knob, delta): Shift + a level knob = the level to 100 (right) / 0 (left); everything else as before
    a.label("c_mxsh")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 6, 2)
    a.emit(bl, L["c_shift"]); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "mx_fwd", "eq")
    a.emit(bl, L["c_gact"]); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "mx_fwd", "ne")                  # Master FX: its own knobs
    a.emit(cmp_imm, 5, 8); a.emit(b_cond, "mx_fwd", "hs")
    a.emit(ldrb_w, 0, 4, O_PAGE); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "mx_fwd", "ne")                # the pan page: stock
    a.emit(ldr_imm, 0, 4, O_CLEAR); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 0, 0, 0)
    a.emit(lsls_imm, 0, 0, 31); a.emit(b_cond, "mx_fwd", "mi")                                         # Clear held: the stock's Clear
    a.emit(cmp_imm, 6, 0); a.emit(b_cond, "mx_fwd", "eq"); a.emit(b_cond, "mx_up", "gt")              # (movs sets the flags: decide first)
    a.emit(movs_imm, 7, LEVEL_DOWN); a.emit(b, "mx_t")
    a.label("mx_up"); a.emit(movs_imm, 7, LEVEL_UP)
    a.label("mx_t")
    a.emit(ldr_imm, 0, 4, O_LEVELS); a.emit(mov_reg, 1, 5); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 0, 0, 0)
    a.emit(subs_reg, 6, 7, 0); a.emit(b_cond, "mx_fwd", "ne")                                            # the turn that lands on the target
    a.emit(raw, popw([4, 5, 6, 7], lr=True)); a.emit(raw, h(0x4770))                                    # already there: nothing
    a.label("mx_fwd")
    a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(mov_reg, 2, 6)
    a.emit(raw, popw([4, 5, 6, 7], lr=True)); a.emit(b_w, prev)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the Mixer view's slot 4 -> c_mxsh (in front of whatever was there)."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    L = dict(c_shift=int(report["sc15"]["labels"]["c_shift"], 16), c_gact=int(report["sc17"]["labels"]["c_gact"], 16))
    prev = struct.unpack_from("<I", img, MIX_VT + 0x10 - BASE)[0] & ~1
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    struct.pack_into("<I", img, MIX_VT + 0x10 - BASE, labels["c_mxsh"] | 1)
    return labels, code, prev
