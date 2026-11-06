"""Code in the ITCM (the user, 2026-11-06: «Primero ITCM y luego NOR», then the flash was full for the next requests): ARM modules assembled for the
ITCM, kept packed in the flash (dspz's LZSS) and unpacked at power-up.

  * The ITCM: 16 KB at 0x0, free and executable (S494D2); 0x2000-0x3FFF is dspz's window while the DSP programs are sent (at power-up and when the
    unit goes back to mode 0), so the code lives in 0x100-0x1FFF: a magic word at 0x100, the modules upwards from 0x104, the veneers downwards from
    0x2000.
  * Calls and branches between the flash and the ITCM are out of reach of bl / b.w (±16 MB): thumb.FAR gives the encoders a veneer within reach
    (ldr.w pc, [pc]; .word target): in the ITCM for the ITCM's calls into the flash (part of the packed image), in the flash (an area kept in
    dspz's first gap) for the flash's calls and hooks into the ITCM.  A vtable slot holds the ITCM address itself.
  * finish(): the image 0x100-0x1FFF packed, its header «ITCZ» (stream address, size, destination), the unpacker and c_itboot in dspz's first gap;
    the bl at dspz.SITES[0] (core 0's program, the first thing the unit sends at power-up) goes to c_itboot: no magic at 0x100 = unpack (dsb, isb),
    then dspz's c_dspz as before.  The emulation's harnesses unpack it the same way when they find the header (emu_sc05.E).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import thumb  # noqa: E402
from thumb import (Asm, adds_imm8, ands_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, lsls_imm, lsrs_imm, mov_reg,  # noqa: E402
                   movs_imm, movt, movw, orrs_reg, pop_list, push_list, raw, strb_imm, subs_imm8, subs_reg)

LO, HI = 0x100, 0x2000
MAGIC = 0x4D435449                          # "ITCM"
HDR = b"ITCZ"
FLASH_VEN = 32                              # veneers kept in the flash (8 B each)
BASE = 0x08010000
ST = None                                   # the state of this build: the image, next, veneers


def _ven(target):
    return h(0xF8DF) + h(0xF000) + struct.pack("<I", target | 1)        # ldr.w pc, [pc, #0]; .word target


def _far(addr, target):
    if addr < 0x08000000 and target >= 0x08000000:                      # ITCM -> flash: a veneer in the ITCM (top down)
        v = ST["iv"].get(target)
        if v is None:
            ST["vlo"] -= 8; v = ST["vlo"]; ST["iv"][target] = v
        return v
    if addr >= 0x08000000 and target < 0x08000000:                      # flash -> ITCM: a veneer in the flash area
        v = ST["fv"].get(target)
        if v is None:
            assert ST["fnext"] + 8 <= ST["fend"], "itcm: the flash veneers are full"
            v = ST["fnext"]; ST["fnext"] += 8; ST["fv"][target] = v
            ST["img"][v - BASE:v - BASE + 8] = _ven(target)
        return v
    raise AssertionError(f"itcm: out of reach {addr:#x} -> {target:#x}")


def start(img, report):
    """the first module: the state, the flash veneer area in dspz's first gap, the encoders' hook"""
    global ST
    if ST is not None and ST["img"] is img: return
    d = report["dspz"]
    at = (int(d.get("next", d["gaps"][0][0]), 16) + 3) & ~3
    assert at + 8 * FLASH_VEN <= int(d["gaps"][0][1], 16)
    d["next"] = hex(at + 8 * FLASH_VEN)
    ST = dict(img=img, buf=bytearray(HI - LO), next=LO + 4, vlo=HI, iv={}, fv={}, fnext=at, fend=at + 8 * FLASH_VEN, blocks={})
    struct.pack_into("<I", ST["buf"], 0, MAGIC)
    thumb.FAR = _far
    report["itcm"] = dict(flash_veneers=hex(at))


def add(img, report, name, mod):
    """as dspz.add, into the ITCM"""
    import build_shared_channels as sc
    start(img, report)
    at = (ST["next"] + 3) & ~3
    n0 = len(img)
    labels, code, prev = mod.install(img, report, at)
    blob = bytes(img[n0:])
    assert blob[:len(code)] == bytes(code), f"{name}: install did not append its code at the end"
    del img[n0:]
    end = at + len(blob)
    assert end <= ST["vlo"], f"{name}: the ITCM is full ({end:#x} > {ST['vlo']:#x})"
    ST["buf"][at - LO:end - LO] = blob
    ST["next"] = end; ST["blocks"][name] = [hex(at), hex(end)]
    report[name] = dict(arm_start=hex(at), labels={k: hex(v) for k, v in labels.items()}, prev={k: hex(v) for k, v in prev.items()},
                        listing=sc.disasm(bytes(code), at), itcm=True)
    return labels


def unpacker(base, stream_at, size, c_dspz):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    # ---- c_itboot (the bl at dspz.SITES[0], core 0's program): the ITCM unpacked when its magic is missing, then dspz's c_dspz
    a.label("c_itboot")
    E(raw, h(0xE92D) + h(0x400F))                                                 # push.w {r0-r3, lr}
    imm32(0, LO); E(ldr_imm, 1, 0, 0); imm32(2, MAGIC); E(cmp_reg, 1, 2); E(b_cond, "ib_x", "eq")
    a.label("c_itload")                                                          # (also the emulation's entry: unpacks unconditionally from here)
    imm32(0, stream_at); imm32(1, LO); imm32(2, LO + size)
    E(movs_imm, 3, 1)
    a.label("iu_l"); E(cmp_reg, 1, 2); E(b_cond, "iu_d", "hs")
    E(cmp_imm, 3, 1); E(b_cond, "iu_f", "ne")
    E(ldrb_imm, 3, 0, 0); E(adds_imm8, 0, 1); E(movs_imm, 4, 1); E(lsls_imm, 4, 4, 8); E(orrs_reg, 3, 4)
    a.label("iu_f"); E(movs_imm, 4, 1); E(ands_reg, 4, 3); E(lsrs_imm, 3, 3, 1); E(cmp_imm, 4, 0); E(b_cond, "iu_m", "eq")
    E(ldrb_imm, 4, 0, 0); E(adds_imm8, 0, 1); E(strb_imm, 4, 1, 0); E(adds_imm8, 1, 1); E(b, "iu_l")
    a.label("iu_m"); E(ldrb_imm, 4, 0, 0); E(ldrb_imm, 5, 0, 1); E(adds_imm8, 0, 2); E(lsls_imm, 5, 5, 8); E(orrs_reg, 4, 5)
    E(lsrs_imm, 5, 4, 13); E(lsls_imm, 4, 4, 19); E(lsrs_imm, 4, 4, 19); E(adds_imm8, 4, 1)
    E(cmp_imm, 5, 7); E(b_cond, "iu_s", "ne"); E(ldrb_imm, 5, 0, 0); E(adds_imm8, 0, 1); E(adds_imm8, 5, 7)
    a.label("iu_s"); E(adds_imm8, 5, 3); E(subs_reg, 6, 1, 4)
    a.label("iu_c"); E(ldrb_imm, 7, 6, 0); E(adds_imm8, 6, 1); E(strb_imm, 7, 1, 0); E(adds_imm8, 1, 1); E(subs_imm8, 5, 1); E(b_cond, "iu_c", "ne")
    E(b, "iu_l")
    a.label("iu_d"); E(raw, h(0xF3BF) + h(0x8F4F) + h(0xF3BF) + h(0x8F6F))        # dsb sy; isb sy
    a.label("ib_x"); E(raw, h(0xE8BD) + h(0x400F)); E(b_w, c_dspz)                # pop.w {r0-r3, lr}
    return a.assemble()


def finish(img, report):
    """the packed image, its header, the unpacker in dspz's first gap; dspz.SITES[0] -> c_itboot"""
    global ST
    import dspz
    import modmx as MX
    for tgt, v in ST["iv"].items(): ST["buf"][v - LO:v - LO + 8] = _ven(tgt)
    raw_ = bytes(ST["buf"])
    stream = dspz._pack(raw_)
    assert dspz.unpack_stream(stream, len(raw_)) == raw_
    d = report["dspz"]
    at = (int(d["next"], 16) + 3) & ~3
    hdr_at = at
    s_at = at + 16
    c_at = (s_at + len(stream) + 3) & ~3
    site = dspz.SITES[0]
    c_dspz = MX.bl_target(img, site, BASE)
    code, labels = unpacker(c_at, s_at, len(raw_), c_dspz)
    end = c_at + len(code)
    assert end <= int(d["gaps"][0][1], 16), f"itcm: dspz's first gap is full ({end:#x})"
    blob = HDR + struct.pack("<III", s_at, len(raw_), LO)
    img[hdr_at - BASE:hdr_at - BASE + 16] = blob
    img[s_at - BASE:s_at - BASE + len(stream)] = stream
    img[c_at - BASE:end - BASE] = code
    d["next"] = hex(end)
    img[site - BASE:site - BASE + 4] = thumb.bl(site, labels["c_itboot"])
    report["itcm"].update(header=hex(hdr_at), stream=[hex(s_at), len(stream)], raw=len(raw_), used=hex(ST["next"]), veneers_lo=hex(ST["vlo"]),
                          flash_veneers_used=len(ST["fv"]), itcm_veneers=len(ST["iv"]), blocks=ST["blocks"], labels={k: hex(v) for k, v in labels.items()})
    thumb.FAR = None
    ST = None


def unpack_image(image):
    """(the emulation) the ITCM image a build carries, or None: (destination, bytes)"""
    import dspz
    i = image.find(HDR)
    if i < 0: return None
    s_at, size, dst = struct.unpack_from("<III", image, i + 4)
    o = s_at - BASE
    return dst, dspz.unpack_stream(bytes(image[o:o + size + 4096]), size)
