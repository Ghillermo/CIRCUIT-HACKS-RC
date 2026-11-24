"""(2026-11-24) noinapp: the running firmware's update header handler (0x08039088) does nothing.
    python tools/emu_noinapp.py firmware/a7.43 [firmware/a7.42]
A header message (byte 5 = 0x7C, 0x1E bytes) goes to the handler with r1 = 1 (as from 0x08038D24) and r1 = 0 (as from 0x0803900A).
Stock / the parent: the handler decodes the header (0x080390A6), takes a partition (0x080390D4) and goes on to erase / start
(0x08038D2A / 0x08038EBA). Ours: returns at once, nothing reached, the update state word unchanged."""
import gc, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE, UcError
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc05

H = 0x08039088
MARKS = {0x080390A6: "decode", 0x080390D4: "partition", 0x08038D2A: "erase/start", 0x08038EBA: "start"}
STATE = 0x20000A6C                                     # [pc literal] = the updater object (its +0x1C = the chosen partition)


def run(img, r1):
    e = emu_sc05.E(img)
    seen = []
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: seen.append(MARKS[a]) if a in MARKS else None)
    msg = bytes([0xF0, 0x00, 0x20, 0x29, 0x00, 0x7C]) + bytes(23) + bytes([0xF7])
    assert len(msg) == 0x1E
    e.uc.mem_write(0x20060000, msg)
    e.uc.mem_write(0x20060100, struct.pack("<II", 0x20060000, len(msg)))
    before = bytes(e.uc.mem_read(STATE, 0x40))
    try: e.call(H, 0x20060100, r1, maxins=400_000)
    except UcError as x: seen.append(f"stopped ({x})")
    after = bytes(e.uc.mem_read(STATE, 0x40))
    del e; gc.collect()
    return seen, before != after


def main(new, old=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  :" if c else "FAIL:"), m); fails += not c
    img = next(Path(new).glob("*.bin")).read_bytes()
    assert img[H - 0x08010000:H - 0x08010000 + 2] == bytes([0x70, 0x47]), "not a noinapp build"
    for r1 in (1, 0):
        seen, changed = run(img, r1)
        check(not seen and not changed, f"ours, r1 = {r1}: nothing reached ({seen}), updater state unchanged ({not changed})")
    if old:
        oimg = next(Path(old).glob("*.bin")).read_bytes()
        for r1 in (1, 0):
            seen, changed = run(oimg, r1)
            check("decode" in seen and "partition" in seen, f"parent, r1 = {r1}: the stock handler runs ({seen}, state changed {changed})")
    print("NOINAPP RESULT:", "ALL PASS" if not fails else f"{fails} FAIL")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(*sys.argv[1:]) else 0)
