"""SC52.2 / Beta 5.25 (vcf21.use_osc2pg2; the user, 2026-11-05: «reasigna (en VA y WT) k1: pitch, k2: pitch fino. k3: shape k4: mezcla. K5: FM,
6,7,8 iguales»): the OSC 2 page of MIDI 1's own synth, each knob turned by its own amount through the knob path (emu_sc43_6's harness):
K1 TUNE 2, K2 FINE 2, K3 SHAPE 2 (PW2), K4 MIX, K5 FM, K6 BITSYNC, K7 WAVE 2, K8 RING; and the matrix's destinations keep the old order
(modmx.dests with KNOB_CODES_C_MX = use_osc2pg's row), each pointing at the knob where its code is now.

    python tools/emu_osc2pg2.py B5.25.bin B5.25_manifest.json [--ratio]
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc22_4 as T4  # noqa: E402
import vcf21 as V  # noqa: E402
import modmx as MX  # noqa: E402

V2 = dict(TUNE2=0, FINE2=1, WAVE2=2, PW2=3, MIX=4, BITSYNC=5, FM=6, RING=7)
WANT = ["TUNE2", "FINE2", "PW2", "MIX", "FM", "BITSYNC", "WAVE2", "RING"]


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    gc.collect(); e = T4.E20(img, man)
    L = {k: int(v, 16) for k, v in man["report"]["vcf20"]["labels"].items()}
    gfst = int(man["report"]["sc17"]["labels"]["c_gfst"], 16)
    e.call(gfst); blk = e.uc.reg_read(UC_ARM_REG_R0)
    v2 = lambda k: struct.unpack("b", bytes([e.r8(blk + V.V2_OFF + k)]))[0]
    for _ in range(30): e.vtick()
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.tailb(V.O_FLAGS) | 0x05]))          # MIDI 1: the mode on, the oscillator source
    e.btn(2); e.btn(8); e.call(L["c_vsetpage"], 0, 2)
    for k, name in enumerate(WANT):
        before = [v2(i) for i in range(8)]
        e.knob_raw(k, 3)
        after = [v2(i) for i in range(8)]
        moved = [i for i in range(8) if after[i] != before[i]]
        check(moved == [V2[name]], f"OSC 2 page K{k + 1} = {name} (moved {[list(V2)[i] for i in moved]})")
    if "--ratio" in sys.argv:                                                     # vcf21.use_ratio2: code 32 goes as the ratio's offset (1/256 semitone)
        import math, vcf21_dsp as VD
        sgn = lambda v: v - 0x10000 if v & 0x8000 else v
        addr = blk + V.V2_OFF + V2["TUNE2"]
        for v in (0, -10, -40, 1, 20, 63):
            e.uc.mem_write(addr, bytes([v & 0xFF]))
            got = [sgn(w & 0xFFFF) for _ in range(60) for w, ad in e.vtick() if ad == VD.VB0 and (w >> 16) & 0x7F == 32]
            want = round(12 * math.log2(V.r2_ratio(v)) * 256)
            check(got and got[-1] == want, f"TUNE 2 = {v}: ratio {V.r2_ratio(v)}, sent {got[-1] if got else None} (want {want})")
    if "--ratio" in sys.argv:                                                     # the granular (O_SIG bit 2: pad 31 without VA-drum): the old page 3, code 27 as it is
        import vcf21_dsp as VD
        e.uc.mem_write(V.TAIL + V.O_SIG, bytes([(e.r8(V.TAIL + V.O_SIG) & 0xF0) | 4]))
        e.call(L["c_vsetpage"], 0, 2)
        old = dict(zip(range(8), ["TUNE2", "PW2", "MIX", "FM", "FINE2", "BITSYNC", "WAVE2", "RING"]))
        for k in (1, 4):
            before = [v2(i) for i in range(8)]; e.knob_raw(k, 3); after = [v2(i) for i in range(8)]
            moved = [i for i in range(8) if after[i] != before[i]]
            check(moved == [V2[old[k]]], f"granular: page 3 K{k + 1} = {old[k]} as before (moved {[list(V2)[i] for i in moved]})")
        e.uc.mem_write(blk + V.V2_OFF + V2["TUNE2"], bytes([20]))
        got = [sgn(w & 0xFFFF) for _ in range(60) for w, ad in e.vtick() if ad == VD.VB0 and (w >> 16) & 0x7F == 32]
        check(got and got[-1] == 20, f"granular: code 27 (LFO -> size) sent as it is ({got[-1] if got else None})")
    V.use_osc2pg(); _r, D0 = MX.dests()
    V.use_osc2pg2(); rows, D = MX.dests()
    check([(c, p) for c, p, _i in D] == [(c, p) for c, p, _i in D0] and all(rows[p][i] == c for c, p, i in D),
          f"the matrix: the destinations in the old order, each at its knob now (page 3: {[(c, i) for c, p, i in D if p == 2]})")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} OSC2PG2 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
