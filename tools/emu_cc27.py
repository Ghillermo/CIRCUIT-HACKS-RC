"""Alpha 7.14 / RC4.20 test (tools/cc27fix.py): CC 27 on channel 16 (the master group's 13th parameter) through the real MIDI input (0x08051720),
then the main loop's sender of the master group (0x08021578):
  * the pending bit 3 set by the CC, then cleared by the sender with nothing called (stock and older builds: a jump to 0xD0002800, a fault);
  * the same for NRPN 1:27 = 1 / 0 on channel 16 (what the Rhythm's -12 dB trim sends, seen on its USB port);
  * bits 0-2 still call their stock handlers (0x08028F41 / 0x08028F63 / 0x08028FD5).

    python tools/emu_cc27.py BUILD.bin
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc05 as X  # noqa: E402
import unicorn  # noqa: E402

PEND, SENDER = 0x20006A0D, 0x08021578
HANDLERS = (0x08028F40, 0x08028F62, 0x08028FD4)


def main(img):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = X.E(img)
    m = 0x20060100
    e.uc.mem_write(PEND - 1, bytes(4)); e.uc.mem_write(m, bytes([0xBF, 27, 127, 0])); e.call(0x08051720, X.CTX, m)
    check(e.r8(PEND) & 8, f"CC 27 on channel 16: the master group's pending bit 3 set ({e.r8(PEND):#x})")
    pcs = []
    h = e.uc.hook_add(unicorn.UC_HOOK_CODE, lambda uc, a, s, d: pcs.append(a))
    try:
        e.call(SENDER, maxins=200000); err = None
    except Exception as ex:
        err = ex
    e.uc.hook_del(h)
    check(err is None and not any((a & ~1) == 0xD0002800 for a in pcs), f"the sender: no jump to 0xD0002800 ({err})")
    check(not (e.r8(PEND) & 8), f"the bit cleared ({e.r8(PEND):#x})")
    for val in (0, 1):                               # (0 first: the CC 27 above left it at 1, an unchanged value marks nothing) what the Circuit Rhythm sends when its -12 dB trim is toggled: NRPN 1:27 on channel 16
        e.uc.mem_write(PEND - 1, bytes(4))
        for cc, v in ((99, 1), (98, 27), (6, val)):
            e.uc.mem_write(m, bytes([0xBF, cc, v, 0])); e.call(0x08051720, X.CTX, m)
        set_ = e.r8(PEND) & 8
        try: e.call(SENDER, maxins=200000); err = None
        except Exception as ex: err = ex
        check(set_ and err is None and not (e.r8(PEND) & 8), f"NRPN 1:27 = {val} (the Rhythm's trim): bit 3 set, then cleared without a fault ({err})")
    for b, hd in enumerate(HANDLERS):
        e.uc.mem_write(PEND, bytes([1 << b])); hit = []
        hh = e.uc.hook_add(unicorn.UC_HOOK_CODE, lambda uc, a, s, d: hit.append(a), begin=hd, end=hd)
        try: e.call(SENDER, maxins=2_000_000)
        except Exception: pass
        e.uc.hook_del(hh)
        check(bool(hit), f"bit {b}: its stock handler {hd:#x} called")
    print(f"{Path(sys.argv[1]).stem} CC27 RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes()) else 0)
