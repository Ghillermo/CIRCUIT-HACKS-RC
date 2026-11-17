"""S557D: is the DSP's external Y $337000-$33FFFF still untouched?  (more automation lanes for the own synth: ~1 600 words for the two playing
patterns; the ARM's RAM has no room).  The Circuit Tracks on USB with S557D installed, the MIDI ports free (close Components and the apps).

    python tools/dspsnap.py start [STATE]     snapshot A (rdiag dspx: 16 bits a word, bits 23..8)
    (use the device a while: play, the own synth with every engine (FM, granular, wavetable, sample), Sample Rec + the captured loop, the Glitch,
     pack and project changes, Save, a Components / SD app session ...)
    python tools/dspsnap.py end [STATE]       snapshot B; the blocks of 256 words that changed are listed

RANGES: the candidate, and a control block at the start of the Glitch's ring ($340000: it changes once the Glitch has played).
STATE defaults to build/dspsnap.json.
"""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ctremote as CR  # noqa: E402

RANGES = [("candidate", 0x337000, 0x340000), ("control: the Glitch ring", 0x340000, 0x341000)]
BLK = 256


def snap(L):
    out = {}
    for name, lo, hi in RANGES:
        words, a, t0 = [], lo, time.time()
        while a < hi:
            k = min(CR.NX, hi - a)
            d = CR.dec_dspx(L.ask(lambda s, a=a, k=k: CR.req_dspx(s, a, k), 8))
            if d["status"]: raise SystemExit(f"dspx status {d['status']} at {a:#x}")
            words += d["samples"]; a += k
        out[name] = words
        print(f"{name}: {hi - lo} words in {time.time() - t0:.0f} s; {sum(1 for w in words if w)} non-zero")
    return out


def main(a):
    cmd = a[0]
    st = Path(a[1]) if len(a) > 1 else Path(__file__).resolve().parents[1] / "build/dspsnap.json"
    L = CR.Link()
    s = snap(L)
    if cmd == "start":
        st.parent.mkdir(parents=True, exist_ok=True); st.write_text(json.dumps(s))
        print(f"snapshot A in {st}: use the device, then `dspsnap.py end`")
        return 0
    A = json.loads(st.read_text())
    for name, lo, hi in RANGES:
        wa, wb = A[name], s[name]
        ch = [lo + i for i in range(0, hi - lo, BLK) if wa[i:i + BLK] != wb[i:i + BLK]]
        nw = sum(1 for x, y in zip(wa, wb) if x != y)
        print(f"{name} ${lo:06X}-${hi - 1:06X}: {nw} words changed in {len(ch)} of {(hi - lo) // BLK} blocks"
              + (": " + ", ".join(f"${c:06X}" for c in ch[:24]) + (" ..." if len(ch) > 24 else "") if ch else " (untouched)"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
