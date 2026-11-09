"""Profile (no pass / fail): the whole DSP service chain from its head (0x080213AA: what runs every ~1 ms with the DSP semaphore held), the ARM
instructions per tick attributed to the module whose label precedes each address (the stock = "stock"), and the SPI writes / reads to the DSP by
the calling module; MIDI 1's own synth with the 8-operator FM (instrument 3), silent, a 4-note chord held, playing.

    python tools/prof_svc.py BUILD.bin manifest.json
"""
from __future__ import annotations
import bisect, json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402,F401
import poly as P  # noqa: E402
import modmx as MX  # noqa: E402
import mpatch as MP  # noqa: E402
import build_sc14 as S14  # noqa: E402
import fmeng as FE  # noqa: E402
import fm8arm as A  # noqa: E402
import fm8inst as FI  # noqa: E402
import emu_poly as EP  # noqa: E402

STOCK_END = 0x0805CDDC


def main(img, man):
    R = man["report"]
    P.adopt(R)
    starts = []
    for m, v in R.items():
        if isinstance(v, dict) and "labels" in v:
            for k, a in v["labels"].items():
                try: starts.append((int(a, 16), m))
                except (TypeError, ValueError): pass
    starts.sort(); addrs = [a for a, _ in starts]
    def mod(pc):
        if pc < STOCK_END: return "stock"
        i = bisect.bisect_right(addrs, pc) - 1
        return starts[i][1] if i >= 0 else "?"
    e = T.EL(img)
    def skip(uc): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    sl = {k: int(v, 16) for k, v in R["sc06"]["labels"].items()}
    for ad in (sl["c_non"], sl["c_noff"], EP.STOCK_TX_ON, EP.STOCK_TX_OFF, EP.REC_GATE):
        e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: skip(uc), begin=ad, end=ad)
    acc, wr, rd = {}, {}, {}
    def w(uc, a, s, d): k = mod(uc.reg_read(UC_ARM_REG_LR)); wr[k] = wr.get(k, 0) + 1; skip(uc)
    e.uc.hook_add(UC_HOOK_CODE, w, begin=P.DSP_WRITE, end=P.DSP_WRITE)
    def r_(uc, a, s, d): k = mod(uc.reg_read(UC_ARM_REG_LR)); rd[k] = rd.get(k, 0) + 1; uc.reg_write(UC_ARM_REG_R0, 0x300000 << 8); skip(uc)
    e.uc.hook_add(UC_HOOK_CODE, r_, begin=0x08029344, end=0x08029344)
    def ins(uc, a, s, d):
        k = "stock" if a < STOCK_END else mod(a); acc[k] = acc.get(k, 0) + 1
    head = MP.bw_target(bytearray(img), S14.SVC_HOOK, 0x08010000)
    def tick(k=1, count=False):
        h = e.uc.hook_add(UC_HOOK_CODE, ins) if count else None
        for _ in range(k): e.at(e.t + 1); e.call(head, maxins=8_000_000)
        if h is not None: e.uc.hook_del(h)
    non, noff = e.r32(MX.NOTE_VT) & ~1, e.r32(MX.NOTE_VT + 4) & ~1
    on = lambda nt: e.call(non, EP.TXOBJ, 2, nt, 100, maxins=8_000_000)
    off = lambda nt: e.call(noff, EP.TXOBJ, 2, nt, 0, maxins=8_000_000)
    e.at(100000); e.transport(0)
    e.btn(2); e.btn(8); e.pad(26); e.pad(FE.ROWPAD); e.pad(26)
    if "c_fiun" in json.dumps(R.get("fm8ui", {})): FI.use_v2()
    e.uc.mem_write(A.FM8R + A.TB0, FI.inst_full(3)); e.uc.mem_write(A.FM8R + A.TB0 + A.B_DIRTY, b"\x01")
    tick(300)
    def meas(label, fn, k):
        acc.clear(); wr.clear(); rd.clear(); fn(); tick(k, True)
        tot = sum(acc.values())
        top = sorted(acc.items(), key=lambda x: -x[1])[:12]
        print(f"{label}: {tot / k:7.0f} ins/tick; writes/tick {sum(wr.values()) / k:5.1f} {dict((m, round(v / k, 2)) for m, v in wr.items())}; "
              f"reads/tick {sum(rd.values()) / k:5.1f} {dict((m, round(v / k, 2)) for m, v in rd.items())}")
        print("    " + ", ".join(f"{m} {v / k:.0f}" for m, v in top))
    print(f"{man.get('marker', '?')}: the DSP service chain, per 1 ms tick")
    meas("FM on, silent, stopped", lambda: None, 100)
    meas("chord held, stopped", lambda: [on(x) for x in (60, 64, 67, 71)], 100)
    e.transport(1)
    meas("chord held, playing", lambda: None, 100)
    meas("released, playing", lambda: [off(x) for x in (60, 64, 67, 71)], 100)


if __name__ == "__main__":
    main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text()))
