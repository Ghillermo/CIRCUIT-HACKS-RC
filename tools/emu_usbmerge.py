"""SC46.4 / Beta 3.21 (tools/usbmerge.py): the DIN In merged into the USB MIDI out.  The emulated firmware, through the controller (Advanced
Setup's pad 23), the real LED task and the post of a short input message (the bl at 0x08021024):
  * off by default: a DIN In note goes to midithru's c_thin and nowhere else;
  * Advanced Setup pad 23 = on: bit 1 of gmdrum's flags byte in both copies of the settings store (with its signature), the save asked; pad 23
    green (dim while off); the mode of GM on / off with K4 keeps it;
  * on: a DIN In note / CC goes to the USB port (port 0's send) and on to c_thin; a message of the USB In (port 0) is not copied; the DIN In's clock
    (0xF8) with the unit's Clock Tx on: not copied; with Clock Tx off: copied; active sensing: copied;
  * pad 23 again = off;
  * the previous build (if given): pad 23 in Advanced Setup changes nothing, no copy.

    python tools/emu_usbmerge.py BUILD.bin manifest.json [PREVIOUS.bin PREVIOUS_manifest.json]
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_LR, UC_ARM_REG_PC
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_gmdrum as EGM  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import midithru as MT  # noqa: E402
import usbmerge as U  # noqa: E402
import gmdrum as G  # noqa: E402
from thumb import bl as bl_enc  # noqa: E402

MSG = 0x2006E100


def run(img, man):
    raw = Path(img).read_bytes()
    e = EGM.EG(raw, man)
    R = man["report"]
    c_thin = int(R["midithru"]["labels"]["c_thin"], 16)
    post = c_thin if "usbmerge" not in R else int(R["usbmerge"]["labels"]["c_usbin"], 16)
    usb = e.r32(e.r32(e.r32(MT.ROUTER_PTR) + 0x14) + 4 * U.USB_PORT)
    sent, thin = [], []
    def skip(uc): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    def snd(uc, a, s, d):
        if uc.reg_read(UC_ARM_REG_R0) == usb: sent.append(bytes(uc.mem_read(uc.reg_read(UC_ARM_REG_R1), 3)))
        skip(uc)
    def th(uc, a, s, d): thin.append(uc.reg_read(UC_ARM_REG_R1)); skip(uc)
    e.uc.hook_add(UC_HOOK_CODE, snd, begin=MT.PORT_SEND, end=MT.PORT_SEND)
    e.uc.hook_add(UC_HOOK_CODE, th, begin=c_thin, end=c_thin)
    o = dict(bl=bytes(raw[MT.POST_CALL - 0x08010000:MT.POST_CALL - 0x08010000 + 4]) == bl_enc(MT.POST_CALL, post))
    def msg(port, b):
        sent.clear(); thin.clear(); e.uc.mem_write(MSG, bytes(b) + bytes(4 - len(b)))
        e.call(post, 0x20000000, port, MSG, maxins=2_000_000)
        return list(sent), list(thin)
    def clock_tx(on):
        v = e.r8(U.TX + 0x18); e.uc.mem_write(U.TX + 0x18, bytes([(v | U.CLOCK_TX) if on else (v & ~U.CLOCK_TX)]))
    def flags(c): return e.param(G.P0, c)
    o["off"] = msg(MT.DIN_IN, [0x90, 60, 100])
    e.setup(True, adv=1); f0 = X.frame(e); e.unpend(); e.pad(U.PAD_USB); f1 = X.frame(e)
    o["on_flags"] = [flags(c) for c in (0, 1)]; o["pending"] = e.pending(); o["led"] = (f0[U.PAD_USB], f1[U.PAD_USB])
    o["note"] = msg(MT.DIN_IN, [0x90, 60, 100]); o["cc"] = msg(MT.DIN_IN, [0xB3, 74, 20])
    o["usb_in"] = msg(0, [0x90, 61, 100])
    clock_tx(True); o["clk_tx"] = msg(MT.DIN_IN, [0xF8]); o["start_tx"] = msg(MT.DIN_IN, [0xFA])
    clock_tx(False); o["clk"] = msg(MT.DIN_IN, [0xF8])
    o["sense"] = msg(MT.DIN_IN, [0xFE])
    e.setup(True, adv=0); e.knob(3, 1); g1 = flags(0); e.knob(3, -1); g2 = flags(0)
    o["gm"] = (g1[2], g2[2])                                    # GM on / off with K4: the USB bit kept
    e.setup(True, adv=1); e.pad(U.PAD_USB); o["off2_flags"] = flags(0); o["off2"] = msg(MT.DIN_IN, [0x90, 62, 100])
    del e; gc.collect()
    return o


def main(img, man, prev=None, pman=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    o = run(img, man)
    check(o["bl"], "the post's bl at 0x08021024 = c_usbin")
    check(o["off"] == ([], [MT.DIN_IN]), f"off: a DIN In note to c_thin only ({o['off']})")
    check(all(p[1] == G.SIG and p[2] & U.F_USB for p in o["on_flags"]) and o["pending"], f"Advanced Setup pad 23: on, in both copies, the save asked ({[p.hex() for p in o['on_flags']]})")
    check(o["led"] == (U.COL_OFF, U.COL_ON), f"pad 23 dim / green ({[hex(x) for x in o['led']]})")
    check(o["note"] == ([bytes([0x90, 60, 100])], [MT.DIN_IN]) and o["cc"][0] == [bytes([0xB3, 74, 20])], f"on: a DIN In note / CC to the USB port and to c_thin ({o['note']}, {o['cc']})")
    check(o["usb_in"][0] == [], f"the USB In: not copied ({o['usb_in']})")
    check(o["clk_tx"][0] == [] and o["start_tx"][0] == [] and o["clk_tx"][1] == [MT.DIN_IN], f"Clock Tx on: the DIN In's clock / start not copied ({o['clk_tx']}, {o['start_tx']})")
    check(o["clk"][0] == [bytes([0xF8, 0, 0])], f"Clock Tx off: its clock copied ({o['clk']})")
    check(o["sense"][0] == [bytes([0xFE, 0, 0])], "active sensing copied")
    check(o["gm"] == (U.F_USB | 1, U.F_USB), f"GM K4 on / off keeps the USB merge ({o['gm']})")
    check(not (o["off2_flags"][2] & U.F_USB) and o["off2"][0] == [], f"pad 23 again: off ({o['off2_flags'].hex()}, {o['off2']})")
    if prev:
        p = run(prev, pman)
        check(not (p["on_flags"][0][2] & U.F_USB) and p["note"][0] == [], f"the previous build: pad 23 nothing, no copy ({p['on_flags'][0].hex()})")
    print(f"{Path(img).stem} RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text()), a[2] if len(a) > 2 else None,
                       json.loads(Path(a[3]).read_text()) if len(a) > 3 else None) else 0)
