"""SC43.2 ARM tests (the user, 2026-10-16: «al grabar un patrón con arpegiador de 32 pasos, sólo se aplica el arpegiador a la página donde se pulsó
grabar»), with the real sequencer tick (0x0802C418), the real recorder (the harness's marks on its note-on / note-off taken out), Record and Play
through the controller and Synth 1's track view pads:
  * a 32-step pattern with the arpeggiator on; a chord of two pads held on step 3 and let go on step 5, the same chord on step 19 and 21: the
    second note (ours, sent to the recorder's note-on gate) gets the recorder's note-off when let go (0x0802E5CC(rec, note, 0)), its entry in the
    recorder's list marked released, and on step 19 the recorder takes it again (the build before: held for ever, ignored on step 19);
  * the first note (the stock's) gets no note-off of ours (the stock sends the recorder one of its own when it is pressed again).
In emulation the stock's own route from the view to the recorder does not record (the first note never reaches it): only our note is checked.

    python tools/emu_sc43_2.py SC43.2.bin SC43.2_manifest.json [SC43.1.bin SC43.1_manifest.json]
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_LR, UC_ARM_REG_PC
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc40_8 as T8  # noqa: E402
import emu_arp as EA_  # noqa: E402
import arp as A  # noqa: E402
from emu_sc08 import CONT  # noqa: E402
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
from emu_sc35 import MGR  # noqa: E402

ENG, SEQ_TICK, REC_OFF = 0x20038EC0, 0x0802C418, 0x0802E5CC
PAD_A, PAD_B = 20, 17                                       # Synth 1's track view: notes 67, 62 in the dump's scale


def run(img, man):
    e = T8.E8(img, man, {k: int(v, 16) for k, v in man["report"]["patchain"]["labels"].items()})
    e.marks.pop(0x0802E5BC, None); e.marks.pop(0x0802E61C, None)
    def skip(uc, a, s, d): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    for f in (A.NOTE_ON, 0x0801BE78, 0x08029A00): e.uc.hook_add(UC_HOOK_CODE, skip, begin=f, end=f)
    pifc = e.r32(EA_.PLAYER + 0x4C)
    def ifc(uc, a, s, d):
        if uc.reg_read(UC_ARM_REG_R0) == pifc: skip(uc, a, s, d)                              # the player's note interface: sound only
    for f in (EA_.IFC_ON, EA_.IFC_OFF): e.uc.hook_add(UC_HOOK_CODE, ifc, begin=f, end=f)
    cur = [0]; offs = []
    def roff(uc, a, s, d): offs.append((cur[0], uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2)))
    e.uc.hook_add(UC_HOOK_CODE, roff, begin=REC_OFF, end=REC_OFF)
    reco = e.r32(A.REC + 0xC)                                                                 # Synth 1's recorder; its held notes from + 0x54
    takes = []
    def mw(uc, acc, addr, size, val, d):
        if reco + 0x54 <= addr < reco + 0x54 + 12 * 8 and size == 4 and val & 0xFF and (addr - reco - 0x54) % 12 == 0:
            takes.append((cur[0], val & 0xFF, (val >> 24) & 0xFF))
    e.uc.hook_add(UC_HOOK_MEM_WRITE, mw, begin=reco, end=reco + 0x200)
    p = e.playing(0); e.setpat(0, p, 0, 31)
    e.call(int(man["report"]["arp"]["labels"]["c_arset"], 16), 0, p, 0x80 | A.M_UP)
    e.set_p0(e.r32(CONT + 0x188), 0)
    for b_ in (0, 9, 16, 17): e.call(0x08033320, MGR, b_, maxins=8_000_000); e.call(0x0803381A, MGR, b_, maxins=8_000_000)   # Synth 1, Note, Record, Play
    rec_on = [e.r8(e.ptr(A.TRANSPORT, k)) for k in range(3)]
    plan = {2: "press", 4: "release", 18: "press", 20: "release"}
    done, t, flags = set(), 500000, {}
    for i in range(24 * 6):
        t += 21; e.w32(A.HAL_TICK, t); e.call(SEQ_TICK, ENG, maxins=5_000_000)
        s = e.r8(e.ptr(e.r32(ENG + 0x30), 1)); cur[0] = s
        if s in plan and s not in done:
            done.add(s)
            if plan[s] == "press": e.call(PRESS, MGR, PAD_A, 100, maxins=8_000_000); e.call(PRESS, MGR, PAD_B, 100, maxins=8_000_000)
            else:
                e.call(RELEASE, MGR, PAD_B, maxins=8_000_000); e.call(RELEASE, MGR, PAD_A, maxins=8_000_000)
                flags[s] = e.r8(reco + 0x54 + 3)
    res = dict(rec=rec_on, done=sorted(done), offs=offs, takes=takes, flags=flags)
    del e; gc.collect()
    return res


def main(img, man, old=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    r = run(img, man)
    note = r["takes"][0][1] if r["takes"] else None
    check(r["rec"] == [1, 1, 0] and r["done"] == [2, 4, 18, 20], f"Record and Play by the controller ({r['rec']}), the chord on steps 3 / 19, let go on 5 / 21")
    check(note is not None and [(s, n) for s, n, _ in r["takes"] if _ == 0] == [(2, note), (18, note)],
          f"the recorder takes the second note on step 3 and again on step 19 ({r['takes']})")
    ours = [o for o in r["offs"] if o[1] == note]; first = [o for o in r["offs"] if o[1] != note and o[0] in (4, 20)]
    check(ours == [(4, note, 0), (20, note, 0)] and not first and r["flags"] == {4: 1, 20: 1},
          f"let go: the recorder's note-off of the second note ({ours}), none of ours for the first ({first}), its entry released ({r['flags']})")
    if old is not None:
        o = run(old, man_old)
        check([s for s, n, f in o["takes"] if f == 0] == [2] and not [x for x in o["offs"] if x[1] == note], f"the build before: held for ever, ignored on step 19 ({o['takes']}, {o['offs']})")
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    old = Path(a[3]).read_bytes() if len(a) > 4 else None
    man_old = json.loads(Path(a[4]).read_text()) if len(a) > 4 else None
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), old) else 0)
