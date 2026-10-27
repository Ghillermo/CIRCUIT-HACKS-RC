"""SC47.9 (the user, 2026-10-24: «modo sample stereo: al pulsar drum 1+2 o drum 3+4, drum 1 o drum 3 respectivamente son el sample master (paneado a
izquierda), drum 2/4 se panean a derecha y utilizan el sample siguiente consecutivo (hasta que el usuario cambie de sample). Los controles de 1/3 y su
secuenciador afectan a ambos samples, su pareja recibe controles de desvío/paneo sobre el principal y su secuenciador no se usa. Volver a pulsar el mismo
atajo (1+2/3+4) vuelve a la normalidad»; 2026-10-27: «implement stereo pair as planned»): stereo drum pairs.

The design of the study of 2026-10-25 (docs/NOTAS.md, «Estudio … sample estéreo completo en los drums»: design B + the per-hit sample / pitch write of
design A) with the user's answers: K2 of the partner = the pan spread (width); detune in cents; no distortion deviation (the pair uses the master's);
the partner's own pads and MIDI notes sound alone on the right; the master on sample 63 -> the partner wraps to 0; saved with the project.

The rule: the partner's (slave's) stored values are never written.  While a pair is on, everything the slave sends to the DSP is redirected where its
DSP group reads it, and its sequencer is silenced:
  * the toggle (UI): the head of the button press (0x08033320): Drum 1 held + Drum 2 (or 2 + 1), Drum 3 + Drum 4; not with Shift, Clear / Duplicate
    held or in Setup; the master's press goes on (its view), the slave's is swallowed; then the stock's commit 0x08033A2E (no peek back on release),
    or, with splitknob holding the first button, its O_USED (its release is no tap).  Enter / exit: MARK_DIRTY of both drums' groups and of the sends,
    every mod code of the slave marked (sc18.c_mh + 0x3E / 0x3F), the slave player reset (0x0804A79C); exit gives back the slave's SC16 bytes;
  * the hits: the funnel's b.w 0x08051B54 (0x08049826, in the DSP semaphore: no MARK_DIRTY) -> c_sttrig: a master hit flushes the slave's group
    (0x080214D0), writes the slave's sample word (the master's + k, & 63) and pitch word (the master's x the detune), then fires the slave
    (X:$9F + s) and goes on to the master's; a slave hit (its pads, MIDI notes) goes on alone, with its newly picked sample when the LED task has not
    seen the pick yet; the slave's sequencer: word 0 of the drum players' vtable (0x0805B72C, the tick) -> c_pstick returns for a paired slave;
  * the stock drum parameters: the group table words of drum 1 / 3 (0x08021534 / 0x0802153C) -> c_stgw0 / 2 (the master's writer, then the slave's
    when paired); the getter sites inside the slave's writers -> c_stg / c_stgc (sample = the master's + k; level / sends = the master's; decay / EQ =
    the master's + deviation; distortion = the master's; pan = the master's pan + W / 2, the master's - (W + 1) / 2; cue mode on: both the master's);
    the slave's pitch conversion (dpitch c_dpc1 / c_dpc3) -> c_stpc1 / 3 (the master's word x the detune: SC12's cents table);
  * the mod's drum values (persist19, in the DSP service tick): the sites in c_dtick19 (c_dget, c_dext_get, c_xt_get), the three c_k3get in c_k3w and
    lfosync's c_lfd -> the master's values (+ the deviations); a master's code marks the slave's bit (the loop runs the drums in order: the same tick);
  * the slave's knobs (macro handlers' slot 4, in front of dpitch): deviations / the width, nothing stored, nothing sent; slot 7: their LEDs;
  * the side-chain: the LED task copies the master's SC16 bytes (preset, trigger) into the slave's (given back on exit) and the group 5 head writes
    the master's knob values (scdrum.c_sdval) into the slave's block;
  * the LED task: the slave's track LED pulses (blinks when selected) in the master's colour; the sample-change detector (the slave's selection
    changed = k = its distance from the master's);
  * saved with the project: a signed block in bytes 8..39 of the settings of MIDI 1's patterns 5 / 6 (pair 1+2 / 3+4; projsyn uses 0..4), written
    by a head of the save call (only when on, or when the block is there already) and read by a head of the load's re-send (0x0802F5B4).
RAM: modmx.MXR + 0x1A00 (72 B, signed).  In the hole (it writes nothing to the card).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm3, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, eors_reg, h, ldr_imm, ldr_sp, ldrb_imm,  # noqa: E402
                   ldrb_reg, ldrb_w, ldrh_imm, lsls_imm, lsls_reg, lsrs_imm, lsrs_reg, mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list,
                   push_list, raw, str_imm, strb_imm, strb_w, strh_imm, strh_reg, subs_imm3, subs_imm8, subs_reg, tst_reg)
import modmx as MX  # noqa: E402
import mpatch as MP  # noqa: E402
import fxdiag as FD  # noqa: E402
import packio as PK  # noqa: E402
import persist19 as P19  # noqa: E402
import srcview as SV  # noqa: E402
import splitknob as SK  # noqa: E402
import build_sc16 as S16  # noqa: E402
import vcf21 as V  # noqa: E402

STR = MX.MXR + 0x1A00                 # + 0 signature, + 4 held mask (ids 4..7), + 5 pair bits; pair p at + 8 + 32 p
SIG = 0x31505453                      # "STP1"
O_SIG, O_HELD, O_PAIR, PB, PSZ = 0, 4, 5, 8, 32
P_K, P_SNAP, P_W, P_SCS, P_SCP, P_SCT, P_DEV = 0, 1, 2, 3, 4, 5, 8      # dev[16] signed, index = knob + 8 x Shift
NSTR = PB + 2 * PSZ
GETTER, PARAM_GET, MARK_DIRTY, DSPW = 0x08036192, 0x0803542C, 0x0803BDCC, 0x080292F8
COMMIT, FLUSH, TRIG, PRESET_RESET = 0x08033A2E, 0x080214D0, 0x08051B54, 0x0804A79C
FUNNEL, RESEND_CALL, PLAYER_VT0, PLAYER_TICK = 0x08049826, 0x0802F5B4, 0x0805B72C, 0x0804A5C6
PLAYERS = (0x20040810, 0x200408A0, 0x20040930, 0x200409C0)
PSTEP = 0x120                         # players[d + 2] - players[d]
GROUP_WORDS = (0x08021534, 0x0802153C)                  # the group table entries of drum 1 / drum 3
WRITERS = (0x080287DE, 0x0802887A, 0x0802890E, 0x080289A2)
SITES_G = (0x08028880, 0x080289A8, 0x080288A8, 0x080289D0, 0x080288BE, 0x080289E6, 0x080288D2, 0x080289FA)   # slave: sample, decay, distortion, EQ
SITES_C = (0x080288EA, 0x08028A12, 0x080288FE, 0x08028A26, 0x08028862, 0x08028992,                          # slave level, slave pan, master pan
           0x08028BBC, 0x08028BE0, 0x08028C4A, 0x08028C6E)                                                     # slave reverb / delay sends
SITES_PC = (0x08028896, 0x080289BE)   # the slaves' pitch conversion (dpitch c_dpc1 / c_dpc3)
MH_VT = 0x0805AADC                    # the drum macro handlers: slot 4 knob, slot 7 LEDs
GRP5 = S16.GROUP_TAB + 5 * 4
SESSION_OBJ, AREA, PSIZE, SET, BYTE0 = 0x2003D71C, 0x1A27C, 0xCA8, 0x380, 8      # MIDI 1's patterns: projsyn's constants
PAT0 = 5                              # pair p's block: MIDI 1's pattern 5 + p
BSIG, BVER = 0xC8, 1
LED0 = 37                             # the panel LED of Drum 2 (Drum 4 = 39)
COL_M = (0x45, 0x49)                  # the masters' colours (Drum 1 / Drum 3)
COL_S = (0x2D, 0x4D)                  # the slaves' own colours (Drum 2 / Drum 4): the stock paints them on the selected track
LED_BLINK, LED_PULSE = 0x47, 0x48     # Drum 1's family (Drum 3's = + 4): blink / pulse (animated codes)
COL_W, COL_CLR, DIM = 0x01, 0x07, 2   # the width: white; Clear held: lavender; the dim level
# the slave's knobs, index = knob + 8 x Shift: kind << 4 | n; kinds 0 none (mirror), 1 a stock parameter (i = n), 2 a mod code bit in + 0x3E (bit n),
# 3 in + 0x3F (bit n), 4 the width
KTAB = (0x12, 0x40, 0x13, 0x24, 0x15, 0x25, 0x22, 0x00,
        0x20, 0x30, 0x32, 0x26, 0x00, 0x21, 0x00, 0x00)
# persist19's codes 0..15 -> the deviation index (0xFF = mirror only): 1 pitch env (Shift + K1), 2 ring frequency (Shift + K6), 3 LFO amount (K7),
# 4 LFO speed (mirror), 5 env -> cutoff (K4), 6 resonance (K6), 7 envelope shape (Shift + K4), 8 ring amount (Shift + K2), 9 filter mode (mirror)
DEVMAP = (0xFF, 8, 13, 6, 0xFF, 3, 5, 11, 9, 0xFF) + (0xFF,) * 6
DEV_START = 10                        # Shift + K3: the sample start
START_MAX = 120
INV = V.INV


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def sxtb(rd, rm): return h(0xB240 | rm << 3 | rd)
def asrs_imm(rd, rm, imm): return h(0x1000 | imm << 6 | rm << 3 | rd)
def negs(rd, rm): return h(0x4240 | rm << 3 | rd)
def ldr_reg(rt, rn, rm): return h(0x5800 | rm << 6 | rn << 3 | rt)
def str_reg(rt, rn, rm): return h(0x5000 | rm << 6 | rn << 3 | rt)
def umull(lo, hi, rn, rm): return h(0xFBA0 | rn) + h(lo << 12 | hi << 8 | rm)


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    zc = [0]
    RET = h(0x4770)
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def bc(target, cond):
        zc[0] += 1; n = f"_t{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)
    def mark(t, ireg=None, i=None):                        # MARK_DIRTY(t, i or the register); clobbers r0-r3
        if ireg is not None: E(mov_reg, 1, ireg)
        else: E(movs_imm, 1, i)
        E(movs_imm, 0, t); E(bl, MARK_DIRTY)

    # ---- data (at the start: their addresses known)
    O_KTAB, O_DEVMAP = 0, 16
    E(raw, bytes(KTAB) + bytes(DEVMAP))
    a.label("st_code")

    # ---- c_stst() -> r0 = STR, set up at the first use (zeros, k 1, snapshot 0xFF, W 127, the signature); clobbers r1-r3
    a.label("c_stst")
    imm32(0, STR); E(ldr_imm, 1, 0, O_SIG); imm32(2, SIG); E(cmp_reg, 1, 2); E(b_cond, "ss_i", "ne"); E(raw, RET)
    a.label("ss_i")
    E(movs_imm, 1, 0); E(movs_imm, 3, 0)
    a.label("ss_z"); E(raw, str_reg(1, 0, 3)); E(adds_imm8, 3, 4); E(cmp_imm, 3, NSTR); E(b_cond, "ss_z", "lo")
    for p in range(2):
        E(mov_reg, 3, 0); E(adds_imm8, 3, PB + PSZ * p)
        E(movs_imm, 1, 1); E(strb_imm, 1, 3, P_K); E(movs_imm, 1, 0xFF); E(strb_imm, 1, 3, P_SNAP); E(movs_imm, 1, 127); E(strb_imm, 1, 3, P_W)
    E(str_imm, 2, 0, O_SIG); E(raw, RET)

    # ---- c_stpb(r0 = pair) -> r0 = the pair's block; clobbers r1
    a.label("c_stpb")
    E(lsls_imm, 0, 0, 5); E(adds_imm8, 0, PB); imm32(1, STR); E(adds_reg, 0, 0, 1); E(raw, RET)

    # ---- c_ston(r0 = drum) -> r0 = 1 when its pair is on; clobbers r1-r3 (RAM only: any context)
    a.label("c_ston")
    E(cmp_imm, 0, 3); E(b_cond, "so_n", "hi"); E(lsrs_imm, 0, 0, 1)
    imm32(1, STR); E(ldr_imm, 2, 1, O_SIG); imm32(3, SIG); E(cmp_reg, 2, 3); E(b_cond, "so_n", "ne")
    E(ldrb_imm, 1, 1, O_PAIR); E(raw, h(0x40C1)); E(movs_imm, 0, 1); E(ands_reg, 0, 1); E(raw, RET)      # lsrs r1, r0
    a.label("so_n"); E(movs_imm, 0, 0); E(raw, RET)

    # ---- c_stcl(r0 = v, r1 = lo, r2 = hi) -> r0 clamped (signed)
    a.label("c_stcl")
    E(cmp_reg, 0, 1); E(b_cond, "cl_1", "ge"); E(mov_reg, 0, 1); E(raw, RET)
    a.label("cl_1"); E(cmp_reg, 0, 2); E(b_cond, "cl_2", "le"); E(mov_reg, 0, 2)
    a.label("cl_2"); E(raw, RET)

    # ---- c_stdev(r0 = pair, r1 = index) -> r0 = dev[index], signed; clobbers r1
    a.label("c_stdev")
    E(push_list, [1], lr=True); E(bl, "c_stpb"); E(pop_list, [1]); E(adds_reg, 0, 0, 1); E(ldrb_imm, 0, 0, P_DEV); E(raw, sxtb(0, 0))
    E(pop_list, [], pc=True)

    # ---- c_stpw(r0 = master) -> r0 = the slave's pitch word: the master's (dpitch's word of its pitch) x the detune (dev[K1] x 25 / 16 cents)
    a.label("c_stpw")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0)
    E(movs_imm, 1, 7); E(muls, 1, 4); E(adds_imm8, 1, 2); E(movs_imm, 0, 0x10); E(bl, GETTER)
    E(mov_reg, 1, 0); E(mov_reg, 0, 4); E(bl, L["c_dpword"]); E(mov_reg, 5, 0)
    E(lsrs_imm, 0, 4, 1); E(movs_imm, 1, 0); E(bl, "c_stdev")
    E(movs_imm, 1, 25); E(muls, 0, 1); E(raw, asrs_imm(0, 0, 4)); E(adds_imm8, 0, 100)                # 0..198
    E(lsls_imm, 0, 0, 2); imm32(1, L["t12"]); E(raw, ldr_reg(1, 1, 0))
    E(raw, umull(0, 2, 5, 1)); E(lsrs_imm, 0, 0, 16); E(lsls_imm, 2, 2, 16); E(orrs_reg, 0, 2)
    imm32(1, 0x7FFFFF); E(cmp_reg, 0, 1); E(b_cond, "pw_x", "ls"); E(mov_reg, 0, 1)
    a.label("pw_x"); E(pop_list, [4, 5], pc=True)

    # ---- c_stpc1 / c_stpc3 (the slaves' bl c_dpc1 / c_dpc3: r0 = their pitch) -> the master's word x the detune when paired
    for d in (1, 3):
        a.label(f"c_stpc{d}")
        E(push_list, [0, 4], lr=True)
        E(movs_imm, 0, d); E(bl, "c_ston"); E(cmp_imm, 0, 0); E(b_cond, f"pc_on{d}", "ne")
        E(raw, popw([0, 4], lr=True)); E(b_w, prev[f"dpc{d}"])
        a.label(f"pc_on{d}")
        E(movs_imm, 0, d - 1); E(bl, "c_stpw"); E(pop_list, [1, 4], pc=True)

    # ---- c_stg / c_stgc (r0 = type, r1 = index): the getter sites of the writers (prev GETTER / cue's c_cqg)
    a.label("c_stgc"); E(push_list, [4, 5, 6, 7], lr=True); imm32(7, prev["cqg"] | 1); E(b, "sg_go")
    a.label("c_stg"); E(push_list, [4, 5, 6, 7], lr=True); imm32(7, GETTER | 1)
    a.label("sg_go")
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(cmp_imm, 4, 0x20); bc("sg_send", "eq"); E(cmp_imm, 4, 0x10); bc("sg_prev", "ne")
    E(movs_imm, 6, 0); E(mov_reg, 0, 5)                                               # r6 = the drum, r0 = i
    a.label("sg_dl"); E(cmp_imm, 0, 7); E(b_cond, "sg_dd", "lo"); E(subs_imm8, 0, 7); E(adds_imm8, 6, 1); E(b, "sg_dl")
    a.label("sg_dd")
    E(push_list, [0]); E(mov_reg, 0, 6); E(bl, "c_ston"); E(mov_reg, 1, 0); E(pop_list, [0])                # r0 = i, r1 = on
    E(cmp_imm, 1, 0); bc("sg_prev", "eq")
    E(lsls_imm, 1, 6, 31); bc("sg_mst", "eq")
    # a paired slave: r0 = i, the master's index = r5 - 7
    E(subs_imm8, 5, 7)
    E(cmp_imm, 0, 0); bc("sg_smp", "eq"); E(cmp_imm, 0, 1); bc("sg_cq", "eq"); E(cmp_imm, 0, 6); bc("sg_pan", "eq")
    E(cmp_imm, 0, 3); bc("sg_dec", "eq"); E(cmp_imm, 0, 5); bc("sg_eq", "eq")
    E(movs_imm, 0, 0x10); E(mov_reg, 1, 5); E(bl, GETTER); E(pop_list, [4, 5, 6, 7], pc=True)                 # distortion (and the rest): the master's
    a.label("sg_smp")
    E(movs_imm, 0, 0x10); E(mov_reg, 1, 5); E(bl, GETTER); E(mov_reg, 4, 0)
    E(lsrs_imm, 0, 6, 1); E(bl, "c_stpb"); E(ldrb_imm, 0, 0, P_K); E(adds_reg, 0, 0, 4); E(movs_imm, 1, 63); E(ands_reg, 0, 1)
    E(pop_list, [4, 5, 6, 7], pc=True)
    a.label("sg_cq")
    E(movs_imm, 0, 0x10); E(mov_reg, 1, 5); E(bl, prev["cqg"]); E(pop_list, [4, 5, 6, 7], pc=True)
    for lb, dv in (("sg_dec", 2), ("sg_eq", 4)):
        a.label(lb)
        E(movs_imm, 0, 0x10); E(mov_reg, 1, 5); E(bl, GETTER); E(mov_reg, 4, 0)
        E(lsrs_imm, 0, 6, 1); E(movs_imm, 1, dv); E(bl, "c_stdev"); E(adds_reg, 0, 0, 4)
        E(movs_imm, 1, 0); E(movs_imm, 2, 127); E(bl, "c_stcl"); E(pop_list, [4, 5, 6, 7], pc=True)
    a.label("sg_pan")                                                                 # the slave's pan: C + W / 2 (cue on: C)
    E(movs_imm, 0, 0x10); E(mov_reg, 1, 5); E(bl, prev["cqg"]); E(mov_reg, 4, 0)
    E(bl, L["c_cqon"]); E(cmp_imm, 0, 0); E(b_cond, "sg_r4", "ne")
    E(lsrs_imm, 0, 6, 1); E(bl, "c_stpb"); E(ldrb_imm, 0, 0, P_W); E(lsrs_imm, 0, 0, 1); E(adds_reg, 0, 0, 4)
    E(movs_imm, 1, 0); E(movs_imm, 2, 127); E(bl, "c_stcl"); E(pop_list, [4, 5, 6, 7], pc=True)
    a.label("sg_r4"); E(mov_reg, 0, 4); E(pop_list, [4, 5, 6, 7], pc=True)
    a.label("sg_mst")                                                                 # a paired master: only its pan changes: C - (W + 1) / 2
    E(push_list, [0]); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(raw, h(0x47B8)); E(mov_reg, 4, 0); E(pop_list, [0])   # blx r7
    E(cmp_imm, 0, 6); E(b_cond, "sg_r4", "ne")
    E(bl, L["c_cqon"]); E(cmp_imm, 0, 0); E(b_cond, "sg_r4", "ne")
    E(lsrs_imm, 0, 6, 1); E(bl, "c_stpb"); E(ldrb_imm, 0, 0, P_W); E(adds_imm8, 0, 1); E(lsrs_imm, 0, 0, 1); E(subs_reg, 0, 4, 0)
    E(movs_imm, 1, 0); E(movs_imm, 2, 127); E(bl, "c_stcl"); E(pop_list, [4, 5, 6, 7], pc=True)
    a.label("sg_send")                                                                # the slaves' sends (2 + d reverb, 13 + d delay): the master's
    E(mov_reg, 6, 5); E(subs_imm8, 6, 2); E(cmp_imm, 6, 3); E(b_cond, "sg_sd", "ls")
    E(mov_reg, 6, 5); E(subs_imm8, 6, 13); E(cmp_imm, 6, 3); bc("sg_prev", "hi")
    a.label("sg_sd")
    E(lsls_imm, 0, 6, 31); bc("sg_prev", "eq"); E(mov_reg, 0, 6); E(bl, "c_ston"); E(cmp_imm, 0, 0); bc("sg_prev", "eq")
    E(movs_imm, 0, 0x20); E(mov_reg, 1, 5); E(subs_imm8, 1, 1); E(bl, prev["cqg"]); E(pop_list, [4, 5, 6, 7], pc=True)
    a.label("sg_prev")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(raw, h(0x47B8)); E(pop_list, [4, 5, 6, 7], pc=True)                # blx r7

    # ---- c_stgw0 / c_stgw2 (the group table's drum 1 / drum 3): the master's writer, then the slave's when paired
    for p in range(2):
        a.label(f"c_stgw{2 * p}")
        E(push_list, [4], lr=True); E(bl, WRITERS[2 * p])
        E(movs_imm, 0, 2 * p + 1); E(bl, "c_ston"); E(cmp_imm, 0, 0); E(b_cond, f"gw_x{p}", "eq")
        E(bl, WRITERS[2 * p + 1])
        a.label(f"gw_x{p}"); E(pop_list, [4], pc=True)

    # ---- c_sttrig (the funnel's b.w 0x08051B54: r0 = drum, r1 = velocity; the DSP semaphore held: no MARK_DIRTY)
    a.label("c_sttrig")
    E(push_list, [0, 1, 4, 5, 6], lr=True)
    E(bl, "c_ston"); E(cmp_imm, 0, 0); E(b_cond, "tr_on", "ne")
    a.label("tr_out"); E(raw, popw([0, 1, 4, 5, 6], lr=True)); E(b_w, TRIG)
    a.label("tr_on")
    E(ldr_sp, 4, 0); E(lsls_imm, 0, 4, 31); E(b_cond, "tr_mst", "eq")
    # a slave hit (its pads, its notes): alone; a pick the LED task has not seen yet sounds at once
    E(movs_imm, 1, 7); E(muls, 1, 4); E(movs_imm, 0, 0x10); E(bl, GETTER); E(mov_reg, 5, 0)
    E(lsrs_imm, 0, 4, 1); E(bl, "c_stpb"); E(ldrb_imm, 1, 0, P_SNAP); E(cmp_reg, 5, 1); E(b_cond, "tr_out", "eq")
    E(lsls_imm, 1, 5, 8); E(movs_imm, 2, 10); E(muls, 2, 4); E(adds_imm8, 2, 0xA3); E(movs_imm, 0, 0); E(bl, DSPW); E(b, "tr_out")
    a.label("tr_mst")
    E(adds_imm3, 5, 4, 1)                                                             # r5 = the slave
    E(mov_reg, 0, 5); E(bl, FLUSH)
    E(movs_imm, 1, 7); E(muls, 1, 4); E(movs_imm, 0, 0x10); E(bl, GETTER); E(mov_reg, 6, 0)
    E(lsrs_imm, 0, 4, 1); E(bl, "c_stpb"); E(ldrb_imm, 0, 0, P_K); E(adds_reg, 0, 0, 6); E(movs_imm, 1, 63); E(ands_reg, 0, 1)
    E(lsls_imm, 1, 0, 8); E(movs_imm, 2, 10); E(muls, 2, 5); E(adds_imm8, 2, 0xA3); E(movs_imm, 0, 0); E(bl, DSPW)
    E(mov_reg, 0, 4); E(bl, "c_stpw"); E(mov_reg, 1, 0); E(movs_imm, 2, 10); E(muls, 2, 5); E(adds_imm8, 2, 0xA4); E(movs_imm, 0, 0); E(bl, DSPW)
    E(ldr_sp, 1, 4); E(cmp_imm, 1, 8); E(b_cond, "tr_v", "ge"); E(movs_imm, 1, 8)
    a.label("tr_v"); E(lsls_imm, 1, 1, 23); E(mov_reg, 2, 5); E(adds_imm8, 2, 0x9F); E(movs_imm, 0, 0); E(bl, DSPW)
    E(b, "tr_out")

    # ---- c_pstick (word 0 of the drum players' vtable, the tick): a paired slave's sequencer does nothing
    a.label("c_pstick")
    E(push_list, [0, 1, 2, 3, 4], lr=True)
    for d in (1, 3):
        imm32(4, PLAYERS[d]); E(cmp_reg, 0, 4); E(b_cond, f"pk_{d}", "eq")
    E(b, "pk_out")
    for d in (1, 3):
        a.label(f"pk_{d}"); E(movs_imm, 0, d); E(b, "pk_t")
    a.label("pk_t")
    E(bl, "c_ston"); E(cmp_imm, 0, 0); E(b_cond, "pk_out", "eq")
    E(pop_list, [0, 1, 2, 3, 4], pc=True)
    a.label("pk_out"); E(raw, popw([0, 1, 2, 3, 4], lr=True)); E(b_w, PLAYER_TICK)

    # ---- c_stdg (c_dtick19's bl c_dget: r0 = drum, r1 = code) -> the value; a slave: the master's (+ the deviation); a master: marks the slave
    a.label("c_stdg")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, "c_ston"); E(cmp_imm, 0, 0); bc("dg_plain", "eq")
    E(lsls_imm, 0, 4, 31); bc("dg_mst", "eq")
    E(subs_imm3, 0, 4, 1); E(mov_reg, 1, 5); E(bl, L["c_dget"]); E(adds_imm3, 1, 0, 1); bc("dg_x", "eq")      # -1: none
    E(mov_reg, 6, 0)
    E(cmp_imm, 5, 15); bc("dg_r6", "hi")
    imm32(1, base + O_DEVMAP); E(ldrb_reg, 7, 1, 5); E(cmp_imm, 7, 0xFF); bc("dg_r6", "eq")
    E(lsrs_imm, 0, 4, 1); E(mov_reg, 1, 7); E(bl, "c_stdev"); E(mov_reg, 7, 0)                                 # r7 = the deviation
    E(lsls_imm, 0, 5, 31); E(b_cond, "dg_u", "eq")
    E(lsls_imm, 0, 6, 25); E(raw, asrs_imm(0, 0, 25)); E(adds_reg, 0, 0, 7); E(movs_imm, 1, 0x40); E(raw, negs(1, 1)); E(movs_imm, 2, 63)
    E(b, "dg_c")
    a.label("dg_u"); E(movs_imm, 0, 0x7F); E(ands_reg, 0, 6); E(adds_reg, 0, 0, 7); E(movs_imm, 1, 0); E(movs_imm, 2, 127)
    a.label("dg_c"); E(bl, "c_stcl")
    E(movs_imm, 1, 0x7F); E(ands_reg, 0, 1); E(movs_imm, 1, 0x80); E(ands_reg, 1, 6); E(orrs_reg, 0, 1); E(b, "dg_x")
    a.label("dg_mst")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, L["c_dget"]); E(mov_reg, 6, 0)
    E(adds_imm3, 0, 4, 1); E(bl, L["c_mh"]); E(cmp_imm, 0, 0); E(b_cond, "dg_r6", "eq")
    E(cmp_imm, 5, 1); E(b_cond, "dg_r6", "lo"); E(cmp_imm, 5, 9); E(b_cond, "dg_r6", "hi")
    E(movs_imm, 2, 1); E(cmp_imm, 5, 7); E(b_cond, "dg_hi", "hi")
    E(subs_imm3, 1, 5, 1); E(lsls_reg, 2, 1); E(ldrb_w, 1, 0, 0x3E); E(orrs_reg, 1, 2); E(strb_w, 1, 0, 0x3E); E(b, "dg_r6")
    a.label("dg_hi")
    E(mov_reg, 1, 5); E(subs_imm8, 1, 8); E(lsls_reg, 2, 1); E(ldrb_w, 1, 0, 0x3F); E(orrs_reg, 1, 2); E(strb_w, 1, 0, 0x3F)
    a.label("dg_r6"); E(mov_reg, 0, 6); E(b, "dg_x")
    a.label("dg_plain"); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, L["c_dget"])
    a.label("dg_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_stdx (c_dext_get: r0 = drum): a slave the master's; a master marks the slave's code 10 (+ 0x3F bit 2)
    a.label("c_stdx")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    E(bl, "c_ston"); E(cmp_imm, 0, 0); E(b_cond, "dx_p", "eq")
    E(lsls_imm, 0, 4, 31); E(b_cond, "dx_m", "eq")
    E(subs_imm3, 0, 4, 1); E(bl, L["c_dext_get"]); E(pop_list, [4], pc=True)
    a.label("dx_m")
    E(adds_imm3, 0, 4, 1); E(bl, L["c_mh"]); E(cmp_imm, 0, 0); E(b_cond, "dx_p", "eq")
    E(ldrb_w, 1, 0, 0x3F); E(movs_imm, 2, 4); E(orrs_reg, 1, 2); E(strb_w, 1, 0, 0x3F)
    a.label("dx_p"); E(mov_reg, 0, 4); E(bl, L["c_dext_get"]); E(pop_list, [4], pc=True)

    # ---- c_stxt (c_xt_get: r0 = drum): a slave the master's
    a.label("c_stxt")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    E(bl, "c_ston"); E(cmp_imm, 0, 0); E(b_cond, "xt_p", "eq"); E(lsls_imm, 0, 4, 31); E(b_cond, "xt_p", "eq"); E(subs_imm8, 4, 1)
    a.label("xt_p"); E(mov_reg, 0, 4); E(bl, L["c_xt_get"]); E(pop_list, [4], pc=True)

    # ---- c_stlf (lfosync's c_dget(drum, 4)): a slave the master's LFO speed
    a.label("c_stlf")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, "c_ston"); E(cmp_imm, 0, 0); E(b_cond, "lf_p", "eq"); E(lsls_imm, 0, 4, 31); E(b_cond, "lf_p", "eq"); E(subs_imm8, 4, 1)
    a.label("lf_p"); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, L["c_dget"]); E(pop_list, [4, 5], pc=True)

    # ---- c_stk3 (c_k3w's c_k3get(drum, i): 0 attack, 1 start, 2 cut): a slave the master's; its start + dev[Shift + K3]
    a.label("c_stk3")
    E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, "c_ston"); E(cmp_imm, 0, 0); E(b_cond, "k3_p", "eq"); E(lsls_imm, 0, 4, 31); E(b_cond, "k3_p", "eq")
    E(subs_imm3, 0, 4, 1); E(mov_reg, 1, 5); E(bl, L["c_k3get"])
    E(cmp_imm, 5, 1); E(b_cond, "k3_x", "ne"); E(mov_reg, 6, 0)
    E(lsrs_imm, 0, 4, 1); E(movs_imm, 1, DEV_START); E(bl, "c_stdev"); E(adds_reg, 0, 0, 6)
    E(movs_imm, 1, 0); E(movs_imm, 2, START_MAX); E(bl, "c_stcl"); E(b, "k3_x")
    a.label("k3_p"); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, L["c_k3get"])
    a.label("k3_x"); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_stknob (the drum macro handlers' slot 4: obj, knob, delta): a paired slave's knobs = the deviations / the width, nothing else
    a.label("c_stknob")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(bl, L["c_dpdrum"]); E(cmp_imm, 0, 3); bc("kn_prev", "hi"); E(lsls_imm, 1, 0, 31); bc("kn_prev", "eq"); E(mov_reg, 5, 0)
    E(bl, "c_ston"); E(cmp_imm, 0, 0); bc("kn_prev", "eq")
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "kn_s", "eq"); E(movs_imm, 0, 8)
    a.label("kn_s"); E(ldr_sp, 1, 4); E(adds_reg, 6, 0, 1); E(cmp_imm, 6, 15); bc("kn_x", "hi")               # r6 = the index
    E(ldr_sp, 0, 0); E(bl, L["c_clr_held"]); E(mov_reg, 7, 0)                                                 # r7 = Clear held
    E(lsrs_imm, 0, 5, 1); E(bl, "c_stpb"); E(mov_reg, 4, 0)                                                   # r4 = the pair
    imm32(1, base + O_KTAB); E(ldrb_reg, 1, 1, 6); E(lsrs_imm, 0, 1, 4); E(cmp_imm, 0, 0); bc("kn_x", "eq")
    E(cmp_imm, 0, 4); E(b_cond, "kn_dev", "ne")
    # the width
    E(ldrb_imm, 0, 4, P_W); E(ldr_sp, 1, 8); E(adds_reg, 0, 0, 1); E(cmp_imm, 7, 0); E(b_cond, "kn_wc", "eq"); E(movs_imm, 0, 127)
    a.label("kn_wc"); E(movs_imm, 1, 0); E(movs_imm, 2, 127); E(bl, "c_stcl"); E(strb_imm, 0, 4, P_W)
    E(movs_imm, 1, 7); E(muls, 1, 5); E(subs_imm8, 1, 1); mark(0x10, ireg=1)                                 # 7 m + 6
    E(movs_imm, 1, 7); E(muls, 1, 5); E(adds_imm8, 1, 6); mark(0x10, ireg=1)                                 # 7 s + 6
    E(b, "kn_x")
    a.label("kn_dev")
    E(adds_reg, 4, 4, 6); E(ldrb_imm, 0, 4, P_DEV); E(raw, sxtb(0, 0)); E(ldr_sp, 1, 8); E(adds_reg, 0, 0, 1)
    E(cmp_imm, 7, 0); E(b_cond, "kn_dc", "eq"); E(movs_imm, 0, 0)
    a.label("kn_dc"); E(movs_imm, 1, 0x40); E(raw, negs(1, 1)); E(movs_imm, 2, 63); E(bl, "c_stcl"); E(strb_imm, 0, 4, P_DEV)
    imm32(1, base + O_KTAB); E(ldrb_reg, 6, 1, 6); E(lsrs_imm, 0, 6, 4); E(movs_imm, 1, 15); E(ands_reg, 6, 1)   # r0 = the kind, r6 = n
    E(cmp_imm, 0, 1); E(b_cond, "kn_mod", "ne")
    E(movs_imm, 1, 7); E(muls, 1, 5); E(adds_reg, 1, 1, 6); mark(0x10, ireg=1); E(b, "kn_x")                 # 7 s + i
    a.label("kn_mod")
    E(mov_reg, 4, 0); E(mov_reg, 0, 5); E(bl, L["c_mh"]); E(cmp_imm, 0, 0); E(b_cond, "kn_x", "eq")
    E(movs_imm, 2, 1); E(lsls_reg, 2, 6); E(cmp_imm, 4, 3); E(b_cond, "kn_3f", "eq")
    E(ldrb_w, 1, 0, 0x3E); E(orrs_reg, 1, 2); E(strb_w, 1, 0, 0x3E); E(b, "kn_x")
    a.label("kn_3f"); E(ldrb_w, 1, 0, 0x3F); E(orrs_reg, 1, 2); E(strb_w, 1, 0, 0x3F)
    a.label("kn_x"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("kn_prev"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["knob"])

    # ---- c_stkled (slot 7: obj) -> r0 = its LED buffer; a paired slave's: the deviations (the master's colour, brightness |dev| x 2), the width
    a.label("c_stkled")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0)
    E(bl, prev["led"]); E(mov_reg, 5, 0)
    E(mov_reg, 0, 4); E(bl, L["c_dpdrum"]); E(cmp_imm, 0, 3); bc("kl_x", "hi"); E(lsls_imm, 1, 0, 31); bc("kl_x", "eq"); E(mov_reg, 6, 0)
    E(bl, "c_ston"); E(cmp_imm, 0, 0); bc("kl_x", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_clr_held"]); E(mov_reg, 7, 0)
    E(bl, L["c_shift"]); E(movs_imm, 4, 0); E(cmp_imm, 0, 0); E(b_cond, "kl_s", "eq"); E(movs_imm, 4, 8)         # r4 = the first index
    a.label("kl_s")
    E(lsrs_imm, 0, 6, 1); E(bl, "c_stpb"); E(mov_reg, 6, 0)                                                   # r6 = the pair
    E(movs_imm, 3, 0)
    a.label("kl_l")
    E(adds_reg, 2, 4, 3); imm32(0, base + O_KTAB); E(ldrb_reg, 0, 0, 2); E(lsrs_imm, 0, 0, 4)
    E(cmp_imm, 0, 0); E(b_cond, "kl_off", "eq")
    E(cmp_imm, 7, 0); E(b_cond, "kl_nc", "eq")
    imm32(0, (127 + DIM) << 8 | COL_CLR); E(b, "kl_w")
    a.label("kl_nc")
    E(cmp_imm, 0, 4); E(b_cond, "kl_dv", "ne")
    E(ldrb_imm, 0, 6, P_W); E(adds_imm8, 0, DIM); E(lsls_imm, 0, 0, 8); E(adds_imm8, 0, COL_W); E(b, "kl_w")
    a.label("kl_dv")
    E(adds_reg, 0, 6, 2); E(ldrb_imm, 0, 0, P_DEV); E(raw, sxtb(0, 0)); E(cmp_imm, 0, 0); E(b_cond, "kl_p", "ge"); E(raw, negs(0, 0))
    a.label("kl_p"); E(lsls_imm, 0, 0, 1); E(cmp_imm, 0, 127); E(b_cond, "kl_b", "ls"); E(movs_imm, 0, 127)
    a.label("kl_b"); E(adds_imm8, 0, DIM); E(lsls_imm, 0, 0, 8)
    imm32(1, STR + PB); E(cmp_reg, 6, 1); E(b_cond, "kl_c1", "ne"); E(adds_imm8, 0, COL_M[0]); E(b, "kl_w")
    a.label("kl_c1"); E(adds_imm8, 0, COL_M[1]); E(b, "kl_w")
    a.label("kl_off"); E(movs_imm, 0, 0)
    a.label("kl_w"); E(lsls_imm, 1, 3, 1); E(strh_reg, 0, 5, 1)
    E(adds_imm8, 3, 1); E(cmp_imm, 3, 8); E(b_cond, "kl_l", "lo")
    a.label("kl_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_sttog(r0 = pair): on <-> off (the UI task): the marks, the slave's player reset (on), its SC16 bytes given back (off)
    a.label("c_sttog")
    E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0)
    E(bl, "c_stst"); E(mov_reg, 5, 0)
    E(mov_reg, 0, 4); E(bl, "c_stpb"); E(mov_reg, 6, 0)
    E(movs_imm, 1, 1); E(lsls_reg, 1, 4); E(ldrb_imm, 2, 5, O_PAIR); E(eors_reg, 2, 1); E(strb_imm, 2, 5, O_PAIR)
    E(tst_reg, 2, 1); E(b_cond, "tg_off", "eq")
    E(movs_imm, 0, 1); E(strb_imm, 0, 6, P_K)
    E(mov_reg, 0, 4); E(bl, "c_stsl"); E(ldr_imm, 0, 0, 0x5C); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(strb_imm, 0, 6, P_SNAP)
    E(mov_reg, 0, 4); E(bl, "c_stsl"); E(bl, PRESET_RESET)
    E(b, "tg_mk")
    a.label("tg_off")
    E(ldrb_imm, 0, 6, P_SCS); E(cmp_imm, 0, 0); E(b_cond, "tg_mk", "eq")
    E(mov_reg, 0, 4); E(bl, "c_stscr")
    a.label("tg_mk")
    E(movs_imm, 1, 14); E(muls, 1, 4); mark(0x10, ireg=1)                              # 7 m
    E(movs_imm, 1, 14); E(muls, 1, 4); E(adds_imm8, 1, 7); mark(0x10, ireg=1)          # 7 s
    mark(0x20, i=0); mark(0x20, i=11)
    E(lsls_imm, 0, 4, 1); E(adds_imm8, 0, 1); E(bl, L["c_mh"]); E(cmp_imm, 0, 0); E(b_cond, "tg_x", "eq")
    E(ldrb_w, 1, 0, 0x3E); E(movs_imm, 2, 0x7F); E(orrs_reg, 1, 2); E(strb_w, 1, 0, 0x3E)
    E(ldrb_w, 1, 0, 0x3F); E(movs_imm, 2, 7); E(orrs_reg, 1, 2); E(strb_w, 1, 0, 0x3F)
    a.label("tg_x"); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_stsl(r0 = pair) -> r0 = its slave's player; c_stml -> its master's; clobbers r1
    a.label("c_stsl"); E(movs_imm, 1, 0x12); E(lsls_imm, 1, 1, 4); E(muls, 1, 0); imm32(0, PLAYERS[1]); E(adds_reg, 0, 0, 1); E(raw, RET)
    a.label("c_stml"); E(movs_imm, 1, 0x12); E(lsls_imm, 1, 1, 4); E(muls, 1, 0); imm32(0, PLAYERS[0]); E(adds_reg, 0, 0, 1); E(raw, RET)

    # ---- c_stscr(r0 = pair): the slave's SC16 bytes given back (the UI task)
    a.label("c_stscr")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0)
    E(bl, "c_stpb"); E(mov_reg, 5, 0); E(movs_imm, 0, 0); E(strb_imm, 0, 5, P_SCS)
    E(bl, L["c_scst"]); E(cmp_imm, 0, 0); E(b_cond, "sr_x", "eq")
    E(lsls_imm, 1, 4, 1); E(adds_reg, 0, 0, 1)                                         # + 2 p: the master's bytes at + 4 / + 8, the slave's at + 5 / + 9
    E(ldrb_imm, 1, 5, P_SCP); E(strb_imm, 1, 0, 5); E(ldrb_imm, 1, 5, P_SCT); E(strb_imm, 1, 0, 9)
    mark(0x20, i=26)
    a.label("sr_x"); E(pop_list, [4, 5], pc=True)

    # ---- c_stbtn (the button press: ctrl, id): Drum 1 + 2 / Drum 3 + 4 = the pair on / off
    a.label("c_stbtn")
    E(push_list, [0, 1, 2, 4, 5, 6], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(cmp_imm, 5, 4); bc("bt_prev", "lo"); E(cmp_imm, 5, 7); bc("bt_prev", "hi")
    E(bl, "c_stst"); E(mov_reg, 6, 0)
    E(subs_imm3, 1, 5, 4); E(movs_imm, 2, 1); E(lsls_reg, 2, 1); E(ldrb_imm, 1, 6, O_HELD); E(orrs_reg, 1, 2); E(strb_imm, 1, 6, O_HELD)
    E(ldr_imm, 0, 4, 0xC); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); bc("bt_prev", "ne")       # Shift
    E(ldr_imm, 0, 4, 0x14); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 8); bc("bt_prev", "eq")      # Setup
    E(ldr_imm, 0, 4, 0x20); E(ldr_imm, 0, 0, 0xC); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(movs_imm, 1, 3); E(tst_reg, 0, 1); bc("bt_prev", "ne")                                                                      # Clear / Duplicate
    E(movs_imm, 1, 1); E(eors_reg, 1, 5); E(subs_imm8, 1, 4); E(ldrb_imm, 2, 6, O_HELD); E(lsrs_reg, 2, 1); E(lsls_imm, 2, 2, 31)  # eors r1, r5 = id ^ 1
    bc("bt_prev", "eq")                                                                                                          # the partner not held
    E(subs_imm3, 0, 5, 4); E(lsrs_imm, 0, 0, 1); E(bl, "c_sttog")
    E(lsls_imm, 0, 5, 31); E(b_cond, "bt_sl", "ne")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, prev["btn"])                              # the master: its view
    a.label("bt_sl")
    imm32(0, SK.SKR); E(ldr_imm, 1, 0, 0); imm32(2, SK.SIG); E(cmp_reg, 1, 2); E(b_cond, "bt_cm", "ne")
    E(ldrb_imm, 1, 0, SK.O_TRK); E(subs_imm8, 1, 4); E(cmp_imm, 1, 3); E(b_cond, "bt_cm", "hi")
    E(movs_imm, 1, 1); E(strb_imm, 1, 0, SK.O_USED); E(b, "bt_x")
    a.label("bt_cm"); E(mov_reg, 0, 4); E(bl, COMMIT)
    a.label("bt_x"); E(pop_list, [0, 1, 2, 4, 5, 6], pc=True)
    a.label("bt_prev"); E(raw, popw([0, 1, 2, 4, 5, 6], lr=True)); E(b_w, prev["btn"])

    # ---- c_strel (the button release: ctrl, id): the held bit cleared
    a.label("c_strel")
    E(push_list, [0, 1, 2, 3], lr=True)
    E(cmp_imm, 1, 4); E(b_cond, "rl_p", "lo"); E(cmp_imm, 1, 7); E(b_cond, "rl_p", "hi")
    imm32(2, STR); E(ldr_imm, 3, 2, O_SIG); imm32(0, SIG); E(cmp_reg, 3, 0); E(b_cond, "rl_p", "ne")
    E(subs_imm8, 1, 4); E(movs_imm, 0, 1); E(lsls_reg, 0, 1); E(ldrb_imm, 3, 2, O_HELD); E(raw, h(0x4383)); E(strb_imm, 3, 2, O_HELD)   # bics r3, r0
    a.label("rl_p"); E(raw, popw([0, 1, 2, 3], lr=True)); E(b_w, prev["rel"])

    # ---- c_stdet(r0 = pair): the slave's selection changed (a pick) -> k = its distance from the master's selection
    a.label("c_stdet")
    E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0)
    E(bl, "c_stpb"); E(mov_reg, 5, 0)
    E(mov_reg, 0, 4); E(bl, "c_stsl"); E(ldr_imm, 0, 0, 0x5C); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 6, 0, 0)
    E(ldrb_imm, 0, 5, P_SNAP); E(cmp_reg, 0, 6); E(b_cond, "dt_x", "eq")
    E(strb_imm, 6, 5, P_SNAP)
    E(mov_reg, 0, 4); E(bl, "c_stml"); E(ldr_imm, 0, 0, 0x5C); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(cmp_imm, 0, 0xFF); E(b_cond, "dt_b", "ne")
    E(movs_imm, 1, 14); E(muls, 1, 4); E(movs_imm, 0, 0x10); E(bl, GETTER)
    a.label("dt_b"); E(subs_reg, 0, 6, 0); E(movs_imm, 1, 63); E(ands_reg, 0, 1); E(strb_imm, 0, 5, P_K)
    E(movs_imm, 1, 14); E(muls, 1, 4); E(adds_imm8, 1, 7); mark(0x10, ireg=1)
    a.label("dt_x"); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_stscs(r0 = pair): the slave's SC16 bytes = the master's (the originals kept for the exit)
    a.label("c_stscs")
    E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0)
    E(bl, "c_stpb"); E(mov_reg, 5, 0)
    E(bl, L["c_scst"]); E(cmp_imm, 0, 0); E(b_cond, "sx_x", "eq")
    E(lsls_imm, 1, 4, 1); E(adds_reg, 6, 0, 1)                                         # r6: + 4 / + 8 the master's, + 5 / + 9 the slave's
    E(ldrb_imm, 0, 5, P_SCS); E(cmp_imm, 0, 0); E(b_cond, "sx_c", "ne")
    E(ldrb_imm, 0, 6, 5); E(strb_imm, 0, 5, P_SCP); E(ldrb_imm, 0, 6, 9); E(strb_imm, 0, 5, P_SCT); E(movs_imm, 0, 1); E(strb_imm, 0, 5, P_SCS)
    a.label("sx_c")
    E(ldrb_imm, 0, 6, 4); E(ldrb_imm, 1, 6, 5); E(cmp_reg, 0, 1); E(b_cond, "sx_cp", "ne")
    E(ldrb_imm, 0, 6, 8); E(ldrb_imm, 1, 6, 9); E(cmp_reg, 0, 1); E(b_cond, "sx_x", "eq")
    a.label("sx_cp")
    E(ldrb_imm, 0, 6, 4); E(strb_imm, 0, 6, 5); E(ldrb_imm, 0, 6, 8); E(strb_imm, 0, 6, 9)
    mark(0x20, i=26)
    a.label("sx_x"); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_stled (the LED task's calls: ctrl, frame): the chain; per pair on: the slave's LED, the pick detector, the SC16 bytes
    a.label("c_stled")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, prev["ledtask"])
    E(bl, "c_stst"); E(mov_reg, 6, 0)
    E(movs_imm, 7, 0)
    a.label("ld_p")
    E(ldrb_imm, 0, 6, O_PAIR); E(raw, h(0x40F8)); E(lsls_imm, 0, 0, 31); bc("ld_n", "eq")          # lsrs r0, r7
    E(ldr_imm, 0, 4, 0x6C); E(cmp_imm, 0, 0); E(b_cond, "ld_d", "eq")                            # Setup on the screen: no LED
    E(lsls_imm, 1, 7, 2); E(adds_imm8, 1, 2 * LED0); E(adds_reg, 1, 1, 5)
    E(ldrh_imm, 0, 1, 0); E(movs_imm, 2, 0xFF); E(ands_reg, 0, 2); E(lsls_imm, 2, 7, 5); E(adds_imm8, 2, COL_S[0])
    E(movs_imm, 3, LED_PULSE); E(cmp_reg, 0, 2); E(b_cond, "ld_w", "ne"); E(movs_imm, 3, LED_BLINK)
    a.label("ld_w"); E(lsls_imm, 2, 7, 2); E(adds_reg, 3, 3, 2); E(strh_imm, 3, 1, 0)
    a.label("ld_d")
    E(mov_reg, 0, 7); E(bl, "c_stdet"); E(mov_reg, 0, 7); E(bl, "c_stscs")
    a.label("ld_n"); E(adds_imm8, 7, 1); E(cmp_imm, 7, 2); bc("ld_p", "lo")
    E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_stsg (the group 5 handler: the side-chain): the chain, then each paired slave with its master's knob values
    a.label("c_stsg")
    E(push_list, [4, 5, 6], lr=True)
    E(bl, prev["grp5"])
    E(movs_imm, 6, 0)
    a.label("sc_p")
    E(lsls_imm, 0, 6, 1); E(adds_imm8, 0, 1); E(bl, "c_ston"); E(cmp_imm, 0, 0); bc("sc_n", "eq")
    E(lsls_imm, 5, 6, 1); E(adds_imm8, 5, 1); E(lsls_imm, 4, 6, 1)                    # r5 = the slave (c_wr wants it in r5), r4 = the master
    for i, conv in ((0, S16.CONV_ATK), (1, S16.CONV_HD), (2, S16.CONV_HD)):
        E(mov_reg, 0, 4); E(movs_imm, 1, i); E(bl, L["c_sdval"]); E(bl, conv); E(mov_reg, 1, 0); E(movs_imm, 2, i + 1); E(bl, L["c_wr"])
    E(mov_reg, 0, 4); E(movs_imm, 1, 3); E(bl, L["c_sdval"]); E(lsls_imm, 1, 0, 24); E(movs_imm, 2, 4); E(bl, L["c_wr"])
    a.label("sc_n"); E(adds_imm8, 6, 1); E(cmp_imm, 6, 2); bc("sc_p", "lo")
    E(pop_list, [4, 5, 6], pc=True)

    # ---- c_stblk(r0 = pair) -> r0 = its block in the RAM record (MIDI 1's pattern 5 + pair, settings + 8), 0 without a record; clobbers r1-r3
    a.label("c_stblk")
    imm32(2, SESSION_OBJ); E(ldr_imm, 2, 2, 0x14); E(cmp_imm, 2, 0); E(b_cond, "bk_0", "eq")
    E(adds_imm8, 0, PAT0); imm32(1, PSIZE); E(muls, 0, 1); E(adds_reg, 0, 0, 2); imm32(1, AREA + SET + BYTE0); E(adds_reg, 0, 0, 1); E(raw, RET)
    a.label("bk_0"); E(movs_imm, 0, 0); E(raw, RET)

    # ---- c_stck(r0 = block) -> r0 = its check byte: 0x5A + bytes 0..30; clobbers r1, r2
    a.label("c_stck")
    E(movs_imm, 1, 0); E(movs_imm, 2, 0x5A)
    a.label("ck_l"); E(raw, h(0x5C43)); E(adds_reg, 2, 2, 3); E(adds_imm8, 1, 1); E(cmp_imm, 1, 31); E(b_cond, "ck_l", "lo")   # ldrb r3, [r0, r1]
    E(movs_imm, 0, 0xFF); E(ands_reg, 0, 2); E(raw, RET)

    # ---- c_stsave (the bl of the stock save): each pair's block into the record (when on, or when the block is there), then the chain
    a.label("c_stsave")
    E(raw, pushw([0, 1, 2, 3, 4, 5, 6, 7], lr=True))
    imm32(0, STR); E(ldr_imm, 1, 0, O_SIG); imm32(2, SIG); E(cmp_reg, 1, 2); bc("sv_x", "ne")
    E(movs_imm, 7, 0)
    a.label("sv_p")
    E(mov_reg, 0, 7); E(bl, "c_stblk"); E(cmp_imm, 0, 0); bc("sv_n", "eq"); E(mov_reg, 4, 0)       # r4 = the block
    imm32(0, STR); E(ldrb_imm, 6, 0, O_PAIR); E(raw, h(0x40FE)); E(movs_imm, 0, 1); E(ands_reg, 6, 0)   # lsrs r6, r7: r6 = on
    E(cmp_imm, 6, 0); E(b_cond, "sv_w", "ne"); E(ldrb_imm, 0, 4, 0); E(cmp_imm, 0, BSIG); bc("sv_n", "ne")
    a.label("sv_w")
    E(mov_reg, 0, 7); E(bl, "c_stpb"); E(mov_reg, 5, 0)                                         # r5 = the pair
    E(movs_imm, 0, BSIG); E(strb_imm, 0, 4, 0); E(movs_imm, 0, BVER); E(strb_imm, 0, 4, 1); E(strb_imm, 6, 4, 2)
    E(ldrb_imm, 0, 5, P_K); E(strb_imm, 0, 4, 3); E(ldrb_imm, 0, 5, P_W); E(strb_imm, 0, 4, 4)
    E(movs_imm, 1, 0)
    a.label("sv_d"); E(adds_reg, 2, 5, 1); E(ldrb_imm, 0, 2, P_DEV); E(adds_reg, 2, 4, 1); E(strb_imm, 0, 2, 5); E(adds_imm8, 1, 1)
    E(cmp_imm, 1, 16); E(b_cond, "sv_d", "lo")
    E(ldrb_imm, 0, 5, P_SNAP); E(strb_imm, 0, 4, 21)
    E(movs_imm, 0, 0); E(movs_imm, 1, 22)
    a.label("sv_z"); E(raw, h(0x5460)); E(adds_imm8, 1, 1); E(cmp_imm, 1, 31); E(b_cond, "sv_z", "lo")                       # strb r0, [r4, r1]
    E(mov_reg, 0, 4); E(bl, "c_stck"); E(strb_imm, 0, 4, 31)
    a.label("sv_n"); E(adds_imm8, 7, 1); E(cmp_imm, 7, 2); bc("sv_p", "lo")
    a.label("sv_x"); E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7], lr=True)); E(b_w, prev["save"])

    # ---- c_stload (the load's bl of the re-send 0x08029A00: a load, a new project, power-up): the pairs off, then the project's blocks applied
    a.label("c_stload")
    E(raw, pushw([0, 1, 2, 3, 4, 5, 6, 7], lr=True))
    E(bl, "c_stst"); E(mov_reg, 6, 0)
    E(movs_imm, 7, 0)
    a.label("lo_r")                                                                    # the SC16 bytes given back (no mark: the re-send follows)
    E(mov_reg, 0, 7); E(bl, "c_stpb"); E(mov_reg, 5, 0); E(ldrb_imm, 0, 5, P_SCS); E(cmp_imm, 0, 0); E(b_cond, "lo_rn", "eq")
    E(movs_imm, 0, 0); E(strb_imm, 0, 5, P_SCS)
    E(bl, L["c_scst"]); E(cmp_imm, 0, 0); E(b_cond, "lo_rn", "eq"); E(lsls_imm, 1, 7, 1); E(adds_reg, 0, 0, 1)
    E(ldrb_imm, 1, 5, P_SCP); E(strb_imm, 1, 0, 5); E(ldrb_imm, 1, 5, P_SCT); E(strb_imm, 1, 0, 9)
    a.label("lo_rn"); E(adds_imm8, 7, 1); E(cmp_imm, 7, 2); E(b_cond, "lo_r", "lo")
    E(movs_imm, 0, 0); E(strb_imm, 0, 6, O_PAIR); E(strb_imm, 0, 6, O_HELD)
    E(movs_imm, 7, 0)
    a.label("lo_p")
    E(mov_reg, 0, 7); E(bl, "c_stpb"); E(mov_reg, 5, 0)
    E(movs_imm, 0, 1); E(strb_imm, 0, 5, P_K); E(movs_imm, 0, 127); E(strb_imm, 0, 5, P_W); E(movs_imm, 0, 0xFF); E(strb_imm, 0, 5, P_SNAP)
    E(movs_imm, 0, 0); E(movs_imm, 1, 0)
    a.label("lo_z"); E(adds_reg, 2, 5, 1); E(strb_imm, 0, 2, P_DEV); E(adds_imm8, 1, 1); E(cmp_imm, 1, 16); E(b_cond, "lo_z", "lo")
    E(mov_reg, 0, 7); E(bl, "c_stblk"); E(cmp_imm, 0, 0); bc("lo_n", "eq"); E(mov_reg, 4, 0)
    E(ldrb_imm, 0, 4, 0); E(cmp_imm, 0, BSIG); bc("lo_n", "ne"); E(ldrb_imm, 0, 4, 1); E(cmp_imm, 0, BVER); bc("lo_n", "ne")
    E(mov_reg, 0, 4); E(bl, "c_stck"); E(ldrb_imm, 1, 4, 31); E(cmp_reg, 0, 1); bc("lo_n", "ne")
    E(ldrb_imm, 0, 4, 3); E(movs_imm, 1, 63); E(ands_reg, 0, 1); E(strb_imm, 0, 5, P_K)
    E(ldrb_imm, 0, 4, 4); E(movs_imm, 1, 127); E(ands_reg, 0, 1); E(strb_imm, 0, 5, P_W)
    E(ldrb_imm, 0, 4, 21); E(strb_imm, 0, 5, P_SNAP)
    E(movs_imm, 1, 0)
    a.label("lo_d"); E(adds_reg, 2, 4, 1); E(ldrb_imm, 0, 2, 5); E(adds_reg, 2, 5, 1); E(strb_imm, 0, 2, P_DEV); E(adds_imm8, 1, 1)
    E(cmp_imm, 1, 16); E(b_cond, "lo_d", "lo")
    E(ldrb_imm, 0, 4, 2); E(cmp_imm, 0, 0); E(b_cond, "lo_n", "eq")
    E(movs_imm, 0, 1); E(lsls_reg, 0, 7); E(ldrb_imm, 1, 6, O_PAIR); E(orrs_reg, 1, 0); E(strb_imm, 1, 6, O_PAIR)
    a.label("lo_n"); E(adds_imm8, 7, 1); E(cmp_imm, 7, 2); bc("lo_p", "lo")
    E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7], lr=True)); E(b_w, prev["resend"])
    return a.assemble()


def bl_sites(img, BASE, lo, hi, target):
    """the bl instructions in [lo, hi) whose target is target"""
    out = []
    for at in range(lo, hi, 2):
        try:
            if FD.bl_target(img, at, BASE) == target: out.append(at)
        except Exception:
            pass
    return out


def install(img, report, base_addr):
    """The code at base_addr (hole.add) and every hook of the docstring."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = dict(c_dpword=lab("dpitch", "c_dpword"), c_dpdrum=lab("dpitch", "c_dpdrum"), c_cqon=lab("cue", "c_cqon"), c_mh=lab("sc18", "c_mh"),
             c_dget=lab("persist19", "c_dget"), c_dext_get=lab("persist19", "c_dext_get"), c_xt_get=lab("persist19", "c_xt_get"),
             c_k3get=lab("persist19", "c_k3get"), c_clr_held=lab("persist19", "c_clr_held"), c_shift=lab("sc15", "c_shift"),
             c_scst=lab("sc16", "c_scst"), c_wr=lab("sc16", "c_wr"), c_sdval=lab("scdrum", "c_sdval"), t12=int(report["sc12"]["table"], 16))
    prev = dict(btn=MP.bw_target(img, SV.BTN, BASE), rel=MP.bw_target(img, SV.BTN_REL, BASE), ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE),
                resend=FD.bl_target(img, RESEND_CALL, BASE), save=FD.bl_target(img, P19.SAVE_CALL, BASE), cqg=lab("cue", "c_cqg"),
                dpc1=lab("dpitch", "c_dpc1"), dpc3=lab("dpitch", "c_dpc3"), knob=u(MH_VT + 16) & ~1, led=u(MH_VT + 28) & ~1, grp5=u(GRP5) & ~1)
    assert FD.bl_target(img, PK.LED_CALLS[1], BASE) == prev["ledtask"]
    assert prev["resend"] == 0x08029A00, hex(prev["resend"])
    assert MP.bw_target(img, FUNNEL, BASE) == TRIG and u(PLAYER_VT0) == PLAYER_TICK | 1
    for w, wr in zip(GROUP_WORDS, (WRITERS[0], WRITERS[2])): assert u(w) == wr | 1, hex(w)
    for s in SITES_G: assert FD.bl_target(img, s, BASE) == GETTER, hex(s)
    for s in SITES_C: assert FD.bl_target(img, s, BASE) == prev["cqg"], hex(s)
    for s, d in zip(SITES_PC, (1, 3)): assert FD.bl_target(img, s, BASE) == prev[f"dpc{d}"], hex(s)
    assert prev["knob"] == lab("dpitch", "c_dpknob") and prev["led"] == lab("typeleds", "c_tdleds") and prev["grp5"] == lab("scdrum", "c_sdgrp")
    tick, k3w, lfd = lab("persist19", "c_dtick19"), lab("persist19", "c_k3w"), lab("lfosync", "c_lfd")
    s_dget, s_dext, s_xt = (bl_sites(img, BASE, tick, tick + 0x100, L[k]) for k in ("c_dget", "c_dext_get", "c_xt_get"))
    s_k3 = bl_sites(img, BASE, k3w, k3w + 0x60, L["c_k3get"])
    s_lf = bl_sites(img, BASE, lfd, lfd + 0x10, L["c_dget"])
    assert (len(s_dget), len(s_dext), len(s_xt), len(s_k3), len(s_lf)) == (1, 1, 1, 3, 1), (s_dget, s_dext, s_xt, s_k3, s_lf)
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert STR + NSTR <= MX.MXR + 0x1B00
    put_bl = lambda at, lb: img.__setitem__(slice(at - BASE, at - BASE + 4), bl(at, labels[lb]))
    put_bw = lambda at, lb: img.__setitem__(slice(at - BASE, at - BASE + 4), b_w(at, labels[lb]))
    put_w = lambda at, lb: struct.pack_into("<I", img, at - BASE, labels[lb] | 1)
    put_bw(SV.BTN, "c_stbtn"); put_bw(SV.BTN_REL, "c_strel")
    for c in PK.LED_CALLS: put_bl(c, "c_stled")
    put_bl(RESEND_CALL, "c_stload"); put_bl(P19.SAVE_CALL, "c_stsave")
    put_bw(FUNNEL, "c_sttrig"); put_w(PLAYER_VT0, "c_pstick")
    put_w(GROUP_WORDS[0], "c_stgw0"); put_w(GROUP_WORDS[1], "c_stgw2")
    for s in SITES_G: put_bl(s, "c_stg")
    for s in SITES_C: put_bl(s, "c_stgc")
    put_bl(SITES_PC[0], "c_stpc1"); put_bl(SITES_PC[1], "c_stpc3")
    put_bl(s_dget[0], "c_stdg"); put_bl(s_dext[0], "c_stdx"); put_bl(s_xt[0], "c_stxt")
    for s in s_k3: put_bl(s, "c_stk3")
    put_bl(s_lf[0], "c_stlf")
    import hole
    hole.rehash(img, report, s_lf[0])                                               # lfosync lives in the hole: its block's hash follows the patch
    put_w(MH_VT + 16, "c_stknob"); put_w(MH_VT + 28, "c_stkled"); put_w(GRP5, "c_stsg")
    prev.update(dget_site=s_dget[0], dext_site=s_dext[0], xt_site=s_xt[0], lf_site=s_lf[0])
    return labels, code, prev
