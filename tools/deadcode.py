"""Unreachable code of ours in a build image (the user, 2026-11-13: flash room for the extra automation lanes, «Code-size pass first»).

    python tools/deadcode.py firmware/b5.57/circuittracks-4486-B5.57.bin firmware/b5.57/manifest.json [--all]

Our code: the hole (0x080101F0 .. hole.next) and everything from MOD_START (0x0805CDDC) to the image's end, minus the known data blocks (the packed
DSP programs, labelled tables are still scanned as code and show up as unreached: check the listing before removing anything).
Entry points: every branch / call from the stock's code into our ranges (a linear sweep of the stock code), every aligned word anywhere outside our
ranges whose value points into them (vtables, vectors, tables), and inside reached code every literal or movw + movt pair pointing into them.
The walk follows fall-through, conditional and unconditional branches, cbz / cbnz, bl / blx targets.  Reported: the unreached runs (not 0xFF
filler), with the nearest label before them, per module; a reached label is never reported.
"""
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
MOD_START = 0x0805CDDC
HOLE_LO = 0x080101F0


def main(a):
    img = Path(a[0]).read_bytes(); R = json.loads(Path(a[1]).read_text())["report"]
    end = BASE + len(img)
    rng = [(HOLE_LO, int(R["hole"]["next"], 16)), (MOD_START, end)]
    data = []
    dz = R.get("dspz", {})
    for k in ("core0", "core1"):
        if k in dz: lo = int(dz[k]["block"], 16); data.append((lo, lo + dz[k]["packed"]))
    ours = lambda x: any(lo <= x < hi for lo, hi in rng) and not any(lo <= x < hi for lo, hi in data)
    labels = {}
    for m, v in R.items():
        if isinstance(v, dict) and isinstance(v.get("labels"), dict):
            for n, ad in v["labels"].items():
                try: x = int(ad, 16)
                except (TypeError, ValueError): continue
                if ours(x): labels.setdefault(x, (m, n))
    la = sorted(labels)
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB | capstone.CS_MODE_MCLASS); md.detail = True
    rd = lambda x, n=4: img[x - BASE:x - BASE + n]
    entries = set()
    # 1. the stock code: every patched spot (the build differs from the stock image) decoded as a branch / call into ours
    stock = (Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    for lo, hi in ((BASE, HOLE_LO), (0x0801855A, MOD_START)):
        for o in range(lo - BASE, min(hi - BASE, len(stock)) - 1, 2):
            if img[o:o + 2] == stock[o:o + 2]: continue
            for st in (o - 2, o):
                ins = next(md.disasm(img[st:st + 4], BASE + st), None)
                if ins and ins.id in (CA.ARM_INS_BL, CA.ARM_INS_B, CA.ARM_INS_BLX, CA.ARM_INS_CBZ, CA.ARM_INS_CBNZ) and ins.operands                         and ins.operands[-1].type == CA.ARM_OP_IMM and ours(ins.operands[-1].imm):
                    entries.add(ins.operands[-1].imm)
    # 2. pointer-like words outside our ranges (and the vector table)
    for o in range(0, len(img) - 3, 4):
        x = BASE + o
        if ours(x): continue
        v = struct.unpack_from("<I", img, o)[0]
        if ours(v & ~1) and v & 1: entries.add(v & ~1)
    # 3. walk
    reached = set(); todo = list(entries); seen_ins = set()
    while todo:
        pc = todo.pop()
        if pc in seen_ins or not ours(pc): continue
        movw = {}
        while ours(pc) and pc not in seen_ins:
            code = rd(pc, 4)
            ins = next(md.disasm(code, pc), None)
            if ins is None: break
            seen_ins.add(pc)
            for k in range(ins.size): reached.add(pc + k)
            mn = ins.mnemonic; ops = ins.operands
            if ins.id == CA.ARM_INS_LDR and len(ops) == 2 and ops[1].type == CA.ARM_OP_MEM and ops[1].mem.base == CA.ARM_REG_PC:
                lit = ((pc + 4) & ~3) + ops[1].mem.disp
                if BASE <= lit < end - 3:
                    for k in range(4): reached.add(lit + k)
                    v = struct.unpack_from("<I", img, lit - BASE)[0]
                    if ours(v & ~1): todo.append(v & ~1)
            if ins.id == CA.ARM_INS_MOVW: movw[ops[0].reg] = ops[1].imm
            if ins.id == CA.ARM_INS_MOVT and ops[0].reg in movw:
                v = (ops[1].imm << 16) | movw[ops[0].reg]
                if ours(v & ~1): todo.append(v & ~1)
            if ins.id in (CA.ARM_INS_ADR,) or (ins.id == CA.ARM_INS_ADD and len(ops) == 3 and ops[1].type == CA.ARM_OP_REG and ops[1].reg == CA.ARM_REG_PC):
                pass
            if ins.id in (CA.ARM_INS_TBB, CA.ARM_INS_TBH):
                print(f"  (tbb/tbh at {pc:#x}: table not followed)")
            br = ins.id in (CA.ARM_INS_B, CA.ARM_INS_BL, CA.ARM_INS_BLX, CA.ARM_INS_CBZ, CA.ARM_INS_CBNZ)
            if br and ops and ops[-1].type == CA.ARM_OP_IMM:
                todo.append(ops[-1].imm)
            uncond = (ins.id == CA.ARM_INS_B and ins.cc in (CA.ARM_CC_AL, CA.ARM_CC_INVALID) and not ins.mnemonic.startswith(("b.", "beq", "bne")) and
                      mn in ("b", "b.w")) or (ins.id == CA.ARM_INS_BX) or (ins.id == CA.ARM_INS_POP and any(o.type == CA.ARM_OP_REG and o.reg == CA.ARM_REG_PC for o in ops)) \
                or (ins.id == CA.ARM_INS_LDR and ops and ops[0].type == CA.ARM_OP_REG and ops[0].reg == CA.ARM_REG_PC) \
                or (ins.id == CA.ARM_INS_MOV and ops and ops[0].type == CA.ARM_OP_REG and ops[0].reg == CA.ARM_REG_PC)
            if ins.id == CA.ARM_INS_POP and mn == "pop.w" and any(o.reg == CA.ARM_REG_PC for o in ops): uncond = True
            if ins.id == CA.ARM_INS_LDM and any(o.type == CA.ARM_OP_REG and o.reg == CA.ARM_REG_PC for o in ops): uncond = True
            if uncond: break
            pc += ins.size
    # 4. unreached runs
    runs = []; cur = None
    for lo, hi in rng:
        for x in range(lo, hi, 2):
            dead = ours(x) and x not in reached and rd(x, 2) != b"\xff\xff"
            if dead and cur is None: cur = [x, x + 2]
            elif dead: cur[1] = x + 2
            elif cur is not None: runs.append(tuple(cur)); cur = None
        if cur is not None: runs.append(tuple(cur)); cur = None
    per = collections.Counter(); out = []
    for lo, hi in runs:
        i = bisect.bisect_right(la, lo) - 1
        m, n = labels[la[i]] if i >= 0 else ("?", "?")
        off = lo - la[i] if i >= 0 else 0
        per[m] += hi - lo; out.append((hi - lo, lo, m, n, off))
    print(f"entries {len(entries)}, reached {len(reached)} B, unreached runs {len(runs)}, {sum(h - l for l, h in runs)} B")
    for m, n in per.most_common(60): print(f"  {m:12s} {n:6d} B")
    if "--all" in a:
        for sz, lo, m, n, off in sorted(out, key=lambda x: -x[0])[:150]: print(f"{sz:6d} B at {lo:#x}  {m}.{n}+{off:#x}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
