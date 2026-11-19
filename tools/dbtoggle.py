"""Alpha 7.06 (the user, 2026-11-18: «Pages (shift+tracks 1-4) exit wrong when they are opened and shift+any track is pressed again» -> «Toggle:
exit»): Shift + Synth 1 / 2 / MIDI 1 / 2 (dblpress: what pressing the track twice does) with that track's page already on the screen (the
controller's sub-mode = 9 x track, its Preset level: the synth's source view or the MIDI track's Preset view) = a plain press of the track
(Shift off for the press, put back after): back to its Note view.  Before, dblpress ran the double press again and the page stayed.  Shift +
another track: unchanged (that track's page).  Same conditions as dblpress (not in the Setup view, no Clear / Duplicate held, not with the MIDI
track's CC editor open).  The outermost head of the button press (0x08033320), in front of dblpress; no RAM."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import Asm, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, mov_reg, movs_imm, muls, pop_list, push_list, raw, strb_imm, subs_imm8  # noqa: E402
import srcview as SV  # noqa: E402

PARAM_GET = 0x0803542C


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def ldrb_w(rt, rn, off): return h(0xF890 | rn) + h(rt << 12 | off)


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    a.label("c_dbt")
    E(push_list, [0, 1, 2, 4, 5, 6], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(cmp_imm, 5, 3); E(b_cond, "dt_p", "hi")
    E(ldr_imm, 0, 4, 0xC); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(mov_reg, 6, 0)       # r6 = the Shift byte
    E(ldrb_imm, 0, 6, 0); E(cmp_imm, 0, 0); E(b_cond, "dt_p", "eq")
    E(raw, ldrb_w(0, 4, SV.S_CUR)); E(movs_imm, 1, 9); E(muls, 1, 5); E(cmp_reg, 0, 1); E(b_cond, "dt_p", "ne")   # its page on the screen
    E(bl, L["c_dbok"]); E(cmp_imm, 0, 0); E(b_cond, "dt_p", "eq")
    E(cmp_imm, 5, 2); E(b_cond, "dt_g", "lo")
    E(mov_reg, 0, 5); E(subs_imm8, 0, 2); E(bl, L["c_edact"]); E(cmp_imm, 0, 0); E(b_cond, "dt_p", "ne")   # its CC editor open
    a.label("dt_g")
    E(ldrb_imm, 0, 6, 0); E(push_list, [0]); E(movs_imm, 0, 0); E(strb_imm, 0, 6, 0)  # Shift off for the press
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, SV.BTN); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, SV.BTN_REL)
    E(ldr_imm, 0, 4, 0xC); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(pop_list, [1]); E(strb_imm, 1, 0, 0)   # Shift back
    E(pop_list, [0, 1, 2, 4, 5, 6], pc=True)
    a.label("dt_p"); E(raw, popw([0, 1, 2, 4, 5, 6], lr=True)); E(b_w, prev["btn"])
    return a.assemble()


def install(img, report, base_addr):
    """Appended at the end (dspz.add moves it into a gap when it fits); the outermost head of the button press."""
    import ct_fw
    import mpatch as MP
    BASE = ct_fw.APP_BASE
    L = dict(c_dbok=int(report["dblpress"]["labels"]["c_dbok"], 16), c_edact=int(report["vcf20"]["labels"]["c_edact"], 16))
    prev = dict(btn=MP.bw_target(img, SV.BTN, BASE))
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    img[SV.BTN - BASE:SV.BTN - BASE + 4] = b_w(SV.BTN, labels["c_dbt"])
    return labels, code, prev


def append(img, report):
    """The RC builds: appended at the image's end."""
    import ct_fw
    import build_shared_channels as sc
    labels, code, prev = install(img, report, (ct_fw.APP_BASE + len(img) + 3) & ~3)
    report["dbtoggle"] = dict(arm_start=hex(int(labels["c_dbt"])), labels={k: hex(v) for k, v in labels.items()}, prev={k: hex(v) for k, v in prev.items()},
                              listing=sc.disasm(bytes(code), int(labels["c_dbt"])))
