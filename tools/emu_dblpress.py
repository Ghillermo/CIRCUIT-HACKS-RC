"""SC48.3 / Beta 3.40: double presses that match the Shift shortcuts (cscale.use_dbl, dblpress) and the knob pages of MIDI 1 / 2 held 1/2 s or
more (pghold), through the controller (emu_sc42_6's harness):
  * Scales: a press = the stock's Scales view, the editor off; again = the editor on (as Shift + Scales); again = off;
  * Velocity: from the Note view, the first press = the Velocity view, fixed velocity unchanged; again = toggled (as the stock's Shift + Velocity,
    which toggles it too); again = back;
  * Shift + Synth 1 from the Mixer = what Synth 1's double press gives (its sub-mode, srcview's source-view flag); Shift + MIDI 1 from the Mixer
    = MIDI 1's Preset view; the Shift byte is 1 again after;
  * MIDI 1, the engine on: pad 2 tapped (100 ms) = page 2 kept; pad 4 held 600 ms = page 4, back to page 2 on the release; Shift + pad 4 held =
    the non-sequenceable page, back on the release; Shift + pad 4 tapped = kept.

    python tools/emu_dblpress.py SC48.3.bin SC48.3_manifest.json
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402  (its import sets vcf21's options)
import cscale as CS  # noqa: E402
import srcview as SV  # noqa: E402

V = T4.V
MGR = X.MGR
PRESS, RELEASE = X.T.PRESS, X.T.RELEASE
ID_SCALES, ID_VEL, ID_NOTE, ID_MIXER = 18, 10, 9, 14


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = X.EP(img, man)
    R = man["report"]
    gst = int(R["sc14"]["labels"]["c_gst"], 16)
    csblk = int(R["cscale"]["labels"]["c_csblk"], 16)
    sub = lambda: e.r8(MGR + SV.S_CUR)
    view = lambda: e.r32(MGR + 0x6C)
    shift_byte = lambda: e.r8(e.r0(0x0803542C, e.r32(MGR + 0xC), 0))
    fixed = lambda: e.r32(e.r0(0x0803542C, e.r32(MGR + 0x78), 2)) >> 1 & 1
    src = lambda: e.r8(e.r0(gst) + 20) & SV.F_SRC
    # Scales
    e.btn(0); e.btn(ID_SCALES)
    blk = e.r0(csblk)
    ed = lambda: e.r8(blk + CS.B_ED) if blk else -1
    v1, e1 = view(), ed()
    e.btn(ID_SCALES); e2, v2 = ed(), view()
    e.btn(ID_SCALES); e3, v3 = ed(), view()
    check(blk and v1 == CS.SCALES_VIEW and e1 == 0 and e2 == 1 and v2 == CS.SCALES_VIEW and e3 == 0 and v3 == CS.SCALES_VIEW,
          f"Scales: the stock view, editor {e1}; again = editor {e2}; again = {e3} (views {v1:#x} {v2:#x} {v3:#x})")
    # Velocity
    e.btn(0); e.btn(ID_NOTE); f0 = fixed()
    e.btn(ID_VEL); s1, f1 = sub(), fixed()
    e.btn(ID_VEL); f2 = fixed()
    e.btn(ID_VEL); f3 = fixed()
    e.shift(True); e.btn(ID_VEL); e.shift(False); f4 = fixed()
    check(s1 == 2 and f1 == f0 and f2 == 1 - f0 and f3 == f0 and f4 == 1 - f0,
          f"Velocity: the view (sub {s1}), fixed {f0} -> {f1}; again {f2}; again {f3}; the stock's Shift + Velocity {f4}")
    e.shift(True); e.btn(ID_VEL); e.shift(False)
    # Shift + Synth 1 = Synth 1 twice (from the Mixer: its Note view, then the source view)
    e.btn(ID_MIXER); e.btn(0); e.btn(0); want = (sub(), src()); e.btn(ID_MIXER)
    s0 = sub(); e.shift(True); e.btn(0); sb = shift_byte(); e.shift(False); got = (sub(), src())
    check(want[1] and got == want and s0 != got[0] and sb == 1, f"Shift + Synth 1 from the Mixer (sub {s0}): {got} = the double press {want}; Shift byte {sb}")
    e.btn(ID_MIXER)
    e.shift(True); e.btn(2); e.shift(False); sm = sub()
    check(sm == 9 * 2, f"Shift + MIDI 1 from the Mixer: MIDI 1's Preset view (sub {sm}, want 18)")
    # pghold: MIDI 1's knob pages
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05]))
    e.btn(2); e.btn(8)
    page = lambda: e.r0(e.vl["c_vpage"], 0)
    def hold(q, ms, sh=False):
        if sh: e.shift(True)
        e.call(PRESS, MGR, q, 100, maxins=8_000_000)
        if sh: e.shift(False)
        p = page(); e.at(e.t + ms); e.call(RELEASE, MGR, q, maxins=8_000_000); return p, page()
    e.at(e.t + 1000)
    tap = hold(1, 100)
    held = hold(3, 600)
    ns = hold(3, 700, sh=True)
    nst = hold(3, 100, sh=True)
    check(tap == (1, 1) and held == (3, 1) and ns == (V.NS_PAGE, 1) and nst == (V.NS_PAGE, V.NS_PAGE),
          f"pages: pad 2 tapped {tap}, pad 4 held {held}, Shift + pad 4 held {ns}, tapped {nst}")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} DBLPRESS RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
