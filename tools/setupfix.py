"""SC41.5 / RC0.9.2: Synth 1 / Synth 2 can be chosen in the Setup view again.

Found while testing pgmch (2026-10-14): srcview's c_bentry (SC19.1 on, the «second press» of a Synth button = the synth's source view) compares the
pressed Synth button with [ctrl + 0x152] (9 * track + sub-mode of the last track view shown) and turns the press into a tap on Preset (id 8).  The
Setup view (the controller's mode 8) leaves [ctrl + 0x152] as it was: after entering the Setup view from Synth 1's (or Synth 2's) track view, pressing
that Synth button there reached the Setup view as Preset, and that synth's MIDI channel could not be shown or changed (in emulation: the stock
gives the Setup view's button slot id 0, the builds since SC19.1 id 8).

Fix: the `ldrb.w r1, [r4, #0x152]` of c_bentry's «second press» test -> bl c_sxcur: r1 = [ctrl + 0x152], or 0xFF (no track view) in the Setup mode.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import Asm, b_cond, bl, cmp_imm, ldr_imm, ldrb_imm, ldrb_w, movs_imm, pop_list, push_list  # noqa: E402

PARAM_GET = 0x0803542C
MODE_STORE, MODE_SETUP, S_CUR = 0x14, 8, 0x152
AT = 6                                                # the ldrb.w after be_closed's `cmp r5, #1` and its branch to be_stock


def arm_code(base):
    a = Asm(base)
    E = a.emit
    # ---- c_sxcur (r4 = the controller) -> r1 = [ctrl + 0x152], 0xFF in the Setup mode; clobbers r0, r2, r3
    a.label("c_sxcur")
    E(push_list, [], lr=True)
    E(ldr_imm, 0, 4, MODE_STORE); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(movs_imm, 1, 0xFF); E(cmp_imm, 0, MODE_SETUP); E(b_cond, "sx_x", "eq")
    E(ldrb_w, 1, 4, S_CUR)
    a.label("sx_x"); E(pop_list, [], pc=True)
    return a.assemble()


def site(report):
    return int(report["srcview"]["labels"]["be_closed"], 16) + AT


def install(img, report, base_addr):
    import ct_fw
    BASE = ct_fw.APP_BASE
    at = site(report)
    assert bytes(img[at - BASE:at - BASE + 4]) == ldrb_w(1, 4, S_CUR), hex(at)
    code, labels = arm_code(base_addr)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    img[at - BASE:at - BASE + 4] = bl(at, labels["c_sxcur"])
    return labels, code, dict(site=at)
