"""Can incoming MIDI leave an impossible value in a pattern (a note step's probability > 7, a unit velocity > 127, a unit mask with bits 6-7, a drum
velocity > 127: the values behind the 5.63 / 5.64 crashes that paintguard now skips)?  Through the real MIDI input (0x08051720), with
tools/bytewatch.py's write hook on the session's pattern memory (it names the writing code): every CC on channels 1-16 at values 0, 1, 7, 8, 31, 32,
63, 64, 100, 127; notes 0-127 on every channel at velocities 1, 64, 127 (on + off); NRPNs (value 0, 32, 127) on the given channels, MSB 0-127 x LSB
0-127 (or --msb N for MSBs 0..N-1).  Every 512 messages the main loop's three senders run (and a fault is reported).  With --rec the transport
store's record flag is set first.

    python tools/emu_midistress.py IMAGE.bin [--nrpn 16,10] [--msb 4] [--rec]
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc05 as X  # noqa: E402
import bytewatch as BW  # noqa: E402
from unicorn import UC_HOOK_MEM_WRITE  # noqa: E402

SENDERS = (0x080214F4, 0x08021544, 0x08021578)


def main(img, nrpn_ch, msb_n, rec):
    e = X.E(img)
    if rec: e.recording(True)
    e.uc.hook_add(UC_HOOK_MEM_WRITE, BW._hook_write, e, BW.LO, BW.HI)
    m = 0x20060100
    n = [0]; faults = []
    def send(st, d1, d2, label):
        e.uc.mem_write(m, bytes([st, d1, d2, 0]))
        try: e.call(0x08051720, X.CTX, m, maxins=400000)
        except Exception as ex: faults.append((label, str(ex)[:60]))
        n[0] += 1
        if n[0] % 512 == 0:
            for s in SENDERS:
                try: e.call(s, maxins=300000)
                except Exception as ex: faults.append((f"sender {s:#x} after {label}", str(ex)[:60]))
            e.uc.mem_write(0x20006A0C, bytes(4))
    for ch in range(16):
        for cc in range(128):
            for v in (0, 1, 7, 8, 31, 32, 63, 64, 100, 127):
                send(0xB0 | ch, cc, v, f"ch{ch + 1} CC{cc}={v}")
        for note in range(128):
            for v in (1, 64, 127):
                send(0x90 | ch, note, v, f"ch{ch + 1} note {note} v{v}"); send(0x80 | ch, note, 0, f"ch{ch + 1} off {note}")
        print(f"ch{ch + 1}: CCs and notes done ({sum(f['n'] for f in BW.FINDS.values())} bad writes so far)", flush=True)
    for ch in nrpn_ch:
        for msb in range(msb_n):
            for lsb in range(128):
                for v in (0, 32, 127):
                    for cc, d in ((99, msb), (98, lsb), (6, v)):
                        send(0xB0 | (ch - 1), cc, d, f"ch{ch} NRPN {msb}:{lsb}={v}")
            if msb % 32 == 31: print(f"ch{ch} NRPN MSB {msb} done", flush=True)
    print(f"{n[0]} messages, {BW.WRITES[0]} writes into the patterns")
    if BW.FINDS:
        for (pc, lr), f in BW.FINDS.items():
            print(f"BAD VALUE: {f['first']} x{f['n']}, PC {pc:#x} LR {lr:#x} {'(ours)' if f['ours'] else '(stock)'}")
    else:
        print("no impossible value written into any pattern")
    print("faults:", faults[:12] if faults else "none")


if __name__ == "__main__":
    a = sys.argv[1:]
    ch = [int(x) for x in a[a.index("--nrpn") + 1].split(",")] if "--nrpn" in a else [16, 10]
    msb = int(a[a.index("--msb") + 1]) if "--msb" in a else 128
    main(Path(a[0]).read_bytes(), ch, msb, "--rec" in a)
