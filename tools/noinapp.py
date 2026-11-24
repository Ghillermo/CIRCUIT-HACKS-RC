"""(2026-11-24) The running firmware never takes an install: only the bootloader (Scales + Preset + Note at power-on) does.

The running firmware has its own updater (SysEx 0x71 init, 0x7C header, 0x72 data, 0x73 end; handlers 0x08038CFC..0x08039102). It writes the
install into the NOR through the same request queue the file system and the USB drive use (device 0x2000AC94: queue at [dev + 8], a pointer
to the caller's stack request; one shared busy flag [dev + 0x10] bit 0 and a counter [dev + 0xC] capped at [dev + 0xD] = 1: with two users at
once the flag can release a caller whose request is still queued and every later request runs another's stale stack request). On the
user's unit (2026-11-24, after installs sent to the running firmware) the internal file system's first 0x4D000 bytes held 32-byte pieces of
the Alpha 7 images: pack 0 and the device settings lost.

The header handler 0x08039088 (its first instruction `cmp r0, #0`) becomes `bx lr`: the header is ignored, nothing is erased or written, the
init / data / end messages find no update in progress. The bootloader's own updater is a different program and is not touched."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

AT = 0x08039088
STOCK = bytes([0x00, 0x28])                            # cmp r0, #0
OURS = bytes([0x70, 0x47])                             # bx lr


def install(img, report):
    import ct_fw
    o = AT - ct_fw.APP_BASE
    stock = (Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    assert bytes(stock[o:o + 6]) == bytes.fromhex("002870b50c46"), "the stock's header handler"
    assert bytes(img[o:o + 2]) == STOCK, f"{AT:#x}: {bytes(img[o:o + 2]).hex()}"
    img[o:o + 2] = OURS
    report["noinapp"] = dict(at=hex(AT))


def use():
    import linein3
    if install not in linein3.POST: linein3.POST.append(install)
