"""SC57.2 / Beta 5.57 test (jumprnd; the user, 2026-11-13: «a randomized choice between both steps»): MIDI 1 points at Synth 1 (the step flip) and
its step 5 holds two notes, for steps 10 and 14.  Through the stock's tick and the players' own slots, as emu_jumpseq.py (whose harness this is):
  * over N loops of MIDI 1's 16 steps, Synth 1 lands on step 10 some loops and on step 14 others, both near half;
  * one note on step 5: always that step (as before);
  * the previous build (if given): always the same one of the two (the last note sent).

    python tools/emu_jumprnd.py BUILD.bin manifest.json [PREVIOUS.bin PREVIOUS_manifest.json] [--loops N]
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc48_8 as S  # noqa: E402
import emu_arp as EAm  # noqa: E402
import emu_jumpseq as EJ  # noqa: E402
import arp as A  # noqa: E402
import jumpseq as J  # noqa: E402
from unicorn.arm_const import UC_ARM_REG_R0  # noqa: E402

ENG, SEQ_TICK, PLAYERS = EJ.ENG, EJ.SEQ_TICK, EJ.PLAYERS
note_of = lambda s_: 59 + (s_ & 16) + 2 * (s_ & 7) + (s_ >> 3 & 1)                    # the pattern's note for a step, the root at C


def run(img_path, man, loops, chord=(9, 13)):
    img = Path(img_path).read_bytes()
    e = S.ET(img, man)
    e.marks.pop(0x0802E5BC, None); e.marks.pop(0x0802E61C, None)
    R = man["report"]
    t = [500000]
    def at(ms): t[0] += ms; e.w32(A.HAL_TICK, t[0])
    at(0)
    rec = e.r32(J.SESSION_OBJ + 0x14) + J.TAIL + J.O_JS
    kb_scale = e.r32(J.MU.KB_CTX + 0xC); kb_root = e.r32(J.MU.KB_CTX + 0x10)
    e.uc.mem_write(kb_root, bytes([0])); e.w32(kb_scale + 4, EJ.mask_of(EJ.MINOR))
    seen = []
    def clock():
        at(21); e.call(SEQ_TICK, ENG, maxins=5_000_000)
        st = e.r32(ENG + 0x30)
        if e.r32(e.ptr(st, 2)) == 0: seen.append((e.r8(e.ptr(e.r32(ENG + 0x38), 1)), e.r8(e.ptr(st, 1))))   # (MIDI 1's step, Synth 1's) on each step start
        for o in (0x14, 0x18):
            for p in PLAYERS: e.call(e.r32(e.r32(p)) & ~1, p, e.r32(p + o), maxins=3_000_000)
    pats = {}
    for m in (0, 1):
        e.call(int(R["vcf20"]["labels"]["c_sdpat"], 16), m, maxins=1_000_000); pats[m] = e.uc.reg_read(UC_ARM_REG_R0)
    empty = bytes(S.chord([], 32))
    for q in (0, 1): e.uc.mem_write(pats[q], empty)
    e.uc.mem_write(pats[0] + 28 * 4, bytes(S.chord([(note_of(s_), 3, 0, 100) for s_ in chord], 1)))
    e.uc.mem_write(rec, bytes([1, 0, J.SIG]))                                         # MIDI 1 -> Synth 1
    for k in range(8):
        st = e.r32(ENG + 0x50 + 4 * k)
        EAm.EA.setp(e, st, 0, bytes([15, 0])); EAm.EA.setp(e, st, 1, bytes([3])); EAm.EA.setp(e, st, 2, bytes([0]))
    e.transport(0)
    for k in range(8):
        st = e.r32(ENG + 0x30 + 4 * k)
        EAm.EA.setp(e, st, 1, bytes([0])); EAm.EA.setp(e, st, 2, struct.pack("<I", 5))
        EAm.EA.setp(e, e.r32(ENG + 0x70 + 4 * k), 1, bytes([0]))
    e.uc.mem_write(J.RAM + 4, bytes(8)); e.transport(1)
    for _ in range(6 * 16 * loops): clock()
    del e; gc.collect()
    land = [sy for m, sy in seen if m == 4]                                           # Synth 1 on the jump step (MIDI 1 index 4: it lands on that step)
    return {s_: land.count(s_) for s_ in chord}, len(land)


def main(a):
    img, man = a[0], json.loads(Path(a[1]).read_text())
    loops = int(a[a.index("--loops") + 1]) if "--loops" in a else 30
    prev = [x for x in a[2:] if not x.startswith("--") and not x.isdigit()]
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    got, n = run(img, man, loops)
    lo = loops * 0.2
    check(n >= loops - 1 and all(v >= lo for v in got.values()), f"two notes on step 5: Synth 1 lands on step 10 / 14 at random over {n} jumps ({ {k + 1: v for k, v in got.items()} })")
    one, n1 = run(img, man, 6, chord=(9,))
    check(one[9] == n1 and n1 >= 5, f"one note: always its step ({one}, {n1})")
    if len(prev) >= 2:
        p, pn = run(prev[0], json.loads(Path(prev[1]).read_text()), 10)
        check(sorted(p.values())[0] == 0 and pn >= 9, f"the previous build: always the same step ({ {k + 1: v for k, v in p.items()} })")
    print(f"{Path(img).stem} RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1:]) else 0)
