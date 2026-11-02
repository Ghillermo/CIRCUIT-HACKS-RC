"""SC50.4 / RC4.06 (a fix; the user, 2026-11-02, on the chord screen with the arpeggiator on: «con la pista muteada en mixer (pad apagado) no suena»): the input's arpeggio
goes on while its track is muted in the Mixer.

Playing, the arpeggio steps from the player's slot 2 (arp.c_arplay), and the players' tick (0x0804A5C6) skips the step of a muted track (0x0804A632, the branch rollers.use_mute
takes): the first note sounded and nothing more.  Now that branch -> c_armute, in front of rollers' c_rlmute: a note track muted while playing (r5 clear, as there) with an
arpeggio of the input running adds its tick to the same accumulator (6 a tick: a step's six micro steps add the ticks a step) and takes its step by hand (c_arlstep with 0: the
player's note interface, each note stopped by the next), because a stock gated note would wait for the note-offs of the tick that is skipped.  It stays on the grid; the sequence
of the muted track stays silent, as always.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import Asm, adds_imm8, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldrb_imm, lsls_imm, mov_reg, movs_imm, muls, pop_list, push_list, raw, subs_reg  # noqa: E402
import arp as A  # noqa: E402
import rollers as R  # noqa: E402


def ldrb_w(rt, rn, off): return h(0xF890 | rn) + h(rt << 12 | off)
def strb_w(rt, rn, off): return h(0xF880 | rn) + h(rt << 12 | off)


def arm_code(base, L):
    a = Asm(base)
    E = a.emit
    ACC = A.D_EXT + 6
    # ---- c_armute (the muted branch of the players' tick, in front of c_rlmute: r4 = the player, r5 = the step's other flag)
    a.label("c_armute")
    E(push_list, [0, 1, 2, 3, 4, 5, 6, 7], lr=True)
    E(cmp_imm, 5, 0); E(b_cond, "am_x", "ne")                                            # (r5 clear here = muted: the branch is taken for one or the other)
    E(mov_reg, 0, 4); E(bl, L["c_artrk"]); E(cmp_imm, 0, 3); E(b_cond, "am_x", "hi"); E(mov_reg, 7, 0)
    E(movs_imm, 1, 1); E(bl, L["c_arst"]); E(cmp_imm, 0, 0); E(b_cond, "am_x", "eq"); E(mov_reg, 6, 0)
    E(ldrb_imm, 0, 6, A.S_FL); E(lsls_imm, 0, 0, 31); E(b_cond, "am_x", "pl")
    E(mov_reg, 0, 6); E(bl, L["c_arG"]); E(mov_reg, 5, 0)                                # the groove's factor (sixths)
    E(mov_reg, 0, 7); E(bl, L["c_arRt"]); E(muls, 5, 0)                                  # r5 = an arpeggio step, in sixths of a tick
    E(raw, ldrb_w(0, 6, ACC)); E(cmp_reg, 0, 5); E(b_cond, "am_a", "lo")
    E(subs_reg, 0, 0, 5); E(raw, strb_w(0, 6, ACC))
    E(mov_reg, 0, 7); E(movs_imm, 1, 0); E(bl, L["c_arlstep"])
    a.label("am_a")
    E(raw, ldrb_w(0, 6, ACC)); E(adds_imm8, 0, 6); E(raw, strb_w(0, 6, ACC))             # (below a step of 216 at most: no overflow)
    a.label("am_x"); E(pop_list, [0, 1, 2, 3, 4, 5, 6, 7])
    E(raw, h(0xF85D) + h(0xEB04))                                                        # ldr.w lr, [sp], #4
    E(b_w, L["c_rlmute"])
    return a.assemble()


def install(img, report, base_addr):
    import ct_fw
    BASE = ct_fw.APP_BASE
    L = {k: int(report["arp"]["labels"][k], 16) for k in ("c_artrk", "c_arst", "c_arG", "c_arRt", "c_arlstep")}
    L["c_rlmute"] = int(report["rollers"]["labels"]["c_rlmute"], 16)
    code, labels = arm_code(base_addr, L)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert bytes(img[R.MUTE_AT - BASE:R.MUTE_AT - BASE + 4]) == b_w(R.MUTE_AT, L["c_rlmute"])
    img[R.MUTE_AT - BASE:R.MUTE_AT - BASE + 4] = b_w(R.MUTE_AT, labels["c_armute"])
    return labels, code, dict(c_rlmute=L["c_rlmute"])
