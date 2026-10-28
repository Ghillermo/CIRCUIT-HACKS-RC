"""SC48.1 / Beta 3.38 (the user, 2026-10-27: «Add metronome on Cue listen only (when metronome and Cue listen are enabled)»): with the Mixer's cue
mode on (cue.py: the left output = the main, the right = the cue), the metronome's click sounds only on the right.

The stock (read in the DSP program, emulated): the clock sends the click trigger to Y:$111 (countin: 0x0803BD58(0xFF, 0, 0x60) -> master
parameter 0x21:9); the block function ($1D9) ends with `jsr $2277`, the click: a parabola-sine burst with its envelope, phase and increment at
X:$1F68..$1F6A, added in a `dor n1` loop to the output ring itself (r7 = Y:$FFD, M7 = $3FF: L and R of each frame in a row, after the master
filter, Master FX and the compressor), the same sample on both sides:
    $2291  move #>$7fc000,x1                  (the envelope's decay)
    $2293  dor n1, ...
    $229B  move x:(r7)+,b  b,y0 / mac y1,y0,b x:(r7)-,a / mac y1,y0,a (r5)+n5 / move b,x:(r7)+ / move a,x:(r7)+
A track's pan cannot move it: the cue mode needs the DSP.

Ours:
  * the loop body with two pointers, the same five words: `move x:(r6),b b,y0 / mac y1,y0,b x:(r7),a / mac y1,y0,a (r5)+n5 /
    move b,x:(r6)+n6 / move a,x:(r7)+n7`;
  * $2291 -> `jsr cc_setup` (appended to core 0): the stock's x1, n6 = n7 = 2, r6 = the frame's L, r7 = its R; with X:FLAG != 0 r6 = R too
    (`tne`): both halves read R, add the click and write R (the same value twice); L is not touched.  Without the flag the arithmetic is the
    stock's word for word.  r6 / n6 / n7 are free there: the block function returns to the main loop ($113), which sets them again before use;
    M6 stays linear (set once at boot) and a block's 64 words never cross the ring's end (Y:$FFD moves by 64 from an aligned start);
  * the ARM: a new head of the DSP service chain writes X:FLAG = cue.c_cqon() (1 = the cue mode on) when it changes and every REFRESH ticks
    (one SPI write; the DSP's RAM is not cleared at power-on).  The count-in's clicks (countin) are the same click: in the cue mode they go to
    the cue as well.
DSP: X:$3FF0 (free: X $3FE8-$3FFF); core 0 + 11 words (room made by dsp56.use_shortmsb).  RAM: modmx.MXR + 0x1AC0 (2 B, no signature: a wrong
byte only delays the first write).  In the hole (no card)."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b_cond, b_w, bl, cmp_reg, h, ldrb_imm, lsls_imm, mov_reg, movs_imm, movt, movw, raw, strb_imm, subs_imm8)  # noqa: E402
import dsp56 as D  # noqa: E402
import masterfx_dsp as G  # noqa: E402
import build_sc14 as S14  # noqa: E402
import mpatch as MP  # noqa: E402
import modmx as MX  # noqa: E402

FLAG = 0x3FF0
RAM = MX.MXR + 0x1AC0                                  # + 0 the flag last written, + 1 the ticks to the refresh
REFRESH = 250
DSP_WRITE = 0x080292F8
DSP_TAB = 0x08029700                                   # the core-0 block's pointer (the relocated program)
AT_X1, AT_BODY = 0x2291, 0x229B
STOCK_X1 = [0x45F400, 0x7FC000]                        # move #>$7fc000,x1
STOCK_BODY = [0x1E9F00, 0x56D7BA, 0x204DB2, 0x575F00, 0x565F00]
NEW_BODY = [0x1EA600, 0x56E7BA, 0x204DB2, 0x574E00, 0x564F00]   # move x:(r6),b b,y0 / mac y1,y0,b x:(r7),a / mac y1,y0,a (r5)+n5 / b -> (r6)+n6 / a -> (r7)+n7


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def dsp_code(base):
    a = D.Asm(base)
    a.label("cc_setup")
    a.emit(G.T("move #>$7fc000,x1", "move #2,n7", "move n7,n6", "move r7,r6", "move (r7)+",
               "move x:>$%x,b" % FLAG, "tst b", "tne x0,a r7,r6", "rts"))
    a.label("cc_end")
    return a.assemble()


def install_dsp(s16):
    """Before building: cc_setup appended to the (wrapped) core-0 code, after everything (sampler_dsp's sm_se)."""
    prev = s16.dsp_code
    def wrapped(base):
        w, l = prev(base)
        w2, l2 = dsp_code(base + len(w))
        return w + w2, {**l, **l2}
    s16.dsp_code = wrapped


def patch_dsp(img, report):
    """After building: the stock click's x1 load -> jsr cc_setup, its loop body -> the two pointers."""
    import ct_fw
    dl = {k: int(v, 16) for k, v in report["sc16"]["dsp_labels"].items()}
    assert dl["cc_end"] <= 0x4000, hex(dl["cc_end"])
    tab = struct.unpack_from("<I", img, DSP_TAB - ct_fw.APP_BASE)[0]
    o = lambda at: tab - ct_fw.APP_BASE + 6 + 3 * at
    def put(at, words, old):
        cur = [int.from_bytes(img[o(at) + 3 * i:o(at) + 3 * i + 3], 'big') for i in range(len(old))]
        assert cur == old, (hex(at), [hex(x) for x in cur])
        for i, w_ in enumerate(words): img[o(at) + 3 * i:o(at) + 3 * i + 3] = w_.to_bytes(3, 'big')
    put(AT_X1, D.jsr(dl["cc_setup"]), STOCK_X1)
    put(AT_BODY, NEW_BODY, STOCK_BODY)
    report["cueclk_dsp"] = dict(cc_setup=hex(dl["cc_setup"]), cc_end=hex(dl["cc_end"]), flag=hex(FLAG))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)

    # ---- c_cchead (the head of the DSP service chain): X:FLAG = the cue mode, when it changes and every REFRESH ticks
    a.label("c_cchead")
    E(raw, pushw([0, 1, 2, 3, 4, 5], lr=True))
    E(bl, L["c_cqon"]); E(mov_reg, 4, 0)
    imm32(5, RAM); E(ldrb_imm, 0, 5, 0); E(cmp_reg, 0, 4); E(b_cond, "ch_w", "ne")
    E(ldrb_imm, 0, 5, 1); E(subs_imm8, 0, 1); E(strb_imm, 0, 5, 1); E(b_cond, "ch_x", "ne")
    a.label("ch_w")
    E(strb_imm, 4, 5, 0); E(movs_imm, 0, REFRESH); E(strb_imm, 0, 5, 1)
    E(lsls_imm, 1, 4, 8); E(movw, 2, FLAG); E(movs_imm, 0, 0); E(bl, DSP_WRITE)
    a.label("ch_x")
    E(raw, popw([0, 1, 2, 3, 4, 5], lr=True)); E(b_w, prev["svc"])
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the head of the DSP service chain."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    L = dict(c_cqon=int(report["cue"]["labels"]["c_cqon"], 16))
    prev = dict(svc=MP.bw_target(img, S14.SVC_HOOK, BASE))
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    img[S14.SVC_HOOK - BASE:S14.SVC_HOOK - BASE + 4] = b_w(S14.SVC_HOOK, labels["c_cchead"])
    assert RAM + 2 <= MX.MXR + 0x1B00
    return labels, code, prev
