"""SC50.8: the DSP programs packed in the flash, unpacked while they are sent (the flash was full: about 20 KB come back).

The stock sends each DSP program from the flash as a Motorola bootstrap block (word count, load address, 24-bit words big-endian): 0x08029260(mode) sends a stub,
then 0x08029200(block, 0) from the table 0x08029700 = [core 0 mode 0, core 0 mode 1, core 1 mode 0, core 1 mode 1] (0x08029294), then 0x08029200(block, 1) (0x080292A6).
0x08029200 waits (0x0803B9D8), selects the core (0x080291B8), sends the block in chunks of at most 170 words (0x0803BA96(pointer, bytes): SPI by DMA, 0x0803B9D8
waits for it after each chunk), waits again and ends with 0x080291CA(core).  It runs at boot (0x0801F568) and again when the device goes back to mode 0 (0x0801F544).

Here the two mode-0 blocks (ours: build_sc16's relocated core 0 and granular_dsp's core 1) are packed in place at the very end of the build, after every DSP patch:
  + 0 'DZ1\\0', + 4 words of the block (count + address + program), + 8 CRC-32 of the block, + 12 the LZSS stream.
LZSS: a flag byte before every 8 items, bit 0 first, 1 = a literal byte, 0 = a match of two bytes: (offset - 1) in bits 0-12, length - 3 in bits 13-15; 7 = an extra
byte with length - 10 (10..265).  The window is the last 8 KB, kept in the ITCM at 0x2000..0x3FFF (16 KB at 0x0, free and never touched by the stock: S494D2);
the first 8 KB of the ITCM stay untouched.  The two bl sites go to c_dspz: a block without the magic (the mode-1 program) goes to 0x08029200 as before; ours are
unpacked chunk by chunk into a 510-byte buffer in the free RAM above the heap (0x20048000, DMA reaches it; the ITCM it may not), with exactly the stock's chunks,
waits and selects.  State of the unpacker at 0x20048200 (7 words).  The freed flash (the rest of each block) is filled with 0xFF and listed in report["dspz"]["gaps"].
"""
from __future__ import annotations
import hashlib, struct, sys, zlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldr_sp, ldrb_imm, ldrb_reg, lsls_imm, lsrs_imm,  # noqa: E402
                   movs_imm, movt, movw, orrs_reg, pop_list, push_list, str_imm, strb_imm, strb_reg, subs_imm8, subs_reg, add_sp_imm, mov_reg)

BASE = 0x08010000
TABLE = 0x08029700
SEND = 0x08029200                                   # the stock's sender (block, core)
SITES = (0x08029294, 0x080292A6)                    # its calls for core 0 / core 1 (mode from the table)
WAIT, SELECT, SPI, END = 0x0803B9D8, 0x080291B8, 0x0803BA96, 0x080291CA
CHUNK = 0xAA                                        # 170 words a chunk, as the stock
MAGIC = b"DZ1\0"
WIN, WBITS = 0x2000, 13                             # 8 KB window ...
RING = 0x2000                                       # ... at ITCM 0x2000
STAGE = 0x20048000                                  # 512 B (510 used)
S = 0x20048200                                      # + 0 src, + 4 flags, + 8 match left, + 12 match index, + 16 write index
MAXL = 265
CACHE = Path(__file__).resolve().parents[1] / "build" / "dspz_cache"


# ---------------------------------------------------------------- packing (build side)
def _pack(raw: bytes) -> bytes:
    n = len(raw)
    best = [(0, 0)] * n
    heads: dict = {}
    for i in range(n):
        bl_, bo = 0, 0
        chain = heads.get(raw[i:i + 3])
        if chain and i + 3 <= n:
            for k in range(len(chain) - 1, max(-1, len(chain) - 1 - 2048), -1):
                j = chain[k]
                if i - j > WIN: break
                l = 0
                while l < MAXL and i + l < n and raw[j + l] == raw[i + l]: l += 1
                if l > bl_: bl_, bo = l, i - j
                if l == MAXL: break
        best[i] = (bl_, bo)
        heads.setdefault(raw[i:i + 3], []).append(i)
    INF = 1 << 60
    cost = [INF] * (n + 1); cost[n] = 0
    pick = [0] * n                                   # 0 = literal, else the match length
    for i in range(n - 1, -1, -1):
        c, p = 9 + cost[i + 1], 0
        L = best[i][0]
        for l in range(3, L + 1):
            mc = (25 if l >= 10 else 17) + cost[i + l]
            if mc < c: c, p = mc, l
        cost[i], pick[i] = c, p
    out, flags, items, i = bytearray(), 0, bytearray(), 0
    nf = 0
    while i < n:
        l = pick[i]
        if l == 0:
            flags |= 1 << nf; items.append(raw[i]); i += 1
        else:
            o = best[i][1] - 1
            code = 7 if l >= 10 else l - 3
            items += bytes([o & 0xFF, (o >> 8) | code << 5])
            if code == 7: items.append(l - 10)
            i += l
        nf += 1
        if nf == 8:
            out.append(flags); out += items; flags, items, nf = 0, bytearray(), 0
    if nf: out.append(flags); out += items
    return bytes(out)


def unpack_stream(stream: bytes, size: int) -> bytes:
    out, i, flags = bytearray(), 0, 1
    while len(out) < size:
        if flags == 1: flags = stream[i] | 0x100; i += 1
        lit = flags & 1; flags >>= 1
        if lit:
            out.append(stream[i]); i += 1
        else:
            t = stream[i] | stream[i + 1] << 8; i += 2
            o, c = (t & 0x1FFF) + 1, t >> 13
            if c == 7: l = 10 + stream[i]; i += 1
            else: l = c + 3
            for _ in range(l): out.append(out[-o])
    assert len(out) == size
    return bytes(out)


def pack(raw: bytes) -> bytes:
    """The whole blob (header + stream), cached by the block's hash."""
    key = hashlib.sha256(raw).hexdigest()
    f = CACHE / f"{key}.dz"
    if f.exists():
        blob = f.read_bytes()
    else:
        assert len(raw) % 3 == 0
        blob = MAGIC + struct.pack("<II", len(raw) // 3, zlib.crc32(raw)) + _pack(raw)
        CACHE.mkdir(parents=True, exist_ok=True); f.write_bytes(blob)
    assert unblob(blob) == raw
    return blob


def unblob(blob: bytes) -> bytes:
    assert blob[:4] == MAGIC
    words, crc = struct.unpack_from("<II", blob, 4)
    raw = unpack_stream(blob[12:], 3 * words)
    assert zlib.crc32(raw) == crc
    return raw


def block_at(img, addr):
    """The bootstrap block at a flash address, packed or not (for tools and tests)."""
    o = addr - BASE
    if bytes(img[o:o + 4]) == MAGIC:
        words = struct.unpack_from("<I", img, o + 4)[0]
        return unblob(bytes(img[o:o + 12 + 3 * words + 64]))         # the stream never is longer than the raw block
    n = int.from_bytes(img[o:o + 3], "big")
    return bytes(img[o:o + 6 + 3 * n])


# ---------------------------------------------------------------- the unpacker (ARM)
def arm_code(base):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    # ---- c_dspz(block, core): in place of 0x08029200 at the two sites
    a.label("c_dspz")
    E(ldr_imm, 2, 0, 0); imm32(3, struct.unpack("<I", MAGIC)[0]); E(cmp_reg, 2, 3); E(b_cond, "dz_go", "eq")
    E(b_w, SEND)                                                        # not ours (the mode-1 program): the stock's sender
    a.label("dz_go")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 1)                                                    # r4 = core
    imm32(3, S)
    E(adds_imm8, 0, 12); E(str_imm, 0, 3, 0)                            # src
    E(movs_imm, 2, 1); E(str_imm, 2, 3, 4)                              # flags: empty
    E(movs_imm, 2, 0); E(str_imm, 2, 3, 8); E(str_imm, 2, 3, 16)        # no match, write index 0
    E(subs_imm8, 0, 12); E(ldr_imm, 6, 0, 4)                            # r6 = words of the block
    E(movs_imm, 5, 0)                                                   # r5 = words sent
    E(bl, WAIT)
    E(mov_reg, 0, 4); E(bl, SELECT)
    a.label("dz_lp")
    E(subs_reg, 7, 6, 5); E(cmp_imm, 7, CHUNK); E(b_cond, "dz_k", "le"); E(movs_imm, 7, CHUNK)
    a.label("dz_k")
    E(adds_reg, 5, 5, 7)
    E(adds_reg, 1, 7, 7); E(adds_reg, 7, 1, 7)                          # r7 = bytes of this chunk
    imm32(0, STAGE); E(mov_reg, 1, 7); E(bl, "dz_fill")
    imm32(0, STAGE); E(mov_reg, 1, 7); E(bl, SPI)
    E(bl, WAIT)
    E(cmp_reg, 5, 6); E(b_cond, "dz_lp", "lt")
    E(bl, WAIT)
    E(mov_reg, 0, 4); E(pop_list, [4, 5, 6, 7]); E(pop_list, [3])       # lr back through r3
    E(mov_reg, 14, 3); E(b_w, END)
    # ---- dz_fill(dst, bytes): r0 dst, [sp] end, r1 the ring, r2 src, r3 flags, r4 match left, r5 match index, r6 write index, r7 byte
    a.label("dz_fill")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(adds_reg, 1, 0, 1); E(push_list, [1])                             # [sp] = end
    imm32(7, S); E(ldr_imm, 2, 7, 0); E(ldr_imm, 3, 7, 4); E(ldr_imm, 4, 7, 8); E(ldr_imm, 5, 7, 12); E(ldr_imm, 6, 7, 16)
    E(movs_imm, 1, RING >> 8); E(lsls_imm, 1, 1, 8)
    a.label("df_lp")
    E(ldr_sp, 7, 0); E(cmp_reg, 0, 7); E(b_cond, "df_x", "hs")
    E(cmp_imm, 4, 0); E(b_cond, "df_cp", "ne")
    E(cmp_imm, 3, 1); E(b_cond, "df_fl", "ne")
    E(ldrb_imm, 3, 2, 0); E(adds_imm8, 2, 1); E(movs_imm, 7, 1); E(lsls_imm, 7, 7, 8); E(orrs_reg, 3, 7)
    a.label("df_fl")
    E(lsrs_imm, 3, 3, 1); E(b_cond, "df_m", "cc")
    E(ldrb_imm, 7, 2, 0); E(adds_imm8, 2, 1); E(b, "df_put")
    a.label("df_m")
    E(ldrb_imm, 7, 2, 0); E(ldrb_imm, 5, 2, 1); E(adds_imm8, 2, 2)
    E(lsrs_imm, 4, 5, 5); E(lsls_imm, 5, 5, 27); E(lsrs_imm, 5, 5, 19); E(orrs_reg, 5, 7)    # r4 = length code, r5 = offset - 1
    E(cmp_imm, 4, 7); E(b_cond, "df_s", "ne")
    E(ldrb_imm, 7, 2, 0); E(adds_imm8, 2, 1); E(adds_reg, 4, 4, 7)      # 7 + extra (+ 3 below = 10 + extra)
    a.label("df_s")
    E(adds_imm8, 4, 3)
    E(subs_reg, 5, 6, 5); E(subs_imm8, 5, 1); E(lsls_imm, 5, 5, 32 - WBITS); E(lsrs_imm, 5, 5, 32 - WBITS)
    a.label("df_cp")
    E(ldrb_reg, 7, 1, 5); E(adds_imm8, 5, 1); E(lsls_imm, 5, 5, 32 - WBITS); E(lsrs_imm, 5, 5, 32 - WBITS)
    E(subs_imm8, 4, 1)
    a.label("df_put")
    E(strb_reg, 7, 1, 6); E(adds_imm8, 6, 1); E(lsls_imm, 6, 6, 32 - WBITS); E(lsrs_imm, 6, 6, 32 - WBITS)
    E(strb_imm, 7, 0, 0); E(adds_imm8, 0, 1); E(b, "df_lp")
    a.label("df_x")
    imm32(7, S); E(str_imm, 2, 7, 0); E(str_imm, 3, 7, 4); E(str_imm, 4, 7, 8); E(str_imm, 5, 7, 12); E(str_imm, 6, 7, 16)
    E(add_sp_imm, 4); E(pop_list, [4, 5, 6, 7], pc=True)
    return a.assemble()


OVERRIDE = {}                                       # core -> raw block -> the block to pack instead (granular_dsp.use_fmc1)


def install(img, report):
    """Last step of a build: pack the two mode-0 blocks in place, the unpacker after the core-0 blob, the two sites to it."""
    from thumb import bl as bl_enc
    for s in SITES:
        assert bytes(img[s - BASE:s - BASE + 4]) == bl_enc(s, SEND), hex(s)
    info, gaps, code_at = {}, [], None
    for core in (0, 1):
        at = struct.unpack_from("<I", img, TABLE + 8 * core - BASE)[0]
        o = at - BASE
        raw = block_at(img, at)
        assert bytes(img[o:o + len(raw)]) == raw, f"core {core}: block already packed"
        new = OVERRIDE[core](raw) if core in OVERRIDE else raw                # (granular_dsp.use_fmc1) a longer core 1 block, packed into the old one's place
        blob = pack(new)
        assert len(blob) <= len(raw)
        img[o:o + len(raw)] = blob + b"\xFF" * (len(raw) - len(blob))
        end = (at + len(blob) + 3) & ~3
        if core == 0:
            code_at = end
            code, labels = arm_code(code_at)
            img[code_at - BASE:code_at - BASE + len(code)] = code
            end = (code_at + len(code) + 3) & ~3
        assert end <= at + len(raw)
        gaps.append([hex(end), hex(at + len(raw))])
        info[f"core{core}"] = dict(block=hex(at), raw=len(new), packed=len(blob), crc32=hex(zlib.crc32(new)))
    for s in SITES:
        img[s - BASE:s - BASE + 4] = bl_enc(s, labels["c_dspz"])
    import build_shared_channels as sc
    report["dspz"] = dict(info, labels={k: hex(v) for k, v in labels.items()}, arm_start=hex(code_at), ring=hex(RING), stage=hex(STAGE), state=hex(S),
                          gaps=gaps, freed=sum(int(b_, 16) - int(a_, 16) for a_, b_ in gaps), listing=sc.disasm(bytes(code), code_at))
    return labels


def add(img, report, name, mod, gap=0):
    """After install(): put an ARM module in the freed flash, in the first gap (19 853 B), as hole.add does for the old blocks.  mod.install(img,
    report, base) appends its code at the end as for build_sc41_5.add; that tail moves into the gap and the image is cut back.  The gap is above
    MOD_START (0x0805CDDC): rodisk's guard and lazysave see code here as the mod's."""
    import build_shared_channels as sc
    d = report["dspz"]
    lo, hi = d["gaps"][gap]
    nk = "next" if gap == 0 else f"next{gap}"                                    # (gap 1: the second gap, SC52.2's ovltop)
    at = (int(d.setdefault(nk, lo), 16) + 3) & ~3
    n0 = len(img)
    labels, code, prev = mod.install(img, report, at)
    blob = bytes(img[n0:])
    assert blob[:len(code)] == bytes(code), f"{name}: install did not append its code at the end"
    del img[n0:]
    end = at + len(blob)
    assert end <= int(hi, 16), f"{name}: the gap is full ({end:#x} > {hi})"
    assert all(b_ == 0xFF for b_ in img[at - BASE:end - BASE]), f"{name}: the gap is not empty"
    img[at - BASE:end - BASE] = blob
    d[nk] = hex(end)
    d.setdefault("blocks", {})[name] = [hex(at), hex(end)]
    report[name] = dict(arm_start=hex(at), labels={k: hex(v) for k, v in labels.items()}, prev={k: hex(v) for k, v in prev.items()},
                        listing=sc.disasm(bytes(code), at), dspz_gap=True)
    return labels
