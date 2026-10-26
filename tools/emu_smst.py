"""SC46.8 ARM tests (tools/smst.py): the stereo sample mode's second sample in smpick's picker, through the controller and the real LED task:
  * MIDI 1 in the sample mode, the picker (Note twice): K = 1 at first, written to the DSP (X:OSB0 + 43) by the service chain's head;
  * a tap = the first and it sounds (smpick's); Shift + a sample = the first without a note; Shift + the first = choosing the second (its pad blinks
    cyan, the first violet); there a tap = the second (K = the distance) and it sounds, Shift + a sample = the second without a note, Shift + the
    second = back to the first; the new K reaches the DSP at the next tick;
  * choosing the first with WAVE > 0: the second violet, with Shift the first yellow; changing the first keeps the distance;
  * the picker off the screen: back to choosing the first;
  * the patch: gather writes 0xB5, K, the check at padding + 121; apply reads it (K), a patch without it = 1.

    python tools/emu_smst.py SC46.8.bin SC46.8_manifest.json
"""
from __future__ import annotations
import json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R5, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
import packio as PK  # noqa: E402
import modesel as MS  # noqa: E402
import smpick as SP  # noqa: E402
import smst as SS  # noqa: E402
import mpatch as MP  # noqa: E402
import vcf21_dsp as VD  # noqa: E402

V = T4.V
MGR = X.MGR


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    R = man["report"]
    sl = {k: int(v, 16) for k, v in R["smst"]["labels"].items()}
    pl = {k: int(v, 16) for k, v in R["smpick"]["labels"].items()}
    ml = {k: int(v, 16) for k, v in R["mpatch"]["labels"].items()}
    e = X.EP(img, man)
    dw = []
    def w(uc, a, s, d): dw.append((uc.reg_read(UC_ARM_REG_R1) >> 8, uc.reg_read(UC_ARM_REG_R2)))
    e.uc.hook_add(UC_HOOK_CODE, w, begin=0x080292F8, end=0x080292F8)
    def tick(n=1):
        for _ in range(n): e.at(e.t + 1); e.call(sl["c_sstick"], maxins=8_000_000)
    KADDR = VD.OSB0 + VD.SM_K
    def lastk():
        v = [x for x, a in dw if a == KADDR]; return v[-1] if v else None
    K = lambda: e.r8(SS.SMS + SS.O_K)
    mode = lambda: e.r8(SS.SMS + SS.O_MODE)
    first = lambda: e.val(0, 25)
    def shift_pad(q):
        e.shift(True); e.pad(q); e.shift(False)
    e.btn(2); e.btn(8); e.pad(26); e.pad(MS.ROW + 5); e.pad(26)                         # MIDI 1: the sample mode
    for _ in range(4):
        if e.r8(MGR + SP.S_CUR) == SP.PICK[0]: break
        e.btn(9)
    check(e.r0(pl["c_spk"]) == 0, f"Note twice: the picker of MIDI 1 (c_spk {e.r0(pl['c_spk'])})")
    dw.clear(); tick(1)
    check(K() == 1 and lastk() == 1, f"K 1 at first, written to the DSP (X:{KADDR:#x} = {lastk()})")
    n0 = len(e.ons); e.pad(16 + 4)
    check(first() == 4 and len(e.ons) > n0, f"a tap: the first = 4 and it sounds ({e.ons[n0:]})")
    n0 = len(e.ons); shift_pad(16 + 6)
    check(first() == 6 and len(e.ons) == n0 and mode() == 0, f"Shift + sample 6: the first = 6 without a note ({e.ons[n0:]})")
    shift_pad(16 + 6); f = X.frame(e)
    check(mode() & 1 and f[16 + 7] == SS.COL_RSEL and f[16 + 6] == SS.COL_R, f"Shift + the first: choosing the second: 7 blinks cyan ({f[23]:#x}), the first violet ({f[22]:#x})")
    n0 = len(e.ons); e.call(PRESS, MGR, 16 + 9, 100, maxins=8_000_000); on1 = len(e.ons); e.call(RELEASE, MGR, 16 + 9, maxins=8_000_000)
    check(K() == 3 and first() == 6 and on1 == n0 + 1 and len(e.ons) == n0 + 2, f"a tap on 9: the second (K {K()}), it sounds and stops ({e.ons[n0:]})")
    n0 = len(e.ons); shift_pad(16 + 10)
    check(K() == 4 and len(e.ons) == n0 and mode() & 1, f"Shift + 10: the second without a note (K {K()})")
    shift_pad(16 + 10)
    check(mode() == 0, f"Shift + the second: back to the first (mode {mode()})")
    dw.clear(); tick(1)
    check(lastk() == 4, f"the new K at the next tick ({lastk()})")
    e.uc.mem_write(e.r0(e.vl["c_vvaddr"], 0, 19), bytes([60])); f = X.frame(e)            # WAVE 60
    check(f[16 + 10] == SS.COL_R and f[16 + 6] == SP.COL_SEL, f"choosing the first, the width up: the second violet ({f[26]:#x}), the first cyan ({f[22]:#x})")
    e.shift(True); f = X.frame(e); e.shift(False)
    check(f[16 + 6] == SS.COL_SH, f"with Shift the first yellow ({f[22]:#x})")
    e.pad(16 + 2); f = X.frame(e)
    check(first() == 2 and K() == 4 and f[16 + 6] == SS.COL_R, f"the first changed to 2: the distance kept, the second 6 violet ({f[22]:#x})")
    shift_pad(16 + 2); m1 = mode(); e.btn(2); tick(1)
    check(m1 & 1 and mode() == 0, f"the picker off the screen: back to the first ({m1} -> {mode()})")
    # the patch
    e.call(ml["c_mpgather"], 0, maxins=4_000_000); e.call(sl["c_ssgath"], 0, maxins=8_000_000)
    buf = bytes(e.uc.mem_read(PK.BUF + SS.POFS, 3))
    check(buf == bytes([SS.PTAG, 4, (4 + 0x5A + SS.PTAG) & 0xFF]), f"gather: padding + 121 = {buf.hex()}")
    rec = bytearray(b"\xFF" * 4096)
    def mpr(uc, a, s, d):
        off, dst, n = uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R3)
        uc.mem_write(dst, bytes(rec[off:off + n])); uc.reg_write(UC_ARM_REG_R0, 0); uc.reg_write(UC_ARM_REG_R1, n)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    hk = e.uc.hook_add(UC_HOOK_CODE, mpr, begin=ml["c_mpr"], end=ml["c_mpr"])
    o = 3 * 512 + MP.OFF + SS.POFS
    rec[o:o + 3] = bytes([SS.PTAG, 9, (9 + 0x5A + SS.PTAG) & 0xFF])
    e.uc.reg_write(UC_ARM_REG_R5, 3); e.call(sl["c_ssappl"], 0, maxins=12_000_000); k9 = K()
    rec[o:o + 3] = b"\xFF\xFF\xFF"
    e.uc.reg_write(UC_ARM_REG_R5, 3); e.call(sl["c_ssappl"], 0, maxins=12_000_000); k1 = K()
    e.uc.hook_del(hk)
    check(k9 == 9 and k1 == 1, f"apply: K from the patch ({k9}), a patch without it = 1 ({k1})")
    print(f"{man['marker']} SMST ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
