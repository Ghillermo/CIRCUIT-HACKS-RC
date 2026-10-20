"""SC45.1 ARM tests: tools/mutebank.py (with the recording of the internal routes on, nothing is recorded into a note track muted in the Mixer).

    python tools/emu_mutebank.py SC45.1.bin SC45.1_manifest.json SC45.bin SC45_manifest.json
  * the hooks: the three recorder gates' b.w -> our heads, which go on to fxsess's;
  * the Mixer's mute: MIDI 1's track pad through the stock's handler (0x08046626) -> c_mbmuted(2) = 1, Synth 1 / MIDI 2 = 0; again = 0;
  * the gates (recording), every combination of the Setup toggle, the «internal» bit and the target: MIDI 1 muted / Synth 1 / Drum 1 (the note
    gates' track 0x10) / the automation gate with an id of MIDI 1's and one of Synth 1's (the stock's table): with the toggle on, MIDI 1 muted
    records nothing; everything else as the previous build (toggle off: external yes, internal no; toggle on: yes); unmuted again: recorded;
  * the user's gesture: a held step of the muted MIDI 1 auditioned (MIDI 1 on Synth 1's channel, the toggle on, recording; the audition's call
    0x0804B07A as the track view's listener makes it): sound and MIDI out as the previous build, nothing recorded into MIDI 1 (the previous build
    did); MIDI 1 not muted: as before.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as LS  # noqa: E402
from emu_sc05 import CTX  # noqa: E402
from thumb import b_w  # noqa: E402
import fxsess as FS  # noqa: E402
import mutebank as MB  # noqa: E402

BASE = 0x08010000
REC = 0x2003C168
MGR = LS.MGR
PT_ON, PT_OFF, PT_AUTO = 0x0802E5BC, 0x0802E61C, 0x0802E66C      # inside the stock gates: where they hand the message to the track's recorder
VIEW_M1, NOTE_ON, NOTE_OFF = 0x200418C8, 0x0804B07A, 0x0804AF5A  # MIDI 1's track view; its live note on (view, note, vel, pad) / off (view, pad)


class EM(LS.EL):
    def __init__(self, img):
        super().__init__(img)
        self.hits = []
        def h(uc, a, s, d):
            if a == PT_ON: self.hits.append(("on", uc.reg_read(UC_ARM_REG_R7), uc.reg_read(UC_ARM_REG_R4)))
            elif a == PT_OFF: self.hits.append(("off", uc.reg_read(UC_ARM_REG_R6), uc.reg_read(UC_ARM_REG_R4)))
            else: self.hits.append(("auto", uc.reg_read(UC_ARM_REG_R3), uc.reg_read(UC_ARM_REG_R5)))
        for p in (PT_ON, PT_OFF, PT_AUTO): self.uc.hook_add(UC_HOOK_CODE, h, begin=p, end=p)
    def r0(self, fn, *a): self.call(fn, *a, maxins=4_000_000); return self.uc.reg_read(UC_ARM_REG_R0)
    def toggle(self, on): self.uc.mem_write(FS.SETUP_OBJ + FS.REC_OFF, struct.pack("<H", FS.REC_ON if on else 0x36EE))
    def internal(self, on):
        ctx = self.r32(0x200069E4); fl = self.r8(ctx + 0x14); self.uc.mem_write(ctx + 0x14, bytes([fl & ~0x20 | (0x20 if on else 0)]))
    def mute_pad(self, t): self.call(0x08046626, MB.MIX_VIEW, t, 127, maxins=4_000_000)
    def muted(self, t):
        st = self.r32(self.r32(MB.MIX_VIEW + 0x68) + self.r32(MB.MIX_VIEW + 0x60) * t)
        return self.r8(self.r0(MB.PARAM_GET, st, 0))


def auto_ids(img):
    """an id of the automation gate's table for MIDI 1 (recorder index 2) and one for Synth 1 (0)"""
    out = {}
    for i in range(128):
        t, lane = img[MB.AUTO_TAB - BASE + 2 * i], img[MB.AUTO_TAB - BASE + 2 * i + 1]
        if t in (0, 2) and lane != 0xFF and t not in out: out[t] = i
    return out


def gate_matrix(img, man, mute=True):
    """{(toggle, internal, target): recorded?} for the three gates"""
    e = EM(img)
    e.recording(True)
    if mute: e.mute_pad(2)
    ids = auto_ids(img)
    res = {}
    for tog in (0, 1):
        for intl in (0, 1):
            e.toggle(tog); e.internal(intl)
            for name, call, want in (("on M1", (MB.GATE_ON, REC, 60, 100, 2), ("on", 2)), ("on S1", (MB.GATE_ON, REC, 60, 100, 0), ("on", 0)),
                                     ("on D1", (MB.GATE_ON, REC, 1, 100, 0x10), ("on", 0x10)),
                                     ("off M1", (MB.GATE_OFF, REC, 60, 2), ("off", 2)), ("off S1", (MB.GATE_OFF, REC, 60, 0), ("off", 0)),
                                     ("auto M1", (MB.GATE_AUTO, REC, ids[2], 77), ("auto", 2)), ("auto S1", (MB.GATE_AUTO, REC, ids[0], 77), ("auto", 0))):
                e.hits.clear(); e.call(*call, maxins=4_000_000)
                res[(tog, intl, name)] = any(h[:2] == want for h in e.hits)
            e.internal(0)
    return e, res


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["mutebank"]["labels"].items()}
    FL = {k: int(v, 16) for k, v in man["report"]["fxsess"]["labels"].items()}
    at = lambda a: bytes(img[a - BASE:a - BASE + 4])
    tgt = {g: int(v, 16) for g, v in ((int(k[5:], 16), v) for k, v in man["report"]["mutebank"]["prev"].items())}
    check(all(at(g) == b_w(g, L[f"c_mbgate_{g:x}"]) and tgt[g] == FL[f"c_fsgate_{g:x}"] for g in FS.GATES)
          and man["report"]["mutebank"].get("hole"), "the hooks: the three gates -> ours (in the hole) -> fxsess's")

    # ---- the Mixer's mute, through the stock's handler
    e = EM(img)
    m0 = [e.r0(L["c_mbmuted"], t) for t in range(4)]
    e.mute_pad(2); m1 = [e.r0(L["c_mbmuted"], t) for t in range(4)] + [e.muted(2)]
    e.mute_pad(2); m2 = [e.r0(L["c_mbmuted"], t) for t in range(4)]
    big = [e.r0(L["c_mbmuted"], t) for t in (4, 7, 0x10, 0xFF)]
    check(m0 == [0, 0, 0, 0] and m1 == [0, 0, 1, 0, 1] and m2 == [0, 0, 0, 0] and big == [0, 0, 0, 0],
          f"the Mixer's MIDI 1 pad (stock handler): c_mbmuted 0..3 = {m0} -> {m1[:4]} (the store {m1[4]}) -> {m2}; drums / none: {big}")
    del e; gc.collect()

    # ---- the gates
    _, new = gate_matrix(img, man); gc.collect()
    _, old = gate_matrix(prev, prev_man); gc.collect()
    _, unm = gate_matrix(img, man, mute=False); gc.collect()
    changed = sorted(k for k in new if new[k] != old[k])
    want_changed = sorted((1, i, n) for i in (0, 1) for n in ("on M1", "off M1", "auto M1"))
    check(changed == want_changed and not any(new[k] for k in want_changed) and all(old[k] for k in want_changed),
          f"MIDI 1 muted, the toggle on (external or internal): nothing recorded (note on, note off, automation); the previous build recorded it ({changed})")
    check(all(new[(0, 0, n)] and not new[(0, 1, n)] for n in ("on M1", "on S1", "on D1", "off M1", "off S1", "auto M1", "auto S1"))
          and all(new[(1, i, n)] for i in (0, 1) for n in ("on S1", "on D1", "off S1", "auto S1")),
          "everything else as before: toggle off = external recorded, internal not; toggle on = Synth 1 / Drum 1 recorded")
    check(unm == old, f"MIDI 1 not muted: as the previous build ({sorted(k for k in unm if unm[k] != old[k])})")

    # ---- the user's gesture: a held step of the muted MIDI 1 auditioned (MIDI 1 on Synth 1's channel), the toggle on, recording.  A step pad
    #      only writes the step object's store; the track view's listener (its slot 8, 0x0804B272) auditions the step's notes through
    #      0x0804B580 -> 0x0804B07A(view, note, vel, pad 0x20); listeners do not run in emulation: the audition's call is made here.
    def audition(image, mute=True):
        e = EM(image)
        e.set_tx_chan(2, 0)                                           # MIDI 1 sends on channel 1 = Synth 1's
        e.btn(2)                                                      # MIDI 1's track view
        if mute: e.mute_pad(2)
        e.toggle(1); e.recording(True)
        e.ev.clear(); e.hits.clear()
        for n in (60, 64, 67): e.call(NOTE_ON, VIEW_M1, n, 100, 0x20, maxins=8_000_000)
        e.call(NOTE_OFF, VIEW_M1, 0x20, maxins=8_000_000)
        return [h for h in e.hits], [x for x in e.ev if x[0] not in ("rec_note_on", "rec_note_off", "rec_param")]
    hn, en = audition(img); gc.collect()
    ho, eo = audition(prev); gc.collect()
    hu, eu = audition(img, mute=False); gc.collect()
    tr = lambda hs: sorted(set((h[0], h[1]) for h in hs))
    check(en == eo and en and not any(h[1] == 2 for h in hn) and any(h[1] == 2 for h in ho) and [h for h in ho if h[1] != 2] == hn,
          f"MIDI 1 muted: the audition sounds / goes out as before ({[x[0] if x[0] != 'ext' else x[1] for x in en][:8]}), recorded nowhere in MIDI 1 "
          f"(now {tr(hn)}, before {tr(ho)})")
    check(hu == ho and eu == eo, f"MIDI 1 not muted: recorded as before ({tr(hu)})")
    print(f"{man.get('marker', '?')} ARM RESULT: {'ALL PASS' if not fails else f'{fails} FAILURES'}")
    return fails


if __name__ == "__main__":
    a = sys.argv
    img, man = Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())
    prev, prev_man = Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())
    sys.exit(1 if main(img, man, prev, prev_man) else 0)
