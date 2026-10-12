"""SC32D.1 tests: the raw probe (tools/probe32b_dsp.py, on the dsp56kEmu interpreter) and its MIDI dump (tools/probe32b.py, on the RAM dump).

    python tools/emu_sc32d_1.py SC32D.1.bin SC32D.1_manifest.json
DSP (the same code assembled with zones 0 / 1 / 14 and the "internal" word mapped into the interpreter's 512 K words; the image's probe = code() word for word):
  * nothing before NWAIT calls, then once: the 13 words (SR, OMR, M0, r0, found / read back by register, absolute, after the delay, absolute write, zone 0, the
    internal word, zone 14), the magic; every written word restored; x0 / x1 / r0 and the interrupt mask as found; later calls change nothing.
ARM (real routes: the DSP service chain head, the controller's pad path 0x08033282 into the synth Preset view):
  * closed source view: no read, pad 9 goes on to srcview (no MIDI);
  * open: one word per call into the buffer (index = uptime >> 3 & 15), pad 9 red before the magic, green with it;
  * pad 9: CC 20 = 127, then per word CC 21..25 (index, 3 + 7 + 7 + 7 bits), CC 20 = 0, all on channel 16, through the stock send; the words decode back; other pads go on.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc19_1 as T  # noqa: E402
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
import masterfx_dsp as G  # noqa: E402
import probe32b as PR  # noqa: E402
import probe32b_dsp as PD  # noqa: E402
import build_sc14 as s14  # noqa: E402
import drums18  # noqa: E402

VIEWS = PR.VIEWS
CODE_AT, RET_AT, DRV_AT, POST_AT = 0x3900, 0x3F00, 0x3E00, 0x3D00
TZ0, TZ1, TZ14, TINT = 0x40000, 0x41000, 0x42000, 0x43000


def T_(*l): return G.T(*l)


def decode(msgs):
    """[(status, cc, value)] -> list of 24-bit words (None if malformed)."""
    if not msgs or msgs[0] != (0xBF, 20, 127) or msgs[-1] != (0xBF, 20, 0): return None
    body, words = msgs[1:-1], []
    if len(body) % 5: return None
    for j in range(0, len(body), 5):
        g = body[j:j + 5]
        if [m[1] for m in g] != [21, 22, 23, 24, 25] or any(m[0] != 0xBF for m in g) or g[0][2] != j // 5: return None
        words.append(g[1][2] << 21 | g[2][2] << 14 | g[3][2] << 7 | g[4][2])
    return words


class E32b(T.E191):
    def __init__(self, image, man):
        super().__init__(image, man)
        self.pl = {k: int(v, 16) for k, v in man["report"]["probe32b"]["labels"].items()}
        self.read_map, self.reads, self.sent, self.sleeps = {}, [], [], []
        def h(uc, a, s, d):
            ad = uc.reg_read(UC_ARM_REG_R1)
            self.reads.append((uc.reg_read(UC_ARM_REG_R0), ad))
            uc.reg_write(UC_ARM_REG_R0, (self.read_map.get(ad, 0) << 8) & 0xFFFFFFFF)
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        self.uc.hook_add(UC_HOOK_CODE, h, begin=PR.DSP_READ, end=PR.DSP_READ)
        def snd(uc, a, s, d):
            self.sent.append((uc.reg_read(UC_ARM_REG_R0), tuple(uc.mem_read(uc.reg_read(UC_ARM_REG_R1), 3))))
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        self.uc.hook_add(UC_HOOK_CODE, snd, begin=PR.SEND, end=PR.SEND)
        def slp(uc, a, s, d):
            self.sleeps.append(uc.reg_read(UC_ARM_REG_R0)); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        self.uc.hook_add(UC_HOOK_CODE, slp, begin=PR.SLEEP, end=PR.SLEEP)
    def tick(self, uptime=0):
        self.uc.mem_write(PR.HAL_TICK, struct.pack("<I", uptime))
        self.reads.clear(); self.chain.clear(); self.dw.clear()
        self.call(self.pl["c_dtick32b"], maxins=3_000_000)
        return list(self.reads)
    def buf(self, v): return self.r32(self.r32(v + 4))
    def row(self, v, first, n): return list(struct.unpack(f"<{n}H", bytes(self.uc.mem_read(self.buf(v) + 2 * first, 2 * n))))
    def allpads(self, v): return self.row(v, 0, 32)
    def words(self): return list(struct.unpack(f"<{PR.NWORDS}I", bytes(self.uc.mem_read(self.st + PR.BUF, 4 * PR.NWORDS))))


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    rep = man["report"]
    dl = {k: int(v, 16) for k, v in rep["sc16"]["dsp_labels"].items()}
    sp = dsp_program(img)
    P0 = [int.from_bytes(sp[i:i + 3], 'big') for i in range(0, len(sp), 3)]
    check(len(P0) <= 0x3800 and P0[0x23C:0x23E] == [0x0BF080, dl["pprobe"]], f"P:$23C = jsr pprobe; program ends at P:${len(P0):x}")
    real, _ = PD.code(dl["pprobe"], PD.PREMIX)
    check(P0[dl["pprobe"]:dl["pprobe"] + len(real)] == real, "the image's probe = code() with the real addresses")
    check(PD.Z14 == 0x337000 and PD.Z1 == 0x128800, "zone 1 / 14 addresses")

    # ---------------------------------------------------------------- DSP logic, addresses in the interpreter's memory
    NWT = 3
    tw, _ = PD.code(CODE_AT, RET_AT, TZ0, TZ1, TZ14, TINT, NWT)
    P = P0 + [0] * (0x4000 - len(P0))
    P[CODE_AT:CODE_AT + len(tw)] = tw
    P[RET_AT] = 0x00000C
    def drv(n): return [0x0BF080, CODE_AT] * n + [0x00000C]
    found = {TZ0: 0x111111, TZ1: 0x222222, TZ14: 0x333333, TINT: 0x444444}
    mem = [('y', a, [v]) for a, v in found.items()]
    pre = T_("move #>$a5a5a5,x0", "move #>$5a5a5a,x1", "move #>$33,r0", "move #>$7777,m0")
    post = lambda n: [0x0BF080, DRV_AT] + T_("move sr,x:>$3a01", "move x0,x:>$3a02", "move x1,x:>$3a03", "move r0,x:>$3a04") + [0x00000C]
    dumps = [('y', PD.YM, 1 + PD.NW), ('x', PD.FLAG, 2), ('x', 0x3A01, 4)] + [('y', a, 1) for a in found]
    def go(n):
        P2 = list(P); P2[DRV_AT:DRV_AT + 2 * n + 1] = drv(n); pst = post(n); P2[POST_AT:POST_AT + len(pst)] = pst
        return run(P2, POST_AT, mem=mem, dumps=dumps, regs_code=pre + T_("move sr,x:>$3a00"), maxins=2_000_000)
    res, ran = go(NWT - 1)
    check(res[('y', PD.YM)] == [0] * (1 + PD.NW) and res[('x', PD.FLAG)] == [0, NWT - 1], f"{NWT - 1} calls: nothing yet, counter {res[('x', PD.FLAG)]}")
    res, ran = go(NWT + 3)
    y = res[('y', PD.YM)]
    check(y[0] == PD.MAGIC and res[('x', PD.FLAG)][0] == 1, f"after {NWT} calls: done, magic ({ran})")
    r = y[1:]
    want = {3: TZ1, 4: found[TZ1], 5: PD.PAT1, 6: PD.PAT1, 7: PD.PAT1, 8: PD.PAT2, 9: PD.PAT0, 10: found[TINT], 11: found[TZ14], 12: PD.PAT14}
    check(all(r[i] == v for i, v in want.items()), f"words {[hex(x) for x in r]}")
    check(r[2] == 0x7777 and r[0] & 0xFF0000 == 0xC00000, f"M0 {r[2]:#x}, SR {r[0]:#x}")
    check([res[('y', a)][0] for a in found] == list(found.values()), "every written word restored")
    rr = res[('x', 0x3A01)]
    check(rr[1:] == [0xA5A5A5, 0x5A5A5A, 0x33] and (rr[0] ^ r[0]) & 0xFFFF00 == 0, f"x0 / x1 / r0 and the interrupt mask restored {[hex(x) for x in rr]}")
    resz, _ = run(P[:DRV_AT] + drv(NWT + 1) + P[DRV_AT + 2 * NWT + 3:], DRV_AT, mem=[], dumps=[('x', 0x3B00, 0x100), ('y', 0x3B00, 0x100), ('x', 0x3A00, 0x100), ('y', 0x3A00, 0x100)])
    xs, ys = resz[('x', 0x3B00)], resz[('y', 0x3B00)]
    check(all(v == 0 for i, v in enumerate(xs) if not (PD.SAV - 0x3B00 <= i <= PD.CNT - 0x3B00)) and all(v == 0 for i, v in enumerate(ys) if not (PD.YM - 0x3B00 <= i <= PD.YM - 0x3B00 + PD.NW))
          and resz[('x', 0x3A00)] == [0] * 0x100 and resz[('y', 0x3A00)] == [0] * 0x100, "only the probe's own words of X / Y:$3A00..$3BFF written")

    # ---------------------------------------------------------------- ARM
    L = {k: int(v, 16) for k, v in rep["probe32b"]["labels"].items()}
    check(drums18.decode_bw(bytearray(img), s14.SVC_HOOK) == L["c_dtick32b"], "DSP service chain head -> c_dtick32b")
    check(struct.unpack_from("<I", img, PR.SP_VT - 0x08010000)[0] == L["c_dpad"] | 1, "slot 0 of the synth Preset view -> c_dpad")
    gc.collect(); e = E32b(img, man)
    snap = [e.allpads(v) for v in VIEWS]
    r = e.tick(uptime=0)
    check(r == [] and [e.allpads(v) for v in VIEWS] == snap and len(e.chain) == 1, "source view closed: no DSP read, LEDs untouched, the chain goes on")
    e.sent.clear(); e.padr(8)
    ours = lambda: [m for k, m in e.sent if k == 7 and m[0] == PR.STATUS]
    check(not e.flag() and ours() == [], "closed view: pad 9 sends no dump (the stock view's own MIDI only)")
    e.btn(0)
    check(e.flag(), "source view open")
    e.sent.clear()
    vals = [PD.MAGIC] + [(0x10203 * (i + 1)) & 0xFFFFFF for i in range(PD.NW)]
    e.read_map = {0x8000 | (PD.YM + i): v for i, v in enumerate(vals)}
    e.read_map[0x8000 | PD.YM] = 0x123456
    e.tick(uptime=0)
    check(e.row(VIEWS[0], 8, 16) == [PR.RED] + [0] * 15, f"no magic yet: pad 9 red, pads 10-24 dark {[hex(x) for x in e.row(VIEWS[0], 8, 4)]}")
    e.read_map[0x8000 | PD.YM] = PD.MAGIC
    for i in range(16):
        r = e.tick(uptime=i << 3)
        if i < PR.NWORDS and [x for _, x in r] != [0x8000 | (PD.YM + i)]: check(False, f"index {i}: read {r}"); break
        if i >= PR.NWORDS and r: check(False, f"index {i}: no read expected {r}"); break
    else: check(True, "one word per call, index = uptime >> 3 & 15, none for 14 / 15")
    check(e.words() == vals, "the buffer holds the 14 words")
    check(e.row(VIEWS[0], 8, 2) == [PR.GREEN, 0] and e.row(VIEWS[1], 8, 1) == [PR.GREEN], "magic: pad 9 green (both views)")
    e.sent.clear(); e.sleeps.clear()
    e.padr(8)
    msgs = [m for k, m in e.sent]
    check(all(k == 7 for k, _ in e.sent) and len(msgs) == 2 + 5 * PR.NWORDS, f"pad 9: {len(msgs)} messages through the stock send (type 7)")
    check(decode(msgs) == vals, f"the dump decodes back to the words ({[hex(x) for x in (decode(msgs) or [])][:3]}...)")
    check(e.sleeps == [2] * PR.NWORDS, "2 ms between words")
    e.sent.clear(); e.padr(9)
    check(ours() == [], "pad 10: no dump (goes on to srcview)")
    print("SC32D.1 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
