"""S513D: the sweep of the dummy FM voices on DSP core 1, from the PC (the Circuit Tracks on USB with S513D installed, the MIDI ports free).

    python tools/fmload_sweep.py [N ...] [--samples S] [--secs T]
For each N (default 0 2 4 6 8 10 12 14 16 20 24): LN = N dummy voices a block in chunks of S samples (default 4: 8 tasks a voice, ~810 instructions
each), T seconds (default 4), then: core 1's late blocks since N was set and its fewest idle passes a block (X:$3FEC / $3FEE, granular_dsp.use_fmload),
core 0's least margin of the last window and the dry rings (dspload: RAM + 20 / + 36; under 192 = a block took longer than a period).  Stops after the
first N with late blocks or a margin under 192; LN = 0 at the end (and on Ctrl+C)."""
from __future__ import annotations
import struct, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ctremote as CR  # noqa: E402
import dspload as DL  # noqa: E402

LX = 0x3FE8


def main(argv):
    S = int(argv[argv.index("--samples") + 1]) if "--samples" in argv else 4
    T = float(argv[argv.index("--secs") + 1]) if "--secs" in argv else 4.0
    ns = [int(a) for i, a in enumerate(argv) if a.isdigit() and (i == 0 or argv[i - 1] not in ("--samples", "--secs"))] or [0, 2, 4, 6, 8, 10, 12, 14, 16, 20, 24]
    assert 1 <= S <= 32 and 32 % S == 0
    L = CR.Link()
    def w(addr, v): CR.dec_write(L.ask(lambda s: CR.req_dspw(s, addr, v), 9))
    def r(addr, n): return CR.dec_dspr(L.ask(lambda s: CR.req_dspr(s, 0, addr, n), 3))["words"]
    def ram(addr, n): return CR.dec_mem(L.ask(lambda s: CR.req_mem(s, addr, n), 2))["data"]
    try:
        w(LX, 0); w(LX + 1, 32 // S); w(LX + 2, S); w(LX + 3, 4)
        time.sleep(0.5)
        nz = r(LX + 7, 1)[0]
        print(f"X:$2B00..$2BFF of core 1 at boot: {'empty (0)' if nz == 0 else f'NOT EMPTY ({nz:06x}): something else uses it'}")
        print(f"{'N':>3} {'late':>5} {'idle min':>8} {'core0 margin':>12} {'dry':>4}")
        for n in ns:
            dry0 = struct.unpack("<I", ram(DL.RAM + DL.O_NDRY, 4))[0]
            w(LX, n)
            t0, mins = time.time(), []
            while time.time() - t0 < T:
                time.sleep(0.6)
                mins.append(struct.unpack("<i", ram(DL.RAM + DL.O_SMIN, 4))[0])
            late, idl, idmin, _ = r(LX + 4, 4)
            dry = struct.unpack("<I", ram(DL.RAM + DL.O_NDRY, 4))[0] - dry0
            m = min(mins)
            print(f"{n:>3} {late:>5} {idmin:>8} {m:>12} {dry:>4}", flush=True)
            if "--nostop" not in argv and (late or m < 192 or dry): print("stop: core 1 late" if late else "stop: core 0 out of time" if m < 192 else "stop: the ring ran dry"); break
    finally:
        w(LX, 0); L.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
