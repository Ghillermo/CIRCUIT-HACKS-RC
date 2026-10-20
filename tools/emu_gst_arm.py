"""SC44.7 ARM test (vcf21.use_grbip): Shift + K3 of the granular page (code 34) bipolar -64..63.

    python tools/emu_gst_arm.py NEW.bin NEW_manifest.json PREV.bin
  * the granular page's table: only the Shift + K3 entry changes (34, 0, 127, value LED -> 34, -64, 63, bipolar LED);
  * c_grknob (track 0, Shift + K3): turned far left stops at -64, far right at 63, and the value is code 34's (the one the DSP reads);
  * Shift + K4 (code 29) keeps 0..126.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc17_5 import EA  # noqa: E402

OLD = bytes([33, 0, 127, 2, 34, 0, 127, 2, 29, 0, 126, 2])
NEW = bytes([33, 0, 127, 2, 34, 0xC0, 63, 0, 29, 0, 126, 2])


def main(img, man, prev):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    check(prev.count(OLD) == 1 and img.count(NEW) == 1 and img.count(OLD) == 0, "the table: Shift + K3 (code 34) -64..63 with a bipolar LED, its neighbours as before")
    L = {k: int(v, 16) for k, v in man["report"]["vcf20"]["labels"].items()}
    e = EA(img)
    def val(code):
        e.call(L["c_vvaddr"], 0, code, maxins=200000); return struct.unpack("b", bytes([e.r8(e.uc.reg_read(UC_ARM_REG_R0))]))[0]
    seq = []
    for d in (-30, -30, -30, 50, 50, 50, -200):
        e.call(L["c_grknob"], 0, 10, d & 0xFFFFFFFF, maxins=8_000_000); seq.append(val(34))
    check(seq == [-30, -60, -64, -14, 36, 63, -64], f"c_grknob Shift + K3: {seq} (-64..63)")
    seq = []
    for d in (-10, 100, 100):
        e.call(L["c_grknob"], 0, 11, d & 0xFFFFFFFF, maxins=8_000_000); seq.append(val(29))
    check(seq[0] == 0 and seq[-1] == 126, f"c_grknob Shift + K4 (code 29, the stereo spread): {seq} (0..126)")
    del e; gc.collect()
    print("SC44.7 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text()), Path(a[2]).read_bytes()) else 0)
