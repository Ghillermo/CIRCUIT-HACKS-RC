"""Line input v2 for the synth noise source (SC16.1 / SC17.1): +6 dB and phase-inverted modes.

Modes per synth (Shift + pads 25..29 in the synth Preset view):
  0 Noise (stock)   1 Input 1   2 Input 2   3 Input 1 inverted   4 Input 2 inverted
Inputs are taken x2 (+6 dB, saturating); inverted modes are x(-2).

DSP: P:$9C3 jmp l2_hook (instead of SC15's li_hook).  Once per block and synth (cache tag = y:$FFD
and mode) the input frames of the chosen channel are copied, scaled and optionally negated, to
Y:$3A00 (Synth 1) / Y:$3A40 (Synth 2); the voice then reads that buffer with step 1.
  X:$3A03/$3A04 tag frame pointer, X:$3A05/$3A06 tag mode, X:$3A07/$3A08 saved r4 / m4.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dsp56 as D  # noqa: E402
import masterfx_dsp as G  # noqa: E402

MODE_S = (0x3A01, 0x3A02)
TAGF, TAGM = (0x3A03, 0x3A04), (0x3A05, 0x3A06)
SAVE_R4, SAVE_M4 = 0x3A07, 0x3A08
YBUF = (0x3A00, 0x3A40)
HOOK_AT, HOOK_RET = 0x9C3, 0x9C5
SYNTH = 0xCC
N_MODES = 5
T, J = G.T, G.J


def code(base):
    a = D.Asm(base)
    def ld(addr, reg): a.emit(T("move x:>$%x,%s" % (addr, reg)))
    def st(reg, addr): a.emit(T("move %s,x:>$%x" % (reg, addr)))
    a.label("l2_hook")
    ld(SYNTH, "a"); a.emit(T("tst a")); a.emit(J("ne"), "l2_s1")
    for s in (0, 1):
        a.label("l2_s%d" % s)
        ld(MODE_S[s], "b"); a.emit(T("tst b")); a.emit(J("eq"), "l2_stock")
        a.emit(T("move y:>$ffd,a"))
        ld(TAGF[s], "x0"); a.emit(T("cmp x0,a")); a.emit(J("ne"), "l2_fill%d" % s)
        ld(TAGM[s], "x0"); a.emit(T("cmp x0,b")); a.emit(J("eq"), "l2_use%d" % s)
        a.label("l2_fill%d" % s)
        st("a", TAGF[s]); st("b", TAGM[s])
        a.emit(T("move r4,x:>$%x" % SAVE_R4)); a.emit(T("move m4,x:>$%x" % SAVE_M4))
        a.emit(T("move #>$ffff,m4"))
        a.emit(T("move #>$%x,r4" % YBUF[s])); a.emit(T("move #2,n2"))
        a.emit(T("cmp #3,b")); a.emit(J("ge"), "l2_inv%d" % s)
        a.emit(T("sub #1,b")); a.emit(T("add b,a")); a.emit(T("move a,r2"))
        a.emit(D.do_x, 0x3A, "l2_e%d" % s)
        a.emit(T("move y:(r2)+n2,a")); a.emit(T("asl a"))
        a.label("l2_e%d" % s); a.emit(T("move a,y:(r4)+"))
        a.emit(J("al"), "l2_rest%d" % s)
        a.label("l2_inv%d" % s)
        a.emit(T("sub #3,b")); a.emit(T("add b,a")); a.emit(T("move a,r2"))
        a.emit(D.do_x, 0x3A, "l2_n%d" % s)
        a.emit(T("move y:(r2)+n2,a")); a.emit(T("asl a")); a.emit(T("neg a"))
        a.label("l2_n%d" % s); a.emit(T("move a,y:(r4)+"))
        a.label("l2_rest%d" % s)
        a.emit(T("move x:>$%x,m4" % SAVE_M4)); a.emit(T("move x:>$%x,r4" % SAVE_R4))
        a.label("l2_use%d" % s)
        a.emit(T("move #>$%x,r2" % YBUF[s])); a.emit(T("move #1,n2"))
        a.emit(J("al"), HOOK_RET)
    a.label("l2_stock")
    a.emit(T("move (r2)+n2")); a.emit(T("move #4,n2")); a.emit(J("al"), HOOK_RET)
    return a.assemble()


def install(s15, s16):
    """Before building: 5 UI modes, and l2 code appended to the (possibly already wrapped) SC16 DSP code."""
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
    patch_p(img, HOOK_AT, [0x0AF080, old], [0x0AF080, dl["l2_hook"]])


def patch_p(img, p, old, new):
    """patch DSP P words in the relocated core-0 block (loader table) and in the original block."""
    import struct
    import build_sc10 as s10
    tab = struct.unpack_from("<I", img, 0x08029700 - 0x08010000)[0]
    for blk in (tab, s10.DSP0):
        o = blk - 0x08010000 + 6 + 3 * p
        cur = [int.from_bytes(img[o + 3 * i:o + 3 * i + 3], 'big') for i in range(len(old))]
        assert cur == old, (hex(blk), hex(p), [hex(x) for x in cur])
        for i, w in enumerate(new):
            img[o + 3 * i:o + 3 * i + 3] = w.to_bytes(3, 'big')


def main(name, build, s15, argv):
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
    patch_hook(img, report, patch_p)
    report["D"]["marker"] = name
    report["linein2"] = dict(hook=report["sc16"]["dsp_labels"]["l2_hook"], ybuf=[hex(x) for x in YBUF], modes=N_MODES)
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
