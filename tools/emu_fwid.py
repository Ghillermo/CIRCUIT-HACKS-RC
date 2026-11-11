"""SC56.2 tests: the firmware identity query (tools/fwid.py) through the real route, the incoming SysEx dispatcher 0x0801EB30(port, msg), with
emu_sc35d8's harness (the SysEx output router 0x08020C90 stubbed; reaching 0x0801EB34 = forwarded to the stock dispatcher).

    python tools/emu_fwid.py IMAGE.bin manifest.json
  * the hook: the first 4 bytes of 0x0801EB30 = b.w c_fwin;
  * F0 7D 43 54 00 seq + 7 x 00 + F7 (ports 0 / 1): one reply through the stock router (the router object, mask 1 << port) =
    F0 7D 43 54 40 seq 01 + the build's 6-byte marker (as in the image at 0x1E8) + F7, and nothing forwarded;
  * the identity request, a request of ours one byte shorter / longer, command 1 (rdiag's ping): forwarded with port and message intact, no reply;
  * through the USB input ring and the real parser (tools/emu_sdsysex.py, as the SD apps reach it): the build answers with its marker, the stock
    image stays silent, the identity reply is the same in both.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc35d8 as D  # noqa: E402
import fwid  # noqa: E402
import rdiag as RD  # noqa: E402


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["fwid"]["labels"].items()}
    check(bytes(img[RD.HOOK - 0x08010000:RD.HOOK - 0x08010000 + 4]) == RD.b_w(RD.HOOK, L["c_fwin"]), "0x0801EB30 = b.w c_fwin")
    mark = bytes(img[0x1E8:0x1E8 + 6])
    check(mark.rstrip(b"\0").decode() == man["marker"][:6], f"the marker in the image: {mark!r}")
    gc.collect()
    e = D.E8(img, man)
    regs = []
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: regs.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1))), begin=RD.HOOK_CONT, end=RD.HOOK_CONT)
    router = struct.unpack_from("<I", bytes(e.uc.mem_read(struct.unpack_from("<I", img, RD.ROUTER_LIT - 0x08010000)[0], 4)))[0]
    for port in (0, 1):
        q = list(fwid.SIG) + [0, 0x23] + [0] * 7 + [0xF7]
        e.sysex(q, port)
        want = bytes(list(fwid.SIG) + [0x40, 0x23, 1]) + bytes(b & 0x7F for b in mark) + b"\xF7"
        ok = len(e.out) == 1 and e.out[0] == (router, 1 << port, want) and e.fwd == 0
        check(ok, f"port {port}: the reply {e.out[0][2].hex(' ') if e.out else None} (router {hex(e.out[0][0]) if e.out else '-'}, mask {e.out[0][1] if e.out else '-'}), nothing forwarded")
    for what, q in (("the identity request", [0xF0, 0x7E, 0x7F, 0x06, 0x01, 0xF7]),
                    ("ours, 13 bytes", list(fwid.SIG) + [0, 1] + [0] * 6 + [0xF7]),
                    ("ours, 15 bytes", list(fwid.SIG) + [0, 1] + [0] * 8 + [0xF7]),
                    ("command 1 (rdiag's ping), 14 bytes", list(fwid.SIG) + [1, 1] + [0] * 7 + [0xF7])):
        regs.clear()
        e.sysex(q, 1)
        check(e.fwd == 1 and e.out == [] and regs == [(1, D.MSG)], f"{what}: forwarded (port 1, the message) with no reply")
    del e; gc.collect()
    import emu_sdsysex as X
    q, ident = bytes(list(fwid.SIG) + [0, 0x23] + [0] * 7 + [0xF7]), bytes([0xF0, 0x7E, 0x7F, 6, 1, 0xF7])
    got = {}
    for k, im in (("build", bytes(img)), ("stock", None)):
        f = X.Fw(image=im, fs=X.PyFat()); f.boot_storage()
        got[k] = ([bytes(m) for m in f.usb_feed(q)], [bytes(m) for m in f.usb_feed(ident)])
        del f; gc.collect()
    want = bytes(list(fwid.SIG) + [0x40, 0x23, 1]) + bytes(b & 0x7F for b in mark) + bytes([0xF7])
    check(got["build"][0] == [want], f"over USB the build answers {[m.hex(' ') for m in got['build'][0]]}")
    check(got["stock"][0] == [], f"over USB the stock image answers nothing ({len(got['stock'][0])} messages)")
    check(got["build"][1] == got["stock"][1] and len(got["stock"][1]) == 1, f"the identity reply is the same: {got['stock'][1][0].hex(' ') if got['stock'][1] else None}")
    print(f"{man.get('marker', '?')} FWID RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text())) else 0)
