"""patchain.use_rangefix (Alpha 7.16 / RC4.21, S715D4): c_pcnext's next pattern with the current one outside the track's stock chain.  Called as
the advance calls it (the frame at SP: [sp] track, [sp + 2] the chain's last, [sp + 0x18] forced, [sp + 0x44] scene change; r8 the first, r9 the
current, fp the look-ahead) -> [sp + 1].  With the fix: current >= last or < first -> the first, else current + 1 (the stock's answer inside the
chain); without it (S715D3 and older) the case the device hit (Drum 4 on 7, chain 0..0) gives 8.

    python tools/emu_rangefix.py firmware/s715d4/circuittracks-4486-S715D4.bin firmware/s715d4/manifest.json [--old]
"""
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn.arm_const import UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R11, UC_ARM_REG_LR, UC_ARM_REG_SP
import emu_sc48_8 as S
from emu_sc05 import STOP

CASES = [  # (track, current, first, last, forced) -> fixed answer
    (7, 7, 0, 0, 0, 0), (7, 3, 2, 5, 0, 4), (7, 5, 2, 5, 0, 2), (7, 1, 2, 5, 0, 2), (0, 6, 2, 5, 0, 2), (4, 0, 0, 7, 0, 1),
    (4, 7, 0, 7, 0, 0), (2, 4, 4, 4, 0, 4), (2, 3, 1, 6, 1, 1)]


def main(a):
    img, man = Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text())
    old = "--old" in a
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    nx = int(man["report"]["patchain"]["labels"]["c_pcnext"], 16)
    e = S.ET(img, man)
    uc = e.uc
    SPV = 0x20047C00
    for fp in (0, 1):
        for t, cur, first, last, forced, want in CASES:
            fr = bytearray(0x50); fr[0] = t; fr[1] = 0xEE; fr[2] = last; fr[0x18] = forced
            uc.mem_write(SPV, bytes(fr))
            uc.reg_write(UC_ARM_REG_R8, first); uc.reg_write(UC_ARM_REG_R9, cur); uc.reg_write(UC_ARM_REG_R11, fp)
            uc.reg_write(UC_ARM_REG_SP, SPV); uc.reg_write(UC_ARM_REG_LR, STOP | 1)
            uc.emu_start(nx | 1, STOP, count=2_000_000)
            got = e.r8(SPV + 1)
            exp = (cur + 1 if cur != last else first) if (old and not forced) else (first if forced else want)
            check(got == exp, f"{'look-ahead' if fp else 'playing'}: track {t}, on {cur}, chain {first}..{last}{', forced' if forced else ''} -> {got} (want {exp})")
    del e; gc.collect()
    print(f"{man.get('marker')} RANGEFIX RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1:]) else 0)
