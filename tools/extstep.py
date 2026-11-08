"""SC54 (the user, 2026-11-07, on the Setup view's Note toggle, the external keyboard into the arpeggiator: «new co-existing feature: while "MIDI to
internal" is on, holding a step and playing notes on an external MIDI controller, saves the notes in the step the same way they do when you hold a
step and play pads»): with that toggle on (arpx's c_xtog), an external note-on on the channel of Synth 1 / 2 or MIDI 1 / 2 while a step is held in
that track's view = the stock's own entry of a pad played with a step held, 0x0804B094(view, note, velocity) (the note added to the held step's
edit store, the step's gate or one step for the first one, the commit to the pattern; stepgate's fixed length / gate by press apply there too);
then the note goes on as before (it sounds, through the arpeggiator when that is on).  Internal injections are left alone.

The outermost head of the MIDI-in listener's note-on (0x080592E0 + 0, this, track, note, velocity), in front of arpx's.  No RAM.  In the hole."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import Asm, b_cond, b_w, bl, cmp_imm, h, ldr_imm, ldr_sp, ldrb_imm, movs_imm, movt, movw, muls, adds_reg, raw  # noqa: E402

LIS_VT = 0x080592E0
ADDNOTE = 0x0804B094
VIEW0, VIEW_SZ = 0x200412E0, 0x2F4
PARAM_GET = 0x0803542C


def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    # ---- c_esin (the listener's note-on: this, track, note, velocity)
    a.label("c_esin")
    E(cmp_imm, 1, 3); E(b_cond, "es_f", "hi"); E(cmp_imm, 3, 0); E(b_cond, "es_f", "eq")
    E(raw, pushw([0, 1, 2, 3, 4], lr=True))                                             # 6 words: [sp] this, + 4 track, + 8 note, + 12 velocity
    E(bl, L["c_xtog"]); E(cmp_imm, 0, 0); E(b_cond, "es_p", "eq")
    E(bl, L["c_xinj"]); E(cmp_imm, 0, 0); E(b_cond, "es_p", "ne")
    E(ldr_sp, 0, 4); E(movw, 1, VIEW_SZ); E(muls, 0, 1); imm32(1, VIEW0); E(adds_reg, 4, 0, 1)   # r4 = the track's view
    E(ldr_imm, 0, 4, 0x2C); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "es_p", "eq")   # a step held
    E(raw, h(0x4620)); E(ldr_sp, 1, 8); E(ldr_sp, 2, 12); E(bl, ADDNOTE)               # mov r0, r4: the stock's entry, as a pad
    a.label("es_p"); E(raw, popw([0, 1, 2, 3, 4], lr=True))
    a.label("es_f"); E(b_w, prev["on"])
    return a.assemble()


def install(img, report, base_addr):
    """hole.add, after arpx: the outermost head of the listener's note-on."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = dict(c_xtog=lab("arpx", "c_xtog"), c_xinj=lab("arpx", "c_xinj"))
    prev = dict(on=u(LIS_VT) & ~1)
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4: img += bytes([0xFF])
    struct.pack_into("<I", img, LIS_VT - BASE, labels["c_esin"] | 1)
    return labels, code, prev
