"""(2026-11-24) Rebuild the internal file system's damaged blocks from inside the Circuit Tracks (NORFXD installed, tools/build_norfxd.py).
    python tools/norfix.py check DUMP.img REPAIRED.img     read-only: the mapping (disk offset + 0x94000 = NOR) and that every block to write still
                                                         holds the dump's bytes; a data block as a control
    python tools/norfix.py write DUMP.img REPAIRED.img     the same checks, then for each block that differs: erase 4 KB, write, read back
The USB drive's disk 0 is NOR 0x94000 (P3, 256 KB) followed by the file-system partition (NOR 0xD4000 = disk 0x40000); NORFXD refuses to erase or write
below 0xD4000.  The data blocks are read through the same stock device the firmware uses: turn Easy Start off first (Advanced Setup), so the PC's
USB drive is not read at the same time."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ctremote as CR

DISK0 = 0x94000
BLK = 4096


def rd(L, nor, n=BLK):
    out = b""
    for o in range(0, n, CR.NMAX):
        p = L.ask(lambda s, a=nor + o: CR.build(20, s, CR.nib32(a) + [CR.NMAX]), 20)
        st = CR.un32(p[:8])
        if st: raise SystemExit(f"read {nor + o:#x}: status {st:#x}")
        out += CR.unbytes(p[8:8 + 2 * CR.NMAX])
    return out


def main(mode, dump, rep):
    OLD, NEW = Path(dump).read_bytes(), Path(rep).read_bytes()
    blocks = [o for o in range(0, len(OLD), BLK) if OLD[o:o + BLK] != NEW[o:o + BLK]]
    print("blocks to write (disk offset):", [hex(o) for o in blocks])
    assert all(o >= 0x40000 for o in blocks)
    L = CR.Link("Circuit Tracks")
    try:
        v = CR.un32(L.ask(lambda s: CR.req_ping(s), 1)[:8])
        if v != 0x35D8 + 0x1000: raise SystemExit(f"ping version {v:#x}: NORFXD is not installed")
        ctl = 0x4D000
        if rd(L, DISK0 + ctl) != OLD[ctl:ctl + BLK]: raise SystemExit("control block (disk 0x4D000 = the first data cluster) differs from the dump: mapping wrong, stopped")
        print("control: disk 0x4D000 = NOR", hex(DISK0 + ctl), "matches the dump")
        for o in blocks:
            if rd(L, DISK0 + o) != OLD[o:o + BLK]: raise SystemExit(f"disk {o:#x} (NOR {DISK0 + o:#x}) no longer holds the dump's bytes: stopped, nothing written")
        print("all blocks still hold the dump's bytes")
        if mode != "write": return
        for o in blocks:
            a = DISK0 + o
            st = CR.un32(L.ask(lambda s: CR.build(18, s, CR.nib32(a)), 18, timeout=10)[:8])
            if st: raise SystemExit(f"erase {a:#x}: status {st:#x}")
            for k in range(0, BLK, CR.NMAX):
                chunk = NEW[o + k:o + k + CR.NMAX]
                st = CR.un32(L.ask(lambda s, x=a + k, c=chunk: CR.build(19, s, CR.nib32(x) + [len(c)] + CR.nibbytes(c)), 19)[:8])
                if st: raise SystemExit(f"write {a + k:#x}: status {st:#x}")
            ok = rd(L, a) == NEW[o:o + BLK]
            print(f"disk {o:#08x} = NOR {a:#08x}: erased, written, read back {'OK' if ok else 'MISMATCH'}")
            if not ok: raise SystemExit("stopped")
        print("done: switch the Circuit off and on")
    finally:
        L.close()


if __name__ == "__main__":
    main(*sys.argv[1:4])
