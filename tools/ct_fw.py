"""Circuit Tracks firmware SysEx <-> image tools (pure Python, no dependencies).

Format (verified byte-for-byte against official circuittracks-firmware-4486.syx):

  F0 00 20 29 00 71  01 64 00 00 | 00 05 07 02 (proto ver 0x572, 4 nibbles) F7   UPDATE_INIT
  F0 00 20 29 00 7C  00 | ver(6 nib) | size(8 nib) | crc32(8 nib) F7               UPDATE_HEADER
  F0 00 20 29 00 72  <37 bytes: 32 image bytes as 7-bit groups + 3 pad bits> F7  UPDATE_WRITE (blocks 1..N-1)
  F0 00 20 29 00 73  <37 bytes: block 0 = vector table>                     F7  UPDATE_FINISH

CRC: CRC-32/MPEG-2 (poly 0x04C11DB7, init 0xFFFFFFFF, no reflection, xorout 0)
over exactly `size` image bytes.  Image is linked at 0x08010000; the 64 KB
bootloader at 0x08000000 is never part of the update stream.
The final partial block is padded with 1-bits (0xFF), matching erased flash.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

APP_BASE = 0x08010000
FLASH_END = 0x08080000          # STM32F745VE: 512 KB
MAX_IMAGE_SIZE = FLASH_END - APP_BASE   # 0x70000 — physical limit, NOT verified against bootloader
HDR = bytes((0xF0, 0x00, 0x20, 0x29, 0x00))
UPDATE_INIT, UPDATE_WRITE, UPDATE_FINISH, UPDATE_HEADER = 0x71, 0x72, 0x73, 0x7C
PRODUCT_TRACKS = 0x64

STOCK_4486 = {
    "syx_sha256": "bd2d294bafa88fdec7ae1f5fcaaa13158323969c5a40f83405a72e4ad329a0bd",
    "image_sha256": "b897e0f01c403974eafae32074876234f2da7ef834796a485993acf01423f8da",
    "size": 0x4CDDC,
    "crc": 0x4E74DA9E,
    "proto_version": 0x572,
}


def crc32_mpeg2(data: bytes) -> int:
    table = []
    for i in range(256):
        c = i << 24
        for _ in range(8):
            c = ((c << 1) ^ 0x04C11DB7) & 0xFFFFFFFF if c & 0x80000000 else (c << 1) & 0xFFFFFFFF
        table.append(c)
    crc = 0xFFFFFFFF
    for b in data:
        crc = ((crc << 8) & 0xFFFFFFFF) ^ table[((crc >> 24) ^ b) & 0xFF]
    return crc


def nibbles(value: int, count: int) -> bytes:
    return bytes((value >> (4 * (count - 1 - i))) & 0xF for i in range(count))


def from_nibbles(data: bytes) -> int:
    v = 0
    for b in data:
        if b > 0xF:
            raise ValueError("nibble out of range")
        v = (v << 4) | b
    return v


def pack_block(block: bytes) -> bytes:
    assert len(block) == 32
    bits = int.from_bytes(block, "big") << 3          # 256 data bits + 3 zero pad bits
    return bytes((bits >> (7 * (36 - i))) & 0x7F for i in range(37))


def unpack_block(payload: bytes) -> bytes:
    if len(payload) != 37 or any(b & 0x80 for b in payload):
        raise ValueError("bad packed block")
    bits = 0
    for b in payload:
        bits = (bits << 7) | b
    return (bits >> 3).to_bytes(32, "big")


def split(syx: bytes):
    msgs, i = [], 0
    while i < len(syx):
        s = syx.index(0xF0, i)
        e = syx.index(0xF7, s)
        raw = syx[s:e + 1]
        if not raw.startswith(HDR):
            raise ValueError(f"not a Novation message at {s}")
        msgs.append((raw[5], raw[6:-1]))
        i = e + 1
    return msgs


def decode(syx: bytes) -> dict:
    msgs = split(syx)
    cmds = [c for c, _ in msgs]
    if cmds[0] != UPDATE_INIT or cmds[1] != UPDATE_HEADER or cmds[-1] != UPDATE_FINISH:
        raise ValueError("unexpected message order")
    if any(c != UPDATE_WRITE for c in cmds[2:-1]):
        raise ValueError("unexpected message inside data stream")
    init = msgs[0][1]
    hdr = msgs[1][1]
    product = init[1]
    proto = from_nibbles(init[2:8])
    hver = from_nibbles(hdr[1:7])
    size = from_nibbles(hdr[7:15])
    crc = from_nibbles(hdr[15:23])
    blocks = [unpack_block(msgs[-1][1])] + [unpack_block(p) for _, p in msgs[2:-1]]
    image = b"".join(blocks)
    if len(image) < size:
        raise ValueError("stream shorter than header size")
    tail = image[size:]
    image = image[:size]
    if crc32_mpeg2(image) != crc:
        raise ValueError("CRC mismatch")
    return dict(product=product, proto=proto, header_version=hver, size=size, crc=crc,
                image=image, tail_all_ff=set(tail) <= {0xFF})


def encode(image: bytes, proto: int = STOCK_4486["proto_version"], product: int = PRODUCT_TRACKS) -> bytes:
    if len(image) > MAX_IMAGE_SIZE:
        raise ValueError("image larger than physical flash")
    padded = image + b"\xFF" * (-len(image) % 32)
    blocks = [padded[i:i + 32] for i in range(0, len(padded), 32)]
    out = bytearray()
    out += HDR + bytes((UPDATE_INIT, 0x01, product, 0x00, 0x00)) + nibbles(proto, 4) + b"\xF7"
    out += HDR + bytes((UPDATE_HEADER, 0x00)) + nibbles(proto, 6) + nibbles(len(image), 8) \
        + nibbles(crc32_mpeg2(image), 8) + b"\xF7"
    for blk in blocks[1:]:
        out += HDR + bytes((UPDATE_WRITE,)) + pack_block(blk) + b"\xF7"
    out += HDR + bytes((UPDATE_FINISH,)) + pack_block(blocks[0]) + b"\xF7"
    return bytes(out)


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path, help=".syx (decode) or .bin (encode)")
    ap.add_argument("-o", "--output", type=Path)
    a = ap.parse_args()
    data = a.input.read_bytes()
    if a.input.suffix.lower() == ".syx":
        info = decode(data)
        print({k: (hex(v) if isinstance(v, int) else v) for k, v in info.items() if k != "image"})
        print("image sha256", sha256(info["image"]))
        print("round trip identical:", encode(info["image"], info["proto"], info["product"]) == data)
        if a.output:
            a.output.write_bytes(info["image"])
    else:
        syx = encode(data)
        print("syx sha256", sha256(syx), "size", len(syx))
        if a.output:
            a.output.write_bytes(syx)
