"""SC50.4: chords.use_shared's c_chshd in the bytes semitab frees (the hole is full); chords calls it at its fixed address, the first thing after jumpoct."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import Asm, h  # noqa: E402
import chords as CH  # noqa: E402

AT = 0x0805D3A4


def install(img, report, base_addr):
    import ct_fw
    assert base_addr == AT, hex(base_addr)
    a = Asm(base_addr)
    CH.shd_code(a, h(0x4770))
    code, labels = a.assemble()
    img += bytes([0xFF]) * (base_addr - ct_fw.APP_BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    return labels, code, {}
