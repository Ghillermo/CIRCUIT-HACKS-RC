"""Line input v3 for the synth noise source (SC17.5): linein2 + delay / reverb returns as sources.

Modes per synth (Shift + pads 25..31 in the synth Preset view):
  0 Noise (stock)   1 Input 1   2 Input 2   3 Input 1 inverted   4 Input 2 inverted
  5 Delay return    6 Reverb return
Modes 0-4 behave exactly as in linein2 (same code, relabelled).  Modes 5 / 6 read the output of the delay /
reverb, captured one block earlier, so a synth can be fed with its own (or the other synth's / drums') echoes.

DSP (core 0):
  P:$D22 (operand of the `jsr int_00009f` SC10 put at P:$D21, i.e. just after the reverb has run and before the
         stock return mix) -> fx_cap: only while a synth uses mode 5 or 6 (X:$3A01 / X:$3A02 >= 5), copies the mono sum L + R (saturating) of the delay output Y:$9C0.. and of the
         reverb output Y:$880.. (x:$3a stereo frames each) to Y:$3A80.. (delay) / Y:$3AC0.. (reverb), then jmp $9F.
         The voices of the next block read those buffers with step 1 (same as the line-input copies).
  P:$9C3 -> l3_hook: l2_hook for modes 0-4; modes >= 5 skip the cache and point r2 at the capture buffer.
  X:$3A03/$3A04 tag frame pointer, X:$3A05/$3A06 tag mode, X:$3A07/$3A08 saved r4 / m4 (as linein2).
  Y:$3A00 / Y:$3A40 line-input copies (linein2), Y:$3A80 delay, Y:$3AC0 reverb (X/Y:$3339..$3BFF is free memory).
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dsp56 as D  # noqa: E402
import masterfx_dsp as G  # noqa: E402
import linein2 as L2  # noqa: E402

MODE_S, TAGF, TAGM, SAVE_R4, SAVE_M4, YBUF = L2.MODE_S, L2.TAGF, L2.TAGM, L2.SAVE_R4, L2.SAVE_M4, L2.YBUF
HOOK_AT, HOOK_RET, SYNTH = L2.HOOK_AT, L2.HOOK_RET, L2.SYNTH
N_MODES = 7
FX_GAIN_SHIFT = 0                     # SC17.7: 3 -> the captured (L + R) is shifted left by 3 (x16 of the average): the returns
                                      # live in the mixer's -24 dB domain (strip gain 0.0615), far below the line inputs
SETUP_RET = False                     # SC19.5: while the Setup sends the reverb return to strip 3 (X:$3A00 bit 0) / the delay return to strip 4 (bit 1), the synth's
                                      # "input 1" / "input 1 inverted" (modes 1 / 3) read the reverb return and "input 2" / "input 2 inverted" (modes 2 / 4) the delay return
SYNTH_RET = True                      # SC21.1: False = the synths no longer read the FX returns (modes 1-4 always read the line input); fx_cap still captures them every block
                                      # while a return is wired to a strip (SETUP_RET), for the feedback of tools/vcf21_dsp.py
FX_MODES = True                       # SC21.1: False = no code for the modes 5 / 6 (needs N_MODES = 5)
SETUP_FLAGS = 0x3A00                  # SC10's FX-return flags (X word: bit 0 reverb -> strip 3 = audio in 1, bit 1 delay -> strip 4 = audio in 2)
METER = False                         # SC20D: fx_cap runs every block (not only for modes 5 / 6) and leaves the mean |L + R| of each capture in Y:$3B00 / Y:$3B01
METER_Y = (0x3B00, 0x3B01)
METER_CHECK, METER_MAGIC = 0x3B02, 0x5A3C69   # Y:$3B02 = a constant the ARM reads back to prove the DSP read path works
FXBUF = (0x3A80, 0x3AC0)              # Y: delay, reverb (mono, x:$3a words)
DELAY_OUT, REVERB_OUT = 0x9C0, 0x880  # Y: stereo frames [L, R] at P:$D21
RET_AT = 0xD21                        # jsr int_00009f (SC10 `returns`)
RET_OLD = 0x9F
T, J = G.T, G.J


def code(base):
    a = D.Asm(base)
    def ld(addr, reg): a.emit(T("move x:>$%x,%s" % (addr, reg)))
    def st(reg, addr): a.emit(T("move %s,x:>$%x" % (reg, addr)))
    a.label("l3_hook")
    ld(SYNTH, "a"); a.emit(T("tst a")); a.emit(J("ne"), "l3_s1")
    for s in (0, 1):
        a.label("l3_s%d" % s)
        ld(MODE_S[s], "b"); a.emit(T("tst b")); a.emit(J("eq"), "l3_stock")
        if FX_MODES: a.emit(T("cmp #5,b")); a.emit(J("ge"), "l3_fx")
        if SETUP_RET and SYNTH_RET:                                   # b = 1..4: does the Setup replace this input by an FX return?  r2 = the capture buffer (r2 is set again at the end)
            ld(SETUP_FLAGS, "a")
            a.emit(T("cmp #2,b")); a.emit(J("eq"), "l3_c2%d" % s)
            a.emit(T("cmp #4,b")); a.emit(J("eq"), "l3_c2%d" % s)
            a.emit(D.jclr_a1, 0, "l3_ns%d" % s)           # input 1 / input 1 inverted: only with the reverb -> strip 3 flag
            a.emit(T("move #>$%x,r2" % FXBUF[1])); a.emit(J("al"), "l3_sr%d" % s)
            a.label("l3_c2%d" % s)
            a.emit(D.jclr_a1, 1, "l3_ns%d" % s)           # input 2 / input 2 inverted: only with the delay -> strip 4 flag
            a.emit(T("move #>$%x,r2" % FXBUF[0]))
            a.label("l3_sr%d" % s)
            a.emit(T("cmp #3,b")); a.emit(J("ge"), "l3_si%d" % s)
            a.emit(T("move #1,n2")); a.emit(J("al"), HOOK_RET)                 # not inverted: the capture itself (as modes 5 / 6)
            a.label("l3_si%d" % s)                        # inverted: -capture into this synth's buffer (cache tag = frame pointer + mode code 11 / 12)
            a.emit(T("add #8,b")); a.emit(T("move y:>$ffd,a"))
            ld(TAGF[s], "x0"); a.emit(T("cmp x0,a")); a.emit(J("ne"), "l3_sf%d" % s)
            ld(TAGM[s], "x0"); a.emit(T("cmp x0,b")); a.emit(J("eq"), "l3_use%d" % s)
            a.label("l3_sf%d" % s)
            st("a", TAGF[s]); st("b", TAGM[s])
            a.emit(T("move r4,x:>$%x" % SAVE_R4)); a.emit(T("move m4,x:>$%x" % SAVE_M4))
            a.emit(T("move #>$ffff,m4")); a.emit(T("move #>$%x,r4" % YBUF[s])); a.emit(T("move #1,n2"))
            a.emit(D.do_x, 0x3A, "l3_sn%d" % s)
            a.emit(T("move y:(r2)+n2,a")); a.emit(T("neg a"))
            a.label("l3_sn%d" % s); a.emit(T("move a,y:(r4)+"))
            a.emit(J("al"), "l3_rest%d" % s)
            a.label("l3_ns%d" % s)
        a.emit(T("move y:>$ffd,a"))
        ld(TAGF[s], "x0"); a.emit(T("cmp x0,a")); a.emit(J("ne"), "l3_fill%d" % s)
        ld(TAGM[s], "x0"); a.emit(T("cmp x0,b")); a.emit(J("eq"), "l3_use%d" % s)
        a.label("l3_fill%d" % s)
        st("a", TAGF[s]); st("b", TAGM[s])
        a.emit(T("move r4,x:>$%x" % SAVE_R4)); a.emit(T("move m4,x:>$%x" % SAVE_M4))
        a.emit(T("move #>$ffff,m4"))
        a.emit(T("move #>$%x,r4" % YBUF[s])); a.emit(T("move #2,n2"))
        a.emit(T("cmp #3,b")); a.emit(J("ge"), "l3_inv%d" % s)
        a.emit(T("sub #1,b")); a.emit(T("add b,a")); a.emit(T("move a,r2"))
        a.emit(D.do_x, 0x3A, "l3_e%d" % s)
        a.emit(T("move y:(r2)+n2,a")); a.emit(T("asl a"))
        a.label("l3_e%d" % s); a.emit(T("move a,y:(r4)+"))
        a.emit(J("al"), "l3_rest%d" % s)
        a.label("l3_inv%d" % s)
        a.emit(T("sub #3,b")); a.emit(T("add b,a")); a.emit(T("move a,r2"))
        a.emit(D.do_x, 0x3A, "l3_n%d" % s)
        a.emit(T("move y:(r2)+n2,a")); a.emit(T("asl a")); a.emit(T("neg a"))
        a.label("l3_n%d" % s); a.emit(T("move a,y:(r4)+"))
        a.label("l3_rest%d" % s)
        a.emit(T("move x:>$%x,m4" % SAVE_M4)); a.emit(T("move x:>$%x,r4" % SAVE_R4))
        a.label("l3_use%d" % s)
        a.emit(T("move #>$%x,r2" % YBUF[s])); a.emit(T("move #1,n2"))
        a.emit(J("al"), HOOK_RET)
    if FX_MODES:
        a.label("l3_fx")                                # b = 5 delay / 6 reverb (any synth)
        a.emit(T("move #>$%x,r2" % FXBUF[0]))
        a.emit(T("cmp #6,b")); a.emit(J("ne"), "l3_fxn")
        a.emit(T("move #>$%x,r2" % FXBUF[1]))
        a.label("l3_fxn")
        a.emit(T("move #1,n2")); a.emit(J("al"), HOOK_RET)
    a.label("l3_stock")
    a.emit(T("move (r2)+n2")); a.emit(T("move #4,n2")); a.emit(J("al"), HOOK_RET)

    a.label("fx_cap")                                   # called from P:$D21; a, b, x0, r0, r1 free (SC10 returns reloads r6/r7)
    if not METER:
        if SETUP_RET:
            ld(SETUP_FLAGS, "a"); a.emit(T("tst a")); a.emit(J("ne"), "fc_do")     # an FX return is wired to a strip: the synths may be reading it
        if FX_MODES:
            ld(MODE_S[0], "a"); ld(MODE_S[1], "b")      # capture only while a synth uses mode 5 / 6 (else ~8 instructions)
            a.emit(T("cmp #5,a")); a.emit(J("ge"), "fc_do")
            a.emit(T("cmp #5,b")); a.emit(J("lt"), "fc_skip")
        else:
            a.emit(J("al"), "fc_skip")
    a.label("fc_do")
    for k, src in enumerate((DELAY_OUT, REVERB_OUT)):
        a.emit(T("move #>$%x,r0" % src)); a.emit(T("move #>$%x,r1" % FXBUF[k]))
        if METER: a.emit(T("move #0,y1"))               # y1 is dead at P:$D21 (reloaded in the final mix); running sum of |L + R| / 32
        a.emit(D.do_x, 0x3A, "fc_e%d" % k)
        a.emit(T("move y:(r0)+,a")); a.emit(T("move y:(r0)+,b")); a.emit(T("add b,a"))
        if FX_GAIN_SHIFT: a.emit(T("asl #%d,a,a" % FX_GAIN_SHIFT))
        if METER:
            a.emit(T("move a,y:(r1)+"))
            a.emit(T("abs a")); a.emit(T("asr #5,a,a")); a.emit(T("add y1,a"))
            a.label("fc_e%d" % k); a.emit(T("move a,y1"))
            a.emit(T("move y1,y:>$%x" % METER_Y[k]))
        else:
            a.label("fc_e%d" % k); a.emit(T("move a,y:(r1)+"))
    a.label("fc_skip")
    if METER:
        a.emit(T("move #>$%x,x0" % METER_MAGIC)); a.emit(T("move x0,y:>$%x" % METER_CHECK))
    a.label("fc_jmp")
    a.emit(J("al"), RET_OLD)                            # SC10 returns: its rts goes back to P:$D23
    return a.assemble()


def install(s15, s16):
    """Before building: 7 UI modes, and the l3 code appended to the (possibly already wrapped) SC16 DSP code."""
    s15.N_MODES = N_MODES
    prev = s16.dsp_code
    def wrapped(base):
        w, l = prev(base)
        w2, l2 = code(base + len(w))
        return w + w2, {**l, **l2}
    s16.dsp_code = wrapped


def patch_hook(img, report, patch_p):
    dl = {k: int(v, 16) for k, v in report["sc16"]["dsp_labels"].items()}
    old = int(report["sc15"]["dsp_labels"]["li_hook"], 16)
    patch_p(img, HOOK_AT, [0x0AF080, old], [0x0AF080, dl["l3_hook"]])
    patch_p(img, RET_AT, [0x0BF080, RET_OLD], [0x0BF080, dl["fx_cap"]])


def main(name, build, s15, argv, extra=None):
    """As linein2.main; `extra(img, report)` may patch the image further before it is encoded."""
    import argparse, json
    import ct_fw
    import build_shared_channels as sc
    ap = argparse.ArgumentParser()
    ap.add_argument("stock_bin", type=Path)
    ap.add_argument("--listing", type=Path, default=Path(__file__).resolve().parents[1] / "re/app.asm")
    ap.add_argument("-o", "--outdir", type=Path, default=Path("build") / name.lower())
    args = ap.parse_args(argv)
    stock = args.stock_bin.read_bytes()
    img, report = build(stock, args.listing)
    img = bytearray(img)
    marker = name.encode().ljust(6, b"\0")[:6]
    img[sc.MARK_OFF:sc.MARK_OFF + 6] = marker
    patch_hook(img, report, L2.patch_p)
    report["D"]["marker"] = name
    report["linein3"] = dict(hook=report["sc16"]["dsp_labels"]["l3_hook"], fx_cap=report["sc16"]["dsp_labels"]["fx_cap"],
                             ybuf=[hex(x) for x in YBUF], fxbuf=[hex(x) for x in FXBUF], modes=N_MODES, fx_gain_shift=FX_GAIN_SHIFT,
                             **({"meter": [hex(x) for x in METER_Y]} if METER else {}), **({"setup_ret": hex(SETUP_FLAGS)} if SETUP_RET else {}), **({"synth_ret": False} if not SYNTH_RET else {}), **({"fx_modes": False} if not FX_MODES else {}))
    if extra: extra(img, report)
    img = bytes(img)
    syx = ct_fw.encode(img)
    info = ct_fw.decode(syx)
    assert info["image"] == img
    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / f"circuittracks-4486-{name}.bin").write_bytes(img)
    (args.outdir / f"circuittracks-4486-{name}.syx").write_bytes(syx)
    manifest = dict(base="circuittracks-firmware-4486 (1.2.1)", marker=name, image_size=hex(len(img)),
                    image_sha256=ct_fw.sha256(img), syx_sha256=ct_fw.sha256(syx), crc32=hex(info["crc"]), report=report)
    (args.outdir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print("image", hex(len(img)), "syx sha", manifest["syx_sha256"], "crc", manifest["crc32"])
