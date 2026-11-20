"""Which incoming CCs / NRPNs leave a pending parameter flag whose sender would jump to a bad address (the CC 27 bug, cc27fix)?  Through the real
MIDI input (0x08051720): every CC 0-127 on channels 1-16 (values 0 / 64 / 127) and every NRPN (MSB 0-127, LSB 0-127, value 127) on the given
channels; after each, the pending bytes at 0x20006A0C (drums type 0x10: byte 0 bits 0-3; master 0x21: byte 1 bits 0-3; project 0x20: halfword 2,
bits 0-9) are read, the flags whose table entry is not code are reported, and the three senders run (a fault = reported).

    python tools/emu_midifuzz.py IMAGE.bin [--nrpn 1,2,10,16]
"""
from __future__ import annotations
import struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc05 as X  # noqa: E402

PEND = 0x20006A0C
SENDERS = (0x080214F4, 0x08021544, 0x08021578)


def main(img, nrpn_ch):
    e = X.E(img)
    B = 0x08010000
    w = lambda a: struct.unpack_from("<I", img, a - B)[0]
    good = lambda v: (v & 1) and 0x08010000 <= v < B + len(img)
    t10 = [w(0x08021534 + 4 * k) for k in range(4)]
    t20 = [w(w(((0x08021562 + 4) & ~3) + 0xB64) + 4 * k) for k in range(10)]
    t21 = [w(0x080215B8 + 4 * k) for k in range(4)]
    bad = {(0, b) for b in range(4) if not good(t10[b])} | {(1, b) for b in range(4) if not good(t21[b])} | {(2, b) for b in range(10) if not good(t20[b])}
    print("flags with a bad table entry:", sorted(bad), "(0 = drums, 1 = master, 2 = project)")
    m = 0x20060100
    hits, faults = {}, {}
    snap = bytes(e.uc.mem_read(0x20000000, 0x50000))

    def send(bs):
        for b3 in bs:
            e.uc.mem_write(m, bytes(b3) + b"\0"); e.call(0x08051720, X.CTX, m, maxins=400000)

    def check(label):
        p = bytes(e.uc.mem_read(PEND, 4))
        fl = {(0, b) for b in range(4) if p[0] >> b & 1} | {(1, b) for b in range(4) if p[1] >> b & 1} | {(2, b) for b in range(10) if struct.unpack_from("<H", p, 2)[0] >> b & 1}
        for f in fl & bad: hits.setdefault(f, []).append(label)
        for s in SENDERS:
            try: e.call(s, maxins=300000)
            except Exception as ex: faults.setdefault(hex(s), []).append(label)
        e.uc.mem_write(PEND, bytes(4))

    for ch in range(16):
        for cc in range(128):
            for v in (0, 64, 127):
                try: send([(0xB0 | ch, cc, v)])
                except Exception: faults.setdefault("input", []).append(f"ch{ch + 1} CC{cc}={v}"); e.uc.mem_write(0x20000000, snap); continue
                check(f"ch{ch + 1} CC{cc}={v}")
        print(f"ch{ch + 1} CCs done", flush=True)
    for ch in nrpn_ch:
        for msb in range(128):
            for lsb in range(128):
                try: send([(0xB0 | (ch - 1), 99, msb), (0xB0 | (ch - 1), 98, lsb), (0xB0 | (ch - 1), 6, 127)])
                except Exception: faults.setdefault("input", []).append(f"ch{ch} NRPN {msb}:{lsb}"); e.uc.mem_write(0x20000000, snap); continue
                check(f"ch{ch} NRPN {msb}:{lsb}")
            if msb % 32 == 31: print(f"ch{ch} NRPN MSB {msb} done", flush=True)
    print("bad flags reached:", {f"{k}": (len(v), v[:12]) for k, v in hits.items()})
    print("faults:", {k: (len(v), v[:12]) for k, v in faults.items()})


if __name__ == "__main__":
    a = sys.argv[1:]
    ch = [int(x) for x in a[a.index("--nrpn") + 1].split(",")] if "--nrpn" in a else [1, 2, 10, 16]
    main(Path(a[0]).read_bytes(), ch)
