"""Build a CIRCUIT-HACKS firmware from the OFFICIAL Novation firmware that you provide (the repository does not ship any Novation code).

    python tools/patch_official.py OFFICIAL.syx|OFFICIAL.bin [--version RC2] [--all] [--list]
  1. The official file: the Circuit Tracks 1.2.1 (build 4486) update as Components serves it (.syx), or its application image (.bin).
     It is checked against the SHA-256 in stock/SHA256SUMS.txt; another version is refused.
  2. It is stored as stock/circuittracks-firmware-4486-STOCK.bin (+ .syx), the Thumb listing re/app.asm is generated (tools/gen_listing.py, needs capstone 5.0.7).
  3. The builder of the version runs (tools/build_*.py) and writes firmware/<dir>/: .bin, .syx, manifest.json.  The result must have the SHA-256 the repository
     records (firmware/<dir>/manifest.json): the build is reproducible, so a mismatch means a different toolchain (capstone) or a modified tree.
  4. Send the .syx with tools/ct_uploader.html (Chrome / Edge, Web MIDI).  Recovery: Scales + Preset + Note at power-on, then the official firmware.
Requirements: Python 3.10+, `pip install -r tools/requirements.txt`.  DSP builds need nothing else (the DSP assembler result is cached in tools/);
if a builder asks for dsptool, run tools/setup_local.sh (see docs/LOCAL.md).
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import ct_fw  # noqa: E402
from verify_builds import BUILDS  # noqa: E402

STOCK_BIN = ROOT / "stock/circuittracks-firmware-4486-STOCK.bin"
STOCK_SYX = ROOT / "stock/circuittracks-firmware-4486-STOCK.syx"


def sums():
    out = {}
    for l in (ROOT / "stock/SHA256SUMS.txt").read_text().splitlines():
        if l.strip(): h, n = l.split(); out[n] = h
    return out


def load_official(path: Path):
    data = path.read_bytes()
    want = sums()
    sha = hashlib.sha256(data).hexdigest()
    if data[:1] == b"\xF0":
        if sha != want["circuittracks-firmware-4486-STOCK.syx"]:
            info = ct_fw.decode(data)
            img = info["image"]
            if hashlib.sha256(img).hexdigest() != want["circuittracks-firmware-4486-STOCK.bin"]:
                raise SystemExit(f"{path}: not the official Circuit Tracks 1.2.1 (build 4486) update (sha256 {sha})")
            return img, data
        return ct_fw.decode(data)["image"], data
    if sha != want["circuittracks-firmware-4486-STOCK.bin"]:
        raise SystemExit(f"{path}: not the official 1.2.1 (build 4486) application image (sha256 {sha})")
    return data, ct_fw.encode(data)


def versions():
    out = {}
    for d, script, extra in BUILDS:
        m = ROOT / "firmware" / d / "manifest.json"
        marker = json.loads(m.read_text()).get("marker", d) if m.exists() else d
        out[marker.upper()] = (d, script, extra)
        out[d.upper()] = (d, script, extra)
    return out


def build_one(d, script, extra):
    man_p = ROOT / "firmware" / d / "manifest.json"
    want = json.loads(man_p.read_text())["syx_sha256"] if man_p.exists() else None
    tmp = ROOT / "build" / ("patch_" + d)
    r = subprocess.run([sys.executable, str(ROOT / "tools" / script), str(STOCK_BIN), *extra, "-o", str(tmp)], capture_output=True, text=True, cwd=ROOT)
    if r.returncode:
        print(r.stdout[-2000:], r.stderr[-4000:]); raise SystemExit(f"{script} failed")
    syx = next(tmp.glob("*.syx")); got = hashlib.sha256(syx.read_bytes()).hexdigest()
    if want and got != want:
        raise SystemExit(f"{d}: built {got[:16]}…, the repository records {want[:16]}… (another capstone version? see docs/LOCAL.md)")
    dst = ROOT / "firmware" / d; dst.mkdir(parents=True, exist_ok=True)
    for f in tmp.iterdir():
        if f.suffix in (".syx", ".bin") or not (dst / f.name).exists(): shutil.copy2(f, dst / f.name)
    print(f"{d}: {dst / syx.name}  sha256 {got}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("official", type=Path, nargs="?")
    ap.add_argument("--version", default="RC2")
    ap.add_argument("--all", action="store_true", help="every version of tools/verify_builds.py")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    vs = versions()
    if a.list:
        for d, script, extra in BUILDS: print(f"{d:10s} {script}")
        return
    if not a.official: ap.error("the official firmware file is needed")
    img, syx = load_official(a.official)
    STOCK_BIN.parent.mkdir(exist_ok=True); STOCK_BIN.write_bytes(img); STOCK_SYX.write_bytes(syx)
    subprocess.run([sys.executable, str(ROOT / "tools/gen_listing.py"), str(STOCK_BIN)], check=True, cwd=ROOT)
    todo = BUILDS if a.all else [vs[a.version.upper()]] if a.version.upper() in vs else None
    if todo is None: raise SystemExit(f"unknown version {a.version}; --list shows them")
    for d, script, extra in todo: build_one(d, script, extra)


if __name__ == "__main__":
    main()
