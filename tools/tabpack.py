"""SC55.8 (room in the flash for the pattern mutate; the user, 2026-11-10: «Both» = the curve tables and the FM tables): tables kept packed in
the flash and rebuilt in free memory every time core 0's DSP program is sent (at power-up, before anything reads them, and when the unit goes back
to mode 0, writing the same bytes again).

  * curve tables (Master FX: PHPER, SMPI, GK, PHTAB; the FM's FIX): their second differences, one or two bytes each (exact, modulo 2^32), into
    RAM 0x20048620-0x20048FFF (after mfxgen's tables: tools/memmap.py's free range);
  * the FM's byte tables (algorithms, defaults, the DX7 defaults, detune, ...): one LZ stream (fm8inst.lz, unpacked by fm8ui's c_fiun) into the
    ITCM 0x18A4-0x1FFF (after the instruments, below dspz's window at 0x2000).

The modules ask want(name, data, kind) for an address while they build (fm8arm.data, build_sc17's tabaddr); install() (the last of the build)
writes the stream (magic "TBPK" for the emulation's harnesses: emu_load) and c_tboot, which the bl at dspz.SITES[0] (core 0's program) now
calls: the tables rebuilt, then c_dspz with the same arguments.  The stream is decoded here at build time and compared with the tables.

Record: u32 destination (0 = the end), u16 n, u8 kind, u8 w.  kind 0 = LZ (n = bytes out), then the packed stream; kind 2 / 4 = n elements of
2 / 4 bytes: v0, v1 (s32), then n - 2 second differences of w bytes (signed).  Each record starts on a word.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, bics_reg, bl, cmp_imm, h, ldr_imm, ldr_sp, ldrb_imm, ldrh_imm, mov_reg, movs_imm,  # noqa: E402
                   movt, movw, pop_list, push_list, raw, str_imm, strh_imm, subs_imm8, subs_reg)

ON = False
MAGIC = b"TBPK"
RAM = (0x20048620, 0x20049000)                 # the curve tables
ITCM = (0x18A4, 0x2000)                        # the LZ group
CURVES_MFX = ("PHPER", "SMPI", "GK", "PHTAB")
CURVES_FM = ("fix",)
LZ_FM = ("algs", "def8", "dxdef", "det", "rof", "kvsa", "ksa", "susm", "algf", "opdef", "fam", "kd", "icol")
BASE = 0x08010000
ST = {}


def use():
    global ON
    ON = True
    ST.clear()
    ST.update(items={}, ram=RAM[0], lz=ITCM[0], order=[])


def wants(name):
    return ON and name in CURVES_MFX + CURVES_FM + LZ_FM


def want(name, data, ew=None):
    """the address of `name` (its bytes `data`; ew = 2 / 4: a curve of elements that size, else a member of the LZ group)"""
    it = ST["items"].get(name)
    if it is not None:
        assert it["data"] == bytes(data), name
        return it["at"]
    data = bytes(data)
    if ew:
        assert len(data) % ew == 0
        at = ST["ram"]; ST["ram"] += (len(data) + 3) & ~3; assert ST["ram"] <= RAM[1], name
    else:
        at = ST["lz"]; ST["lz"] += (len(data) + 3) & ~3; assert ST["lz"] <= ITCM[1], name
    ST["items"][name] = dict(at=at, data=data, ew=ew); ST["order"].append(name)
    return at


def _d2(data, ew):
    fmt = "<%d%s" % (len(data) // ew, "h" if ew == 2 else "i")
    v = list(struct.unpack(fmt, data))
    d1 = [(v[i] - v[i - 1]) for i in range(1, len(v))]
    d2 = [d1[i] - d1[i - 1] for i in range(1, len(d1))]
    w = 1 if all(-128 <= x < 128 for x in d2) else 2
    assert all(-32768 <= x < 32768 for x in d2)
    body = struct.pack("<ii", v[0], v[1]) + b"".join(struct.pack("<b" if w == 1 else "<h", x) for x in d2)
    return w, body


def stream():
    import fm8inst as FI
    out = bytearray()
    def rec(dest, n, kind, w, body):
        out.extend(struct.pack("<IHBB", dest, n, kind, w)); out.extend(body)
        while len(out) % 4: out.append(0)
    for name in ST["order"]:
        it = ST["items"][name]
        if it["ew"]:
            w, body = _d2(it["data"], it["ew"])
            rec(it["at"], len(it["data"]) // it["ew"], it["ew"], w, body)
    lz = [ST["items"][n] for n in ST["order"] if not ST["items"][n]["ew"]]
    if lz:
        lo = lz[0]["at"]; img = bytearray(ST["lz"] - lo)
        for it in lz: img[it["at"] - lo:it["at"] - lo + len(it["data"])] = it["data"]
        rec(lo, len(img), 0, 0, FI.lz(bytes(img)))
    out.extend(struct.pack("<I", 0))
    return bytes(out)


def decode(s, write):
    """the stream `s` (from its first record) -> write(address, bytes) for each table; returns the bytes read"""
    import fm8inst as FI
    i = 0
    while True:
        dest, = struct.unpack_from("<I", s, i)
        if dest == 0: return i + 4
        n, kind, w = struct.unpack_from("<HBB", s, i + 4); i += 8
        if kind == 0:
            p = s[i:]
            out = FI.unlz(p, n)
            # the packed length: re-pack is what the build wrote, so its length is exact
            ln = len(FI.lz(out)); i += ln; write(dest, out)
        else:
            v0, v1 = struct.unpack_from("<ii", s, i); i += 8
            vals = [v0, v1]; d1 = v1 - v0
            for _ in range(n - 2):
                d, = struct.unpack_from("<b" if w == 1 else "<h", s, i); i += w
                d1 += d; vals.append((vals[-1] + d1))
            mask = (1 << (8 * kind)) - 1
            write(dest, b"".join((x & mask).to_bytes(kind, "little") for x in vals))
        i = (i + 3) & ~3


def emu_load(uc, image):
    """(the emulation's harnesses) the tables a build carries, written where c_tboot puts them"""
    i = bytes(image).find(MAGIC)
    if i < 0: return
    decode(bytes(image[i + 8:]), lambda a, b_: uc.mem_write(a, bytes(b_)))


def SXTB(rd, rm): return h(0xB240 | rm << 3 | rd)
def SXTH(rd, rm): return h(0xB200 | rm << 3 | rd)


def arm_code(base, s, prev):
    """the stream's header + stream, then c_tbun / c_tboot"""
    data = MAGIC + struct.pack("<I", len(s)) + s
    a = Asm(base + len(data))
    E = a.emit
    # ---- c_tboot (in place of the bl c_dspz at dspz.SITES[0]): the tables, then c_dspz(r0..r3) -> its r0
    a.label("c_tboot")
    E(push_list, [0, 1, 2, 3, 4], lr=True)
    E(movw, 0, (base + 8) & 0xFFFF); E(movt, 0, (base + 8) >> 16)
    E(bl, "c_tbun")
    E(ldr_sp, 0, 0); E(ldr_sp, 1, 4); E(ldr_sp, 2, 8); E(ldr_sp, 3, 12)
    E(bl, prev["c_dspz"])
    E(raw, h(0xB004))                                   # add sp, #16
    E(pop_list, [4], pc=True)
    # ---- c_tbun(r0 = the first record): every record; clobbers r0-r3
    a.label("c_tbun")
    E(push_list, [4, 5, 6, 7], lr=True)
    a.label("tu_r")
    E(ldr_imm, 4, 0, 0); E(cmp_imm, 4, 0); E(b_cond, "tu_x", "eq")
    E(ldrh_imm, 5, 0, 4); E(ldrb_imm, 6, 0, 6); E(ldrb_imm, 7, 0, 7); E(adds_imm8, 0, 8)
    E(cmp_imm, 6, 0); E(b_cond, "tu_d", "ne")
    E(mov_reg, 1, 4); E(adds_reg, 2, 4, 5); E(bl, prev["c_fiun"]); E(b, "tu_a")
    a.label("tu_d")                                     # r1 = v, r2 = d1
    E(ldr_imm, 1, 0, 0); E(ldr_imm, 2, 0, 4); E(adds_imm8, 0, 8)
    E(bl, "tu_st"); E(subs_reg, 2, 2, 1); E(adds_reg, 1, 1, 2)                    # v0 stored; r2 = d1 = v1 - v0, r1 = v1
    E(bl, "tu_st"); E(subs_imm8, 5, 2)
    a.label("tu_l")
    E(cmp_imm, 5, 0); E(b_cond, "tu_a", "eq")
    E(cmp_imm, 7, 1); E(b_cond, "tu_2", "ne")
    E(ldrb_imm, 3, 0, 0); E(raw, SXTB(3, 3)); E(adds_imm8, 0, 1); E(b, "tu_3")
    a.label("tu_2")
    E(ldrh_imm, 3, 0, 0); E(raw, SXTH(3, 3)); E(adds_imm8, 0, 2)
    a.label("tu_3")
    E(adds_reg, 2, 2, 3); E(adds_reg, 1, 1, 2); E(bl, "tu_st"); E(subs_imm8, 5, 1); E(b, "tu_l")
    a.label("tu_a")                                     # the next record on a word
    E(adds_imm8, 0, 3); E(movs_imm, 3, 3); E(bics_reg, 0, 3); E(b, "tu_r")
    a.label("tu_x")
    E(pop_list, [4, 5, 6, 7], pc=True)
    # ---- tu_st: r1 to [r4] (r6 = 2 / 4 bytes), r4 += r6; clobbers nothing else
    a.label("tu_st")
    E(cmp_imm, 6, 2); E(b_cond, "ts_4", "ne")
    E(strh_imm, 1, 4, 0); E(adds_imm8, 4, 2); E(raw, h(0x4770))
    a.label("ts_4")
    E(str_imm, 1, 4, 0); E(adds_imm8, 4, 4); E(raw, h(0x4770))
    code, labels = a.assemble()
    labels["tbpk"] = base
    return data + bytes(code), labels


def install(img, report, base_addr):
    import dspz
    from thumb import bl as bl_enc
    import fm8dest as FD
    s = stream()
    got = {}
    def wr(a_, b_):
        got[a_] = bytes(b_)
    decode(s, wr)
    for name in ST["order"]:                            # the decoder gives back every table
        it = ST["items"][name]
        if it["ew"]: assert got[it["at"]] == it["data"], name
    lz = [ST["items"][n] for n in ST["order"] if not ST["items"][n]["ew"]]
    if lz:
        blob = got[lz[0]["at"]]
        for it in lz: assert blob[it["at"] - lz[0]["at"]:it["at"] - lz[0]["at"] + len(it["data"])] == it["data"]
    site = dspz.SITES[0]
    tgt = FD.bl_target(img, site, BASE)
    assert tgt == int(report["dspz"]["labels"]["c_dspz"], 16), hex(tgt or 0)
    prev = dict(c_dspz=tgt, c_fiun=int(report["fm8"]["labels"]["c_fiun"], 16), site=site)
    base = (base_addr + 3) & ~3
    blob, labels = arm_code(base, s, prev)
    img += bytes([0xFF]) * (base - BASE - len(img)) + blob
    while len(img) % 4: img += bytes([0xFF])
    assert len(img) <= 0x70000, hex(len(img))
    img[site - BASE:site - BASE + 4] = bl_enc(site, labels["c_tboot"])
    saved = sum(len(ST["items"][n]["data"]) for n in ST["order"]) - len(blob)
    report.setdefault("tabpack_info", {}).update(tables=list(ST["order"]), stream=len(s), blob=len(blob), saved=saved)
    return labels, blob, prev
