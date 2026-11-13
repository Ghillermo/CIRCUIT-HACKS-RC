"""SC56.8 / Beta 5.53 tests: the black box v2 (tools/blackbox.py use_v2): the fault, stall and watchdog-restart captures.  The emulated firmware
(emu_lazysave's harness), a fake exception frame in RAM, the SCB fault registers and RCC_CSR written in the emulated peripherals:
  * the vectors 3-6 and 15 point at the stubs, which end in the stock's handlers;
  * a fault (c_bbfltc: vector 5, EXC_RETURN 0xFFFFFFFD, the frame): frozen FAULT, the frame's PC / LR / r0-r3 / r12 / xPSR, CFSR / HFSR, BFAR (CFSR
    bit 7 clear) or MMFAR (set), the vector and EXC_RETURN, the running TCB and its copy, 384 B of the stack from the frame, the main loop's task's
    stack; a second fault changes nothing; the restart (the main loop's clock back): RESET added, RCC_CSR kept and its flags cleared (RMVF);
  * a stall (c_bbsysc): nothing before STALL2_MS without the main loop, frozen STALL at it (the frame's PC / LR), a sample every 50 ms; the main
    loop running again = dropped; a stall then a restart = kept (RESET); a heartbeat from before a restart (later than the clock) = nothing;
  * a restart with IWDGRSTF and nothing frozen: WARM, the last tick before it; without it: nothing frozen;
  * the SysTick stub end to end (mrs, the stock's HAL_IncTick: the clock + 1).

    python tools/emu_blackbox2.py IMAGE.bin manifest.json
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_SP
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
import blackbox as BX  # noqa: E402

O, O2 = BX.O, BX.O2
TCB, MTCB, FRAME, MSTK = 0x2004F600, 0x2004F660, 0x2004F700, 0x2004F780
PCF, LRF = 0x0804A11C, 0x08036F05


def main(img_path, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    img = Path(img_path).read_bytes()
    R = man["report"]["blackbox"]
    lab = {k: int(v, 16) for k, v in R["labels"].items()}
    prev = {k: int(v, 16) for k, v in R["prev"].items()}
    vec = lambda v: struct.unpack_from("<I", img, 4 * v)[0]
    check(all(vec(v) == lab[f"c_bbv{v}"] | 1 for v in BX.FAULT_VECS) and vec(15) == lab["c_bbsys"] | 1
          and prev["vec3"] == 0x08059960 and prev["vec15"] == 0x0805998C, "the vectors 3-6 / 15: the stubs, the stock's handlers after them")
    e = T.EL(img)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1),
                  begin=prev["svc"] & ~1, end=prev["svc"] & ~1)
    r8 = lambda o: e.r8(BX.BB + o)
    r32 = lambda o: e.r32(BX.BB + o)
    def tick(ms): e.at(ms); e.call(lab["c_bbtick"], maxins=3_000_000)
    def setst(v): e.uc.mem_write(BX.BB + O.ST, bytes([v])); e.uc.mem_write(BX.BB + O.NS, b"\0")
    frame = [0x11, 0x22, 0x33, 0x44, 0x1212, LRF, PCF, 0x21000000] + [0x08050001 + 2 * i for i in range(100)]
    e.uc.mem_write(FRAME, struct.pack(f"<{len(frame)}I", *frame))
    e.uc.mem_write(TCB, struct.pack("<I", FRAME) + b"UI\0\0" + bytes(range(8, 0x5C)))
    mstk = list(range(0x2000, 0x2008)) + [0xFFFFFFFD, 0, 0, 0, 0, 0, 0x0802C001, 0x0802C418, 0x01000000] + [0] * 40
    e.uc.mem_write(MTCB, struct.pack("<I", MSTK) + bytes(0x58)); e.uc.mem_write(MSTK, struct.pack(f"<{len(mstk)}I", *mstk))
    e.w32(BX.CUR_TCB, MTCB)
    tick(100000)
    check(r32(0) == BX.SIG and r8(O.FMT) == 2 and r32(O2.MTCB) == MTCB, f"signed, format 2, the main loop's task kept ({r32(O2.MTCB):#x})")

    # ---- a fault
    e.w32(BX.CUR_TCB, TCB)
    e.w32(BX.SCB_CFSR, 0x00008200); e.w32(BX.SCB_CFSR + 4, 0x40000000); e.w32(BX.SCB_CFSR + 12, 0xAAAA0000); e.w32(BX.SCB_CFSR + 16, 0x2005F494)
    e.at(100010); e.call(lab["c_bbfltc"], 5, 0xFFFFFFFD, FRAME, maxins=3_000_000)
    st = r8(O.ST)
    check(st == BX.ST_FROZEN | BX.ST_FAULT, f"a BusFault: frozen FAULT ({st})")
    regs = [r32(O.PC + 4 * k) for k in range(8)]
    check(r32(O2.RPC) == PCF and r32(O2.RLR) == LRF and regs == [PCF, LRF, 0x11, 0x22, 0x33, 0x44, 0x1212, 0x21000000] and r8(O.NS) == 4,
          f"the frame: PC / LR, r0-r3, r12, xPSR ({[hex(x) for x in regs]})")
    check(r32(O2.CFSR) == 0x8200 and r32(O2.HFSR) == 0x40000000 and r32(O2.FADR) == 0x2005F494 and r32(O2.XTRA) == 5 | 0xFD << 8,
          f"CFSR / HFSR, BFAR (no MMARVALID), the vector and EXC_RETURN ({r32(O2.FADR):#x}, {r32(O2.XTRA):#x})")
    check(r32(O2.RTCB) == TCB and bytes(e.uc.mem_read(BX.BB + O.TCB + 4, 2)) == b"UI" and r32(O.LTOS) == FRAME
          and bytes(e.uc.mem_read(BX.BB + O.STK1, BX.N_STK1)) == bytes(e.uc.mem_read(FRAME, BX.N_STK1)),
          "the running TCB and its copy, 384 B of the stack from the frame")
    check(r32(O.ITOS) == MSTK and bytes(e.uc.mem_read(BX.BB + O.STK2, BX.N_STK2)) == bytes(e.uc.mem_read(MSTK, BX.N_STK2)),
          "176 B of the main loop's task's stack")
    e.w32(BX.SCB_CFSR, 0x00000082)
    e.call(lab["c_bbfltc"], 3, 0xFFFFFFF9, FRAME + 8, maxins=3_000_000)
    check(r8(O.ST) == st and r32(O2.CFSR) == 0x8200, "a second fault: nothing changes")
    tick(100020)
    check(r8(O.ST) == st, "the main loop still running: the fault stays")
    e.w32(BX.RCC_CSR, 0x24000000)
    tick(300)
    csr = e.r32(BX.RCC_CSR)
    check(r8(O.ST) == st | BX.ST_RESET and r32(O2.CSR) == 0x24000000 and csr & BX.CSR_RMVF,
          f"the restart: RESET added, RCC_CSR kept ({r32(O2.CSR):#x}), its flags cleared (RMVF written: {csr:#x})")

    # ---- a stall
    setst(0); e.w32(BX.CUR_TCB, MTCB); tick(1000); e.w32(BX.CUR_TCB, TCB)
    def sys_at(ms): e.at(ms); e.call(lab["c_bbsysc"], 0, 0xFFFFFFFD, FRAME, maxins=3_000_000)
    sys_at(1000 + BX.STALL2_MS - 1)
    check(r8(O.ST) == 0, f"{BX.STALL2_MS - 1} ms without the main loop: nothing")
    sys_at(1000 + BX.STALL2_MS)
    check(r8(O.ST) == BX.ST_FROZEN | BX.ST_STALL and r32(O2.RPC) == PCF and r8(O.NS) == 1 and r32(O.STALL) == BX.STALL2_MS,
          f"{BX.STALL2_MS} ms: frozen STALL, the running task's PC ({r8(O.ST)}, {r32(O2.RPC):#x})")
    t1 = 1000 + BX.STALL2_MS
    sys_at(t1 + 49); n49 = r8(O.NS); sys_at(t1 + 50); n50 = r8(O.NS)
    check(n49 == 1 and n50 == 2 and r32(O.PC + 8) == PCF, f"a sample every 50 ms ({n49}, {n50})")
    tick(t1 + 60)
    check(r8(O.ST) == 0, f"the main loop runs again: the stall dropped ({r8(O.ST)})")
    sys_at(t1 + 60 + BX.STALL2_MS)
    check(r8(O.ST) == BX.ST_FROZEN | BX.ST_STALL, "a stall again")
    e.w32(BX.RCC_CSR, 0x20000000); tick(200); tick(210)
    check(r8(O.ST) == BX.ST_FROZEN | BX.ST_STALL | BX.ST_RESET, f"then a restart: kept, RESET added ({r8(O.ST)})")
    setst(0); e.uc.mem_write(BX.BB + O.NOW, struct.pack("<I", 90000)); e.call(lab["c_bbsysc"], 0, 0xFFFFFFFD, FRAME, maxins=3_000_000)
    check(r8(O.ST) == 0, "a heartbeat from before a restart (later than the clock): nothing")

    # ---- a watchdog restart with nothing frozen
    def clean(): setst(0); e.w32(BX.RCC_CSR, 0); e.uc.mem_write(BX.BB + O.NOW, bytes(4))        # (the emulated RCC_CSR keeps its flags after RMVF)
    clean(); tick(5000); e.w32(BX.RCC_CSR, 0x20000000); tick(40)
    check(r8(O.ST) == BX.ST_FROZEN | BX.ST_WARM | BX.ST_RESET and r32(O.FT) == 5000 and r32(O2.CSR) == 0x20000000,
          f"IWDGRSTF: frozen WARM, the last tick before it ({r8(O.ST)}, {r32(O.FT)})")
    clean(); tick(5000); e.w32(BX.RCC_CSR, 0x14000000); tick(40)
    check(r8(O.ST) == 0, "a pin / power restart: nothing frozen")

    # ---- the SysTick stub end to end
    setst(0); tick(9000)
    h0 = e.r32(BX.HAL_TICK)
    try:
        e.uc.reg_write(UC_ARM_REG_SP, 0x2006F000); e.call(lab["c_bbsys"], maxins=200_000); ok = True
    except Exception as ex:
        ok = repr(ex)
    check(ok is True and e.r32(BX.HAL_TICK) == h0 + 1 and r8(O.ST) == 0, f"the SysTick stub: on to HAL_IncTick (the clock + 1), nothing frozen ({ok})")
    del e; gc.collect()
    print(f"{Path(img_path).stem} BLACKBOX2 RESULT: {'ALL PASS' if not fails else f'{fails} FAILURES'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text())) else 0)
