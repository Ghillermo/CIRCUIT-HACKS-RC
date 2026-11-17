"""Scenes keep a chain each (the user, 2026-11-13, on Beta 5.56 / 5.57: «Pattern chain don't store a different chain per scene»).

    python tools/emu_scnchain.py firmware/b5.57

Through the controller with the Mixer's own pad handler (not stubbed): a chain of patterns 1-2 on Synth 1 and Synth 2, Shift + scene 1;
3-4, Shift + scene 2; then scene 1 picked (stopped): its chains back, then scene 2: its chains."""
import gc, json, struct, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc17_6
emu_sc17_6.MIX_PRESS = -1                                       # run the Mixer's pad handler for real
from emu_sc35 import E35, MGR  # noqa: E402
from emu_sc08 import CONT  # noqa: E402
import stepmod as SM  # noqa: E402

ENG = SM.ENGINE_OBJ
PRESS, RELEASE = 0x08033282, 0x080332FE
import arp as A  # noqa: E402
TRANSPORT, HAL = A.TRANSPORT, A.HAL_TICK if hasattr(A, 'HAL_TICK') else 0x2000081C


def run(d):
    d = Path(d); img = next(d.glob("*.bin")).read_bytes(); man = json.loads((d / "manifest.json").read_text())
    e = E35(img, man)
    ptr = lambda store, k: (e.call(0x0803542C, store, k), e.uc.reg_read(UC_ARM_REG_R0))[1]
    def put(store, k, data):
        e.call(0x080354FA, store, k); e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0), data); e.uc.mem_write(ptr(store, k), data)
    chain = lambda t: bytes(e.uc.mem_read(ptr(e.r32(ENG + 0x9C), t), 2))
    press = lambda i: e.call(0x08033320, MGR, i, maxins=8_000_000)
    release = lambda i: e.call(0x0803381A, MGR, i, maxins=8_000_000)
    shift = lambda v: e.set_p0(e.r32(MGR + 0xC), v)
    pad = lambda q: (e.call(PRESS, MGR, q, 100, maxins=20_000_000), e.call(RELEASE, MGR, q, maxins=20_000_000))
    e.set_p0(e.r32(CONT + 0x188), 0); press(0); release(0)
    press(14); release(14)
    res = []
    for sc, (a, b) in ((0, (0, 1)), (1, (2, 3))):
        for t in (0, 1): put(e.r32(ENG + 0x9C), t, bytes([a, b]))
        shift(1); pad(16 + sc); shift(0)
    for sc in (0, 1, 0):
        pad(16 + sc); res.append((sc, chain(0).hex(), chain(1).hex()))
    # playing: scene 1 running, scene 2 asked for; the patterns that play on Synth 1 / Synth 2
    t = [500000]
    def at(ms): t[0] += ms; e.w32(HAL, t[0])
    def transport(on):
        for fn in (0x080354FA, 0x0803542C):
            e.call(fn, TRANSPORT, 0); e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0), bytes([on]))
    def setp(store, k, data): put(store, k, data)
    for k in range(8):
        st = e.r32(ENG + 0x30 + 4 * k)
        setp(st, 0, bytes([0])); setp(st, 1, bytes([0])); setp(st, 2, struct.pack("<I", 5))
        setp(e.r32(ENG + 0x70 + 4 * k), 1, bytes([0]))
    transport(1)
    seq = {0: [], 1: []}
    def clock():
        at(21); e.call(0x0802C418, ENG, maxins=5_000_000)
        for k in (0, 1):
            st = e.r32(ENG + 0x30 + 4 * k)
            if e.r32(ptr(st, 2)) == 0 and e.r8(ptr(st, 1)) == 0: seq[k].append(e.r8(ptr(st, 0)))
    for i in range(16 * 6 * 6):
        if i == 30: pad(17)                                       # scene 2 asked for while scene 1 plays
        clock()
    gc.collect()
    return res, seq


if __name__ == "__main__":
    for d in sys.argv[1:]:
        print(d, run(d))
