"""Targeted in-unit stress run (S714D2 or later: sxpanel + patscan): instead of single random presses, short scenarios built from the real gestures of
the features around the open bug (impossible step values): pattern-group chains in the Patterns view, pattern mutate, scenes in the Mixer, step edits in
the track views (Note / Velocity / Gate / probability / Pattern Settings) with Record, all while playing.  The black box is read every 3 s: a pause
(stall only) is kept on disk and cleared; anything else (patscan's find, a fault, a restart) stops the run and is printed.

Buttons: tracks 0-7, Note 9, Velocity 10, Gate 11, probability 12 (Shift + 12 = Pattern Settings), Patterns 13, Mixer 14, FX 15, Record 16, Play 17,
Octave 19 / 20, Clear 23, Duplicate 24.  Never: Preset 8, Scales 18, Save 25, Projects 26.  Run it on a throwaway pack (a copy).

    python tools/scenestress_dev.py [seconds] [--seed N]
"""
from __future__ import annotations
import random, struct, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ctremote as CR
import bbread as BR
import blackbox as BB
from panelstress_dev import Panel, show

NOTE, VEL, GATE, PROB, PATTERNS, MIXER, FX, REC, PLAY, OCT_DN, OCT_UP, CLEAR, DUP = 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 20, 23, 24


class Scen:
    def __init__(self, P, rnd):
        self.P, self.r = P, rnd
    def hold(self, b): self.P.g(1, b)
    def let(self, b): self.P.g(2, b)
    def tap(self, b): self.P.tap(b)
    def pad(self, p, v=100): self.P.pad(p, v); self.P.padup(p)
    def shift_tap(self, b): self.P.shift(True); self.tap(b); self.P.shift(False)
    def pat_pad(self, track, pat): return (pat % 4) * 8 + track          # Patterns view: columns = tracks, rows = the page's 4 patterns

    def patterns_chain(self):
        r = self.r; self.tap(PATTERNS)
        if r.random() < 0.5: self.tap(r.choice([OCT_DN, OCT_UP]))           # the page
        if r.random() < 0.5: self.shift_tap(OCT_UP)                         # chain mode on
        for _ in range(r.randrange(2, 7)):
            t = r.randrange(8); a = r.randrange(4); b = r.randrange(4)
            k = r.random()
            if k < 0.3:                                                     # a group: Shift + start + end
                self.P.shift(True); self.P.pad(self.pat_pad(t, a)); self.P.pad(self.pat_pad(t, max(a, b)))
                self.P.padup(self.pat_pad(t, a)); self.P.padup(self.pat_pad(t, max(a, b))); self.P.shift(False)
            elif k < 0.45:                                                  # a start + K1 = repeats
                self.P.pad(self.pat_pad(t, a)); self.P.knob(0, r.choice([-3, 1, 2, 5])); self.P.padup(self.pat_pad(t, a))
            elif k < 0.55: self.hold(CLEAR); self.pad(self.pat_pad(t, a)); self.let(CLEAR)
            elif k < 0.65: self.hold(DUP); self.pad(self.pat_pad(t, a)); self.pad(self.pat_pad(r.randrange(8), b)); self.let(DUP)
            elif k < 0.8:                                                   # a stock chain: hold one pattern, tap another
                self.P.pad(self.pat_pad(t, a)); self.pad(self.pat_pad(t, b)); self.P.padup(self.pat_pad(t, a))
            else: self.pad(self.pat_pad(t, a))
        if r.random() < 0.2: self.shift_tap(OCT_DN)                         # chain mode off

    def mutate(self):
        r = self.r; self.tap(r.choice([PATTERNS, PATTERNS, MIXER]))
        k = r.random()
        if k < 0.5: self.shift_tap(DUP)                                     # a new seed / lists
        elif k < 0.8:                                                       # the settings page: Shift + Duplicate held, pads, track buttons
            self.P.shift(True); self.hold(DUP); time.sleep(0.45)
            for _ in range(r.randrange(1, 5)):
                if r.random() < 0.7: self.pad(r.randrange(8) + 8 * r.randrange(4))
                else: self.tap(r.randrange(8))
            self.let(DUP); self.P.shift(False)
        else: self.hold(CLEAR); self.tap(DUP); self.let(CLEAR)             # the lists end

    def scenes(self):
        r = self.r; self.tap(MIXER)
        for _ in range(r.randrange(2, 6)):
            k = r.random(); sc = 16 + r.randrange(16)
            if k < 0.35: self.pad(sc)                                       # a scene
            elif k < 0.55: self.P.shift(True); self.pad(sc); self.P.shift(False)     # save a scene
            elif k < 0.62: self.hold(CLEAR); self.pad(sc); self.let(CLEAR)
            elif k < 0.75: self.P.shift(True); self.pad(8 + r.randrange(8)); self.P.shift(False)   # repeats
            elif k < 0.85: self.P.shift(True); self.pad(r.randrange(8)); self.P.shift(False)       # mute next bar
            elif k < 0.92: self.P.pad(15); self.pad(r.randrange(8)); self.P.padup(15)               # solo
            else: self.pad(r.randrange(8))                                                         # mute

    def edit_track(self):
        r = self.r; t = r.randrange(8); self.tap(t)
        view = r.choice([NOTE, NOTE, VEL, GATE, PROB, "settings"])
        if view == "settings": self.shift_tap(PROB)
        else: self.tap(view)
        rec = r.random() < 0.35
        if rec: self.tap(REC)
        for _ in range(r.randrange(3, 10)):
            k = r.random(); p = r.randrange(32)
            if k < 0.5: self.pad(p, r.choice([1, 50, 100, 127]))
            elif k < 0.65: self.P.pad(p); self.P.knob(r.randrange(8), r.choice([-10, -2, 2, 10])); self.P.padup(p)   # a step held + knob
            elif k < 0.75: self.P.pad(p); self.pad(r.randrange(32)); self.P.padup(p)                               # a step held + another
            elif k < 0.82: self.hold(CLEAR); self.pad(p); self.let(CLEAR)
            elif k < 0.88: self.hold(DUP); self.pad(p); self.pad(r.randrange(32)); self.let(DUP)
            elif k < 0.94: self.tap(r.choice([OCT_DN, OCT_UP]))
            else: self.P.knob(r.randrange(8), r.choice([-20, -3, 3, 20]))
        if rec: self.tap(REC)

    def transport(self):
        r = self.r
        if r.random() < 0.6: self.tap(PLAY)
        else: self.tap(r.choice([FX, MIXER, PATTERNS, r.randrange(8)]))


def main(seconds, seed):
    rnd = random.Random(seed)
    L = CR.Link("Circuit Tracks")
    log = Path.home() / "Documents" / time.strftime("scenestress_%Y-%m-%d_%H%M%S.log")
    out = log.open("w", encoding="utf-8")
    P = Panel(L, out); S = Scen(P, rnd)
    plan = [(S.patterns_chain, 3), (S.mutate, 2), (S.scenes, 3), (S.edit_track, 4), (S.transport, 1)]
    names = [f.__name__ for f, w in plan for _ in range(w)]
    funcs = {f.__name__: f for f, _ in plan}
    t0 = time.time(); nxt = t0 + 3; n = 0; stalls = 0
    try:
        st = BR.read(L, 0, 64)[BB.O.ST]
        print("start: record state", hex(st), flush=True)
        if st & 1: BR.clear(L)
        P.tap(PLAY)
        while time.time() - t0 < seconds:
            name = rnd.choice(names); out.write(f"# {time.time():.3f} {name}\n")
            try: funcs[name]()
            except Exception as x: print(f"{time.time() - t0:.0f} s: {x} (the device hung or restarted?)", flush=True); break
            n += 1
            if P.lost >= 3: print(f"{time.time() - t0:.0f} s: the device stopped answering (a restart?)", flush=True); break
            if time.time() >= nxt:
                nxt = time.time() + 3
                st = BR.read(L, 0, 64)[BB.O.ST]
                print(f"{time.time() - t0:6.0f} s, {n} scenarios, record state {st:#x}", flush=True)
                if st & 1 and (st & ~(BB.ST_FROZEN | BB.ST_STALL)) == 0:
                    full = BR.read(L, 0, 1024); f = log.with_name(log.stem + f"_stall{stalls}.bin"); f.write_bytes(full); stalls += 1
                    print(f"  a pause (kept: {f.name}); cleared", flush=True); BR.clear(L); continue
                if st & 1: break
        try:
            P.shift(False)
            for b in (CLEAR, DUP, REC): P.g(2, b)
        except Exception: pass
    finally:
        out.close(); L.close()
    time.sleep(6)
    for k in range(10):
        try: L = CR.Link("Circuit Tracks"); break
        except BaseException: time.sleep(3)
    try:
        full = BR.read(L, 0, 1024)
        if full[BB.O.ST] & 1: show(full); Path(str(log.with_suffix("")) + "_record.bin").write_bytes(full)
        else: print(f"no record after {time.time() - t0:.0f} s, {n} scenarios")
    finally:
        L.close()
    print("log:", log)


if __name__ == "__main__":
    a = sys.argv[1:]
    secs = float(a[0]) if a and not a[0].startswith("--") else 1800
    seed = int(a[a.index("--seed") + 1]) if "--seed" in a else 1
    main(secs, seed)
