"""SC45.1 (the user, 2026-10-20: «ajuste: cuando el track está parado (desactivado mediante pad en mixer) y el modo Record amarillo, tocar los steps
durante la grabación los reproduce y envía, pero no los escribe en la pista parada (sólo en la que está sonando). Esto permite usar la pista como
Chord bank sin que se escriba nada en el banco»): with the recording of the internal routes on (fxsess: Record in the Setup view, yellow), the
recorder writes nothing into a note track (Synth 1 / 2, MIDI 1 / 2) that is muted in the Mixer.

A step pad of a track view auditions the step through the live-note path (0x0804B580 -> 0x0804B07A): the notes sound, go out on the track's
channel and, on a channel shared with Synth 1 / 2, are injected there (SC05); with Record on the recorder took them twice: into the tapped track
(at the step playing: the bank got written) and, with the toggle, into the synth.  Now the muted track keeps its steps and the synth that plays
gets them.  Its automation lanes too (the step's lane values reach the automation gate while it is auditioned).

The stock's three recorder gates (0x0802E56A note on (rec, note, vel, track), 0x0802E5CC note off (rec, note, track), 0x0802E62C automation
(rec, id, value)) start with a b.w into fxsess's heads; ours go in front: the recorder index t = the track (0..3; 0x10 = the drums: left alone)
or, for the automation, the stock's table 0x08059080 (two bytes an id: recorder index, lane; 0xFF = none); t < 4, the toggle on and the Mixer's
mute of t set (parameter 0 of [[Mixer + 0x68] + [Mixer + 0x60] x t], the store the Mixer's track pads toggle, 0x08046626) -> return 1 without
recording (as SC05's gate does for an injected message); else the chain as before.  Nothing new in RAM; in the hole (it only reads).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_reg, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, ldrb_reg, ldrh_imm, lsls_imm, mov_reg,  # noqa: E402
                   movs_imm, movt, movw, muls, pop_list, push_list, raw)
import fxsess as FS  # noqa: E402
import mpatch as MP  # noqa: E402

MIX_VIEW, PARAM_GET = 0x200447D4, 0x0803542C
AUTO_TAB = 0x08059080                                   # the automation gate's table: [2 id] = recorder index, [2 id + 1] = lane
GATE_ON, GATE_OFF, GATE_AUTO = FS.GATES                 # (0x0802E56A, 0x0802E5CC, 0x0802E62C)
TRACK_REG = {GATE_ON: 3, GATE_OFF: 2}                   # where each note gate has its track
N_NOTE = 4                                              # recorder indices 0..3 = Synth 1, Synth 2, MIDI 1, MIDI 2 (= the Mixer's pads 1-4)
BX_LR = h(0x4770)


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, prev):
    a = Asm(base); E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)

    # ---- c_mbmuted(r0 = recorder index) -> r0 = 1 if that note track is muted in the Mixer, else 0
    a.label("c_mbmuted")
    E(cmp_imm, 0, N_NOTE); E(b_cond, "mm_no", "cs")
    E(push_list, [4], lr=True)
    imm32(1, MIX_VIEW); E(ldr_imm, 2, 1, 0x60); E(ldr_imm, 3, 1, 0x68)
    E(muls, 2, 0); E(adds_reg, 3, 3, 2); E(ldr_imm, 0, 3, 0)                 # the store [[view + 0x68] + [view + 0x60] x t]
    E(cmp_imm, 0, 0); E(b_cond, "mm_z", "eq")
    E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(cmp_imm, 0, 0); E(b_cond, "mm_z", "eq"); E(movs_imm, 0, 1)
    a.label("mm_z"); E(pop_list, [4], pc=True)
    a.label("mm_no"); E(movs_imm, 0, 0); E(raw, BX_LR)

    # ---- c_mbon(r0 = recorder index) -> r0 = 1 if the gate must not record: the toggle on and that note track muted
    a.label("c_mbon")
    E(push_list, [4], lr=True)
    E(mov_reg, 4, 0)
    imm32(1, FS.SETUP_OBJ + FS.REC_OFF); E(ldrh_imm, 1, 1, 0); E(movw, 2, FS.REC_ON); E(cmp_reg, 1, 2); E(b_cond, "mo_no", "ne")
    E(mov_reg, 0, 4); E(bl, "c_mbmuted"); E(pop_list, [4], pc=True)
    a.label("mo_no"); E(movs_imm, 0, 0); E(pop_list, [4], pc=True)

    # ---- the gates' heads (the stock gate's b.w lands here; r0-r3 = its arguments, lr = its caller)
    for g in FS.GATES:
        n = f"{g:x}"
        a.label(f"c_mbgate_{n}")
        E(push_list, [0, 1, 2, 3, 4], lr=True)
        if g in TRACK_REG:
            E(mov_reg, 0, TRACK_REG[g])                                         # the track (0x10 = the drums: >= 4, left alone)
        else:
            imm32(0, AUTO_TAB); E(lsls_imm, 1, 1, 1); E(ldrb_reg, 0, 0, 1)      # the id's recorder index (0xFF = none)
        E(bl, "c_mbon"); E(cmp_imm, 0, 0)
        E(raw, popw([0, 1, 2, 3, 4], lr=True))                                  # (flags kept)
        E(b_cond, f"mg_{n}", "eq")
        E(movs_imm, 0, 1); E(raw, BX_LR)                                        # not recorded (as SC05's gate for an injected message)
        a.label(f"mg_{n}"); E(b_w, prev[g])
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the three gates' b.w re-pointed (their old targets = fxsess's heads, kept as the next in the chain)."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    prev = {g: MP.bw_target(img, g, BASE) for g in FS.GATES}
    for g in FS.GATES:
        assert prev[g] == lab("fxsess", f"c_fsgate_{g:x}"), (hex(g), hex(prev[g]))
    code, labels = arm_code(base_addr, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    for g in FS.GATES:
        img[g - BASE:g - BASE + 4] = b_w(g, labels[f"c_mbgate_{g:x}"])
    return labels, code, {f"gate_{g:x}": t for g, t in prev.items()}
