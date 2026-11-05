"""DX7 import test data: the card app's conversion (tools/sd_app.html) against fm8.from_dx7, and the firmware's load against both.

    python tools/dx7ref.py        -> build/sdapp_fixture/dx7.json (sd_app_test.html?dx7=1 reads it)

A bulk dump of 32 voices (voice 0 a plausible E.Piano, the rest 7-bit noise: every field past its range, so the masks and limits are tested) and a
single voice (VCED, noise too); for each, the name and the 216 parameters fm8.from_dx7 gives, and voice 0's FM record."""
from __future__ import annotations
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fm8 as F  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "sdapp_fixture" / "dx7.json"


def noise(n, seed):
    x, out = seed, bytearray()
    for _ in range(n):
        x = (x * 1103515245 + 12345) & 0x7FFFFFFF
        out.append(x >> 16 & 127)
    return out


def epiano():
    v = bytearray(128)
    for i, (r, l, ol, crs) in enumerate([((95, 29, 20, 50), (99, 95, 0, 0), 78, 1), ((95, 20, 20, 50), (99, 95, 0, 0), 99, 1),
                                         ((95, 29, 20, 50), (99, 95, 0, 0), 86, 1), ((95, 20, 20, 50), (99, 95, 0, 0), 99, 1),
                                         ((95, 50, 35, 78), (99, 75, 0, 0), 58, 14), ((96, 25, 25, 67), (99, 75, 0, 0), 99, 1)]):
        b = 17 * i                                                        # operator 6 first
        v[b:b + 8] = bytes(r + l)
        v[b + 8], v[b + 9], v[b + 10], v[b + 11] = 39, 0, 25, 0 | 3 << 2
        v[b + 12] = 3 | 7 << 3
        v[b + 13] = 0 | 2 << 2
        v[b + 14], v[b + 15], v[b + 16] = ol, 0 | crs << 1, 0
    v[102:110] = bytes((94, 67, 95, 60, 50, 50, 50, 50))
    v[110], v[111] = 4, 6 | 1 << 3
    v[112:118] = bytes((34, 33, 0, 0, 0 | 0 << 1 | 3 << 4, 24))
    v[118:128] = b"E.PIANO 1 "
    return bytes(v)


def bulk():
    data = epiano() + b"".join(bytes(noise(128, 7 + k)) for k in range(1, 32))
    data = bytearray(data)
    data[128 * 5 + 118:128 * 5 + 128] = b"Odd\x7fName\x01!"
    cs = -sum(data) & 127
    return b"\xF0\x43\x00\x09\x20\x00" + bytes(data) + bytes((cs, 0xF7))


def single():
    v = noise(155, 99)
    v[145:155] = b"SINGLE  V "
    return b"\xF0\x43\x00\x00\x01\x1B" + bytes(v) + bytes((-sum(v) & 127, 0xF7))


def expect(syx):
    return [{"name": n, "params": F.from_dx7(o, g).hex()} for n, o, g in F.dx7_voices(syx)]


def main():
    b, s = bulk(), single()
    vb = expect(b)
    assert len(vb) == 32 and vb[0]["name"] == "E.PIANO 1" and len(expect(s)) == 1
    assert F.dx7_voices(b[6:6 + 4096]) == F.dx7_voices(b)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"bulk": b.hex(), "single": s.hex(), "voices": vb, "one": expect(s)[0],
                               "record0": F.record(bytes.fromhex(vb[0]["params"])).hex()}))
    print("dx7:", OUT, len(vb), "voices +1")


if __name__ == "__main__":
    main()
