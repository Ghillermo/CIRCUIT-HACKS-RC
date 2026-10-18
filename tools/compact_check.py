"""Check thumb.COMPACT (literal pools) on a builder: build it twice, normal and compacted, recording every Asm block, then
compare the two images.   python tools/compact_check.py build_sc44_2.py  [-o build/compact_check]
1. each Asm block's own output, item by item: an LDR that replaced a movw + movt loads the same constant (own addresses
   mapped to where they moved), every branch reaches the mapped target, everything else byte-identical;
2. the image: every difference from the blocks' outputs (later patches over our code) and every difference outside the
   blocks (stock code, hooks, vtables, tables, DSP program) is the same patch / word with own addresses mapped.
The normal build is the builder with COMPACT forced off, the compacted one with it forced on, whatever the builder sets; the normal one runs with
python -O and no flash limit (a build that only fits compacted still gets its reference; it is only compared, never flashed)."""
import bisect
import pickle
import runpy
import struct
import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
STOCK = ROOT / "stock/circuittracks-firmware-4486-STOCK.bin"
BASE = 0x08010000
SIZE4 = {"bl", "cmp_w_imm", "b_w", "movw", "movt", "ldrb_w", "strb_w", "strh_w_imm", "strh_w_reg_lsl1"}
BR = ("b_cond", "b", "bl", "cbz", "b_w")


def record(script, out, compact):
    """(child) run the builder with COMPACT forced; trace.pkl = every Asm block: base, items, output, compacted layout"""
    sys.path.insert(0, str(TOOLS))
    import thumb
    tr, orig = [], thumb.Asm.assemble
    nm = lambda fn: getattr(fn, "__name__", str(fn))

    def wrapped(self, external=None):
        thumb.COMPACT, thumb.LAST = compact, None
        code, labels = orig(self, external)
        rec = dict(base=self.base, n=len(code), code=bytes(code),
                   items=[(k, p if k == "label" else (nm(p[0]), p[1], p[2])) for k, p in self.items])
        if compact:
            seq, addrs, pools, pair, lsz = thumb.LAST
            rec.update(seq=[(e[0], e[1] if e[0] == "label" else nm(e[1]) if e[0] == "ins" else e[1:] if e[0] == "lit" else None) for e in seq],
                       addrs=[addrs[k] for k in range(len(seq))], pools=pools, pair=sorted(pair), lsz=lsz)
        tr.append(rec)
        return code, labels

    thumb.Asm.assemble = wrapped
    if not compact:                                                         # the reference may not fit: it is never flashed (run with -O: no size asserts)
        import ct_fw
        ct_fw.MAX_IMAGE_SIZE = 1 << 20
    sys.argv = [str(TOOLS / script), str(STOCK), "-o", str(out)]
    runpy.run_path(str(TOOLS / script), run_name="__main__")
    Path(out, "trace.pkl").write_bytes(pickle.dumps(tr))
    print("STATS", thumb.STATS)


def size(fn, args):
    return len(args[0]) if fn == "raw" else 4 if fn in SIZE4 else 2


def sext(v, bits):
    return v - (1 << bits) if v & (1 << (bits - 1)) else v


def wide(v):
    return v >> 11 in (0b11101, 0b11110, 0b11111)


class Mem:
    def __init__(self, data, base): self.d, self.b = data, base
    def hw(self, a): return struct.unpack_from("<H", self.d, a - self.b)[0]
    def wd(self, a): return struct.unpack_from("<I", self.d, a - self.b)[0]
    def ok(self, a, n=2): return 0 <= a - self.b and a - self.b + n <= len(self.d)


def branch(m, a):
    """(kind, target, size) of a PC-relative branch at a, or None"""
    if not m.ok(a): return None
    v = m.hw(a)
    if v & 0xF800 == 0xF000 and m.ok(a, 4):
        v2 = m.hw(a + 2)
        if v2 & 0xD000 in (0x9000, 0xD000):
            s = (v >> 10) & 1; i1 = ~((v2 >> 13) & 1 ^ s) & 1; i2 = ~((v2 >> 11) & 1 ^ s) & 1
            off = sext(s << 24 | i1 << 23 | i2 << 22 | (v & 0x3FF) << 12 | (v2 & 0x7FF) << 1, 25)
            return ("bl" if v2 & 0xD000 == 0xD000 else "b.w", a + 4 + off, 4)
        if v2 & 0xD000 == 0x8000 and (v >> 6) & 0xF < 14:            # B<c>.W T3
            s = (v >> 10) & 1
            off = sext(s << 20 | (v2 >> 11 & 1) << 19 | (v2 >> 13 & 1) << 18 | (v & 0x3F) << 12 | (v2 & 0x7FF) << 1, 21)
            return (f"b{(v >> 6) & 0xF}.w", a + 4 + off, 4)
    if v & 0xF800 == 0xE000:
        return ("b", a + 4 + sext((v & 0x7FF) << 1, 12), 2)
    if v & 0xF000 == 0xD000 and (v >> 8) & 0xF < 14:
        return (f"b{(v >> 8) & 0xF}", a + 4 + sext((v & 0xFF) << 1, 9), 2)
    if v & 0xF500 == 0xB100:
        return ("cbz" if not v & 0x800 else "cbnz", a + 4 + ((v >> 9 & 1) << 6 | (v >> 3 & 0x1F) << 1), 2)
    return None


def mov32(m, a):
    v1, v2, v3, v4 = m.hw(a), m.hw(a + 2), m.hw(a + 4), m.hw(a + 6)
    assert v1 & 0xFBF0 == 0xF240 and v3 & 0xFBF0 == 0xF2C0, hex(a)
    imm = lambda x, y: (x & 0xF) << 12 | (x >> 10 & 1) << 11 | (y >> 12 & 7) << 8 | y & 0xFF
    assert (v2 >> 8 & 0xF) == (v4 >> 8 & 0xF)
    return v2 >> 8 & 0xF, imm(v1, v2) | imm(v3, v4) << 16


def ldrlit(m, a):
    v = m.hw(a)
    if v & 0xF800 == 0x4800:
        return v >> 8 & 7, m.wd(((a + 4) & ~3) + (v & 0xFF) * 4)
    v2 = m.hw(a + 2)
    assert v in (0xF85F, 0xF8DF), hex(a)
    off = v2 & 0xFFF
    return v2 >> 12, m.wd(((a + 4) & ~3) + (off if v & 0x80 else -off))


def check(old_dir, new_dir):
    OI = next(old_dir.glob("*.bin")).read_bytes()
    NI = next(new_dir.glob("*.bin")).read_bytes()
    OT = pickle.loads((old_dir / "trace.pkl").read_bytes())
    NT = pickle.loads((new_dir / "trace.pkl").read_bytes())
    STOCK_END = BASE + len(STOCK.read_bytes())
    assert len(OT) == len(NT)
    # ---- the address map: items and labels of every block, old -> new
    M, LITS, blocks, work = {}, {}, [], []
    for bo, bn in zip(OT, NT):
        items, seq, addrs, oitems = bn["items"], bn["seq"], bn["addrs"], bo["items"]
        assert len(items) == len(oitems)
        for (k1, p1), (k2, p2) in zip(oitems, items):
            assert k1 == k2 and (p1 == p2 if k1 == "label" else p1[0] == p2[0]), (p1, p2)
        oa, j, i, w = bo["base"], 0, 0, []
        while i < len(oitems):
            while seq[j][0] == "site": j += 1
            k, p = oitems[i]
            if k == "label":
                assert seq[j] == ("label", p); M.setdefault(oa, addrs[j]); i += 1; j += 1; continue
            fn, args, kw = p
            if seq[j][0] == "lit":
                assert fn == "movw" and oitems[i + 1][1][0] == "movt"
                M.setdefault(oa, addrs[j]); LITS[oa] = addrs[j]; w.append(("lit", oa, addrs[j], 8, fn, args)); oa += 8; i += 2; j += 1; continue
            assert seq[j] == ("ins", fn), (seq[j], fn)
            s = size(fn, args)
            M.setdefault(oa, addrs[j]); w.append(("ins", oa, addrs[j], s, fn, args)); oa += s; i += 1; j += 1
        while j < len(seq) and seq[j][0] == "site": j += 1
        assert j == len(seq) and oa == bo["base"] + bo["n"]
        blocks.append((bo["base"], oa, bn["base"], bn["base"] + bn["n"], bo["code"], bn["code"]))
        work.append(w)
    blocks.sort()
    KEYS = sorted(M)
    STARTS = [b[0] for b in blocks]

    def block_of(a):
        i = bisect.bisect_right(STARTS, a) - 1
        return blocks[i] if i >= 0 and a < blocks[i][1] else None

    def gap_cands(a):
        """outside every block: shifted like the block after it (data placed just before code) or like the one before"""
        i = bisect.bisect_right(STARTS, a)
        c = []
        if i < len(blocks): c.append(a - blocks[i][0] + blocks[i][2])
        if i: c.append(a - blocks[i - 1][1] + blocks[i - 1][3])
        return c

    def mapa(a):
        if a < STOCK_END:
            return a
        if block_of(a):
            k = KEYS[bisect.bisect_right(KEYS, a) - 1]
            return M[k] + (a - k) if k not in LITS or a == k else None
        c = gap_cands(a)
        return c[0] if c else a

    def mapv(v):
        if STOCK_END <= v < BASE + max(len(OI), 0x70000) and v != BASE + 0x70000:      # (0x08080000: the end of the flash, a bound, not an address)
            m = mapa(v & ~1)
            return None if m is None else m | (v & 1)
        return v

    bad, n_lit, n_br, n_eq = [], 0, 0, 0
    # ---- 1. the blocks' own outputs
    for w, bo, bn in zip(work, OT, NT):
        om, nm = Mem(bo["code"], bo["base"]), Mem(bn["code"], bn["base"])
        for kind, oa, na, so, fn, args in w:
            if kind == "lit":
                rd, vo = mov32(om, oa); rn, vn = ldrlit(nm, na); n_lit += 1
                if rd != rn or mapv(vo) != vn:
                    bad.append(f"lit {hex(oa)}->{hex(na)}: r{rd} {hex(vo)} (map {mapv(vo) and hex(mapv(vo))}) vs r{rn} {hex(vn)}")
                continue
            ob, nb = bo["code"][oa - bo["base"]:oa - bo["base"] + so], bn["code"][na - bn["base"]:na - bn["base"] + so]
            if fn in BR:
                x, y = branch(om, oa), branch(nm, na)
                if x and y and x[0] == y[0] and mapa(x[1]) == y[1]: n_br += 1
                else: bad.append(f"{fn} {hex(oa)}->{hex(na)}: {x} vs {y}")
                continue
            if ob == nb or (so % 4 == 0 and all(mapv(struct.unpack_from("<I", ob, q)[0]) == struct.unpack_from("<I", nb, q)[0] for q in range(0, so, 4))):
                n_eq += 1; continue
            bad.append(f"{fn} {hex(oa)}->{hex(na)}: {ob.hex()} vs {nb.hex()}")

    # ---- 2. the images: later patches over our code, and everything outside the blocks
    OM, NM = Mem(OI, BASE), Mem(NI, BASE)
    opatch, npatch = bytearray(len(OI)), bytearray(len(NI))
    for b in blocks:
        for q in range(b[1] - b[0]):
            if OI[b[0] - BASE + q] != b[4][q]: opatch[b[0] - BASE + q] = 1
        for q in range(b[3] - b[2]):
            if NI[b[2] - BASE + q] != b[5][q]: npatch[b[2] - BASE + q] = 1

    def same_at(a, na):
        """the instruction / word at old a against the new one at na: the size consumed, or 0"""
        if na is None: return 0
        x, y = branch(OM, a), branch(NM, na)
        if x and y and x[0] == y[0] and mapa(x[1]) == y[1]:
            return x[2]
        if OM.ok(a, 4) and NM.ok(na, 4) and a % 4 == 0 and mapv(OM.wd(a)) == NM.wd(na) and OM.wd(a) != NM.wd(na):
            return 4
        if OM.ok(a) and NM.ok(na) and OM.hw(a) == NM.hw(na) and not x:
            return 4 if wide(OM.hw(a)) and OM.ok(a, 4) and OM.wd(a) == NM.wd(na) else 2
        return 0

    n_patch = n_out = 0
    seen_new = set()
    a, END = BASE, BASE + len(OI)
    while a < END:
        if block_of(a):
            if not opatch[a - BASE]:
                a += 1; continue
            k = KEYS[bisect.bisect_right(KEYS, a) - 1]
            if k in LITS:
                bad.append(f"patch inside a compacted pair at {hex(a)}"); a += 1; continue
            s = k
            while s + 2 <= a: s += 2
            na = mapa(s)
            n = same_at(s, na) or same_at(s - 2, mapa(s - 2))
            if not n:
                bad.append(f"patch {hex(s)}->{hex(na)}: {OI[s - BASE:s - BASE + 4].hex()} vs {NI[na - BASE:na - BASE + 4].hex()}"); a = s + 2; continue
            for q in range(n): seen_new.add(na + q)
            n_patch += 1; a = s + n; continue
        if a < STOCK_END:
            na = a
        else:
            c = gap_cands(a); na = c[0]
            for cand in c:
                if NM.ok(cand) and OI[a - BASE:a - BASE + 2] == NI[cand - BASE:cand - BASE + 2]: na = cand; break
        if a % 2:
            a += 1; continue
        if a >= STOCK_END and OI[a - BASE:a - BASE + 2] == b"\xff\xff" and any(0 < blk[0] - a <= 2 or 0 <= a - blk[1] < 2 for blk in blocks):
            a += 2; continue                                          # alignment padding before / after a block
        try:
            ro, vo = mov32(OM, a); rn, vn = mov32(NM, na)
            if ro == rn and mapv(vo) == vn and vo != vn:
                n_out += 1; a += 8; continue                          # an own address patched into stock code
        except (AssertionError, struct.error):
            pass
        if NM.ok(na) and OM.hw(a) == NM.hw(na) and not (a + 4 <= END and wide(OM.hw(a)) and OM.wd(a) != NM.wd(na)):
            a += 2; continue
        n = same_at(a, na) or (a % 4 == 2 and same_at(a - 2, na - 2) and 2)
        if n:
            n_out += 1; a += n; continue
        bad.append(f"outside {hex(a)}->{hex(na)}: {OI[a - BASE:a - BASE + 4].hex()} vs {NI[na - BASE:na - BASE + 4].hex() if NM.ok(na, 4) else '-'}")
        a += 2
    extra = [q + BASE for q in range(len(NI)) if npatch[q] and q + BASE not in seen_new]
    if extra:
        bad.append(f"new image patched where the old is not: {len(extra)} bytes, first {[hex(x) for x in extra[:8]]}")
    print(f"blocks {len(blocks)}: loads {n_lit}, branches {n_br}, identical items {n_eq}; later patches {n_patch}; mapped outside {n_out}")
    print(f"normal image {hex(len(OI))}, compacted {hex(len(NI))}: {len(OI) - len(NI)} B saved, {0x70000 - len(NI)} B free")
    print(f"MISMATCHES {len(bad)}")
    for x in bad[:60]:
        print(" ", x)
    return not bad


if __name__ == "__main__":
    if sys.argv[1] == "--record":
        record(sys.argv[2], sys.argv[3], sys.argv[4] == "1")
        sys.exit(0)
    script = sys.argv[1]
    base = Path(sys.argv[sys.argv.index("-o") + 1]) if "-o" in sys.argv else ROOT / "build/compact_check"
    out = base / Path(script).stem
    for d, c in (("normal", "0"), ("compact", "1")):
        r = subprocess.run([sys.executable, *(["-O"] if c == "0" else []), __file__, "--record", script, str(out / d), c], capture_output=True, text=True)
        if r.returncode:
            print(r.stdout[-2000:] + r.stderr[-3000:]); sys.exit(1)
        print(d, r.stdout.strip().splitlines()[-1])
    ok = check(out / "normal", out / "compact")
    print("COMPACT CHECK:", "OK" if ok else "FAIL")
    sys.exit(0 if ok else 1)
