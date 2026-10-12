"""SC19.3 tests: the power-up freeze (persist19.FIX_LOCK), on the live RAM dump (unicorn).

    python tools/emu_sc19_3.py SC19.1.bin SC19.3.bin SC19.3_manifest.json SC19.1_manifest.json

SC19 / SC19.1 / SC20D froze for ever at power-up and SC19.2 (staged work) froze when its stage A ran: persist19.c_xm_load runs in the DSP service tick and
used the stock MARK_DIRTY (0x0803BDCC), which takes the service semaphore (0x08021064: waits while the count at [ptr + 0xC] is 0); the main loop holds that
very semaphore around the service (0x0801D5D4 .. 0x0801D5DC).  Checks:
  * SC19.1 (the bug): a project load followed by the tick calls the semaphore take 0x08021064 from inside the tick;
  * SC19.3: the same flow never takes it, still marks the Audio In group dirty (0x08021FDC(0x20, 48)) and loads exactly the same state;
  * SC19.3 differs from SC19.1 only at the marker and the one call in c_xm_load.
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc19_1 as T1  # noqa: E402
import persist19 as P  # noqa: E402

BASE = 0x08010000


def flow(img, man):
    e = T1.E191(img, man)
    e.setrec(P.XM_SIG, (P.SIG << 3)); e.setrec(P.XM_MODES, 2 | (3 << 3))
    e.apply()
    e.sem.clear(); e.mark.clear()
    out = []
    for _ in range(14):
        m = e.tick19(); out.append(len(m))
        if not m and not e.flags(): break
    return dict(sem=e.sem_max, mark=list(e.mark), modes=e.modes(), flags=e.flags(), msgs=sum(out),
                state=[e.xm(i) for i in range(P.N_XM)], slots=[e.rslot(i) for i in range(28)])


def main(ref, img, man, refman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    check(man["report"]["persist19"].get("fix_lock") is True and not refman["report"]["persist19"].get("fix_lock"), "manifests: SC19.3 has the lock fix, SC19.1 not")
    a = flow(ref, refman); b = flow(img, man)
    check(a["sem"] >= 1, f"SC19.1: the tick takes the service semaphore {a['sem']} time(s) (the freeze: it waits for itself on the hardware)")
    check(b["sem"] == 0, f"SC19.3: the tick never takes the service semaphore ({b['sem']})")
    check((0x20, 48) in b["mark"], f"SC19.3: the Audio In group is still marked dirty {b['mark']}")
    check(a["modes"] == b["modes"] == [2, 3] and a["flags"] == b["flags"] == 0 and a["msgs"] == b["msgs"] and a["state"] == b["state"] and a["slots"] == b["slots"],
          f"same state after the load as SC19.1 (modes {b['modes']}, {b['msgs']} messages, flags {b['flags']})")
    diff = [i for i in range(len(ref)) if ref[i] != img[i]]
    lab = {k: int(v, 16) for k, v in man["report"]["persist19"]["labels"].items()}
    regs = sorted({(BASE + i) & ~3 for i in diff})
    check(all(0x080101E8 <= x < 0x080101F0 or lab["c_xm_load"] <= x < lab["c_xm_save"] for x in regs), f"SC19.1 -> SC19.3 differs only at the marker and the call in c_xm_load {[hex(x) for x in regs]}")
    print("SC19.3 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    ref = Path(sys.argv[1]).read_bytes(); img = Path(sys.argv[2]).read_bytes()
    man = json.loads(Path(sys.argv[3]).read_text()); refman = json.loads(Path(sys.argv[4]).read_text())
    sys.exit(1 if main(ref, img, man, refman) else 0)
