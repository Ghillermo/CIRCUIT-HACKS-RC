"""Probe (2026-11-03): does Synth 1's level follow the velocity in the DSP?  A note at velocity 20 and at 120 on an image, through the real ARM
(dsp_session: its writes replayed on the core-0 emulator), the final mix X:$2C02 / $2C24 measured over the last blocks; optionally CC 108 (the
amp envelope's velocity in Novation's reference) set first.

    python tools/probe_synthvel_dsp.py IMAGE.bin [IMAGE2.bin ...]
"""
from __future__ import annotations
import gc, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dsp_session import Session  # noqa: E402

OUT = [(0x2C02, 64), (0x2C24, 64)]


def level(img, vel, cc=None, k1=None):
    s = Session(img)
    if k1 is not None:                                                # velglob: amp velocity 0 in the patch, K1 in the cache
        import struct, velglob as VG
        s.e.uc.mem_write(0x20010044 + 69, bytes([64])); s.e.uc.mem_write(VG.RAM, struct.pack('<I', VG.RSIG) + bytes([k1, 0, 0, 0]))
    p = bytes(s.e.uc.mem_read(0x20010044, 340)) if hasattr(s, "e") else b""
    s.midi(bytes([0xB0, 56, 127]))                                   # as emu_sc17_5_dsp: the synth's level up
    if cc is not None: s.midi(bytes([0xB0, 108, cc]))
    s.midi(bytes([0x90, 60, vel]))
    ex = [('x', 0x52, 0x7F0000), ('x', 0x53, 0x400000), ('x', 0xE3, 0x500000), ('x', 0xE7, 0x500000), ('x', 0xE5, 0x300000)]
    res, _ = s.run(blocks=24, per_block=True, extra=ex, dumps=[('x', a, n) for a, n in OUT])
    del s; gc.collect()
    vals = [v for _, _, blk in res[-16:] for v in blk]
    sv = [(v - (1 << 24) if v & 0x800000 else v) / (1 << 23) for v in vals]
    rms = math.sqrt(sum(x * x for x in sv) / max(1, len(sv)))
    return rms, p


K1 = "--k1" in sys.argv
for path in [x for x in sys.argv[1:] if not x.startswith("--")]:
    img = Path(path).read_bytes()
    if K1:
        for k1 in (0, 127):
            r20, _ = level(img, 20, k1=k1); r120, _ = level(img, 120, k1=k1)
            print(f"{Path(path).name}  amp velocity 0, K1={k1}: v20 {r20:.6f} v120 {r120:.6f} -> {20 * math.log10(r120 / r20):+.1f} dB", flush=True)
        continue
    for cc in (None, 127):
        r20, p = level(img, 20, cc); r120, _ = level(img, 120, cc)
        db = 20 * math.log10(r120 / r20) if r20 and r120 else float("nan")
        name = p[:16].decode("latin1", "replace").strip() if p else "?"
        info = f"patch {name!r}, amp-env velocity byte {p[69] - 64 if p else '?'}" if p else ""
        print(f"{Path(path).name}  CC108={cc}: rms v20 {r20:.5f}  v120 {r120:.5f}  -> {db:+.1f} dB   {info}", flush=True)
