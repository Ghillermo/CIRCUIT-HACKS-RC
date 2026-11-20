"""Alpha 7.10 test (tools/laneclr.py; the user, 2026-11-19: «Clear knob clears lane» -> «Clear, all patterns»), through the controller:
  * MIDI 1's 8 patterns with values in lanes 0-2 (and MIDI 2's lane 1);
  * on the assigned-knob view (pad 1 = page 4), Duplicate + K2 frees slot 2: lane 1 = 0xFF in all 8 patterns of MIDI 1; lanes 0 / 2 and MIDI 2
    untouched; the pattern store told (STORE_W called);
  * the non-sequenceable view (Shift + pad 1): Duplicate + K1 frees its slot 1, no lane touched.

    python tools/emu_laneclr.py BUILD.bin manifest.json
"""
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402  (its import sets vcf21's options)
import laneclr as LC  # noqa: E402
import vcf21 as V  # noqa: E402

MGR, DUPB = 0x20040B10, 24


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = X.EP(img, man); R = man["report"]
    sdrec = int(R["vcf20"]["labels"]["c_sdrec"], 16)
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05]))
    dup = lambda v: e.call(0x08033320 if v else 0x0803381A, MGR, DUPB, maxins=8_000_000)
    base = [e.r32(e.r0(sdrec, t) + 0x48) for t in (0, 1)]
    lane = lambda t, p, k: bytes(e.uc.mem_read(base[t] + LC.PAT_SZ * p + LC.LANES + LC.LANE_SZ * k, LC.LANE_SZ))
    for p in range(8):
        for k in range(3): e.uc.mem_write(base[0] + LC.PAT_SZ * p + LC.LANES + LC.LANE_SZ * k, bytes([0x10 + 16 * k + p]) * LC.LANE_SZ)
        e.uc.mem_write(base[1] + LC.PAT_SZ * p + LC.LANES + LC.LANE_SZ, bytes([0x60 + p]) * LC.LANE_SZ)
    seen = []
    e.uc.hook_add(1 << 2, lambda uc, a, s, d: seen.append(a), begin=LC.STORE_W, end=LC.STORE_W + 1) if False else None
    import unicorn
    e.uc.hook_add(unicorn.UC_HOOK_CODE, lambda uc, a, s, d: seen.append(a), begin=LC.STORE_W, end=LC.STORE_W + 1)
    e.btn(2); e.btn(8); e.pad(0)
    row = lambda: tuple(e.uc.mem_read(e.r0(e.vl["c_vrow"], 0), 8))
    dup(True); e.knob(1, 1); dup(False)
    check(row()[1] == 0, f"pad 1, Duplicate + K2: slot 2 freed ({row()})")
    check(all(lane(0, p, 1) == b"\xFF" * LC.LANE_SZ for p in range(8)), "lane 1 of MIDI 1 = 0xFF in all 8 patterns")
    check(all(lane(0, p, 0) == bytes([0x10 + p]) * LC.LANE_SZ and lane(0, p, 2) == bytes([0x30 + p]) * LC.LANE_SZ for p in range(8)), "lanes 0 / 2 untouched")
    check(all(lane(1, p, 1) == bytes([0x60 + p]) * LC.LANE_SZ for p in range(8)), "MIDI 2's lane 1 untouched")
    check(len(seen) >= 1, f"the pattern store told ({len(seen)} call(s) of {LC.STORE_W:#x})")
    for p in range(8): e.uc.mem_write(base[0] + LC.PAT_SZ * p + LC.LANES, bytes([0x10 + p]) * LC.LANE_SZ)
    e.shift(True); e.pad(0); e.shift(False)
    dup(True); e.knob(0, 1); dup(False)
    r2 = tuple(e.uc.mem_read(e.r0(e.vl["c_vrow2"], 0), 8))
    check(r2[0] == 0 and all(lane(0, p, 0) == bytes([0x10 + p]) * LC.LANE_SZ for p in range(8)),
          f"the non-sequenceable view: Duplicate + K1 frees its slot 1, lane 0 untouched ({r2})")
    print(f"{man.get('marker', '?')} LANECLR RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text())) else 0)
