"""SC57.9 / Beta 5.64 / RC4.15 tests: the slot-7 vtable guard (rollers.use_vtguard, drumnote.use_vtguard; the black box record of 2026-11-15).

The record (Beta 5.63): the store commit 0x080353C0 of Drum 4's step store 0x2003bd90 called its entry 2, the listener sub-object 0x20043610
(= C3 + 8, the velocity bar of Drum 4) whose vtable word had become 0x0805AD60 (slot 7 of the drum Note view class 0x0805AD44): rollers.c_rlleds
ran with r0 = 0x20043610, drumnote.c_nvl took [[r0 + 4]] = [0x2003bbf4] = 0x1f020520 (a store header) as the LED buffer and read 0x1f02055e ->
BusFault.  On the RAM dump the harness boots from (the same objects as the device's):
  A. c_rlleds(fake) (and c_nvl(fake) where drumnote is guarded too) with a fake listener object ([fake] = 0x0805AD60, [fake + 4] = 0x2003bbf4 as on
     the device, and two other first words; [fake + 4] may also be unreadable): the guarded build returns with no RAM write at all (0x20000000..
     0x20050000 and the ITCM compared byte for byte) and r0 = the object; the unguarded build faults (--expect-fault, the positive control);
  B. the record's state: [0x20043610] = 0x0805AD60, change bit 1 on the store, then the real commit 0x080353C0(0x2003bd90): the guarded build
     returns (the other listeners of the store run as always); the unguarded faults at c_nvl + 6 with r0 0x1f020520, as the record;
  C. the legitimate path: slot 7 of 0x0805AD44 with the real drum Note view 0x200434d4 returns its LED buffer 0x200434fc with the rollers' rows
     painted (the same 64 B on both builds, printed as a hash), the four squares copied (c_nvl), and no byte outside that buffer changed.

    python tools/emu_vtguard.py BUILD.bin manifest.json [--expect-fault]
"""
from __future__ import annotations
import hashlib, json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn import UcError  # noqa: E402
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_R0  # noqa: E402
import emu_sc48_8 as S  # noqa: E402

VT_B, SLOT7_ADDR = 0x0805AD44, 0x0805AD60
C3L, STORE3, STORE1 = 0x20043610, 0x2003bd90, 0x2003bbf4
B_OBJ, B_BUF = 0x200434d4, 0x200434fc
COMMIT = 0x080353C0
FAKE = 0x20061000                                               # free emulated RAM (not the device's SRAM: the harness's stack region)
FAKE_EDGE = 0x2006FFFC                                          # the last word of the mapped region: [fake + 4] unreadable
RAM, RAM_N = 0x20000000, 0x50000
ITCM, ITCM_N = 0x0, 0x4000


def snap(e): return bytes(e.uc.mem_read(RAM, RAM_N)) + bytes(e.uc.mem_read(ITCM, ITCM_N))


def diff(a, b, limit=8):
    out = []
    for i in range(len(a)):
        if a[i] != b[i]:
            out.append((hex((RAM + i) if i < RAM_N else (ITCM + i - RAM_N)), hex(a[i]), hex(b[i])))
            if len(out) >= limit: break
    return out


def run(e, fn, *args):
    try:
        e.call(fn, *args, maxins=2_000_000)
        return ("ok", e.uc.reg_read(UC_ARM_REG_R0))
    except UcError as ex:
        return ("fault", str(ex), hex(e.uc.reg_read(UC_ARM_REG_PC)), hex(e.uc.reg_read(UC_ARM_REG_R0)))


def main(a):
    img, man = Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text())
    expect_fault = "--expect-fault" in a
    R = man["report"]
    c_rlleds = int(R["rollers"]["labels"]["c_rlleds"], 16); c_nvl = int(R["drumnote"]["labels"]["c_nvl"], 16)
    guarded = lambda fn: struct.unpack_from("<H", img, fn - 0x08010000)[0] == 0x6801          # `ldr r1, [r0]` first: the guard
    e = S.ET(img, man)
    slot7 = e.r32(SLOT7_ADDR)
    print(f"{Path(a[0]).name}: slot 7 of 0x0805AD44 = {slot7:#x} (c_rlleds {c_rlleds:#x} guarded {guarded(c_rlleds)}, c_nvl {c_nvl:#x} guarded {guarded(c_nvl)}); fault expected: {expect_fault}")
    assert slot7 == (c_rlleds | 1)
    assert e.r32(C3L) == 0x0805ADA8 and e.r32(C3L + 4) == STORE1 and e.r32(STORE1) == 0x1f020520, (hex(e.r32(C3L)), hex(e.r32(C3L + 4)), hex(e.r32(STORE1)))
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    if not expect_fault:
        check(guarded(c_rlleds), "c_rlleds starts with the vtable check")

    # A. the fake listener object, three first words; the routines that carry the guard
    fns = [("c_rlleds", c_rlleds)] + ([("c_nvl", c_nvl)] if guarded(c_nvl) or expect_fault else [])
    for first in (SLOT7_ADDR, 0x0805ADA8, 0x12345678):
        for name, fn in fns:
            e.w32(FAKE, first); e.w32(FAKE + 4, STORE1); e.w32(FAKE + 8, 0); e.w32(FAKE + 12, 0)
            before = snap(e); r = run(e, fn, FAKE, STORE3, 2); after = snap(e)
            d = diff(before, after)
            if expect_fault:
                check(r[0] == "fault" and "UNMAPPED" in r[1] and r[2] == hex(c_nvl + 6), f"A: {name}(fake [this]={first:#x}) faults at c_nvl + 6 on the unguarded build ({r})")
            else:
                check(r == ("ok", FAKE) and not d, f"A: {name}(fake [this]={first:#x}) returns r0 = the object, no RAM / ITCM write ({r}, diff {d})")
    # A'. [fake + 4] unreadable: the guard must not touch it
    e.w32(FAKE_EDGE, SLOT7_ADDR)
    r = run(e, c_rlleds, FAKE_EDGE, STORE3, 2)
    if expect_fault: check(r[0] == "fault", f"A': c_rlleds(fake at the edge) faults on the unguarded build ({r})")
    else: check(r == ("ok", FAKE_EDGE), f"A': c_rlleds(fake at the edge of the mapped RAM) returns without reading [this + 4] ({r})")

    # B. the record's state through the real commit
    e.w32(C3L, SLOT7_ADDR); e.w32(STORE3 + 8, 2)
    before = snap(e); r = run(e, COMMIT, STORE3); after = snap(e)
    if expect_fault:
        check(r[0] == "fault" and r[2] == hex(c_nvl + 6) and r[3] == hex(0x1f020520), f"B: commit(0x2003bd90) with [0x20043610] = 0x0805AD60 faults as the record ({r})")
    else:
        d = diff(before, after, 40)
        check(r[0] == "ok", f"B: commit(0x2003bd90) with [0x20043610] = 0x0805AD60 returns ({r}); {len(d)} bytes changed by the store's other listeners: {d[:12]}")
        check(e.r32(C3L) == SLOT7_ADDR and e.r32(C3L + 4) == STORE1, "B: the corrupted entry and its store pointer untouched (nothing wrote through the fake `this`)")
    e.w32(C3L, 0x0805ADA8); e.w32(STORE3 + 8, 0)

    # C. the legitimate path: slot 7 with the real drum Note view
    tail = e.r32(0x2003D71C + 0x14) + 0x27024                   # rollers' stamp (use_v2): the tail + 964..967 = the time the view's LEDs were asked for
    before = snap(e); r = run(e, slot7 & ~1, B_OBJ); after = snap(e)
    buf = bytes(e.uc.mem_read(B_BUF, 64))
    d = [x for x in diff(before, after, 200) if not (B_BUF <= int(x[0], 16) < B_BUF + 64 or tail + 964 <= int(x[0], 16) < tail + 968)]
    rows = struct.unpack("<24H", buf[:48]); sq = struct.unpack("<8H", buf[48:64])
    check(r == ("ok", B_BUF), f"C: slot 7 (c_rlleds) with the drum Note view 0x200434d4 returns its LED buffer 0x200434fc ({r})")
    check(all(v in (0x45, 0x46, 0x2D, 0x2E, 0x49, 0x4A, 0x4D, 0x4E) for v in rows), f"C: rows 1-3 = the rollers' colours ({[hex(v) for v in rows[:8]]} ...)")
    check(sq[:4] in (sq[4:], sq[4:][::-1]), f"C: entries 24-27 = the squares 28-31 (c_nvl; mirrored since SC23.4) ({buf[48:64].hex()})")
    check(not d, f"C: nothing outside the buffer (and rollers' stamp) written ({d[:6]})")
    print(f"C: buffer sha256 {hashlib.sha256(buf).hexdigest()[:16]} (compare between builds)")
    print(f"{Path(a[0]).name} VTGUARD RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1:]) else 0)
