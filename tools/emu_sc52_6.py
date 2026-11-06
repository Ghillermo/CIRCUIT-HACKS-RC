"""SC52.6 ARM tests (the controller and the real LED task):
  * rowswap: pad 1 = the assigned knobs (page 4), Shift + pad 1 = the non-sequenceable page, pad 4 = VCA / VCF; the LEDs of pads 1 / 4 exchanged;
  * psave.use_dupsave: Duplicate + an empty slot = mpatch's c_mpsave(track, slot) at once; Duplicate + a slot in use = A (no save);
  * the bipolar knobs: OSC 1's K1 (TUNE) left of its centre = the left mark 0x82.. in the brightness byte, right = plain, at the centre dim (CMIN);
    K5 of OSC 2 (FM): 64 dim in the track's colour, 80 the track's colour, 48 the left mark, 120 violet 0x49; persist19's converter hook turns the
    mark into the lighter shade (0x09 -> 0x13) and the brightness;
  * fm8ui.WTCOL: an engine code 8 slot = sand 0x6D / 0x69;
  * wtui.use_wtdef: Clear + pad 7 = the frame K3 points at back to the base table's frame.

    python tools/emu_sc52_6.py SC52.6.bin manifest.json
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402
import emu_lazysave as T  # noqa: E402
import vcf21 as VV  # noqa: E402
import persist19 as P19  # noqa: E402
import wtui as W  # noqa: E402

V = T4.V
MGR = X.MGR
CLEAR, DUP = 23, 24


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    R = man["report"]
    lab = lambda m, k: int(R[m]["labels"][k], 16)
    e = X.EP(img, man)
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05]))
    e.btn(2); e.btn(8)
    pg = lambda: e.r0(e.vl["c_vpage"], 0)
    e.pad(0); p1 = pg(); e.pad(3); p4 = pg()
    e.shift(True); e.pad(0); e.shift(False); ps1 = pg()
    check(p1 == 3 and p4 == 0 and ps1 == VV.NS_PAGE, f"pad 1 = page 4 ({p1}), pad 4 = VCA / VCF ({p4}), Shift + pad 1 = the non-sequenceable page ({ps1})")
    e.pad(3); f = X.frame(e)
    check(f[3] & 0xFF == VV.COL_PAGE[0][0] and f[0] & 0xFF != VV.COL_PAGE[0][0], f"VCA / VCF on: its bright colour on pad 4 ({f[3]:#x}), pad 1 another ({f[0]:#x})")
    # Duplicate + an empty slot
    saves = []
    def sv(uc, a, s, d): saves.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1))); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    hk = e.uc.hook_add(UC_HOOK_CODE, sv, begin=lab("mpatch", "c_mpsave"), end=lab("mpatch", "c_mpsave"))
    c = e.r0(lab("mpatch", "c_mpc"))
    e.uc.mem_write(c + 4, struct.pack("<H", 0x0001)); e.uc.mem_write(c + 7, bytes([e.r8(c + 3)]))     # slot 0 in use, the rest empty
    e.call(0x08033320, MGR, DUP, maxins=8_000_000); e.pad(8 + 5); e.call(0x0803381A, MGR, DUP, maxins=8_000_000)
    s1 = list(saves); saves.clear()
    e.call(0x08033320, MGR, DUP, maxins=8_000_000); e.pad(8); e.call(0x0803381A, MGR, DUP, maxins=8_000_000)
    check(s1 == [(0, 5)] and not saves, f"Duplicate + empty slot 6: saved there ({s1}); Duplicate + slot 1 in use: no save ({saves})")
    e.uc.hook_del(hk)
    # the bipolar knobs: OSC 1's page (pad 2), K1 = TUNE
    e.pad(1)
    a17 = e.r0(e.vl["c_vvaddr"], 0, 17)
    leds = {}
    for v in (-20, 0, 20):
        e.uc.mem_write(a17, bytes([v & 0xFF])); f = X.frame(e); leds[v] = f[60]
    hb = {v: x >> 8 for v, x in leds.items()}
    check(hb[-20] >= 0x82 and hb[0] == VV.CMIN + 2 and hb[20] == 42 and all(x & 0xFF == VV.COL_TRACK[0] for x in leds.values()),
          f"TUNE -20 / 0 / 20: {[hex(x) for x in leds.values()]} (left mark, dim centre, plain)")
    e.pad(27); e.pad(2)                                                    # two oscillators, OSC 2's page: K5 = FM
    a33 = e.r0(e.vl["c_vvaddr"], 0, 33)
    fm = {}
    for v in (64, 80, 48, 120):
        e.uc.mem_write(a33, bytes([v])); f = X.frame(e); fm[v] = f[64]
    ok = (fm[64] & 0xFF == VV.COL_TRACK[0] and fm[64] >> 8 == VV.CMIN + 2 and fm[80] & 0xFF == VV.COL_TRACK[0] and fm[80] >> 8 == 66
          and fm[48] >> 8 >= 0x82 and fm[120] & 0xFF == VV.FM_VIOLET)
    check(ok, f"K5 FM 64 / 80 / 48 / 120: {[hex(x) for x in fm.values()]}")
    # the converter hook: the mark -> the lighter shade and the brightness
    hook = lab("persist19", "c_ledhook")
    def conv(hw):
        e.uc.mem_write(0x2006F100, struct.pack("<H", hw)); e.uc.reg_write(UC_ARM_REG_R6, 0x2006F100); e.call(hook, maxins=200_000)
        return e.uc.reg_read(UC_ARM_REG_R7), e.uc.reg_read(UC_ARM_REG_R4)
    r_left, r_right, r_stock = conv((0x82 + 20) << 8 | 0x09), conv(42 << 8 | 0x09), conv(0x0009)
    check(r_left == (0x13, 40) and r_right == (0x09, 40) and r_stock == (0x09, 0xFF), f"converter: left {r_left}, right {r_right}, stock {r_stock}")
    # the wavetable's slot colour
    e.uc.mem_write(0x2004E480 + 3, bytes([8])); e.uc.reg_write(UC_ARM_REG_R3, 3); e.uc.reg_write(UC_ARM_REG_R4, 0)
    e.call(lab("fm8", "c_f8scol"), maxins=100_000); c1 = e.uc.reg_read(UC_ARM_REG_R2)
    e.uc.reg_write(UC_ARM_REG_R3, 3); e.uc.reg_write(UC_ARM_REG_R4, 4); e.call(lab("fm8", "c_f8scol"), maxins=100_000); c2 = e.uc.reg_read(UC_ARM_REG_R2)
    check((c1, c2) == (0x69, 0x6D), f"a wavetable patch's slot: sand dim / bright ({c1:#x}, {c2:#x})")
    # Clear + pad 7: the frame back
    wl = {k: int(v, 16) for k, v in R["wtui"]["labels"].items()}
    e.pad(26); e.pad(20); e.pad(26)                                        # the engine row: the wavetable
    tb = e.r0(wl["c_wttb"], 0)
    frames = lambda: list(e.uc.mem_read(tb + W.T_F, e.r8(tb + W.T_N)))
    e.uc.mem_write(tb + W.T_N, bytes([9])); e.uc.mem_write(tb + W.T_F, bytes(3 * 9 + k for k in range(9)))     # Nova table 3
    e.uc.mem_write(a17 + 2, bytes([63]))                                   # K3 (WAVE, code 19) in the middle: frame 4
    e.uc.mem_write(tb + W.T_F + 4, bytes([145]))                           # a sample there
    e.call(0x08033320, MGR, CLEAR, maxins=8_000_000); e.pad(6); e.call(0x0803381A, MGR, CLEAR, maxins=8_000_000)
    check(frames() == [27 + k for k in range(9)], f"Clear + pad 7: frame 4 back to Nova 3's ({frames()})")
    print(f"{man.get('marker', '?')} SC52.6 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
