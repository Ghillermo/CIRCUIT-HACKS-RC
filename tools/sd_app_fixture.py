"""The test card of tools/sd_app_test.html: two packs made of real files of a card copy, and the same operations the test does, done here by another
implementation (tools/patchtool.py for the banks, plain bytes for the rest).  The test compares its result file by file with expected.json.

    python tools/sd_app_fixture.py [C:/path/to/Tracks]       -> build/sdapp_fixture/ (served by the repo-http preview, .claude/launch.json),
                                                                with dx7.json (tools/dx7ref.py) for sd_app_test.html?dx7=1
    python tools/sd_app_fixture.py --full                    + the whole copy there, for sd_app_test.html?full=1
"""
from __future__ import annotations
import hashlib, json, re, shutil, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import patchtool as pt  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "sdapp_fixture"
SRC = next((Path(a) for a in sys.argv[1:] if not a.startswith("--")), Path.home() / "Desktop" / "Tracks")
ALPHA, BETA = "00_Alpha", "03_Beta Pack Long Name 1234567"
MIDI0, PAT, SETT, LANE0 = 0x1A27C, 0xCA8, 0x380, 0x3A8
REC, PSZ, PADN = 512, 340, 172


def rd(f): return Path(f).read_bytes()


def session_with_notes():
    """the session of the copy with most notes on MIDI 1 / 2"""
    best, top = None, -1
    for f in sorted(SRC.glob("*/Sessions/*.ncs")):
        d = rd(f)
        if len(d) != 0x2740C or "Shadow" in f.parts[-3]: continue
        n = sum(bin(d[MIDI0 + PAT * p + 28 * s]).count("1") for p in range(16) for s in range(32))
        if n > top: best, top = f, n
    return best


def make_pack(base: Path, name, src: Path, banks, samples, sessions):
    p = base / name
    for sub in ("Patches", "PCM", "Sessions", "meta"): (p / sub).mkdir(parents=True)
    for b in banks: shutil.copy(src / "Patches" / f"{b:02d}_PATCHBANK.cpb", p / "Patches")
    for f in sorted((src / "PCM").glob("*.wav"))[:samples]: shutil.copy(f, p / "PCM")
    for f, new in sessions: shutil.copy(f, p / "Sessions" / new)
    for f in (src / "meta").glob("*"): shutil.copy(f, p / "meta")
    return p


def pad_of(name, vals, extra=True):
    """a whole padding as a late build leaves it: patchtool's patch + a matrix block, an FM block, a voice mode"""
    b = bytearray(pt.make(3, 0, vals, name))
    if extra:
        b[64:88] = b"MX\x01" + bytes(range(21))
        fm = bytearray(b"FM\x02\x01" + bytes(range(100, 116))); fm.append((0x5A + sum(fm)) & 0xFF)
        b[100:121] = fm
        b[126:130] = bytes([0xB6, 0x53, 10, 20])
    return bytes(b)


def projsyn_put(b, t, pad):
    """tools/projsyn.py's 5 blocks of MIDI 1 / 2 (t = 0 / 1): 0xC6, t << 4 | k, 30 bytes of the padding's first 124 + their 16-bit sum"""
    img = bytearray(pad[:124]); sm = (0x5AC6 + sum(img)) & 0xFFFF; img += bytes([sm & 0xFF, sm >> 8]) + b"\0" * 24
    for k in range(5):
        o = MIDI0 + PAT * (8 * t + k) + SETT + 8
        b[o:o + 32] = bytes([0xC6, t << 4 | k]) + img[30 * k:30 * k + 30]


def usage(p: Path):
    """what the projects of pack p use, as sd_app.html's usageOf should find it: sorted "kind slot session track flip" strings"""
    out = set()
    pads = {}
    for n in range(128):
        f = pt.bank_file(p, n // 8)
        if f:
            r = rd(f)[REC * (n % 8) + PSZ:REC * (n % 8) + REC]
            if len(r) >= 42 and r[:4] == b"CTM1" and sum(r[4:40]) & 0xFF == r[40]: pads[n] = r
    def fm(b):
        if b[100:102] != b"FM" or (0x5A + sum(b[100:120])) & 0xFF != b[120]: return None
        return b[103], bytes(b[104:120])
    for f in sorted((p / "Sessions").glob("*.ncs")):
        b = rd(f); ss = int(f.name[:2])
        if len(b) != 0x2740C or b[:4] != b"USER": continue
        for t in range(2):
            if b[0xCD64 + 8 * t] < 128: out.add(f"nova {b[0xCD64 + 8 * t]} {ss} {t} 0")
        for d in range(4):
            if b[0x26FBC + 11 * d] < 64: out.add(f"drums {b[0x26FBC + 11 * d]} {ss} {4 + d} 0")
            for q in range(8):
                for st in range(32):
                    v = b[0xCD74 + 0x6A8 * (8 * d + q) + 64 + st]
                    if v < 64: out.add(f"drums {v} {ss} {4 + d} 1")
        for t in range(2):
            blk = [b[MIDI0 + PAT * (8 * t + k) + SETT + 8:MIDI0 + PAT * (8 * t + k) + SETT + 40] for k in range(5)]
            if all(x[0] == 0xC6 and x[1] == (t << 4 | k) for k, x in enumerate(blk)):
                img = b"".join(x[2:] for x in blk)
                if (0x5AC6 + sum(img[:124])) & 0xFFFF == img[124] | img[125] << 8 and img[:4] == b"CTM1":
                    if img[4] & 15 in (9, 11) and img[30] < 64: out.add(f"drums {img[30]} {ss} {2 + t} 0")
                    for n, r in pads.items():
                        a, c = fm(r), fm(img)
                        if r[4:40] == img[4:40] and (not a or not c or a == c): out.add(f"custom {n} {ss} {2 + t} 0")
            for q in range(8):
                o = MIDI0 + PAT * (8 * t + q) + LANE0 + 192 * 8
                for v in b[o:o + 192]:
                    if 0x80 <= v < 0xC0: out.add(f"drums {v & 63} {ss} {2 + t} 1")
    return sorted(out)


def build():
    if OUT.exists(): shutil.rmtree(OUT)
    tr = OUT / "card" / "Tracks"; tr.mkdir(parents=True)
    fac = next(SRC.glob("00_*")); sh = next(SRC.glob("02_*"))
    a = make_pack(tr, ALPHA, fac, (0, 1), 6, [(session_with_notes(), "00_With Notes.ncs"), (next((fac / "Sessions").glob("*.ncs")), "01_SESSION.ncs")])
    b = make_pack(tr, BETA, sh, (0,), 4, [(next((sh / "Sessions").glob("*.ncs")), "00_Garbage.ncs")])
    vals = list(pt.DEFAULTS)
    vals[0] = -20; vals[9] = 33
    pt.write_slot(a, 10, pad_of("BASS", vals))
    pt.write_slot(a, 12, pad_of("LEAD", list(pt.DEFAULTS), extra=False))
    bad = bytearray(pad_of("BROKEN", list(pt.DEFAULTS))); bad[40] ^= 0x55
    pt.write_slot(a, 13, bytes(bad))
    # what the projects use (the usage badges): Alpha's 01 gets the own synth of both MIDI tracks, as projsyn saves it, and a sample flip of smpick
    s1 = a / "Sessions" / "01_SESSION.ncs"; sb = bytearray(rd(s1))
    smp = bytearray(pad_of("SAMPLER", list(pt.DEFAULTS))); smp[4] = 9; smp[5 + 25] = 2; smp[40] = sum(smp[4:40]) & 0xFF
    projsyn_put(sb, 0, bytes(smp))
    projsyn_put(sb, 1, pad_of("SAME AS BASS", vals))                 # slot 10's sound under another name
    sb[MIDI0 + PAT * 3 + LANE0 + 192 * 8 + 6 * 7] = 0x85                 # MIDI 1, pattern 4, step 8: the flip to sample 5
    s1.write_bytes(sb)
    (b / "Patches" / "00_PATCHBANK.cpb.bak").write_bytes(b"x")     # what the audit has to report
    (b / "Sessions" / "05_SC34D.bin").write_bytes(b"x")
    return tr


def patch(f: Path, at, data):
    b = bytearray(rd(f)) if f.exists() else bytearray()
    if len(b) < at + len(data): b += b"\xFF" * (at + len(data) - len(b))
    b[at:at + len(data)] = data
    f.parent.mkdir(exist_ok=True)
    f.write_bytes(b)


def bank(p: Path, n): return p / "Patches" / f"{n >> 3:02d}_PATCHBANK.cpb"
def rec(p: Path, n, off, ln): return rd(bank(p, n))[REC * (n & 7) + off:REC * (n & 7) + off + ln]


def pat_merge(cur, src):
    b = bytearray(src)
    b[SETT + 4:SETT + 7] = cur[SETT + 4:SETT + 7]
    b[SETT + 8:SETT + 40] = cur[SETT + 8:SETT + 40]
    return bytes(b)


def pat_empty(cur):
    b = bytearray(cur)
    for s in range(32):
        b[28 * s:28 * s + 28] = bytes([0, 7, 0, 0]) + b"\0\0\0\x60" * 6
    b[SETT:SETT + 4] = bytes([0x0F, 0, 3, 0]); b[SETT + 7] = 0
    b[LANE0:PAT] = b"\xFF" * (PAT - LANE0)
    return bytes(b)


def expected(tr: Path):
    """the operations of sd_app_test.html, on a copy"""
    x = OUT / "exp"; shutil.copytree(tr, x)
    a, b = x / ALPHA, x / BETA
    # Nova: Alpha 3 -> Beta 20 (bank 2 is new); Alpha 5 moved to Alpha 100 (bank 12 is new); Beta 1 deleted
    patch(bank(b, 20), REC * 4, rec(a, 3, 0, PSZ))
    n5 = rec(a, 5, 0, PSZ); patch(bank(a, 100), REC * 4, n5); patch(bank(a, 5), REC * 5, b"\xFF" * PSZ)
    patch(bank(b, 1), REC, b"\xFF" * PSZ)
    # custom: Alpha 10 -> Beta 11 with its 172 bytes; Alpha 12 moved to Beta 70 (bank 8 is new: 340 of 0xFF + the padding); then Beta 11 edited
    p10 = rec(a, 10, PSZ, PADN); p12 = rec(a, 12, PSZ, PADN)
    patch(bank(b, 11), REC * 3 + PSZ, p10)
    patch(bank(b, 70), REC * 6 + PSZ, p12); patch(bank(a, 12), REC * 4 + PSZ, b"\xFF" * PADN)
    e = bytearray(p10)
    e[5 + 1] = (-10) & 0xFF; e[5 + 2] = 77; e[40] = sum(e[4:40]) & 0xFF
    e[44:60] = b"EDITED".ljust(16)
    fm = bytearray(e[100:120]); fm[3] = 0; fm[4 + 12] = 9; e[100:120] = fm; e[120] = (0x5A + sum(fm)) & 0xFF
    e[126:130] = bytes([0xB6, 0x50 + 3, 10, 20])
    patch(bank(b, 11), REC * 3 + PSZ, bytes(e))
    # drums: Alpha 2 -> Beta 40; Alpha 1 over Beta 0 (the old name goes); Alpha 3 deleted; Alpha 4 moved to Alpha 50
    wav = lambda p, n: next((p / "PCM").glob(f"{n:02d}_*.wav"))
    w2, w1, w0 = wav(a, 2), wav(a, 1), wav(b, 0)
    shutil.copy(w2, b / "PCM" / ("40" + w2.name[2:]))
    w0.unlink(); shutil.copy(w1, b / "PCM" / ("00" + w1.name[2:]))
    wav(a, 3).unlink()
    w4 = wav(a, 4); shutil.copy(w4, a / "PCM" / ("50" + w4.name[2:])); w4.unlink()
    # patterns: every MIDI pattern of the session with notes that has notes, the first one -> Beta's M2 P3; the second moved to Alpha M2 P8; a third cleared
    s = a / "Sessions" / "00_With Notes.ncs"; sd = bytearray(rd(s)); bd = bytearray(rd(b / "Sessions" / "00_Garbage.ncs"))
    off = lambda n: MIDI0 + PAT * n
    full = [n for n in range(16) if any(sd[off(n) + 28 * i] for i in range(32))]
    p0, p1, p2 = full[0], full[1], full[2]
    bd[off(10):off(10) + PAT] = pat_merge(bytes(bd[off(10):off(10) + PAT]), bytes(sd[off(p0):off(p0) + PAT]))
    sd[off(15):off(15) + PAT] = pat_merge(bytes(sd[off(15):off(15) + PAT]), bytes(sd[off(p1):off(p1) + PAT]))
    sd[off(p1):off(p1) + PAT] = pat_empty(bytes(sd[off(p1):off(p1) + PAT]))
    sd[off(p2):off(p2) + PAT] = pat_empty(bytes(sd[off(p2):off(p2) + PAT]))
    s.write_bytes(sd); (b / "Sessions" / "00_Garbage.ncs").write_bytes(bd)
    # packs: Beta copied to slot 7 (same name after the number), Alpha moved to slot 9
    shutil.copytree(b, x / ("07" + BETA[2:]))
    (x / ALPHA).rename(x / ("09" + ALPHA[2:]))
    return x, {"full": full}


def tree(d: Path):
    return {str(f.relative_to(d)).replace("\\", "/"): hashlib.sha256(rd(f)).hexdigest() for f in sorted(d.rglob("*")) if f.is_file()}


def full():
    """--full: the whole card copy next to the fixture, and what patchtool / the plain bytes say about every file (the sweep of sd_app_test.html?full=1)"""
    d = OUT / "full"
    if d.exists(): shutil.rmtree(d)
    shutil.copytree(SRC, d)
    packs = {}
    for p in sorted(x for x in d.iterdir() if x.is_dir()):
        nv = []
        for n in range(128):
            f = pt.bank_file(p, n // 8); r = pt.record(rd(f), n % 8)[0] if f else None
            nv.append("" if pt.sempty(r) else pt.sname_of(r))
        ses = {}
        for f in sorted((p / "Sessions").glob("*.ncs")):
            b = rd(f)
            ses[f.name[:2]] = sum(bin(b[MIDI0 + PAT * n + 28 * s]).count("1") for n in range(16) for s in range(32))
        wav = {f.name[:2]: f.name[3:-4] for f in sorted((p / "PCM").glob("*.wav"))}
        packs[p.name] = {"nova": nv, "sessions": ses, "wav": wav, "usage": usage(p),
                         "words": sum(((f.stat().st_size - 44) & ~511) // 2 + 0x100 for f in (p / "PCM").glob("*.wav"))}
    files = [str(f.relative_to(d)).replace("\\", "/") for f in sorted(d.rglob("*")) if f.is_file()]
    (OUT / "full.json").write_text(json.dumps({"packs": packs, "files": files}))
    print("full:", len(packs), "packs,", len(files), "files")


def main():
    if "--full" in sys.argv:
        sys.argv.remove("--full"); return full()
    tr = build()
    names = {"nova": {}, "custom": {}, "drums": {}}
    for nm in (ALPHA, BETA):
        p = tr / nm
        nv = []
        for n in range(128):
            f = pt.bank_file(p, n // 8); r = pt.record(rd(f), n % 8)[0] if f else None
            nv.append("" if pt.sempty(r) else pt.sname_of(r))
        names["nova"][nm] = nv
        cu = []
        for n in range(128):
            b = pt.read_slot(p, n)
            cu.append({"state": {"ok": "ok", "empty": "empty", "bad sum": "bad"}[pt.state(b)], "name": pt.name_of(b)})
        names["custom"][nm] = cu
        names["drums"][nm] = {f.name[:2]: f.name[3:-4] for f in sorted((p / "PCM").glob("*.wav"))}
    use = {nm: usage(tr / nm) for nm in (ALPHA, BETA)}
    words = {nm: sum(((f.stat().st_size - 44) & ~511) // 2 + 0x100 for f in (tr / nm / "PCM").glob("*.wav")) for nm in (ALPHA, BETA)}
    ram = rd(ROOT / "ctre" / "Firmware-Analysis" / "ram_dump_firmware_0x08037988.bin")
    tpl = ram[0x3D2AC:0x3D2AC + 0x78 * 8]                          # the 8 factory templates of a running device
    base = tree(tr)
    x, info = expected(tr)
    (OUT / "expected.json").write_text(json.dumps({"alpha": ALPHA, "beta": BETA, "names": names, "words": words, "usage": use, "ccFactory": tpl.hex(), "full": info["full"],
                                                   "start": sorted(base), "tree": tree(x)}, indent=0))
    print("fixture:", OUT, len(base), "files;", "patterns with notes:", info["full"])
    import dx7ref                                                   # sd_app_test.html?dx7=1
    dx7ref.main()


if __name__ == "__main__":
    main()
