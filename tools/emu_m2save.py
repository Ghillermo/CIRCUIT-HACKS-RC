"""Alpha 7.42 test (m2lanes): the Macros 2 lanes' section saved and loaded through the real stock save and the real content API.

    python tools/emu_m2save.py firmware/a7.42

On emu_sdsysex's firmware (real content API, storage task; FatFs = a Python dictionary), as emu_scsave: the loaded pack = 1, the stock save
0x0802FDF8(manager, slot 2, 0), lanes in the ITCM, then the LED task's work (c_m2work).  Expected:
  * before the ITCM is ours (the power-up send not done): nothing, the flags kept;
  * the section ("M2L1", version 1, the bitmap, 8 192, the checksum + the 8 KB) at 187 392 of the file the stock just wrote, nothing else on the
    card created or grown, the storage task's current pack unchanged;
  * a load of project 2 brings the 8 KB and the bitmap back and the lanes in place; with Synth 1 / 2's patterns changed in the record (another
    session in the file): no lanes (0xFF), the bitmap 0, the lanes in place;
  * a new project: no lanes; a save in pack 0: no write; a project without lanes and a short file: nothing written;
  * a state without the signature (the Easy Start buffer over it): nothing; a save noted for pack 40: nothing."""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sdsysex as X  # noqa: E402
import m2lanes as M  # noqa: E402
import xlanes as XL  # noqa: E402
import persist19 as P19  # noqa: E402

MAN = 0x2003D71C
SAVE = 0x0802FDF8
OWN = X.A + "Sessions/02_Two.ncs"


def run(d):
    d = Path(d); img = next(d.glob("*.bin")).read_bytes(); man = json.loads((d / "manifest.json").read_text())
    R = man["report"]
    A = {k: int(v, 16) for k, v in R["m2lanes"]["labels"].items()}
    B = {k: int(v, 16) for k, v in R["m2lanes"]["io"]["labels"].items()}
    prv = {k: int(v, 16) for k, v in R["m2lanes"]["prev"].items()}
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    f = X.boot(img); uc = f.uc
    for ad in (0x08029344, 0x080292F8, 0x08021064, 0x08029028):
        uc.hook_add(UC_HOOK_CODE, lambda u, a, s, dd: f._ret(u, 0), begin=ad, end=ad)
    for k in ("load", "new"):                                                   # the chains below the load / new heads: not run here
        uc.hook_add(UC_HOOK_CODE, lambda u, a, s, dd: u.reg_write(UC_ARM_REG_PC, u.reg_read(UC_ARM_REG_LR) | 1), begin=prv[k], end=prv[k])
    f.fs.put(OWN, X.SESSION)
    snap = lambda: {k: bytes(v) for k, v in f.fs.files.items()}
    st = lambda o, n: bytes(uc.mem_read(M.M2 + o, n))
    st8 = lambda o: st(o, 1)[0]
    cur = lambda: f.r8(f.r32(X.CURPACK))
    it = lambda: bytes(uc.mem_read(M.IT0, M.DATA))
    work = lambda: (f.call(B["c_m2work"], maxins=80_000_000), f.background())
    uc.mem_write(M.M2, bytes(M.ST_LEN))
    data = bytes((i * 37 + 11) & 0xFF if (i // 64) % 3 == 0 else 0xFF for i in range(M.DATA))
    uc.mem_write(M.IT0, data); uc.mem_write(M.M2 + M.O_MAP, struct.pack("<H", 0x0101))

    # ---- a save in pack 1, slot 2, before the ITCM is ours: noted, nothing written
    f.w8(f.store_p(f.r32(MAN + 0x60), 0), 1)
    f.fs.calls.clear()
    f.call(SAVE, MAN, 2, 0, maxins=60_000_000); f.background()
    check((st8(M.O_SIDX), st8(M.O_SPK), st8(M.O_FL) & M.F_SAVE) == (2, 1, M.F_SAVE), f"noted: project {st8(M.O_SIDX)}, pack {st8(M.O_SPK)}, the save flag")
    before, c0 = snap(), cur()
    f.fs.calls.clear(); work()
    check(snap() == before and st8(M.O_FL) & M.F_SAVE, "the ITCM not ours yet: nothing written, the save still pending")

    # ---- the ITCM ours: the section written
    uc.mem_write(M.M2 + M.O_SIG, struct.pack('<I', M.SSIG)); uc.mem_write(M.M2 + M.O_VAL, bytes([1]))
    f.fs.calls.clear(); work()
    after = snap(); own = after.get(OWN, b"")
    hdr = own[M.OFF:M.OFF + M.HDR]
    ssum = struct.unpack("<I", st(M.O_SSUM, 4))[0]
    check(len(own) == M.OFF + M.SECT and hdr == struct.pack("<IHHII", M.MAGIC, 1, 0x0101, M.DATA, ssum) and own[M.OFF + M.HDR:] == data
          and own[:XL.SZ0] == before[OWN][:XL.SZ0], f"the section at {M.OFF} of the file just saved ({len(own)} B, header {hdr.hex()})")
    other = {k for k in after if k != OWN and after[k] != before.get(k)}
    check(not other, f"nothing else on the card created or grown ({sorted(other)})")
    check(cur() == c0 == 1 and not st8(M.O_FL) & M.F_SAVE, f"the storage task's current pack unchanged ({c0} -> {cur()}), the flag cleared")

    # ---- the load of project 2: the lanes back
    uc.mem_write(M.IT0, b"\xFF" * M.DATA); uc.mem_write(M.M2 + M.O_MAP, bytes(2))
    pj = f.r32(XL.PROJ_OBJ + 0x20); f.w8(f.store_p(pj, 8), 2)
    f.call(A["c_m2ld"], maxins=10_000_000)
    check(st8(M.O_VAL) == 0 and st8(M.O_FL) & M.F_LOAD, "the load head: the lanes not in place, the load pending")
    work()
    check(it() == data and struct.unpack("<H", st(M.O_MAP, 2))[0] == 0x0101 and st8(M.O_VAL) == 1 and not st8(M.O_FL) & M.F_LOAD,
          "the load: the 8 KB and the bitmap back from the file, the lanes in place")

    # ---- another session in the file (Synth 1's patterns changed in the record): no lanes
    rec = f.r32(P19.SESSION_OBJ + 0x14)
    b0 = f.r8(rec + M.SYN_AREA + 5); f.w8(rec + M.SYN_AREA + 5, b0 ^ 0x5A)
    f.call(A["c_m2ld"], maxins=10_000_000); work()
    check(it() == b"\xFF" * M.DATA and struct.unpack("<H", st(M.O_MAP, 2))[0] == 0 and st8(M.O_VAL) == 1,
          "the checksum does not match: no lanes, the bitmap 0, the lanes in place")
    f.w8(rec + M.SYN_AREA + 5, b0)

    # ---- a new project: no lanes
    uc.mem_write(M.IT0, data); uc.mem_write(M.M2 + M.O_MAP, struct.pack("<H", 0x0101))
    f.call(A["c_m2new"], maxins=10_000_000); work()
    check(it() == b"\xFF" * M.DATA and struct.unpack("<H", st(M.O_MAP, 2))[0] == 0 and st8(M.O_VAL) == 1 and st8(M.O_FL) == 0,
          "a new project: no lanes, the lanes in place")

    # ---- a save in pack 0 (internal): nothing
    f.w8(f.store_p(f.r32(MAN + 0x60), 0), 0)
    uc.mem_write(M.IT0, data); uc.mem_write(M.M2 + M.O_MAP, struct.pack("<H", 0x0101))
    f.call(SAVE, MAN, 3, 0, maxins=60_000_000); f.background()
    before = snap(); f.fs.calls.clear(); work()
    w = [c for c in f.fs.calls if c[0] in ("open", "write")]
    check(not w and snap() == before and not st8(M.O_FL) & M.F_SAVE, f"a save in pack 0: no write ({w[:3]})")

    # ---- a project without lanes, a short file: nothing written
    SHORT = X.A + "Sessions/03_Three.ncs"
    f.fs.put(SHORT, X.SESSION)
    f.w8(f.store_p(f.r32(MAN + 0x60), 0), 1)
    uc.mem_write(M.IT0, b"\xFF" * M.DATA); uc.mem_write(M.M2 + M.O_MAP, bytes(2))
    f.call(SAVE, MAN, 3, 0, maxins=60_000_000); f.background()
    before = snap(); f.fs.calls.clear(); work()
    check(len(snap().get(SHORT, b"")) == len(before.get(SHORT, b"")), f"no lanes and a short file: nothing appended ({len(before.get(SHORT, b''))} B)")
    # ---- a state overwritten (the stock's Easy Start buffer): no signature = nothing; a pack out of range = nothing
    uc.mem_write(M.IT0, data); uc.mem_write(M.M2, bytes([0x37]) * M.ST_LEN)
    before = snap(); f.fs.calls.clear(); work()
    w = [c for c in f.fs.calls if c[0] in ("open", "write")]
    check(snap() == before and not w, f"a state without the signature: nothing read or written ({w[:3]})")
    uc.mem_write(M.M2 + M.O_SIG, struct.pack("<I", M.SSIG)); uc.mem_write(M.M2 + M.O_FL, bytes([M.F_SAVE]))
    uc.mem_write(M.M2 + M.O_SPK, bytes([40])); uc.mem_write(M.M2 + M.O_SIDX, bytes([2]))
    before = snap(); f.fs.calls.clear(); work()
    w = [c for c in f.fs.calls if c[0] in ("open", "write")]
    check(snap() == before and not w and not st8(M.O_FL) & M.F_SAVE, f"a save noted for pack 40: nothing written, the flag cleared ({w[:3]})")
    del f; gc.collect()
    return fails


if __name__ == "__main__":
    n = 0
    for d in sys.argv[1:]:
        print("==", d); n += run(d)
    print("M2SAVE RESULT:", "ALL PASS" if not n else f"{n} FAILED")
    sys.exit(1 if n else 0)
