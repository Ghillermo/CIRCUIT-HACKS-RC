"""In-unit stress run for a Circuit Tracks running S714D2 (tools/sxpanel.py + tools/patscan.py): random panel gestures sent over USB (the controller's
own entries, as real presses), with the transport playing most of the time, while patscan watches the patterns and the black box everything else.
Every 3 s the black box is read; the run stops when a record is frozen (or the device stops answering: a restart) and prints it.

Never pressed: Preset (8), Scales (18: Shift + Scales = the packs view), Save (25), Projects (26) - the gestures that write the card or delete.
MIDI 1 / 2 pressed twice still open their Preset view (own-synth patch slots): run it on a project of the internal pack (pack 1, read-only for the
mod) so nothing of the mod can be written to the card.

    python tools/panelstress_dev.py [seconds] [gestures/s] [--seed N]
"""
from __future__ import annotations
import random, struct, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ctremote as CR
import bbread as BR
import blackbox as BB
import patscan as PS
import sxpanel as SP

TRACKS = list(range(8))
VIEWS = [9, 10, 11, 12, 13, 14, 15]                 # the track views, Patterns, Mixer, FX
OTHER = [19, 20, 21, 22]                           # Octave, 1-16 / 17-32, Tempo
CLEAR, DUP, REC, PLAY = 23, 24, 16, 17


class Panel:
    def __init__(self, L, log):
        self.L, self.log, self.seq, self.lost = L, log, 0, 0
    def g(self, kind, ident, val=0):
        self.seq = (self.seq + 1) & 0x7F
        self.L.send(bytes(list(SP.RD.SIG) + [SP.CMD, self.seq, kind, ident, val, 0, 0, 0, 0, 0xF7]))
        self.log.write(f"{time.time():.3f} {kind} {ident} {val}\n")
        t = time.time(); acc = b""
        want = bytes(list(SP.RD.SIG) + [0x45, self.seq])
        while time.time() - t < 1.5:
            try: c, p1 = self.L.q.get(timeout=0.02)
            except Exception: continue
            self.L._readd(p1); acc += c
            if want in acc: self.lost = 0; return True
        self.lost += 1
        return False
    def tap(self, b): self.g(1, b); self.g(2, b)
    def pad(self, p, v=100): self.g(3, p, v)
    def padup(self, p): self.g(4, p)
    def knob(self, k, d): self.g(5, k, max(0, min(127, 64 + d)))
    def shift(self, on): self.g(6, 0, 1 if on else 0)


def show(full):
    st = full[BB.O.ST]
    print(f"black box: state {st:#x}")
    tag, val, adr = struct.unpack_from("<3I", full, BB.O.STK1)
    if tag == 3:
        print(f"  patscan: value {val} at {adr:#x}")
        ring = full[BB.O.STK1 + 12:BB.O.STK1 + 12 + 16 + 8 * PS.NRING]
        idx = struct.unpack_from("<I", ring, 4)[0]
        for i in range(PS.NRING):
            t, a, b, c, p = struct.unpack_from("<I4B", ring, 16 + 8 * ((idx + i) % PS.NRING))
            if t: print(f"  MIDI in {t} ms: {a:02X} {b} {c}")
    elif tag in (1, 2):
        print(f"  paintguard skipped a {'probability' if tag == 1 else 'velocity'} of {val}")
    if st & BB.ST_FAULT:                                  # a fault capture (vector 12 = a DWT watch: the writer's PC / LR)
        pc, lr = struct.unpack_from("<2I", full, BB.O2.RPC)
        print(f"  fault capture, vector {full[BB.O2.XTRA]}: PC {pc:#010x}  LR {lr:#010x}")
        regs = struct.unpack_from("<8I", full, BB.O.PC + 8)
        print("  r0-r3 " + " ".join(f"{x:#010x}" for x in regs[:4]) + f"  r12 {regs[4]:#010x}  xPSR {regs[5]:#010x}")
    print("  (read the whole record with: python tools/bbread.py --firmware S714D2)")


def main(seconds, rate, seed):
    rnd = random.Random(seed)
    L = CR.Link("Circuit Tracks")
    log = Path.home() / "Documents" / time.strftime("panelstress_%Y-%m-%d_%H%M%S.log")
    out = log.open("w", encoding="utf-8")
    P = Panel(L, out)
    held = []                                         # pads held
    mod = None                                        # a modifier held: ("shift",) or ("btn", id)
    n, t0, nxt, stalls = 0, time.time(), time.time() + 3, 0
    try:
        st = BR.read(L, 0, 64)[BB.O.ST]
        print("start: record state", hex(st), flush=True)
        if st & 1: print("a record is frozen already: read it / clear it first (bbread.py --clear)"); return
        P.tap(PLAY)
        while time.time() - t0 < seconds:
            k = rnd.random()
            if k < 0.36:                                                   # pads: press, release later
                if held and rnd.random() < 0.55: P.padup(held.pop(rnd.randrange(len(held))))
                else:
                    p = rnd.randrange(32); P.pad(p, rnd.choice([1, 40, 80, 100, 127, rnd.randrange(1, 128)])); held.append(p)
            elif k < 0.54: P.knob(rnd.randrange(8), rnd.choice([-20, -5, -2, -1, 1, 2, 5, 20]))
            elif k < 0.66: P.tap(rnd.choice(TRACKS))
            elif k < 0.76: P.tap(rnd.choice(VIEWS))
            elif k < 0.80: P.tap(rnd.choice(OTHER))
            elif k < 0.95:                                                 # a modifier: hold, then let go
                if mod:
                    if mod == ("shift",): P.shift(False)
                    else: P.g(2, mod[1])
                    mod = None
                else:
                    c = rnd.choice(["shift", CLEAR, DUP, REC, "shift", CLEAR, DUP])
                    if c == "shift": P.shift(True); mod = ("shift",)
                    else: P.g(1, c); mod = ("btn", c)
            elif k < 0.97: P.tap(CLEAR); P.tap(DUP)                         # Clear, Duplicate taps alone
            else: P.tap(PLAY)
            n += 1
            if len(held) > 4: P.padup(held.pop(0))
            if P.lost >= 3:
                print(f"{time.time() - t0:.0f} s: the device stopped answering (a restart?)", flush=True); break
            time.sleep(max(0.0, 1.0 / rate))
            if time.time() >= nxt:
                nxt = time.time() + 3
                st = BR.read(L, 0, 64)[BB.O.ST]
                print(f"{time.time() - t0:6.0f} s, {n} gestures, record state {st:#x}", flush=True)
                if st & 1 and (st & ~(BB.ST_FROZEN | BB.ST_STALL)) == 0 and "--stop-stall" not in sys.argv:
                    full = BR.read(L, 0, 1024)                # a pause only (S714D3: > 400 ms): kept on disk, cleared, the run goes on
                    f = log.with_name(log.stem + f"_stall{stalls}.bin"); f.write_bytes(full); stalls += 1
                    pcs = [hex(struct.unpack_from("<I", full, BB.O.PC + 8 * k)[0]) for k in range(full[BB.O.NS])]
                    print(f"  a pause of the main loop (kept: {f.name}), samples {pcs}; cleared", flush=True)
                    BR.clear(L); continue
                if st & 1: break
        for p in held: P.padup(p)
        if mod == ("shift",): P.shift(False)
        elif mod: P.g(2, mod[1])
    finally:
        out.close()
        L.close()
    time.sleep(6)
    L = CR.Link("Circuit Tracks")
    try:
        full = BR.read(L, 0, 1024)
        if full[BB.O.ST] & 1: show(full)
        else: print(f"no record after {time.time() - t0:.0f} s, {n} gestures")
    finally:
        L.close()
    print("log:", log)


if __name__ == "__main__":
    a = sys.argv[1:]
    secs = float(a[0]) if a and not a[0].startswith("--") else 600
    rate = float(a[1]) if len(a) > 1 and not a[1].startswith("--") else 12
    seed = int(a[a.index("--seed") + 1]) if "--seed" in a else 1
    main(secs, rate, seed)
