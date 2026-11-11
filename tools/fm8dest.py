"""SC55.7 / Beta 5.42 (the user, 2026-11-10: «Build example patches based on traditional and popular synth patches. assign pertinent macro
destinations to new and existing patches»; chosen: the own synth of MIDI 1 / 2, the example patches as card files (tools/make_examples.py), the
FM instruments' destinations in the firmware): loading one of the 48 instruments of the 8-operator FM from the pad 8 list sets the track's page 4
(the 8 sequenceable knobs) and its non-sequenceable page (Shift + pad 4) to the destinations of the instrument's family (make_examples.FAM_DEST:
keys, bass, lead, pad, pluck, perc, bell, wind), the knobs worth turning for that sound; the example patches of those instruments carry the same.

fm8ui's pad 8 list (pad 8 held + pads 9-32) loads an instrument by `mov r7, r0; mov r1, r6; bl c_fminst` with the track in r4: that bl ->
c_fmidest(r0 = the instrument 0..47, r1 = the track's block) = c_fminst, then vcf21's c_vrow / c_vrow2(track) (the rows, put to their defaults
the first time) get the family's 8 + 8 codes.  Nothing is sent: the knobs' values stay, the lanes' automation now moves the new destinations
(as Shift + knob does).  A save of the patch keeps them (p4dest's gather), Clear held + Shift + knob still brings back the factory one.
Flash: 48 bytes (each instrument's family) + 16 a family + the code, at the end of the image (build_sc41_5.add)."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import Asm, adds_imm8, adds_reg, b_cond, bl, cmp_imm, ldrb_reg, lsls_imm, mov_reg, movs_imm, movt, movw, pop_list, push_list, strb_reg, subs_imm8  # noqa: E402
import fm8inst as FI  # noqa: E402
import make_examples as MK  # noqa: E402

FAMS = tuple(MK.FAM_DEST)


def bl_target(img, addr, base):
    h1, h2 = struct.unpack_from("<HH", img, addr - base)
    if h1 & 0xF800 != 0xF000 or h2 & 0xD000 != 0xD000: return None
    s = (h1 >> 10) & 1; j1 = (h2 >> 13) & 1; j2 = (h2 >> 11) & 1
    i1, i2 = 1 - (j1 ^ s), 1 - (j2 ^ s)
    off = s << 24 | i1 << 23 | i2 << 22 | (h1 & 0x3FF) << 12 | (h2 & 0x7FF) << 1
    if s: off -= 1 << 25
    return addr + 4 + off


def tables():
    FI.use_v2()
    assert len(FI.INST) == 48 and all(x["fam"] in FAMS for x in FI.INST)
    fam = bytes(FAMS.index(x["fam"]) for x in FI.INST)
    dt = b"".join(bytes(MK.FAM_DEST[f][0]) + bytes(MK.FAM_DEST[f][1]) for f in FAMS)
    return fam, dt


def arm_code(base, prev):
    fam, dt = tables()
    data = fam + dt
    data += b"\xFF" * (-len(data) % 4)
    a = Asm(base + len(data))
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    # ---- c_fmidest(r0 = instrument, r1 = block; the caller's r4 = the track): the instrument, then the family's destinations
    a.label("c_fmidest")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 5, 0)
    E(bl, prev["c_fminst"])
    E(cmp_imm, 4, 1); E(b_cond, "fd_x", "hi"); E(cmp_imm, 5, len(fam)); E(b_cond, "fd_x", "hs")
    imm32(6, base); E(ldrb_reg, 6, 6, 5); E(lsls_imm, 6, 6, 4); imm32(7, base + len(fam)); E(adds_reg, 6, 6, 7)    # r6 = the family's 16 codes
    for fn in ("c_vrow", "c_vrow2"):                                                    # r0 = the row (clobbers r1-r3): r6[0..7] -> r0[0..7]
        E(mov_reg, 0, 4); E(bl, prev[fn])
        E(movs_imm, 7, 8)
        a.label(f"fd_{fn}")
        E(subs_imm8, 7, 1); E(ldrb_reg, 2, 6, 7); E(strb_reg, 2, 0, 7); E(cmp_imm, 7, 0); E(b_cond, f"fd_{fn}", "ne")
        E(adds_imm8, 6, 8)
    a.label("fd_x")
    E(pop_list, [4, 5, 6, 7], pc=True)
    code, labels = a.assemble()
    return data + code, labels


def site(img, report, base):
    """the bl c_fminst of fm8ui's pad 8 list (after mov r7, r0; mov r1, r6)"""
    fl = report["fm8"]
    lo = int(fl["arm_start"], 16) if "arm_start" in fl else min(int(v, 16) for v in fl["labels"].values())
    hi = max(int(v, 16) for v in fl["labels"].values()) + 0x400
    tgt = int(fl["labels"]["c_fminst"], 16)
    out = [a_ for a_ in range(lo & ~1, hi, 2) if bytes(img[a_ - 4 - base:a_ - base]) == bytes.fromhex("07463146") and bl_target(img, a_, base) == tgt]
    assert len(out) == 1, [hex(x) for x in out]
    return out[0], tgt


def install(img, report, base_addr):
    import ct_fw
    BASE = ct_fw.APP_BASE
    at, tgt = site(img, report, BASE)
    vl = report["vcf20"]["labels"]
    prev = dict(c_fminst=tgt, c_vrow=int(vl["c_vrow"], 16), c_vrow2=int(vl["c_vrow2"], 16), site=at)
    blob, labels = arm_code(base_addr, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + blob
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000, hex(len(img))
    img[at - BASE:at - BASE + 4] = bl(at, labels["c_fmidest"])
    return labels, blob, prev
