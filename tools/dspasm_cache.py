"""The DSP assembler (dsptool asm) behind a persistent cache, so building a firmware needs no dsptool: tools/dsp_asm_cache.json holds every line the builders
assemble (line -> words).  A line that is not there runs dsptool; with DSP_ASM_CACHE_UPDATE=1 in the environment the new lines are added to the file at exit
(regenerate: DSP_ASM_CACHE_UPDATE=1 python tools/verify_builds.py)."""
from __future__ import annotations
import atexit
import json
import os
import subprocess
from pathlib import Path

FILE = Path(__file__).resolve().parent / "dsp_asm_cache.json"
_mem: dict[str, list[int]] = {}
_new: dict[str, list[int]] = {}
try:
    _mem.update({k: v for k, v in json.loads(FILE.read_text()).items()})
except (OSError, ValueError):
    pass


def assemble(lines):
    """-> one list of words per line (cached, else dsptool)."""
    todo = [l for l in dict.fromkeys(lines) if l not in _mem]
    if todo:
        from dsptool_path import TOOL
        out = subprocess.run([TOOL, "asm"], input="\n".join(todo) + "\n", capture_output=True, text=True).stdout.splitlines()
        for l, o in zip(todo, out):
            p = o.split()
            assert p and p[0] != "ERR", (l, o)
            _mem[l] = _new[l] = [int(x, 16) for x in p[1:]]
        assert all(l in _mem for l in todo), "dsptool did not answer every line (see docs/LOCAL.md: tools/setup_local.sh builds it)"
    return [_mem[l] for l in lines]


@atexit.register
def _save():
    if _new and os.environ.get("DSP_ASM_CACHE_UPDATE") == "1":
        try:
            cur = json.loads(FILE.read_text())
        except (OSError, ValueError):
            cur = {}
        cur.update(_new)
        FILE.write_text(json.dumps(dict(sorted(cur.items())), separators=(",", ":")))


def dis_listing(words, base):
    """The DSP disassembly of words (for the manifests' listings): [] when there is no dsptool (it never changes the image)."""
    from dsptool_path import TOOL
    import dsp56 as D
    try:
        return subprocess.run([TOOL, "dis", "/dev/stdin", "%x" % base], input=D.to_bytes(words), capture_output=True).stdout.decode().splitlines()
    except OSError:
        return []
