"""SC46.9 ARM test (recinst.use_sig, fmeng.use_sig2): RAM left by the power-up or by an older build.

    python tools/emu_risig.py NEW.bin NEW_manifest.json OLD.bin OLD_manifest.json      (OLD = SC46.8 / Beta 3.25)

  * recinst's four bytes (MXR + 0x180) filled with a power-up pattern, MIDI 1's track view with the engine on, a step pad without Record: OLD
    swallows it (the bug: no step entry until Record is pressed), NEW passes it to the stock's step handler; NEW: Record held + the step still
    swallows it (the snapshot), and after Record let go the pads are the stock's;
  * the FM's block (MXR + 0x200) with a version-1 block ("FME1", Shift + K1-K4 = 0): NEW sets it up again at the first use ("FME2", the
    defaults: Shift + K1-K4 at the centre); OLD keeps the 0s (= percussive, the shortest decay).
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402  (its import sets vcf21's options)
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
import recinst as RI  # noqa: E402
import fmeng as F  # noqa: E402

V = T4.V
MGR = X.MGR


def run_one(img, man, pattern):
    e = X.EP(img, man)
    R = man["report"]
    spad = int(R["recinst"]["prev"]["spad"], 16)
    hits = []
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: hits.append(1), begin=spad, end=spad)
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05]))       # the engine on (MIDI 1)
    e.uc.mem_write(RI.RAM, pattern)
    e.btn(2)                                                                            # MIDI 1's track view
    e.call(PRESS, MGR, 4, 100, maxins=8_000_000); e.call(RELEASE, MGR, 4, maxins=8_000_000)
    plain = len(hits)
    hits.clear()
    e.call(0x08033320, MGR, RI.REC_ID, maxins=8_000_000)
    e.call(PRESS, MGR, 5, 100, maxins=8_000_000); e.call(RELEASE, MGR, 5, maxins=8_000_000)
    held = len(hits)
    e.call(0x0803381A, MGR, RI.REC_ID, maxins=8_000_000)
    hits.clear()
    e.call(PRESS, MGR, 6, 100, maxins=8_000_000); e.call(RELEASE, MGR, 6, maxins=8_000_000)
    after = len(hits)
    # the FM block of a version 1 build
    blk = bytearray(64 + 16 + 128)
    struct.pack_into("<I", blk, 0, F.SIG)
    blk[F.B0:F.B0 + 16] = bytes(F.DEFAULTS)                                             # version 1's defaults: Shift + K1-K4 = 0
    e.uc.mem_write(F.FMR, bytes(blk))
    fl = {k: int(v, 16) for k, v in R["fmeng"]["labels"].items()}
    e.call(fl["c_fmst"], maxins=1_000_000)
    sig = e.r32(F.FMR)
    atk = [e.r8(F.FMR + F.B0 + F.P_ATK + k) for k in range(4)]
    del e; gc.collect()
    return plain, held, after, sig, atk


def main(img, man, old, oman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    for pat in (bytes([0xA5]) * 8, bytes([1, 0, 0, 0, 0x12, 0x34, 0x56, 0x78]), bytes([0xFF]) * 8):
        n = run_one(img, man, pat); o = run_one(old, oman, pat)
        check(o[0] == 0, f"OLD, RAM {pat[:4].hex()}: the step pad swallowed (the bug reproduced: {o[0]} calls of the stock's step handler)")
        check(n[0] >= 1 and n[1] == 0 and n[2] >= 1, f"NEW, RAM {pat[:4].hex()}: a step pad goes to the stock ({n[0]}), with Record held the snapshot "
              f"swallows it ({n[1]}), after Record the stock's again ({n[2]})")
        check(n[3] == F.SIG2 and n[4] == [F.CENTRE] * 4, f"NEW: a version-1 FM block set up again (signature {n[3]:#x}, Shift + K1-K4 {n[4]})")
        check(o[3] == F.SIG and o[4] == [0] * 4, f"OLD: the version-1 block kept (Shift + K1-K4 {o[4]}: percussive, the shortest decay)")
    print(f"{man.get('marker', '?')} RISIG RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
