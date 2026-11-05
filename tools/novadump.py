"""S516D: copies of the Nova oscillator waves from the device to the PC (the Circuit Tracks on USB with S516D installed, the MIDI ports free).

    python tools/novadump.py [NAME=0xSTART:0xWORDS ...]      (default: the areas tools/study_novawaves.py found)
For each area: X:$3FE8.. = seq, source (core 1's external X), words (dspw), wait until X:$3FEC = seq (core 1 has copied it to external Y at
granular_dsp.ND_Y, 256 words a pass), then dspx reads it (16 bits a word).  Up to 32 K words an area (cut into pieces).  Saved to re/novadump/NAME.bin
(little-endian int16; re/ is not in git: these are the device's data, never published).
"""
from __future__ import annotations
import struct, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ctremote as CR  # noqa: E402
import granular_dsp as GD  # noqa: E402

AREAS = dict(w2_saw=(0x173000, 0x2000), w0=(0x102000, 0x4000), w1=(0x14A000, 0x2000), w13=(0x19B000, 0x2000), w15=(0x1E0000, 0x6000),
             w20=(0x2AB000, 0x5000), z_head=(0x100000, 0x1000))
PIECE = 0x2000


def main(argv):
    areas = dict(AREAS)
    if argv:
        areas = {}
        for a in argv:
            n, _, r = a.partition("="); s, _, w = r.partition(":"); areas[n] = (int(s, 0), int(w, 0))
    L = CR.Link()
    mark = bytes(CR.dec_mem(L.ask(lambda s: CR.req_mem(s, 0x080101E8, 6), 2))["data"]).rstrip(b"\0")
    nd_x = GD.ND_X2 if mark == b"S516D2" else GD.ND_X                     # S516D's X:$3FE8 is core 1's late count too: use S516D2
    print(f"{mark.decode(errors='replace')}: commands at X:${nd_x:04X}", flush=True)
    out =Path(__file__).resolve().parents[1] / "re" / "novadump"; out.mkdir(parents=True, exist_ok=True)
    seq = int(time.time()) & 0x7FFF
    def w(addr, v): CR.dec_write(L.ask(lambda s: CR.req_dspw(s, addr, v), 9))
    def r(addr): return CR.dec_dspr(L.ask(lambda s: CR.req_dspr(s, 0, addr, 1), 3))["words"][0]
    try:
        for name, (src, n) in areas.items():
            data = []
            for p in range(0, n, PIECE):
                k = min(PIECE, n - p); seq += 1
                w(nd_x + 1, src + p); w(nd_x + 2, k); w(nd_x, seq)
                t0 = time.time()
                while r(nd_x + 4) != seq:
                    if time.time() - t0 > 10: raise SystemExit(f"{name}: core 1 did not copy (seq {seq})")
                    time.sleep(0.05)
                got = []
                while len(got) < k:
                    d = CR.dec_dspx(L.ask(lambda s, a=GD.ND_Y + len(got), m=min(CR.NX, k - len(got)): CR.req_dspx(s, a, m), 8))
                    if d["status"]: raise SystemExit(f"dspx status {d['status']}")
                    got += d["samples"]
                data += got
            (out / f"{name}.bin").write_bytes(struct.pack("<%dh" % len(data), *[(v ^ 0x8000) - 0x8000 for v in data]))
            nz = sum(1 for v in data if v)
            print(f"{name}: X:${src:06X} + {n:#x} -> {out / (name + '.bin')} ({nz} words not zero)", flush=True)
    finally:
        L.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
