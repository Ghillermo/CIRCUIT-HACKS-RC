"""SC35D8 tests: the remote SysEx diagnostics (tools/rdiag.py) through the real route, the incoming SysEx dispatcher 0x0801EB30(port, msg), on the RAM dump.
The stock content API (exists / size / read / write) and the SysEx output router 0x08020C90 are stubbed; reaching 0x0801EB34 = forwarded to the stock dispatcher.

    python tools/emu_sc35d8.py SC35D8.bin SC35D8_manifest.json
  * the hook: the first 4 bytes of 0x0801EB30 = b.w c_rdin; a foreign SysEx (identity request) runs the original prologue and goes on (no reply of ours);
  * an unpadded request of ours is swallowed without a reply (nothing is written past the buffer);
  * ping (ports 0 / 1): VERSION and the port, through the stock router with the router object and mask 1 << port;
  * mem: flash and RAM bytes; outside flash / RAM = status 1; the length is clamped to NMAX;
  * info / read / write: the API gets the item (kind, idx, pack; 0x7F -> 0xFF), offset, length, synchronous (cb = 0); write gets exactly the bytes sent;
  * an unknown command = status 0xFFFFFFFF.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc19_1 as T  # noqa: E402
import rdiag as RD  # noqa: E402
import ctremote as CR  # noqa: E402
import drums18  # noqa: E402

MSG, BUF = 0x20060000, 0x20060100
HEAD = b"RIFF" + struct.pack("<I", 187180) + b"WAVEfmt " + struct.pack("<IB", 16, 1)


def nib32(v): return [(v >> s) & 15 for s in range(28, -1, -4)]
def nibbytes(bs): return [x for b in bs for x in (b >> 4, b & 15)]
def un32(n): return int("".join("%x" % x for x in n), 16)
def unbytes(n): return bytes(n[i] << 4 | n[i + 1] for i in range(0, len(n), 2))


class E8(T.E191):
    def __init__(self, image, man):
        super().__init__(image, man)
        self.api, self.out, self.fwd = [], [], 0
        def ret(uc, v):
            uc.reg_write(UC_ARM_REG_R0, v & 0xFFFFFFFF); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        def item(uc):
            b = bytes(uc.mem_read(uc.reg_read(UC_ARM_REG_R0), 12)); return struct.unpack("<II", b[:8]) + (b[8],)
        def exists(uc, a, s, d): self.api.append(("exists", item(uc))); ret(uc, 1)
        def size(uc, a, s, d): self.api.append(("size", item(uc))); ret(uc, 0x12345678)
        def read(uc, a, s, d):
            sp = uc.reg_read(UC_ARM_REG_SP); cb, ctx, done = struct.unpack("<III", bytes(uc.mem_read(sp, 12)))
            off, buf, n = uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R3)
            self.api.append(("read", item(uc), off, n, cb, ctx)); m = min(n, len(HEAD))
            uc.mem_write(buf, HEAD[:m]); uc.mem_write(done, struct.pack("<I", m)); ret(uc, 0)
        def write(uc, a, s, d):
            sp = uc.reg_read(UC_ARM_REG_SP); cb, ctx = struct.unpack("<II", bytes(uc.mem_read(sp, 8)))
            off, buf, n = uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R3)
            self.api.append(("write", item(uc), off, bytes(uc.mem_read(buf, n)), cb, ctx)); ret(uc, 0)
        def router(uc, a, s, d):
            m = uc.reg_read(UC_ARM_REG_R2); bp, ln = struct.unpack("<II", bytes(uc.mem_read(m, 8)))
            self.out.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1), bytes(uc.mem_read(bp, ln)))); ret(uc, 0)
        def fwd(uc, a, s, d):
            self.fwd += 1; uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        def delete(uc, a, s, d): self.api.append(("del", item(uc), uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2))); ret(uc, 0)
        for f, ad in ((exists, RD.EXISTS), (size, RD.SIZE), (read, RD.READ), (write, RD.WRITE), (router, RD.ROUTER), (fwd, RD.HOOK_CONT), (delete, RD.DEL_FN)):
            self.uc.hook_add(UC_HOOK_CODE, f, begin=ad, end=ad)

    def sysex(self, data, port=0):
        self.api.clear(); self.out.clear(); self.fwd = 0
        self.uc.mem_write(BUF, bytes(data)); self.uc.mem_write(MSG, struct.pack("<II", BUF, len(data)))
        self.call(RD.HOOK, port, MSG, 0, maxins=2_000_000)

    def req(self, cmd, payload=(), seq=5, port=0, pad=RD.PAD):
        body = list(RD.SIG) + [cmd, seq] + list(payload)
        body += [0] * max(0, pad - 1 - len(body))
        self.sysex(body + [0xF7], port)
        if len(self.out) != 1: return None
        r, mask, msg = self.out[0]
        return r, mask, msg


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["rdiag"]["labels"].items()}
    check(drums18.decode_bw(bytearray(img), RD.HOOK) == L["c_rdin"], "0x0801EB30: b.w c_rdin")
    gc.collect(); e = E8(img, man)
    router_obj = e.r32(struct.unpack_from("<I", img, RD.ROUTER_LIT - 0x08010000)[0])
    e.sysex([0xF0, 0x7E, 0x7F, 0x06, 0x01, 0xF7])
    check(e.fwd == 1 and e.out == [] and e.api == [], "a foreign SysEx (identity request): forwarded to the stock dispatcher, no reply of ours")
    e.sysex(list(RD.SIG) + [1, 5, 0, 0, 0xF7])
    check(e.fwd == 0 and e.out == [], "an unpadded request of ours (9 bytes): swallowed, no reply")
    def payload(msg, cmd, seq=5):
        ok = msg[:4] == bytes(RD.SIG) and msg[4] == cmd | 0x40 and msg[5] == seq and msg[-1] == 0xF7 and all(b < 0x80 for b in msg[1:-1])
        return list(msg[6:-1]) if ok else None
    for port in (0, 1):
        r = e.req(1, port=port)
        p = r and payload(r[2], 1)
        ver = RD.VERSION + (1 if RD.DELETE else 0) + (0x10 if RD.DSPX else 0) + (0x20 if RD.DEL_PACK else 0) + (0x40 if getattr(RD, 'DSPW', False) else 0) + (0x80 if 'c_dmon' in L else 0)
        check(r is not None and r[0] == router_obj and r[1] == 1 << port and p is not None and un32(p[:8]) == ver and un32(p[8:16]) == port,
              f"ping on port {port}: version {ver:#x}, port, router {router_obj:#x}, mask {1 << port}")
    r = e.req(2, nib32(0x08010000) + [16]); p = payload(r[2], 2)
    check(un32(p[:8]) == 0 and unbytes(p[8:]) == bytes(img[:16]), f"mem flash 0x08010000, 16 B = the image ({unbytes(p[8:]).hex()})")
    want = bytes(e.uc.mem_read(0x20000800, 8))
    r = e.req(2, nib32(0x20000800) + [8]); p = payload(r[2], 2)
    check(un32(p[:8]) == 0 and unbytes(p[8:]) == want, "mem RAM 0x20000800, 8 B")
    r = e.req(2, nib32(0x40000000) + [8]); p = payload(r[2], 2)
    check(un32(p[:8]) == 1 and len(p) == 8, "mem outside flash / RAM: status 1, no bytes")
    r = e.req(2, nib32(0x08010000) + [127]); p = payload(r[2], 2)
    check(len(p) == 8 + 2 * RD.NMAX, f"mem: the length clamped to {RD.NMAX}")
    r = e.req(4, [4, 3, 0x7F]); p = payload(r[2], 4)
    check(e.api == [("exists", (4, 3, 0xFF)), ("size", (4, 3, 0xFF))] and un32(p[:8]) == 1 and un32(p[8:16]) == 0x12345678, f"info PCM 3 of the current pack: {e.api}")
    r = e.req(5, [4, 2, 5] + nib32(0x1000) + [21]); p = payload(r[2], 5)
    check(e.api == [("read", (4, 2, 5), 0x1000, 21, 0, 0)] and un32(p[:8]) == 0 and un32(p[8:16]) == 21 and unbytes(p[16:]) == HEAD[:21],
          f"read PCM 2 of pack 5 at 0x1000, 21 B, synchronous: {unbytes(p[16:])!r}")
    data = bytes(range(0xA0, 0xA8))
    r = e.req(6, [4, 1, 0x7F] + nib32(0x10) + [8] + nibbytes(data)); p = payload(r[2], 6)
    check(e.api == [("write", (4, 1, 0xFF), 0x10, data, 0, 0)] and un32(p[:8]) == 0, f"write PCM 1 at 0x10: exactly the 8 bytes sent, synchronous ({e.api})")
    UNK = 13 if 'c_dmon' in L else 10                                          # SEQWD (rdiag.WATCH): 10-12 are watch / poke / wlog
    r = e.req(UNK); p = payload(r[2], UNK)
    check(un32(p[:8]) == 0xFFFFFFFF and e.api == [], "unknown command: status -1")
    r = e.req(7); p = payload(r[2], 7)
    if RD.DELETE:
        r = e.req(7, [4, 5, 0x7F]); p = payload(r[2], 7)
        check(e.api == [("del", (4, 5, 0xFF), 0, 0)] and un32(p[:8]) == 0, f"delete PCM 5 of the current pack: op 5, synchronous ({e.api})")
        for k in ((0, 7) if RD.DEL_PACK else (0, 1, 7)):
            r = e.req(7, [k, 0, 3]); p = payload(r[2], 7)
            check(e.api == [] and un32(p[:8]) == 0xFFFFFFFE, f"delete kind {k}: refused (status -2), no API call")
    else:
        check(un32(p[:8]) == 0xFFFFFFFF and e.api == [], "no delete command (command 7 unknown)")
    # ---- the PC tool's own protocol functions (tools/ctremote.py) against the firmware
    check(CR.PAD == RD.PAD and CR.NMAX == RD.NMAX and CR.SIG == RD.SIG, "ctremote and rdiag agree on SIG / PAD / NMAX")
    def ask(make, cmd, seq=9):
        e.sysex(list(make(seq))); return CR.parse(e.out[0][2], cmd, seq) if len(e.out) == 1 else None
    p = ask(CR.req_ping, 1)
    check(p is not None and CR.dec_ping(p) == dict(version=RD.VERSION + (1 if RD.DELETE else 0) + (0x10 if RD.DSPX else 0) + (0x20 if RD.DEL_PACK else 0) + (0x40 if getattr(RD, 'DSPW', False) else 0) + (0x80 if 'c_dmon' in L else 0), port=0), f"ctremote ping: {p and CR.dec_ping(p)}")
    if RD.DELETE:
        p = ask(lambda s: CR.req_del(s, 4, 9), 7)
        check(CR.dec_del(p) == dict(status=0) and e.api == [("del", (4, 9, 0xFF), 0, 0)], "ctremote del")
    p = ask(lambda s: CR.req_mem(s, 0x08010004, 12), 2)
    check(CR.dec_mem(p) == dict(status=0, data=bytes(img[4:16])), "ctremote mem")
    p = ask(lambda s: CR.req_info(s, 4, 0), 4)
    check(CR.dec_info(p) == dict(exists=1, size=0x12345678) and e.api[0] == ("exists", (4, 0, 0xFF)), "ctremote info")
    p = ask(lambda s: CR.req_read(s, 4, 0, 0, 21), 5)
    check(CR.dec_read(p) == dict(status=0, done=21, data=HEAD[:21]), "ctremote read")
    p = ask(lambda s: CR.req_write(s, 4, 7, 4, bytes([1, 2, 0xFE])), 6)
    check(CR.dec_write(p) == dict(status=0) and e.api == [("write", (4, 7, 0xFF), 4, bytes([1, 2, 0xFE]), 0, 0)], "ctremote write")
    check(all(len(CR.build(c, 1, [0] * 20)) == CR.PAD for c in (1, 2, 4, 5, 6)), f"every request is {CR.PAD} bytes")
    print(f"SC35D8{'/9 (delete)' if RD.DELETE else ''} RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    if "--delete" in a:
        RD.DELETE = True
    if "--dspx" in a:                                                  # PATCHD: the image also carries the DSP read commands
        RD.DSPX = True
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
