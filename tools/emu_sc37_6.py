"""SC37.6 ARM tests (live RAM dump, the real routes): Duplicate stays out of SC19.1's source view of the synth (packio.use_srcguard).

    python tools/emu_sc37_6.py SC37.6.bin SC37.6_manifest.json [SC37.5.bin SC37.5_manifest.json]
  (a build without the pack management, e.g. RC0.3S: only the drumrep.use_clearrep checks)
  * the source view (Synth 1 pressed with its track view on the screen): Duplicate stays dim (pressing it closes the view);
  * Duplicate held in the track view, then the source view: a pad there copies no patch (SC37.4 / SC37.5 copied page x 32 + pad);
  * Duplicate pressed in the source view closes it (SC19.1: any button does), then Duplicate + pad is the patch list again (copies, lit);
  * with the previous build (optional): the held-before case copied a patch;
  * drumrep.use_clearrep: Clear + pad 4 = asked, again = confirmed (request 4); Shift + pad reaches the stock (its silent selection), nothing asked.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R4
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc35 as T  # noqa: E402
import packio as PK  # noqa: E402
from emu_sc05 import STOP  # noqa: E402
from emu_sc08 import CONT  # noqa: E402
from emu_sc17_6 import PRESS  # noqa: E402

MGR = T.MGR
LED_DUP = 56


def run(img, man, guard):
    out = {}
    e = T.E35(img, man); T.set_loaded(e, man, 31)
    st = int(man["report"]["sc17"]["sc14_state"], 16)
    src = lambda: (e.r8(st + PK.S_PAINT) >> 2) & 1
    def frame():
        e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR)
        e.call(0x08033B3E, maxins=5_000_000)
        return struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138)))
    dup = lambda on: e.call(0x08033320 if on else 0x0803381A, MGR, 24, maxins=900000)
    e.set_p0(e.r32(CONT + 0x188), 0)
    if e.r8(MGR + 0x152) != 1: e.btn(0)
    assert e.r8(MGR + 0x152) == 1                                      # Synth 1's track view (where the dump starts)
    # 1. the source view: the Duplicate LED
    e.btn(0); out["src"] = (e.r8(MGR + 0x152), src()); out["src_led"] = frame()[LED_DUP]
    # 2. Duplicate held before the source view opens, then a pad of the source view
    e.btn(0); assert e.r8(MGR + 0x152) == 1 and not src()
    dup(True); out["held_track"] = e.hp0() & 2
    e.call(0x08033320, MGR, 0, maxins=900000); e.call(0x0803381A, MGR, 0, maxins=900000)   # Synth 1 with Duplicate held
    out["src2"] = (e.r8(MGR + 0x152), src())
    e.x.pop(T.SD.PCLIPW, None); e.api.clear()
    e.call(PRESS, MGR, 26, 100, maxins=20_000_000)                    # pad 27 of the source view
    out["src_clip"] = e.x.get(T.SD.PCLIPW, 0); dup(False)
    # 3. Duplicate pressed in the source view closes it (SC19.1: any button does); then Duplicate + pad is the patch list
    out["src3"] = (e.r8(MGR + 0x152), src())
    dup(True); out["after_dup"] = (e.r8(MGR + 0x152), src(), e.hp0() & 2)
    e.x.pop(T.SD.PCLIPW, None); e.call(PRESS, MGR, 5, 100, maxins=20_000_000)
    out["pre_clip"] = e.x.get(T.SD.PCLIPW, 0); out["pre_led"] = frame()[LED_DUP]; dup(False)
    del e; gc.collect()
    return out


def replace(img, man):
    """drumrep.use_clearrep: Clear (the real button) + pad twice = the drum replaced by the capture; Shift + pad goes to the stock."""
    import build_sc17 as B
    from unicorn import UC_HOOK_CODE
    from unicorn.arm_const import UC_ARM_REG_R1
    out = {}
    e = T.E35(img, man)
    blk = e.r32(e.r32(0x20044E58)) if False else None
    gf = int(man["report"]["sc17"]["labels"]["c_gfst"], 16); e.call(gf); blk = e.uc.reg_read(T.UC_ARM_REG_R0)
    e.w32(blk + B.S_SMT, 0)
    e.set_p0(e.r32(CONT + 0x188), 4); e.btn(4); e.btn(8)
    dv = T.DVIEW; e.uc.mem_write(dv + 0x51, bytes(1))
    clear = lambda on: e.call(0x08033320 if on else 0x0803381A, MGR, 23, maxins=900000)
    pad = lambda p_, sh=False: e.pad(p_, shift=sh)
    clear(True); pad(3); clear(False); out["clear1"] = (e.r8(dv + 0x51), e.r32(blk + B.S_SMT))
    clear(True); pad(3); clear(False); out["clear2"] = (e.r8(dv + 0x51), e.r32(blk + B.S_SMT))
    e.w32(blk + B.S_SMT, 0)
    prev = int(man["report"]["drumrep"]["prev_pad"], 16); seen = []
    hk = e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s_, d: seen.append(uc.reg_read(UC_ARM_REG_R1)), begin=prev, end=prev)
    pad(5, sh=True); e.uc.hook_del(hk)
    out["shift"] = (e.r8(dv + 0x51), e.r32(blk + B.S_SMT)); out["shift_stock"] = 5 in seen
    del e; gc.collect()
    return out


def main(img, man, prev=None, prev_man=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    PK.use_copyx(); PK.use_dupmask(); PK.use_pkled(); PK.use_srcguard()
    if not T.feat(man, "srcguard"):                                                        # the safer builds (no packio): only the capture replacement
        print("(no pack management in this build: the source-view checks are skipped)")
        o = None
    else:
        o = run(img, man, True)
    if o: check(o["src"] == (0, 1) and o["src_led"] != 0, f"Synth 1 pressed again: the source view {o['src']}; Duplicate dim there ({o['src_led']:#x}: pressing it goes back to the patch list)")
    if o: check(o["held_track"] == 2 and o["src2"] == (0, 1) and o["src_clip"] == 0,
          f"Duplicate held in the track view, then the source view {o['src2']}: pad 27 copies no patch (clip {o['src_clip']:#x})")
    if o: check(o["after_dup"][:2] == (0, 0) and o["after_dup"][2] == 2 and o["pre_clip"] >> 16 == PK.PCLIP_MAGIC and o["pre_clip"] & 0xFF == 5 and o["pre_led"] != 0,
          f"Duplicate pressed in the source view closes it (as any button) {o['after_dup']}: Duplicate + pad 6 copies patch 5 ({o['pre_clip']:#x}), Duplicate lit")
    if prev and o:
        q = run(prev, prev_man, False)
        check(q["src_clip"] != 0, f"(the previous build) Duplicate held + pad 27 of the source view copied patch 26 ({q['src_clip']:#x})")
    if man["report"]["drumrep"].get("clearrep"):
        r = replace(img, man)
        check(r["clear1"][0] == (3 + 1) << 1 and r["clear1"][1] == 0, f"drum Preset view, Clear + pad 4: asked ({r['clear1'][0]:#x}), nothing requested yet")
        check(r["clear2"][0] == 0 and r["clear2"][1] >> 23 == 4, f"Clear + pad 4 again: confirmed, request 4 ({r['clear2'][1]:#x})")
        check(r["shift"] == (0, 0) and r["shift_stock"], f"Shift + pad 6: no question, nothing requested {r['shift']}; the pad goes to the stock (silent selection)")
    print("SC37.6 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    pv = (Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) if len(a) > 4 else (None, None)
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), *pv) else 0)
