"""SC50.8 dspz: the DSP upload (0x08029260, modes 0 and 1) sends the same chunks, waits and selects with the packed blocks as SC50.7 with the plain ones.

    python tools/emu_dspz.py build/sc50.7/...bin build/sc50.8/...bin

The RTOS / delay calls of 0x08029260 return at once; 0x0803BA96 (the SPI send) is recorded with its bytes, 0x0803B9D8 / 0x080291B8 / 0x080291CA by name and r0.
Also: the ITCM below the window (0x0000..0x1FFF) and the RAM around the buffer are untouched; the blocks unpack (Python) to the SC50.7 ones.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn import UC_HOOK_CODE  # noqa: E402
from unicorn.arm_const import UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0, UC_ARM_REG_R1  # noqa: E402
from emu_sc05 import E  # noqa: E402
import dspz  # noqa: E402
from thumb import bl as bl_enc  # noqa: E402

UPLOAD = 0x08029260
RETURN_AT = (0x0803BADA, 0x08023438, 0x0801B394, 0x0803BAD6, 0x08029492)
ZERO_AT = (0x0801B13E,)                             # the DSP's ready line: 0 = ready (the stock waits while it is not 0)


def run(img, mode):
    e = E(img)
    e.uc.mem_write(0, bytes((i * 7 + 3) & 0xFF for i in range(0x4000)))
    e.uc.mem_write(dspz.STAGE - 0x200, b"\x5A" * 0x200)
    ev = []
    def h(uc, a, s, d):
        lr = uc.reg_read(UC_ARM_REG_LR)
        r0, r1 = uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1)
        def ret(v=None):
            if v is not None: uc.reg_write(UC_ARM_REG_R0, v)
            uc.reg_write(UC_ARM_REG_PC, lr | 1)
        if a == dspz.SPI: ev.append(("spi", bytes(uc.mem_read(r0, r1)))); ret()
        elif a == dspz.WAIT: ev.append(("wait",)); ret()
        elif a == dspz.SELECT: ev.append(("select", r0)); ret()
        elif a == dspz.END: ev.append(("end", r0)); ret()
        elif a in RETURN_AT:
            if a == 0x08029492: ev.append(("tail",))                    # (Alpha 7.38) the mode-0 tail (the tables after the programs): seen, not run
            ret()
        elif a in ZERO_AT: ret(0)
    e.uc.hook_add(UC_HOOK_CODE, h)
    e.call(UPLOAD, mode, maxins=200_000_000)
    itcm_low = bytes(e.uc.mem_read(0, 0x2000))
    below = bytes(e.uc.mem_read(dspz.STAGE - 0x200, 0x200))
    del e; gc.collect()
    return ev, itcm_low, below


def main(old_path, new_path):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  :" if c else "FAIL:"), m); fails += 0 if c else 1
    old, new = Path(old_path).read_bytes(), Path(new_path).read_bytes()
    man = json.loads((Path(new_path).parent / "manifest.json").read_text())["report"]["dspz"]
    oman = json.loads((Path(old_path).parent / "manifest.json").read_text())["report"] if (Path(old_path).parent / "manifest.json").exists() else {}
    oblk = oman.get("dspz", {})                                                        # (SC57.8) the old build's blocks may sit a few bytes away
    fm2 = "exp" in json.loads((Path(new_path).parent / "manifest.json").read_text())["report"].get("tabpack_info", {}).get("tables", [])
    c_dspz = int(man["labels"]["c_dspz"], 16)
    for s in dspz.SITES:
        rep = json.loads((Path(new_path).parent / "manifest.json").read_text())["report"]
        wraps = {int(rep[m]["labels"][k], 16) for m, k in (("tabpack", "c_tboot"), ("c1ms", "c_c1ms")) if m in rep}   # (SC51.5 / SC55.8) the heads in front of c_dspz
        check(any(new[s - dspz.BASE:s - dspz.BASE + 4] == bl_enc(s, t) for t in {c_dspz} | wraps), f"bl {s:#x} -> c_dspz (or a head in front of it)")
    for core in (0, 1):
        at = int(man[f"core{core}"]["block"], 16)
        check(new[at - dspz.BASE:at - dspz.BASE + 4] in (dspz.MAGIC, dspz.MAGIC2), f"core {core}: block packed at {at:#x} ({bytes(new[at - dspz.BASE:at - dspz.BASE + 3]).decode()})")
        at_o = int(oblk[f"core{core}"]["block"], 16) if f"core{core}" in oblk else at
        check(dspz.block_at(new, at) == dspz.block_at(old, at_o), f"core {core}: unpacks to SC50.7's block ({man[f'core{core}']['raw']} -> {man[f'core{core}']['packed']} B)")
    pattern = bytes((i * 7 + 3) & 0xFF for i in range(0x2000))
    for mode in (0, 1):
        eo, itcm_o, _ = run(old, mode)
        en, itcm, below = run(new, mode)
        spi_o = [x for x in eo if x[0] == "spi"]
        check(len(eo) > 10 and en == eo, f"mode {mode}: {len(en)} calls, {len(spi_o)} chunks, {sum(len(x[1]) for x in spi_o)} B: the same as SC50.7")
        if "tabpack" in json.loads((Path(new_path).parent / "manifest.json").read_text())["report"]:   # (SC55.8) tabpack's tables in 0x18A4..: as the old build
            if fm2:                                                                   # (SC57.8) tabpack.use_fm2's curves live in ITCM 0x1048..0x18A3: not the old build's
                import tabpack as TP
                lo, hi = TP.ITCM2
                itcm, itcm_o = itcm[:lo] + itcm[hi:], itcm_o[:lo] + itcm_o[hi:]
            check(itcm == itcm_o, f"mode {mode}: ITCM 0x0000-0x1FFF as the old build's" + (" (tabpack's second curve area left out)" if fm2 else ""))
        else:
            check(itcm == pattern, f"mode {mode}: ITCM 0x0000-0x1FFF untouched")
        check(below == b"\x5A" * 0x200, f"mode {mode}: RAM below the buffer untouched")
    print("RESULT:", "ALL PASS" if not fails else f"{fails} FAIL")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(*sys.argv[1:3]) else 0)
