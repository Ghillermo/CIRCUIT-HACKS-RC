"""Live audit over USB (S564D4, blackbox.use_memrd): poll the corrupted word 0x20042988 (and the 32 bytes around it) and the 16 DMA streams while
the device runs; log every DMA stream whose memory address moves into 0x20042000..0x20043800, and the exact moment the word changes, with the DMA
state of that poll and the one before.  Writes Documents/livewatch_<time>.log.

    python tools/livewatch.py [seconds]
"""
from __future__ import annotations
import struct, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ctremote as CR
import bbread as BR

WORD, GOOD = 0x20042988, 0x0805ACC8
NEAR = (0x20042000, 0x20043800)
DMAS = ((0x40026010, "DMA1"), (0x40026410, "DMA2"))


def streams(link):
    out = []
    for base, nm in DMAS:
        d = BR.read(link, base, 192)
        for s in range(8):
            cr, ndtr, par, m0, m1, fcr = struct.unpack_from("<6I", d, 0x18 * s)
            out.append((f"{nm} S{s}", cr, ndtr, par, m0, m1))
    return out


def main(a):
    secs = float(a[0]) if a else 3600
    hz = float(a[1]) if len(a) > 1 else 5.0                                     # (each poll is a SysEx the device answers in its main loop: ~300 Hz slowed the clock)
    link = CR.Link()
    logp = Path.home() / "Documents" / f"livewatch_{time.strftime('%Y-%m-%d_%H%M%S')}.log"
    log = logp.open("w", encoding="utf-8")
    def say(s):
        line = f"{time.strftime('%H:%M:%S')} {s}"; print(line); log.write(line + "\n"); log.flush()
    say(f"watching {WORD:#x} (good {GOOD:#x}) and the DMA streams; log {logp}")
    t0 = time.time(); prev = None; n = 0; seen = set()
    try:
        while time.time() - t0 < secs:
            blk = BR.read(link, WORD - 8, 64)
            w = struct.unpack_from("<I", blk, 8)[0]
            st = []; n += 1                                                    # (the DMA registers only take word accesses: the USB read
                                                                                 #  is byte-wise and faults there; the firmware's dmawatch dumps them)
            if w != GOOD:
                say(f"*** the word changed: {w:#x}; 32 bytes {blk[:32].hex()}; the DMA dump: python tools/bbread.py --firmware S564D5")
                for row in (prev or []): say(f"   before: {row[0]} CR {row[1]:#x} NDTR {row[2]} PAR {row[3]:#x} M0 {row[4]:#x} M1 {row[5]:#x}")
                for row in st: say(f"   now:    {row[0]} CR {row[1]:#x} NDTR {row[2]} PAR {row[3]:#x} M0 {row[4]:#x} M1 {row[5]:#x}")
                break
            prev = st
            time.sleep(1.0 / hz)
            if n % 200 == 0: say(f"{n} polls, word ok")
    finally:
        link.close(); log.close()


if __name__ == "__main__":
    main(sys.argv[1:])
