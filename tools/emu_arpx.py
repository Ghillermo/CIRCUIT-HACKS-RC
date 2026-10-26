"""SC47.2 ARM tests (tools/arpx.py, arp.use_bpm0): the arpeggiator's input from a held step and from an external keyboard, Shift + a key = latch, the
stopped arpeggio at the project's BPM.  Through the controller, the real LED task call and the MIDI-in dispatcher (0x08051720):

    python tools/emu_arpx.py NEW.bin NEW_manifest.json [OLD.bin OLD_manifest.json]      (OLD = SC47.1 / Beta 3.28)
    python tools/emu_arpx.py --tempo NEW.bin NEW_manifest.json OLD.bin OLD_manifest.json   (the RC: RC2.10 / RC2.09, only the stopped tempo)

  * Synth 1, a chord at step 0 (64, 60, 67), its pattern's arpeggiator on (up), stopped, the project at 60 BPM (p1 of the tempo store 120):
    holding step 1 = only the first note on (the stock's audition), the LED task = the first off, the arpeggio on (the step's order: 64, 60,
    67); 250 ms later the next one (OLD:
    the three notes at once, 125 ms); letting go of the step = the last note off, nothing more; the arpeggiator off = the stock's three notes;
  * the step held, the transport started, the step let go (the stock sends no note-off): the LED task ends the arpeggio;
  * an external keyboard on Synth 1's channel: the toggle off = every note to the stock as before; on = the first to the stock, the second held
    (the recorder by us), the LED task stops the first through the listener's chain and starts the arpeggio; letting go of both = the recorder's
    note-off for ours, nothing to the stock, the arpeggio ends; an internal injection is left alone;
  * latch (the arpeggiator off): Shift + a key = its note on, its release ignored; with Shift the keys yellow, the latched one green; the next
    press of the key = its note off, nothing else; then it plays as always; (the arpeggiator on) two latched keys = an arpeggio that goes on
    (in the pressed order);
    pressing them stops it;
  * Advanced Setup pad 22: the toggle (bit 2 of gmdrum's flags in both copies, the save asked), green / dim.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_LR, UC_ARM_REG_PC
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_arp as EA_  # noqa: E402
from emu_sc08 import CONT  # noqa: E402
import arp as A  # noqa: E402
import arpx as X  # noqa: E402
import gmdrum as G  # noqa: E402

MSG = 0x2006E100
DISPATCH, LIS_ON, LIS_OFF, REC_OFF = 0x08051720, 0x08034D10, 0x08034D56, 0x0802E5CC
CHORD = [(64, 18, 0, 100), (60, 18, 0, 90), (67, 12, 0, 80)]


class EX(EA_.EA):
    def __init__(self, img, man):
        super().__init__(img, man)
        self.lis, self.rec_off = [], []
        def skip(uc): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        def lis(uc, a, s, d):
            self.lis.append(("on" if a == LIS_ON else "off", uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2) & 0xFF, uc.reg_read(UC_ARM_REG_R3) & 0xFF)); skip(uc)
        for f in (LIS_ON, LIS_OFF): self.uc.hook_add(UC_HOOK_CODE, lis, begin=f, end=f)
        def ro(uc, a, s, d): self.rec_off.append((uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2))); skip(uc)
        self.uc.hook_add(UC_HOOK_CODE, ro, begin=REC_OFF, end=REC_OFF)
        self.R = man["report"]

    def lab(self, m, k): return int(self.R[m]["labels"][k], 16)

    def note_view(self, chord=CHORD, setting=0x80 | A.M_UP):
        p = self.playing(0)
        base = self.settings(0, p) - 0x380
        self.uc.mem_write(base, EA_.chord_steps(chord))
        self.call(self.A["c_arset"], 0, p, setting)
        self.set_p0(self.r32(CONT + 0x188), 0); self.press(0); self.release(0); self.press(9); self.release(9)
        self.transport(0); self.w32(A.HAL_TICK, 100000)
        self.setp(A.TEMPO, 0, bytes([60])); self.setp(A.TEMPO, 1, bytes([120]))
        return p

    def live(self):
        self.call(self.A["c_arst"], 0, 1); s = self.uc.reg_read(UC_ARM_REG_R0)
        return bytes(self.uc.mem_read(s, 28))

    def midi(self, status, n, v, inj=False):
        a = self.r32(X.CTX); fl = self.r8(a + 0x14); ch = self.r8(a + 4)                  # Synth 1's channel
        self.uc.mem_write(a + 0x14, bytes([(fl | 1 | X.INJ) if inj else ((fl | 1) & ~X.INJ)]))
        self.uc.mem_write(MSG, bytes([status | ch, n, v, 0])); self.call(DISPATCH, a, MSG, maxins=20_000_000)
        self.uc.mem_write(a + 0x14, bytes([fl]))

    def ifc_ons(self): return [x[2] for x in self.ifc if x[0] == "on"]


def audition(img, man):
    o = {}
    e = EX(img, man); e.note_view()
    pifc = e.r32(EA_.PLAYER + 0x4C)
    e.ifc.clear(); e.pad(0, up=False); o["press"] = e.ifc_ons()
    e.ifc.clear(); e.ledtask(); o["led0"] = list(e.ifc)
    e.ifc.clear(); e.w32(A.HAL_TICK, 100249); e.ledtask(); o["led249"] = list(e.ifc)
    e.ifc.clear(); e.w32(A.HAL_TICK, 100250); e.ledtask(); o["led250"] = list(e.ifc)
    e.ifc.clear(); e.unpad(0); o["rel"] = list(e.ifc)
    e.ifc.clear(); e.w32(A.HAL_TICK, 101000); e.ledtask(); o["after"] = list(e.ifc); o["live_after"] = e.live()
    o["pifc"] = pifc
    # the transport started while the step is held
    e.ifc.clear(); e.w32(A.HAL_TICK, 102000); e.pad(0, up=False); e.ledtask(); o["held"] = e.live()
    e.transport(1); e.unpad(0); e.transport(0); o["held_rel"] = e.live()
    e.ifc.clear(); e.w32(A.HAL_TICK, 103000); e.ledtask(); o["clean"] = e.live(); o["clean_ifc"] = list(e.ifc)
    del e; gc.collect()
    e = EX(img, man); e.note_view(setting=0)
    e.ifc.clear(); e.pad(0, up=False); o["off_press"] = e.ifc_ons(); e.unpad(0)
    del e; gc.collect()
    return o


def tempo(img, man):
    """two held pads (the arpeggiator's input), stopped at 60 BPM: when the second note comes"""
    e = EX(img, man); e.note_view()
    e.pad(20, up=False); e.pad(17, up=False); e.ifc.clear(); e.ledtask()
    out = []
    for t in (100124, 100125, 100249, 100250):
        e.ifc.clear(); e.w32(A.HAL_TICK, t); e.ledtask(); out.append(len(e.ifc) > 0)
    e.unpad(17); e.unpad(20)
    del e; gc.collect()
    return out


def external(img, man):
    o = {}
    e = EX(img, man); e.note_view()
    pifc = e.r32(EA_.PLAYER + 0x4C)
    def ev(): r = (list(e.lis), list(e.rec_on), list(e.rec_off), list(e.ifc)); e.lis.clear(); e.rec_on.clear(); e.rec_off.clear(); e.ifc.clear(); return r
    ev()
    e.midi(0x90, 60, 100); e.midi(0x90, 64, 90); o["off_on"] = ev(); e.midi(0x80, 64, 0); e.midi(0x80, 60, 0); o["off_off"] = ev(); o["off_live"] = e.live()
    if "arpx" in e.R:
        e.call(e.lab("gmdrum", "c_gmput"), G.B_FLAGS, X.F_ARX); e.call(e.lab("arpx", "c_xtog")); o["tog"] = e.uc.reg_read(UC_ARM_REG_R0)
    ev()
    e.midi(0x90, 60, 100); o["first"] = ev()
    e.midi(0x90, 64, 90); o["second"] = ev()
    e.ledtask(); o["led0"] = ev()
    e.w32(A.HAL_TICK, 100250); e.ledtask(); o["led250"] = ev()
    e.midi(0x80, 64, 0); o["rel64"] = ev()
    e.midi(0x80, 60, 0); o["rel60"] = ev(); o["live"] = e.live()
    e.midi(0x90, 62, 100, inj=True); e.midi(0x90, 65, 100, inj=True); o["inj"] = ev(); e.midi(0x80, 62, 0, inj=True); e.midi(0x80, 65, 0, inj=True)
    o["pifc"] = pifc
    del e; gc.collect()
    return o


def latch(img, man):
    o = {}
    e = EX(img, man); e.note_view(setting=0)
    e.ifc.clear(); e.pad(20, shift=True); o["sh"] = list(e.ifc)                    # pad 21 = 67
    o["leds_sh"] = e.pads(shift=True); o["leds"] = e.pads()
    e.ifc.clear(); e.pad(20); o["again"] = list(e.ifc)
    e.ifc.clear(); e.pad(20); o["normal"] = list(e.ifc)
    del e; gc.collect()
    e = EX(img, man); e.note_view()
    pifc = e.r32(EA_.PLAYER + 0x4C)
    e.ifc.clear(); e.pad(20, shift=True); e.pad(17, shift=True); o["arp_press"] = list(e.ifc)    # 67, then 62
    e.ifc.clear(); e.ledtask(); o["arp_led0"] = list(e.ifc)
    e.ifc.clear(); e.w32(A.HAL_TICK, 100250); e.ledtask(); o["arp_led1"] = list(e.ifc)
    e.ifc.clear(); e.w32(A.HAL_TICK, 100500); e.ledtask(); o["arp_led2"] = list(e.ifc)
    e.ifc.clear(); e.pad(17); e.pad(20); o["arp_stop"] = list(e.ifc); o["arp_live"] = e.live()
    o["pifc"] = pifc
    del e; gc.collect()
    return o


def toggle(img, man):
    import emu_gmdrum as EGM
    import emu_sc42_6 as XX
    e = EGM.EG(Path(img).read_bytes() if isinstance(img, (str, Path)) else img, man)
    e.setup(True, adv=1); f0 = XX.frame(e); e.unpend(); e.pad(X.PAD_ARX); f1 = XX.frame(e)
    o = dict(flags=[e.param(G.P0, c) for c in (0, 1)], pending=e.pending(), led=(f0[X.PAD_ARX], f1[X.PAD_ARX]))
    e.pad(X.PAD_ARX); f2 = XX.frame(e); o["flags2"] = e.param(G.P0, 0); o["led2"] = f2[X.PAD_ARX]
    del e; gc.collect()
    return o


def main(img, man, old=None, oman=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    VI = EA_.VIEW_IFC
    a = audition(img, man); P = a["pifc"]
    check(a["press"] == [64], f"a held step, the arpeggiator on: only the first note on ({a['press']})")
    check(a["led0"] == [("off", VI, 64), ("on", P, 64)], f"the LED task: the first off (the view's interface), the arpeggio's first (the step's order) on ({a['led0']})")
    check(a["led249"] == [] and a["led250"] == [("off", P, 64), ("on", P, 60)], f"60 BPM, 1/16: the next one 250 ms later ({a['led249']}, {a['led250']})")
    check(("off", P, 60) in a["rel"] and a["after"] == [] and a["live_after"][A.S_N] == 0, f"the step let go: the last note off, then nothing ({a['rel']}, {a['after']})")
    check(a["held"][A.S_N] == 3 and a["held_rel"][A.S_N] == 3 and a["clean"][A.S_N] == 0 and a["clean"][A.S_FL] == 0,
          f"the transport started with the step held: the LED task ends it (held {a['held'][:1]}, after {a['clean'][:1]}, {a['clean_ifc']})")
    check(sorted(a["off_press"]) == [60, 64, 67], f"the arpeggiator off: the stock's three notes ({a['off_press']})")
    x = external(img, man); P = x["pifc"]
    check([l[:3] for l in x["off_on"][0]] == [("on", 0, 60), ("on", 0, 64)] and [l[:3] for l in x["off_off"][0]] == [("off", 0, 64), ("off", 0, 60)]
          and x["off_live"][A.S_N] == 0, f"the toggle off: every external note to the stock as before ({x['off_on'][0]}, {x['off_off'][0]})")
    check(x.get("tog") == 1, "the toggle on (gmdrum's flags bit 2)")
    check([l[:3] for l in x["first"][0]] == [("on", 0, 60)], f"on: the first note to the stock ({x['first']})")
    check(x["second"][0] == [] and [r[0] for r in x["second"][1]] == [64], f"the second held: not to the stock, the recorder by us ({x['second']})")
    check([l[:3] for l in x["led0"][0]] == [("off", 0, 60)] and ("on", P, 60) in x["led0"][3], f"the LED task: the first stopped through the listener, the arpeggio starts ({x['led0']})")
    check(x["led250"][3] == [("off", P, 60), ("on", P, 64)], f"250 ms later: the next one ({x['led250'][3]})")
    check(x["rel64"][0] == [] and [r[0] for r in x["rel64"][2]] == [64], f"the second let go: nothing to the stock, the recorder's note-off ({x['rel64']})")
    check(x["rel60"][0] == [] and x["live"][A.S_N] == 0 and x["live"][A.S_FL] == 0, f"the first let go: nothing more to the stock, the arpeggio ends ({x['rel60']})")
    check([l[:3] for l in x["inj"][0]] == [("on", 0, 62), ("on", 0, 65)], f"an internal injection: left alone ({x['inj'][0]})")
    lt = latch(img, man); P = lt["pifc"]
    check([z[0] for z in lt["sh"]] == ["on"] and lt["sh"][0][2] == 67, f"Shift + a key: its note on, the release ignored ({lt['sh']})")
    ks = lt["leds_sh"][16:32]
    check(lt["leds_sh"][20] == X.COL_LAT and all(c == X.COL_AV for i, c in enumerate(ks) if i + 16 != 20), f"with Shift: keys yellow, the latched one green ({[hex(c) for c in ks]})")
    check(lt["leds"][16:32] != lt["leds_sh"][16:32] and X.COL_AV not in lt["leds"][16:32], "without Shift: the keyboard's own colours")
    check(lt["again"] == [("off", VI, 67)], f"the next press: its note off, nothing else ({lt['again']})")
    check([z[0] for z in lt["normal"]] == ["on", "off"], f"then the key as always ({lt['normal']})")
    check(lt["arp_press"] == [("on", VI, 67)] and lt["arp_led0"] == [("off", VI, 67), ("on", P, 67)] and lt["arp_led1"] == [("off", P, 67), ("on", P, 62)]
          and lt["arp_led2"] == [("off", P, 62), ("on", P, 67)], f"two latched keys, the arpeggiator on (the pressed order): it goes on ({lt['arp_press']}, {lt['arp_led0']}, {lt['arp_led1']}, {lt['arp_led2']})")
    check(lt["arp_live"][A.S_N] == 0 and lt["arp_live"][A.S_FL] == 0, f"pressing them: the arpeggio ends ({lt['arp_stop']})")
    tg = toggle(img, man)
    check(all(p[1] == G.SIG and p[2] & X.F_ARX for p in tg["flags"]) and tg["pending"], f"Advanced Setup pad 22: on, in both copies, the save asked ({[p.hex() for p in tg['flags']]})")
    check(tg["led"] == (X.COL_OFF, X.COL_ON) and not tg["flags2"][2] & X.F_ARX and tg["led2"] == X.COL_OFF, f"pad 22: dim / green, again off ({tg['led']}, {tg['led2']})")
    tp = tempo(img, man)
    check(tp == [False, False, False, True], f"held pads, 60 BPM: the next note 250 ms later ({tp})")
    if old is not None:
        ao = audition(old, oman); to = tempo(old, oman)
        check(sorted(ao["press"]) == [60, 64, 67] and to[1], f"OLD: the held step's three notes; the arpeggio 125 ms later at 60 BPM (p1 = 120) ({ao['press']}, {to})")
    print(f"{man.get('marker', '?')} ARPX RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


def main_tempo(img, man, old, oman):
    fails = 0
    tp, to = tempo(img, man), tempo(old, oman)
    for c, m in ((tp == [False, False, False, True], f"held pads, 60 BPM (p1 120): the next note 250 ms later ({tp})"),
                 (to[1], f"OLD: 125 ms later (the p1 bug reproduced: {to})")):
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    print(f"{man.get('marker', '?')} ARP TEMPO RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    if a[1] == "--tempo":
        sys.exit(1 if main_tempo(Path(a[2]).read_bytes(), json.loads(Path(a[3]).read_text()), Path(a[4]).read_bytes(), json.loads(Path(a[5]).read_text())) else 0)
    old = (Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) if len(a) > 4 else (None, None)
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), *old) else 0)
