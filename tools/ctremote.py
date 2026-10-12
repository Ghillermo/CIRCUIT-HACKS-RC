"""Remote diagnostics of a Circuit Tracks running SC35D8 (tools/rdiag.py), over USB MIDI SysEx, from Windows (WinMM through ctypes, no extra packages).

    python tools/ctremote.py ports
    python tools/ctremote.py ping
    python tools/ctremote.py mem 0x20000800 64
    python tools/ctremote.py info KIND IDX [PACK]            kinds: 2 sessions, 3 patches, 4 pcm, 5 meta, 6 fx; PACK 127 (default) = the current pack
    python tools/ctremote.py read KIND IDX OFFSET LEN [PACK]
    python tools/ctremote.py dump KIND IDX FILE [PACK]       the whole item, 64 bytes per request, into FILE
    python tools/ctremote.py write KIND IDX OFFSET HEXBYTES [PACK] --yes   writes to the SD card (use only on a test pack)
    python tools/ctremote.py put KIND IDX FILE [PACK] --yes          writes FILE into the item from offset 0, 64 bytes per request (SC35D8+)
    python tools/ctremote.py del KIND IDX [PACK] --yes               deletes the item (op 5; SC35D9, kinds 2-6 only)
    python tools/ctremote.py delpack PACK --yes                      deletes a whole pack (SC35DA; numbered as the API = folder + 1; never the current one)
    python tools/ctremote.py dspr X|Y ADDR N / dspx SRC N / capture FILE.wav     DSP memory and the captured sample (SC342D+)
    python tools/ctremote.py dspw ADDR VALUE                         writes one DSP X word (SC35DB)
  SEQWD (rdiag.WATCH): the DWT data watchpoint and its log of the code that touched the address
    python tools/ctremote.py watch ADDR [read|write|rw|off] [MASK]   arms comparator 0 (MASK = low address bits ignored) and clears the log
    python tools/ctremote.py wlog                                    hits + the distinct PC / LR that touched the address
    python tools/ctremote.py poke ADDR HEXBYTES --yes                writes RAM (0x20000000-0x2004FFFF)
    python tools/ctremote.py step TRACK PATTERN STEP                 a step's address ([[0x2003C168 + 0xC + 4 t] + 0x48] + 0xCA8 p + 28 s) and its 28 bytes
    python tools/ctremote.py seqwatch TRACK PATTERN STEP [BYTE] [read|write|rw]   watch that step's byte (default 4 = the note of its first unit)
Close any other program that holds the Circuit Tracks MIDI ports (MIDI monitors, Components, a DAW): on Windows a port opens only once.
"""
from __future__ import annotations
import ctypes
import queue
import sys
import time
from ctypes import wintypes

SIG = (0xF0, 0x7D, 0x43, 0x54)
PAD = 232
NMAX = 64
KINDS = {"sessions": 2, "patches": 3, "pcm": 4, "meta": 5, "fx": 6}


# ---------------------------------------------------------------- protocol (no I/O; also used by the emulation test)
def nib32(v): return [(v >> s) & 15 for s in range(28, -1, -4)]
def nibbytes(bs): return [x for b in bs for x in (b >> 4, b & 15)]
def un32(n): return int("".join("%x" % x for x in n), 16)
def unbytes(n): return bytes(n[i] << 4 | n[i + 1] for i in range(0, len(n), 2))


def build(cmd, seq, payload=()):
    body = list(SIG) + [cmd, seq & 0x7F] + list(payload)
    body += [0] * max(0, PAD - 1 - len(body))
    return bytes(body + [0xF7])


def parse(msg, cmd, seq):
    """-> the payload nibbles of our reply to (cmd, seq), or None."""
    if len(msg) < 7 or tuple(msg[:4]) != SIG or msg[4] != (cmd | 0x40) or msg[5] != (seq & 0x7F) or msg[-1] != 0xF7:
        return None
    return list(msg[6:-1])


def req_ping(seq): return build(1, seq)
WFUNC = {"off": 0, "read": 5, "write": 6, "rw": 7}
GATE_OBJ, STEP_SZ, PAT_SZ = 0x2003C168, 28, 0xCA8
def req_watch(seq, addr, func, mask=0): return build(10, seq, nib32(addr) + [func & 0x7F, mask & 0x7F])
def req_poke(seq, addr, data): return build(11, seq, nib32(addr) + [len(data)] + nibbytes(data))
def req_wlog(seq): return build(12, seq)
def dec_watch(p): return dict(status=un32(p[:8]), dwt_ctrl=un32(p[8:16]), demcr=un32(p[16:24]), function0=un32(p[24:32]), log=un32(p[32:40]))
def dec_wlog(p):
    st, hits = un32(p[:8]), un32(p[8:16])
    pairs = [(un32(p[i:i + 8]), un32(p[i + 8:i + 16])) for i in range(16, len(p) - 15, 16)]
    return dict(status=st, hits=hits, pcs=[(pc, lr) for pc, lr in pairs if pc])
def req_mem(seq, addr, n): return build(2, seq, nib32(addr) + [min(n, NMAX)])
def req_info(seq, kind, idx, pack=0x7F): return build(4, seq, [kind, idx, pack])
def req_read(seq, kind, idx, off, n, pack=0x7F): return build(5, seq, [kind, idx, pack] + nib32(off) + [min(n, NMAX)])
def req_write(seq, kind, idx, off, data, pack=0x7F):
    assert len(data) <= NMAX
    return build(6, seq, [kind, idx, pack] + nib32(off) + [len(data)] + nibbytes(data))


def dec_ping(p): return dict(version=un32(p[:8]), port=un32(p[8:16]))
def dec_mem(p): return dict(status=un32(p[:8]), data=unbytes(p[8:]))
def dec_info(p): return dict(exists=un32(p[:8]), size=un32(p[8:16]))
def dec_read(p): return dict(status=un32(p[:8]), done=un32(p[8:16]), data=unbytes(p[16:]))
def dec_write(p): return dict(status=un32(p[:8]))
def req_del(seq, kind, idx, pack=0x7F): return build(7, seq, [kind, idx, pack])
dec_del = dec_write
NR, NX = 24, 48                                  # SC342D (rdiag.DSPX): words per dspr, samples per dspx
CAP_BASE, X_LEN = 0xE80000, 0x3D09               # SC34.1+: the captured sample at Y:$E80000, its length at X:LEN (sampler_dsp)
def req_dspr(seq, space, addr, n): return build(3, seq, [space] + nib32(addr) + [min(n, NR)])
def req_dspx(seq, src, n): return build(8, seq, nib32(src) + [min(n, NX)])
def dec_delpack(p): return dict(status=un32(p[:8]), reselect_exists=un32(p[8:16]) if len(p) >= 16 else None, current=un32(p[16:24]) if len(p) >= 24 else None)
def req_dspw(seq, addr, v): return build(9, seq, nib32(addr) + nib32(v))
def dec_dspr(p): return dict(status=un32(p[:8]), words=[un32([0, 0] + p[i:i + 6]) for i in range(8, len(p), 6)])
def dec_dspx(p): return dict(status=un32(p[:8]), samples=[un32([0] * 4 + p[i:i + 4]) for i in range(8, len(p), 4)])


def wav16(samples, rate=48000):
    """mono 16-bit PCM WAV, 'fmt ' + 'data' only (the format of the packs' PCM folder)."""
    import struct
    data = b"".join(struct.pack("<H", s & 0xFFFF) for s in samples)
    return b"RIFF" + struct.pack("<I", 36 + len(data)) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, rate, rate * 2, 2, 16) + b"data" + struct.pack("<I", len(data)) + data


# ---------------------------------------------------------------- WinMM
winmm = ctypes.WinDLL("winmm") if sys.platform == "win32" else None
CALLBACK_FUNCTION = 0x30000
MIM_LONGDATA = 0x3C4
MHDR_DONE = 1


class MIDIHDR(ctypes.Structure):
    _fields_ = [("lpData", ctypes.c_void_p), ("dwBufferLength", wintypes.DWORD), ("dwBytesRecorded", wintypes.DWORD), ("dwUser", ctypes.c_void_p),
                ("dwFlags", wintypes.DWORD), ("lpNext", ctypes.c_void_p), ("reserved", ctypes.c_void_p), ("dwOffset", wintypes.DWORD),
                ("dwReserved", ctypes.c_void_p * 8)]


class MIDIINCAPSW(ctypes.Structure):
    _fields_ = [("wMid", wintypes.WORD), ("wPid", wintypes.WORD), ("vDriverVersion", wintypes.UINT), ("szPname", wintypes.WCHAR * 32), ("dwSupport", wintypes.DWORD)]


class MIDIOUTCAPSW(ctypes.Structure):
    _fields_ = [("wMid", wintypes.WORD), ("wPid", wintypes.WORD), ("vDriverVersion", wintypes.UINT), ("szPname", wintypes.WCHAR * 32), ("wTechnology", wintypes.WORD),
                ("wVoices", wintypes.WORD), ("wNotes", wintypes.WORD), ("wChannelMask", wintypes.WORD), ("dwSupport", wintypes.DWORD)]


MIDIINPROC = getattr(ctypes, "WINFUNCTYPE", ctypes.CFUNCTYPE)(   # CFUNCTYPE elsewhere: importable on Linux for the emulation tests
    None, wintypes.HANDLE, wintypes.UINT, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)


def ports():
    ins, outs = [], []
    for i in range(winmm.midiInGetNumDevs()):
        c = MIDIINCAPSW(); winmm.midiInGetDevCapsW(i, ctypes.byref(c), ctypes.sizeof(c)); ins.append(c.szPname)
    for i in range(winmm.midiOutGetNumDevs()):
        c = MIDIOUTCAPSW(); winmm.midiOutGetDevCapsW(i, ctypes.byref(c), ctypes.sizeof(c)); outs.append(c.szPname)
    return ins, outs


class Link:
    def __init__(self, name="Circuit"):
        ins, outs = ports()
        ii = [i for i, n in enumerate(ins) if name.lower() in n.lower()]
        oo = [i for i, n in enumerate(outs) if name.lower() in n.lower()]
        if not ii or not oo:
            raise SystemExit(f"no MIDI port named '{name}' (inputs {ins}, outputs {outs}): is the Circuit Tracks connected by USB?")
        self.q = queue.Queue()
        self.hin, self.hout = wintypes.HANDLE(), wintypes.HANDLE()
        self.cb = MIDIINPROC(self._cb)
        r = winmm.midiInOpen(ctypes.byref(self.hin), ii[0], self.cb, None, CALLBACK_FUNCTION)
        if r: raise SystemExit(f"midiInOpen({ins[ii[0]]}) failed ({r}): another program holds the port?")
        r = winmm.midiOutOpen(ctypes.byref(self.hout), oo[0], None, None, 0)
        if r:
            winmm.midiInClose(self.hin); raise SystemExit(f"midiOutOpen({outs[oo[0]]}) failed ({r}): another program holds the port?")
        self.bufs = []
        for _ in range(8):
            b = ctypes.create_string_buffer(1024); hd = MIDIHDR(); hd.lpData = ctypes.cast(b, ctypes.c_void_p); hd.dwBufferLength = 1024
            winmm.midiInPrepareHeader(self.hin, ctypes.byref(hd), ctypes.sizeof(hd)); winmm.midiInAddBuffer(self.hin, ctypes.byref(hd), ctypes.sizeof(hd))
            self.bufs.append((b, hd))
        winmm.midiInStart(self.hin)
        self.seq = 0

    def _cb(self, h, msg, inst, p1, p2):
        if msg == MIM_LONGDATA and p1:
            hd = ctypes.cast(p1, ctypes.POINTER(MIDIHDR)).contents
            if hd.dwBytesRecorded:
                self.q.put((ctypes.string_at(hd.lpData, hd.dwBytesRecorded), p1))
            else:
                self.q.put((b"", p1))

    def _readd(self, p1):
        winmm.midiInAddBuffer(self.hin, ctypes.c_void_p(p1), ctypes.sizeof(MIDIHDR))

    def send(self, data):
        b = ctypes.create_string_buffer(bytes(data), len(data)); hd = MIDIHDR(); hd.lpData = ctypes.cast(b, ctypes.c_void_p); hd.dwBufferLength = len(data)
        winmm.midiOutPrepareHeader(self.hout, ctypes.byref(hd), ctypes.sizeof(hd))
        r = winmm.midiOutLongMsg(self.hout, ctypes.byref(hd), ctypes.sizeof(hd))
        if r: raise SystemExit(f"midiOutLongMsg failed ({r})")
        t = time.time()
        while not hd.dwFlags & MHDR_DONE and time.time() - t < 2: time.sleep(0.001)
        winmm.midiOutUnprepareHeader(self.hout, ctypes.byref(hd), ctypes.sizeof(hd))

    def ask(self, make, cmd, timeout=3.0):
        self.seq = (self.seq + 1) & 0x7F
        self.send(make(self.seq))
        t = time.time(); acc = b""
        while time.time() - t < timeout:
            try: chunk, p1 = self.q.get(timeout=0.05)
            except queue.Empty: continue
            self._readd(p1); acc += chunk
            while b"\xF0" in acc and b"\xF7" in acc[acc.index(b"\xF0"):]:
                s = acc.index(b"\xF0"); e = acc.index(b"\xF7", s); msg, acc = acc[s:e + 1], acc[e + 1:]
                p = parse(msg, cmd, self.seq)
                if p is not None: return p
        raise SystemExit(f"no reply to command {cmd} (is SC35D8 installed and the Circuit Tracks connected by USB?)")

    def close(self):
        winmm.midiInStop(self.hin); winmm.midiInReset(self.hin)
        for b, hd in self.bufs: winmm.midiInUnprepareHeader(self.hin, ctypes.byref(hd), ctypes.sizeof(hd))
        winmm.midiInClose(self.hin); winmm.midiOutClose(self.hout)


def num(s): return int(s, 0)


def kind_of(s): return KINDS.get(s.lower(), None) if not s[0].isdigit() else int(s, 0)


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__); return 0
    cmd = argv[0]
    if cmd == "ports":
        ins, outs = ports(); print("in :", ins); print("out:", outs); return 0
    L = Link()
    try:
        if cmd == "ping":
            print(dec_ping(L.ask(req_ping, 1)))
        elif cmd == "mem":
            addr, n = num(argv[1]), num(argv[2]); out = b""
            while n > 0:
                d = dec_mem(L.ask(lambda s, a=addr, k=min(n, NMAX): req_mem(s, a, k), 2))
                if d["status"]: raise SystemExit(f"status {d['status']} at {addr:#x}")
                out += d["data"]; addr += len(d["data"]); n -= len(d["data"])
            for i in range(0, len(out), 16): print(f"{num(argv[1]) + i:08x}  {out[i:i + 16].hex(' ')}")
        elif cmd == "info":
            k, i = kind_of(argv[1]), num(argv[2]); pk = num(argv[3]) if len(argv) > 3 else 0x7F
            print(dec_info(L.ask(lambda s: req_info(s, k, i, pk), 4)))
        elif cmd == "read":
            k, i, off, n = kind_of(argv[1]), num(argv[2]), num(argv[3]), num(argv[4]); pk = num(argv[5]) if len(argv) > 5 else 0x7F
            d = dec_read(L.ask(lambda s: req_read(s, k, i, off, n, pk), 5)); print(dict(status=d["status"], done=d["done"]), d["data"].hex(" "))
        elif cmd == "dump":
            k, i, fn = kind_of(argv[1]), num(argv[2]), argv[3]; pk = num(argv[4]) if len(argv) > 4 else 0x7F
            inf = dec_info(L.ask(lambda s: req_info(s, k, i, pk), 4)); size = inf["size"]; out = b""
            print(f"exists {inf['exists']}, size {size}")
            while len(out) < size:
                d = dec_read(L.ask(lambda s, o=len(out): req_read(s, k, i, o, min(NMAX, size - o), pk), 5))
                if d["status"] or not d["done"]: raise SystemExit(f"read status {d['status']} done {d['done']} at {len(out)}")
                out += d["data"]
                if len(out) % 4096 < NMAX: print(f"\r{len(out)} / {size}", end="", flush=True)
            open(fn, "wb").write(out); print(f"\n{fn}: {len(out)} bytes")
        elif cmd == "write":
            if "--yes" not in argv: raise SystemExit("write changes the SD card: add --yes (and use a test pack)")
            a = [x for x in argv if x != "--yes"]
            k, i, off, data = kind_of(a[1]), num(a[2]), num(a[3]), bytes.fromhex(a[4]); pk = num(a[5]) if len(a) > 5 else 0x7F
            print(dec_write(L.ask(lambda s: req_write(s, k, i, off, data, pk), 6)))
        elif cmd == "dspr":
            sp, addr, n = (1 if argv[1].lower() == "y" else 0), num(argv[2]), num(argv[3])
            d = dec_dspr(L.ask(lambda s: req_dspr(s, sp, addr, n), 3)); print(d["status"], [f"{w:06x}" for w in d["words"]])
        elif cmd == "dspw":
            addr, v = num(argv[1]), num(argv[2])
            print(dec_write(L.ask(lambda s: req_dspw(s, addr, v), 9)))
        elif cmd == "dspx":
            src, n = num(argv[1]), num(argv[2])
            d = dec_dspx(L.ask(lambda s: req_dspx(s, src, n), 8)); print(d["status"], [f"{w:04x}" for w in d["samples"]])
        elif cmd == "capture":
            ln = dec_dspr(L.ask(lambda s: req_dspr(s, 0, X_LEN, 1), 3))["words"][0]
            print(f"capture length {ln} samples ({ln / 48000:.2f} s)"); out = []
            while len(out) < ln:
                d = dec_dspx(L.ask(lambda s, o=len(out): req_dspx(s, CAP_BASE + o, min(NX, ln - o)), 8))
                if d["status"]: raise SystemExit(f"dspx status {d['status']} at {len(out)}")
                out += d["samples"]
                if len(out) % 4800 < NX: print(f"{len(out)} / {ln}", flush=True)
            open(argv[1], "wb").write(wav16(out)); print(f"{argv[1]}: {len(out)} samples")
        elif cmd == "watch":
            addr = num(argv[1]); f = WFUNC[argv[2]] if len(argv) > 2 else WFUNC["read"]; m = num(argv[3]) if len(argv) > 3 else 0
            d = dec_watch(L.ask(lambda s: req_watch(s, addr, f, m), 10))
            print({k: (hex(v) if isinstance(v, int) else v) for k, v in d.items()}, f"(DWT comparators: {d['dwt_ctrl'] >> 28})")
        elif cmd == "wlog":
            d = dec_wlog(L.ask(req_wlog, 12)); print(f"status {d['status']}, hits {d['hits']}")
            for pc, lr in d["pcs"]: print(f"  pc {pc:#010x}  lr {lr:#010x}")
        elif cmd == "poke":
            if "--yes" not in argv: raise SystemExit("poke writes the device's RAM: add --yes")
            a = [x for x in argv if x != "--yes"]; addr, data = num(a[1]), bytes.fromhex(a[2])
            print(dec_write(L.ask(lambda s: req_poke(s, addr, data), 11)))
        elif cmd in ("step", "seqwatch"):
            t, pt, st = num(argv[1]), num(argv[2]), num(argv[3])
            word = lambda ad: int.from_bytes(dec_mem(L.ask(lambda s: req_mem(s, ad, 4), 2))["data"], "little")
            rec = word(GATE_OBJ + 0xC + 4 * t); base = word(rec + 0x48); addr = base + PAT_SZ * pt + STEP_SZ * st
            data = dec_mem(L.ask(lambda s: req_mem(s, addr, STEP_SZ), 2))["data"]
            print(f"track {t} recorder {rec:#x} patterns {base:#x}: pattern {pt} step {st} at {addr:#x}")
            print(f"  mask {data[0]:#04x} probability {data[1]} [2..3] {data[2]:#04x} {data[3]:#04x}  units", " ".join(data[4 + 4 * u:8 + 4 * u].hex() for u in range(6)))
            if cmd == "seqwatch":
                b = num(argv[4]) if len(argv) > 4 else 4; f = WFUNC[argv[5]] if len(argv) > 5 else WFUNC["read"]
                d = dec_watch(L.ask(lambda s: req_watch(s, addr + b, f), 10))
                print(f"watching {addr + b:#x} ({[k for k, v in WFUNC.items() if v == f][0]}): status {d['status']}, FUNCTION0 {d['function0']:#x}, log {d['log']:#x}")
        elif cmd == "delpack":
            if "--yes" not in argv: raise SystemExit("delpack deletes a whole pack from the SD card: add --yes")
            pk = num([x for x in argv if x != "--yes"][1])
            print(dec_delpack(L.ask(lambda s: req_del(s, 1, 0, pk), 7, timeout=60)))
        elif cmd in ("put", "del"):
            if "--yes" not in argv: raise SystemExit(f"{cmd} changes the SD card: add --yes (and use a test pack)")
            a = [x for x in argv if x != "--yes"]
            k, i = kind_of(a[1]), num(a[2])
            if cmd == "del":
                pk = num(a[3]) if len(a) > 3 else 0x7F
                print(dec_del(L.ask(lambda s: req_del(s, k, i, pk), 7)))
            else:
                data = open(a[3], "rb").read(); pk = num(a[4]) if len(a) > 4 else 0x7F
                for off in range(0, len(data), NMAX):
                    d = dec_write(L.ask(lambda s, o=off: req_write(s, k, i, o, data[o:o + NMAX], pk), 6))
                    if d["status"]: raise SystemExit(f"write status {d['status']} at {off}")
                    if off % 4096 == 0: print(f"{off} / {len(data)}", flush=True)
                print(f"{len(data)} bytes written")
        else:
            print(__doc__); return 1
    finally:
        L.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
