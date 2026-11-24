"""Circuit Tracks 4486 - NORFXD (DIAGNOSTIC, 2026-11-24) = the stock firmware + tools/rdiag.py with NOR only: the PC reads, erases and writes 4 KB blocks of
the internal NOR through the stock's own device (tools/norfix.py), to rebuild the user's internal file system (its boot sector, FATs and root
directory were overwritten; the USB drive is read-only).  Erase / write only inside the file-system partition (NOR 0xD4000..).  Nothing else."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ct_fw, rdiag, build_shared_channels as sc

NAME = "NORFXD"


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("stock_bin", type=Path); ap.add_argument("-o", "--outdir", type=Path, default=Path("build") / NAME.lower())
    args = ap.parse_args(argv)
    rdiag.NOR = True
    img = bytearray(args.stock_bin.read_bytes())
    img[sc.MARK_OFF:sc.MARK_OFF + 6] = NAME.encode()[:6]
    ext = (len(img) + ct_fw.APP_BASE + 3) & ~3
    labels, code = rdiag.install(img, {}, ext)
    report = dict(rdiag=dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, listing=sc.disasm(bytes(code), ext)))
    img = bytes(img); syx = ct_fw.encode(img); info = ct_fw.decode(syx); assert info["image"] == img
    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / f"circuittracks-4486-{NAME}.bin").write_bytes(img)
    (args.outdir / f"circuittracks-4486-{NAME}.syx").write_bytes(syx)
    (args.outdir / "manifest.json").write_text(json.dumps(dict(base="circuittracks-firmware-4486 (1.2.1)", marker=NAME, image_size=hex(len(img)),
        image_sha256=ct_fw.sha256(img), syx_sha256=ct_fw.sha256(syx), crc32=hex(info["crc"]), report=report), indent=2))
    print(f"image {len(img):#x} syx sha {ct_fw.sha256(syx)} crc {info['crc']:#x}")


if __name__ == "__main__":
    main(sys.argv[1:])
