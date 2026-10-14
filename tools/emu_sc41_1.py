"""SC41.1 ARM tests: the Master FX view's LED buffer out of the idle memory (build_sc17.use_ledbuf) and the random value of the FX sequencer
(vcf21.use_fxseqrand + build_sc17.use_fxseqrand).

    python tools/emu_sc41_1.py SC41.1.bin SC41.1_manifest.json SC41.bin SC41_manifest.json
  * the Master FX view on the screen, frames drawn: the 84 bytes at c_gst() + 104..187 (the chains' mark, the step frequency counters, the states
    of the Sidechain knobs, the patch slots, the copy, the editor, the granular source) stay as they were; the LEDs are in the record's tail + 192;
    the running part of the chains survives; the previous build overwrote them;
  * MIDI 1 in the FX sequencer state, a note on step 1, its pair at the position of value 7: c_fsqbits = bit 6 + a seed that holds for the whole
    step and changes with the tick the step started at; c_fsqfx = exactly one of the list (the two assigned slots' effects or pad 31, the mechanical gesture), all over the seeds; the
    knob LED white; the previous build: value 7 does not exist (nothing).
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R4
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc35 import MGR  # noqa: E402
from emu_sc05 import STOP  # noqa: E402
import emu_sc40_8 as T8  # noqa: E402
import build_sc17 as S17  # noqa: E402
import patchain as PC  # noqa: E402

ENG = PC.ENG


def view_part(img, man):
    LP = {k: int(v, 16) for k, v in man["report"]["patchain"]["labels"].items()}
    e = T8.E8(img, man, LP)
    def frame():
        e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR); e.call(0x08033B3E, maxins=40_000_000)
        return list(struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138))))
    btn = lambda i: (e.call(0x08033320, MGR, i, maxins=8_000_000), e.call(0x0803381A, MGR, i, maxins=8_000_000))
    e.st(); frame()
    e.uc.mem_write(e.scr + PC.S_CNT, bytes(range(1, 25)))                         # (the chains' running counts)
    idle = lambda: bytes(e.uc.mem_read(e.gst + 104, 84))
    i0, c0 = idle(), bytes(e.uc.mem_read(e.scr + PC.S_CNT, 24))
    btn(14); btn(14); gv = e.r32(MGR + 0x6C)
    for k in range(4): e.w32(0x2000081C, 400000 + 300 * k); f = frame()
    i1 = idle(); e.st(); c1 = bytes(e.uc.mem_read(e.scr + PC.S_CNT, 24))
    buf = list(struct.unpack("<32H", bytes(e.uc.mem_read(e.tail + 192, 64))))
    del e; gc.collect()
    return i0 == i1, c0 == c1, buf == f[:32] and any(buf), [i for i in range(84) if i0[i] != i1[i]][:12]


def seq_part(img, man):
    import emu_sc36_1 as T361
    V = T361.V
    e = T361.E20(img, man)
    for _ in range(30): e.vtick()
    pad = lambda p: (e.padr(p), e.rel(p))
    def r0(fn, *a): e.call(fn, *a, maxins=8_000_000); return e.uc.reg_read(UC_ARM_REG_R0)
    def put(store, k, data):
        for fn in (0x080354FA, 0x0803542C): e.uc.mem_write(r0(fn, store, k), data)
    L17 = {k: int(v, 16) for k, v in man["report"]["sc17"]["labels"].items()}
    e.btn(2); e.track(2); e.btn(8)
    for _ in range(5): pad(V.PAD_OSC)
    pad(V.PAD_SD)
    e.set_p0(e.r32(MGR + 0xC), 1); pad(0); e.set_p0(e.r32(MGR + 0xC), 0)        # a note on step 1
    pat = r0(e.vl["c_sdpat"], 0); h0 = r0(e.vl["c_sdhalf"], 0)
    for st in (h0, h0 + 1): e.uc.mem_write(r0(e.vl["c_sdlna"], pat, st), bytes([7 * 16]) * 12)
    put(0x20011034, 0, b"\1")
    pl = e.r32(ENG + 0x30 + 4 * 2); put(pl, 1, bytes([h0]))
    blk = r0(L17["c_gfst"])
    slots = bytearray(28); slots[0:4] = b"\x80\x00\x00\x80"; slots[8:12] = b"\x80\x80\x00\x80"     # slot 0 = effect 1, slot 2 = effect 3
    e.uc.mem_write(blk + S17.S_SLOT if hasattr(S17, "S_SLOT") else blk + 148, bytes(slots))
    res = []
    for start in range(0, 48 * 24, 48):
        for tin in (0, 5):
            put(e.r32(ENG + 0x90), 0, struct.pack("<I", start + tin)); put(pl, 2, struct.pack("<I", tin))
            bits = r0(e.vl["c_fsqbits"])
            e.uc.reg_write(UC_ARM_REG_R4, blk); e.call(L17["c_fsqfx"], maxins=4_000_000); fx = e.uc.reg_read(UC_ARM_REG_R0) & 0x7F
            res.append((start, tin, bits, fx))
    e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR); e.call(0x08033B3E, maxins=40_000_000)
    led = struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138)))[60]
    del e; gc.collect()
    return res, led


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    a = view_part(img, man); gc.collect(); p = view_part(prev, prev_man)
    check(set(a[3]) <= {16, 20} and a[1] and a[2] and len(p[3]) > 8, f"the Master FX view drawn: the idle memory (c_gst() + 104..187) kept (only the tags macroed / psave write themselves at + 120 / + 124 may change) and the chains' running part, the LEDs in the record's tail + 192 ({a}); the previous build overwrote it (bytes {p[3]})")
    gc.collect(); res, led = seq_part(img, man)
    seeds = {r[0]: r[2] >> 8 & 0xFF for r in res}
    same = all(r[2] == next(q[2] for q in res if q[0] == r[0]) for r in res)
    fxs = {r[3] for r in res}
    check(all(r[2] & 0x40 for r in res) and same and len(set(seeds.values())) > 12, f"value 7: bit 6 and a seed that holds within the step and changes from step to step ({len(set(seeds.values()))} seeds of 24)")
    check(fxs == {1 << 1, 1 << 3, 0x40}, f"c_fsqfx: one of the list each time (the two assigned slots' effects, pad 31's gesture = bit 6), all of them over the steps ({sorted(fxs)})")
    check(led & 0xFF == 0x01, f"the knob LED of the pair: white ({led:#x})")
    gc.collect(); pres, pled = seq_part(prev, prev_man)
    check(all(r[3] == 0 and r[2] & 0x7F == 0 for r in pres), "the previous build: no value 7 (nothing)")
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
