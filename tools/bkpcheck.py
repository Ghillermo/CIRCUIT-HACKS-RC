"""S725D: the backup SRAM over USB (blackbox.use_memrd): its header and how many pattern words differ from what icache.use_bkp wrote at the last
reset (a differing word = something else wrote there since).
    python tools/bkpcheck.py"""
import struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bbread as BR
import ctremote as CR
import icache as I


def main():
    link = CR.Link()
    try: d = BR.read(link, I.BKPSRAM, 4096)[:4096]
    finally: link.close()
    w = struct.unpack("<8I", d[:32])
    print("magic %08x  boots %d  AHB1ENR %08x  APB1ENR %08x  PWR_CR1 %08x  RCC_CSR %08x" % w[:6])
    print("at that reset: pattern words changed since the boot before =", "none found (no header: lost)" if w[6] == 0xFFFFFFFF else w[6],
          "| readback errors right after writing =", w[7])
    pat = struct.unpack("<1008I", d[64:4096])
    bad = [i for i in range(1008) if pat[i] != (I.BKP_SEED + i * I.BKP_K) & 0xFFFFFFFF]
    print("now: pattern words changed since that reset =", len(bad), ("first at + %d" % (64 + 4 * bad[0])) if bad else "")
    return 0 if w[0] == I.BKP_MAGIC and not bad and w[7] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
