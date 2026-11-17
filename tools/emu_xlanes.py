"""xlanes phase 1 tests (the storage of the extra automation lanes), on the RAM dump with emu_sc35's card / DSP model:
  * a save of a project without lanes whose file has no tail: nothing written (the file stays 160 780 B); the save as the device makes it (the
    stock's 0x0802FDF8: r5 = the project slot, [session + 0x60] p0 = the pack; the card keyed by the loaded pack, the storage task's current pack
    modelled): the tail in that project's file, the current pack unchanged (Beta 5.58-5.62 swapped the two: xlanes.use_svfix());
  * with lanes (block 0 and 15 holding data in the DSP's external memory): the header at 0x2740C ("XLN1", version 1, the bitmap, the checksum of
    MIDI 1 / 2's patterns, the length) and the 16 blocks after it, byte for byte from the DSP's words, in the slot the save names ([session + 0x60]);
  * a load of that project (the Projects view's param 8): the blocks back into the DSP, the bitmap back;
  * a load whose patterns differ from the saved checksum (Components put another project there): no lanes;
  * a new project: no lanes; then a save with no lanes over a file with a tail: only the header (bitmap 0);
  * the Projects view's check (0x080404B4): a file at least as long as its header says = valid; shorter = not;
  * all along: the stock's memset (0x0801A9BC) / word copy (0x0801AA34) never called with an unaligned destination / source for 8 bytes or more
    (they store with stm: a UsageFault on the device, which Unicorn does not raise; Beta 5.62's crash recording a VA knob: xlanes.use_memfix()).

    python tools/emu_xlanes.py BUILD.bin manifest.json
"""
from __future__ import annotations
import json, random, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_LR, UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R5
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc35 import E35  # noqa: E402
import packio as PK  # noqa: E402
import xlanes as XL  # noqa: E402

SES = XL.SESSION_OBJ
PACK = 1                                                       # the loaded pack in these tests (its items are kept under 0xFF)
MEMSET, WCOPY = 0x0801A9BC, 0x0801AA34


def align_guard(e):
    """the stock's memset (dst, n, c) / word copy (dst, src, n) store with stm / strd: an unaligned address for 8 bytes or more faults on the
    device (UNALIGNED); the calls that would, as (pc, lr, r0, r1, r2)"""
    bad = []
    def ms(uc, a, s, d):
        r0, r1, r2 = (uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2))
        if a == MEMSET and r0 & 3 and r1 >= 8 or a == WCOPY and (r0 | r1) & 3 and r2 >= 8:
            bad.append((hex(a), hex(uc.reg_read(UC_ARM_REG_LR)), hex(r0), hex(r1), hex(r2)))
    for ad in (MEMSET, WCOPY): e.uc.hook_add(UC_HOOK_CODE, ms, begin=ad, end=ad)
    return bad


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = E35(img, man); R = man["report"]
    unaligned = align_guard(e)
    e.cur = e.scur = PACK
    xl = {k: int(v, 16) for k, v in R["xlanes"]["labels"].items()}
    pv = {k: int(v, 16) for k, v in R["xlanes"]["prev"].items()}
    for k in ("load", "new"):                                   # the chains after our heads: back to the caller
        e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1), begin=pv[k], end=pv[k])
    rec = e.r32(SES + 0x14)
    item = lambda slot: (XL.KIND_SES, slot, 0xFF)
    st = lambda: bytes(e.uc.mem_read(XL.XLR, XL.ST_LEN))
    def save(slot, pack=PACK):                                    # as the stock's save: r5 = the slot, [session + 0x60] p0 = the pack
        e.set_p0(e.r32(SES + 0x60), pack)
        e.uc.reg_write(UC_ARM_REG_R5, slot); e.call(xl["c_xlsv"], SES, maxins=2_000_000)
        e.call(xl["c_xlwork"], maxins=200_000_000)
    def load(slot):
        e.set_p0(e.r32(XL.PROJ_OBJ + 0x20), 0) if False else None
        e.call(PK.PARAM_GET, e.r32(XL.PROJ_OBJ + 0x20), 8, maxins=100000); e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0), bytes([slot]))
        e.call(xl["c_xlld"], maxins=2_000_000); e.call(xl["c_xlwork"], maxins=200_000_000)
    bmap = lambda: struct.unpack_from("<H", st(), XL.O_MAP)[0]
    def setmap(v): e.call(xl["c_xlst"], maxins=10000); e.uc.mem_write(XL.XLR + XL.O_MAP, struct.pack("<H", v))
    csum = lambda: sum(struct.unpack_from(f"<{XL.PATLEN // 4}I", bytes(e.uc.mem_read(rec + XL.PAT0, XL.PATLEN)))) & 0xFFFFFFFF

    plain = bytes(random.Random(5).randrange(256) for _ in range(XL.SZ0))
    e.sd[item(3)] = plain
    setmap(0); n0 = len(e.api); save(3)
    check(e.sd[item(3)] == plain and not [x for x in e.api[n0:] if x[0] == "write"], "no lanes, no tail: nothing written")
    # lanes in blocks 0 and 15
    rnd = random.Random(7)
    words = {XL.XB + i: rnd.randrange(0x10000) << 8 for i in range(XL.BLKW)}
    words.update({XL.XB + 15 * XL.BLKW + i: rnd.randrange(0x10000) << 8 for i in range(XL.BLKW)})
    e.ext.clear(); e.ext.update(words)
    setmap(0x8001); save(3); f = e.sd[item(3)]
    hdr = f[XL.SZ0:XL.SZ0 + XL.HDR]
    exp_data = b"".join(struct.pack("<H", (e.ext.get(XL.XB + i, 0) >> 8) & 0xFFFF) for i in range(XL.DATA // 2))
    check(len(f) == XL.SZ0 + XL.HDR + XL.DATA and f[:XL.SZ0] == plain, f"with lanes: the file = the stock part + {XL.HDR} + {XL.DATA} ({len(f)})")
    check(hdr == struct.pack("<IHHII", XL.MAGIC, 1, 0x8001, csum(), XL.DATA), f"the header: XLN1, 1, the bitmap, the checksum, the length ({hdr.hex()})")
    check(f[XL.SZ0 + XL.HDR:] == exp_data, "the 16 blocks byte for byte from the DSP's words")
    wr = {x[1] for x in e.api if x[0] == "write"}
    check(wr == {(XL.KIND_SES, 3, PACK)} and e.scur == PACK and sorted(e.sd) == [item(3)],
          f"the save's item = {{2, slot 3, pack {PACK}}} only; the storage task's current pack unchanged ({wr}, {e.scur}, {sorted(e.sd)})")
    check(e.sem == 0 and e.lock == 0, f"the semaphore and the buffer lock balanced ({e.sem}, {e.lock})")
    # load it back
    e.ext.clear(); setmap(0); load(3)
    got = {XL.XB + i: e.ext.get(XL.XB + i, 0) for i in range(XL.DATA // 2)}
    check(bmap() == 0x8001 and all(got[k] == words.get(k, 0) for k in got if k in words), f"a load: the blocks back into the DSP, the bitmap {bmap():#x}")
    # a load with other patterns (Components put another project there)
    e.uc.mem_write(rec + XL.PAT0 + 100, bytes([e.r8(rec + XL.PAT0 + 100) ^ 0x5A]))
    load(3)
    check(bmap() == 0, f"a load whose patterns differ: no lanes ({bmap():#x})")
    e.uc.mem_write(rec + XL.PAT0 + 100, bytes([e.r8(rec + XL.PAT0 + 100) ^ 0x5A]))
    # a new project; then a save with no lanes over the file with a tail: the header only
    setmap(0x0003); e.call(xl["c_xlnew"], maxins=2_000_000); e.call(xl["c_xlwork"], maxins=200_000_000)
    check(bmap() == 0, "a new project: no lanes")
    n0 = len(e.api); save(3); f2 = e.sd[item(3)]
    w = [x for x in e.api[n0:] if x[0] == "write"]
    check(len(w) == 1 and w[0][2:4] == (XL.SZ0, XL.HDR) and len(f2) >= XL.SZ0 + 8 and struct.unpack_from("<H", f2, XL.SZ0 + 6)[0] == 0, f"no lanes, a tail there: the header only, bitmap 0 ({w})")
    # pattern paste / clear (the stock's dispatcher calls): MIDI 2 pattern 4 (block 12) -> MIDI 1 pattern 5 (block 5)
    obj = lambda t: XL.PAT_OBJ + XL.PAT_SZ * t
    src = lambda t, p: e.r32(obj(t) + 4) + XL.PAT_N * p
    e.ext.clear(); blk12 = {XL.XB + 12 * XL.BLKW + i: rnd.randrange(0x10000) << 8 for i in range(XL.BLKW)}; e.ext.update(blk12)
    setmap(1 << 12)
    e.call(xl["c_xlcp"], obj(2), src(3, 4), 5, maxins=5_000_000)
    q = st()[XL.O_QN]
    e.call(xl["c_xlwork"], maxins=200_000_000)
    ok = all(e.ext.get(XL.XB + 5 * XL.BLKW + i, 0) == blk12[XL.XB + 12 * XL.BLKW + i] for i in range(XL.BLKW))
    check(q == 1 and ok and bmap() == (1 << 12) | (1 << 5) and st()[XL.O_QN] == 0, f"MIDI 2 p5 -> MIDI 1 p6: queued, the block copied in the DSP, its bit set ({bmap():#x})")
    e.call(xl["c_xlcp"], obj(2), src(0, 1), 5, maxins=5_000_000)
    check(bmap() == 1 << 12 and st()[XL.O_QN] == 0, f"Synth 1 -> MIDI 1 p6: no lanes there ({bmap():#x})")
    e.call(xl["c_xlcp"], obj(3), src(2, 7), 0, maxins=5_000_000)
    check(bmap() == 1 << 12 and st()[XL.O_QN] == 0, f"an empty block -> MIDI 2 p1: none, nothing queued ({bmap():#x})")
    e.call(xl["c_xlcp"], obj(0), src(3, 4), 2, maxins=5_000_000)
    check(bmap() == 1 << 12, f"MIDI 2 -> Synth 1: no lanes touched ({bmap():#x})")
    e.call(xl["c_xlclr"], obj(3), 4, maxins=5_000_000)
    check(bmap() == 0, f"Clear MIDI 2 p5: its bit off ({bmap():#x})")
    # Components rewrites a session of pack 7, slot 5 (its write: the delete at the start, the host's bytes, the end)
    e.cur = e.scur = None                                         # (c_resel is not modelled: the raw items from here)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s_, d: uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1), begin=0x080399FE, end=0x080399FE)   # the stock's end
    SCR = 0x2006F100
    it7 = (XL.KIND_SES, 5, 7)
    pats = bytes(e.uc.mem_read(rec, XL.SZ0))
    tail_data = bytes(rnd.randrange(256) for _ in range(XL.DATA))
    sum7 = sum(struct.unpack_from(f"<{XL.PATLEN // 4}I", pats, XL.PAT0)) & 0xFFFFFFFF
    full7 = pats + struct.pack("<IHHII", XL.MAGIC, 1, 0x0041, sum7, XL.DATA) + tail_data
    def comp(new_file):
        e.sd[it7] = full7
        e.uc.mem_write(SCR, struct.pack("<IIB", XL.KIND_SES, 5, 7) + bytes(3))
        e.call(xl["c_xlds"], SCR, 0, 0, maxins=300_000_000)
        held = e.sd.get(it7) is None
        e.sd[it7] = new_file
        e.uc.mem_write(SCR + 0x40, bytes(0x1C) + bytes([XL.T_SES, 7, 5]) + bytes(1))
        e.call(xl["c_xlce"], SCR + 0x40, 0, maxins=300_000_000)
        return held, e.sd[it7]
    held, f7 = comp(pats)
    check(held and f7 == full7, f"Components rewrites the same project without lanes: its lanes back ({len(f7)} B)")
    other = bytearray(pats); other[XL.PAT0 + 40] ^= 0x33
    held, f7 = comp(bytes(other))
    check(f7 == bytes(other), f"Components puts another project there: the held lanes dropped ({len(f7)} B)")
    own = pats + b"Z" * 40
    held, f7 = comp(own)
    check(f7 == own, "a host file with a tail of its own: left as written")
    check(e.sem == 0 and e.lock == 0, f"the semaphore and the buffer lock balanced ({e.sem}, {e.lock})")
    # ---- phase 3: recording into the playing block (ITCM), its write-back, playback at micro steps 0 and 3
    import emu_arp as EAm, vcf21 as V
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05]))           # the own engine on
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s_, d: uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1), begin=pv["play"], end=pv["play"])
    applied = []
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s_, d: applied.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2))),
                  begin=xl["c_xlap"], end=xl["c_xlap"])
    P1 = XL.PLAYER0 + 2 * XL.PLAYER_SZ
    st1 = e.r32(XL.ENG + 0x38); pst = e.r32(P1 + 0x10)
    EAm.EA.setp(e, pst, 1, bytes([3])); tps = e.r32(XL.TICKS_TAB + 12)
    def at(pat, step, tick): EAm.EA.setp(e, st1, 0, bytes([pat])); EAm.EA.setp(e, st1, 1, bytes([step])); EAm.EA.setp(e, st1, 2, struct.pack("<I", tick))
    setmap(0); e.ext.clear()
    EAm.EA.setp(e, XL.REC_ON, 0, bytes([1]))                                              # playing (stopped: the edited pattern is cached, use_editcache)
    e.call(xl["c_xlpl"], P1, 2, 5, 0, maxins=2_000_000); e.call(xl["c_xlwork"], maxins=200_000_000)
    meta_ = lambda: bytes(e.uc.mem_read(XL.XLR + XL.O_CM, 8))
    check(meta_()[0] == 3 and meta_()[4] == 3, f"MIDI 1 plays pattern 3: block 2 wanted and cached ({meta_().hex()})")
    for k, v in ((1, 1), (0, 0)): EAm.EA.setp(e, e.r32(XL.REC_ON) if False else XL.REC_ON, k, bytes([1]))
    rec_fn = int(R["vcf20"]["labels"]["c_vcc_rec"], 16)
    at(2, 5, 0); e.call(rec_fn, 0, 19, 40, maxins=5_000_000)
    at(2, 5, tps - 1); e.call(rec_fn, 0, 19, -20 & 0xFFFFFFFF, maxins=5_000_000)
    c0 = 0x100
    blk = bytes(e.uc.mem_read(c0, XL.BLK))
    s0 = blk.index(19) if 19 in blk[:XL.NSLOT] else -1
    vt = lambda c, v: (e.call(int(R["vcf20"]["labels"]["c_vtou"], 16), c, v & 0xFFFFFFFF, maxins=100000), e.uc.reg_read(UC_ARM_REG_R0))[1]
    ok = s0 >= 0 and blk[XL.VOFF + 64 * s0 + 10] == vt(19, 40) and blk[XL.VOFF + 64 * s0 + 11] == vt(19, -20)
    check(ok and bmap() == 1 << 2 and meta_()[2] == 1, f"Record: code 19 in slot {s0}, step 6's two halves; block 2 holds data, changed ({bmap():#x}, {meta_().hex()})")
    e.call(xl["c_xlpl"], P1, 4, 0, 0, maxins=2_000_000); e.call(xl["c_xlwork"], maxins=200_000_000)
    dsp = b"".join(struct.pack("<H", (e.ext.get(XL.XB + 2 * XL.BLKW + i, 0) >> 8) & 0xFFFF) for i in range(XL.BLKW))
    check(dsp[:XL.BLK] == blk and meta_()[0] == 5 and meta_()[2] == 0, f"another pattern: the changed block written back to the DSP, block 4 cached ({meta_().hex()})")
    e.call(xl["c_xlpl"], P1, 2, 5, 0, maxins=2_000_000); e.call(xl["c_xlwork"], maxins=200_000_000)
    applied.clear(); e.call(xl["c_xlpl"], P1, 2, 5, 0, maxins=2_000_000); a0 = list(applied)
    applied.clear(); e.call(xl["c_xlpl"], P1, 2, 5, 3, maxins=2_000_000); a3 = list(applied)
    applied.clear(); e.call(xl["c_xlpl"], P1, 2, 5, 1, maxins=2_000_000); a1 = list(applied)
    check(a0 == [(0, 19, vt(19, 40))] and a3 == [(0, 19, vt(19, -20))] and a1 == [], f"playback: micro 0 = the first half, 3 = the second, 1 = nothing ({a0}, {a3}, {a1})")
    at(2, 5, 0); e.call(rec_fn, 0, 17, 30, maxins=5_000_000)
    check(17 not in bytes(e.uc.mem_read(c0, XL.NSLOT)), "a code on page 4 (17): its stock lane, not a slot")
    # the release mark (autorel: bit 7 of the step's byte 3): nothing from the slots on that step
    pb = e.r32(XL.PAT_OBJ + 2 * XL.PAT_SZ + 4) + 2 * XL.PAT_N + 28 * 5 + 3
    b3 = e.r8(pb); e.uc.mem_write(pb, bytes([b3 | 0x80]))
    applied.clear(); e.call(xl["c_xlpl"], P1, 2, 5, 0, maxins=2_000_000)
    check(applied == [], f"a released step (Shift + step): the slots play nothing ({applied})")
    e.uc.mem_write(pb, bytes([b3]))
    # Clear + K3 to the left on the OSC 1 page (code 19): its slot erased in the edited pattern
    vl = {k: int(v, 16) for k, v in R["vcf20"]["labels"].items()}
    e.call(vl["c_vsetpage"], 0, 1, maxins=2_000_000)
    EAm.EA.setp(e, e.r32(XL.PAT_OBJ + 2 * XL.PAT_SZ + 0x24), 0, bytes([2]))
    e.call(vl["c_vkc"], 0, 16 * 1 + 2, maxins=100000); k3 = e.uc.reg_read(UC_ARM_REG_R0)
    e.call(vl["c_vclrauto"], 0x2006F200, 2, 0, maxins=5_000_000)
    blk2 = bytes(e.uc.mem_read(c0, XL.BLK))
    check(k3 == 19 and 19 not in blk2[:XL.NSLOT] and blk2[XL.VOFF + 64 * s0:XL.VOFF + 64 * s0 + 64] == bytes([0xFF]) * 64 and meta_()[2] == 1,
          f"Clear + K3 (code {k3}) to the left: its slot erased, the block changed ({meta_().hex()})")
    # Record + step (recinst's snapshot): a differing code without a stock lane = its slot, both halves of the step; the row untouched
    vrow = lambda: bytes(e.uc.mem_read((e.call(vl["c_vrow"], 0, maxins=100000), e.uc.reg_read(UC_ARM_REG_R0))[1], 8))
    row0 = vrow()
    e.call(vl["c_vvaddr"], 0, 19, maxins=100000); e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0), bytes([77]))
    ri = int(R["recinst"]["labels"]["c_riinst"], 16)
    e.call(ri, 0, 7, maxins=20_000_000)
    blk3 = bytes(e.uc.mem_read(c0, XL.BLK)); s3 = blk3[:XL.NSLOT].index(19) if 19 in blk3[:XL.NSLOT] else -1
    check(s3 >= 0 and blk3[XL.VOFF + 64 * s3 + 14] == vt(19, 77) and blk3[XL.VOFF + 64 * s3 + 15] == vt(19, 77) and vrow() == row0,
          f"Record + step 8: code 19 in slot {s3}, both halves = {vt(19, 77)}; the row unchanged")
    # Nudge (pad 26) on steps 5..8 of MIDI 1 pattern 3: the slots' pairs rotated one step back
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s_, d: uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1), begin=pv["nudge"], end=pv["nudge"])
    e.call(int(R["patchain"]["labels"]["c_pcrule"], 16), 2, 2, maxins=100000); rp = e.uc.reg_read(UC_ARM_REG_R0) - 4
    e.uc.mem_write(rp, bytes([7, 4]))                                                  # last 8, first 5
    pre = bytes(e.uc.mem_read(c0 + XL.VOFF + 64 * s3, 64))
    e.call(xl["c_xlnu"], 0x2006F300, 2, 2, 0, maxins=5_000_000)
    post = bytes(e.uc.mem_read(c0 + XL.VOFF + 64 * s3, 64))
    want = pre[:8] + pre[10:16] + pre[8:10] + pre[16:]
    check(post == want, f"Nudge back on steps 5..8: the pairs rotated by one ({pre[8:16].hex()} -> {post[8:16].hex()})")
    e.call(xl["c_xlnu"], 0x2006F300, 2, 2, 1, maxins=5_000_000)
    check(bytes(e.uc.mem_read(c0 + XL.VOFF + 64 * s3, 64)) == pre, "Nudge forward: back as before")
    # the Projects view's session check
    chk = 0x080404B4
    for sz, want in ((XL.SZ0, 1), (XL.SZ0 + XL.HDR + XL.DATA, 1), (XL.SZ0 - 4, 0)):
        e.call(chk, rec, sz, maxins=1000); r = e.uc.reg_read(UC_ARM_REG_R0)
        check(r == want, f"the Projects view's check, a file of {sz} B: {r}")
    check(not unaligned, f"no unaligned memset / word copy of 8 bytes or more ({unaligned[:4]})")
    print(f"{R['D']['marker']} XLANES RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text())) else 0)
