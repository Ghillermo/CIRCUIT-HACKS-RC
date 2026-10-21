"""SC45.7 / RC2.05 (tools/kbguard.py): the note tracks' pad LEDs never written out of their buffer.

The emulated firmware, the custom scale set by c_csput and the keyboard rebuilt by the real LED task; then Synth 1's track view redraws its held step
and its sounding notes through its store listener 0x0804B272 (the route the stock takes when a note sounds; stopped after the redraw 0x0804AE96,
the rest waits for the sound path):
  * a custom scale of period 1 (every note in it, the keyboard covers 24..79): note 100 sounding -> index 0xFF at 0x0804AE66; the previous build
    writes the LED buffer + 0x1FE (inside Synth 2's track view) and a stray pad through the link it reads past the table ([0x20041044 + 0x27F]),
    this one nothing out of the buffer and no stray pad; note 60 still lights its pad;
  * the moment after a change (the quantiser on the new scale, the keyboard still on the old one): the same;
  * the stock's major scale: the same pads lit as the previous build.

    python tools/emu_kbguard.py BUILD.bin manifest.json [PREVIOUS.bin PREVIOUS_manifest.json]
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_R0, UC_ARM_REG_R1
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_cscale as ECS  # noqa: E402
import cscale as CS  # noqa: E402

TV = 0x200412E0                                   # Synth 1's track view
LISTENER, AFTER_REDRAW = 0x0804B272, 0x0804B2DC
SET_LED, AE66 = 0x0804AA48, 0x0804AE66


def run(path, man, keys, notes, change=None):
    """-> (the indices 0x0804AE66 got, the LED writes out of the buffer, the LED writes in it)"""
    img = bytearray(Path(path).read_bytes())
    lab = {k: int(v, 16) for k, v in man["report"]["cscale"]["labels"].items()}
    e = ECS.EC(img, lab); e.at(100000); e.transport(0)
    e.frame(shift=True); e.sbtn(CS.ID_SCALES)
    if keys: e.put_keys(keys); e.frame()
    if change: e.put_keys(change)                 # no LED frame: the keyboard still holds the old scale
    buf = e.r32(e.r32(TV + 4))
    e.call(0x08035418, e.r32(TV + 0x30)); p = e.uc.reg_read(UC_ARM_REG_R0)
    w = [0, 0, 0, 0]
    for n in notes: w[n >> 5] |= 1 << (n & 31)
    e.uc.mem_write(p, struct.pack("<4I", *w))
    idx, out, inn = [], [], {}
    def wh(uc, acc, addr, size, val, d):
        if uc.reg_read(UC_ARM_REG_PC) == SET_LED:
            if buf <= addr < buf + 448: inn[(addr - buf) // 2] = val
            else: out.append(addr - buf)
    e.uc.hook_add(UC_HOOK_MEM_WRITE, wh)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: idx.append(uc.reg_read(UC_ARM_REG_R1)), begin=AE66, end=AE66)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: uc.emu_stop(), begin=AFTER_REDRAW, end=AFTER_REDRAW)
    e.call(LISTENER, TV, e.r32(TV + 0x2C), 0, maxins=8_000_000)
    del e; gc.collect()
    return idx, out, inn


def main(img, man, prev=None, pman=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    cases = [("period 1, note 100 sounding", [1], [60, 100], None),
             ("right after a change (major -> period 1), note 100", [2, 4, 5, 7, 9, 11, 12], [60, 100], [1]),
             ("the major scale made by hand, notes 60 / 64 / 67", [2, 4, 5, 7, 9, 11, 12], [60, 64, 67], None)]
    for name, keys, notes, change in cases:
        idx, out, inn = run(img, man, keys, notes, change)
        bad = [i for i in idx if i >= 224]
        check(not out, f"{name}: no LED write out of the buffer (indices {sorted(set(idx))})")
        if prev:
            pidx, pout, pinn = run(prev, pman, keys, notes, change)
            if bad: check(0x1FE in pout, f"{name}: the previous build writes the buffer + 0x1FE ({[hex(a) for a in sorted(set(pout))]})")
            extra = sorted(set(pinn) - set(inn))
            same = all(pinn.get(k) == v for k, v in inn.items()) and (not extra or bad)
            check(same, f"{name}: the pads lit as the previous build ({len(inn)}; the previous one also lit {extra} through the link of 0xFF)")
        check(any(v for v in inn.values()) or not idx, f"{name}: the notes on the keyboard still light their pads")
    print(f"{Path(img).stem} RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text()), a[2] if len(a) > 2 else None,
                       json.loads(Path(a[3]).read_text()) if len(a) > 3 else None) else 0)
