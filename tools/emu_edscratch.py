"""SC48.3 / Beta 3.40 / RC2.11 / RC2.11S (vcf21.use_edscratch): the CC editor's undo copy out of the Master FX block's old LED buffer.

    python tools/emu_edscratch.py BUILD.bin manifest.json [PREVIOUS.bin PREVIOUS_manifest.json]

Through the controller (emu_sc23_4_ed's harness, the knobs by 0x08033848): MIDI 1's Preset view, template 1; pad 25 = the editor; K1 touched and
turned (an unsaved change: the copy taken); the LED task and the DSP service run (the modules that keep their state in the old LED buffer write
it); pad 25 again = leave, the change discarded:
  * the build: the copy at use_edscratch's address (= the 8 records); after the discard the 8 records as before, and K1..K8 send their CCs;
  * use_saveexit: the editor on again, K1 + 3, the Save pad: saved (one store write) and the editor left (its state byte 0, the Preset view), K1
    sends the new CC;
  * the previous build (the bug, expected): the copy in the Master FX block + 64 and, after the discard, records changed and knobs that send nothing.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0, UC_ARM_REG_R2, UC_ARM_REG_R3
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc23_4_ed as T  # noqa: E402  (the editor v2's options of vcf21)

V = T.V
KNOB = 0x08033848
STORE_WRITE = 0x0803C920
SCR = 0x20046B00


def run(img, man):
    e = T.E20(img, man)
    for _ in range(12): e.vtick()
    ccs = []
    writes = []
    def sw(uc, a, s, d): writes.append(1); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, sw, begin=STORE_WRITE, end=STORE_WRITE)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: ccs.append((uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R3))),
                  begin=V.CC_HELPER, end=V.CC_HELPER)
    base = e.r32(e.r32(T.SETOBJ - 4) + 0xC)
    recs = lambda: [bytes(e.uc.mem_read(base + 0x28 + 10 * k, 10)) for k in range(8)]
    knob = lambda k, d: e.call(KNOB, T.MGR, k, d, maxins=8_000_000)
    e.btn(0); e.btn(2)
    if e.cur() != 18: e.btn(8)
    e.padr(0); e.rel(0)
    r0 = recs()
    e.padr(V.PAD_CC); e.rel(V.PAD_CC)
    knob(0, 1); knob(0, 3)
    changed = recs()[0] != r0[0]
    at_new = bytes(e.uc.mem_read(SCR, 80)) == b"".join(r0)
    for _ in range(6): e.frame(); e.vtick()
    e.padr(V.PAD_CC); e.rel(V.PAD_CC)
    r1 = recs()
    sends = []
    for k in range(8):
        ccs.clear(); knob(k, 2); sends.append(ccs[0][0] if ccs else None)
    writes.clear()
    e.padr(V.PAD_CC); e.rel(V.PAD_CC); knob(0, 1); knob(0, 3)
    e.padr(V.PAD_SAVE); e.rel(V.PAD_SAVE)
    saved = (len(writes), e.tailb(V.O_ED), e.cur(), recs()[0][4])
    ccs.clear(); knob(0, 2); after = ccs[0][0] if ccs else None
    del e; gc.collect()
    return dict(changed=changed, at_new=at_new, same=[a == b for a, b in zip(r0, r1)], sends=sends,
                want=[r[4] if r[0] == 1 else None for r in r0], saved=saved, after=after)


def main(img, man, prev=None, pman=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    o = run(Path(img).read_bytes(), man)
    check(o["changed"] and o["at_new"], f"K1 turned in the editor: a change ({o['changed']}), the copy of the 8 records at {SCR:#x} ({o['at_new']})")
    check(all(o["same"]), f"pad 25 with the change pending (discarded): the 8 records as before {o['same']}")
    check(o["sends"] == o["want"], f"K1..K8 send their CCs {o['sends']} (the records: {o['want']})")
    n, ed, cur, num = o["saved"]
    check(n == 1 and ed == 0 and cur == 18 and o["after"] == num == o["want"][0] + 3,
          f"the Save pad: saved ({n} write), the editor left (state {ed:#x}, view {cur}), K1 sends the new CC ({o['after']} / {num})")
    if prev:
        p = run(Path(prev).read_bytes(), pman)
        check(not p["at_new"] and not all(p["same"]), f"the previous build (the bug): the copy elsewhere, records changed by the discard {p['same']}, "
                                                        f"sends {p['sends']}")
    print(f"{Path(img).stem} EDSCRATCH RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text()), a[2] if len(a) > 2 else None,
                       json.loads(Path(a[3]).read_text()) if len(a) > 3 else None) else 0)
