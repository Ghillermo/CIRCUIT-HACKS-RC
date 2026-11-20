"""S714D test (tools/patscan.py), through the real LED task and the real MIDI input:
  * 80 frames over the clean patterns: nothing frozen;
  * MIDI in (CC 7 = 100 on channel 1, a note on channel 10): both in the ring, in order;
  * a probability byte of 40 planted in MIDI 1's pattern 5 step 9 (and later a drum velocity of 200): within 64 frames the black box frozen
    (state 0x85), STK1 = 3, the value, its address, then the ring.

    python tools/emu_patscan.py BUILD.bin manifest.json
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc35 import E35, MGR, TICK  # noqa: E402
import emu_sc05 as X  # noqa: E402
import patscan as PS  # noqa: E402
import blackbox as BB  # noqa: E402
from unicorn.arm_const import UC_ARM_REG_R4  # noqa: E402


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = E35(img, man)
    def frame():
        from emu_sc05 import STOP
        e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR)
        e.call(0x08033B3E, maxins=5_000_000)
    st = lambda: e.r8(BB.BB + BB.O.ST)
    e.w32(TICK, 100000)
    for k in range(80): frame()
    check(not (st() & 1), f"80 frames over the clean patterns: nothing frozen (state {st():#x})")
    m = 0x20060100
    for t, msg in ((100500, (0xB0, 7, 100)), (100600, (0x99, 36, 90))):
        e.w32(TICK, t); e.uc.mem_write(m, bytes(msg) + b"\0"); e.call(0x08051720, X.CTX, m, maxins=2_000_000)
    ring = bytes(e.uc.mem_read(PS.MRING, 16 + 8 * PS.NRING))
    idx = struct.unpack_from("<I", ring, 4)[0]
    ents = [struct.unpack_from("<I4B", ring, 16 + 8 * i) for i in range(PS.NRING)]
    last2 = [ents[(idx - 2) % PS.NRING], ents[(idx - 1) % PS.NRING]]
    check(ring[:4] == b"MRG1" and last2[0][:4] == (100500, 0xB0, 7, 100) and last2[1][:4] == (100600, 0x99, 36, 90), f"the MIDI ring: {last2}")
    note5 = PS.NOTE[2] + 5 * PS.NPAT + 9 * 28 + 1                    # MIDI 1 (the third note track), pattern 5, step 9, its probability byte
    old = e.r8(note5); e.uc.mem_write(note5, bytes([40]))
    for k in range(70):
        frame()
        if st() & 1: break
    s1 = struct.unpack("<3I", bytes(e.uc.mem_read(BB.BB + BB.O.STK1, 12)))
    check(st() == 0x85 and s1 == (3, 40, note5), f"a probability of 40 caught after {k + 1} frames: state {st():#x}, STK1 {s1[0]}, {s1[1]}, {s1[2]:#x}")
    r2 = bytes(e.uc.mem_read(BB.BB + BB.O.STK1 + 12, 16 + 8 * PS.NRING))
    check(r2 == bytes(e.uc.mem_read(PS.MRING, 16 + 8 * PS.NRING)), "the ring copied into the record")
    e.uc.mem_write(note5, bytes([old])); e.uc.mem_write(BB.BB + BB.O.ST, bytes([0]))
    d = PS.DRUM[1] + 3 * PS.DPAT + 17
    e.uc.mem_write(d, bytes([200]))
    for k in range(70):
        frame()
        if st() & 1: break
    s1 = struct.unpack("<3I", bytes(e.uc.mem_read(BB.BB + BB.O.STK1, 12)))
    check(st() == 0x85 and s1 == (3, 200, d), f"a drum velocity of 200 caught: STK1 {s1[1]}, {s1[2]:#x}")
    print(f"{man.get('marker', '?')} PATSCAN RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text())) else 0)
