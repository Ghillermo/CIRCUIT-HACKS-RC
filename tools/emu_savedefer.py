"""SC49.7 test (savedefer + packio.use_svskip): the project save waits while the sequencer plays; ours reads the DSP once when nothing is pending.

    python tools/emu_savedefer.py BUILD.bin manifest.json
The real route: Save twice (button 25) -> the session manager's store -> its listener (0x08059CF0) -> the save routine 0x0802FDF8; the posting of
the record to the storage task (0x0803C946) is counted and skipped; after each stock save the manager's «saving» ([+ 0x64] p1 = 2, cleared by the
storage task's callback) is cleared by hand.
  * stopped: Save twice posts at once, as the stock;
  * playing: nothing posted, the save kept (its slot); the Save LED (57) yellow / off by the clock; Save twice again: still nothing;
  * stopped again: the next LED frame posts it, once; the LED back to the stock's;
  * a kept save waits while the manager is busy, and is dropped if the manager's pack changed;
  * a save of another slot through the listener: the kept one is posted first and the new one finds the stock «saving» (ignored, as the stock
    does while it saves); asked again: kept; the same slot again: nothing posted;
  * svskip: the save hook with every capture slot saved reads the DSP once; with none saved and nothing in the slots, 65 reads and the slots' bits
    set (X:$3D1E = $FF), so the next save reads once.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn import UC_HOOK_CODE  # noqa: E402
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_LR, UC_ARM_REG_PC  # noqa: E402
import emu_lazysave as T  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import savedefer as SD  # noqa: E402
import fxdiag as FD  # noqa: E402

MAN = 0x2003D71C
POST = 0x0803C946
SAVE_BTN = 25


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    R = man["report"]
    lab = lambda m, k: int(R[m]["labels"][k], 16)
    e = T.EL(img); e.at(300000); e.transport(0)
    posts = []
    def post(uc, a, s, d): posts.append(1); uc.reg_write(UC_ARM_REG_R0, 0); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, post, begin=POST, end=POST)
    r0 = lambda fn, *a: (e.call(fn, *a, maxins=8_000_000), e.uc.reg_read(UC_ARM_REG_R0))[1]
    p_at = lambda store, k: r0(0x0803542C, store, k)
    def busy(v):
        for fn in (0x080354FA, 0x0803542C): e.uc.mem_write(r0(fn, e.r32(MAN + 0x64), 1), bytes([v]))
    def save():
        e.btn(SAVE_BTN); e.btn(SAVE_BTN)
    ram = lambda: bytes(e.uc.mem_read(SD.RAM, 16))
    def frame(t):
        e.at(t); return X.frame(e)[SD.LED_SAVE]
    t = 300000
    # stopped: as the stock
    save(); n1 = len(posts); busy(0)
    check(n1 == 1 and ram()[4] == 0, f"stopped: Save twice posts the record at once ({n1}), nothing kept ({ram()[4]})")
    # playing: kept
    e.transport(1); save(); k = ram()
    slot = e.r8(p_at(e.r32(MAN + 0x60), 0))
    check(len(posts) == 1 and k[4] == 1 and struct.unpack_from("<I", k, 8)[0] == MAN and k[12] == slot,
          f"playing: nothing posted ({len(posts) - 1}), the save kept (manager {struct.unpack_from('<I', k, 8)[0]:#x}, slot {k[6]}, pack {k[12]} / {slot})")
    l1, l2 = frame(t + 0x100), frame(t + 0x200)
    check({l1 & 0xFF, l2 & 0xFF} == {SD.YELLOW, 0} and len(posts) == 1, f"the Save LED blinks yellow while it waits ({l1:#x} / {l2:#x}), still nothing posted")
    save(); check(len(posts) == 1 and ram()[4] == 1, f"Save twice again while playing: still kept, nothing posted ({len(posts) - 1})")
    e.transport(0); l3 = frame(t + 0x400); n2 = len(posts); busy(0); l4 = frame(t + 0x500)
    check(n2 == 2 and ram()[4] == 0 and len(posts) == 2 and l3 & 0xFF != SD.YELLOW,
          f"stopped: the next LED frame posts it, once ({n2 - 1}, then {len(posts) - n2}); the LED as the stock's ({l3:#x})")
    # busy: waits
    e.transport(1); save(); busy(2); e.transport(0); frame(t + 0x600)
    w1 = (len(posts), ram()[4]); busy(0); frame(t + 0x700); w2 = (len(posts), ram()[4]); busy(0)
    check(w1 == (2, 1) and w2 == (3, 0), f"the manager busy: the kept save waits ({w1}), then posted ({w2})")
    # the pack changed: dropped
    e.transport(1); save(); pk = p_at(e.r32(MAN + 0x60), 0); old = e.r8(pk); e.uc.mem_write(pk, bytes([old ^ 1])); e.transport(0); frame(t + 0x800)
    w3 = (len(posts), ram()[4]); e.uc.mem_write(pk, bytes([old]))
    check(w3 == (3, 0), f"the manager's pack changed: the kept save dropped ({w3})")
    # another slot through the listener: the kept one first
    e.transport(1); save(); s0 = ram()[6]
    lst = struct.unpack_from("<I", img, SD.DISP_VT - 0x08010000)[0]
    e.call(lst & ~1 | 1, MAN + 4, e.r32(MAN + 0x48), s0 ^ 1, 0, maxins=8_000_000)
    k2 = ram()
    check(len(posts) == 4 and k2[4] == 0, f"a save of another slot while one is kept: the kept one posted ({len(posts) - 3}), the new one ignored while it saves ({k2[4]})")
    busy(0); e.call(lst & ~1 | 1, MAN + 4, e.r32(MAN + 0x48), s0 ^ 1, 0, maxins=8_000_000); k3 = ram()
    e.call(lst & ~1 | 1, MAN + 4, e.r32(MAN + 0x48), s0 ^ 1, 0, maxins=8_000_000); k4 = ram()
    check(len(posts) == 4 and k3[4] == 1 and k3[6] == s0 ^ 1 and k4[4] == 1, f"asked again: kept (slot {k3[6]}); the same slot again: nothing posted ({len(posts) - 4})")
    e.transport(0); frame(t + 0x900); busy(0)
    del e; gc.collect()
    # svskip
    e = T.EL(img); e.at(300000); e.transport(0)
    mem = {}
    reads = []
    def xr(uc, a, s, d):
        ad = uc.reg_read(UC_ARM_REG_R0); reads.append(ad); uc.reg_write(UC_ARM_REG_R0, mem.get(ad, 0)); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    def xw(uc, a, s, d):
        mem[uc.reg_read(UC_ARM_REG_R0)] = uc.reg_read(UC_ARM_REG_R1) & 0xFFFFFF; uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, xr, begin=lab("packio", "c_xr"), end=lab("packio", "c_xr"))
    e.uc.hook_add(UC_HOOK_CODE, xw, begin=lab("packio", "c_xw"), end=lab("packio", "c_xw"))
    import packio as PK
    tgt = FD.bl_target(img, 0x0802FE5E, 0x08010000)
    def hook_save():
        reads.clear(); e.call(tgt, MAN, maxins=200_000_000); return len(reads)
    mem[PK.SAVED] = 0xFF; n_all = hook_save()
    mem[PK.SAVED] = 0; n_none = hook_save(); sv = mem.get(PK.SAVED); n_next = hook_save()
    check(n_all == 1 and n_none == 65 and sv == 0xFF and n_next == 1,
          f"svskip: every slot saved = 1 DSP read ({n_all}); none = 65 ({n_none}) and the bits set ({sv:#x}); the next save = 1 ({n_next})")
    del e; gc.collect()
    print(f"SAVEDEFER RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
