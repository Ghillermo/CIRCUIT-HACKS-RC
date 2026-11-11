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
                   movs_imm, movt, movw, orrs_reg, pop_list, push_list, str_imm, strb_imm, strb_reg, subs_imm8, subs_reg, add_sp_imm, mov_reg,
                   h, raw, muls, ldrh_imm, strh_imm, bics_reg, ands_reg, lsls_reg, bx_lr, str_sp, subs_imm3, adds_imm3)

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


def pack(raw: bytes, v2=None) -> bytes:
    """The whole blob (header + stream), cached by the block's hash (v2: the format; None = this build's)."""
    v2 = V2 if v2 is None else v2
    key = hashlib.sha256(raw).hexdigest()
    f = CACHE / (f"{key}.dz2" if v2 else f"{key}.dz")
    if f.exists():
        blob = f.read_bytes()
    else:
        assert len(raw) % 3 == 0
        blob = (MAGIC2 if v2 else MAGIC) + struct.pack("<II", len(raw) // 3, zlib.crc32(raw)) + (_pack2(raw) if v2 else _pack(raw))
        CACHE.mkdir(parents=True, exist_ok=True); f.write_bytes(blob)
    assert unblob(blob) == raw
    return blob


def unblob(blob: bytes) -> bytes:
    assert blob[:4] in (MAGIC, MAGIC2)
    words, crc = struct.unpack_from("<II", blob, 4)
    raw = (unpack_stream2 if blob[:4] == MAGIC2 else unpack_stream)(blob[12:], 3 * words)
    assert zlib.crc32(raw) == crc
    return raw


def block_at(img, addr):
    """The bootstrap block at a flash address, packed or not (for tools and tests)."""
    o = addr - BASE
    if bytes(img[o:o + 4]) in (MAGIC, MAGIC2):
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
        assert len(blob) <= len(raw) and (at & 3 == 0 or not V2)              # (v2 reads the stream's first word with ldr)
        img[o:o + len(raw)] = blob + b"\xFF" * (len(raw) - len(blob))
        end = (at + len(blob) + 3) & ~3
        if core == 0:
            code_at = end
            code, labels = (arm_code2 if V2 else arm_code)(code_at)
            img[code_at - BASE:code_at - BASE + len(code)] = code
            end = (code_at + len(code) + 3) & ~3
        assert end <= at + len(raw)
        gaps.append([hex(end), hex(at + len(raw))])
        info[f"core{core}"] = dict(block=hex(at), raw=len(new), packed=len(blob), crc32=hex(zlib.crc32(new)))
    for s in SITES:
        img[s - BASE:s - BASE + 4] = bl_enc(s, labels["c_dspz"])
    import build_shared_channels as sc
    if V2: info.update(v2=True, probs=hex(PROBS), nprob=NPROB, window=hex(RING2))
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


# ================================================================ v2 (SC56): LZ + adaptive binary range coding
# use_v2(): the two blocks packed as 'DZ2\0' + words + CRC-32 + the stream (the user, 2026-11-10, «build 1 and then 2»: room in the flash, nothing lost).
# The model is LZMA's with fewer parts (lc = lp = pb = 0, rep0 only, short rep, matched literals), the window 4 KB (ITCM 0x3000..0x3FFF) and the 1 738
# probabilities (11 bits, in halfwords) in ITCM 0x2000..0x2D93: both only while a block is sent.  The range coder is LZMA's (top 2^24, move 5); the
# stream starts with the decoder's first four code bytes (the encoder's always-0 first byte is dropped).  The encoder is integer only and deterministic
# (two passes: an optimal parse with the prices of the first pass's probabilities), so the installer's JavaScript (dzPack2) gives the same bytes.
V2 = False
MAGIC2 = b"DZ2\0"
WIN2 = 0x1000
RING2 = 0x3000
PROBS = 0x2000
MAXL2 = 273
PBITS, PMOVE, PONE, PTOP = 11, 5, 1 << 11, 1 << 24
# probability indices: literals first (the literal loop adds nothing)
LIT, ISM, ISR, ISR0L = 0, 0x300, 0x30C, 0x318
MLEN, RLEN = 0x324, 0x324 + 274
SLOT = RLEN + 274
SPEC = SLOT + 256
ALIGN = SPEC + 114
NPROB = ALIGN + 16
NEXT_LIT = (0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 4, 5)


def use_v2():
    global V2
    V2 = True


def _prices():
    P = []
    for i in range(PONE >> 4):
        w, bc = (i << 4) + 8, 0
        for _ in range(4):
            w = w * w; bc <<= 1
            while w >= 1 << 16: w >>= 1; bc += 1
        P.append((PBITS << 4) - 15 - bc)
    return P


_PT = _prices()


def _slot(d):
    if d < 4: return d
    n = d.bit_length() - 1
    return 2 * n + ((d >> (n - 1)) & 1)


def _lit_bits(byte, st, mbyte):
    """(index, bit) of a literal; matched (st >= 7) as LZMA's: offs = 0x100 while the bits agree with the match byte's."""
    offs = 0x100 if st >= 7 else 0
    m, sym, out = mbyte, 1, []
    for k in range(7, -1, -1):
        m <<= 1; bit = m & offs; b = (byte >> k) & 1
        out.append((LIT + offs + bit + sym, b))
        sym = sym << 1 | b
        offs = offs & bit if b else offs & ~bit
    return out


def _len_bits(o, l):
    l -= 2
    if l < 8: out, sub, nb, base = [(o, 0)], l, 3, o + 2
    elif l < 16: out, sub, nb, base = [(o, 1), (o + 1, 0)], l - 8, 3, o + 10
    else: out, sub, nb, base = [(o, 1), (o + 1, 1)], l - 16, 8, o + 18
    m = 1
    for j in range(nb - 1, -1, -1):
        b = (sub >> j) & 1; out.append((base + m, b)); m = m << 1 | b
    return out


def _dist_bits(l, d):
    """(index, bit) and ('D', value, n) for the direct bits."""
    sl, out, m = _slot(d), [], 1
    base = SLOT + 64 * min(l - 2, 3)
    for j in range(5, -1, -1):
        b = (sl >> j) & 1; out.append((base + m, b)); m = m << 1 | b
    if sl >= 4:
        nd = (sl >> 1) - 1; bse = (2 | (sl & 1)) << nd; rem = d - bse
        if sl < 14:
            o, m = SPEC + bse - sl - 1, 1
            for j in range(nd):
                b = (rem >> j) & 1; out.append((o + m, b)); m = m << 1 | b
        else:
            out.append(("D", rem >> 4, nd - 4)); m = 1
            for j in range(4):
                b = (rem >> j) & 1; out.append((ALIGN + m, b)); m = m << 1 | b
    return out


class _Enc:
    def __init__(s):
        s.low, s.rng, s.cache, s.csize, s.out = 0, 0xFFFFFFFF, 0, 1, bytearray()

    def _shift(s):
        if s.low < 0xFF000000 or s.low >= 1 << 32:
            c, t = s.low >> 32, s.cache
            while True:
                s.out.append((t + c) & 0xFF); t = 0xFF; s.csize -= 1
                if s.csize == 0: break
            s.cache = (s.low >> 24) & 0xFF
        s.csize += 1
        s.low = (s.low & 0x00FFFFFF) << 8

    def bits(s, P, seq):
        for t in seq:
            if t[0] == "D":
                v, n = t[1], t[2]
                for k in range(n - 1, -1, -1):
                    s.rng >>= 1
                    if (v >> k) & 1: s.low += s.rng
                    if s.rng < PTOP: s.rng = (s.rng << 8) & 0xFFFFFFFF; s._shift()
                continue
            i, b = t
            p = P[i]; bound = (s.rng >> PBITS) * p
            if b == 0: s.rng = bound; P[i] = p + ((PONE - p) >> PMOVE)
            else: s.low += bound; s.rng -= bound; P[i] = p - (p >> PMOVE)
            if s.rng < PTOP: s.rng = (s.rng << 8) & 0xFFFFFFFF; s._shift()

    def flush(s):
        for _ in range(5): s._shift()
        assert s.out[0] == 0
        return bytes(s.out[1:])


def _matches(raw):
    """At every position the (length, distance - 1) pairs of growing length, nearest first, inside the window."""
    n, heads, res = len(raw), {}, []
    for i in range(n):
        out = []
        if i + 2 <= n:
            key = raw[i] << 8 | raw[i + 1]
            ch = heads.get(key)
            if ch:
                bl_ = 1
                for k in range(len(ch) - 1, -1, -1):
                    j = ch[k]
                    if i - j > WIN2: break
                    l = 0
                    while l < MAXL2 and i + l < n and raw[j + l] == raw[i + l]: l += 1
                    if l > bl_: bl_ = l; out.append((l, i - j - 1))
                    if l == MAXL2: break
                ch.append(i)
            else:
                heads[key] = [i]
        res.append(out)
    return res


def _pack2(raw: bytes) -> bytes:
    n = len(raw)
    cand = _matches(raw)
    P = [PONE // 2] * NPROB
    INF = 1 << 60
    for ps in range(2):
        Q = list(P) if ps else [PONE // 2] * NPROB                         # the prices of this pass (pass 0: every bit 1)
        def price(seq):
            c = 0
            for t in seq:
                if t[0] == "D": c += 16 * t[2]
                else: c += _PT[(Q[t[0]] if t[1] == 0 else PONE - Q[t[0]]) >> 4]
            return c
        def bp(i, b): return _PT[(Q[i] if b == 0 else PONE - Q[i]) >> 4]
        cost = [INF] * (n + 1); cost[0] = 0
        stt, rep, back = [0] * (n + 1), [0] * (n + 1), [None] * (n + 1)
        for i in range(n):
            c0 = cost[i]
            st, r0 = stt[i], rep[i]
            mb = raw[i - r0 - 1] if i - r0 - 1 >= 0 else 0
            pc = c0 + bp(ISM + st, 0) + price(_lit_bits(raw[i], st, mb))
            if pc < cost[i + 1]: cost[i + 1], stt[i + 1], rep[i + 1], back[i + 1] = pc, NEXT_LIT[st], r0, (i, 0, 1)
            if i > r0:
                lr, j = 0, i - r0 - 1
                while lr < MAXL2 and i + lr < n and raw[j + lr] == raw[i + lr]: lr += 1
                if lr:
                    base = c0 + bp(ISM + st, 1) + bp(ISR + st, 1)
                    pc = base + bp(ISR0L + st, 0)
                    if pc < cost[i + 1]: cost[i + 1], stt[i + 1], rep[i + 1], back[i + 1] = pc, (9 if st < 7 else 11), r0, (i, 1, 1)
                    b2 = base + bp(ISR0L + st, 1)
                    for l in range(2, lr + 1):
                        pc = b2 + price(_len_bits(RLEN, l))
                        if pc < cost[i + l]: cost[i + l], stt[i + l], rep[i + l], back[i + l] = pc, (8 if st < 7 else 11), r0, (i, 2, l)
            base = c0 + bp(ISM + st, 1) + bp(ISR + st, 0)
            prevl = 1
            for l, d in cand[i]:
                for ll in range(max(2, prevl + 1), l + 1):
                    pc = base + price(_len_bits(MLEN, ll)) + price(_dist_bits(ll, d))
                    if pc < cost[i + ll]: cost[i + ll], stt[i + ll], rep[i + ll], back[i + ll] = pc, (7 if st < 7 else 10), d, (i, 3, ll)
                prevl = l
        ops, i = [], n
        while i > 0:
            b_ = back[i]; ops.append((b_[0], b_[1], b_[2], rep[i])); i = b_[0]
        ops.reverse()
        E, P, st, r0 = _Enc(), [PONE // 2] * NPROB, 0, 0
        for i, k, l, d in ops:
            if k == 0:
                mb = raw[i - r0 - 1] if i - r0 - 1 >= 0 else 0
                E.bits(P, [(ISM + st, 0)] + _lit_bits(raw[i], st, mb)); st = NEXT_LIT[st]
            elif k == 1:
                E.bits(P, [(ISM + st, 1), (ISR + st, 1), (ISR0L + st, 0)]); st = 9 if st < 7 else 11
            elif k == 2:
                E.bits(P, [(ISM + st, 1), (ISR + st, 1), (ISR0L + st, 1)] + _len_bits(RLEN, l)); st = 8 if st < 7 else 11
            else:
                E.bits(P, [(ISM + st, 1), (ISR + st, 0)] + _len_bits(MLEN, l) + _dist_bits(l, d)); st = 7 if st < 7 else 10; r0 = d
        out = E.flush()
    return out


def unpack_stream2(data: bytes, size: int) -> bytes:
    """The decoder as the ARM one (bytes past the stream read as 0xFF)."""
    pos = [4]
    def nb():
        b_ = data[pos[0]] if pos[0] < len(data) else 0xFF; pos[0] += 1; return b_
    code, rng = int.from_bytes(data[:4], "big"), 0xFFFFFFFF
    P = [PONE // 2] * NPROB
    def bit(i):
        nonlocal code, rng
        p = P[i]; bound = (rng >> PBITS) * p
        if code < bound: rng = bound; P[i] = p + ((PONE - p) >> PMOVE); b_ = 0
        else: code -= bound; rng -= bound; P[i] = p - (p >> PMOVE); b_ = 1
        if rng < PTOP: rng = (rng << 8) & 0xFFFFFFFF; code = ((code << 8) | nb()) & 0xFFFFFFFF
        return b_
    def direct(n):
        nonlocal code, rng
        v = 0
        for _ in range(n):
            rng >>= 1; v <<= 1
            if code >= rng: code -= rng; v |= 1
            if rng < PTOP: rng = (rng << 8) & 0xFFFFFFFF; code = ((code << 8) | nb()) & 0xFFFFFFFF
        return v
    def tr(base, n):
        m, v = 1, 0
        for j in range(n):
            b_ = bit(base + m); m = m << 1 | b_; v |= b_ << j
        return v, m - (1 << n)
    def dlen(o):
        if not bit(o): return 2 + tr(o + 2, 3)[1]
        if not bit(o + 1): return 10 + tr(o + 10, 3)[1]
        return 18 + tr(o + 18, 8)[1]
    out, st, r0 = bytearray(), 0, 0
    while len(out) < size:
        if not bit(ISM + st):
            offs, m, sym = (0x100, out[-r0 - 1], 1) if st >= 7 else (0, 0, 1)
            while sym < 0x100:
                m <<= 1; b0 = m & offs
                b_ = bit(LIT + offs + b0 + sym); sym = sym << 1 | b_
                offs = offs & b0 if b_ else offs & ~b0
            out.append(sym & 0xFF); st = NEXT_LIT[st]; continue
        if bit(ISR + st):
            if not bit(ISR0L + st): l, st = 1, (9 if st < 7 else 11)
            else: l, st = dlen(RLEN), (8 if st < 7 else 11)
        else:
            l = dlen(MLEN); st = 7 if st < 7 else 10
            sl = tr(SLOT + 64 * min(l - 2, 3), 6)[1]
            if sl < 4: r0 = sl
            else:
                nd = (sl >> 1) - 1; d = (2 | (sl & 1)) << nd
                if sl < 14: d += tr(SPEC + d - sl - 1, nd)[0]
                else: d += direct(nd - 4) << 4; d += tr(ALIGN, 4)[0]
                r0 = d
        for _ in range(l): out.append(out[-r0 - 1])
    return bytes(out[:size])


def arm_code2(base):
    """c_dspz for 'DZ2' blocks: the same sender loop; dz_fill = the range decoder (r4 range, r5 code, r6 src, r7 = S while it runs)."""
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def rev(rd, rm): E(raw, h(0xBA00 | rm << 3 | rd))
    def ring(rd): E(movs_imm, rd, RING2 >> 8); E(lsls_imm, rd, rd, 8)
    a.label("c_dspz")
    E(ldr_imm, 2, 0, 0); imm32(3, struct.unpack("<I", MAGIC2)[0]); E(cmp_reg, 2, 3); E(b_cond, "dz_go", "eq")
    E(b_w, SEND)
    a.label("dz_go")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 1)                                                    # r4 = core
    E(movs_imm, 2, PROBS >> 8); E(lsls_imm, 2, 2, 8); E(movw, 3, NPROB); E(movs_imm, 1, 1); E(lsls_imm, 1, 1, 10)
    a.label("dz_ip")
    E(strh_imm, 1, 2, 0); E(adds_imm8, 2, 2); E(subs_imm8, 3, 1); E(b_cond, "dz_ip", "ne")   # every probability 1/2
    imm32(3, S)
    E(ldr_imm, 1, 0, 12); rev(1, 1); E(str_imm, 1, 3, 8)                # code = the stream's first four bytes, big-endian
    E(mov_reg, 2, 0); E(adds_imm8, 2, 16); E(str_imm, 2, 3, 0)          # src
    E(movs_imm, 2, 0); E(str_imm, 2, 3, 12); E(str_imm, 2, 3, 16); E(str_imm, 2, 3, 20); E(str_imm, 2, 3, 24)   # st, rep0, left, write index
    E(subs_imm8, 2, 1); E(str_imm, 2, 3, 4)                             # range
    E(ldr_imm, 6, 0, 4)                                                 # r6 = words of the block
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
    E(mov_reg, 0, 4); E(pop_list, [4, 5, 6, 7]); E(pop_list, [3])
    E(mov_reg, 14, 3); E(b_w, END)
    # ---- dz_fill(dst, bytes): [sp] dst, [sp + 4] end; S: + 0 src, + 4 range, + 8 code, + 12 state, + 16 rep0, + 20 left, + 24 write index
    a.label("dz_fill")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(adds_reg, 1, 0, 1); E(push_list, [0, 1])
    imm32(7, S); E(ldr_imm, 6, 7, 0); E(ldr_imm, 4, 7, 4); E(ldr_imm, 5, 7, 8)
    a.label("df_lp")
    E(ldr_sp, 0, 0); E(ldr_sp, 1, 4); E(cmp_reg, 0, 1); E(b_cond, "df_x", "hs")
    E(ldr_imm, 0, 7, 20); E(cmp_imm, 0, 0); E(b_cond, "df_cp", "ne")
    E(bl, "dz_sym")
    E(lsrs_imm, 1, 0, 8); E(b_cond, "df_put", "eq")                     # a literal: r0 = the byte
    a.label("df_cp")
    E(ldr_imm, 1, 7, 20); E(subs_imm8, 1, 1); E(str_imm, 1, 7, 20)      # left - 1
    E(ldr_imm, 1, 7, 24); E(ldr_imm, 2, 7, 16); E(subs_reg, 1, 1, 2); E(subs_imm8, 1, 1); E(lsls_imm, 1, 1, 20); E(lsrs_imm, 1, 1, 20)
    ring(2); E(ldrb_reg, 0, 2, 1)
    a.label("df_put")
    E(ldr_imm, 1, 7, 24); ring(2); E(strb_reg, 0, 2, 1); E(adds_imm8, 1, 1); E(lsls_imm, 1, 1, 20); E(lsrs_imm, 1, 1, 20); E(str_imm, 1, 7, 24)
    E(ldr_sp, 1, 0); E(strb_imm, 0, 1, 0); E(adds_imm8, 1, 1); E(str_sp, 1, 0)
    E(b, "df_lp")
    a.label("df_x")
    E(str_imm, 6, 7, 0); E(str_imm, 4, 7, 4); E(str_imm, 5, 7, 8)
    E(add_sp_imm, 8); E(pop_list, [4, 5, 6, 7], pc=True)
    # ---- dz_rb(r0 = byte offset of the probability) -> r0 = the bit; r1-r3 used
    a.label("dz_rb")
    E(movs_imm, 3, PROBS >> 8); E(lsls_imm, 3, 3, 8); E(adds_reg, 3, 3, 0)
    E(ldrh_imm, 1, 3, 0); E(lsrs_imm, 2, 4, PBITS); E(muls, 2, 1)       # bound = (range >> 11) * p
    E(cmp_reg, 5, 2); E(b_cond, "rb_1", "hs")
    E(mov_reg, 4, 2)
    E(movs_imm, 2, 1); E(lsls_imm, 2, 2, PBITS); E(subs_reg, 2, 2, 1); E(lsrs_imm, 2, 2, PMOVE); E(adds_reg, 1, 1, 2); E(strh_imm, 1, 3, 0)
    E(movs_imm, 0, 0); E(b, "rb_n")
    a.label("rb_1")
    E(subs_reg, 5, 5, 2); E(subs_reg, 4, 4, 2)
    E(lsrs_imm, 2, 1, PMOVE); E(subs_reg, 1, 1, 2); E(strh_imm, 1, 3, 0)
    E(movs_imm, 0, 1)
    a.label("rb_n")
    E(lsrs_imm, 2, 4, 24); E(b_cond, "rb_x", "ne")
    E(lsls_imm, 4, 4, 8); E(lsls_imm, 5, 5, 8); E(ldrb_imm, 2, 6, 0); E(adds_imm8, 6, 1); E(orrs_reg, 5, 2)
    a.label("rb_x")
    E(bx_lr)
    # ---- dz_tr(r0 = byte offset of the tree, r1 = bits) -> r0 = the value read LSB first, r1 = MSB first; r7 kept
    a.label("dz_tr")
    E(movs_imm, 2, 0); E(movs_imm, 3, 1); E(push_list, [0, 1, 2, 3, 7], lr=True); E(movs_imm, 7, 1)
    a.label("tr_l")
    E(ldr_sp, 0, 0); E(adds_reg, 0, 0, 7); E(adds_reg, 0, 0, 7); E(bl, "dz_rb")
    E(lsls_imm, 7, 7, 1); E(orrs_reg, 7, 0)
    E(ldr_sp, 3, 12); E(cmp_imm, 0, 0); E(b_cond, "tr_z", "eq")
    E(ldr_sp, 2, 8); E(orrs_reg, 2, 3); E(str_sp, 2, 8)
    a.label("tr_z")
    E(lsls_imm, 3, 3, 1); E(str_sp, 3, 12)
    E(ldr_sp, 1, 4); E(subs_imm8, 1, 1); E(str_sp, 1, 4); E(b_cond, "tr_l", "ne")
    E(subs_reg, 1, 7, 3); E(ldr_sp, 0, 8)
    E(add_sp_imm, 16); E(pop_list, [7], pc=True)
    # ---- dz_len(r0 = byte offset of the length coder) -> r0 = length
    a.label("dz_len")
    E(push_list, [7], lr=True); E(mov_reg, 7, 0); E(bl, "dz_rb"); E(cmp_imm, 0, 0); E(b_cond, "dl_1", "ne")
    E(adds_imm3, 0, 7, 4); E(movs_imm, 7, 2); E(movs_imm, 1, 3); E(b, "dl_t")
    a.label("dl_1")
    E(adds_imm3, 0, 7, 2); E(bl, "dz_rb"); E(cmp_imm, 0, 0); E(b_cond, "dl_2", "ne")
    E(mov_reg, 0, 7); E(adds_imm8, 0, 20); E(movs_imm, 7, 10); E(movs_imm, 1, 3); E(b, "dl_t")
    a.label("dl_2")
    E(mov_reg, 0, 7); E(adds_imm8, 0, 36); E(movs_imm, 7, 18); E(movs_imm, 1, 8)
    a.label("dl_t")
    E(bl, "dz_tr"); E(adds_reg, 0, 1, 7); E(pop_list, [7], pc=True)
    # ---- dz_sym: one item -> r0 = a literal byte, or 0x100 with left / rep0 set; the state updated
    a.label("dz_sym")
    E(push_list, [], lr=True)
    E(ldr_imm, 0, 7, 12); E(lsls_imm, 0, 0, 1); E(movw, 1, 2 * ISM); E(adds_reg, 0, 0, 1); E(bl, "dz_rb")
    E(cmp_imm, 0, 0); E(b_cond, "sy_m", "ne")
    E(ldr_imm, 1, 7, 12); E(movs_imm, 2, 0); E(movs_imm, 3, 0)          # m = 0, offs = 0
    E(cmp_imm, 1, 7); E(b_cond, "sy_l", "lo")
    E(ldr_imm, 0, 7, 24); E(ldr_imm, 2, 7, 16); E(subs_reg, 0, 0, 2); E(subs_imm8, 0, 1); E(lsls_imm, 0, 0, 20); E(lsrs_imm, 0, 0, 20)
    ring(2); E(ldrb_reg, 2, 2, 0)                                       # m = the match byte
    E(movs_imm, 3, 1); E(lsls_imm, 3, 3, 8)                             # offs = 0x100
    a.label("sy_l")
    E(movs_imm, 0, 1); E(push_list, [0, 1, 2, 3])                       # [sp] sym, [sp + 4] bit, [sp + 8] m, [sp + 12] offs
    a.label("sy_ll")
    E(ldr_sp, 1, 8); E(lsls_imm, 1, 1, 1); E(str_sp, 1, 8)
    E(ldr_sp, 2, 12); E(ands_reg, 1, 2); E(str_sp, 1, 4)
    E(adds_reg, 0, 2, 1); E(ldr_sp, 3, 0); E(adds_reg, 0, 0, 3); E(lsls_imm, 0, 0, 1)
    E(bl, "dz_rb")
    E(ldr_sp, 3, 0); E(lsls_imm, 3, 3, 1); E(orrs_reg, 3, 0); E(str_sp, 3, 0)
    E(ldr_sp, 1, 4); E(ldr_sp, 2, 12)
    E(cmp_imm, 0, 0); E(b_cond, "sy_0", "eq")
    E(ands_reg, 2, 1); E(b, "sy_1")
    a.label("sy_0")
    E(bics_reg, 2, 1)
    a.label("sy_1")
    E(str_sp, 2, 12)
    E(lsrs_imm, 3, 3, 8); E(b_cond, "sy_ll", "eq")
    E(ldr_sp, 0, 0); E(lsls_imm, 0, 0, 24); E(lsrs_imm, 0, 0, 24)
    E(add_sp_imm, 16)
    E(ldr_imm, 1, 7, 12); E(cmp_imm, 1, 4); E(b_cond, "sy_s0", "lo")
    E(subs_imm8, 1, 3); E(cmp_imm, 1, 7); E(b_cond, "sy_s1", "lo"); E(subs_imm8, 1, 3); E(b, "sy_s1")
    a.label("sy_s0")
    E(movs_imm, 1, 0)
    a.label("sy_s1")
    E(str_imm, 1, 7, 12)
    E(pop_list, [], pc=True)
    a.label("sy_m")
    E(ldr_imm, 0, 7, 12); E(lsls_imm, 0, 0, 1); E(movw, 1, 2 * ISR); E(adds_reg, 0, 0, 1); E(bl, "dz_rb")
    E(cmp_imm, 0, 0); E(b_cond, "sy_n", "eq")
    E(ldr_imm, 0, 7, 12); E(lsls_imm, 0, 0, 1); E(movw, 1, 2 * ISR0L); E(adds_reg, 0, 0, 1); E(bl, "dz_rb")
    E(cmp_imm, 0, 0); E(b_cond, "sy_r", "ne")
    E(movs_imm, 0, 1); E(movs_imm, 1, 9); E(b, "sy_st")                 # short rep: one byte at rep0
    a.label("sy_r")
    E(movw, 0, 2 * RLEN); E(bl, "dz_len"); E(movs_imm, 1, 8); E(b, "sy_st")
    a.label("sy_n")
    E(movw, 0, 2 * MLEN); E(bl, "dz_len"); E(str_imm, 0, 7, 20)
    E(subs_imm8, 0, 2); E(cmp_imm, 0, 3); E(b_cond, "sy_k", "ls"); E(movs_imm, 0, 3)
    a.label("sy_k")
    E(lsls_imm, 0, 0, 7); E(movw, 1, 2 * SLOT); E(adds_reg, 0, 0, 1); E(movs_imm, 1, 6); E(bl, "dz_tr")   # r1 = the slot
    E(cmp_imm, 1, 4); E(b_cond, "sy_d", "lo")
    E(lsrs_imm, 2, 1, 1); E(subs_imm8, 2, 1)                            # r2 = bits
    E(movs_imm, 3, 1); E(ands_reg, 3, 1); E(adds_imm8, 3, 2); E(lsls_reg, 3, 2)   # r3 = base
    E(push_list, [3])
    E(cmp_imm, 1, 14); E(b_cond, "sy_dd", "hs")
    E(subs_reg, 0, 3, 1); E(subs_imm8, 0, 1); E(lsls_imm, 0, 0, 1); E(movw, 3, 2 * SPEC); E(adds_reg, 0, 0, 3); E(mov_reg, 1, 2)
    E(bl, "dz_tr"); E(b, "sy_da")
    a.label("sy_dd")
    E(subs_imm3, 1, 2, 4); E(bl, "dz_dir"); E(lsls_imm, 0, 0, 4)
    E(ldr_sp, 3, 0); E(adds_reg, 3, 3, 0); E(str_sp, 3, 0)
    E(movw, 0, 2 * ALIGN); E(movs_imm, 1, 4); E(bl, "dz_tr")
    a.label("sy_da")
    E(pop_list, [3]); E(adds_reg, 1, 0, 3)
    a.label("sy_d")
    E(str_imm, 1, 7, 16)                                                # rep0
    E(ldr_imm, 0, 7, 20); E(movs_imm, 1, 7)
    a.label("sy_st")                                                    # r0 = length, r1 = the next state after a state < 7
    E(str_imm, 0, 7, 20)
    E(ldr_imm, 2, 7, 12); E(cmp_imm, 2, 7); E(b_cond, "st_a", "hs")
    E(mov_reg, 2, 1); E(b, "st_b")
    a.label("st_a")
    E(movs_imm, 2, 11); E(cmp_imm, 1, 7); E(b_cond, "st_b", "ne"); E(movs_imm, 2, 10)
    a.label("st_b")
    E(str_imm, 2, 7, 12)
    E(movs_imm, 0, 1); E(lsls_imm, 0, 0, 8)
    E(pop_list, [], pc=True)
    # ---- dz_dir(r1 = bits) -> r0: the range coder's direct bits
    a.label("dz_dir")
    E(movs_imm, 0, 0)
    a.label("dr_l")
    E(lsrs_imm, 4, 4, 1); E(lsls_imm, 0, 0, 1); E(cmp_reg, 5, 4); E(b_cond, "dr_n", "lo"); E(subs_reg, 5, 5, 4); E(adds_imm8, 0, 1)
    a.label("dr_n")
    E(lsrs_imm, 2, 4, 24); E(b_cond, "dr_c", "ne")
    E(lsls_imm, 4, 4, 8); E(lsls_imm, 5, 5, 8); E(ldrb_imm, 2, 6, 0); E(adds_imm8, 6, 1); E(orrs_reg, 5, 2)
    a.label("dr_c")
    E(subs_imm8, 1, 1); E(b_cond, "dr_l", "ne")
    E(bx_lr)
    return a.assemble()
