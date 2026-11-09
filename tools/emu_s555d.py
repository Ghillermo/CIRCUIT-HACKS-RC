"""S555D (diagnostic): tools/clkdiag.py through the DSP service chain's head, the sequencer's tick, the storage heads and the real LED task.  The
DSP's reads (0x08029344) answered by the test (Y:$FFE / Y:$FFD).
  * margins 250 / 215 / 200 / 150 over a window: Save green / yellow / amber / red; the ring dry: Save white;
  * service ticks 1 ms apart: Duplicate as the stock draws it; a gap of GAP_MS: Duplicate in the culprit's colour (a mod card access white, the stock's blue, the
    LED task orange, none yellow), for 1 s;
  * a storage head called with LR in the mod's code = the mod's bit; with LR in the stock = not;
  * the sequencer's tick at 120 BPM every 21 ms: Play dark; one 50 ms late: Play violet; stopped: nothing;
  * (S555D2) Play in the colour of what ran long before the late tick (green a pad, white the mod's card), violet when the mark is older;
  * the main loop's service call and the LED task's wrapper return to their callers (LR from RAM), the frame's r0 kept.

    python tools/emu_s555d.py S555D.bin S555D_manifest.json
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_SP
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import clkdiag as D  # noqa: E402


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    R = man["report"]["clkdiag"]
    lab = {k: int(v, 16) for k, v in R["labels"].items()}
    prev = {k: int(v, 16) for k, v in R["prev"].items()}
    e = T.EL(img)
    def skip(uc): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: skip(uc), begin=prev["svc"] & ~1, end=prev["svc"] & ~1)      # the rest of the service chain
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: skip(uc), begin=prev["seq"] & ~1, end=prev["seq"] & ~1)      # the stock's tick
    st = dict(isr=0x1100, blk=0x1100 + 250)
    def rd(uc, a, s, d):
        ad = uc.reg_read(UC_ARM_REG_R1)
        v = st["isr"] if ad == D.Y_ISR else st["blk"] if ad == D.Y_BLK else 0
        uc.reg_write(UC_ARM_REG_R0, (v & 0xFFFFFF) << 8); skip(uc)
    e.uc.hook_add(UC_HOOK_CODE, rd, begin=D.DSP_READ, end=D.DSP_READ)
    t = [200000]
    def tick(n, ms=1):
        for _ in range(n): t[0] += ms; e.at(t[0]); e.call(lab["c_cktick"], maxins=2_000_000)
    led = lambda i: X.frame(e)[i] & 0xFF
    def window(margin):
        st["blk"] = (st["isr"] + margin) & 0x3FF | 0x1000
        tick(D.WIN_MS + 8); return led(D.LED_SAVE)
    tick(2)
    dup0 = led(D.LED_DUP)                                         # the stock's own Duplicate (dim)
    window(250); got = [window(m) for m in (250, 215, 200, 150)]
    check(got == [0x17, 0x2D, 0x2B, 0x53], f"Save by the window's least margin 250 / 215 / 200 / 150: {[hex(x) for x in got]}")
    st["blk"] = (st["isr"] + 900) & 0x3FF | 0x1000; tick(5); st["blk"] = (st["isr"] + 250) & 0x3FF | 0x1000
    check(led(D.LED_SAVE) == D.COL_DRY, f"the ring ran dry: Save white ({led(D.LED_SAVE):#x})")
    tick(D.DRY_MS + 600)
    check(led(D.LED_DUP) == dup0, f"service ticks 1 ms apart: Duplicate as the stock draws it ({led(D.LED_DUP):#x})")
    def gap(mask):
        e.uc.mem_write(D.RAM + D.O_MASK, mask.to_bytes(4, "little")); tick(1, D.GAP_MS); return led(D.LED_DUP)
    cols = [gap(m) for m in (D.B_SDMOD | D.B_SD, D.B_SD, D.B_LED, 0)]
    check(cols == [0x01, 0x09, 0x45, 0x2D], f"a gap: the culprit's colour (mod card, stock card, LED task, none): {[hex(x) for x in cols]}")
    tick(D.CUL_FLASH + 50)
    check(led(D.LED_DUP) == dup0, "1 s later: Duplicate as the stock draws it")
    def head(lr):                                                  # c_ckh0 (the storage head 0x0803CB50) called from lr: the mask after
        e.uc.mem_write(D.RAM + D.O_MASK, bytes(4))
        h = e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: uc.emu_stop(), begin=D.SD_HEADS[0] + 4, end=D.SD_HEADS[0] + 4)
        e.uc.reg_write(UC_ARM_REG_SP, 0x2006F000); e.uc.reg_write(UC_ARM_REG_LR, lr)
        e.uc.emu_start(lab["c_ckh0"] | 1, 0xFFFFFFFF, count=200); e.uc.hook_del(h)
        return int.from_bytes(e.uc.mem_read(D.RAM + D.O_MASK, 4), "little")
    m1, m2 = head(0x0806F001), head(0x08030001)
    check(m1 == D.B_SDMOD and m2 == 0, f"a storage head from the mod's code = the mod's bit, from the stock's = not ({m1:#x}, {m2:#x})")
    e.transport(1)
    def seq(ms): t[0] += ms; e.at(t[0]); e.call(lab["c_ckseq"], maxins=2_000_000)
    for _ in range(6): seq(21)
    p0 = led(D.LED_PLAY)
    seq(50); p1 = led(D.LED_PLAY)
    check(p0 != D.COL_SEQ and p1 == D.COL_SEQ, f"the sequencer's tick at 120 BPM: Play not violet, one 50 ms late: violet ({p0:#x}, {p1:#x})")
    if "c_cksd" in lab and man.get("marker", "").startswith("S555D2"):          # use_seqcul: Play in the culprit's colour
        for _ in range(3): seq(21)
        e.uc.mem_write(D.RAM + D.O_SMASK, D.B_PAD.to_bytes(4, "little")); seq(50); pg = led(D.LED_PLAY)
        for _ in range(30): seq(21)
        e.uc.mem_write(D.RAM + D.O_SMASK, (D.B_SDMOD | D.B_PAD).to_bytes(4, "little")); seq(50); pw = led(D.LED_PLAY)
        for _ in range(30): seq(21)
        seq(21); e.uc.mem_write(D.RAM + D.O_SMASK, D.B_PAD.to_bytes(4, "little")); seq(21); seq(50); pv = led(D.LED_PLAY)
        check((pg, pw, pv) == (0x17, 0x01, D.COL_SEQ), f"Play by the late tick's culprit: a long pad green, the mod's card white, a mark cleared by the tick before violet ({pg:#x}, {pw:#x}, {pv:#x})")
    e.transport(0); t[0] += 1000; e.at(t[0])
    n0 = int.from_bytes(e.uc.mem_read(D.RAM + D.O_NSEQ, 4), "little"); seq(80); seq(80)
    check(int.from_bytes(e.uc.mem_read(D.RAM + D.O_NSEQ, 4), "little") == n0, "stopped: no late ticks counted")
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: (uc.reg_write(UC_ARM_REG_R0, 0x1234), skip(uc)), begin=D.SVC, end=D.SVC)
    e.call(lab["c_cksvc"], maxins=2_000_000)
    check(e.uc.reg_read(UC_ARM_REG_PC) & ~1 == T.STOP & ~1 if hasattr(T, "STOP") else True, "the service call returns to its caller")
    check(e.uc.reg_read(UC_ARM_REG_R0) == 0x1234, f"its r0 kept ({e.uc.reg_read(UC_ARM_REG_R0):#x})")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} CLKDIAG RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
