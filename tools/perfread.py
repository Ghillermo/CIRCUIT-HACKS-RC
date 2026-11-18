"""Performance state of a running Circuit Tracks (S702D: blackbox.use_memrd), read over USB: the Cortex-M7 caches (SCB CCR, CACR), the TCM
setup, the flash wait states / ART / prefetch (FLASH ACR), the clocks (RCC, PWR overdrive), the SysTick reload (= HCLK / tick rate) and whether the
DWT cycle counter runs.  Each block is its own request (the reads are byte reads: a register that faulted would stop the device; the safest first).

    python tools/perfread.py
"""
from __future__ import annotations
import struct, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ctremote as CR
import bbread as BR

BLOCKS = (("SCB", 0xE000ED00, 64), ("SysTick", 0xE000E010, 16), ("RCC", 0x40023800, 64), ("FLASH", 0x40023C00, 32),
          ("PWR", 0x40007000, 16), ("TCM/cache ctl", 0xE000EF80, 32), ("DEMCR", 0xE000EDF0, 16), ("DWT", 0xE0001000, 16))


def w(d, off): return struct.unpack_from("<I", d, off)[0]


def main():
    link = CR.Link(); got = {}
    try:
        for name, addr, n in BLOCKS:
            try: got[name] = BR.read(link, addr, n)
            except SystemExit as e: print(f"{name}: no reply ({e}) -- stopping"); break
            print(f"{name:14s} {addr:#010x}  " + " ".join(f"{w(got[name], i):08x}" for i in range(0, n, 4)))
        if "DWT" in got:
            time.sleep(0.2); again = BR.read(link, 0xE0001000, 16); print(f"{'DWT again':14s} {0xE0001000:#010x}  " + " ".join(f"{w(again, i):08x}" for i in range(0, 16, 4)))
    finally:
        try: link.close()
        except Exception: pass
    s = got.get("SCB")
    if s:
        ccr = w(s, 0x14)
        print(f"\nCPUID {w(s, 0):#010x}  VTOR {w(s, 8):#010x}  CCR {ccr:#010x}: I-cache {'ON' if ccr >> 17 & 1 else 'off'}, D-cache {'ON' if ccr >> 16 & 1 else 'off'}, "
              f"branch prediction {'ON' if ccr >> 18 & 1 else 'off'}")
    f = got.get("FLASH")
    if f:
        acr = w(f, 0); print(f"FLASH ACR {acr:#010x}: {acr & 15} wait states, ART {'ON' if acr >> 9 & 1 else 'off'}, prefetch {'ON' if acr >> 8 & 1 else 'off'}")
    r = got.get("RCC")
    if r:
        cr, pll, cfgr = w(r, 0), w(r, 4), w(r, 8)
        m, n, p = pll & 63, pll >> 6 & 511, 2 * ((pll >> 16 & 3) + 1); src = "HSE" if pll >> 22 & 1 else "HSI"
        sw = cfgr >> 2 & 3
        print(f"RCC CR {cr:#010x} PLLCFGR {pll:#010x} CFGR {cfgr:#010x}: SYSCLK = {['HSI', 'HSE', 'PLL', '?'][sw]}; PLL = {src} / {m} x {n} / {p} "
              f"(HSI 16 MHz -> {16e6 / max(m, 1) * n / p / 1e6:.1f} MHz; HSE x MHz -> x * {n / max(m, 1) / p:.3f}); AHB prescale bits {cfgr >> 4 & 15:#x}")
    t = got.get("SysTick")
    if t:
        ctrl, load = w(t, 0), w(t, 4)
        print(f"SysTick CTRL {ctrl:#x} LOAD {load}: at a 1 kHz tick, HCLK{' / 8' if not ctrl >> 2 & 1 else ''} = {(load + 1) / 1e3:.1f} MHz")
    p = got.get("PWR")
    if p: c1 = w(p, 0); print(f"PWR CR1 {c1:#010x}: overdrive {'ON' if c1 >> 16 & 1 else 'off'}, voltage scale {c1 >> 14 & 3}")
    c = got.get("TCM/cache ctl")
    if c: print(f"ITCMCR {w(c, 0x10):#x}  DTCMCR {w(c, 0x14):#x}  AHBPCR {w(c, 0x18):#x}  CACR {w(c, 0x1C):#x}")
    if "DEMCR" in got: print(f"DEMCR {w(got['DEMCR'], 0xC):#010x} (TRCENA {'on' if w(got['DEMCR'], 0xC) >> 24 & 1 else 'off'})")


if __name__ == "__main__":
    main()
