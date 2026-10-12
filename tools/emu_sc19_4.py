"""SC19.4 tests: the saved settings come back after a project load (persist19.REC_RESTORE), on the live RAM dump (unicorn), real stock apply / new-project code.

    python tools/emu_sc19_4.py SC19.3.bin SC19.4.bin SC19.4_manifest.json SC19.3_manifest.json

Why SC19.3 lost everything that was saved (also when switching between projects): the stock apply (0x0802EEFE) restores the project and drum blobs whole, but a
synth blob only when the patch of the record differs from the loaded one (flag bytes at [sp] / [sp + 1] from 0x0802F172 / 0x0802F19E, used at 0x0802F438 /
0x0802F4A2; with the same patch only 6 parameters).  44 of our 65 bytes live in the synth blobs, among them the signature, so the zone was judged empty and cleared.
  * same patch id, gate store != 0 (the stock "same patch" route): SC19.3 restores 0 of 22 bytes of each synth and loses the whole state; SC19.4 restores everything
    (signature, Master FX slots, modes, drum values) from the session record;
  * a different patch id (the whole-blob route): both restore everything;
  * a new project: still cleared in both (the record is not read);
  * a record without our signature (a stock project, an older build): cleared in both.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc19_1 as T1  # noqa: E402
import persist19 as P  # noqa: E402

OBJ = 0x2003D71C


def state():
    """a saved zone: signature (+ filter mode 3 of drum 0), Synth 1 = In 2 / Synth 2 = inverted In 1, slot 1 = effect 2 assigned, some drum values"""
    z = [0] * P.N_XM
    z[P.XM_SIG] = (P.SIG << 3) | 3
    z[P.XM_MODES] = 2 | (3 << 3)
    z[4:8] = [0x11, 0x12 | 0x80, 0x13, 0x14 | 0x80]                # slot 1: effect bits (0, 1, 0) = 2, assigned
    z[P.XM_DRUMS + 0] = 0x30                                      # drum 0, code 1
    z[P.XM_DRUMS + 9 + 2] = 0x41                                  # drum 1, code 3
    z[P.XM_DRUMS + 18 + 6] = 0x55                                 # drum 2, code 7
    z[P.XM_DRUMS + 27 + 3] = 0x62                                 # drum 3, code 4
    return z


def scenario(img, man, same_id=True, new=False, sig=True, patch_in_record=None):
    e = T1.E191(img, man)
    r6 = OBJ + 0x88
    s0 = e.r32(r6 + 0x14); e.set_p0(s0, 1)                        # the "not forced" gate of the stock same-patch test
    arr = e.r32(r6 + 0x28)
    for i in range(2):
        st = e.r32(arr + 4 * i)
        e.call(0x0803542C, st, 0xA); lid = e.r8(e.uc.reg_read(UC_ARM_REG_R0))
        e.call(0x0802AF66, e.r32(OBJ + 0x14), i); ptr = e.uc.reg_read(UC_ARM_REG_R0)
        e.uc.mem_write(ptr, bytes([lid if same_id else (lid + 5) & 0x7F]))
    z = state()
    if not sig: z[P.XM_SIG] = 0
    for i in range(P.N_XM): e.setrec(i, z[i]); e.setxm(i, 0)      # the record has the project's bytes, the live stores hold zeros
    if new:
        e.call(0x0802F5BC, OBJ, maxins=30_000_000)
    e.apply(0)
    ticks = [e.tick19() for _ in range(3)]
    for _ in range(14):
        m = e.tick19()
        if not m and not e.flags(): break
    return e, z


def main(ref, img, man, refman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    check(man["report"]["persist19"].get("rec_restore") is True and not refman["report"]["persist19"].get("rec_restore"), "manifests: SC19.4 restores from the record, SC19.3 not")
    # ---- the failing case: the same patch is loaded again
    e0, z = scenario(ref, refman, same_id=True)
    live0 = [e0.xm(i) for i in range(P.N_XM)]
    check(e0.modes() == [0, 0] and not any(live0[P.XM_DRUMS:P.XM_DRUMS + 36]), f"SC19.3, same patch: the saved state is lost (modes {e0.modes()}, drum bytes all zero)")
    e1, z = scenario(img, man, same_id=True)
    live1 = [e1.xm(i) for i in range(P.N_XM)]
    check(live1 == z, f"SC19.4, same patch: all 65 bytes restored from the record ({sum(1 for a, b in zip(live1, z) if a == b)} / {P.N_XM})")
    check(e1.modes() == [2, 3], f"   modes {e1.modes()} (Synth 1 = In 2, Synth 2 = inverted In 1)")
    check(e1.rslot(5) == 0x12 | 0x80 and e1.rslot(7) == 0x14 | 0x80 and e1.rslot(4) == 0x11, f"   Master FX slot 1 back in RAM {[hex(e1.rslot(i)) for i in range(4, 8)]}")
    sg = lambda b: (b & 0x7F) - 128 if (b & 0x7F) >= 64 else (b & 0x7F)                            # the bipolar codes 1, 3, 4, 5, 7
    check(e1.dval(0, 1) == sg(0x30) and e1.dval(1, 3) == sg(0x41) and e1.dval(2, 7) == sg(0x55) and e1.dval(3, 4) == sg(0x62), "   drum values kept (the DSP gets them as absolute messages)")
    check(e1.flags() == 0, f"   deferred work finished (flags {e1.flags()})")
    # ---- the whole-blob route and the cases that must stay cleared
    for name, kw in (("a different patch", dict(same_id=False)),):
        for im, mn, tag in ((ref, refman, "SC19.3"), (img, man, "SC19.4")):
            e, z = scenario(im, mn, **kw)
            check([e.xm(i) for i in range(P.N_XM)] == z and e.modes() == [2, 3], f"{tag}, {name}: everything restored")
    for im, mn, tag in ((ref, refman, "SC19.3"), (img, man, "SC19.4")):
        e, z = scenario(im, mn, same_id=False, new=True)
        check(not any(e.xm(i) for i in range(P.N_XM)) and e.modes() == [0, 0], f"{tag}, new project: cleared (the record is not read)")
        e, z = scenario(im, mn, same_id=False, sig=False)
        check(not any(e.xm(i) for i in range(P.N_XM)) and e.modes() == [0, 0], f"{tag}, record without our signature: cleared")
    # ---- a synth patch change copies a whole blob into the store (stock 0x0802FC82: reload patch idx from the record, vtable slot 3): our bytes must survive
    for im, mn, tag, keep in ((ref, refman, "SC19.3", False), (img, man, "SC19.4", True)):
        for idx, first in ((0, P.S1_FIRST), (1, P.S2_FIRST)):
            e = T1.E191(im, mn)
            for i in range(first, first + P.N_SYNTH_B):
                e.setrec(i, 0); e.setxm(i, 0x40 + (i & 0x1F))                  # the library patch has zeros there; the live stores hold our state
            e.call(0x0802FC82, OBJ, idx, 0, maxins=30_000_000)
            live = [e.xm(i) for i in range(first, first + P.N_SYNTH_B)]
            want = [0x40 + (i & 0x1F) for i in range(first, first + P.N_SYNTH_B)]
            check((live == want) if keep else (live == [0] * P.N_SYNTH_B),
                  f"{tag}, patch reload of Synth {idx + 1}: our {P.N_SYNTH_B} bytes {'kept' if keep else 'wiped by the whole-blob copy (the bug)'}")
    print("SC19.4 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    ref = Path(sys.argv[1]).read_bytes(); img = Path(sys.argv[2]).read_bytes()
    man = json.loads(Path(sys.argv[3]).read_text()); refman = json.loads(Path(sys.argv[4]).read_text())
    sys.exit(1 if main(ref, img, man, refman) else 0)
