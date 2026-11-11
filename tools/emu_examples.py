"""The example patches of tools/make_examples.py on the emulated firmware: each .ctm put into a slot of a bank image (padding at 512 (n & 7) + 340,
the 8-operator FM record at 4096 + 512 (n & 7)), loaded into MIDI 1 by mpatch's c_mpload, saved again into another slot by c_mpsave; the blocks the
file sets must come back byte for byte (the engine and codes 1..34, the LFO shape, page 4's and the non-sequenceable page's destinations, the voice
mode, the one-oscillator / two-oscillator blocks, the FM block and the FM record), and the codes must be the file's in the engine's RAM.

    python tools/emu_examples.py SC55.6.bin SC55.6_manifest.json [DIR]
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_PC, UC_ARM_REG_SP, UC_ARM_REG_LR
from unicorn.arm_const import UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402,F401
import packio as PK  # noqa: E402
import make_examples as MK  # noqa: E402

BLOCKS = [("base", 0, 43), ("page 4", MK.P4_AT, 12), ("non-seq", MK.NS_AT, 12), ("FM block", MK.FM_AT, 21), ("voice mode", MK.VM_AT, 4),
          ("one osc", MK.SO_AT, 8), ("two osc", MK.OM_AT, 8)]


def main(img_p, man_p, d="docs/patches"):
    img, man = Path(img_p).read_bytes(), json.loads(Path(man_p).read_text())
    R = man["report"]
    ml = {k: int(v, 16) for k, v in R["mpatch"]["labels"].items()}
    vl = {k: int(v, 16) for k, v in R["vcf20"]["labels"].items()}
    files = sorted(Path(d).glob("*.ctm"))
    fails = []
    def check(c, m):
        print(("  ok   " if c else "  FAIL ") + m)
        if not c: fails.append(m)
    e = T.EL(img)
    banks = {}
    def body(uc, a, s, dd):
        r0, r1, r2, r3, r4 = (uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R4))
        b = banks.setdefault(r0, bytearray(b"\xFF" * 8192))
        if (r4 & ~1) == PK.READ: uc.mem_write(r2, bytes(b[r1:r1 + r3]))
        else: b[r1:r1 + r3] = uc.mem_read(r2, r3)
        sp = uc.reg_read(UC_ARM_REG_SP) + 32
        regs = struct.unpack("<5I", uc.mem_read(sp, 20))
        for rg, v in zip((UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7), regs[:4]): uc.reg_write(rg, v)
        uc.reg_write(UC_ARM_REG_R0, 0); uc.reg_write(UC_ARM_REG_R1, r3); uc.reg_write(UC_ARM_REG_SP, sp + 20); uc.reg_write(UC_ARM_REG_PC, regs[4])
    e.uc.hook_add(UC_HOOK_CODE, body, begin=ml["mp_io"] + 4, end=ml["mp_io"] + 4)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, dd: (uc.reg_write(UC_ARM_REG_R0, 8192), uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)),
                  begin=0x0803CB6A, end=0x0803CB6A)
    e.at(100000); e.btn(2); e.btn(8)
    r8 = lambda c: (e.call(vl["c_vvaddr"], 0, c, maxins=4_000_000), e.r8(e.uc.reg_read(UC_ARM_REG_R0)))[1]
    for f in files:
        data = f.read_bytes(); pad, rec = data[:MK.PADN], data[MK.PADN:]
        print(f.name)
        b = banks.setdefault(0, bytearray(b"\xFF" * 8192))
        b[340:340 + MK.PADN] = pad; b[4096:4096 + MK.RECN] = rec
        e.call(ml["c_mpload"], 0, 0, maxins=60_000_000)
        codes = [r8(c) for c in range(1, 35)]
        check(codes == list(pad[6:40]), "codes 1..34 in the engine's RAM" + ("" if codes == list(pad[6:40]) else f": {[(c + 1, x, y) for c, (x, y) in enumerate(zip(codes, pad[6:40])) if x != y]}"))
        e.call(ml["c_mpsave"], 0, 1, maxins=60_000_000)
        s = bytes(b[512 + 340:512 + 340 + MK.PADN]); sr = bytes(b[4096 + 512:4096 + 512 + MK.RECN])
        for nm, at, n in BLOCKS:
            if pad[at] == 0xFF: continue
            ok = s[at:at + n] == pad[at:at + n]
            check(ok, f"{nm} back after load + save" + ("" if ok else f": file {pad[at:at + n].hex()} saved {s[at:at + n].hex()}"))
        if rec[0] != 0xFF: check(sr[:4 + 216 + 2] == rec[:4 + 216 + 2], "the 8-operator FM record back")
        gc.collect()
    print("EXAMPLES RESULT:", "ALL PASS" if not fails else f"{len(fails)} FAIL")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))
