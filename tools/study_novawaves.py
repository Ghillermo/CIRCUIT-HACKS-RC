"""Study (no build): where the stock synth (Nova engine) keeps its oscillator waves, from the stock DSP program run in emulation (dsp_session).

    python tools/study_novawaves.py [stock.bin] [--notes 36,60,84,108] [--waves 0-29]
For each Osc 1 wave (CC 19 on Synth 1's channel) and note, a note-on, N blocks, then the gather list core 0 leaves for core 1 in the shared memory
(X:$30000 = the list's end, X:$30002.. the addresses): the external X addresses asked for, grouped into tables (runs of 4096 words).  Only addresses:
no data of the device (core 1 and its memory are not emulated).  The result goes to stdout (and re/novawaves.json, kept out of git).
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dsp_session as DS  # noqa: E402

LIST, LIST_N = 0x30000, 0x400


def parse_range(s):
    out = []
    for part in s.split(","):
        a, _, b = part.partition("-"); out += list(range(int(a), int(b or a) + 1))
    return out


def main(argv):
    stock = Path(argv[0]) if argv and not argv[0].startswith("--") else Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin"
    notes = parse_range(argv[argv.index("--notes") + 1]) if "--notes" in argv else [60]
    waves = parse_range(argv[argv.index("--waves") + 1]) if "--waves" in argv else list(range(30))
    img = stock.read_bytes()
    res = {}
    s0 = DS.Session(img); out0, _ = s0.run(blocks=2, dumps=[('x', LIST, LIST_N)])
    w0 = out0[-1][2]; base = {a for a in w0[2:max(2, min(LIST_N, w0[0] - LIST))] if a}
    print(f"no note: {len(base)} addresses ({sorted({hex(a & ~0xFFF) for a in base})[:8]})", flush=True)
    for w in waves:
        for n in notes:
            gc.collect(); s = DS.Session(img)
            s.midi(bytes([0xB0, 19, w])); s.midi(bytes([0xB0, 20, 0])); s.midi(bytes([0x90, n, 100]))
            out, rans = s.run(blocks=2, dumps=[('x', LIST, LIST_N)])
            words = out[-1][2]
            end = words[0]
            addrs = [a for a in words[2:max(2, min(LIST_N, end - LIST))] if a and a not in base]
            bases = sorted({a & ~0xFFF for a in addrs})
            res[f"{w}/{n}"] = dict(end=hex(end), n=len(addrs), lo=hex(min(addrs)) if addrs else None, hi=hex(max(addrs)) if addrs else None,
                                  pages=[hex(b) for b in bases][:12],
                                  runs={hex(b): [hex(min(a for a in addrs if a & ~0xFFF == b)), hex(max(a for a in addrs if a & ~0xFFF == b)), sum(1 for a in addrs if a & ~0xFFF == b)] for b in bases})
            del s; gc.collect()
            print(f"wave {w:2d} note {n:3d}: {len(addrs):4d} reads, {res[f'{w}/{n}']['lo']}..{res[f'{w}/{n}']['hi']}, pages {res[f'{w}/{n}']['pages'][:6]}", flush=True)
    out = Path(__file__).resolve().parents[1] / "re" / "novawaves.json"
    out.parent.mkdir(exist_ok=True); out.write_text(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
