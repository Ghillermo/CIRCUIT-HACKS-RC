"""RC2.08 / SC46.3 (tools/kbin.py): an external keyboard plays the own synth of MIDI 1 / 2.  The emulated firmware, notes through the MIDI-in
dispatcher 0x08051720 (as a DIN / USB message):
  * MIDI 1 with its engine on: a note-on on its channel reaches the engine (vcf21's c_vnon with track 2, the note, the velocity) and the recorder's
    gate, not SC06's c_non nor the stock's MIDI out (no echo); its note-off (0x80, and a note-on with velocity 0) reaches c_vnoff, not c_noff;
  * MIDI 2 with its engine off: nothing new (the recorder only);
  * an internal injection (bit 5 of [ctx] + 0x14): nothing new;
  * a note-on with velocity 0: only the note-off that follows (no new note for the engine);
  * a note of the track sent by the device (the transmitter's entry): the engine and the MIDI out (SC06's c_non) as before;
  * the previous build (if given): the engine never sees the external note.

    python tools/emu_kbin.py BUILD.bin manifest.json [PREVIOUS.bin PREVIOUS_manifest.json]
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_LR, UC_ARM_REG_PC
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402  (its import sets vcf21's options)
import kbin as K  # noqa: E402

V = T4.V
MSG = 0x2006E100
DISPATCH, STOCK_TX_ON, STOCK_TX_OFF, REC_GATE = 0x08051720, 0x08029EFE, 0x08029F2A, 0x0802E56A


def run(img, man):
    e = T.EL(Path(img).read_bytes())
    R = man["report"]
    vl = {k: int(v, 16) for k, v in R["vcf20"]["labels"].items()}
    sl = {k: int(v, 16) for k, v in R["sc06"]["labels"].items()}
    hits = []
    def skip(uc): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    def mk(tag, sk):
        def f(uc, a, s, d):
            hits.append((tag, uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2) & 0xFF, uc.reg_read(UC_ARM_REG_R3) & 0xFF))
            if sk: skip(uc)
        return f
    for tag, ad, sk in (("vnon", vl["c_vnon"], False), ("vnoff", vl["c_vnoff"], False), ("non", sl["c_non"], True), ("noff", sl["c_noff"], True),
                        ("tx_on", STOCK_TX_ON, True), ("tx_off", STOCK_TX_OFF, True), ("rec", REC_GATE, True)):
        e.uc.hook_add(UC_HOOK_CODE, mk(tag, sk), begin=ad, end=ad)
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05]))
    e.call(vl["c_von"], 0, maxins=1_000_000); von0 = e.uc.reg_read(UC_ARM_REG_R0) & 0xFF
    e.call(vl["c_von"], 1, maxins=1_000_000); von1 = e.uc.reg_read(UC_ARM_REG_R0) & 0xFF
    A = e.r32(K.CTX); tab = list(e.uc.mem_read(A + 4, 5)); fl = e.r8(A + 0x14)
    e.uc.mem_write(A + 0x14, bytes([fl | 1]))
    def midi(status, ch, n, v, inj=False):
        hits.clear()
        e.uc.mem_write(A + 0x14, bytes([(fl | 1 | (K.INJ if inj else 0)) & ~(0 if inj else K.INJ)]))
        e.uc.mem_write(MSG, bytes([status | ch, n, v, 0])); e.call(DISPATCH, A, MSG, maxins=20_000_000)
        e.uc.mem_write(A + 0x14, bytes([fl | 1]))
        return [h[0] for h in hits], [h for h in hits if h[0] in ("vnon", "vnoff")]
    o = dict(von=(von0, von1), ch=tab)
    o["on"] = midi(0x90, tab[2], 60, 100)
    o["off"] = midi(0x80, tab[2], 60, 0)
    o["on0"] = midi(0x90, tab[2], 62, 90); o["off0"] = midi(0x90, tab[2], 62, 0)
    o["m2"] = midi(0x90, tab[3], 64, 100) if tab[3] != tab[2] else None
    o["inj"] = midi(0x90, tab[2], 65, 100, inj=True)
    hits.clear(); tx = struct.unpack_from("<I", Path(img).read_bytes(), K.TX_VT - 0x08010000)[0] & ~1
    e.call(tx, K.TX, 2, 67, 100, maxins=8_000_000); o["panel"] = [h[0] for h in hits]
    o["flag"] = e.r32(K.FLAG)
    del e; gc.collect()
    return o


def main(img, man, prev=None, pman=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    o = run(img, man)
    check(o["von"][0] == 1 and o["von"][1] == 0, f"MIDI 1's engine on, MIDI 2's off ({o['von']}; channels {[c + 1 for c in o['ch']]})")
    t, v = o["on"]
    check(("vnon", 2, 60, 100) in v and "rec" in t and "non" not in t and "tx_on" not in t, f"note-on on MIDI 1's channel: the engine and the recorder, no MIDI out ({t})")
    t, v = o["off"]
    check(("vnoff", 2, 60, 0) in v and "noff" not in t and "tx_off" not in t, f"its note-off: the engine, no MIDI out ({t})")
    t, v = o["off0"]
    check(any(x[0] == "vnoff" and x[2] == 62 for x in v) and not any(x[0] == "vnon" for x in v) and "noff" not in t,
          f"a note-on with velocity 0: only the engine's note-off ({t})")
    if o["m2"] is not None:
        check("vnon" not in o["m2"][0] and "vnoff" not in o["m2"][0], f"MIDI 2 (engine off): nothing new ({o['m2'][0]})")
    check("vnon" not in o["inj"][0], f"an internal injection: nothing new ({o['inj'][0]})")
    check("vnon" in o["panel"] and "non" in o["panel"], f"a note sent by the track: the engine and SC06's MIDI out ({o['panel']})")
    check(o["flag"] == 0, "the marker cleared")
    if prev:
        p = run(prev, pman)
        check("vnon" not in p["on"][0], f"the previous build: the engine never sees it ({p['on'][0]})")
    print(f"{Path(img).stem} RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text()), a[2] if len(a) > 2 else None,
                       json.loads(Path(a[3]).read_text()) if len(a) > 3 else None) else 0)
