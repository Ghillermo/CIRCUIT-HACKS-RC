"""SC48.3 / Beta 3.40 (mpatch.use_slots128): 128 own-synth patch slots, 8 pages of 16 in the Preset view of MIDI 1 / 2 (emu_sc39_4's harness: the
controller, the LED task, emu_sc35's model of the SD card).

    python tools/emu_mp128.py BUILD.bin manifest.json [PREVIOUS.bin PREVIOUS_manifest.json]

  * the pack with 16 banks (128 synth patch records, padding 0xFF); MIDI 1's Preset view; Octave down seven times = page 8 (the cache's page 7):
    Octave down unlit there, Octave up lit; one more Octave down stays on page 8;
  * Clear + pad 24 twice on page 8 = slot 127: one write, the track's engine in the padding of record 127 (bank 15, record 7), the 340 bytes of the
    synth patch and the other records untouched; page 4 (the old last page): Octave down lit;
  * the previous build: page 4 is the last one (Octave down unlit there).
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc39_4 as T4  # noqa: E402
import emu_sc39_1 as T1  # noqa: E402

LED_DOWN, LED_UP = 51, 52


def run(img, man):
    e = T4.E4(Path(img).read_bytes(), man); e.setup(man)
    A = (0b101011, 0x5, [(7 * i + 3) % 120 - 50 for i in range(26)], [(5 * i + 1) % 100 for i in range(8)])
    pa = T1.patch_bytes(*A)
    e.btn(2); e.btn(8)
    e.set_engine(0, *A)
    banks = {b: b"".join(bytes((3 + 8 * b + k + i) & 0x7F for i in range(340)) + bytes([0xFF]) * 172 for k in range(8)) for b in range(16)}
    e.sd = {(3, b, 0xFF): v for b, v in banks.items()}
    leds = lambda: (lambda f: (f[LED_DOWN], f[LED_UP]))(e.frame_full())
    o = {}
    pages = []
    for i in range(8):
        e.frame(0); pages.append((e.st_page(), leds()))
        e.btn(19)
    e.frame(0); o["pages"] = pages; o["end"] = e.st_page()
    e.clear(1); e.api.clear(); e.pad(23); e.pad(23); e.clear(0)
    rec = e.sd[(3, 15, 0xFF)]
    o["save"] = (len(e.wr()), rec[512 * 7 + 340:512 * 7 + 380] == pa[:40], rec[512 * 7:512 * 7 + 340] == banks[15][512 * 7:512 * 7 + 340],
                 rec[:512 * 7] == banks[15][:512 * 7], all(e.sd[(3, b, 0xFF)] == banks[b] for b in range(15)))
    del e; gc.collect()
    return o


def frame_full(self):
    """the LED task through its caller (as emu_cscale): the 69 LEDs of the panel's frame"""
    import struct
    from unicorn.arm_const import UC_ARM_REG_R4
    from emu_sc35 import MGR
    from emu_sc19_6 import STOP
    self.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); self.uc.reg_write(UC_ARM_REG_R4, MGR)
    self.call(0x08033B3E, maxins=8_000_000)
    return list(struct.unpack("<69H", bytes(self.uc.mem_read(self.r32(self.r32(MGR + 0x90)), 138))))


def st_page(self):
    """mpatch's cache: [3] = the page shown"""
    from unicorn.arm_const import UC_ARM_REG_R0
    self.call(self.mp_c); return self.r8(self.uc.reg_read(UC_ARM_REG_R0) + 3)


T4.E4.frame_full = frame_full
T4.E4.st_page = st_page


def main(img, man, prev=None, pman=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    for im, mn, new in ((img, man, True),) + (((prev, pman, False),) if prev else ()):
        T4.E4.mp_c = int(mn["report"]["mpatch"]["labels"]["c_mpc"], 16)
        o = run(im, mn)
        pg = [p for p, _ in o["pages"]]
        if new:
            check(pg == list(range(8)) and o["end"] == 7, f"Octave down: pages 1..8 ({pg}), stays on 8 ({o['end']})")
            lit = [(d != 0, u != 0) for _, (d, u) in o["pages"]]
            check(lit[0] == (True, False) and lit[3] == (True, True) and lit[7] == (False, True),
                  f"Octave LEDs: page 1 down only, page 4 both, page 8 up only ({lit[0]}, {lit[3]}, {lit[7]})")
            check(o["save"] == (1, True, True, True, True), f"Clear + pad 24 twice on page 8 = slot 127: one write in the padding of record 127 "
                                                            f"(bank 15, record 7), the rest untouched {o['save']}")
        else:
            check(pg[:4] == [0, 1, 2, 3] and o["end"] == 3 and o["pages"][3][1][0] == 0, f"the previous build: 4 pages ({pg}, Octave down on page 4 "
                                                                                       f"{o['pages'][3][1][0]:#x})")
    print(f"{Path(img).stem} MP128 RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text()), a[2] if len(a) > 2 else None,
                       json.loads(Path(a[3]).read_text()) if len(a) > 3 else None) else 0)
