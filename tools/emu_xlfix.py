"""The extra lanes' fixes of the 2026-11-14 bug hunt (xlanes.use_svfix / use_memfix / use_editcache / use_fillfix / use_atomic), on the RAM dump
with emu_sc35's card / DSP model.  Every case fails on Beta 5.62 and passes with the option:
  * XL-1 (use_svfix): a save as the device makes it (r5 = the slot 2, [session + 0x60] p0 = the pack 1) writes the tail in that project's file
    only, the storage task's current pack unchanged; a project of pack 0 (internal, read-only for the mod): no write at all, the save flag gone;
  * XL-3 (use_memfix): Clear + K3 to the left with the edited block cached in the ITCM but its bitmap bit clear (stale content): nothing erased,
    the block not marked changed (and no unaligned memset);
  * XL-4 (use_editcache): the transport stopped: the LED task's work caches the edited pattern (not the last one played); Record + step on it
    (recinst) lands in its slot and goes back to the DSP when another pattern is edited; playing: the playing pattern stays wanted;
  * XL-5 (use_fillfix): while a block fills it is not cached (cached = 0 at the 2nd DSP copy); a failed copy = still not cached, filled the next
    frame; a failed copy back = the block changed again, written back the next frame (not overwritten by the next block's fill);
  * XL-6 (use_atomic): a save that fails half way over a file that had lanes leaves bitmap 0 in the header (the next load: no lanes, not stale
    blocks); a code above 34 in a block is never played.
  * all along: no unaligned memset / word copy of 8 bytes or more (emu_xlanes.align_guard).

    python tools/emu_xlfix.py BUILD.bin manifest.json
"""
from __future__ import annotations
import gc, json, random, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_LR, UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R5
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc35 import E35  # noqa: E402
from emu_xlanes import align_guard  # noqa: E402
import packio as PK  # noqa: E402
import xlanes as XL  # noqa: E402

SES = XL.SESSION_OBJ
IT = lambda slot: (XL.KIND_SES, slot, 0xFF)                    # the loaded pack's items (e.cur = 1)


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    import emu_arp as EAm, vcf21 as V
    e = E35(img, man); R = man["report"]
    unaligned = align_guard(e)
    xl = {k: int(v, 16) for k, v in R["xlanes"]["labels"].items()}
    pv = {k: int(v, 16) for k, v in R["xlanes"]["prev"].items()}
    vl = {k: int(v, 16) for k, v in R["vcf20"]["labels"].items()}
    pk = {k: int(v, 16) for k, v in R["packio"]["labels"].items()}
    back = lambda uc, a, s_, d: uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    for k in ("load", "new", "play"): e.uc.hook_add(UC_HOOK_CODE, back, begin=pv[k], end=pv[k])
    # the DSP copies: count them, fail chosen ones (r0 = 1 back), note the cached bytes at a chosen call
    cp = dict(n=0, fail=set(), at=None, seen=None, n2=0, fail2=set(), via=False)
    def h_copy(uc, a, s_, d):                                      # c_copy (= c_copy2(src, WIN, n): it runs into c_copy2)
        cp["n"] += 1
        if cp["n"] == cp["at"]: cp["seen"] = bytes(uc.mem_read(XL.XLR + XL.O_CM, 2))
        if cp["n"] in cp["fail"]: uc.reg_write(UC_ARM_REG_R0, 1); back(uc, a, s_, d)
        else: cp["via"] = True
    def h_copy2(uc, a, s_, d):                                     # direct calls of c_copy2 only
        if cp["via"]: cp["via"] = False; return
        cp["n2"] += 1
        if cp["n2"] in cp["fail2"]: uc.reg_write(UC_ARM_REG_R0, 1); back(uc, a, s_, d)
    e.uc.hook_add(UC_HOOK_CODE, h_copy, begin=pk["c_copy"] & ~1, end=pk["c_copy"] & ~1)
    e.uc.hook_add(UC_HOOK_CODE, h_copy2, begin=pk["c_copy2"] & ~1, end=pk["c_copy2"] & ~1)
    def reset_cp(): cp.update(n=0, fail=set(), at=None, seen=None, n2=0, fail2=set(), via=False)
    st = lambda: bytes(e.uc.mem_read(XL.XLR, XL.ST_LEN))
    bmap = lambda: struct.unpack_from("<H", st(), XL.O_MAP)[0]
    def setmap(v): e.call(xl["c_xlst"], maxins=10000); e.uc.mem_write(XL.XLR + XL.O_MAP, struct.pack("<H", v))
    meta = lambda: bytes(e.uc.mem_read(XL.XLR + XL.O_CM, 8))
    def setmeta(cached=None, changed=None, wanted=None, m=0):
        for off, v in ((0, cached), (2, changed), (4, wanted)):
            if v is not None: e.uc.mem_write(XL.XLR + XL.O_CM + off + m, bytes([v]))
    work = lambda: e.call(xl["c_xlwork"], maxins=200_000_000)
    fixed = "xs_fix" in xl
    def save(slot, pack, dev=False):
        """dev: as the stock's save 0x0802FDF8 at its bl 0x0802FE5E (r5 = the slot, [session + 0x60] p0 = the pack); else, on a build without
        use_svfix, the swapped way it expects (so the other cases test their own fix)"""
        if not (dev or fixed): slot, pack = pack, slot
        e.set_p0(e.r32(SES + 0x60), pack); e.uc.reg_write(UC_ARM_REG_R5, slot); e.call(xl["c_xlsv"], SES, maxins=2_000_000); work()
    hmap = lambda f: struct.unpack_from("<H", f, XL.SZ0 + 6)[0] if len(f) >= XL.SZ0 + 8 else -1
    def load(slot):
        e.call(PK.PARAM_GET, e.r32(XL.PROJ_OBJ + 0x20), 8, maxins=100000); e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0), bytes([slot]))
        e.call(xl["c_xlld"], maxins=2_000_000); work()
    rnd = random.Random(11)
    blockwords = lambda b: {XL.XB + b * XL.BLKW + i: rnd.randrange(0x10000) << 8 for i in range(XL.BLKW)}
    dspblock = lambda b: b"".join(struct.pack("<H", (e.ext.get(XL.XB + b * XL.BLKW + i, 0) >> 8) & 0xFFFF) for i in range(XL.BLKW))[:XL.BLK]
    itcm = lambda m=0: bytes(e.uc.mem_read(XL.IC0 + XL.ICS * m, XL.BLK))
    setp = lambda store, k, v: EAm.EA.setp(e, store, k, bytes([v]))
    edited = lambda m: e.r32(XL.PAT_OBJ + (2 + m) * XL.PAT_SZ + 0x24)

    # ================= XL-1: the slot and the pack
    e.cur = e.scur = 1
    plain = bytes(random.Random(5).randrange(256) for _ in range(XL.SZ0))
    e.sd[IT(2)] = plain
    w0 = blockwords(0); e.ext.clear(); e.ext.update(w0); setmap(1)
    n0 = len(e.api); save(2, 1, dev=True)
    f = e.sd.get(IT(2), b"")
    wr = {x[1] for x in e.api[n0:] if x[0] == "write"}
    check(len(f) == XL.SZ0 + XL.HDR + XL.DATA and f[:XL.SZ0] == plain and wr == {(XL.KIND_SES, 2, 1)} and sorted(e.sd) == [IT(2)] and e.scur == 1,
          f"XL-1: save of slot 2 in pack 1 (r5 = 2, p0 = 1): the tail in that file only, the current pack kept ({len(f)} B, {wr}, {sorted(e.sd)}, {e.scur})")
    e.ext.clear(); setmap(0); load(2)
    check(bmap() == 1 and all(e.ext.get(k, 0) == v for k, v in w0.items()), f"XL-1: the load of slot 2 finds them (bitmap {bmap():#x})")
    keys = set(e.sd); n0 = len(e.api); e.ext.update(blockwords(0)); setmap(1)
    save(2, 0, dev=True)
    wr = [x for x in e.api[n0:] if x[0] in ("write", "size", "del")]
    check(not wr and set(e.sd) == keys and not st()[XL.O_FL] & XL.F_SAVE,
          f"XL-1: a project of pack 0 (internal, read-only): nothing asked of the card, the save flag gone ({wr[:3]}, flags {st()[XL.O_FL]:#x})")

    # ================= XL-6: a save that fails half way; a damaged code
    e.ext.clear(); e.ext.update(blockwords(0)); setmap(1)
    e.sd[IT(2)] = plain; e.cur = e.scur = 1; save(2, 1)
    ok0 = hmap(e.sd[IT(2)]) == 1
    e.ext.update(blockwords(0)); e.ext.update(blockwords(1)); setmap(3)
    reset_cp(); cp["fail"] = {3}
    save(2, 1); reset_cp()
    f = e.sd[IT(2)]
    hb = hmap(f)
    check(ok0 and hb == 0 and e.lock == 0, f"XL-6: a save whose 3rd DSP copy fails over a file with lanes: the header's bitmap 0 ({hb:#x}), the lock given back")
    e.ext.clear(); setmap(0x55); load(2)
    check(bmap() == 0, f"XL-6: ... the next load: no lanes ({bmap():#x})")
    e.cur = e.scur = None
    # a block with code 0xFF in slot 0 and 19 in slot 1, step 5 holding values: c_xlpl plays only 19
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05]))     # the own engine on
    setp(XL.REC_ON, 0, 1)
    applied = []
    def h_ap(uc, a, s_, d):
        applied.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2))); back(uc, a, s_, d)
    e.uc.hook_add(UC_HOOK_CODE, h_ap, begin=xl["c_xlap"], end=xl["c_xlap"])
    P1 = XL.PLAYER0 + 2 * XL.PLAYER_SZ
    blk = bytearray([0xFF]) * XL.BLK; blk[:XL.NSLOT] = bytes(XL.NSLOT); blk[0] = 0xFF; blk[1] = 19
    for s_ in (0, 1): blk[XL.VOFF + 64 * s_ + 10] = 50
    e.uc.mem_write(XL.IC0, bytes(blk)); setmap(1 << 2); setmeta(cached=3, wanted=3, changed=0)
    pb = e.r32(XL.PAT_OBJ + 2 * XL.PAT_SZ + 4) + 2 * XL.PAT_N + 28 * 5 + 3; e.uc.mem_write(pb, bytes([e.r8(pb) & 0x7F]))
    e.call(xl["c_xlpl"], P1, 2, 5, 0, maxins=2_000_000)
    check([c for _m, c, _v in applied] == [19], f"XL-6: a code above {XL.MAXCODE} in a block is not played ({applied})")
    gc.collect()

    # ================= XL-3: Clear + K3 to the left, the edited block cached but its bit clear
    e.call(vl["c_vsetpage"], 0, 1, maxins=2_000_000)
    setp(edited(0), 0, 2)
    e.call(vl["c_vkc"], 0, 16 * 1 + 2, maxins=100000); k3 = e.uc.reg_read(UC_ARM_REG_R0)
    blk = bytearray([0x11]) * XL.BLK; blk[:XL.NSLOT] = bytes(XL.NSLOT); blk[0] = k3
    e.uc.mem_write(XL.IC0, bytes(blk)); setmap(0); setmeta(cached=3, wanted=3, changed=0)
    nu = len(unaligned)
    e.call(vl["c_vclrauto"], 0x2006F200, 2, 0, maxins=5_000_000)
    check(k3 == 19 and itcm() == bytes(blk) and meta()[2] == 0 and len(unaligned) == nu,
          f"XL-3: Clear + K3 (code {k3}), the block's bit clear: the stale ITCM block untouched, not changed ({meta().hex()}, unaligned {unaligned[nu:]})")

    # ================= XL-5: the fill, the copy back
    setp(XL.REC_ON, 0, 1)
    e.ext.clear(); w2 = blockwords(2); e.ext.update(w2); setmap(1 << 2); setmeta(cached=0, wanted=3, changed=0)
    reset_cp(); cp["at"] = 2; work()
    seen = cp["seen"]
    check(seen is not None and seen[0] == 0 and meta()[0] == 3 and itcm() == dspblock(2),
          f"XL-5: while block 2 fills it is not cached (cached {seen.hex() if seen else None} at the 2nd copy), then cached = 3 with the DSP's bytes")
    e.uc.mem_write(XL.IC0, bytes(XL.BLK)); setmeta(cached=0, wanted=3, changed=0)
    reset_cp(); cp["fail"] = {2}; work()
    m1 = meta()[0]
    reset_cp(); work()
    check(m1 == 0 and meta()[0] == 3 and itcm() == dspblock(2), f"XL-5: a failed copy: not cached ({m1}), filled the next frame ({meta()[0]})")
    e.uc.mem_write(XL.IC0 + XL.VOFF + 7, bytes([0x42])); setmeta(changed=1, wanted=5)
    want2 = itcm()
    reset_cp(); cp["fail2"] = {1}; work()
    ch = meta()[2]
    reset_cp(); work()
    check(ch == 1 and dspblock(2) == want2 and meta()[0] == 5, f"XL-5: a failed copy back: changed again ({ch}), written back the next frame, then block 4 cached ({meta().hex()})")
    gc.collect()

    # ================= XL-4: the transport stopped: the edited pattern cached
    setp(XL.REC_ON, 0, 0)
    e.ext.clear(); setmap(0); setmeta(cached=3, wanted=3, changed=0); setp(edited(0), 0, 4)
    e.call(PK.PARAM_GET, edited(1), 0, maxins=100000); p2 = e.r8(e.uc.reg_read(UC_ARM_REG_R0)) & 7
    work()
    check(meta()[0] == 5 and meta()[4] == 5 and meta()[5] == 9 + p2, f"XL-4: stopped: MIDI 1's edited pattern 5 (block 4) wanted and cached, MIDI 2's too ({meta().hex()})")
    rd = lambda fn, *a: (e.call(fn, *a, maxins=100000), e.uc.reg_read(UC_ARM_REG_R0))[1]
    e.uc.mem_write(rd(vl["c_vvaddr"], 0, 19), bytes([77]))
    e.call(int(R["recinst"]["labels"]["c_riinst"], 16), 0, 7, maxins=20_000_000)
    b4 = itcm(); s4 = b4[:XL.NSLOT].index(19) if 19 in b4[:XL.NSLOT] else -1
    vt = rd(vl["c_vtou"], 19, 77)
    check(s4 >= 0 and b4[XL.VOFF + 64 * s4 + 14] == vt and b4[XL.VOFF + 64 * s4 + 15] == vt and bmap() == 1 << 4,
          f"XL-4: Record + step 8 while stopped: code 19 in slot {s4} of block 4, both halves {vt}; its bit set ({bmap():#x})")
    setp(edited(0), 0, 5); work()
    check(dspblock(4) == b4 and meta()[0] == 6, f"XL-4: another pattern edited: block 4 back to the DSP, block 5 cached ({meta().hex()})")
    setp(XL.REC_ON, 0, 1); setmeta(cached=3, wanted=3); setp(edited(0), 0, 7); work()
    check(meta()[0] == 3 and meta()[4] == 3, f"XL-4: playing: the playing block stays wanted ({meta().hex()})")

    check(not unaligned, f"no unaligned memset / word copy of 8 bytes or more ({unaligned[:4]})")
    print(f"{R['D']['marker']} XLFIX RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text())) else 0)
