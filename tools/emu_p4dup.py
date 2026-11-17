"""SC57.3 test (p4dest.use_dup; the user, 2026-11-13: «knobs on dedicated views get now assigned by pressing duplicate+knob (duplicate+knob on the
dedicated view frees it up)», «Page 4 first», «go to the next 8 slots (shift+pad1) when all 16 are taken, accept no more»), through the controller:
  * the rows start full (page 4 = LANE_TAB, the non-sequenceable page = NS_DEF): Duplicate + K3 on the OSC 1 page (code 19) = nothing;
  * on the assigned-knob view (pad 1), Duplicate + K2 frees slot 2 (code 0); turning it on in the same hold again changes nothing; the knob LEDs
    with Duplicate held: slot 2 dark, the others in their destination's colour;
  * back on OSC 1, Duplicate + K3 = code 19 into slot 2; Duplicate + K3 again (a new hold): already there, nothing;
  * the non-sequenceable view (Shift + pad 1): Duplicate + K1 frees its slot 1; page 4 full again after one more assignment; the next one goes there;
  * all 16 taken: nothing;
  * without Duplicate a knob on the assigned view moves its value as before (the handler chain), and Shift + knob no longer changes the destination;

    python tools/emu_p4dup.py BUILD.bin manifest.json
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402  (its import sets vcf21's options)
import packio as PK  # noqa: E402
import p4dest as P4  # noqa: E402
import vcf21 as V  # noqa: E402

MGR, DUPB = 0x20040B10, 24


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = X.EP(img, man); R = man["report"]
    vk = int(R["vcf20"]["labels"]["c_vkc"], 16)
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05]))
    row = lambda: tuple(e.uc.mem_read(e.r0(e.vl["c_vrow"], 0), 8))
    row2 = lambda: tuple(e.uc.mem_read(e.r0(e.vl["c_vrow2"], 0), 8))
    dup = lambda v: e.call(0x08033320 if v else 0x0803381A, MGR, DUPB, maxins=8_000_000)
    def dk(k, d=1, n=1):
        dup(True)
        for _ in range(n): e.knob(k, d)
        dup(False); e.knob(7, 0) if False else None
    e.btn(2); e.btn(8)
    r40, r20 = row(), row2()
    check(r40 == tuple(V.LANE_TAB) and r20 == tuple(V.NS_DEF), f"the rows start full ({r40}, {r20})")
    e.pad(1); pg = e.r0(e.vl["c_vpage"], 0); code3 = e.r0(vk, 0, 16 * pg + 2)
    dk(2)
    check(row() == r40 and row2() == r20 and code3 == 19, f"OSC 1 (page {pg}), Duplicate + K3 (code {code3}) with all 16 taken: nothing")
    e.pad(0)
    dup(True); e.knob(1, 1); f_dup = X.frame(e); e.knob(1, 1); r_a = row(); dup(False)
    check(r_a[1] == 0 and r_a[:1] + r_a[2:] == r40[:1] + r40[2:], f"pad 1, Duplicate + K2: slot 2 freed ({r_a})")
    check(f_dup[61] & 0xFF == 0 and f_dup[60] & 0xFF != 0, f"Duplicate held: K2's LED dark, K1's lit ({f_dup[60]:#x}, {f_dup[61]:#x})")
    e.pad(1); dk(2)
    check(row()[1] == 19, f"OSC 1, Duplicate + K3: code 19 into slot 2 ({row()})")
    dk(2); check(row().count(19) == 1, f"again: already there, nothing ({row()})")
    e.pad(0); e.shift(True); e.pad(0); e.shift(False); pg2 = e.r0(e.vl["c_vpage"], 0)
    dk(0); r2b = row2()
    check(r2b[0] == 0, f"the non-sequenceable view (page {pg2}): Duplicate + K1 frees its slot 1 ({r2b})")
    dc = set(tuple(e.uc.mem_read(int(R["modmx"]["labels"]["t_dcode"], 16), int(R["p4dest"]["prev"]["nd"], 16))))
    free = [(p_, sh, k) for p_ in (1, 2) for sh in (0, 1) for k in range(8)
            if (c := e.r0(vk, 0, 16 * p_ + 8 * sh + k)) and c in dc and c not in row() + row2()]
    def dks(p_, sh, k):
        e.pad(p_); e.shift(bool(sh)); dup(True); e.knob(k, 1); dup(False); e.shift(False)
        return e.r0(vk, 0, 16 * p_ + 8 * sh + k)
    c1 = dks(*free[0])
    check(row() == r40[:1] + (19,) + r40[2:] and row2()[0] == c1, f"page 4 full: {free[0]} (code {c1}) to the non-sequenceable view's slot 1 ({row()}, {row2()})")
    r_full = (row(), row2()); c3 = dks(*free[1])
    check((row(), row2()) == r_full, f"all 16 taken: {free[1]} (code {c3}) goes nowhere")
    # without Duplicate: the value, not the destination
    e.pad(0); r_b = row()
    e.shift(True); e.knob(0, 5); e.shift(False)
    check(row() == r_b, f"Shift + K1 on the assigned view: no destination change ({row()})")
    print(f"{Path(R.get('D', {}).get('marker', 'build')).name} P4DUP RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text())) else 0)
