"""Read the black box over USB (the app's «Caja negra…» from the command line): 16 chunks of 64 B by SysEx 01, saved as
Documents/blackbox_<firmware>_<time>.json (raw hex + the key fields).

    python tools/bbread.py [--firmware NAME]
    python tools/bbread.py --clear          (SysEx 02: unfreeze and clear the record so the next event is captured)
"""
from __future__ import annotations
import json, struct, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ctremote as CR
import blackbox as BB


def read(link, addr=0, n=1024):
    data = b""
    a7 = [(addr >> s) & 0x7F for s in (28, 21, 14, 7, 0)]
    for c in range((n + 63) // 64):
        link.seq = (link.seq + 1) & 0x7F
        link.send(bytes([0xF0, 0x7D, 0x43, 0x54, 0x01, link.seq, c, 0x00]) + bytes(a7) + bytes(123) + bytes([0xF7]))
        t = time.time(); acc = b""; got = None
        while got is None and time.time() - t < 3:
            try: chunk, p1 = link.q.get(timeout=0.05)
            except Exception: continue
            link._readd(p1); acc += chunk
            while got is None and b"\xF0" in acc and b"\xF7" in acc[acc.index(b"\xF0"):]:
                s = acc.index(b"\xF0"); e = acc.index(b"\xF7", s); msg, acc = acc[s:e + 1], acc[e + 1:]
                if msg[:5] == bytes([0xF0, 0x7D, 0x43, 0x54, 0x41]) and msg[5] == link.seq and msg[6] == c:
                    n = msg[8:-1]; got = bytes(n[i] << 4 | n[i + 1] for i in range(0, 128, 2))
        if got is None: raise SystemExit(f"no reply for chunk {c}")
        data += got
    return data


def clear(link):
    link.seq = (link.seq + 1) & 0x7F
    link.send(bytes([0xF0, 0x7D, 0x43, 0x54, 0x02, link.seq]) + bytes(7) + bytes([0xF7]))
    t = time.time(); acc = b""
    while time.time() - t < 3:
        try: chunk, p1 = link.q.get(timeout=0.05)
        except Exception: continue
        link._readd(p1); acc += chunk
        if bytes([0xF0, 0x7D, 0x43, 0x54, 0x42, link.seq]) in acc: return True
    return False


def main(a):
    if "--clear" in a:
        link = CR.Link()
        try: print("cleared" if clear(link) else "no reply to the clear")
        finally: link.close()
        return
    if "--mem" in a:                                                            # (S564D4) python tools/bbread.py --mem ADDR [LEN]  (RAM only: byte reads; a peripheral that wants words faults)
        i = a.index("--mem"); addr = int(a[i + 1], 0); n = int(a[i + 2], 0) if len(a) > i + 2 else 64
        link = CR.Link()
        try: d = read(link, addr, n)[:n]
        finally: link.close()
        for o in range(0, n, 16): print(f"{addr + o:08x}: " + " ".join(f"{x:08x}" for x in struct.unpack_from("<4I", d.ljust(o + 16, b"\0"), o)))
        return
    fw = a[a.index("--firmware") + 1] if "--firmware" in a else "unknown"
    link = CR.Link()
    try: raw = read(link)
    finally: link.close()
    u = lambda o: struct.unpack_from("<I", raw, o)[0]
    O, O2 = BB.O, BB.O2
    ring = []
    for i in range(16):
        t, k = struct.unpack_from("<IB", raw, O.RING + 8 * i)[:2]
    st = raw[O.ST]
    out = dict(firmware=fw, read=time.strftime("%Y-%m-%dT%H:%M:%S"), state=st, frozen=bool(st & 1), fault=bool(st & BB.ST_FAULT),
               vector_xtra=hex(u(O2.XTRA)), pc=hex(u(O2.RPC)), lr=hex(u(O2.RLR)), regs=[hex(u(O.PC + 8 + 4 * i)) for i in range(6)],
               cfsr=hex(u(O2.CFSR)), fault_address=hex(u(O2.FADR)), view=hex(u(O.VIEW)), freeze_ms=u(O.FT), raw=raw.hex())
    tag, val = struct.unpack_from("<2I", raw, O.STK1)
    if st == 0x85 and tag in (1, 2):                                               # Beta 5.65 (paintguard): a painter skipped a bad value
        out["paintguard"] = dict(what=("probability view" if tag == 1 else "drum velocity bar"), value=val)
    elif st == 0x85:                                                               # S564D3 (dmawatch): the DMA dump at O.STK1
        o = raw[O.STK1:O.STK1 + 8 + 256]
        out["dmawatch"] = dict(frames=struct.unpack_from("<I", o)[0], word=hex(struct.unpack_from("<I", o, 4)[0]),
                               streams=[dict(stream=("DMA1" if i < 8 else "DMA2") + f" S{i % 8}", **dict(zip(("ndtr", "m0ar", "cr", "par"), (hex(x) for x in struct.unpack_from("<4I", o, 8 + 16 * i)))))
                                        for i in range(16)])
    p = Path.home() / "Documents" / f"blackbox_{fw}_{time.strftime('%Y-%m-%d_%H%M%S')}.json"
    p.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "raw"}, indent=1)); print("saved", p)


if __name__ == "__main__":
    main(sys.argv[1:])
