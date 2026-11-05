"""The DX7 import of the card app (tools/sd_app.html) on the firmware: a slot written as the app writes it loads into the 8-operator FM.

    python tools/emu_dx7imp.py SC52.bin SC52_manifest.json

emu_sc39_4's harness (as emu_fm8store part A): slot 3 saved by the firmware with FM on gives a real padding; its FM block replaced by the app's
("FM" 3, on, 16 zeros, the check byte: sd_app's fmSet) and the slot's record by fm8.record(from_dx7(...)) for three voices (dx7ref: the E.Piano,
a noise voice, the single voice); c_mpload of slot 3: the track's 216 parameters = from_dx7 and FM on.  A bank cut before the record (the app
wrote nothing there) keeps the parameters (FM on from the padding)."""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fm8 as F  # noqa: E402
import fm8arm as A  # noqa: E402
import dx7ref as R  # noqa: E402

fails = 0
FM_AT, FM_LEN = 100, 21


def check(c, m):
    global fails
    print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1


def fm_block(on=1):                                     # sd_app's fmSet({ver: 3, on, params: 16 zeros})
    b = bytearray(b"FM" + bytes((3, on)) + bytes(16) + b"\0")
    b[FM_LEN - 1] = (0x5A + sum(b[:FM_LEN - 1])) & 0xFF
    return bytes(b)


def main(img, man):
    import emu_sc39_4 as T4
    Rp = man["report"]
    lab = lambda m, k: int(Rp[m]["labels"][k], 16)
    e = T4.E4(img, man); e.setup(man)
    e.btn(2); e.btn(8)
    e.call(lab("fm8", "c_fmst"))
    blk = A.FM8R + A.TB0
    e.uc.mem_write(blk + A.B_ON, b"\x01")
    stock = [bytes((3 + k + i) & 0x7F for i in range(340)) for k in range(8)]
    e.sd = {(3, 0, 0xFF): b"".join(stock[k] + b"\xFF" * 172 for k in range(7)) + stock[7]}
    e.call(lab("mpatch", "c_mpsave"), 0, 3, maxins=40_000_000)
    base = bytearray(e.sd[(3, 0, 0xFF)])
    p0 = 512 * 3 + 340
    base[p0 + FM_AT:p0 + FM_AT + FM_LEN] = fm_block()
    t = 4096 + 512 * 3
    voices = F.dx7_voices(R.bulk())
    for name, ops, g in (voices[0], voices[9], F.dx7_voices(R.single())[0]):
        want = F.from_dx7(ops, g)
        f = bytearray(base); f[t:t + F.REC_N] = F.record(want)
        e.sd[(3, 0, 0xFF)] = bytes(f)
        e.uc.mem_write(blk, bytes(F.PLEN)); e.uc.mem_write(blk + A.B_ON, b"\x00")
        e.call(lab("mpatch", "c_mpload"), 0, 3, maxins=40_000_000)
        got = bytes(e.uc.mem_read(blk, F.PLEN))
        check(got == want and e.r8(blk + A.B_ON) == 1, f"{name!r}: loaded, the 216 parameters = from_dx7, FM on (alg {got[F.GLB]}, fb {got[F.GLB + 1]})")
    e.sd[(3, 0, 0xFF)] = bytes(base[:t])
    e.uc.mem_write(blk, bytes(range(F.PLEN))); e.uc.mem_write(blk + A.B_ON, b"\x00")
    e.call(lab("mpatch", "c_mpload"), 0, 3, maxins=40_000_000)
    check(bytes(e.uc.mem_read(blk, F.PLEN)) == bytes(range(F.PLEN)) and e.r8(blk + A.B_ON) == 1, "no record: the parameters stay, FM on")
    del e; gc.collect()
    print(f"{man['marker']} DX7 IMPORT RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
