"""Profile (no pass / fail): what the LED task does per frame in MIDI 1's Preset view and its morph view (own synth with the 8-operator FM, two
slots that carry an FM record): ARM instructions per frame, card reads (mpatch's c_mpr / c_mpsz and the content API), the FM block marked dirty,
own codes changed, over 20 s of frames, stopped and playing, the morph still and moving (K2 / K3 = LFO 1 depth / rate).

    python tools/prof_morph.py BUILD.bin manifest.json
"""
from __future__ import annotations
import gc, json, os, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc48_8 as S  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import emu_sc17_6 as T6  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402,F401
import morphz as M  # noqa: E402
import jumpseq as J  # noqa: E402
import mpatch as MP  # noqa: E402
import fmeng as FE  # noqa: E402
import fm8arm as A  # noqa: E402
import fm8inst as FI  # noqa: E402
import vcf21 as V  # noqa: E402
import lazysave as LZ  # noqa: E402

MGR, PRESS, RELEASE = S.MGR, T6.PRESS, T6.RELEASE
LRS = {}
SD_OPS = (0x0803CBF0, 0x0803CB50)


def main(img, man):
    e = S.ET(img, man)
    def drain():
        r = e.r32(0x200069F4)
        for k in range(e.r8(r + 0x18)): e.uc.mem_write(e.r32(e.r32(e.r32(r + 0x14) + 4 * k) + 0x10), bytes(4))
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: uc.mem_write(e.r32(uc.reg_read(UC_ARM_REG_R0) + 0x10), bytes(4)), begin=0x08035A50, end=0x08035A50)
    e.btn = lambda b: (drain(), e.call(0x08033320, MGR, b, maxins=20_000_000), drain(), e.call(0x0803381A, MGR, b, maxins=20_000_000))
    R = man["report"]
    SVCL = R["morphz"]["labels"].get("c_mzsvc")
    if SVCL:
        nxt = int(R["morphz"]["prev"]["svc"], 16)
        e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1), begin=nxt, end=nxt)
    t = [500000]
    def at(ms): t[0] += ms; e.w32(J.HAL_TICK, t[0])
    at(0)
    cnt = {"mpr": 0, "mpsz": 0, "api": 0, "dirty": 0, "store": 0, "ins": 0}
    import projsyn as PS
    bank0 = bytearray(b"\xFF" * 8192)
    for slot, k in ((1, 0), (2, 3)):
        p = bytearray(b"\xFF" * 40); struct.pack_into("<I", p, 0, MP.MAGIC4)
        for c in range(34): p[6 + c] = (c * 7 + slot * 13) & 0x3F
        bank0[512 * slot:512 * slot + 340] = bytes(340); bank0[512 * slot + MP.OFF:512 * slot + MP.OFF + 40] = p
        f = bytearray(4) + FI.inst_full(k) + bytes(4); struct.pack_into("<I", f, 0, 0x01384D46)
        bank0[4096 + 512 * slot:4096 + 512 * slot + len(f)] = f
    def mpr(uc, a, s_, d):
        bank, off, buf, n = (uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3))
        if e.r8(PS.STR + PS.O_VS): return                                  # projsyn's RAM IO: let it run
        cnt["mpr"] += 1
        src = bank0 if bank == 0 else b"\xFF" * 8192
        uc.mem_write(buf, bytes(src[off:off + n]).ljust(n, b"\xFF"))
        uc.reg_write(UC_ARM_REG_R0, 0); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, mpr, begin=int(R["mpatch"]["labels"]["c_mpr"], 16), end=int(R["mpatch"]["labels"]["c_mpr"], 16))
    def size(uc, a, s_, d):
        cnt["mpsz"] += 1; uc.reg_write(UC_ARM_REG_R0, 8192); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, size, begin=0x0803CB6A, end=0x0803CB6A)
    def api(uc, a, s_, d): cnt["api"] += 1
    for f_ in SD_OPS: e.uc.hook_add(UC_HOOK_CODE, api, begin=f_, end=f_)
    blk = A.FM8R + A.TB0
    def dw(uc, acc, a_, sz, v, d):
        if v: cnt["dirty"] += 1
    e.uc.hook_add(UC_HOOK_MEM_WRITE, dw, begin=blk + A.B_DIRTY, end=blk + A.B_DIRTY)
    vst = int(R["vcf20"]["labels"]["c_vstore"], 16) if "c_vstore" in R["vcf20"]["labels"] else None
    if vst: e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: cnt.__setitem__("store", cnt["store"] + 1), begin=vst, end=vst)
    def ins(uc, a, s, d): cnt["ins"] += 1
    hold = lambda q: (e.call(PRESS, MGR, q, 100, maxins=8_000_000), at(5))
    let = lambda q: (e.call(RELEASE, MGR, q, maxins=8_000_000), at(5))
    peak = [0]
    def frames(n, step=20):
        for _ in range(n):
            i0 = cnt["ins"]; at(step); X.frame(e); peak[0] = max(peak[0], cnt["ins"] - i0)
            if SVCL: e.call(int(SVCL, 16), maxins=8_000_000)
    def meas(label, secs, step=20):
        for k in cnt: cnt[k] = 0
        peak[0] = 0
        h = e.uc.hook_add(UC_HOOK_CODE, ins); nf = secs * 1000 // step; frames(nf, step); e.uc.hook_del(h)
        print(f"  {label:44s} {cnt['ins'] / nf:8.0f} ins/frame (peak {peak[0]:6d})   card: c_mpr {cnt['mpr']:3d} sizes {cnt['mpsz']:3d} api {cnt['api']:3d}   "
              f"FM dirty {cnt['dirty']:4d}  own codes stored {cnt['store']:5d}  ({nf} frames)")
    print(f"{man.get('marker', '?')}: 20 ms frames")
    e.btn(2); e.btn(8)
    if not os.environ.get("NOFM"):
        for q in (26, FE.ROWPAD, 26, 1):
            e.call(PRESS, MGR, q, 100, maxins=8_000_000); a1 = e.r32(MGR + 0x84); v1 = hex(e.r32(MGR + 0x6C))
            e.call(RELEASE, MGR, q, maxins=8_000_000); print(f"  pad {q + 1}: held after press {a1:#x} ({v1}), after release {e.r32(MGR + 0x84):#x} ({e.r32(MGR + 0x6C):#x})")
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 1])); frames(5)
    if not os.environ.get("QUICK"): meas("MIDI 1 Preset (FM), stopped", 20)
    if not os.environ.get("QUICK"): e.transport(1); meas("MIDI 1 Preset (FM), playing", 20); e.transport(0)
    for k in cnt: cnt[k] = 0

    if os.environ.get("TAP"):
        LR = {}
        def lr(uc, a, s_, d):
            if not e.r8(PS.STR + PS.O_VS): k = hex(uc.reg_read(UC_ARM_REG_LR)); LR[k] = LR.get(k, 0) + 1
        hh = e.uc.hook_add(UC_HOOK_CODE, lr, begin=int(R["mpatch"]["labels"]["c_mpr"], 16), end=int(R["mpatch"]["labels"]["c_mpr"], 16))
        for play in (0, 1):
            e.transport(play)
            for q in (9, 10, 9):
                for k in cnt: cnt[k] = 0
                LR.clear(); dw = [0]
                h1 = e.uc.hook_add(UC_HOOK_CODE, ins); h2 = e.uc.hook_add(UC_HOOK_CODE, lambda uc, a_, s_, d_: dw.__setitem__(0, dw[0] + 1), begin=0x080292F8, end=0x080292F8)
                e.call(PRESS, MGR, q, 100, maxins=20_000_000); e.call(RELEASE, MGR, q, maxins=20_000_000); e.uc.hook_del(h1); e.uc.hook_del(h2); ti = cnt["ins"]
                frames(150)
                print(f"  playing {play}: tap slot {q - 8}: {ti} ins in the press + release, {dw[0]} DSP writes; c_mpr {cnt['mpr']} sizes {cnt['mpsz']} api {cnt['api']} FM dirty {cnt['dirty']}  callers {LR}")
        return
    if os.environ.get("QUICK"):
        print("view", hex(e.r32(MGR + 0x6C)), "152", e.r8(MGR + 0x152))
        print("pads", [hex(x & 0xFFFF) for x in X.frame(e)[:32]])
        Lm = {k: int(v, 16) for k, v in R["morphz"]["labels"].items()}
        e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s_, d: print("  c_mzpadX reached r1", uc.reg_read(UC_ARM_REG_R1)), begin=Lm["c_mzpadX"], end=Lm["c_mzpadX"])
        e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s_, d: print("  c_mzpad r4..r7", [uc.reg_read(r) for r in (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7)], "MGR84", hex(e.r32(MGR + 0x84)), "clr/dup", hex(e.r32(e.r32(e.r32(MGR + 0x20) + 0xC)))), begin=Lm["c_mzpad"], end=Lm["c_mzpad"])
        hold(8); print("after hold 8: HP", e.r8(M.MZ + M.O_HP), "SNAP", e.r8(M.MZ + M.O_SNAP), "ACT", e.r8(M.MZ + M.O_ACT)); hold(9)
        frames(1); at(450); frames(3); print("act", e.r8(M.MZ + M.O_ACT)); return
    hold(8); hold(9); frames(1); at(450); frames(3); let(8); let(9)
    print(f"  entering the morph: card c_mpr {cnt['mpr']}, c_mpsz {cnt['mpsz']}, api {cnt['api']}; act {e.r8(M.MZ + M.O_ACT)} n {e.r8(M.MZ + M.O_N)} cv {e.r8(M.MZ + M.O_CV):#x}")
    meas("morph view, still, stopped", 20)
    e.transport(1); meas("morph view, still, playing", 20)
    for _ in range(40): e.knob(1, 1)
    for _ in range(40): e.knob(2, 1)
    meas("morph view, LFO 1 moving, playing", 20)
    e.transport(0); meas("morph view, LFO 1 moving, stopped", 20)
    del e; gc.collect()


if __name__ == "__main__":
    main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text()))
