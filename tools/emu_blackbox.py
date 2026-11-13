"""SC56.6 / Beta 5.51 tests: the black box (tools/blackbox.py) through the real routes: the controller's entries (buttons, pads, knobs), the LED
task (0x08033B3E -> its calls), the head of the DSP service chain (the rest of the chain skipped), the incoming SysEx dispatcher (emu_sc35d8's
harness) and the USB parser (emu_sdsysex).  No RTOS here: pxCurrentTCB (0x20006138) points at a fake TCB whose saved stack holds a known frame.

    python tools/emu_blackbox.py IMAGE.bin manifest.json
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_LR, UC_ARM_REG_PC
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import blackbox as BX  # noqa: E402
import rdiag as RD  # noqa: E402
import packio as PK  # noqa: E402
import build_sc14 as S14  # noqa: E402

O = BX.O
TCB, TOS = 0x2004F600, 0x2004F680
PC0, LR0 = 0x0803ABCC, 0x0803ABCD


def bw(img, a): import mpatch as MP; return MP.bw_target(img, a, 0x08010000)


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    R = man["report"]["blackbox"]
    lab = {k: int(v, 16) for k, v in R["labels"].items()}
    prev = {k: int(v, 16) for k, v in R["prev"].items()}
    import fxdiag as FD
    hooks = [bw(img, S14.SVC_HOOK) == lab["c_bbtick"], bw(img, RD.HOOK) == lab["c_bbsx"]]
    kh = man["report"].get("knobhold", {}).get("prev", {})                                # SC56.7: knobhold's heads in front of the LED calls / the knob entry
    led_at = lambda c: FD.bl_target(img, c, 0x08010000)
    hooks += [(led_at(c) == lab["c_bbled"]) or (kh and int(kh["ledtask"], 16) == lab["c_bbled"]) for c in PK.LED_CALLS]
    mh = man["report"].get("mfxhold", {}).get("prev", {})                                 # SC57.1: mfxhold's heads in front of the button press / release
    mh_at = {0x08033320: "btn", 0x0803381A: "rel"}
    hooks += [(bw(img, a) == lab[f"c_bbin{k}"]) or (kh and a == 0x08033848 and int(kh["knob"], 16) == lab[f"c_bbin{k}"])
              or (mh and a in mh_at and int(mh[mh_at[a]], 16) == lab[f"c_bbin{k}"]) for a, k in BX.ENTRIES]
    check(all(hooks), f"the hooks: service head, SysEx, the LED task's two calls, the 5 input entries ({hooks})")
    e = T.EL(img)
    def skip(uc): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: skip(uc), begin=prev["svc"] & ~1, end=prev["svc"] & ~1)
    rst = []
    def wr(uc, acc, a, s, v, d):
        if a == BX.AIRCR: rst.append(v); uc.emu_stop()
    e.uc.hook_add(UC_HOOK_MEM_WRITE, wr, begin=BX.AIRCR, end=BX.AIRCR + 3)
    r8 = lambda o: e.r8(BX.BB + o)
    r32 = lambda o: e.r32(BX.BB + o)
    def tick(ms): e.at(ms); e.call(lab["c_bbtick"], maxins=3_000_000)
    led = lambda: X.frame(e)[BX.LED_SAVE] & 0xFF
    # a fake TCB whose saved stack holds r4-r11, EXC_RETURN (no FP), r0-r3, r12, LR, PC, xPSR, then a caller's frame
    stk = list(range(0x1000, 0x1008)) + [0xFFFFFFFD, 1, 2, 3, 4, 12, LR0, PC0, 0x01000000] + [0x08040001 + 2 * i for i in range(80)]
    e.uc.mem_write(TCB, struct.pack("<I", TOS) + bytes(range(4, 0x5C)))
    e.uc.mem_write(TOS, struct.pack(f"<{len(stk)}I", *stk))
    e.w32(BX.CUR_TCB, TCB)
    tick(100000)
    check(r32(0) == BX.SIG and r8(O.ST) == 0 and r8(O.FMT) == (2 if "c_bbsys" in lab else 1), f"signed, nothing frozen ({r32(0):#x}, state {r8(O.ST)})")
    tick(100001); n0 = r32(O.LFN); X.frame(e); X.frame(e)
    check(r32(O.LFN) == n0 + 2 and r32(O.LF1) == 100001 and r32(O.LTCB) == TCB, f"two LED frames: counted, the time, the task ({r32(O.LFN) - n0}, {r32(O.LTCB):#x})")
    ri0 = r8(O.RI)
    e.btn(2); e.pad(5)
    for _ in range(4): e.call(0x08033848, T.MGR, 3, 1, maxins=8_000_000)
    ents = []
    for i in range(r8(O.RI) - ri0):
        b_ = BX.BB + O.RING + 8 * ((ri0 + i) & 15)
        ents.append((e.r8(b_ + 4), e.r8(b_ + 5)))
    want = [(BX.K_PRESS, 2), (BX.K_RELEASE, 2), (BX.K_PAD, 5), (BX.K_PADUP, 5), (BX.K_KNOB, 3)]
    check(ents == want, f"the breadcrumbs: button 2 down / up, pad 5 down / up, knob 3 x 4 folded into one: {ents}")
    view = e.r32(T.MGR + 0x6C) & 0xFFFF
    b_ = BX.BB + O.RING + 8 * ((ri0 + 4) & 15)
    check(struct.unpack("<H", bytes(e.uc.mem_read(b_ + 6, 2)))[0] == view and r32(O.ITCB) == TCB, "an entry keeps the view's address and the input task")
    # stopped: no freeze however long; playing since after the last frame: none either
    tick(100002); X.frame(e)
    for t in (120000, 200000): tick(t)
    check(r8(O.ST) == 0, "stopped, 100 s without a frame: nothing frozen")
    e.transport(1); tick(200001)
    for t in (210000, 240000): tick(t)
    check(r8(O.ST) == 0, "playing, but started after the last frame: nothing frozen")
    e.at(240002); X.frame(e)
    tick(240003); tick(240003 + BX.STALL_MS - 2)
    check(r8(O.ST) == 0, f"playing, {BX.STALL_MS - 5} ms without a frame: nothing")
    tick(240002 + BX.STALL_MS)
    st = r8(O.ST)
    check(st == BX.ST_FROZEN | BX.ST_PLAY, f"playing, {BX.STALL_MS} ms without a frame: frozen ({st})")
    check(r32(O.FT) == 240002 + BX.STALL_MS and r32(O.STALL) == BX.STALL_MS and r32(O.VIEW) == e.r32(T.MGR + 0x6C),
          f"the time, the stall, the view ({r32(O.FT)}, {r32(O.STALL)}, {r32(O.VIEW):#x})")
    tcb = bytes(e.uc.mem_read(BX.BB + O.TCB, BX.N_TCB)); s1 = bytes(e.uc.mem_read(BX.BB + O.STK1, BX.N_STK1))
    s2 = bytes(e.uc.mem_read(BX.BB + O.STK2, BX.N_STK2))
    allstk = struct.pack(f"<{len(stk)}I", *stk)
    check(tcb == struct.pack("<I", TOS) + bytes(range(4, 0x5C)) and r32(O.LTOS) == TOS and s1 == allstk[:BX.N_STK1],
          "the TCB and 384 B of the saved stack copied")
    check(r32(O.ITOS) == TOS + BX.N_STK1 and s2 == bytes(e.uc.mem_read(TOS + BX.N_STK1, BX.N_STK2)), "the same task: its stack goes on in the second copy")
    nm = BX.N_MGR1_V2 if r8(O.FMT) == 2 else 64                                             # (v2: 32 B, the rest are the fault fields)
    check(bytes(e.uc.mem_read(BX.BB + O.MGR1, nm)) == bytes(e.uc.mem_read(T.MGR + 0x60, nm)), f"{nm} B of the controller")
    check(r8(O.NS) == 1 and r32(O.PC) == PC0 and r32(O.PC + 4) == LR0, f"sample 0: the saved PC / LR ({r32(O.PC):#x}, {r32(O.PC + 4):#x})")
    ri1 = r8(O.RI); e.btn(3); X.frame(e)
    check(r8(O.RI) == ri1 and r32(O.LF1) == 240002, "frozen: no breadcrumb, no frame time")
    t0 = 240002 + BX.STALL_MS
    for k in range(1, BX.NSAMP):
        tick(t0 + 50 * k - 1); tick(t0 + 50 * k)
    check(r8(O.NS) == BX.NSAMP and not rst, f"{BX.NSAMP} samples 50 ms apart, no restart yet")
    tick(t0 + 50 * BX.NSAMP)
    check(rst == [BX.RESET_KEY] and r8(O.ST) & BX.ST_RESET, f"then SYSRESETREQ ({[hex(v) for v in rst]}), state {r8(O.ST)}")
    # the restart: the clock back to 0, the record kept, Save blinking violet for SHOW_MS
    tick(200); s0 = r8(O.ST)
    e.at(200); c1 = led(); e.at(300); c2 = led(); e.at(BX.SHOW_MS + 200); c3 = led()
    check(s0 == st | BX.ST_RESET and c1 == BX.COL_SHOW and c2 == 0 and c3 != BX.COL_SHOW,
          f"after the restart: the record kept, Save violet / dark for 30 s ({c1:#x}, {c2:#x}, then {c3:#x})")
    rec = bytes(e.uc.mem_read(BX.BB, BX.SIZE))
    del e; gc.collect()
    # SysEx: read, clear, capture; the rest forwarded (fwid still answers)
    import emu_sc35d8 as D
    f = D.E8(img, man)
    f.uc.mem_write(BX.BB, rec)
    def read(c, port=0):
        f.sysex(list(RD.SIG) + [1, 0x23, c, 0] + [0] * 128 + [0xF7], port)
        return f.out[0][2] if len(f.out) == 1 else None
    got = b""
    for c in range(BX.SIZE // BX.CHUNK):
        m = read(c)
        if not m or len(m) != BX.LEN_READ or m[4] != 0x41 or m[6] != c or m[7] != 1: break
        got += bytes(m[8 + 2 * i] << 4 | m[9 + 2 * i] for i in range(BX.CHUNK))
    check(got == rec, f"read over SysEx: 16 chunks = the record ({len(got)} B)")
    m = read(16)
    check(m is not None and m[7] == 0 and set(m[8:136]) == {0}, "chunk 16: none (format 0, zeros)")
    def cmd(k):
        f.sysex(list(RD.SIG) + [k, 0x24] + [0] * 7 + [0xF7], 1)
        return f.out[0][2] if len(f.out) == 1 else None
    m = cmd(2)
    check(m == bytes(list(RD.SIG) + [0x42, 0x24, 1] + [0] * 6 + [0xF7]) and f.r32(BX.BB) == BX.SIG and f.r8(BX.BB + O.ST) == 0
          and not any(f.uc.mem_read(BX.BB + 8, BX.SIZE - 8)), "clear: answered, the record zeroed, signed")
    f.w32(BX.CUR_TCB, 0)
    m = cmd(3)
    check(m is not None and m[4] == 0x43 and m[7] == BX.ST_FROZEN | BX.ST_MANUAL and f.r8(BX.BB + O.ST) == BX.ST_FROZEN | BX.ST_MANUAL,
          f"freeze now: answered with the state ({m[7] if m else None})")
    m = cmd(0)
    check(m is not None and m[4] == 0x40 and f.fwd == 0, "command 0 goes on to fwid (its reply)")
    f.sysex(list(RD.SIG) + [1, 1] + [0] * 7 + [0xF7], 1)
    check(f.fwd == 1 and not f.out, "a read of the wrong length: forwarded, no reply")
    del f; gc.collect()
    import emu_sdsysex as XS
    fw = XS.Fw(image=bytes(img), fs=XS.PyFat()); fw.boot_storage()
    out = [bytes(x) for x in fw.usb_feed(bytes(list(RD.SIG) + [1, 0x25, 0, 0] + [0] * 128 + [0xF7]))]
    check(len(out) == 1 and len(out[0]) == BX.LEN_READ and out[0][4] == 0x41 and out[0][7] == 1,
          f"over USB (the real parser): a 137-byte read answered ({[len(x) for x in out]})")
    del fw; gc.collect()
    print(f"{man.get('marker', '?')} BLACKBOX RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text())) else 0)
