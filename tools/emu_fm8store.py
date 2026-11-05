"""SC51.7 part 3 (tools/fm8store.py): where the 8-operator FM's patches live.

    python tools/emu_fm8store.py SC51.7.bin SC51.7_manifest.json

A. emu_sc39_4's harness (the firmware, emu_sc35's card), mpatch's own save / load called as the panel does:
  * bank 0 of the loaded pack = 7 records (3924 bytes); slot 3 saved with FM on: its padding = the own patch ("FM" 3 at + 100), the bank 0xFF from
    3924 up to the FM record of slot 3 (4096 + 3 x 512), the record = "FM8" 1 + the 216 parameters + their sum; the stock's 340-byte patches untouched;
  * the parameters changed, slot 3 loaded: back as saved;
  * projsyn's virtual slot: its gather (c_ysrun) puts the record in FMIMG[0], not on the card; c_fsprj writes it into bytes 8..39 of Synth 1's
    patterns 0..7 (0xC8, block id), reads it back; its apply restores the parameters; a damaged block = FMIMG's header 0;
  * psave's swap (3 <-> 5): the records follow the paddings; xpatch's copy from pack 7's slot 3 into slot 6: the record too.
B. emu_sdsysex's harness (the stock's file protocol, real above FatFs), pack 1, a bank with own bytes (paddings + FM records):
  * a Components-style write (7 records, 0xFF paddings): the new patches + the own bytes back (0xFF from 3924 to the records);
  * a host's write that carries own bytes (the SD app): kept as sent;
  * a delete: the file made again, 8 empty records (0xFF) + the own bytes; a bank without own bytes: deleted;
  * pack 0: a write leaves the file as sent.
"""
from __future__ import annotations
import gc, json, struct, sys, zlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fm8 as F  # noqa: E402
import fm8arm as A  # noqa: E402
import fm8store as FS  # noqa: E402
import mpatch as MP  # noqa: E402
import projsyn as PS  # noqa: E402

fails = 0


def check(c, m):
    global fails
    print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1


def rec_of(params):
    s = (FS.SUM0 + sum(params)) & 0xFFFF
    return struct.pack("<I", FS.HDR) + bytes(params) + struct.pack("<H", s) + b"\xFF" * (FS.RECN - 6 - F.PLEN)


def part_a(img, man):
    import emu_sc39_4 as T4
    R = man["report"]
    lab = lambda m, k: int(R[m]["labels"][k], 16)
    e = T4.E4(img, man); e.setup(man)
    e.btn(2); e.btn(8)
    e.call(lab("fm8", "c_fmst"))
    blk = A.FM8R + A.TB0
    pa = [(7 * i + 11) % 100 for i in range(F.PLEN)]
    e.uc.mem_write(blk, bytes(pa)); e.uc.mem_write(blk + A.B_ON, b"\x01")
    stock = [bytes((3 + k + i) & 0x7F for i in range(340)) for k in range(8)]
    bank0 = b"".join(stock[k] + b"\xFF" * 172 for k in range(7)) + stock[7]
    assert len(bank0) == 3924
    e.sd = {(3, 0, 0xFF): bank0}
    e.api.clear(); e.call(lab("mpatch", "c_mpsave"), 0, 3, maxins=40_000_000)
    f = e.sd[(3, 0, 0xFF)]
    t = 4096 + 512 * 3
    check(len(f) == t + FS.RECN, f"slot 3 saved: the bank {len(f)} bytes (the record of slot 3 ends at {t + FS.RECN})")
    check(all(f[512 * k:512 * k + 340] == stock[k] for k in range(8)), "the stock's 340-byte patches untouched")
    check(f[512 * 3 + 340:512 * 3 + 344] == struct.pack("<I", MP.MAGIC4) and f[512 * 3 + 440:512 * 3 + 443] == b"FM\x03", "slot 3's padding: the own patch, FM version 3")
    check(f[3924:t] == b"\xFF" * (t - 3924) or all(f[i] == 0xFF for i in range(3924, t) if not 512 * 3 + 340 <= i < 512 * 4), "0xFF from 3924 up to the record")
    check(f[t:t + FS.RECN] == rec_of(pa), "the record: FM8 1, the parameters, the sum")
    e.uc.mem_write(blk, bytes(F.PLEN)); e.uc.mem_write(blk + A.B_ON, b"\x00")
    e.call(lab("mpatch", "c_mpload"), 0, 3, maxins=40_000_000)
    got = list(e.uc.mem_read(blk, F.PLEN))
    check(got == pa and e.r8(blk + A.B_ON) == 1, f"slot 3 loaded: the parameters and FM on back ({got[:6]}..)")
    # projsyn's virtual slot
    n_wr = len(e.wr())
    e.call(lab("projsyn", "c_ysst")); e.call(lab("projsyn", "c_ysrun"), 0, 0, maxins=40_000_000)
    img0 = bytes(e.uc.mem_read(FS.FMIMG, FS.RECN))
    check(img0 == rec_of(pa) and len(e.wr()) == n_wr, "projsyn's gather: the record in FMIMG[0], nothing on the card")
    rp = e.r32(FS.SESSION_OBJ + 0x14)
    head = lambda: [bytes(e.uc.mem_read(rp + FS.SYN_AREA + FS.PSIZE * k + FS.PSET, 8)) for k in range(16)] + [bytes(e.uc.mem_read(rp + FS.SYN_AREA + FS.PSIZE * 8 + FS.PSET + 8, 32))]
    before = head()
    e.call(lab("fm8", "c_fsprj"), 0, 0, maxins=2_000_000)
    blocks = [bytes(e.uc.mem_read(rp + FS.SYN_AREA + FS.PSIZE * k + FS.PSET + FS.PBYTE0, 32)) for k in range(8)]
    check(all(b_[0] == FS.PSIG and b_[1] == k for k, b_ in enumerate(blocks)) and b"".join(b_[2:] for b_ in blocks)[:FS.RECN] == img0,
          "the project: 8 blocks in Synth 1's patterns 0..7 (0xC8, the id, the record)")
    check(head() == before, "bytes 0..7 of Synth 1 / 2's pattern settings and Synth 2's blocks: not written")
    e.uc.mem_write(FS.FMIMG, bytes(FS.RECN)); e.call(lab("fm8", "c_fsprj"), 0, 1, maxins=2_000_000)
    check(bytes(e.uc.mem_read(FS.FMIMG, FS.RECN)) == img0, "read back from the project into FMIMG[0]")
    e.uc.mem_write(blk, bytes(F.PLEN)); e.call(lab("projsyn", "c_ysrun"), 0, 1, maxins=40_000_000)
    check(list(e.uc.mem_read(blk, F.PLEN)) == pa, "projsyn's apply: the parameters from the project")
    e.uc.mem_write(rp + FS.SYN_AREA + FS.PSIZE * 4 + FS.PSET + FS.PBYTE0 + 1, b"\x09"); e.call(lab("fm8", "c_fsprj"), 0, 1, maxins=2_000_000)
    check(e.r32(FS.FMIMG) == 0, "a damaged block: FMIMG's header 0 (nothing applied)")
    # psave's swap and xpatch's copy
    e.sd[(3, 0, 0xFF)] = f
    e.call(lab("fm8", "c_fsswap"), 3, 5, maxins=60_000_000)
    g = e.sd[(3, 0, 0xFF)]
    r5 = 4096 + 512 * 5
    check(g[512 * 5 + 340:512 * 5 + 440] == f[512 * 3 + 340:512 * 3 + 440] and g[r5:r5 + FS.RECN] == rec_of(pa) and g[t:t + FS.RECN] == b"\xFF" * FS.RECN,
          "psave's swap 3 <-> 5: the padding and the FM record moved together")
    other = bytearray(g); other[t:t + FS.RECN] = rec_of(list(reversed(pa)))
    e.sd[(3, 0, 7)] = bytes(other); e.cur = 31
    e.call(lab("fm8", "c_fsxcopy"), 7, 5, 6, maxins=60_000_000)
    h_ = e.sd[(3, 0, 0xFF)]; r6 = 4096 + 512 * 6
    check(h_[512 * 6 + 340:512 * 6 + 440] == other[512 * 5 + 340:512 * 5 + 440] and h_[r6:r6 + FS.RECN] == other[r5:r5 + FS.RECN],
          "xpatch's copy (pack 7 slot 5 -> slot 6): the padding and the record")
    del e; gc.collect()


def part_b(img):
    import emu_sdsysex as SX
    S = SX.Suite(verbose=False)
    own = bytearray()
    stock = [bytes((5 * k + i) & 0x7F or 1 for i in range(340)) for k in range(8)]
    pads = [b"CTM1" + bytes((k + i) & 0x7F for i in range(168)) for k in range(8)]
    for k in range(8): own += stock[k] + pads[k]
    ext = [rec_of([(k * 13 + i) % 100 for i in range(F.PLEN)]) + b"\xFF" * (512 - FS.RECN) for k in range(8)]
    for k in range(8): own += ext[k]
    own = bytes(own)
    comp = [bytes((9 * k + i) & 0x7F or 2 for i in range(340)) for k in range(8)]
    cfile = b"".join(comp[k] + b"\xFF" * 172 for k in range(7)) + comp[7]
    f = SX.boot(img)
    f.fs.put(SX.A + "Patches/02_PATCHBANK.cpb", own)
    f.fs.put(SX.A + "Patches/03_PATCHBANK.cpb", cfile)
    f.fs.put("0:/Tracks/00_Internal/Patches/02_PATCHBANK.cpb", own)
    path = lambda n: next(k for k in f.fs.files if k.startswith(SX.A + "Patches/%02d_" % n))
    f.send(SX.OPEN)
    w = SX.write_file(f, S, SX.T_PATCH, 1, 2, cfile)
    got = bytes(f.fs.files[path(2)])
    want = bytearray(cfile + b"\xFF" * (8192 - len(cfile)))
    for k in range(8): want[512 * k + 340:512 * k + 512] = pads[k]
    for k in range(8): want[4096 + 512 * k:4096 + 512 * k + FS.RECN] = ext[k][:FS.RECN]
    want = bytes(want[:4096 + 512 * 7 + FS.RECN])
    check(w[0] == "end" and got == want, f"a Components-style write: its patches + the own bytes back ({len(got)} bytes, {w[0]})")
    sd = own[:100] + b"\x01" + own[101:]
    SX.write_file(f, S, SX.T_PATCH, 1, 2, sd)
    check(bytes(f.fs.files[path(2)]) == sd, "a write that carries own bytes (the SD app): kept as sent")
    r = f.send(SX.sx(0x08, SX.T_PATCH, 1, 2))
    got = bytes(f.fs.files.get(path(2), b"")) if any(k.startswith(SX.A + "Patches/02_") for k in f.fs.files) else b""
    want = bytearray(b"\xFF" * (4096 + 512 * 7 + FS.RECN))
    for k in range(8): want[512 * k + 340:512 * k + 512] = sd[512 * k + 340:512 * k + 512]
    for k in range(8): want[4096 + 512 * k:4096 + 512 * k + FS.RECN] = sd[4096 + 512 * k:4096 + 512 * k + FS.RECN]
    check(got == bytes(want), f"a delete: 8 empty records + the own bytes ({len(got)} bytes; {r})")
    f.send(SX.sx(0x08, SX.T_PATCH, 1, 3))
    check(not any(k.startswith(SX.A + "Patches/03_") for k in f.fs.files), "a bank without own bytes: deleted")
    SX.write_file(f, S, SX.T_PATCH, 0, 2, cfile)
    p0 = next(k for k in f.fs.files if k.startswith("0:/Tracks/00_Internal/Patches/02_"))
    check(bytes(f.fs.files[p0]) == cfile, "pack 0: the write as sent")
    f.send(SX.CLOSE)
    del f; gc.collect()


def main(img, man):
    part_a(img, man)
    part_b(img)
    print(f"{man['marker']} FM8 STORE RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
