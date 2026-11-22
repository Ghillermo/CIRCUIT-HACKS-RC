"""Alpha 7.21 (the user, 2026-11-20: «Cut unused stock features» -> «Easy Start USB drive»): the stock's USB mass-storage mode (Easy Start: the
Tracks shown as a USB drive) removed, and its disk-command handler's flash given to our code.

  * Settings parameter 2, bit 17 (WRONG, see use_midionly: 1 = Easy Start on = MIDI + the USB drive, 0 = USB MIDI only).  Its three reads that choose the USB mode now read 1: the
    settings listener's compare (0x08029E1A / 0x08029E1E: old = new, so a toggle does nothing) and the mode choice (0x08029E3C: always USB MIDI);
    the Setup view's Easy Start LED (0x0804732C) is dark (unavailable = no light, the user's rule).
  * The three calls of the SCSI command handler 0x0803B27C (in the drive's bulk-only transport, 0x08026DCE / 0x08026E28 / 0x08026E9A) are
    `mvn r0, #0` (-1: the command failed) instead: nothing calls the handler any more.
  * The handler and what only it uses, 0x0803B27C-0x0803B732 (1 206 B, tools/fullwalk.py with the handler cut), filled with 0xFF and offered
    as a new gap of dspz.add (GAP_OF): modules that never write to the card nor save settings may go there (below MOD_START, rodisk / lazysave
    see it as the stock's)."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

LO, HI = 0x0803B27C, 0x0803B732
PATCHES = [                                             # (address, the stock's bytes, ours)
    (0x08029E1A, bytes.fromhex("c1f34041"), bytes.fromhex("0121c046")),       # ubfx r1, r1, #17, #1 -> movs r1, #1; nop
    (0x08029E1E, bytes.fromhex("c0f34040"), bytes.fromhex("0120c046")),       # ubfx r0, r0, #17, #1 -> movs r0, #1; nop
    (0x08029E3C, bytes.fromhex("c1f34040"), bytes.fromhex("0120c046")),       # ubfx r0, r1, #17, #1 -> movs r0, #1; nop
    (0x0804732C, None, bytes.fromhex("0020")),                                # ldrh r0, [r5, r0] -> movs r0, #0
]
MIDIONLY = False                                        # (S725D3, use_midionly)


def use_midionly():
    """S725D3 (a fix, 2026-11-21): bit 17 = 1 is Easy Start ON (the factory default; the RAM dump of the user's unit has it at 1): the mode
    choice 0x08029E3C turns it into the second byte of the USB set-up's mode (0x08038C54), and 0x08038C98 registers the drive class
    (0x200000F8 -> the class table 0x0805A480) next to MIDI only when that byte is not 0.  So the three reads above made the Tracks a MIDI + USB
    drive device with a dead disk handler (S725D / S725D2 trapped in its DeInit and its descriptor getter, called by the USB stack at
    1.9 s).  With this the three reads give 0: USB MIDI only, the drive class never registered (the stock's own Easy Start off path)."""
    global MIDIONLY, PATCHES
    MIDIONLY = True
    PATCHES = [(a, old, bytes.fromhex("0021c046") if new == bytes.fromhex("0121c046") else bytes.fromhex("0020c046") if new == bytes.fromhex("0120c046") else new)
               for a, old, new in PATCHES]


CALLS = (0x08026DCE, 0x08026E28, 0x08026E9A)            # bl 0x0803B27C -> mvn r0, #0
MVN_M1 = bytes.fromhex("6ff00000")
DONE = {}


def install(img, report):
    """Once per build (the first module placed after it may use the gap: the builder sets dspz.GAP_OF)."""
    import ct_fw
    import dspz
    from thumb import bl as bl_enc
    if DONE.get("gap") is not None: return DONE["gap"]
    BASE = ct_fw.APP_BASE
    stock = (Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    for a, old, new in PATCHES:
        o = a - BASE
        assert img[o:o + len(new)] == stock[o:o + len(new)], f"{a:#x}: not the stock's bytes"
        if old is not None: assert bytes(img[o:o + len(old)]) == old, f"{a:#x}: {bytes(img[o:o + 4]).hex()}"
        img[o:o + len(new)] = new
    assert struct.unpack_from("<H", stock, 0x0804732C - BASE)[0] == 0x5A28, "0x0804732C: ldrh r0, [r5, r0]"
    for c in CALLS:
        o = c - BASE
        assert bytes(img[o:o + 4]) == bl_enc(c, LO), f"{c:#x}: not bl 0x0803B27C"
        img[o:o + 4] = MVN_M1
    assert img[LO - BASE:HI - BASE] == stock[LO - BASE:HI - BASE]
    img[LO - BASE:HI - BASE] = bytes([0xFF]) * (HI - LO)
    gaps = report["dspz"]["gaps"]
    gaps.append([hex(LO), hex(HI)])
    DONE["gap"] = len(gaps) - 1
    report["msdcut"] = dict(gap=[hex(LO), hex(HI)], index=DONE["gap"], patches=[hex(a) for a, _, _ in PATCHES], calls=[hex(c) for c in CALLS])
    return DONE["gap"]
