"""SC34D tests: our file next to the sessions (tools/sidecar34.py).  The stock file functions (open 0x08025CB8, read 0x08025D4C, write 0x08025D98, close 0x08025D10)
are replaced by a file system in memory (they need the SD card); the calls come in through the real vtable of the file class (0x0805B150), on one of the two stock
file objects ([0x20003738]), as the storage task makes them.

    python tools/emu_sc34d.py SC34D.bin SC34D_manifest.json
  * a write to ".../03_SESSION.ncs" passes to the stock write untouched (arguments, fifth argument on the stack) and marks bit 6 of byte 179;
  * its close: the stock close, then open ".../03_SC34D.bin" on the same object, read 16 bytes, write "SC34DTST" + saves + loads, close; the mark is cleared;
  * a second save: saves 2; a load (read + close): loads 1; a foreign file in our place starts again from 0;
  * other files (_PCM.wav, _PATCHBANK.cpb) and a close without a session: nothing more; our file cannot be opened: only the close.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc17_7 import E7  # noqa: E402
import sidecar34 as SC  # noqa: E402
import build_sc17 as B  # noqa: E402

OBJ_PTR = 0x20003738
BUF = 0x20060100


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["sidecar34"]["labels"].items()}
    vt = [struct.unpack_from("<I", img, SC.FVT + 4 * i - 0x08010000)[0] for i in range(6)]
    check(vt[1] == L["c_sc"] | 1 and vt[4] == L["c_sr"] | 1 and vt[5] == L["c_sw"] | 1 and vt[0] == SC.F_OPEN | 1, "vtable: close / read / write = ours, open = stock")
    gc.collect(); e = E7(img, man)
    obj = e.r32(OBJ_PTR)
    files, calls, cur, fail_open = {}, [], {}, [False]
    def cstr(a):
        out = b""
        while True:
            c = e.uc.mem_read(a + len(out), 1)
            if c == b"\0" or len(out) > 200: return out.decode()
            out += bytes(c)
    def ret(uc, v): uc.reg_write(UC_ARM_REG_R0, v); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    def h_open(uc, a, s, d):
        p = cstr(uc.reg_read(UC_ARM_REG_R1)); calls.append(("open", uc.reg_read(UC_ARM_REG_R0), p))
        if fail_open[0]: ret(uc, 1); return
        files.setdefault(p, b""); cur[uc.reg_read(UC_ARM_REG_R0)] = p
        e.uc.mem_write(uc.reg_read(UC_ARM_REG_R0) + SC.PATH_OFF, p.encode() + b"\0"); ret(uc, 0)
    def h_rw(kind):
        def h(uc, a, s, d):
            o, buf, n, off = (uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3))
            done = e.r32(uc.reg_read(UC_ARM_REG_SP)); p = cur.get(o)
            calls.append((kind, o, n, off, done))
            if kind == "read":
                data = files[p][off:off + n]; e.uc.mem_write(buf, data); m = len(data)
            else:
                data = bytes(e.uc.mem_read(buf, n)); f = files[p]; f = f + bytes(max(0, off - len(f))); files[p] = f[:off] + data + f[off + n:]; m = n
            if done: e.w32(done, m)
            ret(uc, 0)
        return h
    def h_close(uc, a, s, d):
        calls.append(("close", uc.reg_read(UC_ARM_REG_R0))); cur.pop(uc.reg_read(UC_ARM_REG_R0), None); ret(uc, 0)
    for addr, fn in ((SC.F_OPEN, h_open), (SC.F_READ, h_rw("read")), (SC.F_WRITE, h_rw("write")), (SC.F_CLOSE, h_close)):
        e.uc.hook_add(UC_HOOK_CODE, fn, begin=addr, end=addr)
    def vcall(slot, *args):                                                       # through the vtable, as the storage task calls it
        e.call(e.r32(SC.FVT + 4 * slot), *args, maxins=2_000_000)
        return e.uc.reg_read(UC_ARM_REG_R0)
    def open_as(path):
        files.setdefault(path, b""); cur[obj] = path; e.uc.mem_write(obj + SC.PATH_OFF, path.encode() + b"\0")
    SESS = "0:/Packs/Pack 01/Sessions/03_SESSION.ncs"
    SIDE = "0:/Packs/Pack 01/Sessions/03_SC34D.bin"
    e.uc.mem_write(BUF, b"0123456789")
    e.uc.mem_write(e.blk + 179, bytes([e.blkb(179)[0] & 0x3F]))
    open_as(SESS); calls.clear()
    vcall(5, obj, BUF, 10, 0)
    check(calls[:1] and calls[0][:4] == ("write", obj, 10, 0) and files[SESS] == b"0123456789", f"write to the session: the stock write with its arguments {calls[:1]}")
    check(e.blkb(179)[0] & SC.B_WR, "marked as written (bit 6)")
    calls.clear(); vcall(1, obj)
    seq = [c[0] for c in calls]
    check(seq == ["close", "open", "read", "write", "close"] and calls[1][2] == SIDE, f"close: stock close, then our file {calls[1][2] if len(calls) > 1 else ''}: {seq}")
    check(calls[2][2:4] == (16, 0) and calls[3][2:4] == (16, 0), "16 bytes at offset 0")
    check(calls[2][4] != 0 and calls[2][4] % 4 == 0 and calls[2][4] == calls[3][4], f"the fifth argument (bytes done) is a pointer on our stack frame ({calls[2][4]:#x})")
    check(files.get(SIDE) == SC.MAGIC + struct.pack("<II", 1, 0), f"our file: SC34DTST, 1 save, 0 loads {files.get(SIDE)}")
    check(not e.blkb(179)[0] & (SC.B_WR | SC.B_RD) and files[SESS] == b"0123456789", "the mark cleared; the session file untouched")
    open_as(SESS); vcall(5, obj, BUF, 4, 0); vcall(5, obj, BUF, 4, 4); vcall(1, obj)
    check(files[SIDE][8:16] == struct.pack("<II", 2, 0), f"a second save (two writes): saves 2 {files[SIDE][8:16].hex()}")
    open_as(SESS); calls.clear(); vcall(4, obj, BUF, 8, 0); vcall(1, obj)
    check(calls[0][0] == "read" and files[SIDE][8:16] == struct.pack("<II", 2, 1), f"a load (read + close): loads 1 {files[SIDE][8:16].hex()}")
    files[SIDE] = b"something else, not ours"
    open_as(SESS); vcall(5, obj, BUF, 4, 0); vcall(1, obj)
    check(files[SIDE][:16] == SC.MAGIC + struct.pack("<II", 1, 0), "a foreign file in our place: starts again from 0")
    for other in ("0:/Packs/Pack 01/PCM/_PCM.wav", "0:/Packs/Pack 01/Patches/_PATCHBANK.cpb"):
        open_as(other); calls.clear(); vcall(5, obj, BUF, 4, 0); vcall(1, obj)
        check([c[0] for c in calls] == ["write", "close"], f"{other.split('/')[-1]}: nothing more {[c[0] for c in calls]}")
    open_as(SESS); calls.clear(); vcall(1, obj)
    check([c[0] for c in calls] == ["close"], "a close without a session read / write: only the close")
    fail_open[0] = True
    open_as(SESS); vcall(5, obj, BUF, 4, 0); calls.clear(); vcall(1, obj)
    check([c[0] for c in calls] == ["close", "open", "close"], f"our file cannot be opened: nothing more than its close {[c[0] for c in calls]}")
    print("SC34D RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
