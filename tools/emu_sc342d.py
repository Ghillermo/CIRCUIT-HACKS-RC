"""SC342D tests: SC35D9's remote-diagnostic tests (emu_sc35d8 with DELETE) on the SC342D image, plus the DSP commands of rdiag.DSPX, through the real
incoming SysEx route 0x0801EB30.  The DSP host port (0x08029344 read / 0x080292F8 write), the DSP service semaphore (take 0x08021064 / give 0x08029028) and the
sleep 0x0801BE78 are simulated: a dict of X / Y words; at every sleep the "DSP" runs the sampler's block copy (CPLEN words from external Y:CPSRC to Y:CPDST).

    python tools/emu_sc342d.py SC342D.bin SC342D_manifest.json
  * command 3: X and Y internal words, 24 bits, n clamped to NR, the semaphore held around the reads;
  * command 8: CPLEN busy -> status 3, nothing written; free -> CPSRC = src, CPDST = WIN, CPLEN = n (written in that order, under the semaphore), waits for the
    copy, returns the n samples (bits 23..8) from Y:WIN; never runs the host port without the semaphore; a copy that never ends -> status 4 after 100 sleeps;
  * the image: SC34.2's code plus rdiag (the hook at 0x0801EB30).
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
import rdiag as RD  # noqa: E402
RD.DELETE = RD.DSPX = True
import emu_sc35d8 as T8  # noqa: E402
import ctremote as CR  # noqa: E402
import sampler_dsp as SD  # noqa: E402


class EX(T8.E8):
    def __init__(self, image, man):
        super().__init__(image, man)
        self.x, self.y, self.ext = {}, {}, {}
        self.held, self.bad, self.log, self.stuck, self.sleeps = 0, 0, [], False, 0
        def ret(uc, v):
            uc.reg_write(UC_ARM_REG_R0, v & 0xFFFFFFFF); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        def take(uc, a, s, d): self.held += 1; ret(uc, 0)
        def give(uc, a, s, d): self.held -= 1; ret(uc, 0)
        def rd(uc, a, s, d):
            core, ad = uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1)
            if self.held != 1: self.bad += 1
            v = (self.y if ad & 0x8000 else self.x).get(ad & 0x7FFF, 0)
            self.log.append(("r", "y" if ad & 0x8000 else "x", ad & 0x7FFF)); ret(uc, (v & 0xFFFFFF) << 8)
        def wr(uc, a, s, d):
            core, v, ad = uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2)
            if self.held != 1: self.bad += 1
            self.x[ad] = (v >> 8) & 0xFFFFFF; self.log.append(("w", ad, (v >> 8) & 0xFFFFFF)); ret(uc, 0)
        def slp(uc, a, s, d):
            self.sleeps += 1
            n = self.x.get(SD.CPLEN, 0)
            if n and not self.stuck:
                src, dst = self.x.get(SD.CPSRC, 0), self.x.get(SD.CPDST, 0)
                for i in range(n): self.y[dst + i] = self.ext.get(src + i, 0)
                self.x[SD.CPLEN] = 0
            ret(uc, 0)
        for f, ad in ((take, RD.SEM_TAKE), (give, RD.SEM_GIVE), (rd, RD.DSP_READ), (wr, RD.DSP_WRITE), (slp, RD.SLEEP)):
            self.uc.hook_add(UC_HOOK_CODE, f, begin=ad, end=ad)


def main(img, man):
    fails = T8.main(img, man)
    gc.collect()
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    check(man["report"]["sc17"].get("sp3") is True and "drumrep" in man["report"], "the image is SC34.2 (sp3, drumrep) + rdiag")
    e = EX(img, man)
    def ask(make, cmd, seq=9):
        e.log.clear(); e.sysex(list(make(seq))); return CR.parse(e.out[0][2], cmd, seq) if len(e.out) == 1 else None
    # command 3
    e.x.update({SD.LEN: 0x012345, SD.LEN + 1: 0xABCDEF}); e.y.update({0x3BFE: 0x00FF00})
    p = ask(lambda s: CR.req_dspr(s, 0, SD.LEN, 2), 3)
    d = CR.dec_dspr(p)
    check(d == dict(status=0, words=[0x012345, 0xABCDEF]) and e.bad == 0 and e.held == 0, f"dspr X:LEN, 2 words {d}; the semaphore held around the reads")
    p = ask(lambda s: CR.req_dspr(s, 1, 0x3BFE, 1), 3)
    check(CR.dec_dspr(p) == dict(status=0, words=[0x00FF00]) and e.log == [("r", "y", 0x3BFE)], f"dspr Y:$3BFE {CR.dec_dspr(p)}")
    p = ask(lambda s: CR.req_dspr(s, 0, 0x100, 99), 3)
    check(len(CR.dec_dspr(p)["words"]) == RD.NR, f"dspr: n clamped to {RD.NR}")
    # command 8
    e.ext = {0xE80000 + i: ((i * 37) & 0xFFFF) << 8 for i in range(200)}
    e.x[SD.CPLEN] = 5
    p = ask(lambda s: CR.req_dspx(s, 0xE80000, 48), 8)
    check(CR.dec_dspx(p) == dict(status=3, samples=[]) and not any(l[0] == "w" for l in e.log) and e.held == 0, "dspx while a copy runs: status 3, nothing written")
    e.x[SD.CPLEN] = 0
    p = ask(lambda s: CR.req_dspx(s, 0xE80010, 48), 8)
    d = CR.dec_dspx(p)
    writes = [l for l in e.log if l[0] == "w"]
    check(writes == [("w", SD.CPSRC, 0xE80010), ("w", SD.CPDST, RD.WIN), ("w", SD.CPLEN, 48)], f"dspx: CPSRC, CPDST = WIN, CPLEN written in that order {writes}")
    check(d["status"] == 0 and d["samples"] == [(((16 + i) * 37) & 0xFFFF) for i in range(48)] and e.bad == 0 and e.held == 0,
          f"dspx: 48 samples from $E80010 (bits 23..8), the host port only under the semaphore ({e.bad} bad)")
    p = ask(lambda s: CR.req_dspx(s, 0xE80000, 200), 8)
    check(len(CR.dec_dspx(p)["samples"]) == RD.NX, f"dspx: n clamped to {RD.NX}")
    e.stuck = True; e.sleeps = 0
    p = ask(lambda s: CR.req_dspx(s, 0xE80000, 8), 8)
    check(CR.dec_dspx(p) == dict(status=4, samples=[]) and e.sleeps == 100 and e.held == 0, f"a copy that never ends: status 4 after {e.sleeps} sleeps")
    if RD.DEL_PACK:                                                             # SC35DA: delete a whole pack (not the current one), then re-select the current
        cur_obj = e.r32(RD.CUR_PACK_PTR); e.uc.mem_write(cur_obj, bytes([31]))
        for pk in (31, 0x7F):
            e.api.clear(); p = ask(lambda s: CR.req_del(s, 1, 0, pk), 7)
            check(CR.dec_delpack(p)["status"] == 0xFFFFFFFE and e.api == [], f"delpack {pk:#x} (the current pack / 0x7F): refused, no API call")
        e.api.clear(); p = ask(lambda s: CR.req_del(s, 1, 0, 30), 7)
        d = CR.dec_delpack(p)
        check(e.api == [("del", (1, 0, 30), 0, 0), ("exists", (4, 0, 31))] and d == dict(status=0, reselect_exists=1, current=31),
              f"delpack 30: op 5 kind 1 on pack 30, then exists on PCM 0 of the current pack 31 ({e.api}, {d})")
        e.api.clear(); p = ask(lambda s: CR.req_del(s, 4, 5, 0x7F), 7)
        check(e.api == [("del", (4, 5, 0xFF), 0, 0)], "items are deleted as before")
    print("SC342D" + ("/DA" if RD.DEL_PACK else "") + " RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    if "--delpack" in a:
        RD.DEL_PACK = True
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
