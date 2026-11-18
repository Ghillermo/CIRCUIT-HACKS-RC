"""Audit (2026-11-17, the 5.63 / 5.64 crashes): run an emulation test with a write hook on the session's pattern memory and report every write that
leaves a value the stock pad painters cannot draw: a note step's probability (byte [1]) > 7, a note unit's velocity > 127, a note step's unit mask
(byte [0]) with bits 6-7, a drum step's velocity > 127; and every trip of paintguard's skips (c_pgl / c_vg returning without painting).  Each find
names the writing code (PC, LR; «ours» when the instruction bytes differ from the stock flash) and the pattern / step.  Writes the tests make
themselves (uc.mem_write) are not hooked.

    python tools/bytewatch.py tools/emu_xxx.py ARGS...     (the test runs as usual; the report follows its output)
"""
from __future__ import annotations
import atexit
import runpy
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc05  # noqa: E402
from unicorn import UC_HOOK_MEM_WRITE, UC_HOOK_CODE  # noqa: E402
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_LR, UC_ARM_REG_R0, UC_ARM_REG_R4  # noqa: E402

LO, HI = 0x2001183C, 0x2001183C + 0x2740C                 # the session record in the RAM dump
NOTE = (("note A", 0x20011B20), ("note B", 0x20018060), ("note C", 0x2002BAB8), ("note D", 0x20031FF8))
DRUM = tuple((f"drum {d + 1}", 0x2001E5B0 + 0x3540 * d) for d in range(4))
NPAT, DPAT = 0xCA8, 0x6A8
FINDS = {}
TRIPS = []
WRITES = [0]
GUARDS = {}


def classify(a, v):
    for name, base in NOTE:
        if base <= a < base + 8 * NPAT:
            p, o = divmod(a - base, NPAT)
            if o >= 0x380: return None
            s, b = divmod(o, 28)
            if b == 1 and v > 7: return f"{name} pat {p} step {s}: probability {v}"
            if b == 0 and v & 0xC0: return f"{name} pat {p} step {s}: unit mask 0x{v:02x}"
            if b >= 4 and (b - 4) % 4 == 3 and v > 127: return f"{name} pat {p} step {s} unit {(b - 4) // 4}: velocity {v}"
            return None
    for name, base in DRUM:
        if base <= a < base + 8 * DPAT:
            p, o = divmod(a - base, DPAT)
            if o < 0x20 and v > 127: return f"{name} pat {p} step {o}: velocity {v}"
            return None
    return None


def _hook_write(uc, access, a, size, value, emu):
    WRITES[0] += 1
    pc = uc.reg_read(UC_ARM_REG_PC); lr = uc.reg_read(UC_ARM_REG_LR)
    for i in range(size):
        k = classify(a + i, (value >> (8 * i)) & 0xFF)
        if k:
            ours = bytes(uc.mem_read(pc & ~1, 2)) != emu_sc05.FL[(pc & ~1) - 0x08000000:(pc & ~1) - 0x08000000 + 2]
            key = (pc, lr)
            f = FINDS.setdefault(key, dict(n=0, first=k, ours=ours, addr=a + i, size=size, base=a))
            f["n"] += 1


def _hook_guard(uc, a, s, d):
    n = GUARDS[a]                                                    # pg_x: the byte in r4; vg_x: in r0 (moved to r4 after the label)
    TRIPS.append((n, uc.reg_read(UC_ARM_REG_R4 if n == "pg_x" else UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_LR)))


_init = emu_sc05.E.__init__


def _patched(self, image):
    _init(self, image)
    self.uc.hook_add(UC_HOOK_MEM_WRITE, _hook_write, self, LO, HI)
    for a in GUARDS: self.uc.hook_add(UC_HOOK_CODE, _hook_guard, None, a, a)


def report():
    print(f"\n==== bytewatch: {WRITES[0]} writes to the session record watched")
    if not FINDS and not TRIPS: print("     nothing out of range"); return
    for (pc, lr), f in sorted(FINDS.items()):
        print(f"     {'OURS ' if f['ours'] else 'stock'} pc {pc:#010x} lr {lr:#010x} x{f['n']}: {f['first']} (at {f['addr']:#010x}, a {f['size']}-byte write at {f['base']:#010x})")
    for name, v, lr in TRIPS[:20]: print(f"     paintguard {name} skipped value {v} (lr {lr:#010x})")


def main(argv):
    test, args = argv[0], argv[1:]
    import json
    for x in args:                                                   # paintguard's skip labels from the manifest, when the build has them
        m = Path(x) / "manifest.json" if Path(x).is_dir() else Path(x)
        if m.name.endswith("manifest.json") and m.exists():
            M = json.loads(m.read_text())
            L = M.get("report", M).get("paintguard", {}).get("labels", {})
            for n in ("pg_x", "vg_x"):
                if n in L: GUARDS[int(L[n], 16)] = n
            break
    emu_sc05.E.__init__ = _patched
    atexit.register(report)
    sys.argv = [test] + args
    runpy.run_path(test, run_name="__main__")


if __name__ == "__main__":
    main(sys.argv[1:])
