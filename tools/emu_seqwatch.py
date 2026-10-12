"""SEQWD tests (live RAM dump): rdiag.WATCH through the real route, the incoming SysEx dispatcher 0x0801EB30 (emu_sc35d8's harness), and the
DebugMonitor handler c_dmon.  Unicorn has no DWT and no debug exceptions: the system registers are plain memory here, and the handler is called with
a hand-made exception frame.

    python tools/emu_seqwatch.py SEQWD.bin SEQWD_manifest.json
  * ping: version $35D8 + $10 (DSPX) + $80 (WATCH);
  * watch ADDR read: DEMCR |= TRCENA | MON_EN (the rest kept), DWT LAR unlocked, FUNCTION0 = 0 before COMP0 / MASK0, then FUNCTION0 = 5; the reply
    gives DWT_CTRL, DEMCR, FUNCTION0 and the log's address (c_gst() + LOG_OFF); the log cleared;
  * the vector table: entry 12 (DebugMonitor) = c_dmon;
  * c_dmon with frames on MSP (EXC_RETURN bit 2 = 0): hits counted, the first LOG_N distinct PCs kept with their LR, a repeated PC not added;
    DFSR written with DWTTRAP (4), FUNCTION0 read; with PSP (bit 2 = 1) the frame is taken from PSP;
  * wlog: the hits and the pairs as logged; watch again: the log cleared; poke: RAM written, outside RAM = status 1.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_MEM_WRITE, UC_HOOK_MEM_READ
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc35d8 as T  # noqa: E402
import rdiag as RD  # noqa: E402
import ctremote as CR  # noqa: E402
from emu_sc05 import STOP  # noqa: E402

PPB = 0xE0000000


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["rdiag"]["labels"].items()}
    gst = int(man["report"]["sc14"]["labels"]["c_gst"], 16)
    check(struct.unpack_from("<I", img, RD.VEC_DEBUGMON - 0x08010000)[0] == L["c_dmon"] | 1, f"vector 12 (DebugMonitor) = c_dmon {L['c_dmon']:#x}")
    gc.collect(); e = T.E8(img, man)
    try: e.uc.mem_map(PPB, 0x100000)
    except Exception: pass
    e.uc.mem_write(RD.DWT_CTRL, struct.pack("<I", 0x40000000))                 # 4 comparators
    e.uc.mem_write(RD.DEMCR, struct.pack("<I", 0x00000400))                    # some other bit set
    sysw = []
    e.uc.hook_add(UC_HOOK_MEM_WRITE, lambda uc, acc, a, size, v, d: sysw.append((a, v)), begin=PPB, end=PPB + 0xFFFFF)
    sysr = []
    e.uc.hook_add(UC_HOOK_MEM_READ, lambda uc, acc, a, size, v, d: sysr.append(a), begin=PPB, end=PPB + 0xFFFFF)
    def payload(msg, cmd, seq=5):
        ok = msg[:4] == bytes(RD.SIG) and msg[4] == cmd | 0x40 and msg[5] == seq and msg[-1] == 0xF7 and all(b < 0x80 for b in msg[1:-1])
        return list(msg[6:-1]) if ok else None
    r = e.req(1); p = payload(r[2], 1)
    ver = RD.VERSION + 0x10 + 0x80
    check(CR.un32(p[:8]) == ver, f"ping: version {CR.un32(p[:8]):#x} (want {ver:#x})")
    e.call(gst); g = e.uc.reg_read(UC_ARM_REG_R0); log = g + RD.LOG_OFF
    e.uc.mem_write(log, bytes(range(1, 69)))                                   # garbage in the log
    W = 0x20011B24
    sysw.clear(); r = e.req(10, CR.nib32(W) + [5, 0]); d = CR.dec_watch(payload(r[2], 10))
    fn = [v for a, v in sysw if a == RD.DWT_COMP0 + 8]
    check(d["status"] == 0 and d["log"] == log and d["dwt_ctrl"] == 0x40000000, f"watch: status 0, the log at c_gst() + {RD.LOG_OFF} ({d['log']:#x}), DWT_CTRL read")
    check((RD.DEMCR, 0x01010400) in sysw and d["demcr"] == 0x01010400, f"DEMCR = TRCENA | MON_EN, the other bit kept ({d['demcr']:#x})")
    check((RD.DWT_LAR, 0xC5ACCE55) in sysw and (RD.DWT_COMP0, W) in sysw and (RD.DWT_COMP0 + 4, 0) in sysw and fn == [0, 5] and d["function0"] == 5,
          f"LAR unlocked, COMP0 = {W:#x}, MASK0 = 0, FUNCTION0 0 then 5 ({fn})")
    check(bytes(e.uc.mem_read(log, 68)) == bytes(68), "the log cleared")
    # the handler: frames on MSP (call() starts with SP = 0x2006F000 and LR = STOP | 1: bit 2 clear = MSP)
    def hit(pc, lr, psp=False):
        frame = struct.pack("<8I", 0, 0, 0, 0, 0, lr, pc, 0x01000000)
        if psp:
            e.uc.mem_write(0x2006E800, frame); e.uc.reg_write(UC_ARM_REG_PSP, 0x2006E800) if hasattr(sys.modules["unicorn.arm_const"], "UC_ARM_REG_PSP") else None
        else:
            e.uc.mem_write(0x2006F000, frame)
        sysw.clear(); sysr.clear(); e.call(L["c_dmon"], maxins=20000)
        return (RD.DFSR, 4) in sysw and RD.DWT_COMP0 + 8 in sysr
    pcs = [0x0803F000 + 0x10 * i for i in range(RD.LOG_N + 2)]
    oks = [hit(pc, 0x0802A001 + i) for i, pc in enumerate(pcs)] + [hit(pcs[1], 0x1234)]
    hits = struct.unpack("<I", bytes(e.uc.mem_read(log, 4)))[0]
    ent = [struct.unpack_from("<2I", bytes(e.uc.mem_read(log + 4 + 8 * i, 8))) for i in range(RD.LOG_N)]
    check(all(oks), "every hit: DFSR.DWTTRAP cleared, FUNCTION0 read")
    check(hits == RD.LOG_N + 3 and ent == [(pcs[i], 0x0802A001 + i) for i in range(RD.LOG_N)],
          f"{hits} hits, the first {RD.LOG_N} distinct PCs with their LR, a repeated PC not added, the 9th / 10th dropped")
    if hasattr(sys.modules["unicorn.arm_const"], "UC_ARM_REG_PSP"):
        e.uc.mem_write(log, bytes(68))
        frame = struct.pack("<8I", 0, 0, 0, 0, 0, 0x0802B001, 0x0802B100, 0x01000000); e.uc.mem_write(0x2006E800, frame)
        e.uc.reg_write(UC_ARM_REG_PSP, 0x2006E800)
        e.uc.reg_write(UC_ARM_REG_SP, 0x2006F000); e.uc.reg_write(UC_ARM_REG_LR, 0xFFFFFFFD)
        stop = []
        from unicorn import UC_HOOK_CODE
        h = e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s_, d: (stop.append(a), uc.emu_stop()) if a == L["c_dmon"] + 0x100000 else None)
        try:
            e.uc.emu_start(L["c_dmon"] | 1, 0, count=200)
        except Exception:
            pass
        e.uc.hook_del(h)
        got = struct.unpack_from("<2I", bytes(e.uc.mem_read(log + 4, 8)))
        check(got == (0x0802B100, 0x0802B001), f"EXC_RETURN with bit 2 set: the frame from PSP ({got[0]:#x}, {got[1]:#x})")
    r = e.req(12); d = CR.dec_wlog(payload(r[2], 12))
    check(d["status"] == 0 and d["hits"] == struct.unpack("<I", bytes(e.uc.mem_read(log, 4)))[0] and len(d["pcs"]) >= 1, f"wlog: {d['hits']} hits, {len(d['pcs'])} PCs")
    r = e.req(10, CR.nib32(W) + [0, 0]); d = CR.dec_watch(payload(r[2], 10))
    check(d["function0"] == 0 and bytes(e.uc.mem_read(log, 68)) == bytes(68), "watch off: FUNCTION0 = 0, the log cleared")
    r = e.req(11, CR.nib32(0x2004FFF0) + [4] + CR.nibbytes(b"\xDE\xAD\xBE\xEF")); p = payload(r[2], 11)
    check(CR.un32(p[:8]) == 0 and bytes(e.uc.mem_read(0x2004FFF0, 4)) == b"\xDE\xAD\xBE\xEF", "poke: 4 bytes of RAM written")
    r = e.req(11, CR.nib32(0x08010000) + [4] + CR.nibbytes(b"\x00\x00\x00\x00")); p = payload(r[2], 11)
    check(CR.un32(p[:8]) == 1 and bytes(img[:4]) == bytes(e.uc.mem_read(0x08010000, 4)), "poke outside RAM (the flash): status 1, nothing written")
    del e; gc.collect()
    print("SEQWD RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
