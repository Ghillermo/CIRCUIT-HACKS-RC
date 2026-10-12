"""SC30 ARM tests: the project save writes our settings again (persist19.SAVE_MASK) and the Master FX assignments survive a session change
(persist19.GFX_GLOBAL).

    python tools/emu_sc30.py SC29.bin SC30.bin SC29_manifest.json SC30_manifest.json
Real routes as emu_sc19.py: the stock apply (0x0802EEFE: power-up / project load), the stock new-project defaults (0x0802F5BC), the stock save through
the hooked bl (c_pl_save), and the whole DSP service chain from its head (c_vtick of the VCF mode, then c_dtick19), which is what sets bit 3 of the
flag byte on the hardware.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc19 import E19, OBJ, NEW_PROJECT  # noqa: E402
import persist19 as P  # noqa: E402
import build_sc17 as B  # noqa: E402

SLOTS_A = [(11, 22, 33, 0x80 | 44), (5, 6, 7, 0x80 | 1)]     # (slot index 2: Gater params; slot 4)
SLOTS_B = [(1, 2, 3, 0x80 | 3)]                               # another project: slot 0


def main(prev, img, man_prev, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1

    class E(E19):
        def __init__(self, image, mf):
            gc.collect(); super().__init__(image, mf); self.grid()
            self.vt = int(mf["report"]["vcf20"]["labels"]["c_vtick"], 16)
        def svc(self, n=16):                                   # the whole DSP service chain from its head
            for _ in range(n): self.call(self.vt, maxins=5_000_000)
        def save(self): self.call(self.lab["c_pl_save"], OBJ, maxins=8_000_000)
        def setslots(self, slots):
            self.uc.mem_write(self.blk + B.S_SLOT, bytes(28))
            for j, s in slots: self.uc.mem_write(self.blk + B.S_SLOT + 4 * j, bytes(s))
        def slots(self): return [self.rslot(i) for i in range(28)]
        def knobs(self): return list(self.blkb(B.S_KNOB, 20))
        def record(self, slots, sig=True, drum1=9):           # a saved project in the session record
            for i in range(P.N_XM): self.setrec(i, 0)
            for j, s in slots:
                for i, v in enumerate(s): self.setrec(P.XM_SLOTS + 4 * j + i, v)
            self.setrec(P.XM_DRUMS, drum1)
            self.setrec(P.XM_SIG, (P.SIG << 3) if sig else 0)
    def flat(slots):
        out = [0] * 28
        for j, s in slots: out[4 * j:4 * j + 4] = list(s)
        return out
    A = [(2, SLOTS_A[0]), (4, SLOTS_A[1])]; Bs = [(0, SLOTS_B[0])]

    # ---- 1. save after the service chain has run (bit 3 of the flag byte set by the VCF tick)
    for name, image, mf in (("SC29", prev, man_prev), ("SC30", img, man)):
        e = E(image, mf)
        for i in range(P.N_XM): e.setxm(i, 0)
        e.setslots(A); e.svc(1)
        fl = e.flags(); e.save()
        got = ([e.xm(P.XM_SLOTS + i) for i in range(28)], e.xm(P.XM_SIG) >> 3)
        if name == "SC29":
            check(fl & 8 and got == ([0] * 28, 0), f"SC29 (the bug): flag byte {fl:#x} after one service tick -> the save copies nothing, no signature")
        else:
            check(fl & 8 and got == (flat(A), P.SIG), f"SC30: flag byte {fl:#x} -> the save copies the slots and writes the signature")
    e = E(img, man)
    for i in range(P.N_XM): e.setxm(i, 0)
    e.setslots(A); e.svc(1); e.uc.mem_write(e.blk + P.FLAGS, bytes([e.flags() | P.F_RESYNC])); e.save()
    check(e.xm(P.XM_SLOTS + 8) == 0 and e.xm(P.XM_SIG) == 0, "SC30: a load still pending -> the save does not copy the stale RAM")

    # ---- 2. power-up: the assignments come from the project
    e = E(img, man)
    e.record(A); e.apply(1); e.svc()
    check(e.slots() == flat(A) and e.flags() & P.F_GBOOT, f"power-up: slots from the project, power-up mark set (flags {e.flags():#x})")
    check(e.xm(P.XM_DRUMS) == 9, "power-up: drum values from the project")
    # ---- 3. change session: the assignments and the top-row parameters stay; effects and song pointer off; drums per project
    knobs = [10 + i for i in range(20)]
    e.uc.mem_write(e.blk + B.S_KNOB, bytes(knobs))
    e.pad(0, shift=True); e.rel(0); e.setsp(ls=5, le=12)
    check(e.blkb(B.S_LATCH)[0] != 0, "an effect latched before the change")
    e.record(Bs, drum1=21); e.apply(1); e.svc()
    check(e.slots() == flat(A), f"load of another session: the slot assignments are kept {e.slots()[:20]}")
    check(e.knobs() == knobs, "load of another session: the top-row parameters are kept")
    check(e.blkb(B.S_LATCH)[0] == 0 and e.sp() == (0, 0, 0, 0), "load of another session: Master FX effects and song pointer off")
    check(e.xm(P.XM_DRUMS) == 21 and e.dval(0, 1) == 21, "load of another session: the drums are the project's")
    # ---- 4. a project without our signature (stock / SC20..SC29 save): the slots stay, the zone is cleared
    e.record(Bs, sig=False, drum1=30); e.apply(1); e.svc()
    check(e.slots() == flat(A) and e.xm(P.XM_DRUMS) == 0, "project without signature: slots kept, drum values cleared")
    # ---- 5. new project: the slots stay
    e.call(NEW_PROJECT, OBJ, maxins=30_000_000); e.apply(1); e.svc()
    check(e.slots() == flat(A) and e.knobs() == knobs and e.xm(P.XM_SIG) >> 3 == 0 and e.xm(P.XM_DRUMS) == 0,
          "new project: slots and parameters kept, the zone starts clean")
    # ---- 6. save it, power off, power on with that project: the slots come back
    e.save()
    saved = [e.xm(P.XM_SLOTS + i) for i in range(28)]
    check(saved == flat(A) and e.xm(P.XM_SIG) >> 3 == P.SIG, "save after the session change: the current slots and the signature go to the project")
    rec = [e.xm(i) for i in range(P.N_XM)]
    e2 = E(img, man)
    for i, v in enumerate(rec): e2.setrec(i, v)
    e2.apply(1); e2.svc()
    check(e2.slots() == flat(A), "next power-up with that project: the slots come back")
    # ---- 7. SC29 for reference: a session change replaces / clears the slots
    e = E(prev, man_prev)
    e.record(A); e.apply(1); e.svc(); e.record(Bs); e.apply(1); e.svc()
    check(e.slots() == flat(Bs), "SC29 for reference: a session change takes the project's slots")
    print("SC30 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(Path(a[0]).read_bytes(), Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), json.loads(Path(a[3]).read_text())) else 0)
