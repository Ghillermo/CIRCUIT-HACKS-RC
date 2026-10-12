"""Watch ARM memory words on a Circuit Tracks running the remote diagnostics (rdiag), printing every change: a way to find which RAM byte a button or a
pad changes while the user presses it.

    python tools/ctwatch.py SECONDS ADDR[:LEN] [ADDR[:LEN] ...]       (LEN in bytes, default 4, <= 64)
"""
from __future__ import annotations
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ctremote as CR  # noqa: E402


def main(argv):
    secs = float(argv[0])
    areas = []
    for a in argv[1:]:
        ad, _, ln = a.partition(":")
        areas.append((int(ad, 0), int(ln, 0) if ln else 4))
    L = CR.Link()
    last = {}
    t0 = time.time()
    try:
        while time.time() - t0 < secs:
            for ad, ln in areas:
                d = CR.dec_mem(L.ask(lambda s, a=ad, n=ln: CR.req_mem(s, a, n), 2))
                if last.get(ad) != d["data"]:
                    print(f"{time.time() - t0:6.1f}s  {ad:08x}  {d['data'].hex(' ')}", flush=True)
                    last[ad] = d["data"]
            time.sleep(0.1)
    finally:
        L.close()


if __name__ == "__main__":
    main(sys.argv[1:])
