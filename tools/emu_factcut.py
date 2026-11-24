"""Alpha 7.38 test (tools/factcut.py): the factory-test mode is gone and its DSP programs' flash is ours.

    python tools/emu_factcut.py firmware/a7.38 firmware/a7.37        (the build, the build before it)

With emu_sdsysex's harness (the real SysEx entry 0x0801EB30 and the real USB input ring + parser on the live RAM dump) and emu_dspz's (the DSP
program send 0x08029260 with the SPI calls recorded):
  * static: factcut.check; the freed range no longer holds the stock's blocks;
  * the build before (this proves the messages are the right ones): F0 00 20 29 01 63 70 60 01 F7 reaches 0x0801F284 (door a) and 0x0802527C's
    accepted path (door c) and sets the test bits (0x15) of 0x20000A6C; ... 63 71 00 ... reaches 0x08038BA0's accepted path (door b);
    ... 63 70 5C ... asks 0x0801F51E for mode 1; ... 63 70 60 00 clears the bits;
  * the build: those messages and 300 more that start F0 00 20 29 01 63, on ports 0 and 1 and through the USB ring: none of the three accepted
    paths runs, no command handler, no mode request, the test bits and the port mask stay 0, nothing is answered;
  * controls: the file protocol's open / close, the identity request, a few messages with other headers and our firmware query answer as before;
  * the DSP program send: mode 0 = the build before's, call for call and byte for byte; mode 1 = mode 0 (the build before sends the stock's two
    test blocks).
"""
from __future__ import annotations
import gc, json, random, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn import UC_HOOK_CODE  # noqa: E402
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_R0, UC_ARM_REG_R1  # noqa: E402
import emu_sdsysex as X  # noqa: E402
import emu_dspz as Z  # noqa: E402
import factcut as F  # noqa: E402
import fwid  # noqa: E402

BASE = 0x08010000
FLAGS, PMASK = 0x20000A6C, 0x20006A4D                # the test bits (0, 2, 4) and the ports in test mode
DOOR_A, DOOR_B, DOOR_C = 0x0801F284, 0x08038BAC, 0x0802528E     # what runs only once byte 5 = 0x63 was accepted
MODE, SENDP = 0x0801F51E, 0x08029260
HANDLERS = (0x080267F8, 0x08023E22, 0x08026B68, 0x08026BDC, 0x08026918, 0x08026C78, 0x080269E4, 0x080252F8)
H63 = bytes([0xF0, 0, 0x20, 0x29, 1, 0x63])
ENTER, LEAVE = H63 + bytes([0x70, 0x60, 1, 0xF7]), H63 + bytes([0x70, 0x60, 0, 0xF7])
DSP1 = H63 + bytes([0x70, 0x5C, 0, 0, 0, 0, 0xF7])
B71 = H63 + bytes([0x71, 0, 0, 1, 0xF7])
SERIAL = H63 + bytes([0x70, 0x6C]) + b"ABCDEFGH123456" + b"\xF7"
IDENT = bytes([0xF0, 0x7E, 0x7F, 6, 1, 0xF7])
NAMES = {DOOR_A: "a", DOOR_B: "b", DOOR_C: "c"}


def unexplained(old, new, oman, nman, addrs):
    """The differing bytes that are not a relocation: a 32-bit branch (bl / b.w) or an aligned word whose old target maps, label for label
    (the same label of the same module in the two manifests), to the new one."""
    m = {}
    for mod, v in oman["report"].items():
        w = nman["report"].get(mod)
        if isinstance(v, dict) and isinstance(w, dict) and isinstance(v.get("labels"), dict) and isinstance(w.get("labels"), dict):
            for k, a in v["labels"].items():
                if k in w["labels"]: m[int(a, 16)] = int(w["labels"][k], 16)
    def br(img, at):
        h1, h2 = struct.unpack_from("<HH", img, at - BASE)
        if h1 & 0xF800 != 0xF000 or h2 & 0xD000 not in (0xD000, 0x9000): return None
        s_, j1, j2 = (h1 >> 10) & 1, (h2 >> 13) & 1, (h2 >> 11) & 1
        off = s_ << 24 | (1 - (j1 ^ s_)) << 23 | (1 - (j2 ^ s_)) << 22 | (h1 & 0x3FF) << 12 | (h2 & 0x7FF) << 1
        return (at + 4 + off - (s_ << 25), h2 & 0x4000)
    left = set(addrs)
    for at in sorted(addrs):
        if at not in left: continue
        for u in (at - at % 2, at - at % 2 - 2):
            to, tn = br(old, u), br(new, u)
            if to and tn and to[1] == tn[1] and to[0] != tn[0] and m.get(to[0]) == tn[0]:
                left -= set(range(u, u + 4)); break
        else:
            u = at - at % 4
            wo, wn = struct.unpack_from("<I", old, u - BASE)[0], struct.unpack_from("<I", new, u - BASE)[0]
            if wo & 1 == wn & 1 and wo != wn and m.get(wo & ~1) == wn & ~1:
                left -= set(range(u, u + 4))
    return sorted(left)


class Rig:
    def __init__(self, img):
        gc.collect()
        self.f = X.Fw(image=bytes(img), fs=X.PyFat()); self.f.boot_storage()
        self.hits = []
        def h(uc, a, s, d):
            if a in (MODE, SENDP):                    # a DSP mode request: noted, and the handler dropped there (the rest talks to the DSP)
                self.hits.append(("mode", uc.mem_read(uc.reg_read(UC_ARM_REG_R1), 1)[0]) if a == MODE else ("send", uc.reg_read(UC_ARM_REG_R0)))
                uc.reg_write(UC_ARM_REG_PC, X.STOP | 1)
            else:
                self.hits.append(("door", NAMES[a]) if a in NAMES else ("handler", a))
        for a in (DOOR_A, DOOR_B, DOOR_C, MODE, SENDP) + HANDLERS: self.f.uc.hook_add(UC_HOOK_CODE, h, begin=a, end=a)
    def send(self, msg, port=0, usb=False):
        self.hits = []
        out = self.f.usb_feed(msg) if usb else self.f.send(msg, port)
        return [bytes(m) for m in out]
    def state(self): return self.f.r32(FLAGS), self.f.r8(PMASK)
    def close(self):
        del self.f; gc.collect()


def others():
    """messages that are not factory-test ones: answered (or ignored) the same by both builds"""
    rnd = random.Random(7)
    out = [X.OPEN, X.CLOSE, IDENT, bytes([0xF0, 0, 0x20, 0x29, 1, 0x62, 0x70, 0x60, 1, 0xF7]), bytes([0xF0, 0, 0x20, 0x29, 0, 0x63, 0x70, 0x60, 1, 0xF7]),
           bytes([0xF0, 0, 0x20, 0x29, 1, 0x64, 0x70, 0x60, 1, 0xF7]), bytes([0xF0, 0, 0x20, 0x29, 1, 0x64, 0x08, 0xF7]), bytes([0xF0, 0x7D, 1, 2, 3, 0xF7])]
    for _ in range(12):
        n = rnd.randrange(1, 14)
        out.append(bytes([0xF0, 0, 0x20, 0x29, 1, rnd.choice((0x60, 0x61, 0x62, 0x65, 0x7F))]) + bytes(rnd.randrange(128) for _ in range(n)) + b"\xF7")
    return out


def main(a):
    new_d, old_d = Path(a[0]), Path(a[1])
    new, old = next(new_d.glob("*.bin")).read_bytes(), next(old_d.glob("*.bin")).read_bytes()
    man = json.loads((new_d / "manifest.json").read_text())
    oman = json.loads((old_d / "manifest.json").read_text())
    stock = X.STOCK.read_bytes()
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    # ---- static
    bad = F.check(new, man["report"])
    check(not bad, f"factcut.check: {bad or 'the patches, the load table and the freed range'}")
    lo, hi, r0 = F.LO - BASE, F.HI - BASE, F.R0 - BASE
    check(old[r0:hi] == stock[r0:hi] and new[lo:hi] != stock[lo:hi] and new[r0:lo] == stock[r0:lo] and new[hi:hi + 2] == stock[hi:hi + 2],
          f"the build before holds the stock's two test blocks at {F.R0:#x}-{F.HI:#x}; the build keeps only their first {F.KEEP} bytes (the parameter table's overrun rows)")
    used = [(n, b_) for n, b_ in man["report"]["dspz"].get("blocks", {}).items() if F.LO <= int(b_[0], 16) < F.HI]
    check(bool(used), f"modules in the freed range: {used}")
    ours = [(r0, hi)] + [(x - BASE, y - BASE) for x, y in ((0x080101F0, 0x08018110 + 1098), (0x0803B27C, 0x0803B732))]      # the freed range, the hole, msdcut's gap
    diff = [BASE + i for i in range(min(len(old), 0x4CDDC)) if old[i] != new[i] and not any(x <= i < y for x, y in ours)]
    want = {a_ + k for a_, o_, n_ in F.PATCHES for k in range(len(o_))} | {F.TABLE + 4 + k for k in range(4)} | {F.TABLE + 12 + k for k in range(4)}
    moved = [d_ for d_ in diff if d_ not in want and not BASE + 0x1E8 <= d_ < BASE + 0x1EE]          # (0x1E8: the marker)
    cut = sorted(d_ for d_ in diff if d_ in want)
    bad = unexplained(old, new, oman, man, moved)
    check(len(cut) >= len(F.PATCHES) and not bad, f"in the stock's code and data (outside our areas) the build differs from the one before in {len(cut)} bytes of the cut "
          f"and {len(moved)} more, all relocated branches / words to the moved modules' same labels ({len(bad)} unexplained: {[hex(x) for x in bad[:12]]})")
    # ---- the build before: the messages are the real ones
    r = Rig(old)
    r.send(ENTER)
    check(("door", "a") in r.hits and ("door", "c") in r.hits and r.state() == (0x15, 1) and sum(1 for k, _ in r.hits if k == "handler") == 6,
          f"before: ENTER passes doors a and c, test bits {r.state()[0]:#x}, port mask {r.state()[1]:#x}, {sum(1 for k, _ in r.hits if k == 'handler')} command handlers")
    r.send(B71)
    check(("door", "b") in r.hits, f"before: ... 63 71 00 ... passes door b ({r.hits})")
    r.send(DSP1)
    check(("mode", 1) in r.hits, f"before: ... 63 70 5C asks 0x0801F51E for mode 1 ({[h_ for h_ in r.hits if h_[0] == 'mode']})")
    r.send(LEAVE)
    check(r.state() == (0, 0), f"before: LEAVE clears the bits ({r.state()})")
    ctl_old = [r.send(m, usb=k % 2 == 0) for k, m in enumerate(others())]
    r.close()
    # ---- the build
    r = Rig(new)
    rnd = random.Random(1)
    many = [ENTER, DSP1, B71, SERIAL, H63 + bytes([0x70, 0x5E, 0, 0xF7]), H63 + bytes([0x71, 1, 0, 0, 0xF7]), H63 + bytes([0x71, 2, 1, 0, 0xF7]), LEAVE, ENTER]
    for _ in range(300):
        n = rnd.choice((0, 1, 2, 3, 4, 8, 16, 17, 40))
        many.append(H63 + bytes([rnd.choice((0x70, 0x71, rnd.randrange(128)))]) + bytes(rnd.randrange(128) for _ in range(n)) + b"\xF7")
    for what, kw, msgs in (("port 0", dict(port=0), many), ("port 1", dict(port=1), many[:60]), ("the USB ring", dict(usb=True), many[:60])):
        outs, hits = [], []
        for m in msgs:
            outs += r.send(m, **kw); hits += r.hits
        check(not hits and not outs and r.state() == (0, 0), f"{what}: {len(msgs)} messages F0 00 20 29 01 63 ... ignored (hits {hits[:6]}, replies {len(outs)}, bits {r.state()})")
    ctl_new = [r.send(m, usb=k % 2 == 0) for k, m in enumerate(others())]
    check(ctl_new == ctl_old and len(ctl_new[0]) >= 1 and len(ctl_new[2]) == 1,
          f"{len(ctl_new)} other messages answered as before ({sum(len(x) for x in ctl_new)} replies; open {[m.hex(' ') for m in ctl_new[0]]}, identity {ctl_new[2][0].hex(' ') if ctl_new[2] else None})")
    q = bytes(list(fwid.SIG) + [0, 0x23] + [0] * 7 + [0xF7])
    got = r.send(q, usb=True)
    mark = bytes(new[0x1E8:0x1E8 + 6])
    check(got == [bytes(list(fwid.SIG) + [0x40, 0x23, 1]) + bytes(b & 0x7F for b in mark) + b"\xF7"], f"our firmware query answers {mark!r}")
    r.close()
    # ---- the DSP program send
    ev = {}
    for k, im in (("old", old), ("new", new)):
        for mode in (0, 1):
            ev[k, mode] = Z.run(im, mode)[0]; gc.collect()
    spi = lambda e: b"".join(x[1] for x in e if x[0] == "spi")
    check(len(ev["new", 0]) > 10 and ev["new", 0] == ev["old", 0], f"mode 0: {len(ev['new', 0])} calls, {len(spi(ev['new', 0]))} B to the DSP, as the build before")
    check(ev["new", 1] == ev["new", 0], "mode 1 asked for: the build sends the normal programs (the same calls and bytes as mode 0)")
    blocks = [stock[at - BASE:at - BASE + 6 + 3 * w] for at, w in F.BLOCKS]
    o1, n1 = spi(ev["old", 1]), spi(ev["new", 1])
    check(all(b_ in o1 for b_ in blocks) and not any(b_[:64] in n1 or b_ in n1 for b_ in blocks) and len(n1) == len(spi(ev["new", 0])),      # (their last words are shared code: only the head and the whole)
          f"mode 1 in the build before sends the stock's two test blocks ({len(o1)} B in all); the build never does")
    print(f"{man.get('marker', '?')} FACTCUT RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
