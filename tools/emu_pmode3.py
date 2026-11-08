"""RC4.09 / packio.use_pmode3 (fix, 2026-11-08): the voice-mode colours of the synth Preset view without card reads on a tap.

    python tools/emu_pmode3.py NEW.bin NEW_manifest.json OLD.bin OLD_manifest.json
  * emu_sc38_8's sequence on both builds: the colours of every frame the same (the first read, a tap, 4 s later, another page, another pack,
    back from Master FX); a tap reads nothing on the new build (the old one read the four banks again); the lock balanced;
  * during a reread the colours shown stay the old ones (the cache's modes unchanged until the last bank is read);
  * a tap, then frames for 4 s: no read; after 4 s: one reread.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc38_8 as S  # noqa: E402
from emu_sc35 import E35, MGR, TICK, PK, set_loaded, SVIEW  # noqa: E402
from emu_sc08 import CONT  # noqa: E402

fails = []


def check(c, m):
    print(("  ok   " if c else "  FAIL ") + m)
    if not c: fails.append(m)


def mid_read(img, man):
    e = E35(img, man)
    e.set_p0(e.r32(CONT + 0x188), 0); e.btn(0); e.btn(8); set_loaded(e, man, 31)
    e.sd = {(3, k, 0xFF): S.bank([S.MONO if k & 1 else S.GLIDE]) for k in range(8)}
    e.call(int(man["report"]["sc14"]["labels"]["c_gst"], 16)); C = e.uc.reg_read(UC_ARM_REG_R0) + PK.PM_CACHE
    ms = [200000]
    def frame(dt=20):
        ms[0] += dt; e.w32(TICK, ms[0]); e.call(0x08034196, MGR, 0x2006E000, maxins=8_000_000)
        return list(struct.unpack("<32H", bytes(e.uc.mem_read(0x2006E000, 64))))
    def setp(st, n, v):
        e.call(0x080354FA, st, n); e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0), bytes([v])); e.call(0x080353C0, st, maxins=8_000_000)
    f0 = frame(); old = bytes(e.uc.mem_read(C + 4, 8))
    seen = []
    def hk(uc, a, s, d): seen.append(bytes(uc.mem_read(C + 4, 8)))
    h = e.uc.hook_add(UC_HOOK_CODE, hk, begin=PK.READ & ~1, end=PK.READ & ~1)
    for k in range(8): e.sd[(3, k, 0xFF)] = S.bank([S.GLIDE if k & 1 else S.MONO])
    e.api.clear(); f1 = frame(4200); e.uc.hook_del(h)
    nr = len([c for c in e.api if c[0] == "read"])
    setp(e.r32(SVIEW + 0x14), 10, 3)                                             # a tap
    e.api.clear(); quiet = 0
    for i in range(10):
        frame(380); quiet += len([c for c in e.api if c[0] in ("size", "read")])
    e.api.clear(); frame(800); later = len([c for c in e.api if c[0] in ("size", "read")])
    out = dict(old=old, seen=seen, nr=nr, f0=f0, f1=f1, quiet=quiet, later=later, lock=e.lock)
    del e; gc.collect()
    return out


def main(new_bin, new_man, old_bin, old_man):
    ni, nm = Path(new_bin).read_bytes(), json.loads(Path(new_man).read_text())
    oi, om = Path(old_bin).read_bytes(), json.loads(Path(old_man).read_text())
    n = S.run(ni, nm, True); gc.collect(); o = S.run(oi, om, True); gc.collect()
    for k in ("f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8"):
        check(n[k] == o[k], f"{k}: the pads' colours as before")
    check(o["r3"] != [] and n["r3"] == [], f"a tap: the old build read the banks ({len(o['r3'])}), the new one nothing")
    check(n["r1"] == o["r1"] and n["r5"] == o["r5"] and n["r6"] == o["r6"] and n["r7"] == o["r7"], "the first read, 4 s, page, pack: read as before")
    check(n["lock1"] == 0 and n["lock8"] == 0, "the lock balanced")
    m = mid_read(ni, nm)
    check(m["nr"] > 1 and all(s == m["old"] for s in m["seen"]), f"during a reread the old modes stay ({m['nr']} reads)")
    check(m["f1"] != m["f0"], "after the reread: the new colours")
    check(m["quiet"] == 0 and m["later"] > 0, f"after a tap: nothing for 4 s ({m['quiet']}), then one reread within 4.6 s ({m['later']} requests)")
    mo = mid_read(oi, om)
    check(any(s != mo["old"] for s in mo["seen"]), "(the old build cleared the modes during the reread)")
    print("PMODE3 RESULT:", "ALL PASS" if not fails else f"{len(fails)} FAIL")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:5]))
