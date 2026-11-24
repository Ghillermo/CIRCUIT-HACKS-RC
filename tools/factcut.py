"""Alpha 7.38 (the user, 2026-11-23: «yes» to «a no-feature build that ignores the factory-test messages and frees the 3.5 KB»): the stock's
factory-test mode removed, and the flash of its two DSP programs given to our code (the flash was full: 44 B free in Alpha 7.37).

The stock's factory test = the SysEx messages F0 00 20 29 01 63 ... (the 5-byte header F0 00 20 29 01, then byte 5 = 0x63; Components and the
file protocol use F0 00 20 29 01 64).  Three places test that byte:
  (a) 0x0802484C (the first handler of 0x0801EB30, ports 0 / 1): 0x63, 9 bytes or more, byte 6 = 0x70 -> 0x0801F284: byte 7 = 0x60 sets / clears
      the test bits 0, 2, 4 of the flags word 0x20000A6C and the port's bit of 0x20006A4D; 0x5E -> 0x080269E4; then, with bit 4 set, the six
      command handlers 0x080267F8, 0x08023E22, 0x08026B68, 0x08026BDC, 0x08026918, 0x08026C78.  0x08026918's commands 0x5C / 0x5D / 0x71 ask
      0x0801F51E(obj, &1) for the «mode 1» DSP programs: 0x08029260(1) sends the blocks of the load table's slots 1 and 3 (0x08029700:
      [core 0 mode 0, core 0 mode 1, core 1 mode 0, core 1 mode 1]) = 0x08054EFC (808 words) and 0x0805587C (360 words);
  (b) 0x08038B70 (for 0x08038BA0, called by 0x0802484C for every message): 0x63, 9 bytes or more, byte 6 = 0x71 -> byte 7 = 0 / 1 / 2;
  (c) 0x0803A614 with r1 = 0 (for 0x0802527C, the first object 0x0801EB30 calls): 0x63 and a closing F7 -> byte 6 = 0x70: byte 7 = 0x60 sets /
      clears test bit 4, 0x6C (23 bytes, bit 4 set) writes the 14-character serial number.
Nothing else reads the two mode-1 blocks; the power-up send is mode 0 (0x0801D582 -> 0x0801F51E -> 0x0801F554 -> 0x08029260(0)).

Here (PATCHES, each checked against the stock's bytes):
  * the three `bne` after `cmp rX, #0x63` (0x08024870, 0x08038B8A, 0x0803A642) are `b`: byte 5 = 0x63 never matches, so no factory-test message
    is handled, the test bits are never set and nothing asks for mode 1;
  * 0x08029262 `mov r4, r0` -> `movs r4, #0`: the DSP program send is mode 0 for any argument (the freed blocks can never be sent to the DSP);
  * the load table's slots 1 / 3 = its slots 0 / 2 (no pointer into the freed range is left).
The two blocks are 0x08054EFC-0x08055CBA (3 518 B).  Right below them is the stock's table of the 310 synth parameters (0x0805454C + 8 row; our
modules call it 0x0805454A), whose accessors (0x0803BBBE, 0x0803BBDC, 0x0803BF96) do not bound the row: rows 310 / 311 would be the blocks' first
16 bytes, so **those 16 bytes stay as they are** (KEEP) and the rest, 0x08054F0C-0x08055CBA (3 502 B), is filled with 0xFF and offered as a new
gap of dspz.add (GAP_OF), as msdcut's: below MOD_START (0x0805CDDC), where rodisk's guard and lazysave see the caller as the stock's, so **only
modules that never call the card's write / delete nor the settings save themselves** may go there.  thumb.OUT_ZONES gets the range, so a module
assembled there is outlined like the rest (outline.py).  Above the range: two unused bytes, then the stock's NRPN map (0x08055CBC).

0x63 is also the Circuit Rhythm's product byte: with this cut a Tracks no longer reacts to a Rhythm's traffic on the same MIDI line (on the stock,
F0 00 20 29 01 63 70 60 01 F7 from anywhere puts the Tracks in test mode until it is switched off).

A side effect wanted for later: with no factory-test mode the DSP programs are sent once, at power-up, so dspz's unpacking window and
probabilities (ITCM 0x2000-0x3FFF) stay untouched afterwards."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

R0, KEEP, HI = 0x08054EFC, 16, 0x08055CBA                # the two mode-1 blocks; their first bytes left as they are (the parameter table's rows 310 / 311)
LO = R0 + KEEP                                          # the gap: 0x08054F0C-0x08055CBA
TABLE = 0x08029700
PATCHES = [                                             # (address, the stock's bytes, ours)
    (0x08024870, bytes.fromhex("08d1"), bytes.fromhex("08e0")),               # (a) bne 0x08024884 -> b
    (0x08038B8A, bytes.fromhex("07d1"), bytes.fromhex("07e0")),               # (b) bne 0x08038B9C -> b
    (0x0803A642, bytes.fromhex("01d1"), bytes.fromhex("01e0")),               # (c) bne 0x0803A648 -> b
    (0x08029262, bytes.fromhex("0446"), bytes.fromhex("0024")),               # mov r4, r0 -> movs r4, #0
]
CMP63 = (0x0802486E, 0x08038B88, 0x0803A640)             # the three `cmp rX, #0x63` in front of those branches
BLOCKS = ((0x08054EFC, 808), (0x0805587C, 360))         # the two mode-1 blocks: (address, words)
DONE = {}


def install(img, report):
    """Once per build, after dspz.install (the builder calls it before the first module it sends to the gap); returns the gap's index."""
    import ct_fw
    import thumb
    if DONE.get("gap") is not None: return DONE["gap"]
    BASE = ct_fw.APP_BASE
    stock = (Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    u32 = lambda d, a: struct.unpack_from("<I", d, a - BASE)[0]
    for c in CMP63:                                       # cmp r0 / r1, #0x63 (plain or inside an IT block), still the stock's
        assert stock[c - BASE] == 0x63 and stock[c - BASE + 1] in (0x28, 0x29) and bytes(img[c - BASE:c - BASE + 2]) == bytes(stock[c - BASE:c - BASE + 2]), f"{c:#x}"
    for a, old, new in PATCHES:
        o = a - BASE
        assert len(old) == len(new) and bytes(stock[o:o + len(old)]) == old, f"{a:#x}: the stock has {bytes(stock[o:o + len(old)]).hex()}"
        assert bytes(img[o:o + len(old)]) == old, f"{a:#x}: already patched ({bytes(img[o:o + len(old)]).hex()})"
        img[o:o + len(new)] = new
    assert (u32(stock, TABLE + 4), u32(stock, TABLE + 12)) == (BLOCKS[0][0], BLOCKS[1][0]) == (u32(img, TABLE + 4), u32(img, TABLE + 12)), "the load table's mode-1 slots"
    for at, words in BLOCKS:                              # the blocks are what the table says they are, and still the stock's
        o = at - BASE
        assert int.from_bytes(stock[o:o + 3], "big") == words, f"{at:#x}: {int.from_bytes(stock[o:o + 3], 'big')} words"
    assert BLOCKS[0][0] == R0 and BLOCKS[0][0] + 6 + 3 * BLOCKS[0][1] + 2 == BLOCKS[1][0] and BLOCKS[1][0] + 6 + 3 * BLOCKS[1][1] == HI and LO % 4 == 0
    assert bytes(img[R0 - BASE:HI - BASE + 2]) == bytes(stock[R0 - BASE:HI - BASE + 2]), "the mode-1 blocks are not the stock's"
    struct.pack_into("<I", img, TABLE + 4 - BASE, u32(img, TABLE))            # slots 1 / 3 = slots 0 / 2 (dspz's packed mode-0 blocks)
    struct.pack_into("<I", img, TABLE + 12 - BASE, u32(img, TABLE + 8))
    img[LO - BASE:HI - BASE] = bytes([0xFF]) * (HI - LO)
    gaps = report["dspz"]["gaps"]
    gaps.append([hex(LO), hex(HI)])
    DONE["gap"] = len(gaps) - 1
    if (LO, HI) not in thumb.OUT_ZONES: thumb.OUT_ZONES.append((LO, HI))
    report["factcut"] = dict(gap=[hex(LO), hex(HI)], index=DONE["gap"], bytes=HI - LO, kept=[hex(R0), hex(LO)], patches=[hex(a) for a, _, _ in PATCHES],
                             table=[hex(u32(img, TABLE + 4 * k)) for k in range(4)])
    return DONE["gap"]


def check(img, report):
    """For tests and the end of a build: the cut is in place and the freed range holds only what dspz.add put there."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u32 = lambda a: struct.unpack_from("<I", img, a - BASE)[0]
    out = []
    if "factcut" not in report: return ["a build without factcut"]
    for a, old, new in PATCHES:
        if bytes(img[a - BASE:a - BASE + len(new)]) != new: out.append(f"{a:#x}: {bytes(img[a - BASE:a - BASE + len(new)]).hex()} is not {new.hex()}")
    if (u32(TABLE + 4), u32(TABLE + 12)) != (u32(TABLE), u32(TABLE + 8)): out.append("the load table's mode-1 slots are not its mode-0 slots")
    d = report["dspz"]; k = report["factcut"]["index"]
    used = int(d.get(f"next{k}", hex(LO)), 16)
    if not LO <= used <= HI: out.append(f"the gap's next address {used:#x}")
    if any(b != 0xFF for b in img[used - BASE:HI - BASE]): out.append("the unused part of the freed range is not 0xFF")
    stock = (Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    if bytes(img[R0 - BASE:LO - BASE]) != bytes(stock[R0 - BASE:LO - BASE]) or bytes(img[HI - BASE:HI - BASE + 2]) != bytes(stock[HI - BASE:HI - BASE + 2]):
        out.append("the bytes kept at the range's start (16) or after its end (2) are not the stock's")
    blocks = [(n, int(a, 16), int(b, 16)) for n, (a, b) in d.get("blocks", {}).items() if LO <= int(a, 16) < HI]
    if sum(b - a for _, a, b in blocks) > used - LO or any(b > HI for _, a, b in blocks): out.append(f"the blocks placed in the freed range: {blocks}")
    return out
