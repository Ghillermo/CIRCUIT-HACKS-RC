"""Install a firmware .syx from the command line, as tools/ct_uploader.html does (Components' pull protocol): the device must be in bootloader mode
(Scales + Preset + Note at power-on: its port is «Circuit Tracks Boot»).  Only files whose SHA-256 is in the uploader's KNOWN list are sent.
INIT and HEADER, then one message per 0x72 request; 0x73 = the status (1: press Play on the device to confirm; 127: success).

    python tools/ctflash.py firmware/<dir>/circuittracks-4486-<NAME>.syx
"""
from __future__ import annotations
import hashlib, re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ctremote as CR

NOV = bytes([0xF0, 0x00, 0x20, 0x29, 0x00])
STATUS = {0: "update start", 1: "waiting: PRESS PLAY on the Circuit Tracks", 16: "cancelled on the device", 17: "confirmation timed out",
          124: "FAILED (not viable)", 125: "received (not viable)", 126: "FAILED (CRC)", 127: "SUCCESS"}


def main(a):
    data = Path(a[0]).read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    known = Path(__file__).with_name("ct_uploader.html").read_text(encoding="utf-8")
    if f'"{sha}"' not in known: raise SystemExit(f"{sha} is not in the uploader's KNOWN list: not sent")
    msgs, i = [], 0
    while i < len(data):
        s = data.index(0xF0, i); e = data.index(0xF7, s); msgs.append(data[s:e + 1]); i = e + 1
    ins, outs = CR.ports()
    if not any("boot" in n.lower() for n in outs): raise SystemExit(f"not in bootloader mode (ports {outs}): power on holding Scales + Preset + Note")
    link = CR.Link("Circuit Tracks Boot")
    nxt, last = 0, -1
    def send():
        nonlocal nxt
        link.send(msgs[nxt]); nxt += 1
    print(f"{len(msgs)} messages -> Circuit Tracks Boot ({sha[:12]}…)")
    try:
        send()
        if nxt < len(msgs) and msgs[nxt][5] == 0x7C: send()
        t = time.time(); acc = b""; deadline = 25
        while time.time() - t < deadline:
            try: chunk, p1 = link.q.get(timeout=0.05)
            except Exception: continue
            link._readd(p1); acc += chunk
            while b"\xF0" in acc and b"\xF7" in acc[acc.index(b"\xF0"):]:
                s = acc.index(b"\xF0"); e = acc.index(b"\xF7", s); d, acc = acc[s:e + 1], acc[e + 1:]
                if d[:5] != NOV: continue
                if d[5] == 0x72:
                    n = d[6] + (d[7] << 7) + (d[8] << 14) if len(d) == 10 else (d[13] + (d[12] << 4) + (d[11] << 8) if len(d) == 15 else None)
                    if n is not None and (n > last or n == 0) and nxt < len(msgs):
                        last = n; send(); t = time.time(); deadline = 10 if nxt < len(msgs) else 30
                        if nxt % 200 == 0 or nxt == len(msgs): print(f"  {nxt}/{len(msgs)}")
                elif d[5] == 0x73 and len(d) == 10:
                    c = d[6]; print(f"  status {c}: {STATUS.get(c, '?')}")
                    if c == 127: print("installed: the device restarts"); return 0
                    if c in (16, 17, 124, 126): print("rejected: the firmware is unchanged"); return 1
                    t = time.time(); deadline = 30
        print("timed out"); return 1
    finally:
        link.close()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
