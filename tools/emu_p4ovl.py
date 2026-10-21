"""SC45.9 (tools/p4ovl.py): while Shift + a page-4 knob picks its destination, pads 9-24 show where it lives (as the mod matrix's overlay).

The emulated firmware, MIDI 1's own engine on, its Preset view on page 4 (pad 4), through the controller and the real LED task:
  * Shift + K1 a destination further: pads 9-24 = the destination's page (K1..K8 / Shift + K1..K8: dim with a parameter, bright the destination),
    the page's pad bright (modmx's tables); a pad 9-24 pressed meanwhile goes nowhere;
  * after OVL_MS: the pads as before; K1 alone (no Shift): no overlay;
  * the previous build (if given): no overlay.

    python tools/emu_p4ovl.py BUILD.bin manifest.json [PREVIOUS.bin PREVIOUS_manifest.json]
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402  (its import sets vcf21's options)
import modmx as MX  # noqa: E402
import p4dest as P4  # noqa: E402

V = T4.V


def run(img, man, shift=True):
    e = X.EP(Path(img).read_bytes(), man)
    R = man["report"]
    ml = {k: int(v, 16) for k, v in R["modmx"]["labels"].items()}
    nd = int(R["p4dest"]["prev"]["nd"], 16)
    rd = lambda k, n: bytes(e.uc.mem_read(ml[k], n))
    dcode, dmap, rows = rd("t_dcode", nd), rd("t_dmap", nd), rd("t_rows", 16 * 8)
    pdim, pbri = rd("t_pdim", 8), rd("t_pbri", 8)
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05]))
    e.w32(V.HAL_TICK, 100000)
    e.btn(2); e.btn(8); e.pad(3)
    f0 = X.frame(e)[:32]
    if shift: e.shift(True)
    for _ in range(3 * P4.DIV): e.knob(0, 1)
    if shift: e.shift(False)
    code = tuple(e.uc.mem_read(e.r0(e.vl["c_vrow"], 0), 8))[0]
    f1 = X.frame(e)[:32]
    i = dcode.index(code); pg, at = dmap[i] >> 4, dmap[i] & 15
    want = list(f1)
    for j in range(16): want[8 + j] = 0 if rows[16 * pg + j] == 0 else (pbri[pg] if j == at else pdim[pg])
    want[pg] = pbri[pg]
    prev_pad = int(R["p4ovl"]["prev"]["pad"], 16) if "p4ovl" in R else None
    hits = []
    if prev_pad: e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: hits.append(a), begin=prev_pad, end=prev_pad)
    e.pad(10)
    e.w32(V.HAL_TICK, 100000 + MX.OVL_MS + 100)
    f2 = X.frame(e)[:32]
    out = dict(f0=f0, f1=f1, f2=f2, want=want, code=code, page=pg, swallowed=not hits if prev_pad else None)
    del e; gc.collect()
    return out


def main(img, man, prev=None, pman=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    r = run(img, man)
    check(r["code"] != 17, f"Shift + K1: a new destination (code {r['code']}, page {r['page']})")
    check(r["f1"][8:24] == r["want"][8:24] and r["f1"][r["page"]] == r["want"][r["page"]],
          f"pads 9-24 = the destination's page ({[hex(x) for x in r['f1'][8:24]]} / {[hex(x) for x in r['want'][8:24]]}), its page pad bright")
    check(r["swallowed"] is True, "a pad 9-24 meanwhile goes nowhere")
    check(r["f2"][8:24] == r["f0"][8:24], "after OVL_MS: the pads as before")
    n = run(img, man, shift=False)
    check(n["f1"][8:24] == n["f0"][8:24], "K1 alone: no overlay")
    if prev:
        p = run(prev, pman)
        check(p["f1"][8:24] == p["f0"][8:24], "the previous build: no overlay")
    print(f"{Path(img).stem} RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text()), a[2] if len(a) > 2 else None,
                       json.loads(Path(a[3]).read_text()) if len(a) > 3 else None) else 0)
