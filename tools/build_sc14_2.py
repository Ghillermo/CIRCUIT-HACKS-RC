"""Circuit Tracks 4486 — SC14.2 = SC14 with the SC10 FX-return flag moved out of the DSP voice table.

SC10..SC14 kept their flag in DSP X:$EC.  X:$EB..$15A is core 0's voice-slot table (14 slots of
8 words, filled by the DSP init at P:$2890 and walked indirectly by func_00198d), so X:$EC is
slot 0's r0 (Synth 1 voice 0 state pointer, $1960): every Audio In group send overwrote it.

SC14.2 puts the flag at X:$3A00, inside X:$3339..$3BFF, which a whole-core emulation never reads
or writes after init, the ARM never writes, and no DSP instruction references absolutely or via
an immediate base within 0x100 words (tools/dsp_free_scan.py).  Nothing else changes.

Marker "SC14.2" (6 bytes) in the version-block padding, so it never matches an installed SC14.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ct_fw  # noqa: E402
import build_shared_channels as sc  # noqa: E402
import build_sc10 as s10  # noqa: E402

FLAGS_NEW = 0x3A00
MARKER = b"SC14.2"
NAME = "SC14.2"

s10.FLAGS = FLAGS_NEW                  # read at build time by SC10's DSP code and the H9 ARM tail
import build_sc14 as s14  # noqa: E402


def build(stock: bytes, listing: Path):
    assert sc.MARK_OFF + len(MARKER) <= sc.INFO_OFF + sc.INFO_LEN
    assert stock[sc.MARK_OFF:sc.INFO_OFF + sc.INFO_LEN] == bytes(sc.INFO_OFF + sc.INFO_LEN - sc.MARK_OFF)
    img, report = s14.build(stock, listing)
    img = bytearray(img)
    img[sc.MARK_OFF:sc.MARK_OFF + len(MARKER)] = MARKER
    report["D"]["marker"] = MARKER.decode()
    report["sc14_2"] = dict(flags=hex(FLAGS_NEW), reason="X:$EC is DSP voice slot 0 r0 (table X:$EB..$15A)")
    return bytes(img), report


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("stock_bin", type=Path)
    ap.add_argument("--listing", type=Path, default=Path(__file__).resolve().parents[1] / "re/app.asm")
    ap.add_argument("-o", "--outdir", type=Path, default=Path("build/sc14.2"))
    args = ap.parse_args()
    stock = args.stock_bin.read_bytes()
    img, report = build(stock, args.listing)
    syx = ct_fw.encode(img)
    info = ct_fw.decode(syx)
    assert info["image"] == img
    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / f"circuittracks-4486-{NAME}.bin").write_bytes(img)
    (args.outdir / f"circuittracks-4486-{NAME}.syx").write_bytes(syx)
    manifest = dict(base="circuittracks-firmware-4486 (1.2.1)", marker=NAME, image_size=hex(len(img)),
                    image_sha256=ct_fw.sha256(img), syx_sha256=ct_fw.sha256(syx), crc32=hex(info["crc"]), report=report)
    (args.outdir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print("image", hex(len(img)))
    print("syx sha", manifest["syx_sha256"], "crc", manifest["crc32"])
