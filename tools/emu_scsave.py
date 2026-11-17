"""The chains' section (scrules) saved and loaded through the real stock save and the real content API (scrules.use_svfix(), Beta 5.63; the
2026-11-14 bug hunt, SCR-1 / XC-1).

    python tools/emu_scsave.py firmware/b5.62 [more build dirs]

On emu_sdsysex's firmware (real content API, storage task and path building; FatFs = a Python dictionary): the loaded pack = 1 (00_Alpha), the
stock save 0x0802FDF8(manager, slot 2, 0) (r5 there = the slot, [manager + 0x60] p0 = the pack), a chain in place, then the LED task's work
(c_srwork).  Expected: the section ("SCN3" + 564 B) at 186 812 of the file the stock just wrote (pack 1, project 2), nothing else on the card
created or grown, the storage task's current pack still 1; then a load of project 2 brings the chain back.  Up to Beta 5.62 the pack and the
slot were swapped: the section went to project 1 of pack 2.  Then a save in pack 0 (the internal pack, read-only for the mod): no write at all
(before: an item of another pack, or Save red through rodisk)."""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sdsysex as X  # noqa: E402
import scrules as SR  # noqa: E402
import xlanes as XL  # noqa: E402
import packio as PK  # noqa: E402

MAN = 0x2003D71C                     # the session manager: [+ 0x60] p0 = the loaded pack
SAVE = 0x0802FDF8                    # the stock save (manager, slot, flag)
OWN = X.A + "Sessions/02_Two.ncs"    # pack 1, project 2
OTHER = "1:/Tracks/01_Beta/Sessions/01_Other.ncs"     # pack 2, project 1: where 5.59-5.62 wrote


def run(d):
    d = Path(d); img = next(d.glob("*.bin")).read_bytes(); man = json.loads((d / "manifest.json").read_text())
    R = man["report"]
    A = {k: int(v, 16) for k, v in R["scrules"]["labels"].items()}
    B = {k: int(v, 16) for k, v in R["scrules"]["io"]["labels"].items()}
    prv = {k: int(v, 16) for k, v in R["scrules"]["prev"].items()}
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    f = X.boot(img); uc = f.uc
    for ad in (0x08029344, 0x080292F8, 0x08021064, 0x08029028):                # the DSP's reads / writes and its semaphore
        uc.hook_add(UC_HOOK_CODE, lambda u, a, s, dd: f._ret(u, 0), begin=ad, end=ad)
    uc.hook_add(UC_HOOK_CODE, lambda u, a, s, dd: u.reg_write(UC_ARM_REG_PC, u.reg_read(UC_ARM_REG_LR) | 1), begin=prv["load"], end=prv["load"])
    f.fs.put(OWN, X.SESSION); f.fs.put(OTHER, X.SESSION)
    snap = lambda: {k: bytes(v) for k, v in f.fs.files.items()}
    RB = SR.RB
    st = lambda o, n: bytes(uc.mem_read(RB + o, n))
    cur = lambda: f.r8(f.r32(X.CURPACK))
    WORD = SR.pack([(0, 1, 2), (3, 3, 1)])

    # ---- a save in pack 1, slot 2
    f.w8(f.store_p(f.r32(MAN + 0x60), 0), 1)
    f.fs.calls.clear()
    f.call(SAVE, MAN, 2, 0, maxins=60_000_000); f.background()
    stock = [c for c in f.fs.calls if c[0] == "write"]
    check(stock and all(c[1] == OWN for c in stock), f"the stock save wrote pack 1's project 2 ({sorted({c[1] for c in stock})})")
    check((st(SR.H_SIDX, 1)[0], st(SR.H_SPK, 1)[0]) == (2, 1), f"noted: project {st(SR.H_SIDX, 1)[0]}, pack {st(SR.H_SPK, 1)[0]} (expected 2, 1)")
    uc.mem_write(RB + SR.O_CURM, bytes([1])); uc.mem_write(RB + SR.O_CURW, struct.pack("<I", WORD))
    data = st(SR.O_DATA, SR.DATA)
    before, c0 = snap(), cur()
    f.fs.calls.clear(); f.call(B["c_srwork"], maxins=60_000_000); f.background()
    after = snap()
    own = after.get(OWN, b"")
    check(len(own) == SR.OFF + SR.SECT and own[SR.OFF:SR.OFF + 4] == b"SCN3" and own[SR.OFF + SR.HDR:] == data and own[:XL.SZ0] == before[OWN][:XL.SZ0],
          f"the section at {SR.OFF} of the file just saved ({len(own)} B)")
    other = {k for k in after if k != OWN and after[k] != before.get(k)}
    check(not other, f"nothing else on the card created or grown ({sorted(other)})")
    check(cur() == c0 == 1, f"the storage task's current pack unchanged ({c0} -> {cur()})")

    # ---- the load of project 2 (pack 0xFF = the loaded one): the chain back
    uc.mem_write(RB + SR.O_DATA, bytes(SR.DATA))
    pj = f.r32(XL.PROJ_OBJ + 0x20); f.w8(f.store_p(pj, 8), 2)
    f.call(A["c_srld"], maxins=10_000_000); f.call(B["c_srwork"], maxins=60_000_000); f.background()
    check(st(SR.O_DATA, SR.DATA) == data and st(SR.O_CURM, 1)[0] == 1 and struct.unpack("<I", st(SR.O_CURW, 4))[0] == WORD,
          "the load: the chain back from the file")

    # ---- a save in pack 0 (internal): nothing written by scrules
    f.w8(f.store_p(f.r32(MAN + 0x60), 0), 0)
    f.call(SAVE, MAN, 3, 0, maxins=60_000_000); f.background()
    uc.mem_write(RB + SR.O_CURM, bytes([1]))
    before = snap(); f.fs.calls.clear()
    f.call(B["c_srwork"], maxins=60_000_000); f.background()
    w = [c for c in f.fs.calls if c[0] in ("open", "write")]
    check(not w and snap() == before and not st(SR.H_FL, 1)[0] & SR.F_SAVE, f"a save in pack 0: no section write ({w[:3]})")
    del f; gc.collect()
    return fails


if __name__ == "__main__":
    n = 0
    for d in sys.argv[1:]:
        print("==", d); n += run(d)
    print("ALL PASS" if not n else f"{n} FAILED")
    sys.exit(1 if n else 0)
