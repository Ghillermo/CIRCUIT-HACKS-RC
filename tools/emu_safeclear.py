"""Alpha 7.15 / S714D6 test (blackbox.use_safeclear): the black box's clear (SysEx 02, through the real dispatcher) zeroes the record but keeps the
LED head's live LR / frame (O.LR / O.FR) and the signature; before it zeroed them too (a crash when the LED task was inside the chain).

    python tools/emu_safeclear.py BUILD.bin manifest.json
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc35d8 as D  # noqa: E402
import blackbox as BB  # noqa: E402
import rdiag as RD  # noqa: E402


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = D.E8(img, man)
    e.uc.mem_write(BB.BB, struct.pack("<I", BB.SIG) + bytes([0x13]) + bytes(BB.SIZE - 5))
    e.uc.mem_write(BB.BB + BB.O.LR, struct.pack("<2I", 0x08067BBB, 0x20012345))
    e.uc.mem_write(BB.BB + 100, b"\xAA" * 8)
    e.sysex(list(RD.SIG) + [0x02, 9] + [0] * 7 + [0xF7], 0)
    lr, fr = struct.unpack("<2I", bytes(e.uc.mem_read(BB.BB + BB.O.LR, 8)))
    sig = struct.unpack("<I", bytes(e.uc.mem_read(BB.BB, 4)))[0]
    check(e.r8(BB.BB + BB.O.ST) == 0 and bytes(e.uc.mem_read(BB.BB + 100, 8)) == bytes(8) and sig == BB.SIG, "the clear: state 0, the record zeroed, the signature kept")
    check((lr, fr) == (0x08067BBB, 0x20012345), f"the LED head's LR / frame kept ({lr:#x}, {fr:#x})")
    print(f"{man.get('marker', '?')} SAFECLEAR RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text())) else 0)
