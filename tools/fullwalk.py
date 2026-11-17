"""Full reachability walk of a whole image, stock and ours (the user, 2026-11-13: «Do the full walk to check for unused code»).

    python tools/fullwalk.py BUILD.bin [manifest.json] [--all] [--min N]

Roots: the odd words of the stock's RAM (a live dump, and the RAM after its start-up emulated: its RAM vtables come from compressed
initialisers), even literals that point at code (bases of computed calls), every odd word in the image that points into it (the vector table, vtables, the .data initialisers, literal pools) that is not inside a
decoded instruction, iterated until no new root appears.  The walk follows fall-through, every branch (IT blocks: a conditional instruction also
falls through), cbz / cbnz, bl, tbb / tbh tables (bound from the cmp before them), literal loads and movw + movt pairs.  The same walk runs on the
stock image: unreached code is reported as «dead in the stock too», «dead since our patches» (reached in the stock, not in the build) and «ours».
Only code-like runs are listed (they decode cleanly and hold a push / pop / bx lr); data (tables, strings, packed DSP programs) is left out.
A run listed here can still be entered through a computed jump (a register branch whose target was built by arithmetic): check each by hand."""
from __future__ import annotations
import bisect
import collections
import json
import struct
import sys
from pathlib import Path
import capstone
from capstone import arm as CA

BASE = 0x08010000
STOCK_END = 0x0805CDDC
HOLE_LO = 0x080101F0
PC = CA.ARM_REG_PC
BR = (CA.ARM_INS_B, CA.ARM_INS_BL, CA.ARM_INS_CBZ, CA.ARM_INS_CBNZ)


RAMDUMP = Path(__file__).resolve().parents[1] / "ctre/Firmware-Analysis/ram_dump_firmware_0x08037988.bin"


def init_ram():
    """the stock's RAM right after its own start-up (data init emulated from the reset handler, peripheral reads = all ones): the RAM vtables come
    from compressed initialisers that a scan of the image cannot read"""
    try:
        from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS, UC_HOOK_MEM_READ, UcError
        from unicorn.arm_const import UC_ARM_REG_SP
    except ImportError:
        return b""
    root = Path(__file__).resolve().parents[1]
    st = (root / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    fl = bytearray((root / "ctre/Firmware-Analysis/dumpCT_flash_0x08000000.bin").read_bytes()); fl[0x10000:0x10000 + len(st)] = st
    uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)
    uc.mem_map(0x08000000, 0x80000); uc.mem_write(0x08000000, bytes(fl))
    for lo, n in ((0x20000000, 0x50000), (0x40000000, 0x20000000), (0xE0000000, 0x100000), (0, 0x100000)): uc.mem_map(lo, n)
    uc.hook_add(UC_HOOK_MEM_READ, lambda u, acc, a, size, v, d: u.mem_write(a, bytes([255]) * size), begin=0x40000000, end=0x5FFFFFFF)
    uc.reg_write(UC_ARM_REG_SP, 0x20050000)
    try: uc.emu_start(0x0805C1A0 | 1, 0x0805C1A8, count=50_000_000)       # FPU on, then the C start-up (data init, into main)
    except UcError: pass
    return bytes(uc.mem_read(0x20000000, 0x50000))


def ram_roots(end):
    """odd words of the stock's RAM pointing into flash: a live dump of the running stock (task entries, objects, saved return addresses) and the
    RAM right after start-up (the vtables of the compressed initialisers)"""
    out = set()
    for r in ((RAMDUMP.read_bytes() if RAMDUMP.exists() else b""), init_ram()):
        out |= {v - 1 for v in struct.unpack_from(f"<{len(r) // 4}I", r) if v & 1 and BASE <= v - 1 < end}
    return out


def walk(img, data=(), stock=None):
    end = BASE + len(img)
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB | capstone.CS_MODE_MCLASS); md.detail = True
    cache = {}

    def dec(a):
        if a not in cache:
            o = a - BASE
            cache[a] = next(md.disasm(img[o:o + 4], a), None) if 0 <= o < len(img) - 1 else None
        return cache[a]

    isdata = lambda x: any(lo <= x < hi for lo, hi in data)
    covered = bytearray(len(img)); ins_at = set(); warn = []
    roots = set()

    is_pc0 = lambda o: o.type == CA.ARM_OP_REG and o.reg == PC

    def cover(a, n, k=1):
        for i in range(n):
            if 0 <= a - BASE + i < len(img): covered[a - BASE + i] |= k

    def scan_ptrs():
        new = set()
        for o in range(0, len(img) - 3, 4):
            if covered[o] & 1 or covered[o + 2] & 1 or isdata(BASE + o): continue
            v = struct.unpack_from("<I", img, o)[0]
            if stock is not None and BASE + o < STOCK_END and v - 1 >= STOCK_END and img[o:o + 4] == stock[o:o + 4]:
                continue                                       # a word left as in the stock cannot point into our code (a stock data word)
            if v & 1 and BASE <= v - 1 < end - 1 and v - 1 not in roots and not isdata(v - 1):
                new.add(v - 1)
        return new

    todo = sorted(r for r in ram_roots(min(end, STOCK_END)) if not isdata(r)); roots |= set(todo)
    while True:
        new = scan_ptrs(); roots |= new; todo += list(new)
        if not todo: break
        while todo:
            pc = todo.pop(); state = {}; itn = 0
            if isinstance(pc, tuple): pc, state = pc
            while BASE <= pc < end and pc not in ins_at and not isdata(pc):
                ins = dec(pc)
                if ins is None: warn.append(("undecodable", pc)); break
                ins_at.add(pc); cover(pc, ins.size, 1)
                ops = ins.operands; cond = itn > 0
                if itn: itn -= 1
                iid = ins.id
                if iid == CA.ARM_INS_IT:
                    itn = len(ins.mnemonic) - 1
                elif iid == CA.ARM_INS_CMP and len(ops) == 2 and ops[0].type == CA.ARM_OP_REG and ops[1].type == CA.ARM_OP_IMM:
                    state["cmp"] = (ops[0].reg, ops[1].imm)
                elif iid == CA.ARM_INS_LDR and len(ops) == 2 and ops[1].type == CA.ARM_OP_MEM and ops[1].mem.base == PC:
                    lit = ((pc + 4) & ~3) + ops[1].mem.disp
                    if BASE <= lit < end - 3:
                        cover(lit, 4, 2)
                        v = struct.unpack_from("<I", img, lit - BASE)[0]
                        if v & 1 and BASE <= v - 1 < end: todo.append(v - 1)
                        elif BASE <= v < end and not isdata(v) and dec(v) is not None: todo.append(v)   # a base for computed calls (c_conv0 + 16 d + 1)
                elif iid == CA.ARM_INS_MOVW and ops[0].type == CA.ARM_OP_REG:
                    state[("w", ops[0].reg)] = ops[1].imm
                elif iid == CA.ARM_INS_MOVT and ("w", ops[0].reg) in state:
                    v = ops[1].imm << 16 | state[("w", ops[0].reg)]
                    if v & 1 and BASE <= v - 1 < end: todo.append(v - 1)
                elif ins.mnemonic.split(".")[0] in ("adr", "add", "addw", "sub", "subw") and ops and ops[0].type == CA.ARM_OP_REG                         and not is_pc0(ops[0]):
                    # a pc-relative address (adr / addw rd, pc, #imm): an odd one is a Thumb function pointer (the storage task passes
                    # 0x08022E09 as a callback this way: 2026-11-14, these were reported «dead» before)
                    imm = None
                    if ins.mnemonic.startswith("adr") and len(ops) == 2 and ops[1].type == CA.ARM_OP_IMM: imm = ops[1].imm
                    elif len(ops) == 3 and is_pc0(ops[1]) and ops[2].type == CA.ARM_OP_IMM:
                        imm = -ops[2].imm if ins.mnemonic.startswith("sub") else ops[2].imm
                    if imm is not None:
                        v = ((pc + 4) & ~3) + imm
                        if v & 1 and BASE <= v - 1 < end and not isdata(v - 1): todo.append(v - 1)
                if iid in (CA.ARM_INS_TBB, CA.ARM_INS_TBH):
                    t0 = pc + 4; w = 1 if iid == CA.ARM_INS_TBB else 2
                    reg = ops[0].mem.index if ops and ops[0].type == CA.ARM_OP_MEM else None
                    n = state["cmp"][1] + 1 if "cmp" in state and state["cmp"][0] == reg else None
                    rd_e = lambda k: img[t0 - BASE + k] if w == 1 else struct.unpack_from("<H", img, t0 - BASE + 2 * k)[0]
                    if n is None:                     # no bound seen (a hook replaced the cmp): the table ends where its first target starts
                        warn.append(("tb bound guessed", pc)); n = 0; lim = 1 << 30
                        while n < 256 and t0 + n * w < lim:
                            tgt = t0 + 2 * rd_e(n)
                            if tgt < t0 + (n + 1) * w or dec(tgt) is None: break
                            lim = min(lim, tgt); n += 1
                    for k in range(n): todo.append((t0 + 2 * rd_e(k), {}))
                    cover(t0, n * w, 2)
                    break
                tgt = ops[-1].imm if iid in BR and ops and ops[-1].type == CA.ARM_OP_IMM else None
                if tgt is not None: todo.append((tgt, dict(state) if iid != CA.ARM_INS_BL else {}))
                is_pc = lambda o: o.type == CA.ARM_OP_REG and o.reg == PC
                stop = (iid == CA.ARM_INS_B and ins.cc in (CA.ARM_CC_AL, CA.ARM_CC_INVALID)) or iid == CA.ARM_INS_BX \
                    or (iid in (CA.ARM_INS_POP, CA.ARM_INS_LDM) and any(is_pc(o) for o in ops)) \
                    or (iid in (CA.ARM_INS_LDR, CA.ARM_INS_MOV) and ops and is_pc(ops[0])) \
                    or (iid == CA.ARM_INS_ADD and ops and is_pc(ops[0]))
                if iid == CA.ARM_INS_BLX and ops and ops[0].type == CA.ARM_OP_REG: stop = False
                if iid in (CA.ARM_INS_ADD, CA.ARM_INS_MOV) and ops and is_pc(ops[0]): warn.append(("computed pc", pc))
                if stop and not cond: break
                pc += ins.size
    return covered, ins_at, warn, dec


def codelike(img, lo, hi, dec):
    """the run decodes linearly with no gap and holds a function-like instruction"""
    a = lo; good = 0; fn = False; n = 0
    while a < hi:
        ins = dec(a)
        if ins is None: return False
        if img[a - BASE:a - BASE + 2] in (b"\x00\x00", b"\xff\xff"): a += 2; continue
        n += 1
        if ins.id == CA.ARM_INS_PUSH or (ins.id == CA.ARM_INS_POP) or (ins.id == CA.ARM_INS_BX and "lr" in ins.op_str) or ins.id == CA.ARM_INS_BL:
            fn = True
        a += ins.size
    return fn and n >= 3


def runs_of(img, covered, lo, hi):
    out = []; cur = None
    for x in range(lo, hi, 2):
        o = x - BASE
        dead = not covered[o] and img[o:o + 2] != b"\xff\xff"
        if dead and cur is None: cur = [x, x + 2]
        elif dead: cur[1] = x + 2
        elif cur is not None: out.append(tuple(cur)); cur = None
    if cur: out.append(tuple(cur))
    return out


def main(a):
    img = Path(a[0]).read_bytes()
    root = Path(__file__).resolve().parents[1]
    stock = (root / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    mn = int(a[a.index("--min") + 1]) if "--min" in a else 16
    R = json.loads(Path(a[1]).read_text())["report"] if len(a) > 1 and a[1].endswith(".json") else {}
    data = []
    dz = R.get("dspz", {})
    for k in ("core0", "core1"):
        if k in dz: lo = int(dz[k]["block"], 16); data.append((lo, lo + dz[k]["packed"]))
    hole_hi = int(R["hole"]["next"], 16) if "hole" in R else HOLE_LO
    labels = {}
    for m, v in R.items():
        if isinstance(v, dict) and isinstance(v.get("labels"), dict):
            for nm, ad in v["labels"].items():
                try: labels.setdefault(int(ad, 16), (m, nm))
                except (TypeError, ValueError): pass
    la = sorted(labels)

    cs, ins_s, ws, dec_s = walk(stock)
    cb, ins_b, wb, dec_b = walk(img, data, stock)
    print(f"stock: {len(ins_s)} instructions reached, {sum(1 for c in cs if c)} B covered; warnings {collections.Counter(k for k, _ in ws)}")
    print(f"build: {len(ins_b)} instructions reached, {sum(1 for c in cb if c)} B covered; warnings {collections.Counter(k for k, _ in wb)}")
    for k, p in wb:
        if k != "undecodable": print(f"  {k} at {p:#x}")

    ours = lambda x: HOLE_LO <= x < hole_hi or x >= STOCK_END
    cats = collections.defaultdict(list)
    for lo, hi in runs_of(img, cb, BASE, BASE + len(img)):
        if hi - lo < mn or any(dlo <= lo < dhi for dlo, dhi in data): continue
        if not codelike(img, lo, hi, dec_b): continue
        if ours(lo):
            i = bisect.bisect_right(la, lo) - 1
            tag = f"{labels[la[i]][0]}.{labels[la[i]][1]}+{lo - la[i]:#x}" if i >= 0 else "?"
            cats["ours"].append((hi - lo, lo, tag))
        else:
            same = img[lo - BASE:hi - BASE] == stock[lo - BASE:hi - BASE]
            in_stock = any(cs[x - BASE] for x in range(lo, hi, 2))
            k = "dead since our patches" if in_stock else "dead in the stock too"
            cats[k].append((hi - lo, lo, "" if same else "(bytes changed)"))
    for k in ("dead since our patches", "dead in the stock too", "ours"):
        v = sorted(cats[k], reverse=True)
        print(f"\n{k}: {len(v)} runs, {sum(n for n, *_ in v)} B")
        for n, lo, tag in v[:None if "--all" in a else 40]:
            print(f"  {n:6d} B at {lo:#x} {tag}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
