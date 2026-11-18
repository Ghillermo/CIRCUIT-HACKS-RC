"""The hardware study on a running Circuit Tracks with S703D (blackbox.use_memrd / use_memrdw / use_samp, icache.use_dwt), over USB (the user,
2026-11-18: «make a diag build for all those»): the clock tree (PLL, PLLI2S, PLLSAI, prescalers, kernel clock selections: what a faster CPU clock
would have to keep the same), the peripherals that are clocked, the NVIC lines on, the DMA streams that run and their memory buffers (what a data
cache would have to leave uncached), the timers that count, CRC / RNG / backup SRAM / QUADSPI state, the CPU's real clock from the cycle counter,
and the task shares + hot code from the SysTick sampler.

Peripheral registers are read as whole words (request byte 13 = the word count) and never a data register (SPI / SAI / UART / QUADSPI / RNG DR:
a read pops a FIFO).  Writes nothing.

    python tools/hwdiag.py [--secs 10] [--manifest firmware/s703d/manifest.json] [--out report.json]
"""
from __future__ import annotations
import argparse, bisect, json, struct, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ctremote as CR

SAMP = 0x2004F600


def readw(link, addr, n):
    """n words (<= 16) at addr, read with ldr on the device"""
    assert 1 <= n <= 16 and addr & 3 == 0
    link.seq = (link.seq + 1) & 0x7F
    a7 = [(addr >> s) & 0x7F for s in (28, 21, 14, 7, 0)]
    link.send(bytes([0xF0, 0x7D, 0x43, 0x54, 0x01, link.seq, 0, 0x00]) + bytes(a7) + bytes([n]) + bytes(122) + bytes([0xF7]))
    t = time.time(); acc = b""
    while time.time() - t < 3:
        try: chunk, p1 = link.q.get(timeout=0.05)
        except Exception: continue
        link._readd(p1); acc += chunk
        while b"\xF0" in acc and b"\xF7" in acc[acc.index(b"\xF0"):]:
            s = acc.index(b"\xF0"); e = acc.index(b"\xF7", s); msg, acc = acc[s:e + 1], acc[e + 1:]
            if msg[:5] == bytes([0xF0, 0x7D, 0x43, 0x54, 0x41]) and msg[5] == link.seq:
                q = msg[8:-1]; d = bytes(q[i] << 4 | q[i + 1] for i in range(0, 128, 2))
                return list(struct.unpack_from(f"<{n}I", d))
    raise SystemExit(f"no reply for {addr:#x}")


def block(link, addr, nwords):
    out = []
    while nwords > 0:
        k = min(16, nwords); out += readw(link, addr, k); addr += 4 * k; nwords -= k
    return out


def rd(link, addr, nbytes):
    return b"".join(struct.pack("<I", x) for x in block(link, addr, (nbytes + 3) // 4))[:nbytes]


AHB1 = {0: "GPIOA", 1: "GPIOB", 2: "GPIOC", 3: "GPIOD", 4: "GPIOE", 5: "GPIOF", 6: "GPIOG", 7: "GPIOH", 8: "GPIOI", 12: "CRC", 18: "BKPSRAM",
        20: "DTCMRAM", 21: "DMA1", 22: "DMA2", 23: "DMA2D", 25: "ETHMAC", 29: "OTGHS", 30: "OTGHSULPI"}
AHB2 = {0: "DCMI", 4: "CRYP", 5: "HASH", 6: "RNG", 7: "OTGFS"}
AHB3 = {0: "FMC", 1: "QSPI"}
APB1 = {0: "TIM2", 1: "TIM3", 2: "TIM4", 3: "TIM5", 4: "TIM6", 5: "TIM7", 6: "TIM12", 7: "TIM13", 8: "TIM14", 9: "LPTIM1", 11: "WWDG", 14: "SPI2",
        15: "SPI3", 16: "SPDIFRX", 17: "USART2", 18: "USART3", 19: "UART4", 20: "UART5", 21: "I2C1", 22: "I2C2", 23: "I2C3", 24: "I2C4", 25: "CAN1",
        26: "CAN2", 27: "CEC", 28: "PWR", 29: "DAC", 30: "UART7", 31: "UART8"}
APB2 = {0: "TIM1", 1: "TIM8", 4: "USART1", 5: "USART6", 8: "ADC1", 9: "ADC2", 10: "ADC3", 11: "SDMMC1", 12: "SPI4", 13: "SPI1", 14: "SYSCFG",
        16: "TIM9", 17: "TIM10", 18: "TIM11", 20: "SPI5", 21: "SPI6", 22: "SAI1", 23: "SAI2", 26: "LTDC"}
PERIPH = {0x40013000: "SPI1", 0x40003800: "SPI2", 0x40003C00: "SPI3", 0x40013400: "SPI4", 0x40015000: "SPI5", 0x40015400: "SPI6",
          0x40015800: "SAI1", 0x40015C00: "SAI2", 0x40011000: "USART1", 0x40004400: "USART2", 0x40004800: "USART3", 0x40004C00: "UART4",
          0x40005000: "UART5", 0x40011400: "USART6", 0x40007800: "UART7", 0x40007C00: "UART8", 0x40012C00: "SDMMC1", 0xA0001000: "QUADSPI",
          0x40007400: "DAC", 0x40012000: "ADC1", 0x40003000: "IWDG"}
TIMERS = {"TIM1": 0x40010000, "TIM2": 0x40000000, "TIM3": 0x40000400, "TIM4": 0x40000800, "TIM5": 0x40000C00, "TIM6": 0x40001000,
          "TIM7": 0x40001400, "TIM8": 0x40010400, "TIM9": 0x40014000, "TIM10": 0x40014400, "TIM11": 0x40014800, "TIM12": 0x40001800,
          "TIM13": 0x40001C00, "TIM14": 0x40002000}
SPIS = {"SPI1": 0x40013000, "SPI2": 0x40003800, "SPI3": 0x40003C00, "SPI4": 0x40013400, "SPI5": 0x40015000, "SPI6": 0x40015400}
UARTS = {"USART1": 0x40011000, "USART2": 0x40004400, "USART3": 0x40004800, "UART4": 0x40004C00, "UART5": 0x40005000, "USART6": 0x40011400,
         "UART7": 0x40007800, "UART8": 0x40007C00}


def bits(v, names): return [n for b, n in names.items() if v >> b & 1]


def periph_of(a):
    for base, n in PERIPH.items():
        if base <= a < base + 0x400: return f"{n}+{a - base:#x}"
    return f"{a:#x}"


def labels_of(man):
    out = []
    if man:
        for mod, v in man["report"].items():
            if isinstance(v, dict) and isinstance(v.get("labels"), dict):
                for k, a in v["labels"].items():
                    try: out.append((int(a, 16), f"{mod}.{k}"))
                    except Exception: pass
    out.sort(); return out


def name_pc(pc, labs, keys):
    if pc < 0x0805CDDC or not labs: return f"stock {pc & ~0xFF:#x}..+0xff" if 0x08010000 <= pc < 0x0805CDDC else f"{pc & ~0xFF:#x}"
    i = bisect.bisect_right(keys, pc) - 1
    return f"{labs[i][1]}+{pc - labs[i][0]:#x}" if i >= 0 else f"{pc:#x}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--secs", type=float, default=10.0, help="how long to sample the tasks / PCs (play the heavy patch meanwhile)")
    ap.add_argument("--manifest", type=Path, default=Path(__file__).resolve().parents[1] / "firmware/s703d/manifest.json")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    man = json.loads(a.manifest.read_text()) if a.manifest.exists() else None
    labs = labels_of(man); keys = [x[0] for x in labs]
    link = CR.Link(); R = {}
    try:
        R["scb"] = block(link, 0xE000ED00, 16); R["mpu"] = block(link, 0xE000ED90, 2)
        R["rcc"] = block(link, 0x40023800, 37); R["pwr"] = block(link, 0x40007000, 4); R["flash"] = block(link, 0x40023C00, 7)
        R["nvic_iser"] = block(link, 0xE000E100, 8); R["nvic_iabr"] = block(link, 0xE000E300, 8)
        R["systick"] = block(link, 0xE000E010, 3)
        R["dma"] = {f"DMA{d + 1}": block(link, base, 2) + block(link, base + 0x10, 48) for d, base in enumerate((0x40026000, 0x40026400))}
        R["crc"] = block(link, 0x40023000, 6); R["rng"] = block(link, 0x50060800, 2)
        R["qspi"] = block(link, 0xA0001000, 3) + [0] + block(link, 0xA0001010, 4)
        R["iwdg"] = block(link, 0x40003004, 3)
        R["sdmmc"] = block(link, 0x40012C00, 2)
        R["sai"] = {n: block(link, b_, 8) + block(link, b_ + 0x24, 7) for n, b_ in (("SAI1", 0x40015800), ("SAI2", 0x40015C00))}
        R["spi"] = {n: block(link, b_, 3) + block(link, b_ + 0x1C, 2) for n, b_ in SPIS.items()}
        R["uart"] = {n: block(link, b_, 4) for n, b_ in UARTS.items()}
        R["tim"] = {n: block(link, b_, 12) for n, b_ in TIMERS.items()}
        c0 = readw(link, 0xE0001004, 1)[0]; t0 = time.perf_counter()
        # the sampler: totals before / after, the PC ring read as often as possible
        s0 = block(link, SAMP, 34); pcs = []; last = s0[1]; t_end = time.time() + a.secs
        while time.time() < t_end:
            idx = readw(link, SAMP + 4, 1)[0]; ring = block(link, SAMP + 0x100, 64)
            new = min(idx - last, 64)
            for j in range(idx - new, idx): pcs.append(ring[j & 63])
            last = idx
        s1 = block(link, SAMP, 34)
        c1 = readw(link, 0xE0001004, 1)[0]; t1 = time.perf_counter()
        R["cyc"] = [c0, c1, t1 - t0]
        R["samp0"], R["samp1"], R["pcs"] = s0, s1, pcs
        tcbs = [s1[2 + 2 * i] for i in range(16) if s1[2 + 2 * i] >= 0x20000000]
        R["tcb_names"] = {}
        for t in tcbs:
            raw = rd(link, t + 0x34, 16); R["tcb_names"][t] = raw.split(b"\0")[0].decode("latin-1", "replace")
    finally:
        try: link.close()
        except Exception: pass
    report(R, labs, keys)
    if a.out: a.out.write_text(json.dumps(R, indent=1, default=str))


def report(R, labs, keys):
    rcc = R["rcc"]; cr, pll, cfgr = rcc[0], rcc[1], rcc[2]
    m, n, p, q = pll & 63, pll >> 6 & 511, 2 * ((pll >> 16 & 3) + 1), pll >> 24 & 15
    src = "HSE" if pll >> 22 & 1 else "HSI"
    st = R["systick"]; hclk = (st[1] + 1) * 1000 if st[0] & 4 else None
    print("== clocks")
    print(f"RCC CR {cr:#010x} (HSE {'on' if cr >> 16 & 1 else 'off'}{', bypass' if cr >> 18 & 1 else ''}; PLL {'on' if cr >> 24 & 1 else 'off'}; "
          f"PLLI2S {'on' if cr >> 26 & 1 else 'off'}; PLLSAI {'on' if cr >> 28 & 1 else 'off'})")
    if hclk:
        vin = hclk * p / n                                                             # the PLL input = HCLK x P / N (AHB / 1 assumed)
        print(f"PLL {src} / {m} x {n} / P {p}, / Q {q}: HCLK {hclk / 1e6:.1f} MHz (SysTick) -> PLL input {vin / 1e6:.3f} MHz, {src} {vin * m / 1e6:.2f} MHz, "
              f"VCO {vin * n / 1e6:.1f} MHz, PLL48 (Q) {vin * n / max(q, 1) / 1e6:.2f} MHz")
    hpre, ppre1, ppre2 = cfgr >> 4 & 15, cfgr >> 10 & 7, cfgr >> 13 & 7
    dv = lambda x, base: 1 if x < base else 2 ** (x - base + 1)
    ah = dv(hpre, 8); a1 = dv(ppre1, 4); a2 = dv(ppre2, 4)
    print(f"CFGR {cfgr:#010x}: AHB / {ah}, APB1 / {a1}, APB2 / {a2}" + (f" -> APB1 {hclk / a1 / 1e6:.1f} MHz, APB2 {hclk / a2 / 1e6:.1f} MHz" if hclk else "")
          + f"; MCO1 sel {cfgr >> 21 & 3}, MCO2 sel {cfgr >> 30 & 3}, I2SSRC {cfgr >> 23 & 1}")
    i2s, sai, d1, d2 = rcc[0x84 // 4], rcc[0x88 // 4], rcc[0x8C // 4], rcc[0x90 // 4]
    print(f"PLLI2S {i2s:#010x}: N {i2s >> 6 & 511}, P {2 * ((i2s >> 16 & 3) + 1)}, Q {i2s >> 24 & 15}, R {i2s >> 28 & 7}")
    print(f"PLLSAI {sai:#010x}: N {sai >> 6 & 511}, P {2 * ((sai >> 16 & 3) + 1)}, Q {sai >> 24 & 15}, R {sai >> 28 & 7}")
    print(f"DCKCFGR1 {d1:#010x}: PLLI2SDIVQ {(d1 & 31) + 1}, PLLSAIDIVQ {(d1 >> 8 & 31) + 1}, SAI1SEL {d1 >> 20 & 3}, SAI2SEL {d1 >> 22 & 3}, TIMPRE {d1 >> 24 & 1}")
    print(f"DCKCFGR2 {d2:#010x}: USART1..8 sel {[d2 >> 2 * k & 3 for k in range(8)]}, CK48MSEL {d2 >> 27 & 1} ({'PLLSAI P' if d2 >> 27 & 1 else 'PLL Q'}), "
          f"SDMMC1SEL {d2 >> 28 & 1}")
    pw = R["pwr"]; fl = R["flash"]
    print(f"PWR CR1 {pw[0]:#010x}: voltage scale {pw[0] >> 14 & 3}, overdrive {'on' if pw[0] >> 16 & 1 else 'off'} / switch {'on' if pw[0] >> 17 & 1 else 'off'}; "
          f"CSR1 {pw[1]:#010x} (ODRDY {pw[1] >> 16 & 1}, VOSRDY {pw[1] >> 14 & 1}, BRE {pw[1] >> 9 & 1})")
    print(f"FLASH ACR {fl[0]:#x}: {fl[0] & 15} wait states, ART {fl[0] >> 9 & 1}, prefetch {fl[0] >> 8 & 1}; OPTCR {fl[5]:#010x}")
    c0, c1, dt = R["cyc"]
    print(f"cycle counter: {(c1 - c0) & 0xFFFFFFFF} cycles in {dt:.3f} s = {((c1 - c0) & 0xFFFFFFFF) / dt / 1e6:.1f} MHz (with the USB round trips' error)")
    print("\n== clocked peripherals")
    for nm, off, tab in (("AHB1", 0x30, AHB1), ("AHB2", 0x34, AHB2), ("AHB3", 0x38, AHB3), ("APB1", 0x40, APB1), ("APB2", 0x44, APB2)):
        print(f"{nm} {rcc[off // 4]:#010x}: {', '.join(bits(rcc[off // 4], tab))}")
    print(f"BDCR {rcc[0x70 // 4]:#010x}  CSR {rcc[0x74 // 4]:#010x}")
    print("\n== NVIC lines enabled:", [32 * k + b for k in range(8) for b in range(32) if R["nvic_iser"][k] >> b & 1],
          " active now:", [32 * k + b for k in range(8) for b in range(32) if R["nvic_iabr"][k] >> b & 1])
    print("\n== DMA streams (enabled or configured)")
    for d, v in R["dma"].items():
        for s in range(8):
            crs, ndt, par, m0, m1, fcr = v[2 + 6 * s:8 + 6 * s]
            if not crs and not ndt: continue
            print(f"{d} S{s}: {'EN ' if crs & 1 else 'off'} ch {crs >> 25 & 7} dir {['P->M', 'M->P', 'M->M', '?'][crs >> 6 & 3]} circ {crs >> 8 & 1} dbm {crs >> 18 & 1} "
                  f"psize {8 << (crs >> 11 & 3)} msize {8 << (crs >> 13 & 3)} ndtr {ndt} par {periph_of(par)} m0 {m0:#010x} m1 {m1:#010x} fifo {fcr:#x}")
    print("\n== timers counting")
    for nmt, v in R["tim"].items():
        if v[0] & 1: print(f"{nmt}: CR1 {v[0]:#x} DIER {v[3]:#x} PSC {v[10]} ARR {v[11]}")
    print("\n== serial / audio")
    for nmt, v in R["spi"].items():
        if v[0] or v[3]: print(f"{nmt}: CR1 {v[0]:#06x} CR2 {v[1]:#06x} SR {v[2]:#06x} I2SCFGR {v[3]:#06x} I2SPR {v[4]:#06x} (baud div {2 << (v[0] >> 3 & 7)})")
    for nmt, v in R["uart"].items():
        if v[0]: print(f"{nmt}: CR1 {v[0]:#x} CR3 {v[2]:#x} BRR {v[3]}")
    for nmt, v in R["sai"].items():
        if v[1] or v[8]: print(f"{nmt}: GCR {v[0]:#x} A CR1 {v[1]:#x} CR2 {v[2]:#x} FRCR {v[3]:#x} SLOTR {v[4]:#x} | B CR1 {v[8]:#x} CR2 {v[9]:#x}")
    print(f"QUADSPI: CR {R['qspi'][0]:#010x} DCR {R['qspi'][1]:#010x} (flash size 2^{(R['qspi'][1] >> 16 & 31) + 1} B) SR {R['qspi'][2]:#x} CCR {R['qspi'][5]:#010x}")
    print(f"SDMMC1: POWER {R['sdmmc'][0]:#x} CLKCR {R['sdmmc'][1]:#x}   IWDG PR {R['iwdg'][0]} RLR {R['iwdg'][1]}")
    print(f"CRC: DR {R['crc'][0]:#010x} CR {R['crc'][2]:#x} INIT {R['crc'][4]:#x} POL {R['crc'][5]:#x}   RNG: CR {R['rng'][0]:#x} SR {R['rng'][1]:#x}")
    print(f"MPU TYPE {R['mpu'][0]:#x} CTRL {R['mpu'][1]:#x}   SCB CCR {R['scb'][5]:#010x}")
    s0, s1 = R["samp0"], R["samp1"]
    tot = s1[0] - s0[0]
    print(f"\n== task shares over {tot} SysTick samples (sampled on the tick)")
    before = {s0[2 + 2 * i]: s0[3 + 2 * i] for i in range(16)}
    rows = sorted(((s1[3 + 2 * i] - before.get(s1[2 + 2 * i], 0), s1[2 + 2 * i]) for i in range(16) if s1[2 + 2 * i]), reverse=True)
    for c, t in rows:
        nm = R["tcb_names"].get(t, f"handler {t & 0x1FF}" if t < 0x1000 else "?")
        print(f"{100 * c / max(tot, 1):5.1f} %  {t:#010x}  {nm}")
    from collections import Counter
    cnt = Counter(name_pc(pc, labs, keys).rsplit("+", 1)[0] for pc in R["pcs"])
    print(f"\n== hot code ({len(R['pcs'])} PCs)")
    for k_, c in cnt.most_common(25): print(f"{100 * c / max(len(R['pcs']), 1):5.1f} %  {k_}")


if __name__ == "__main__":
    main()
