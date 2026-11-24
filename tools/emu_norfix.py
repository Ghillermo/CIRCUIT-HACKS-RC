"""(2026-11-24) NORFXD: rdiag's NOR commands (18 erase / 19 write / 20 read) on the stock image, the device methods replaced by a recorder.
    python tools/emu_norfix.py firmware/norfxd"""
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_SP
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc05, ctremote as CR, rdiag

READ, WRITE, ERASE = 0x08024130, 0x08024164, 0x080241B8


def main(d):
    img = next(Path(d).glob("*.bin")).read_bytes()
    lab = {k: int(v, 16) for k, v in json.loads((Path(d) / "manifest.json").read_text())["report"]["rdiag"]["labels"].items()}
    e = emu_sc05.E(img); uc = e.uc
    calls, sent = [], []
    nor = bytearray(b"\xA5" * 0x100)

    def hook(uc, a, s, _):
        r = lambda n: uc.reg_read(UC_ARM_REG_R0 + n)
        if a in (READ, WRITE, ERASE):
            dev, x, y, z = r(0), r(1), r(2), r(3)
            sp = uc.reg_read(UC_ARM_REG_SP)
            if a == READ: calls.append(("read", dev, x, z)); uc.mem_write(y, bytes(nor[:z]))
            if a == WRITE: calls.append(("write", dev, x, bytes(uc.mem_read(y, z)), struct.unpack("<I", uc.mem_read(sp, 4))[0]))
            if a == ERASE: calls.append(("erase", dev, x, y))
            uc.reg_write(UC_ARM_REG_R0, 0); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
        if a == rdiag.ROUTER:
            m = struct.unpack("<II", uc.mem_read(r(2), 8)); sent.append(bytes(uc.mem_read(m[0], m[1])))
            uc.reg_write(UC_ARM_REG_R0, 0); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
    uc.hook_add(UC_HOOK_CODE, hook)
    dev = struct.unpack("<I", uc.mem_read(struct.unpack("<I", uc.mem_read(rdiag.NOR_DEV, 4))[0], 4))[0]
    fails = 0

    def check(c, m):
        nonlocal fails
        print(("ok  :" if c else "FAIL:"), m); fails += not c

    def run(cmd, payload):
        msg = bytes(CR.build(cmd, 1, payload)); calls.clear(); sent.clear()
        uc.mem_write(0x20060000, msg); uc.mem_write(0x20060400, struct.pack("<II", 0x20060000, len(msg)))
        e.call(lab["c_rdin"], 0, 0x20060400, 0)
        p = list(sent[-1][6:-1]) if sent else []
        return CR.un32(p[:8]) if p else None, p
    st, _ = run(18, CR.nib32(0xD4000)); check(st == 0 and calls == [("erase", dev, 0xD4000, 0xD5000)], f"erase 0xD4000 -> 0xD5000 on the device {dev:#x}: {calls}")
    for a, why in ((0x94000, "below the FS"), (0xD4800, "not 4 KB aligned"), (0x2000000, "past the end"), (0x0, "the install copy")):
        st, _ = run(18, CR.nib32(a)); check(st == 0xFFFFFFFE and not calls, f"erase {a:#x} refused ({why})")
    data = bytes(range(64))
    st, _ = run(19, CR.nib32(0xD5FC0) + [64] + CR.nibbytes(data)); check(st == 0 and calls == [("write", dev, 0xD5FC0, data, 0)], "write 64 B at the end of a block, 5th argument 0")
    st, _ = run(19, CR.nib32(0xD5FC1) + [64] + CR.nibbytes(data)); check(st == 0xFFFFFFFE and not calls, "write crossing a 4 KB block refused")
    st, _ = run(19, CR.nib32(0x7F000) + [16] + CR.nibbytes(data[:16])); check(st == 0xFFFFFFFE and not calls, "write outside the FS refused")
    st, p = run(20, CR.nib32(0x94000) + [32]); check(st == 0 and calls == [("read", dev, 0x94000, 32)] and CR.unbytes(p[8:]) == bytes(nor[:32]), "read 32 B anywhere")
    st, p = run(1, []); check(st == rdiag.VERSION + 0x1000, "ping reports NOR (version + 0x1000)")
    print("NORFIX RESULT:", "ALL PASS" if not fails else f"{fails} FAIL")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1]) else 0)
