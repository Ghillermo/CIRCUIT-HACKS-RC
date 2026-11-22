"""S725D (diagnostic, 2026-11-21; the user: «test whether we can clean it»): what is left of the stock's USB drive (Easy Start) after msdcut,
filled with UDF #0xD7 (0xDED7) like tools/stocktrap.py: anything that runs there freezes the black box with its PC.  The runs are the code that
tools/fullwalk.py (prel=True) reaches only through the drive's transport (0x08026DB0, called from the main loop when a drive packet came in) or
the drive class table (0x0805A47C-0x0805A4B8): 356 B, plus the 36 B msdcut left at 0x0803B758.  Hours of use and the stress runs with no
capture = the drive code is dead in USB MIDI mode and can be reused (in islands of 16-204 B)."""
from __future__ import annotations

UDF = bytes([0xD7, 0xDE])
RUNS = [(0x8026D94, 20), (0x8026DB0, 54), (0x8026ED6, 40), (0x803AC60, 22), (0x8058EC2, 204), (0x8058F90, 16), (0x803B758, 36)]
# (S725D on the device, 2026-11-21) trapped at 0x08058EC2 (LR 0x08036459, 1.9 s after power-up): the drive class's DeInit (0x08058EC2-0x08058ECB:
# 0x08026DA8, return 0), called through the class table by the USB stack's class dispatch (0x08047CF2) when the connection is set up, also
# in USB MIDI mode: the class stays registered.  use_live(): DeInit kept, its Setup (0x08058ECC) and the rest trapped (S725D2).
DEINIT = (0x8058EC2, 10)


def use_live():
    global RUNS
    RUNS = [r for r in RUNS if r != (0x8058EC2, 204)] + [(0x8058ECC, 194)]


def install(img, report):
    import ct_fw
    BASE = ct_fw.APP_BASE
    for a, n in RUNS:
        o = a - BASE
        assert a % 2 == 0 and n % 2 == 0 and bytes(img[o:o + n]) != UDF * (n // 2), hex(a)
        img[o:o + n] = UDF * (n // 2)
    report["usbtrap"] = dict(runs=[(hex(a), n) for a, n in RUNS], bytes=sum(n for _, n in RUNS))
    return report["usbtrap"]["bytes"]


# (S725D3 on the device, 2026-11-21: with msdcut.use_midionly) trapped at 0x08026DB0 (LR 0x0801F3A7, 5.1 s): the transport's entry, called
# by the main loop on a USB event flag in MIDI mode too; its first 20 B read the drive's state byte and return when no drive is active
# (0x08026DB0-0x08026DC3).  use_prologue(): those kept, the rest of the transport trapped (S725D4).
def use_prologue():
    global RUNS
    RUNS = [r for r in RUNS if r != (0x8026DB0, 54)] + [(0x8026DC4, 34)]
