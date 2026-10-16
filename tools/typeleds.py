"""SC39.5 (the user, 2026-10-12: «actualiza el indicador [del modo de filtro de drums], haciéndolo multicolor. Lo mismo para todos los knobs de
"selección múltiple / tipo"»): the knobs that pick one of a few types show the type as a colour, not as a brightness.

The MIDI engine's type knobs already did (vcf21.c_vtype: effect type, filter type, waveform, BITSYNC), as do the mode of the captured sample (K2)
and the source of the granular engine.  What was left, all on the Shift layer:
  * drums, Shift + K5 = the filter mode: DJ white, band-pass yellow, notch magenta, comb teal, EQ tilt green;
  * drums, Shift + K8 = the distortion type: 0 white, 1 yellow, 2 orange, 3 red;
  * the granular engine, Shift + K6 = the note mode: pitch white, slicer yellow, stretch teal.
The colour goes at full brightness in the knob's LED halfword ((brightness + 2) << 8 | colour, persist19's c_ledhook splits it), only while Shift
is held and, for the drums, not while Clear shows its red / blue.  Hooks: slot 7 of the drum macro handlers (in front of persist19's c_mhleds19)
and slot 7 of the note tracks' macro handlers (in front of the macro editor's).  Steady colour codes only (docs/NOTAS.md, the animated codes).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, ands_reg, b, b_cond, bl, cmp_imm, cmp_reg, ldrb_imm, ldrb_reg, lsls_imm, mov_reg, movs_imm, movt, movw, orrs_reg,  # noqa: E402
                   pop_list, push_list, strh_imm)
import persist19 as P19  # noqa: E402
import macroed as MC  # noqa: E402

MH_SLOT7 = P19.MH_SLOT7               # the drum macro handlers' LED slot
AC64_SLOT7 = MC.AC64_VT + 28          # the note tracks' macro handlers' LED slot
COL_FMODE = (0x01, 0x2D, 0x32, 0x4D, 0x17)


def use_fselstock():
    """With persist19.use_fselstock: the colours follow the stored value, whose 0 is now the stock EQ (green) and 4 the DJ filter (white)."""
    global COL_FMODE
    COL_FMODE = (0x17, 0x2D, 0x32, 0x4D, 0x01)
COL_DTYPE = (0x01, 0x2D, 0x2B, 0x45)
COL_NMODE = (0x01, 0x2D, 0x4D)
POS_FMODE, POS_DTYPE, POS_NMODE = 4, 7, 5     # K5, K8 (drums), K6 (granular)
CODE_FMODE, CODE_NMODE = 9, 26
FULL = (127 + 2) << 8


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    from thumb import raw
    t_fm, t_dt, t_nm = base, base + 5, base + 9
    E(raw, bytes(COL_FMODE) + bytes(COL_DTYPE) + bytes(COL_NMODE))
    def put(tab, pos):                                                                # buffer[pos] = FULL | tab[r0]; clobbers r0-r2
        imm32(1, tab); E(ldrb_reg, 0, 1, 0); imm32(1, FULL); E(orrs_reg, 0, 1); E(strh_imm, 0, 5, 2 * pos)

    # ---- c_tdleds (the drum macro handlers' slot 7: handler -> the buffer): Shift held = the filter mode and the distortion type as colours
    a.label("c_tdleds")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(bl, prev["dleds"]); E(mov_reg, 5, 0)
    E(movs_imm, 6, 0)
    a.label("td_f")
    E(mov_reg, 0, 6); E(bl, L["c_mh"]); E(cmp_reg, 0, 4); E(b_cond, "td_hit", "eq")
    E(adds_imm8, 6, 1); E(cmp_imm, 6, 4); E(b_cond, "td_f", "lo"); E(b, "td_x")
    a.label("td_hit")
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "td_x", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_clr_held"]); E(cmp_imm, 0, 0); E(b_cond, "td_x", "ne")
    E(mov_reg, 0, 6); E(movs_imm, 1, CODE_FMODE); E(bl, L["c_dget"])
    E(mov_reg, 2, 0); E(adds_imm8, 2, 1); E(b_cond, "td_d", "eq")                      # (no value)
    E(movs_imm, 1, 7); E(ands_reg, 0, 1); E(cmp_imm, 0, 4); E(b_cond, "td_m", "ls"); E(movs_imm, 0, 4)
    a.label("td_m"); put(t_fm, POS_FMODE)
    a.label("td_d")
    E(mov_reg, 0, 6); E(bl, L["c_xt_get"]); E(movs_imm, 1, 3); E(ands_reg, 0, 1); put(t_dt, POS_DTYPE)
    a.label("td_x"); E(mov_reg, 0, 5); E(pop_list, [3, 4, 5, 6, 7], pc=True)

    # ---- c_tgleds (the note tracks' macro handlers' slot 7): the granular page with Shift held = the note mode as a colour
    a.label("c_tgleds")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(bl, prev["gleds"]); E(mov_reg, 5, 0)
    E(mov_reg, 0, 4); E(bl, L["c_vtrack"]); E(mov_reg, 6, 0); E(cmp_imm, 6, 0xFF); E(b_cond, "tg_x", "eq")
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "tg_x", "eq")
    E(mov_reg, 0, 6); E(bl, L["c_grpg"]); E(cmp_imm, 0, 0); E(b_cond, "tg_x", "eq")
    E(mov_reg, 0, 6); E(movs_imm, 1, CODE_NMODE); E(bl, L["c_vvaddr"]); E(ldrb_imm, 0, 0, 0)
    E(cmp_imm, 0, 2); E(b_cond, "tg_m", "ls"); E(movs_imm, 0, 0)
    a.label("tg_m"); put(t_nm, POS_NMODE)
    a.label("tg_x"); E(mov_reg, 0, 5); E(pop_list, [3, 4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; slot 7 of the drum macro handlers and of the note tracks' macro handlers."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a: struct.unpack_from("<I", img, a - BASE)[0]
    lab = lambda sec, n: int(report[sec]["labels"][n], 16)
    L = dict(c_mh=lab("sc18", "c_mh"), c_shift=lab("sc15", "c_shift"), c_clr_held=lab("persist19", "c_clr_held"), c_dget=lab("persist19", "c_dget"),
             c_xt_get=lab("persist19", "c_xt_get"), c_vtrack=lab("vcf20", "c_vtrack"), c_grpg=lab("vcf20", "c_grpg"), c_vvaddr=lab("vcf20", "c_vvaddr"))
    prev = dict(dleds=u(MH_SLOT7) & ~1, gleds=u(AC64_SLOT7) & ~1)
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    struct.pack_into("<I", img, MH_SLOT7 - BASE, labels["c_tdleds"] | 1)
    struct.pack_into("<I", img, AC64_SLOT7 - BASE, labels["c_tgleds"] | 1)
    return labels, code, prev
