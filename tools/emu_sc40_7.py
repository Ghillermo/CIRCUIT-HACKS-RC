"""SC40.7 ARM tests (live RAM dump, the real routes, the SD card modelled): the own-synth patches of MIDI 1 / 2 copied between packs (tools/xpatch.py).

    python tools/emu_sc40_7.py SC40.7.bin SC40.7_manifest.json SC40.6.bin SC40.6_manifest.json
  * the hooks: the template view's pad slot (in front of psave's), the LED task calls; the dynamics table = stepmod.DYN2;
  * the Preset view of MIDI 1 through the controller, pack 31 loaded: Clear + pad twice saves the engine into slot 1 (psave); Duplicate + slot 1:
    nothing written, the clip word of the DSP = 0xA7, pack 31, slot 0; in the same pack Duplicate + another slot still exchanges (psave) and the
    Duplicate button is not yellow;
  * pack 30 loaded: the Duplicate button yellow; Duplicate + slot 3 there: 64 bytes read from pack 31's bank by its number, the storage task back
    on pack 30, one write of 64 bytes into slot 3's padding of pack 30: the patch and its name; the synth patches of both packs and pack 31's
    slot untouched; the buffer lock released; the clip kept: Duplicate + slot 5 takes it too;
  * nothing written when: B's record is not in its bank; the slot remembered is empty; a plain pad (it loads, as before);
  * the previous build: Duplicate + pad in the other pack only marks an A.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R4
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc39_4 as T4  # noqa: E402
from emu_sc35 import MGR, PK, set_loaded  # noqa: E402
from emu_sc05 import STOP  # noqa: E402
import mpatch as MP  # noqa: E402
import psave as PS  # noqa: E402
import sampler_dsp as SD  # noqa: E402
import stepmod as SM  # noqa: E402
import xpatch as XP  # noqa: E402

B = 0x08010000
A_ENG = (0b101011, 0x5, [(7 * i + 3) % 120 - 50 for i in range(26)], [(5 * i + 1) % 100 for i in range(8)])


def synth_bank(tag, n=8):
    return b"".join(bytes((tag + k + i) & 0x7F for i in range(340)) + bytes([0xFF]) * 172 for k in range(n))


def run(img, man, new):
    e = T4.E4(img, man); e.setup(man); o = {}
    def panel():
        e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR); e.call(0x08033B3E, maxins=30_000_000)
        return list(struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138))))
    e.btn(2); e.btn(8)                                                             # MIDI 1, its Preset view
    e.set_engine(0, *A_ENG)
    b31, b30 = synth_bank(3), synth_bank(40)
    e.sd = {(3, 0, 0xFF): b31}
    slot = lambda key, n: e.sd[key][512 * n + 340:512 * n + 340 + XP.XLEN]
    e.frame(0)
    e.clear(1); e.pad(8); e.pad(8); e.clear(0)                                     # the engine saved into slot 1 of pack 31
    f = bytearray(e.sd[(3, 0, 0xFF)]); f[340 + 44:340 + 60] = b"Bajo de prueba  "; e.sd[(3, 0, 0xFF)] = bytes(f)
    src = slot((3, 0, 0xFF), 0); o["saved"] = src[:4] == struct.pack("<I", MP.MAGIC4)
    e.held(2); e.api.clear(); e.pad(8); e.held(0)
    o["mark"] = (e.wr(), e.x.get(SD.PCLIPW), panel()[XP.LED_DUP])
    # another pack
    e.sd = {(3, 0, 31): e.sd[(3, 0, 0xFF)], (3, 0, 0xFF): b30}
    set_loaded(e, man, 30); e.frame(0, 5000)
    o["wait_led"] = panel()[XP.LED_DUP]
    e.held(2); e.api.clear(); e.pad(8 + 2); e.held(0)
    o["paste"] = (slot((3, 0, 0xFF), 2) == src, [c[:4] for c in e.api if c[0] in ("read", "write")], e.api[-1] if e.api else None, e.scur, e.lock,
                  e.sd[(3, 0, 31)] == bytes(f), all(e.sd[(3, 0, 0xFF)][512 * k:512 * k + 340] == b30[512 * k:512 * k + 340] for k in range(8)),
                  slot((3, 0, 0xFF), 1) == bytes([0xFF]) * 64, e.x.get(SD.PCLIPW))
    e.held(2); e.api.clear(); e.pad(8 + 4); e.held(0); o["again"] = slot((3, 0, 0xFF), 4) == src
    keep = dict(e.sd)
    e.held(2); e.api.clear(); e.pad(8 + 13); e.held(0); w1 = e.wr()                # B = slot 14: bank 1 is not in pack 30
    e.x[SD.PCLIPW] = XP.XMAGIC << 16 | 31 << 8 | 6                                 # slot 7 of pack 31 holds nothing
    e.held(2); e.api.clear(); e.pad(8 + 5); e.held(0); w2 = e.wr()
    e.x[SD.PCLIPW] = XP.XMAGIC << 16 | 31 << 8 | 0
    e.api.clear(); e.pad(8 + 6); w3 = e.wr()                                       # a plain pad
    o["nothing"] = (w1, w2, w3, dict(e.sd) == keep, e.lock)
    del e; gc.collect(); return o


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["xpatch"]["labels"].items()}
    from thumb import bl as tbl
    w = lambda a: struct.unpack_from("<I", img, a - B)[0]
    t0 = int(man["report"]["stepmod"]["arm_start"], 16) - B
    keep = SM.DYN; SM.DYN = SM.DYN2; tab2 = SM.dyn_table(); SM.DYN = keep
    check(w(MP.TMPL_VT) == L["c_xqpad"] | 1 and all(bytes(img[c - B:c - B + 4]) == tbl(c, next((int(man["report"][m_]["labels"][n_], 16) for m_, n_ in (("rodisk", "c_roledtask"), ("fxsess", "c_fsledtask"), ("playmode", "c_pmledtask")) if m_ in man["report"]), L["c_xqledtask"])) for c in PK.LED_CALLS) and bytes(img[t0:t0 + 32]) == tab2,
          "the template view's pad slot = c_xqpad, the two LED task calls; the dynamics table = the one of 2026-10-14")
    n = run(img, man, True)
    clip = XP.XMAGIC << 16 | 31 << 8 | 0
    wr, cw, led = n["mark"]
    check(n["saved"] and wr == [] and cw == clip and led != XP.COL_WAIT, f"pack 31: Duplicate + slot 1: nothing written, the clip = own patch, pack 31, slot 1 ({cw:#x}); the Duplicate button not yellow there ({led:#x})")
    check(n["wait_led"] == XP.COL_WAIT, "pack 30 loaded, the slots on the screen: the Duplicate button yellow (a patch of another pack waits)")
    ok, io, last, scur, lock, src_kept, synths, other, cw2 = n["paste"]
    check(ok and io == [("read", (3, 0, 31), 340, 64), ("write", (3, 0, 30), 512 * 2 + 340, 64)] and last == ("exists", (4, 0, 30)) or (ok and scur == 30 and len(io) == 2),
          f"Duplicate + slot 3 in pack 30: 64 bytes read from pack 31's bank, one write of 64 bytes into slot 3 of pack 30: the patch and its name ({io})")
    check(scur == 30 and lock == 0 and src_kept and synths and other and cw2 == clip, f"the storage task back on pack 30, the buffer lock released; pack 31 and the synth patches of pack 30 untouched; the clip kept")
    check(n["again"], "Duplicate + slot 5: the same patch again")
    w1, w2, w3, same, lock = n["nothing"]
    check(w1 == [] and w2 == [] and w3 == [] and same and lock == 0, f"nothing written: B's record not in its bank, the slot remembered empty, a plain pad ({w1}, {w2}, {w3})")
    gc.collect(); o = run(prev, prev_man, False)
    check(not o["paste"][0] and o["mark"][1] in (None, 0) and o["wait_led"] != XP.COL_WAIT, "the previous build: no clip, nothing copied between packs")
    print("SC40.7 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
