"""SC54: build_sc17.use_gentab / tools/mfxgen.py.  c_gtgen run in emulation writes Master FX's generated knob tables into RAM byte for byte as
build_sc17.tables() gives them; a second call with the stamp in place writes nothing; a wrong stamp writes them again.

    python tools/emu_gentab_mfx.py BUILD.bin manifest.json
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
import build_sc17 as S  # noqa: E402
import mfxgen as G  # noqa: E402


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    R = man["report"]["sc17"]
    gen = int(R["labels"]["c_gtgen"], 16)
    S.LFOSYNC = "LDIV" in R["tables"]                                                # (the build's option: LDIV)
    tabs = S.tables()
    ram = {k: int(v, 16) for k, v in R["tables"].items() if int(v, 16) >= 0x20000000}
    e = T.EL(img)
    check(set(ram) == set(n for n in G.GEN if n in tabs), f"the generated tables in RAM: {sorted(ram)}")
    for a in ram.values(): e.uc.mem_write(a, b"\xAA" * 512)
    e.call(gen, maxins=5_000_000)
    bad = [n for n, a in ram.items() if bytes(e.uc.mem_read(a, 512)) != struct.pack("<128I", *[v & 0xFFFFFFFF for v in tabs[n]])]
    check(not bad, f"c_gtgen: the tables byte for byte ({bad})")
    a0 = next(iter(ram.values())); e.uc.mem_write(a0, b"\x55" * 4)
    e.call(gen, maxins=5_000_000)
    check(bytes(e.uc.mem_read(a0, 4)) == b"\x55" * 4, "the stamp in place: nothing written again")
    _, stamp, _, crc = G.plan(tabs)
    e.w32(stamp, crc ^ 2); e.call(gen, maxins=5_000_000)
    check(bytes(e.uc.mem_read(a0, 512)) == struct.pack("<128I", *[v & 0xFFFFFFFF for v in tabs[next(iter(ram))]]) and e.r32(stamp) == crc,
          "another stamp: written again")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} GENTAB-MFX RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    img = Path(sys.argv[1]).read_bytes()
    man = json.loads(Path(sys.argv[2]).read_text())
    sys.exit(1 if main(img, man) else 0)
