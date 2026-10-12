"""Development dependencies of CIRCUIT-HACKS, fetched from their original sources (nothing third-party is stored in this repository).

    python tools/setup_dev.py                 everything (Linux, macOS, WSL2 or Windows with Git + MinGW-w64 / WinLibs)
    python tools/setup_dev.py --check         only report what is there and what is missing
    python tools/setup_dev.py --no-dsptool    skip the DSP emulator (builds still work: the DSP assembly is cached in tools/)
    python tools/setup_dev.py --official FILE use your copy of the official firmware instead of downloading it

Sources (see docs/DEPENDENCIAS.md):
  1. Python packages, pinned (tools/requirements.txt), from PyPI: capstone 5.0.7 (BSD-3-Clause), unicorn 2.1.4 (GPL-2.0).
  2. Official firmware Circuit Tracks 1.2.1 (build 4486), from Novation Components; checked against stock/SHA256SUMS.txt and stored in stock/ (ignored by git).
     Novation's firmware, under Novation's terms: it is downloaded to your machine, never redistributed.
  3. userx14/circuittracksreverseengineering (device RAM / flash dumps used by the ARM emulators), git, pinned commit -> ext/, linked as ctre/.
  4. dsp56300/dsp56300 (dsp56kEmu, GPL-3.0), git, pinned commit + submodule asmjit -> ext/, our patches tools/dsptool/*.patch, then tools/dsptool/dsptool.cpp
     is built against it -> ext/bin/dsptool[.exe].
  5. re/app.asm: Thumb listing of the official firmware (tools/gen_listing.py), used by the builders.
Everything goes to ext/, stock/ and re/, which git ignores.  The script can be run again: finished steps are skipped.
"""
from __future__ import annotations
import argparse
import hashlib
import os
import platform
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "ext"
WIN = os.name == "nt"
OFFICIAL_URL = "https://components.novationmusic.com/api/v2/firmwares/168/file"
CTRE = dict(url="https://github.com/userx14/circuittracksreverseengineering", rev="d6aec9fc9d975d65f54ed5ca16c096227e6974ab",
            dir=EXT / "circuittracksreverseengineering", probe="Firmware-Analysis/ram_dump_firmware_0x08037988.bin")
DSP = dict(url="https://github.com/dsp56300/dsp56300", rev="44353be2f0156cac970c6ab4f467ea1998b40605", dir=EXT / "dsp56300")
PATCHES = [ROOT / "tools/dsptool/dsp56kEmu-memtrace.patch"] + ([ROOT / "tools/dsptool/dsp56300-mingw.patch"] if WIN else [])
DSPTOOL = EXT / "bin" / ("dsptool.exe" if WIN else "dsptool")
STOCK_BIN = ROOT / "stock/circuittracks-firmware-4486-STOCK.bin"
STOCK_SYX = ROOT / "stock/circuittracks-firmware-4486-STOCK.syx"


def say(m): print(m, flush=True)


def run(cmd, cwd=None, env=None):
    say("  $ " + " ".join(str(c) for c in cmd))
    subprocess.run([str(c) for c in cmd], cwd=cwd, check=True, env=env)


def out(cmd, cwd=None):
    r = subprocess.run([str(c) for c in cmd], cwd=cwd, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def need(tool, hint):
    if not shutil.which(tool): raise SystemExit(f"'{tool}' not found: {hint}")


# ---------------------------------------------------------------------------------------------------- 1. Python
def step_python(check):
    say("== 1/5 Python packages (PyPI, pinned in tools/requirements.txt)")
    if sys.version_info < (3, 10): raise SystemExit("Python 3.10+ is needed")
    try:
        import capstone, unicorn  # noqa: F401,E401
        ok = capstone.__version__ == "5.0.7" and unicorn.__version__.startswith("2.1.4")
    except ImportError:
        ok = False
    if ok: say("  ok: capstone 5.0.7, unicorn 2.1.4"); return True
    if check: say("  missing / other versions (the builders compare Capstone text: exactly 5.0.7)"); return False
    run([sys.executable, "-m", "pip", "install", "-r", ROOT / "tools/requirements.txt"])
    return True


# ---------------------------------------------------------------------------------------------------- 2. official firmware
def sums():
    return {n: h for h, n in (l.split() for l in (ROOT / "stock/SHA256SUMS.txt").read_text().splitlines() if l.strip())}


def step_official(check, official):
    say("== 2/5 Official firmware 1.2.1 (build 4486) -> stock/  (Novation Components; downloaded, never redistributed)")
    want = sums()
    if STOCK_BIN.exists() and hashlib.sha256(STOCK_BIN.read_bytes()).hexdigest() == want["circuittracks-firmware-4486-STOCK.bin"]:
        say("  ok: " + str(STOCK_BIN.relative_to(ROOT))); return True
    if check: say(f"  missing: python tools/setup_dev.py downloads it from {OFFICIAL_URL}"); return False
    sys.path.insert(0, str(ROOT / "tools"))
    import patch_official
    if official:
        src = Path(official)
    else:
        src = ROOT / "stock/download-4486.syx"; src.parent.mkdir(exist_ok=True)
        say(f"  downloading {OFFICIAL_URL}")
        req = urllib.request.Request(OFFICIAL_URL, headers={"User-Agent": "CIRCUIT-HACKS setup_dev.py"})
        with urllib.request.urlopen(req, timeout=60) as r: src.write_bytes(r.read())
    img, syx = patch_official.load_official(src)                    # refuses anything that is not the official 4486
    STOCK_BIN.write_bytes(img); STOCK_SYX.write_bytes(syx)
    if src.name == "download-4486.syx": src.unlink()
    say("  ok: SHA-256 checked, " + STOCK_BIN.name)
    return True


# ---------------------------------------------------------------------------------------------------- 3. dumps
def git_at(d, url, rev, check, submodules=()):
    if (d / ".git").exists() and out(["git", "rev-parse", "HEAD"], d) == rev:
        return "ok"
    if check: return "missing"
    need("git", "install git (https://git-scm.com)")
    env = dict(os.environ, GIT_LFS_SKIP_SMUDGE="1")
    if not (d / ".git").exists():
        d.parent.mkdir(parents=True, exist_ok=True)
        run(["git", "clone", "--filter=blob:none", url, d], env=env)
    run(["git", "-c", "advice.detachedHead=false", "checkout", "-q", rev], cwd=d, env=env)
    for s in submodules: run(["git", "submodule", "update", "--init", "--depth", "1", s], cwd=d, env=env)
    return "fetched"


def link_dir(link, target):
    if link.exists(): return
    try:
        os.symlink(target, link, target_is_directory=True)
    except OSError:
        if WIN: subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], check=True, capture_output=True)   # a junction needs no admin rights
        else: raise


def step_dumps(check):
    say(f"== 3/5 Device dumps: {CTRE['url']} @ {CTRE['rev'][:8]} -> ext/, ctre/")
    st = git_at(CTRE["dir"], CTRE["url"], CTRE["rev"], check)
    if st == "missing": say("  missing"); return False
    if not check: link_dir(ROOT / "ctre", CTRE["dir"])
    ok = (ROOT / "ctre" / CTRE["probe"]).exists()
    say(f"  {'ok' if ok else 'missing'}: ctre/{CTRE['probe']}")
    return ok


# ---------------------------------------------------------------------------------------------------- 4. dsptool
def step_dsptool(check, skip, rebuild):
    say(f"== 4/5 DSP emulator: {DSP['url']} @ {DSP['rev'][:8]} (GPL-3.0) + tools/dsptool -> {DSPTOOL.relative_to(ROOT)}")
    if skip: say("  skipped (--no-dsptool): builds use tools/dsp_asm_cache.json; the DSP tests need dsptool"); return True
    if DSPTOOL.exists() and not rebuild:
        r = subprocess.run([str(DSPTOOL), "dis"], input="0af080 000100\n", capture_output=True, text=True)
        say(f"  {'ok' if r.returncode == 0 else 'broken (use --rebuild-dsptool)'}: " + str(DSPTOOL.relative_to(ROOT))); return r.returncode == 0
    if check: say("  missing"); return False
    git_at(DSP["dir"], DSP["url"], DSP["rev"], check, submodules=["source/asmjit"])
    d = DSP["dir"]
    for p in PATCHES:
        if subprocess.run(["git", "apply", "--check", "--ignore-whitespace", str(p)], cwd=d, capture_output=True).returncode == 0:
            run(["git", "apply", "--ignore-whitespace", p], cwd=d)
        else:
            say(f"  (patch already applied or not needed: {p.name})")
    need("cmake", "install cmake >= 3.20 (https://cmake.org)")
    gen = ["-G", "Ninja"] if shutil.which("ninja") else (["-G", "MinGW Makefiles"] if WIN else [])
    run(["cmake", "-S", ".", "-B", "build", *gen, "-DCMAKE_BUILD_TYPE=Release"], cwd=d)
    run(["cmake", "--build", "build", "--target", "dsp56kEmu", "-j", str(os.cpu_count() or 4)], cwd=d)
    cxx = shutil.which("g++") or shutil.which("c++") or shutil.which("clang++")
    if not cxx: raise SystemExit("no C++17 compiler (g++ / clang++); on Windows: winget install BrechtSanders.WinLibs.POSIX.UCRT")
    libs = [f"build/source/{p}" for p in ("dsp56kEmu/libdsp56kEmu.a", "dsp56kBase/libdsp56kBase.a", "asmjit/libasmjit.a", "vtuneSdk/libvtuneSdk.a")]
    extra = ["-static", "-lpthread"] if WIN else (["-lpthread", "-ldl"] + (["-lrt"] if platform.system() == "Linux" else []))
    DSPTOOL.parent.mkdir(parents=True, exist_ok=True)
    run([cxx, "-O2", "-std=c++17", "-Isource", "-Isource/asmjit/src", ROOT / "tools/dsptool/dsptool.cpp", *libs, *extra, "-o", DSPTOOL], cwd=d)
    r = subprocess.run([str(DSPTOOL), "dis"], input="0af080 000100\n", capture_output=True, text=True)
    say("  dsptool: " + (r.stdout.strip() or r.stderr.strip())[:80])
    return r.returncode == 0


# ---------------------------------------------------------------------------------------------------- 5. listing
def step_listing(check):
    say("== 5/5 re/app.asm (Thumb listing of the official firmware)")
    asm = ROOT / "re/app.asm"
    if asm.exists() and STOCK_BIN.exists() and asm.stat().st_mtime >= STOCK_BIN.stat().st_mtime:
        say("  ok: re/app.asm"); return True
    if check or not STOCK_BIN.exists(): say("  missing (needs step 2)"); return False
    run([sys.executable, ROOT / "tools/gen_listing.py", STOCK_BIN], cwd=ROOT)
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="only report")
    ap.add_argument("--no-dsptool", action="store_true", help="skip the DSP emulator")
    ap.add_argument("--rebuild-dsptool", action="store_true")
    ap.add_argument("--official", help="your copy of the official firmware (.syx or .bin) instead of downloading it")
    a = ap.parse_args()
    res = [step_python(a.check), step_official(a.check, a.official), step_dumps(a.check),
           step_dsptool(a.check, a.no_dsptool, a.rebuild_dsptool), step_listing(a.check)]
    say("")
    if all(res):
        say("Ready. Check with: python tools/verify_builds.py   and   bash tools/run_tests.sh")
    else:
        say("Not complete: " + ", ".join(n for n, r in zip(("python", "firmware", "dumps", "dsptool", "listing"), res) if not r)); sys.exit(1)


if __name__ == "__main__":
    main()
