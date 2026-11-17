"""SC57.5 / Beta 5.60 tests: Clear + Duplicate twice in a track view = the pattern edited there back as the card has it (tools/patrev.py,
xlanes.use_reload()), on the RAM dump with emu_sc35's card / DSP model, through the controller (0x08033320 / 0x0803381A) and the LED task call.

    python tools/emu_patrev.py BUILD.bin manifest.json
  * Synth 1, Note view: the first Clear + Duplicate asks (nothing changes; Duplicate's LED blinks white), the second puts the card's pattern back:
    the steps, the lanes, the settings' bytes 0..7 (the stores follow: the settings store and the engine's), the settings' bytes 8..39 kept;
  * a question older than ~5 s: the next press asks again;
  * Drum 1, Velocity view: the pattern back with drumpat's bytes when the file has 'DQ', zeroed without it;
  * MIDI 1, Pattern Settings view: the pattern back and its extra lanes' block read again into the DSP by the LED task (bit set, the cached copy
    dropped); a file whose tail does not match: the block emptied;
  * refused (Save red, nothing changed): a new project never saved, a file shorter than the stock's 160 780 B;
  * not in Patterns nor Sidechain: the press goes on (no question);
  * the buffer lock balanced.
"""
from __future__ import annotations
import json, random, struct, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R4
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc35 import E35  # noqa: E402
from emu_sc05 import STOP  # noqa: E402
import packio as PK  # noqa: E402
import xlanes as XL  # noqa: E402
import patrev as PR  # noqa: E402

MGR, CONT, ENG = 0x20040B10, 0x20040DB8, 0x20038EC0
SES = XL.SESSION_OBJ
CLEAR, DUP = 23, 24
T_S1, T_M1, T_D1 = 0, 2, 4
V_PRESET, V_NOTE, V_VEL, V_GATE, V_PS, V_PATTERNS, V_FX = 8, 9, 10, 11, 12, 13, 15


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = E35(img, man)
    R = man["report"]
    cur = int(R["packio"]["labels"]["c_curpack"], 16)
    xst = int(R["xlanes"]["labels"]["c_xlst"], 16)
    press = lambda i: e.call(0x08033320, MGR, i, maxins=20_000_000)
    release = lambda i: e.call(0x0803381A, MGR, i, maxins=8_000_000)
    btn = lambda i: (press(i), release(i))
    def at(ms): e.w32(PK.HAL_TICK, ms)
    def frame():
        e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR)
        e.call(0x08033B3E, maxins=200_000_000)
        return struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138)))
    def p0(store, k=0):
        e.call(PK.PARAM_GET, store, k, maxins=100000); return e.uc.reg_read(UC_ARM_REG_R0)
    xlr = lambda o, n=1: bytes(e.uc.mem_read(XL.XLR + o, n))
    def setx(o, b): e.uc.mem_write(XL.XLR + o, bytes(b))

    at(100000)
    e.call(xst, maxins=10000)
    e.uc.mem_write(SDR := __import__("savedefer").RAM, b"SD01" + bytes([0, 0xA5]) + bytes(10))   # no save kept; byte +5 never
    # written by savedefer: the device's RAM is not cleared at power-up, so it holds garbage there
    rec = e.r32(SES + 0x14)
    slot = e.r8(p0(e.r32(XL.PROJ_OBJ + 0x20), 8))
    e.call(cur, maxins=100000); pk = e.uc.reg_read(UC_ARM_REG_R0) & 0xFF
    e.cur = pk                                                                    # the loaded pack: its items answer to its number and to 0xFF
    key = (XL.KIND_SES, slot, 0xFF)
    rnd = random.Random(11)
    card = bytearray(e.uc.mem_read(rec, XL.SZ0))
    e.sd[key] = bytes(card)
    print(f"slot {slot}, pack {pk:#x}")

    def edited(t):
        obj = PR.NOBJ + PR.NSTRIDE * t if t < 4 else PR.DOBJ + PR.DSTRIDE * (t - 4)
        return obj, e.r8(p0(e.r32(obj + (0x24 if t < 4 else 0x20))))
    def base(t, p):
        if t < 2: return rec + 0x2E4 + 0x6540 * t + PR.NLEN * p
        if t < 4: return rec + 0x1A27C + 0x6540 * (t - 2) + PR.NLEN * p
        return rec + 0xCD74 + 0x3540 * (t - 4) + PR.DLEN * p
    def edit_notes(b_):                                                          # a valid edit: notes in steps 0..7, lane values, the range
        n0 = rnd.randrange(36, 80)
        for st_ in range(8):
            e.uc.mem_write(b_ + 28 * st_, bytes([1, 7, 0, 0, n0 + st_, 6, 0, 100]))
        e.uc.mem_write(b_ + 0x3A8, bytes(rnd.randrange(128) for _ in range(64)))
        e.uc.mem_write(b_ + 0x380, bytes([rnd.randrange(8, 32), rnd.randrange(0, 8)]))
    def edit_drum(b_):                                                           # velocity, probability, flips, micro steps; settings 4..39; lane 0
        e.uc.mem_write(b_, bytes(rnd.randrange(128) for _ in range(32)) + bytes(rnd.randrange(8) for _ in range(32))
                       + bytes(rnd.randrange(16) for _ in range(32)) + bytes(rnd.randrange(64) for _ in range(32)))
        e.uc.mem_write(b_ + 0x84, bytes(rnd.randrange(8) for _ in range(0x24)))
        e.uc.mem_write(b_ + 0xA8, bytes(rnd.randrange(128) for _ in range(64)))
    def ask_and_confirm(dt=1000):
        t0 = e.r32(PK.HAL_TICK)
        press(CLEAR); press(DUP); release(DUP)
        asked = xlr(PR.O_T)[0]
        at(t0 + dt); press(DUP); release(DUP); release(CLEAR)
        return asked

    # ---- Synth 1, Note view
    btn(T_S1); btn(V_NOTE)
    obj, p = edited(T_S1); b = base(T_S1, p)
    good = bytes(card[b - rec:b - rec + PR.NLEN])
    keep = bytes(rnd.randrange(256) for _ in range(32))
    edit_notes(b); e.uc.mem_write(b + 0x388, keep)
    before = bytes(e.uc.mem_read(b, PR.NLEN))
    e.api.clear()
    press(CLEAR); press(DUP); release(DUP)
    check(xlr(PR.O_T)[0] == T_S1 + 1 and xlr(PR.O_P)[0] == p and bytes(e.uc.mem_read(b, PR.NLEN)) == before,
          f"Synth 1 Note: the first Clear + Duplicate asks (track {xlr(PR.O_T)[0]}, pattern {xlr(PR.O_P)[0]}), nothing changed")
    seen = set()
    for dt in (0, 128, 256, 384):
        at(100000 + dt); seen.add(frame()[PR.LED_DUP])
    check(seen == {0, PR.COL_ASK}, f"... Duplicate's LED blinks white ({sorted(hex(x) for x in seen)})")
    at(101000); press(DUP); release(DUP); release(CLEAR)
    now = bytes(e.uc.mem_read(b, PR.NLEN))
    check(now[:0x388] == good[:0x388] and now[0x3A8:] == good[0x3A8:], "... the second: the steps, the settings' bytes 0..7 and the lanes as on the card")
    check(now[0x388:0x3A8] == keep, "... the settings' bytes 8..39 kept (project data)")
    sp = p0(e.r32(obj + 0x1C)); ep = p0(e.r32(ENG + 0x50 + 4 * T_S1))
    check(e.r8(sp) == good[0x380] and e.r8(ep) == good[0x380], f"... the settings store and the engine's follow ({e.r8(sp):#x}, {e.r8(ep):#x}, card {good[0x380]:#x})")
    check(xlr(PR.O_T)[0] == 0 and any(x[0] == "read" and x[1] == (XL.KIND_SES, slot, pk) and x[2] == b - rec and x[3] == PR.NLEN for x in e.api),
          "... one read of that pattern at its offset in the file")
    check(e.lock == 0, f"... the buffer lock balanced ({e.lock})")

    # ---- a question too old
    edit_notes(b); before = bytes(e.uc.mem_read(b, PR.NLEN))
    ask_and_confirm(dt=7000)
    check(bytes(e.uc.mem_read(b, PR.NLEN)) == before and xlr(PR.O_T)[0] == T_S1 + 1, "after ~7 s the next press asks again (nothing changed)")
    at(110000); press(CLEAR); press(DUP); release(DUP); release(CLEAR)
    check(bytes(e.uc.mem_read(b, 0x388)) == good[:0x388], "... and a press within the time puts it back")

    # ---- Drum 1, Velocity view, with 'DQ' and without
    btn(T_D1); btn(V_VEL)
    dobj, dp = edited(T_D1); db = base(T_D1, dp)
    for dq in (True, False):
        c2 = bytearray(e.sd[key]); c2[0x2740A:0x2740C] = b"DQ" if dq else b"\x00\x00"
        c2[db - rec + 0x88:db - rec + 0xA8] = bytes(rnd.randrange(256) for _ in range(32)); e.sd[key] = bytes(c2)
        dgood = bytes(c2[db - rec:db - rec + PR.DLEN])
        edit_drum(db)
        at(e.r32(PK.HAL_TICK) + 10000); ask_and_confirm()
        now = bytes(e.uc.mem_read(db, PR.DLEN))
        exp = dgood if dq else dgood[:0x88] + bytes(32) + dgood[0xA8:]
        check(now == exp, f"Drum 1 Velocity, file {'with' if dq else 'without'} 'DQ': the pattern back"
              + ("" if dq else ", drumpat's bytes zeroed") + f" ({sum(x != y for x, y in zip(now, exp))} bytes differ)")
    check(e.lock == 0, f"... the buffer lock balanced ({e.lock})")

    # ---- MIDI 1, Pattern Settings view: the pattern and its extra lanes' block
    btn(T_M1); btn(V_PS)
    mobj, mp = edited(T_M1); mb = base(T_M1, mp); blk = mp
    lsum = 0x12345678
    blkdata = bytes(rnd.randrange(256) for _ in range(XL.BLK))
    c3 = bytearray(e.sd[key]) + bytearray(XL.HDR + XL.DATA)
    struct.pack_into("<IHHII", c3, XL.SZ0, XL.MAGIC, 1, 1 << blk, lsum, XL.DATA)
    c3[XL.SZ0 + XL.HDR + XL.BLK * blk:XL.SZ0 + XL.HDR + XL.BLK * (blk + 1)] = blkdata
    e.sd[key] = bytes(c3)
    mgood = bytes(c3[mb - rec:mb - rec + PR.NLEN])
    e.uc.mem_write(XL.XLR + XL.O_LSUM, struct.pack("<I", lsum))
    setx(XL.O_MAP, b"\x00\x00"); setx(XL.O_CM, bytes([blk + 1])); setx(XL.O_CM + 2, b"\x01"); setx(XL.O_CM + 4, b"\x00")
    xb = XL.XB + XL.BLKW * blk
    for i in range(XL.BLKW): e.ext[xb + i] = 0x777700
    edit_notes(mb)
    at(e.r32(PK.HAL_TICK) + 10000); ask_and_confirm()
    now = bytes(e.uc.mem_read(mb, PR.NLEN))
    check(now[:0x388] == mgood[:0x388], "MIDI 1 Pattern Settings: the pattern back")
    check(xlr(XL.O_RQ)[0] == blk + 1, f"... its extra lanes' block asked of the LED task ({xlr(XL.O_RQ)[0]})")
    frame()
    got = bytes(b_ for i in range(XL.BLKW) for b_ in struct.pack("<H", (e.ext.get(xb + i, 0) >> 8) & 0xFFFF))
    m_ = struct.unpack_from("<H", xlr(XL.O_MAP, 2))[0]
    check(got[:XL.BLK] == blkdata[:XL.BLK] and m_ >> blk & 1 and xlr(XL.O_RQ)[0] == 0,
          f"... the LED task: the block from the card into the DSP, its bit set ({m_:#x})")
    ic = bytes(e.uc.mem_read(XL.IC0, XL.BLK))                                  # (SC57.8: use_editcache refills the cache from the reloaded block, stopped)
    check(xlr(XL.O_CM + 2)[0] == 0 and (xlr(XL.O_CM)[0] == 0 or xlr(XL.O_CM)[0] == blk + 1 and ic == blkdata[:XL.BLK]),
          "... its cached copy dropped or refilled from the card's block (cached, changed)")
    # a tail that does not match: the block emptied
    e.uc.mem_write(XL.XLR + XL.O_LSUM, struct.pack("<I", lsum ^ 1)); e.uc.mem_write(XL.XLR + XL.O_SSUM, struct.pack("<I", lsum ^ 2))
    at(e.r32(PK.HAL_TICK) + 10000); ask_and_confirm(); frame()
    m_ = struct.unpack_from("<H", xlr(XL.O_MAP, 2))[0]
    check(not m_ >> blk & 1 and xlr(XL.O_RQ)[0] == 0, f"... a file whose tail is another's: the block emptied ({m_:#x})")
    e.uc.mem_write(XL.XLR + XL.O_SSUM, struct.pack("<I", lsum))
    at(e.r32(PK.HAL_TICK) + 10000); ask_and_confirm(); frame()
    m_ = struct.unpack_from("<H", xlr(XL.O_MAP, 2))[0]
    check(m_ >> blk & 1, f"... the checksum of the last save accepted too ({m_:#x})")
    check(e.lock == 0 and e.sem == 0, f"... the lock and the DSP semaphore balanced ({e.lock}, {e.sem})")

    # ---- refusals
    btn(T_S1); btn(V_GATE)
    obj, p = edited(T_S1); b = base(T_S1, p)
    setx(XL.O_NB, b"\x01"); edit_notes(b); before = bytes(e.uc.mem_read(b, PR.NLEN))
    t1 = e.r32(PK.HAL_TICK) + 10000; at(t1); ask_and_confirm()
    f = frame()
    check(bytes(e.uc.mem_read(b, PR.NLEN)) == before and f[PR.LED_SAVE] == PR.COL_NO, f"a new project never saved: refused, Save red ({f[PR.LED_SAVE]:#x})")
    at(t1 + 1000 + 2000); f = frame()
    check(f[PR.LED_SAVE] != PR.COL_NO, f"... the red gone after ~1.5 s ({f[PR.LED_SAVE]:#x})")
    check(xlr(PR.O_FAIL, 2) == bytes(2), "... and the refusal cleared (it never comes back)")
    setx(XL.O_NB, b"\x00")
    full = e.sd[key]; e.sd[key] = full[:XL.SZ0 - 4]
    at(e.r32(PK.HAL_TICK) + 10000); ask_and_confirm()
    check(bytes(e.uc.mem_read(b, PR.NLEN)) == before, "a file shorter than 160 780 B: refused")
    e.sd[key] = full
    check(e.lock == 0, f"... the buffer lock balanced ({e.lock})")

    # ---- elsewhere: no question
    for name, seq in (("Patterns", (V_PATTERNS,)), ("Sidechain", (T_S1, V_FX, V_FX))):
        for i in seq: btn(i)
        setx(PR.O_T, b"\x00")
        press(CLEAR); press(DUP); release(DUP); release(CLEAR)
        extra = f" (sub-view {e.r8(CONT + PR.SUB)})" if name == "Sidechain" else ""
        check(xlr(PR.O_T)[0] == 0, f"{name}: Clear + Duplicate goes on, no question{extra}")
    return fails


if __name__ == "__main__":
    img = Path(sys.argv[1]).read_bytes(); man = json.loads(Path(sys.argv[2]).read_text())
    n = main(img, man)
    print("RESULT:", "PASS" if n == 0 else f"{n} FAIL")
    sys.exit(1 if n else 0)
