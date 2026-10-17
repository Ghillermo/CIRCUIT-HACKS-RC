"""SC42.4 (the user, 2026-10-16): micro-step rollers in the drums' Note view.

    «on Drum's Note Expand view (press note twice after selecting a drum) we have some drum triggers.  Add microstep rollers to them.  Microstep rollers
    are dimly lit, same color than their column and symbolize each drum.  While a roller or combination of rollers is held, the sounds will trigger for
    each step at such microstep position (for example: pads 1, 9, 17, 5, 13 and 21 are microsteps 1, 2, 3, 4, 5 and 6 respectively and trigger drum 1)».

The stock (read in the firmware, emulated):
  * the drums' Note view (subview 9 x (4 + d) + 6 of the container; class 0x0805AD44, drumnote.py): pads 29-32 = drums 1-4, 25-28 their copy
    (SC23.4: mirrored, 25 = drum 4); rows 1-3 empty;
  * the drum players (0x20040810 + 0x90 d, vtable 0x0805B72C): slot 2 = 0x08041252(this, pattern, step, micro step), called for every micro step while
    playing: the hit test 0x0804AA08(pattern base, step, micro step, random) (velocity <> 0, probability, bit micro step of [+ 0x60 + step]), then the
    note-on through the interface [this + 0x4C] (its slot 0: note [this + 0x58], velocity = [base + step]); [this + 0x59] = sounding (the interface's
    slot 1 stops it on the next step's micro step 0); a drum pattern is 0x6A8 bytes from [this + 0x48].

Ours:
  * rows 1-3 of the drums' Note view are the rollers: each column is the drum of its bottom pad (so with the mirror columns 1-4 are drums 4-1), the
    drum's left column = micro steps 1-3 (rows 1-3), its right column = 4-6; dim in the drum's colour, bright while held; held pads set bits of a mask
    per drum (the record's tail + 956 + d, RAM only, cleared when the view is left);
  * the drum players' slot 2 -> c_rlplay: the stock's, then on a micro step whose bit is held (and that the pattern does not hit already) a hit with
    the step's velocity (100 on an empty step) through the same interface: it sounds live and is not recorded.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldr_sp, ldrb_imm, ldrb_reg, lsls_imm, lsrs_imm,  # noqa: E402
                   mov_reg, movs_imm, movt, movw, muls, pop_list, push_list, raw, str_imm, str_sp, strb_imm, strb_reg, strh_imm, sub_sp_imm, add_sp_imm, subs_imm8, subs_reg)
from build_sc14 import udiv  # noqa: E402
import drumnote as DN  # noqa: E402

DP_VT, DP_PLAY = 0x0805B72C, 0x08041252
DP0, DP_SZ = 0x20040810, 0x90
HIT = 0x0804AA08
PAT_SZ = 0x6A8
NV_VT = 0x0805AD44                                         # the drums' Note view
SESSION_OBJ, TAIL, O_MASK = 0x2003D71C, 0x27024, 956
MGR, CONT = 0x20040B10, 0x20040DB8
VEL_EMPTY = 100
V2 = False                                                 # SC42.5 (use_v2)
O_STAMP = 964                                              # (V2) the time the view's LEDs were last asked for
SEEN_MS = 200
TRANSPORT, PARAM_GET, HAL_TICK = 0x20011034, 0x0803542C, 0x2000081C


def use_v2():
    """SC42.5 (the user, 2026-10-16: «roller worked just once but wasn't recorded, won't work anymore»): the rollers are cleared when the view's
    LEDs have not been asked for in 200 ms (instead of comparing the container's subview); with Record armed a roller's hit is also written into
    the pattern (the micro step's bit of the step, and velocity 100 on an empty step), as a live drum hit would be."""
    global V2
    V2 = True


FREE = False                                               # SC42.7 (use_free)
SYNC = False                                               # SC43 (use_sync)


def use_sync():
    """SC43: a roller's hit recorded into the pattern also goes into the drum's edit store (drumstore.py): the stock's next commit (a probability
    edit, for one) put the old arrays back and the hit vanished."""
    global SYNC
    assert V2
    SYNC = True
O_FREE = 564                                               # (FREE) the clock: + 0 the next micro step's time (1/16 ms), + 4 its number 0..5, + 5 0xA7 = running
TICKS_TAB, TEMPO = 0x0805B8B8, 0x20011404


def use_free():
    """SC42.7 (the user, 2026-10-16: «modo roll (en drums): ahora funciona, hacer que funcione sin estar play pulsado»): with the transport stopped,
    the LED task plays the held rollers at the project's tempo and Drum 1's sync rate, on a clock that starts with the first roller held (micro step 1
    at once); velocity 100, not recorded.  RAM in the record's tail + 564..569 (free in the builds without stutdiag).  Needs use_v2."""
    global FREE
    FREE = True


NOTEOFF = False                                            # SC43.1 (use_noteoff)
O_OFF, OFF_MS = 664, 100                                   # (NOTEOFF) a drum's note-off time (ms, 0 = none), 4 B a drum


MUTE = False                                               # SC43.7 (use_mute)
MUTE_AT, MUTE_OLD, MUTE_BACK = 0x0804A632, bytes.fromhex("002004f13801"), 0x0804A638   # the muted branch of the players' tick (movs r0, #0; add.w r1, r4, #0x38)
TICK_TAB, MICRO_N = 0x08059218, 0x0804A2E8                 # the step's micro step of a tick by the sync index (24 B a row); the micro steps of a tick


def use_mute():
    """SC43.7 (the user, 2026-10-17: «durante la reproducción, los roller con pistas desactivadas en el pad mixer no suena»): the stock (emulated):
    a track muted in the Mixer has [player + 0x28] p0 = 1 (the Mixer's mute store), and the players' tick (0x0804A5C6) then skips the step
    (0x0804A714: its automation and its hits through slot 2, where c_rlplay lives): the rollers stopped with the track.  Now that branch
    (0x0804A632) -> c_rlmute: a drum player muted while playing (the step's flag r5 clear) runs only the rollers' part of the step (c_rlroll) for
    the micro steps of the tick, as 0x0804A714 finds them (TICK_TAB, 0x0804A2E8); every roller hit leaves its note-off (c_rloffset), which the
    LED task sends after 100 ms when its track is muted (playing and unmuted, the sequencer's next step does it).  Needs use_noteoff."""
    global MUTE
    assert NOTEOFF
    MUTE = True


def use_noteoff():
    """SC43.1 (the user, 2026-10-16: «en el roller, la fila inferior se ve parcialmente blanca (pads 27 al 30)»): a drum's note-on through its
    player's interface lights its two boxes of the Note view white (0x01, the palette + 0x148) until the note-off; playing, the stock sends it on
    the next step, but the hits of the rollers (and of the drum arpeggio) with the transport stopped never got one: the boxes stayed white and the
    drum's MIDI note hung.  Now such a hit leaves a note-off time (+ 100 ms) in the record's tail + 664 + 4 d (RAM, free in the builds without
    stutdiag; c_rloffset) and the LED task sends it (c_rlsweep); playing, the time is dropped (the sequencer's).  Needs use_free."""
    global NOTEOFF
    assert FREE
    NOTEOFF = True


DRUM_COL = (0x45, 0x2D, 0x49, 0x4D)                        # drums 1-4 (the bottom row's colours); + 1 = the dim one of the same family


def tables():
    """pad 0..23 -> drum (0..3), micro step (0..5)"""
    col_drum = [3 - c if DN.MIRROR else c for c in range(4)] + [0, 1, 2, 3]
    pd, pm = [], []
    for p in range(24):
        r, c = divmod(p, 8)
        d = col_drum[c]
        cols = sorted(k for k in range(8) if col_drum[k] == d)
        pd.append(d); pm.append(r + 3 * cols.index(c))
    return bytes(pd), bytes(pm)


def ldrbw(rt, rn, off): return h(0xF890 | rn) + h(rt << 12 | off)
def strbw(rt, rn, off): return h(0xF880 | rn) + h(rt << 12 | off)
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    pd, pm = tables()
    E(raw, pd + pm + bytes(DRUM_COL))
    t_pd, t_pm, t_col = base, base + 24, base + 48
    assert (base + 52) % 2 == 0

    # ---- c_rlm() -> r0 = the masks (the record's tail + 956), or 0; clobbers r1
    a.label("c_rlm")
    imm32(0, SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); E(cmp_imm, 0, 0); E(b_cond, "rm_x", "eq"); imm32(1, TAIL + O_MASK); E(adds_reg, 0, 0, 1)
    a.label("rm_x"); E(raw, h(0x4770))

    # ---- c_rlbit(r1 = pad 0..23) -> r0 = the drum's mask byte address, r1 = its bit; clobbers r2, r3 (0 when no record)
    a.label("c_rlbit")
    E(push_list, [4], lr=True); E(mov_reg, 4, 1)
    E(bl, "c_rlm"); E(cmp_imm, 0, 0); E(b_cond, "rb_x", "eq")
    imm32(2, t_pd); E(ldrb_reg, 3, 2, 4); E(adds_reg, 0, 0, 3)
    imm32(2, t_pm); E(ldrb_reg, 3, 2, 4); E(movs_imm, 1, 1); E(raw, h(0x4099))                     # lsls r1, r3
    a.label("rb_x"); E(pop_list, [4], pc=True)

    # ---- c_rlpad / c_rlrel (the drums' Note view slots 0 / 1: view, pad, ...): rows 1-3 = the rollers
    for name, setbit in (("c_rlpad", True), ("c_rlrel", False)):
        a.label(name)
        E(cmp_imm, 1, 24); E(b_cond, name + "_s", "hs")
        E(push_list, [4], lr=True)
        E(bl, "c_rlbit"); E(cmp_imm, 0, 0); E(b_cond, name + "_x", "eq")
        E(ldrb_imm, 2, 0, 0)
        E(raw, h(0x430A) if setbit else h(0x438A))                                                     # orrs r2, r1 / bics r2, r1
        E(strb_imm, 2, 0, 0)
        a.label(name + "_x"); E(pop_list, [4], pc=True)
        a.label(name + "_s"); E(b_w, prev["pad" if setbit else "rel"])

    # ---- c_rlleds (the drums' Note view slot 7: view) -> its LED buffer, rows 1-3 = the rollers (dim, bright while held)
    a.label("c_rlleds")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(bl, prev["leds"]); E(mov_reg, 5, 0)
    if V2:                                                                                             # the stamp
        E(bl, "c_rlm"); E(cmp_imm, 0, 0); E(b_cond, "rl_s", "eq"); imm32(1, HAL_TICK); E(ldr_imm, 1, 1, 0); E(str_imm, 1, 0, O_STAMP - O_MASK)
        a.label("rl_s")
    E(movs_imm, 4, 0)
    a.label("rl_l")
    E(mov_reg, 1, 4); E(bl, "c_rlbit"); E(mov_reg, 6, 0); E(mov_reg, 7, 1)
    imm32(2, t_pd); E(ldrb_reg, 3, 2, 4); imm32(2, t_col); E(ldrb_reg, 1, 2, 3); E(adds_imm8, 1, 1)                # dim
    E(cmp_imm, 6, 0); E(b_cond, "rl_w", "eq"); E(ldrb_imm, 0, 6, 0); E(raw, h(0x4238)); E(b_cond, "rl_w", "eq")   # tst r0, r7
    E(subs_imm8, 1, 1)                                                                                 # held: bright
    a.label("rl_w"); E(lsls_imm, 0, 4, 1); E(raw, h(0x5229))                                           # strh r1, [r5, r0]
    E(adds_imm8, 4, 1); E(cmp_imm, 4, 24); E(b_cond, "rl_l", "lo")
    E(mov_reg, 0, 5); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_rlplay (the drum players' slot 2: this, pattern, step, micro step): the stock's, then a roller's hit
    a.label("c_rlplay")
    E(push_list, [4, 5, 6, 7], lr=True); E(sub_sp_imm, 16)
    E(str_sp, 0, 0); E(str_sp, 1, 4); E(str_sp, 2, 8); E(str_sp, 3, 12)
    E(bl, DP_PLAY)
    if MUTE: a.label("rp_go")
    E(ldr_sp, 4, 0); imm32(1, DP0); E(subs_reg, 0, 4, 1); E(movs_imm, 1, DP_SZ); E(raw, udiv(6, 0, 1)); E(cmp_imm, 6, 3); E(b_cond, "rp_x", "hi")   # r6 = the drum
    E(bl, "c_rlm"); E(cmp_imm, 0, 0); E(b_cond, "rp_x", "eq"); E(ldrb_reg, 0, 0, 6)
    E(ldr_sp, 1, 12); E(raw, h(0x40C8)); E(movs_imm, 1, 1); E(raw, h(0x4208)); E(b_cond, "rp_x", "eq")          # lsrs r0, r1; tst r0, r1
    imm32(0, PAT_SZ); E(ldr_sp, 1, 4); E(muls, 0, 1); E(ldr_imm, 1, 4, 0x48); E(adds_reg, 7, 0, 1)              # r7 = the pattern
    E(mov_reg, 0, 7); E(ldr_sp, 1, 8); E(ldr_sp, 2, 12); E(ldr_imm, 3, 4, 4); E(bl, HIT); E(cmp_imm, 0, 0); E(b_cond, "rp_x", "ne")
    E(ldr_sp, 1, 8); E(ldrb_reg, 5, 7, 1); E(cmp_imm, 5, 0); E(b_cond, "rp_v", "ne"); E(movs_imm, 5, VEL_EMPTY)  # r5 = the velocity
    a.label("rp_v")
    E(raw, ldrbw(0, 4, 0x59)); E(cmp_imm, 0, 0); E(b_cond, "rp_on", "eq")                                       # a note sounding: off first
    E(ldr_imm, 0, 4, 0x4C); E(raw, ldrbw(1, 4, 0x58)); E(movs_imm, 2, 0); E(ldr_imm, 3, 0, 0); E(ldr_imm, 3, 3, 4); E(raw, h(0x4798))   # blx r3
    a.label("rp_on")
    E(ldr_imm, 0, 4, 0x4C); E(raw, ldrbw(1, 4, 0x58)); E(mov_reg, 2, 5); E(movs_imm, 3, 0); E(ldr_imm, 6, 0, 0); E(ldr_imm, 6, 6, 0); E(raw, h(0x47B0))   # blx r6
    E(movs_imm, 0, 1); E(raw, strbw(0, 4, 0x59))
    if MUTE: E(mov_reg, 0, 4); E(bl, "c_rloffset")                                                   # its note-off (the LED task: only when muted)
    if V2:                                                                                             # Record armed: into the pattern
        imm32(0, TRANSPORT); E(movs_imm, 1, 1); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "rp_x", "eq")
        E(ldr_sp, 1, 8); E(ldrb_reg, 0, 7, 1); E(cmp_imm, 0, 0); E(b_cond, "rp_m", "ne"); E(strb_reg, 5, 7, 1)   # an empty step: its velocity
        a.label("rp_m")
        E(adds_reg, 2, 7, 1); E(adds_imm8, 2, 0x60); E(ldrb_imm, 0, 2, 0); E(ldr_sp, 1, 12); E(movs_imm, 3, 1); E(raw, h(0x408B))   # lsls r3, r1
        E(raw, h(0x4318)); E(strb_imm, 0, 2, 0)                                                        # orrs r0, r3: the micro step's bit
        if SYNC: E(mov_reg, 0, 4); E(ldr_sp, 1, 8); E(mov_reg, 2, 7); E(bl, "c_rlsync")
    a.label("rp_x"); E(add_sp_imm, 16); E(pop_list, [4, 5, 6, 7], pc=True)
    if MUTE:
        # ---- c_rlroll (this, pattern, step, micro step): the rollers' part of c_rlplay alone (a muted track: no stock hit)
        a.label("c_rlroll")
        E(push_list, [4, 5, 6, 7], lr=True); E(sub_sp_imm, 16)
        E(str_sp, 0, 0); E(str_sp, 1, 4); E(str_sp, 2, 8); E(str_sp, 3, 12); E(b, "rp_go")
        # ---- c_rlmute (in place of the muted branch's movs r0, #0; add.w r1, r4, #0x38: r4 = the player, r5 = the step's other flag)
        a.label("c_rlmute")
        E(push_list, [0, 1, 2, 3, 4, 5, 6, 7], lr=True); E(sub_sp_imm, 8)
        E(cmp_imm, 5, 0); E(b_cond, "rmu_x", "ne")
        imm32(1, DP0); E(subs_reg, 0, 4, 1); E(movs_imm, 1, DP_SZ); E(raw, udiv(2, 0, 1)); E(cmp_imm, 2, 3); E(b_cond, "rmu_x", "hi")
        E(muls, 1, 2); E(cmp_reg, 1, 0); E(b_cond, "rmu_x", "ne")
        E(ldr_imm, 0, 4, 0x28); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "rmu_x", "eq")   # muted
        E(ldr_imm, 0, 4, 8); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 6, 0, 0)                    # r6 = the pattern
        E(ldr_imm, 0, 4, 8); E(movs_imm, 1, 1); E(bl, PARAM_GET); E(ldrb_imm, 7, 0, 0)                    # r7 = the step
        E(ldr_imm, 0, 4, 8); E(movs_imm, 1, 2); E(bl, PARAM_GET); E(ldr_imm, 5, 0, 0)                     # r5 = the tick
        E(ldr_imm, 0, 4, 0x10); E(movs_imm, 1, 1); E(bl, PARAM_GET); E(ldrb_imm, 1, 0, 0)                 # r1 = the sync index
        E(movs_imm, 2, 24); E(muls, 2, 1); imm32(3, TICK_TAB); E(adds_reg, 2, 2, 3); E(ldrb_reg, 3, 2, 5)  # r3 = the micro step
        E(cmp_imm, 3, 0xFF); E(b_cond, "rmu_x", "eq"); E(str_sp, 3, 0)
        E(movs_imm, 0, 1); E(str_sp, 0, 4)
        E(cmp_imm, 1, 3); E(b_cond, "rmu_l", "hs")
        E(mov_reg, 0, 5); E(bl, MICRO_N); E(str_sp, 0, 4); E(cmp_imm, 0, 1); E(b_cond, "rmu_x", "lt")
        a.label("rmu_l")
        E(mov_reg, 0, 4); E(mov_reg, 1, 6); E(mov_reg, 2, 7); E(ldr_sp, 3, 0); E(bl, "c_rlroll")
        E(ldr_sp, 3, 0); E(adds_imm8, 3, 1); E(str_sp, 3, 0); E(ldr_sp, 0, 4); E(subs_imm8, 0, 1); E(str_sp, 0, 4); E(b_cond, "rmu_l", "ne")
        a.label("rmu_x"); E(add_sp_imm, 8); E(pop_list, [0, 1, 2, 3, 4, 5, 6, 7])
        E(raw, h(0xF85D) + h(0xEB04))                                                                  # ldr.w lr, [sp], #4
        E(raw, MUTE_OLD); E(b_w, MUTE_BACK)

    # ---- c_rlledtask (the LED task calls: ctrl, frame): the chain; out of a drums' Note view the masks are cleared
    a.label("c_rlledtask")
    E(push_list, [3, 4], lr=True)
    E(bl, prev["ledtask"])
    if V2:                                                                                             # the view drawn in the last 200 ms: kept
        E(bl, "c_rlm"); E(cmp_imm, 0, 0); E(b_cond, "rt_x", "eq"); E(ldr_imm, 1, 0, O_STAMP - O_MASK)
        imm32(0, HAL_TICK); E(ldr_imm, 0, 0, 0); E(subs_reg, 0, 0, 1); imm32(1, SEEN_MS); E(cmp_reg, 0, 1); E(b_cond, "rt_k" if FREE else "rt_x", "ls")
    else:
        imm32(0, MGR); E(ldr_imm, 1, 0, 0x6C); imm32(2, CONT); E(cmp_reg, 1, 2); E(b_cond, "rt_z", "ne")
        E(raw, h(0xF890) + h(1 << 12 | 0x152))                                                          # ldrb.w r1, [r0, #0x152]
        for v in (42, 51, 60, 69): E(cmp_imm, 1, v); E(b_cond, "rt_x", "eq")
    a.label("rt_z")
    E(bl, "c_rlm"); E(cmp_imm, 0, 0); E(b_cond, "rt_x", "eq"); E(movs_imm, 1, 0); E(raw, h(0x6001))         # str r1, [r0]: the four masks
    if FREE: E(b, "rt_x"); a.label("rt_k"); E(bl, "c_rlfree")
    a.label("rt_x")
    if NOTEOFF: E(bl, "c_rlsweep")
    E(pop_list, [3, 4], pc=True)
    if SYNC:
        import drumstore
        drumstore.emit_sync(a, "c_rlsync")
    if FREE:
        zc = [0]
        INV = {"eq": "ne", "ne": "eq", "mi": "pl", "pl": "mi", "hs": "lo", "lo": "hs"}
        def bc(target, cond):
            zc[0] += 1; n = f"_f{zc[0]}"; E(b_cond, n, INV[cond]); E(b, target); a.label(n)
        # ---- c_rlhit(r0 = drum): a hit through its player's interface (off first if it sounds), velocity 100
        a.label("c_rlhit")
        E(push_list, [4, 5], lr=True)
        E(movs_imm, 1, DP_SZ); E(muls, 0, 1); imm32(1, DP0); E(adds_reg, 4, 0, 1)
        E(raw, ldrbw(0, 4, 0x59)); E(cmp_imm, 0, 0); E(b_cond, "rh_on", "eq")
        E(ldr_imm, 0, 4, 0x4C); E(raw, ldrbw(1, 4, 0x58)); E(movs_imm, 2, 0); E(ldr_imm, 3, 0, 0); E(ldr_imm, 3, 3, 4); E(raw, h(0x4798))   # blx r3
        a.label("rh_on")
        E(ldr_imm, 0, 4, 0x4C); E(raw, ldrbw(1, 4, 0x58)); E(movs_imm, 2, VEL_EMPTY); E(movs_imm, 3, 0); E(ldr_imm, 5, 0, 0); E(ldr_imm, 5, 5, 0); E(raw, h(0x47A8))   # blx r5
        E(movs_imm, 0, 1); E(raw, strbw(0, 4, 0x59))
        if NOTEOFF: E(mov_reg, 0, 4); E(bl, "c_rloffset")
        E(pop_list, [4, 5], pc=True)
        # ---- c_rlfree(): the transport stopped and a roller held: the micro steps due on our clock
        a.label("c_rlfree")
        E(push_list, [4, 5, 6, 7], lr=True)
        E(bl, "c_rlm"); E(cmp_imm, 0, 0); bc("rf_x", "eq"); E(mov_reg, 4, 0)                                 # r4 = the masks
        E(movw, 1, O_MASK - O_FREE); E(subs_reg, 5, 4, 1)                                                   # r5 = the clock
        E(ldr_imm, 0, 4, 0); E(cmp_imm, 0, 0); bc("rf_z", "eq")                                             # no roller held
        imm32(0, TRANSPORT); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); bc("rf_z", "ne")   # playing: the sequencer's
        imm32(0, HAL_TICK); E(ldr_imm, 6, 0, 0); E(lsls_imm, 6, 6, 4)                                      # r6 = now, 1/16 ms
        E(ldrb_imm, 0, 5, 5); E(cmp_imm, 0, 0xA7); E(b_cond, "rf_r", "eq")
        E(movs_imm, 0, 0xA7); E(strb_imm, 0, 5, 5); E(str_imm, 6, 5, 0); E(movs_imm, 0, 0); E(strb_imm, 0, 5, 4)   # the clock starts: micro step 1 now
        a.label("rf_r")
        imm32(0, DP0); E(ldr_imm, 0, 0, 0x10); E(movs_imm, 1, 1); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 7); E(b_cond, "rf_t", "ls"); E(movs_imm, 0, 3)
        a.label("rf_t"); E(lsls_imm, 0, 0, 2); imm32(1, TICKS_TAB); E(adds_reg, 0, 0, 1); E(ldr_imm, 7, 0, 0)    # r7 = the ticks a step
        imm32(0, TEMPO); E(movs_imm, 1, 1); E(bl, PARAM_GET); E(ldrb_imm, 1, 0, 0); E(cmp_imm, 1, 30); E(b_cond, "rf_b", "hs"); E(movs_imm, 1, 120)
        a.label("rf_b")
        E(movs_imm, 0, 6); E(muls, 1, 0); imm32(0, 40000); E(muls, 0, 7); E(raw, udiv(7, 0, 1))            # r7 = a micro step in 1/16 ms: 40000 tps / (6 BPM)
        E(movs_imm, 0, 6); E(push_list, [0])                                                                 # at most 6 a call
        a.label("rf_l")
        E(ldr_imm, 0, 5, 0); E(subs_reg, 0, 6, 0); bc("rf_e", "mi")                                          # not due yet
        E(ldrb_imm, 1, 5, 4)
        for d in range(4):
            E(ldrb_imm, 0, 4, d); E(raw, h(0x40C8)); E(lsls_imm, 0, 0, 31); E(b_cond, f"rf_n{d}", "pl")        # lsrs r0, r1
            E(push_list, [1]); E(movs_imm, 0, d); E(bl, "c_rlhit"); E(pop_list, [1])
            a.label(f"rf_n{d}")
        E(adds_imm8, 1, 1); E(cmp_imm, 1, 6); E(b_cond, "rf_k", "lo"); E(movs_imm, 1, 0)
        a.label("rf_k"); E(strb_imm, 1, 5, 4)
        E(ldr_imm, 0, 5, 0); E(adds_reg, 0, 0, 7); E(str_imm, 0, 5, 0)
        E(ldr_sp, 0, 0); E(subs_imm8, 0, 1); E(str_sp, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "rf_l", "ne")
        E(ldr_imm, 0, 5, 0); E(subs_reg, 0, 6, 0); E(b_cond, "rf_e", "mi"); E(str_imm, 6, 5, 0)            # still behind: from now
        a.label("rf_e"); E(pop_list, [0]); E(b, "rf_x")
        a.label("rf_z"); E(movs_imm, 0, 0); E(strb_imm, 0, 5, 5)                                            # stopped: the next roller starts the clock again
        a.label("rf_x"); E(pop_list, [4, 5, 6, 7], pc=True)
    if NOTEOFF:
        # ---- c_rloffset(r0 = a drum player): its note-off due in OFF_MS; clobbers r0-r3
        a.label("c_rloffset")
        E(push_list, [4], lr=True)
        imm32(1, DP0); E(subs_reg, 0, 0, 1); E(movs_imm, 1, DP_SZ); E(raw, udiv(4, 0, 1))                  # r4 = the drum
        E(bl, "c_rlm"); E(cmp_imm, 0, 0); E(b_cond, "ro_x", "eq")
        E(movw, 1, O_MASK - O_OFF); E(subs_reg, 0, 0, 1); E(lsls_imm, 4, 4, 2); E(adds_reg, 4, 0, 4)
        imm32(1, HAL_TICK); E(ldr_imm, 1, 1, 0); E(adds_imm8, 1, OFF_MS); E(cmp_imm, 1, 0); E(b_cond, "ro_s", "ne"); E(movs_imm, 1, 1)
        a.label("ro_s"); E(str_imm, 1, 4, 0)
        a.label("ro_x"); E(pop_list, [4], pc=True)
        # ---- c_rloff1(r0 = a drum player): its note-off when it sounds
        a.label("c_rloff1")
        E(push_list, [4], lr=True); E(mov_reg, 4, 0)
        E(raw, ldrbw(0, 4, 0x59)); E(cmp_imm, 0, 0); E(b_cond, "r1_x", "eq")
        E(ldr_imm, 0, 4, 0x4C); E(raw, ldrbw(1, 4, 0x58)); E(movs_imm, 2, 0); E(ldr_imm, 3, 0, 0); E(ldr_imm, 3, 3, 4); E(raw, h(0x4798))   # blx r3
        E(movs_imm, 0, 0); E(raw, strbw(0, 4, 0x59))
        a.label("r1_x"); E(pop_list, [4], pc=True)
        # ---- c_rlsweep() (the LED task): the note-offs due, stopped; playing they are dropped
        a.label("c_rlsweep")
        E(push_list, [4, 5, 6, 7], lr=True)
        E(bl, "c_rlm"); E(cmp_imm, 0, 0); E(b_cond, "sw_x", "eq")
        E(movw, 1, O_MASK - O_OFF); E(subs_reg, 5, 0, 1)                                                     # r5 = the times
        imm32(0, TRANSPORT); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 7, 0, 0)                      # r7 = playing
        imm32(0, HAL_TICK); E(ldr_imm, 6, 0, 0)                                                             # r6 = now
        E(movs_imm, 4, 0)
        a.label("sw_l")
        E(lsls_imm, 0, 4, 2); E(adds_reg, 0, 5, 0); E(ldr_imm, 1, 0, 0); E(cmp_imm, 1, 0); E(b_cond, "sw_n", "eq")
        if MUTE:                                                                                       # playing: dropped, unless the drum is muted
            E(cmp_imm, 7, 0); E(b_cond, "sw_d", "eq")
            E(movs_imm, 0, DP_SZ); E(muls, 0, 4); imm32(1, DP0); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, 0x28); E(movs_imm, 1, 0); E(bl, PARAM_GET)
            E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "sw_c", "eq")
            E(lsls_imm, 0, 4, 2); E(adds_reg, 0, 5, 0); E(ldr_imm, 1, 0, 0)
            a.label("sw_d")
        else:
            E(cmp_imm, 7, 0); E(b_cond, "sw_c", "ne")
        E(subs_reg, 1, 6, 1); E(b_cond, "sw_n", "mi")                                                       # not due yet
        E(movs_imm, 0, DP_SZ); E(muls, 0, 4); imm32(1, DP0); E(adds_reg, 0, 0, 1); E(bl, "c_rloff1")
        a.label("sw_c"); E(lsls_imm, 0, 4, 2); E(adds_reg, 0, 5, 0); E(movs_imm, 1, 0); E(str_imm, 1, 0, 0)
        a.label("sw_n"); E(adds_imm8, 4, 1); E(cmp_imm, 4, 4); E(b_cond, "sw_l", "lo")
        a.label("sw_x"); E(pop_list, [4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the drum players' slot 2, the drums' Note view slots 0 / 1 / 7, the LED task calls."""
    import ct_fw
    import packio as PK, fxdiag as FD
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    assert u(DP_VT + 8) == DP_PLAY | 1, hex(u(DP_VT + 8))
    prev = dict(pad=u(NV_VT) & ~1, rel=u(NV_VT + 4) & ~1, leds=u(NV_VT + 28) & ~1, ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    code, labels = arm_code(base_addr, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    struct.pack_into("<I", img, DP_VT + 8 - BASE, labels["c_rlplay"] | 1)
    if MUTE:
        from thumb import b_w as bw
        assert bytes(img[MUTE_AT - BASE:MUTE_AT - BASE + 6]) == MUTE_OLD
        img[MUTE_AT - BASE:MUTE_AT - BASE + 6] = bw(MUTE_AT, labels["c_rlmute"]) + h(0xBF00)
    struct.pack_into("<I", img, NV_VT - BASE, labels["c_rlpad"] | 1)
    struct.pack_into("<I", img, NV_VT + 4 - BASE, labels["c_rlrel"] | 1)
    struct.pack_into("<I", img, NV_VT + 28 - BASE, labels["c_rlleds"] | 1)
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_rlledtask"])
    return labels, code, prev
