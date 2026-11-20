"""Stress a Circuit Tracks running S714D (tools/patscan.py) with random MIDI from the PC and watch its black box: CCs, NRPNs, notes and pitch bend on
all 16 channels (no program changes, no SysEx, no clock / start / stop), RATE messages a second; every 3 s the record's state is read over USB
(bbread.read); the run stops as soon as the record is frozen and prints its tag, value and address and the last MIDI in (the device's own ring).
Everything sent goes to Documents/midistress_<time>.log too.

    python tools/midistress_dev.py [seconds] [rate] [--seed N] [--ch 1,2,10,16]
"""
from __future__ import annotations
import ctypes, random, struct, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ctremote as CR
import bbread as BR
import blackbox as BB
import patscan as PS

winmm = ctypes.windll.winmm


def main(seconds, rate, seed, chans):
    rnd = random.Random(seed)
    L = CR.Link("Circuit Tracks")
    log = Path.home() / "Documents" / time.strftime("midistress_%Y-%m-%d_%H%M%S.log")
    out = log.open("w", encoding="utf-8")
    def short(st, d1, d2):
        winmm.midiOutShortMsg(L.hout, st | (d1 << 8) | (d2 << 16)); out.write(f"{time.time():.3f} {st:02X} {d1} {d2}\n")
    held = []
    t0 = time.time(); nxt = t0 + 3; n = 0
    try:
        rec = BR.read(L, 0, 64)
        print("start: record state", hex(rec[BB.O.ST]), flush=True)
        while time.time() - t0 < seconds:
            ch = rnd.choice(chans) - 1
            k = rnd.random()
            if k < 0.45:
                short(0xB0 | ch, rnd.randrange(128), rnd.choice([0, 1, 7, 8, 31, 32, 63, 64, 100, 126, 127, rnd.randrange(128)]))
            elif k < 0.65:
                for cc, d in ((99, rnd.randrange(16)), (98, rnd.randrange(128)), (6, rnd.randrange(128))): short(0xB0 | ch, cc, d)
            elif k < 0.95:
                if held and rnd.random() < 0.5:
                    c, nt = held.pop(rnd.randrange(len(held))); short(0x80 | c, nt, 0)
                else:
                    nt = rnd.randrange(128); short(0x90 | ch, nt, rnd.choice([1, 64, 100, 127, rnd.randrange(1, 128)])); held.append((ch, nt))
            else:
                short(0xE0 | ch, rnd.randrange(128), rnd.randrange(128))
            n += 1
            time.sleep(1.0 / rate)
            if time.time() >= nxt:
                nxt = time.time() + 3
                rec = BR.read(L, 0, 64)
                st = rec[BB.O.ST]
                print(f"{time.time() - t0:6.0f} s, {n} messages, record state {st:#x}", flush=True)
                if st & 1:
                    break
        for c, nt in held: short(0x80 | c, nt, 0)
        full = BR.read(L, 0, 1024)
        st = full[BB.O.ST]
        if st & 1:
            tag, val, adr = struct.unpack_from("<3I", full, BB.O.STK1)
            print(f"FROZEN: state {st:#x}, tag {tag}, value {val}, address {adr:#x}")
            ring = full[BB.O.STK1 + 12:BB.O.STK1 + 12 + 16 + 8 * PS.NRING]
            idx = struct.unpack_from("<I", ring, 4)[0]
            for i in range(PS.NRING):
                t, a, b, c, p = struct.unpack_from("<I4B", ring, 16 + 8 * ((idx + i) % PS.NRING))
                print(f"  MIDI in {t} ms: {a:02X} {b} {c} (port flags {p:#x})")
        else:
            print(f"no record after {time.time() - t0:.0f} s, {n} messages")
    finally:
        out.close(); L.close()
    print("log:", log)


if __name__ == "__main__":
    a = sys.argv[1:]
    secs = float(a[0]) if a and not a[0].startswith("--") else 300
    rate = float(a[1]) if len(a) > 1 and not a[1].startswith("--") else 200
    seed = int(a[a.index("--seed") + 1]) if "--seed" in a else 1
    ch = [int(x) for x in a[a.index("--ch") + 1].split(",")] if "--ch" in a else list(range(1, 17))
    main(secs, rate, seed, ch)
