"""Does the stock keep bytes after the end of a session file?  (the user, 2026-11-13: extra automation lanes for the own synth stored after each
session's 160 780 bytes; «Can we try two? Do we need a diagnostic?»).  No firmware: the card in the PC.

    python tools/sesstail.py append CARD PACK PROJECT [--bytes N]   # adds N bytes (default 25 600 = 25 lanes x 2 values x 32 steps x 8 patterns x 2 tracks)
    python tools/sesstail.py check  CARD PACK PROJECT               # size, the tail still there, the stock part changed or not
    python tools/sesstail.py cut    CARD PACK PROJECT               # back to 160 780 bytes (the stock part kept as it is now)

CARD = the card's root (e.g. E:/), PACK = the pack number as on the card (the folder Tracks/NN_...), PROJECT = 1..64 as on the device.
Before appending, a copy of the session goes to build/sesstail/ (never on the card: the firmware finds files by their NN_ prefix).
The tail: "STL1", the project, the length, then a fixed pseudo-random pattern; check compares it byte by byte.

On the device, between append and check: load that project (does it load? the same as before?), change something, save it (the stock save),
load another project and come back, power off and on, load it once more.
"""
from __future__ import annotations
import hashlib
import shutil
import struct
import sys
from pathlib import Path

SIZE = 0x2740C
ROOT = Path(__file__).resolve().parents[1]


def find(card, pack, proj):
    tr = Path(card) / "Tracks"
    packs = [p for p in tr.iterdir() if p.is_dir() and p.name[:2] == f"{pack:02d}" and p.name[2:3] == "_"]
    assert len(packs) == 1, f"pack {pack:02d}_ not found once in {tr}"
    ses = [f for f in (packs[0] / "Sessions").iterdir() if f.suffix.lower() == ".ncs" and f.name[:3] == f"{proj - 1:02d}_"]
    have = sorted(int(f.name[:2]) + 1 for f in (packs[0] / "Sessions").iterdir() if f.suffix.lower() == ".ncs" and f.name[:2].isdigit())
    assert len(ses) == 1, f"project {proj} ({proj - 1:02d}_*.ncs) not found once in {packs[0] / 'Sessions'}; its projects: {have}"
    return ses[0]


def tail(proj, n):
    out = bytearray(b"STL1" + struct.pack("<HI", proj, n))
    x = 0x12345678 ^ proj
    while len(out) < n:
        x = (x * 1103515245 + 12345) & 0xFFFFFFFF
        out.append(x >> 16 & 0xFF)
    return bytes(out[:n])


def main(a):
    cmd, card, pack, proj = a[0], a[1], int(a[2]), int(a[3])
    n = int(a[a.index("--bytes") + 1]) if "--bytes" in a else 25600
    f = find(card, pack, proj)
    d = f.read_bytes()
    print(f"{f}: {len(d)} bytes")
    if cmd == "append":
        assert len(d) == SIZE, f"expected {SIZE} bytes: already appended? (check / cut)"
        bk = ROOT / "build/sesstail"; bk.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, bk / f"{pack:02d}_{f.name}")
        (bk / f"{pack:02d}_{f.name}.sha").write_text(hashlib.sha256(d).hexdigest())
        f.write_bytes(d + tail(proj, n))
        print(f"appended {n} bytes; copy in {bk}")
    elif cmd == "check":
        sha0 = (ROOT / f"build/sesstail/{pack:02d}_{f.name}.sha")
        if len(d) <= SIZE:
            print(f"the tail is GONE: the file is {len(d)} bytes")
        else:
            t = d[SIZE:]; want = tail(proj, len(t))
            print("the tail is " + ("THERE, byte for byte" if t == want else f"there but CHANGED ({sum(x != y for x, y in zip(t, want))} bytes differ)")
                  + f": {len(t)} bytes")
        if sha0.exists():
            print("the stock part " + ("is unchanged (not saved since the append?)" if hashlib.sha256(d[:SIZE]).hexdigest() == sha0.read_text() else "changed (saved by the device)"))
    elif cmd == "cut":
        f.write_bytes(d[:SIZE]); print(f"cut to {SIZE} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
