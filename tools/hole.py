"""SC44.8+: ARM code in the stock image's dead DSP programs (the flash after 0x70000 is full).

The stock image holds the DSP programs right after the vector table: core 0's at 0x080101F0 (10 846 words, 32 544 B) and core 1's at 0x08018110
(364 words, 1 098 B).  build_sc16 relocates core 0's program to the end of the image (with ours appended) and granular_dsp core 1's: the load table
(0x08029700) points at the copies, and nothing else reads the old blocks (the four stock literals that fall in the range are packed byte tables of
0x0805xxxx, not pointers; checked 2026-10-19).  Some early builders still patch words of the old core-0 block in place (0x08010376..0x08016783 in
SC44.7): dead too, but those patches run before extra(), so a module put here (from extra, last) is never overwritten; the builder checks it.

add(img, report, name, mod): mod.install(img, report, base) as for the end of the image (build_sc41_5.add), with base inside the hole; install
pads nothing (base < the end), appends its code (+ alignment) at the end: that tail moves into the hole and the image is cut back.  The hooks it
patched already point at base.  build_sc41_5.HOLE = the names its add() sends here.

**Only code that never writes to the card nor calls the settings save may live here:** rodisk's guard and lazysave tell the mod's calls by
LR >= 0x0805CDDC (MOD_START); from the hole they would pass as the stock's (the guard of pack 0 and the deferred save skipped).
"""
from __future__ import annotations

BASE = 0x08010000
LO, HI = 0x080101F0, 0x08018110 + 1098            # the two old DSP blocks, back to back
FILL = 0xFF


def add(img, report, name, mod):
    import build_shared_channels as sc
    h = report.setdefault("hole", {"next": hex(LO), "blocks": {}})
    at = (int(h["next"], 16) + 3) & ~3
    n0 = len(img)
    labels, code, prev = mod.install(img, report, at)
    blob = bytes(img[n0:])
    assert blob[:len(code)] == bytes(code), f"{name}: install did not append its code at the end"
    del img[n0:]
    end = at + len(blob)
    assert end <= HI, f"{name}: the hole is full ({end:#x} > {HI:#x})"
    img[at - BASE:end - BASE] = blob
    import hashlib
    h["next"] = hex(end); h["blocks"][name] = [hex(at), hex(end), hashlib.sha256(blob).hexdigest()]
    report[name] = dict(arm_start=hex(at), labels={k: hex(v) for k, v in labels.items()}, prev={k: hex(v) for k, v in prev.items()},
                        listing=sc.disasm(bytes(code), at), hole=True)


def check(img, report):
    """At the very end of a build: every block placed in the hole is still there (nothing patched the old DSP blocks after it)."""
    h = report.get("hole")
    if not h: return
    import hashlib
    for name, (a, b, sha) in h["blocks"].items():
        a, b = int(a, 16), int(b, 16)
        assert hashlib.sha256(bytes(img[a - BASE:b - BASE])).hexdigest() == sha, f"{name}: its code in the hole was overwritten"
