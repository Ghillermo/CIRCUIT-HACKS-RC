"""SC52.4 ARM tests (vcf21.use_osc4, tools/oscmod.py, tools/autolane.py) through the controller and the real LED task:
  * OSC 1's page (pad 2): K1 TUNE, K2 FINE, K3 WAVE, K4 SHAPE, K7 LFOM; Shift: K1 ENVP, K2 LFOP, K3 ENVM, K4 ENVW, K7 LFOW;
  * OSC 2's page (pad 3): K3 WAVE 2, K4 SHAPE 2, K5 FM, K6 RING, K7 BITSYNC, K8 MIX; FM starts at 64 and its LED shows the distance from it;
  * oscmod: OSC 1's K8 / K6 / K5 = LFO -> MIX / RING / FM, with Shift the envelope's; clamped at +-63 / -64; Clear held = 0; the LEDs; the tick
    writes a changed depth to core 0 (OM_T + 48 t + i), once;
  * the patch: c_omgath writes 0xC4, the 6 depths, the check at padding + 163; c_omappl restores them; a patch without them = no depths and FM
    v -> 64 + k (0 -> 64, 32 -> 79, 127 -> 95);
  * autolane: Record armed, a knob whose code has no lane takes the first lane empty in the playing pattern and is recorded there; not armed:
    nothing;
  * psave / xpatch move 171 bytes of padding.

    python tools/emu_osc4.py SC52.4.bin manifest.json
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R5, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402  (its import sets vcf21's options)
import packio as PK  # noqa: E402
import oscmod as OM  # noqa: E402
import recinst as RI  # noqa: E402

V = T4.V
MGR = X.MGR
CLEAR = 23
COL = (0x09, 0x3B)


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = X.EP(img, man)
    R = man["report"]
    ol = {k: int(v, 16) for k, v in {**R["oscmod"]["labels"], **R["oscmod2"]["labels"]}.items()}
    om_t = 0x5400
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05]))
    e.btn(2); e.btn(8)
    check(e.val(0, 33) == 64 and e.val(1, 33) == 64, f"FM starts at its centre ({e.val(0, 33)}, {e.val(1, 33)})")
    e.pad(1); pg = e.r0(e.vl["c_vpage"], 0)
    check(pg == 1, f"pad 2: page {pg}")
    lay = {}
    for shift, codes in ((False, (17, 18, 19, 20, None, None, 26, None)), (True, (22, 21, 25, 23, None, None, 24, None))):
        e.shift(shift)
        for k, c in enumerate(codes):
            if c is None: continue
            v0 = e.val(0, c); e.knob(k, 2); lay[(shift, k)] = (c, e.val(0, c) != v0)
        e.shift(False)
    check(all(ok for _c, ok in lay.values()), f"OSC 1's page: {[(('S+' if s else '') + 'K%d' % (k + 1), c, ok) for (s, k), (c, ok) in lay.items()]}")
    dep = lambda t=0: [int.from_bytes(bytes([b]), "little", signed=True) for b in e.uc.mem_read(OM.OMR + 4 + 6 * t, 6)]
    e.knob(7, 5); e.shift(True); e.knob(7, -3); e.shift(False)
    e.knob(5, 70); e.shift(True); e.knob(4, -90); e.shift(False)
    d = dep()
    check(d == [5, -3, 63, 0, 0, -64] and dep(1) == [0] * 6, f"K8 / S+K8 / K6 / S+K5: the depths {d} (MIDI 2 {dep(1)})")
    f = X.frame(e)
    want = [COL[0] | ((min(126, 2 * abs(v) if v >= 0 else 2 * (-v - 1)) + 2) << 8) for v in (d[4], d[2], d[0])]
    check([f[64], f[65], f[67]] == want, f"the LEDs of K5 / K6 / K8: {[hex(x) for x in (f[64], f[65], f[67])]} (want {[hex(x) for x in want]})")
    e.call(0x08033320, MGR, CLEAR, maxins=8_000_000); e.knob(7, 1); e.call(0x0803381A, MGR, CLEAR, maxins=8_000_000)
    check(dep()[0] == 0 and dep()[1] == -3, f"Clear held + K8: LFO -> MIX = 0 ({dep()})")
    # the tick: one depth a tick to core 0 when it changed
    writes = []
    def dw(uc, a, s, dd): writes.append((uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R1))); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    def sk(uc, a, s, dd): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    h1 = e.uc.hook_add(UC_HOOK_CODE, dw, begin=OM.DSPW, end=OM.DSPW)
    h2 = e.uc.hook_add(UC_HOOK_CODE, sk, begin=int(R["oscmod"]["prev"]["svc"], 16), end=int(R["oscmod"]["prev"]["svc"], 16))
    for _ in range(24): e.call(ol["c_omtick"], maxins=2_000_000)
    got = {a_: ((v_ >> 8) ^ 0x800000) - 0x800000 for a_, v_ in writes}
    exp = {om_t + i: v for i, v in enumerate(dep())}; exp.update({om_t + 48 + i: 0 for i in range(6)})
    check(got == exp and len(writes) == 12, f"the tick: each depth written once ({len(writes)} writes, {got == exp})")
    writes.clear(); e.knob(5, -1)
    for _ in range(12): e.call(ol["c_omtick"], maxins=2_000_000)
    check(writes == [(om_t + 2, ((62 << 8) & 0xFFFFFFFF))], f"a change: one write ({[(hex(a_), hex(v_)) for a_, v_ in writes]})")
    e.uc.hook_del(h1); e.uc.hook_del(h2)
    # OSC 2's page
    e.pad(27); e.pad(2)                                                     # two oscillators on (pad 28), OSC 2's page
    lay2 = []
    for k, c in enumerate((27, 28, 29, 30, 33, 34, 32, 31)):
        v0 = e.val(0, c); e.knob(k, 3); lay2.append((k + 1, c, e.val(0, c) != v0))
    check(all(ok for *_x, ok in lay2), f"OSC 2's page: {lay2}")
    fm = e.val(0, 33); f = X.frame(e)
    check(f[64] >> 8 == min(126, 2 * abs(fm - 64)) + 2, f"FM {fm}: its LED's level {f[64] >> 8} = 2 |v - 64| + 2")
    # the patch
    e.call(ol["c_omgath"], 0, maxins=8_000_000)
    buf = bytes(e.uc.mem_read(PK.BUF + OM.REC_AT, OM.REC_N))
    sm = (0x5A + sum(buf[:7])) & 0xFF
    check(buf[0] == OM.REC_SIG and list(int.from_bytes(bytes([b]), "little", signed=True) for b in buf[1:7]) == dep() and buf[7] == sm, f"gather: {buf.hex()}")
    keep = {}
    def rd(uc, a, s, dd):
        n = uc.reg_read(UC_ARM_REG_R3)
        uc.mem_write(uc.reg_read(UC_ARM_REG_R2), keep.get(n, bytes(n))); uc.reg_write(UC_ARM_REG_R0, 0); uc.reg_write(UC_ARM_REG_R1, n)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    mpr = int(R["mpatch"]["labels"]["c_mpr"], 16)
    hk = e.uc.hook_add(UC_HOOK_CODE, rd, begin=mpr, end=mpr)
    saved = dep(); keep[OM.REC_N] = buf
    e.uc.mem_write(OM.OMR + 4, bytes(6))
    e.uc.mem_write(PK.BUF + 32 + 6, bytes([100]))                           # the patch image's FM (c_mpapply puts it in)
    e.uc.reg_write(UC_ARM_REG_R5, 11); e.call(ol["c_omappl"], 0, maxins=12_000_000)
    check(dep() == saved and e.val(0, 33) == 100, f"apply: the depths back ({dep()}), FM untouched ({e.val(0, 33)})")
    mig = []
    for v in (0, 32, 127):
        keep[OM.REC_N] = bytes(OM.REC_N); e.uc.mem_write(PK.BUF + 32 + 6, bytes([v]))
        e.uc.reg_write(UC_ARM_REG_R5, 11); e.call(ol["c_omappl"], 0, maxins=12_000_000)
        mig.append((v, e.val(0, 33), dep() == [0] * 6))
    check(mig == [(0, 64, True), (32, 79, True), (127, 95, True)], f"an older patch: no depths, FM moved {mig}")
    e.uc.hook_del(hk)
    ps, xp = R["psave"]["listing"], R["xpatch"]["listing"]
    check(any("#0xab" in l for l in ps) and any("#0xab" in l for l in xp), "psave / xpatch: 171 bytes of padding (movs #0xab)")
    del e; gc.collect()
    autolane_part(img, man, check)
    print(f"{man.get('marker', '?')} OSC4 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


def autolane_part(img, man, check):
    e = X.EP(img, man)
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05]))
    e.btn(2); e.btn(8); e.pad(1)
    row = lambda: tuple(e.uc.mem_read(e.r0(e.vl["c_vrow"], 0), 8))
    r0_ = row()
    pat = e.r0(e.vl["c_sdpat"], 0)
    for k in range(8): e.uc.mem_write(pat + RI.LANES + RI.LANE_BYTES * k, bytes([0x40 if k < 3 else 0xFF]) * RI.LANE_BYTES)
    def armed(on, play=1):
        for prm, v in ((1, on), (0, play)):
            p = e.r0(RI.PARAM_WPTR, RI.TRANSPORT, prm); e.uc.mem_write(p, bytes([1 if v else 0])); e.call(RI.COMMIT, RI.TRANSPORT, maxins=2_000_000)
    armed(False); e.gates.clear(); e.knob(3, 2)
    check(row() == r0_ and not e.gates, f"not armed: SHAPE (K4) takes no lane ({row()})")
    armed(True, 0); e.gates.clear(); e.knob(3, 2)
    check(row() == r0_ and not e.gates, f"armed, stopped: no lane ({row()})")
    armed(True); e.gates.clear(); e.knob(3, 2)
    r1 = row()
    check(r1[:3] == r0_[:3] and r1[3] == 20 and r1[4:] == r0_[4:] and any(g[0] == 23 for g in e.gates),
          f"armed: SHAPE takes lane 3, the first empty one ({r1}), recorded (gate ids {sorted(set(g[0] for g in e.gates))})")
    e.uc.mem_write(pat + RI.LANES + RI.LANE_BYTES * 3, bytes([0x40]))     # (the gate is emulated away: what it would have written)
    e.gates.clear(); e.knob(1, 2)
    r2 = row()
    check(r2[4] == 18 and any(g[0] == 24 for g in e.gates), f"FINE (K2): lane 4 ({r2})")
    for k in range(8): e.uc.mem_write(pat + RI.LANES + RI.LANE_BYTES * k, bytes([0x40]) * RI.LANE_BYTES)
    e.gates.clear(); r3 = row(); e.knob(2, 2)
    check(row() == r3 and not e.gates, f"no empty lane: WAVE (K3) nothing ({row()})")
    del e; gc.collect()


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
