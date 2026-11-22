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


# (S721D on the device, 2026-11-21) the run at 0x0801A7EA is live: the C runtime's zero-init (it clears the RAM's zero-initialised data at boot),
# called through the scatter-load table at 0x0805B7B4 by the loop at 0x0805B590 (`blx r1` on a table-relative offset: tools/fullwalk.py does
# not follow it).  S721D trapped there at once (PC 0x0801A7EA, LR 0x0805B5A9, CFSR UNDEFINSTR) and never came up on USB.  The table's other
# two handlers (0x080596C4, 0x0805B958) sit in data-area runs already dropped.  The boot emulation (from the reset vector, restoring each
# run it traps in) then went through 16 more: the C++ static constructors (table 0x0805B5B8..0x0805B5E0, loop 0x0805B978) and what they call.
# tools/fullwalk.py walk(..., prel=True) takes both tables as roots: with them only 9 stock runs (364 B) stay dead, 6 below the data area.
# use_boot(): trap only those (S721D2); never reuse a run in BOOT_LIVE.
BOOT = (0x801A7EA, 58)
BOOT_LIVE = [(0x8022E26, 248), (0x8025070, 132), (0x801DEA4, 108), (0x801E56C, 88), (0x801A7EA, 58), (0x801E480, 48), (0x804633C, 42),
             (0x8040386, 34), (0x802EB96, 34), (0x801DC64, 34), (0x802E688, 26), (0x80244B8, 26), (0x80373A4, 24), (0x8022890, 24),
             (0x8022698, 10), (0x801E788, 8), (0x804A35A, 56)]
NOBOOT = False


def use_boot():
    global NOBOOT
    NOBOOT = True


# (S721D2 on the device, 2026-11-21) trapped at 0x0802244A (LR 0x080493D9, task Main, 301 ms after boot): the C library's sprintf char-store
# callback, passed as ldr r0, [pc, #x]; add r0, pc; adds r0, #0x1e (0x0803AF2C); fullwalk(prel=True) now follows that pattern and reaches it
# and 0x0801D102.  The four runs still unreached in the stock (0x08018548, 0x080557A8, 0x080557C0, 0x08055C06) are byte tables, not code:
# trapping them would change data, not trap.  Result: no dead stock code to reuse; only what our own patches bypass (0x080470A8, 0x0804D398)
# and the end of msdcut's handler (0x0803B758): 94 B.  The stock-trap line of work ends here.
LIVE2 = [(0x802244A, 10), (0x801D102, 26)]
DATA_LIKE = [(0x8018548, 20), (0x80557A8, 22), (0x80557C0, 52), (0x8055C06, 182)]

EXTRA = []                                             # (S721D) more runs, e.g. the end of msdcut's disk handler (0x0803B758, 36 B)


def install(img, report):
    import ct_fw
    BASE = ct_fw.APP_BASE
    stock = (Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    total = 0
    runs = [r for r in RUNS if not (NOBOOT and r in BOOT_LIVE)] + EXTRA
    for a, n in runs:
        o = a - BASE
        assert img[o:o + n] == stock[o:o + n], f"run {a:#x} is not the stock's bytes"
        assert a % 2 == 0 and n % 2 == 0, hex(a)
        img[o:o + n] = UDF * (n // 2); total += n
    report["stocktrap"] = dict(runs=[(hex(a), n) for a, n in runs], bytes=total)
    return total
