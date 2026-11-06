"""The views of docs/VOCES.md as the firmware draws them: runs a build in emulation through each view of MIDI 1 and keeps the 69 LEDs of each, as RGB from the LED table (bytes B, G, R),
in docs/voces_panels.json, so the drawings of tools/make_voces.py cannot disagree with the device.

    python tools/capture_voces.py BUILD.bin MANIFEST.json
"""
from __future__ import annotations
import json, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402  (its import sets vcf21's options)
import emu_lazysave as T  # noqa: E402

V = T4.V
ROOT = Path(__file__).resolve().parents[1]
MGR = X.MGR
NOTE, VEL, GATE, PS = 9, 10, 11, 12


def main(img, man):
    e = X.EP(img, man)
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05]))
    tick = lambda n=1: [(e.at(e.t + 40), e.call(e.vl["c_vtick"], maxins=3_000_000)) for _ in range(n)]
    tick(10)
    pal = bytes(e.uc.mem_read(0x20003804, 4 * 256))
    rgb = lambda c: "#%02x%02x%02x" % (pal[4 * c + 2], pal[4 * c + 1], pal[4 * c])
    out = {}
    def snap(name, frames=3):
        for _ in range(frames - 1): X.frame(e)
        fr = X.frame(e)
        out[name] = dict(codes=[v & 0xFF for v in fr], bright=[v >> 8 for v in fr], rgb=[rgb(v & 0xFF) for v in fr])
        print(name, " ".join("%02x" % (v & 0xFF) for v in fr[:32]), flush=True)
    hold = lambda q: e.call(T.PRESS, MGR, q, 100, maxins=8_000_000)
    let = lambda q: e.call(T.RELEASE, MGR, q, maxins=8_000_000)
    pat = lambda: (e.call(int(man["report"]["vcf20"]["labels"]["c_sdpat"], 16), 0), e.uc.reg_read(UC_ARM_REG_R0))[1]
    base = pat()
    for st in (0, 4, 8, 12): e.uc.mem_write(base + 28 * st, bytes([1, 7, 0, 0, 60 + st, 6, 0, 100]))
    e.btn(2); e.btn(8); e.at(e.t + 3000); snap("preset")
    e.pad(26); snap("motores"); e.pad(26); X.frame(e)
    e.pad(31); snap("voz"); e.pad(31); X.frame(e)
    e.pad(29); snap("step"); e.pad(29); X.frame(e)
    e.btn(2); e.btn(8); X.frame(e)
    e.pad(26); X.frame(e); e.pad(23); X.frame(e); e.pad(26); X.frame(e); e.at(e.t + 2000)
    fm8 = "fm8" in man["report"]                                               # (Beta 5.20 on: the 8-operator FM; the 4-operator drawings keep their old capture)
    if fm8: e.pad(6); X.frame(e)                                              # pad 7: the FM page
    snap("fm8" if fm8 else "fm")
    hold(7); snap("inst8" if fm8 else "partida", 1); let(7); X.frame(e)
    hold(6); snap("algos8" if fm8 else "algos", 1); let(6); X.frame(e)
    if "wtui" in man["report"]:                                               # the wavetable (Beta 5.24 on): pad 21 of the row, then its two lists
        e.btn(2); e.btn(8); X.frame(e); e.pad(26); X.frame(e); e.pad(20); X.frame(e); e.pad(26); X.frame(e); e.at(e.t + 2000)
        snap("wt")
        hold(6); snap("wtnova", 1); let(6); X.frame(e)
        hold(7); snap("wtsmp", 1); let(7); X.frame(e)
    e.pad(26); X.frame(e); e.pad(21); X.frame(e); e.pad(26); X.frame(e)
    e.btn(NOTE); e.btn(NOTE); e.at(e.t + 2000); snap("muestra")
    e.btn(2); e.btn(8); X.frame(e); e.pad(26); X.frame(e); e.pad(18); X.frame(e); e.pad(12); X.frame(e)
    while e.t & 0x100: e.at(e.t + 100); X.frame(e)                                  # pad 27 blinks: the bright half (the row closes after 300 ms without a frame)
    snap("saltos"); e.pad(26); X.frame(e)
    e.btn(NOTE); X.frame(e); snap("saltosnote")
    e.btn(2); e.btn(8); X.frame(e); e.pad(26); X.frame(e); e.pad(12); X.frame(e); e.pad(26); X.frame(e)
    e.btn(PS); snap("ps"); e.shift(True); snap("arp"); e.shift(False)
    e.pad(24); X.frame(e); e.pad(0); X.frame(e); e.pad(16 + 5); e.pad(24); e.pad(31); snap("mutate")
    e.btn(2); e.btn(GATE); e.btn(GATE); snap("micro")
    f = ROOT / "docs/voces_panels.json"
    old = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    f.write_text(json.dumps({**old, **out}), encoding="utf-8")              # the panels this build does not draw (the 4-operator FM) stay


if __name__ == "__main__":
    a = sys.argv[1:]
    main(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text()))
