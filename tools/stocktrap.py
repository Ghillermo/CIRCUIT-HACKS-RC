"""S720D (diagnostic, 2026-11-20; the user: «Prove + reuse stock dead code»): every stretch of the stock image that tools/fullwalk.py finds
unreached (Alpha 7.20: 32 runs dead in the stock itself, 3 more dead since our patches; the one whose bytes our patches changed is left out)
is filled with UDF #0xD7 (0xDED7): an undefined instruction.  Anything that runs there raises a UsageFault (or a HardFault): the black box's
fault capture freezes with the PC inside the run, and the stock's handler waits for the watchdog: Save violet after the restart.  A data read of
a run would see 0xDED7 instead of the stock's bytes (the walk lists only code-like runs, and every literal a reached instruction loads is
covered, so none is expected).  Each run's bytes are checked against the official image before they are replaced.  Hours of use / the
stress runs with no capture = the runs are dead; then a build can reuse them for our code."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

UDF = bytes([0xD7, 0xDE])                              # udf #0xd7
RUNS = [(0x8022E26, 248), (0x8055C06, 182), (0x8025070, 132), (0x801DEA4, 108), (0x8059378, 92), (0x801E56C, 88), (0x801A7EA, 58),
        (0x8059704, 56), (0x80584BC, 52), (0x80557C0, 52), (0x80596BC, 48), (0x801E480, 48), (0x804633C, 42), (0x80593DC, 40),
        (0x8040386, 34), (0x802EB96, 34), (0x801DC64, 34), (0x802E688, 26), (0x80244B8, 26), (0x801D102, 26), (0x805B978, 24),
        (0x80598D0, 24), (0x80373A4, 24), (0x8022890, 24), (0x805B958, 22), (0x80557A8, 22), (0x8059C5C, 20), (0x8018548, 20),
        (0x8022698, 10), (0x802244A, 10), (0x8059C50, 8), (0x801E788, 8),
        (0x804A35A, 56), (0x80470A8, 32), (0x804D398, 26)]                      # the last three: dead since our patches (bytes unchanged)


# (2026-11-20) dropped after the first emulation runs: the runs at 0x08058000 and up sit in the stock's data area (vtables, tables): two of them
# are read as data in emulation (0x08059378: a function pointer loaded at 0x080353F0; 0x080598D0: five code pointers) and the others hold
# pointer-like words or sit among the tables
DATA_AREA = 0x08058000
DROPPED = [(a, n) for a, n in RUNS if a >= DATA_AREA]
RUNS = [(a, n) for a, n in RUNS if a < DATA_AREA]


EXTRA = []                                             # (S721D) more runs, e.g. the end of msdcut's disk handler (0x0803B758, 36 B)


def install(img, report):
    import ct_fw
    BASE = ct_fw.APP_BASE
    stock = (Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    total = 0
    for a, n in RUNS + EXTRA:
        o = a - BASE
        assert img[o:o + n] == stock[o:o + n], f"run {a:#x} is not the stock's bytes"
        assert a % 2 == 0 and n % 2 == 0, hex(a)
        img[o:o + n] = UDF * (n // 2); total += n
    report["stocktrap"] = dict(runs=[(hex(a), n) for a, n in RUNS + EXTRA], bytes=total)
    return total
