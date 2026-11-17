"""SC57.2 / Beta 5.57 (the user, 2026-11-13: «Pre-listen on note-flip is broken. All pads produce the same note», «A drum track», «Stopped»): the step
flip's stopped pre-listen (jumpx.c_jsa) on a drum target played the drum's selected sample on every step: a step's sample flip was not heard.

Now the drum branch's `ldrb.w r1, [r4, #0x58]` (the hit's note) is a call of c_jfl: on the press, a step with a sample flip (pattern + 0x40 + step,
0xFF = none) sets that sample through the player's setter (drumarp.c_dasmp, as the stock's sample flip and the drum arpeggio); on the release, the
drum's selected sample again (PARAM_GET([player + 0x5C], 0), as drumarp.c_daend).  A step without a flip = the selected sample, as before.

In dspz's gap (dspz.add)."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import Asm, adds_imm8, b_cond, bl, cmp_imm, h, ldr_imm, ldrb_imm, ldrb_reg, mov_reg, movs_imm, pop_list, push_list, raw  # noqa: E402

PARAM_GET = 0x0803542C
SITE = bytes.fromhex("94f85810")                              # c_jsa's drum branch: ldrb.w r1, [r4, #0x58]
USE_SEL = False                                               # SC57.8 / Beta 5.63 (use_sel)


def use_sel():
    """SC57.8 / Beta 5.63 (the 2026-11-14 bug hunt, JR-6): a press on a step without a flip sets the drum's selected sample too (before: with a
    flipped step's pad still held, a second pad on a step without a flip sounded the first one's flip).  The no-flip branch goes to the release's
    path (the selected sample, PARAM_GET([player + 0x5C], 0)): the same bytes, one branch target, 0 B."""
    global USE_SEL
    USE_SEL = True


def ldrbw(rt, rn, off): return h(0xF890 | rn) + h(rt << 12 | off)


def arm_code(base, L):
    a = Asm(base)
    E = a.emit
    # ---- c_jfl (from c_jsa: r0 = the drum's pattern, r2 = the step's velocity, r4 = the player, r5 = the step, r6 = on, r7 = the drum)
    #      -> r1 = the hit's note, r2 kept
    a.label("c_jfl")
    E(push_list, [2], lr=True)
    E(adds_imm8, 0, 0x40); E(ldrb_reg, 1, 0, 5); E(cmp_imm, 1, 0xFF); E(b_cond, "jf_r" if USE_SEL else "jf_x", "eq")   # the step's sample flip
    E(cmp_imm, 6, 0); E(b_cond, "jf_s", "ne")
    if USE_SEL: a.label("jf_r")                                                                  # (use_sel) no flip: the selected sample, also on a press
    E(ldr_imm, 0, 4, 0x5C); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 1, 0, 0)            # the release: the selected sample again
    E(cmp_imm, 1, 0xFF); E(b_cond, "jf_x", "eq")
    a.label("jf_s")
    E(mov_reg, 0, 7); E(bl, L["c_dasmp"])
    a.label("jf_x")
    E(raw, ldrbw(1, 4, 0x58)); E(pop_list, [2], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """Appended at the end (dspz.add moves it into the gap); c_jsa's drum note load becomes a call."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    L = dict(c_dasmp=int(report["drumarp"]["labels"]["c_dasmp"], 16))
    code, labels = arm_code(base_addr, L)
    img += code
    while len(img) % 4:
        img += bytes([0xFF])
    lab = report["jumpx"]["labels"]
    d0, d1 = int(lab["ja_d"], 16), int(lab["ja_c"], 16)
    seg = bytes(img[d0 - BASE:d1 - BASE])
    k = seg.find(SITE); assert k >= 0 and seg.find(SITE, k + 1) < 0, "c_jsa's drum note load not found once"
    at = d0 + k
    img[at - BASE:at - BASE + 4] = bl(at, labels["c_jfl"])
    return labels, code, dict(site=at)
