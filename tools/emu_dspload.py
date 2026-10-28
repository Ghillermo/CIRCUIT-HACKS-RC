"""S484D (diagnostic): the two meters of tools/dspload.py, through the DSP service chain's head and the real LED task.  The DSP's reads
(0x08029344) are answered by the test: Y:$FFE (the interrupt's place), Y:$FFD (the next block's), the ring's words (the synth's samples).
  * margins 250 / 215 / 200 / 150 over a window: Save green / yellow / orange / red (the window's minimum);
  * Y:$FFE past Y:$FFD (the margin 900): Save white for 2 s, then the colour of the window again;
  * samples 0.1 / 0.4 / 0.7 / 0.95 / 1.0 of full scale (negative too): Duplicate off / green / yellow / orange / red.

    python tools/emu_dspload.py S484D.bin S484D_manifest.json
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_LR, UC_ARM_REG_PC
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import dspload as D  # noqa: E402


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    lab = {k: int(v, 16) for k, v in man["report"]["dspload"]["labels"].items()}
    e = T.EL(img)
    st = dict(isr=0x1100, blk=0x1100 + 250, smp=0)
    reads = []
    def rd(uc, a, s, d):
        ad = uc.reg_read(UC_ARM_REG_R1); reads.append(ad)
        v = st["isr"] if ad == D.Y_ISR else st["blk"] if ad == D.Y_BLK else st["smp"] if ad & 0x8000 and 0x1000 <= ad & 0x7FFF < 0x1400 else 0
        uc.reg_write(UC_ARM_REG_R0, (v & 0xFFFFFF) << 8); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, rd, begin=D.DSP_READ, end=D.DSP_READ)
    t = [200000]
    def tick(n, ms=D.SAMPLE_MS):
        for _ in range(n): t[0] += ms; e.at(t[0]); e.call(lab["c_dltick"], maxins=2_000_000)
    def window(margin, smp=0):
        st["blk"] = (st["isr"] + margin) & 0x3FF | 0x1000; st["smp"] = smp
        tick(D.WIN_MS // D.SAMPLE_MS + 2)
        f = X.frame(e); return f[D.LED_SAVE] & 0xFF, f[D.LED_DUP] & 0xFF
    tick(2)
    check(reads[:3] == [D.Y_ISR, D.Y_BLK, reads[2]] and 0x9000 <= reads[2] < 0x9400, f"a sample: Y:$FFE, then Y:$FFD, then a ring word ({[hex(x) for x in reads[:3]]})")
    window(250); got = [window(m)[0] for m in (250, 215, 200, 150)]
    check(got == [0x17, 0x2D, 0x2B, 0x53], f"Save by the window's least margin 250 / 215 / 200 / 150: {[hex(x) for x in got]}")
    window(250); st["blk"] = (st["isr"] + 900) & 0x3FF | 0x1000; tick(1); st["blk"] = (st["isr"] + 250) & 0x3FF | 0x1000
    w1 = window(250)[0]; tick((D.DRY_MS + 100) // D.SAMPLE_MS); w2 = X.frame(e)[D.LED_SAVE] & 0xFF
    check(w1 == D.COL_DRY and w2 == 0x17, f"the ring ran dry: Save white, 2 s later the window's green ({w1:#x}, {w2:#x})")
    full = 1 << 23
    pk = [window(250, int(full * x) if x < 1 else full - 1)[1] for x in (0.1, 0.4, 0.7, 0.95, 1.0)]
    pn = window(250, -full)[1]
    check(pk == [0x00, 0x17, 0x2D, 0x2B, 0x53] and pn == 0x53, f"Duplicate by the peak 0.1 / 0.4 / 0.7 / 0.95 / 1.0: {[hex(x) for x in pk]}, -1.0 {pn:#x}")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} DSPLOAD RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
