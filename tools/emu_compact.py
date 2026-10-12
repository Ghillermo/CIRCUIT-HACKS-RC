"""drums2_dsp.COMPACT (SC36): the tables TATK / TDEC stored as their useful halves, differential test against a build without it.

    python tools/emu_compact.py NEW.bin NEW_manifest.json REF.bin REF_manifest.json
  * the tables: TATK = the first 65 words of the full table, TDEC = its last 64; the program is 123 words shorter;
  * drums (dctl, drum 0): for every envelope value ENVS -64..63, in the attack and in the decay phase, the drum block after one control block is
    identical in both images;
  * the VCA-VCF mode (vpre, two voices): ATK / DEC / SUS / REL swept over 0..127 (line input, oscillator, VA-drum), and random voice states (every
    parameter 0..127, ACT, the flags of DFLAGS, gate, note, velocity) over several blocks with gate changes: the voice blocks, both oscillator
    blocks and the output are identical in both images.
"""
from __future__ import annotations
import gc, json, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
from emu_masterfx_dsp import u24  # noqa: E402
import drums2_dsp as DD  # noqa: E402
import vcf21_dsp as V  # noqa: E402
import masterfx_dsp as G  # noqa: E402

N, RING = 32, 0x1000
VOICE_R3, SC16_BLK = 0x1E8D, 0x3A10
OSB, OS2 = V.OSB0, V.OS2B0


def main(img, man, ref, rman, shrink=123):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    prog = lambda im: (lambda b: [int.from_bytes(b[i:i + 3], 'big') for i in range(0, len(b), 3)])(dsp_program(im))
    lab = lambda m: {k: int(v, 16) for k, v in m["report"]["sc16"]["dsp_labels"].items()}
    P0, PR, dl, dr = prog(img), prog(ref), lab(man), lab(rman)
    t = DD.tables()
    check(P0[dl["TATK"]:dl["TATK"] + 65] == t["TATK"][:65] and P0[dl["TDEC"]:dl["TDEC"] + 64] == t["TDEC"][64:]
          and PR[dr["TDEC"]:dr["TDEC"] + 128] == t["TDEC"], "tables: TATK = its first 65 words, TDEC = its last 64 (the reference has them whole)")
    if shrink is not None:
        check(len(PR) - len(P0) == shrink, f"program {len(P0):#x} words, {len(PR) - len(P0)} fewer than the reference ({len(PR):#x})")

    # ---------------------------------------------------------------- drums: dctl
    common = [('x', 0x3A, [N]), ('x', 0x39, [5]), ('x', SC16_BLK, [0] * 36), ('x', 0x1ED6, [0x9F, 0xA3, VOICE_R3])]
    def dctl(P, d, vals):
        blk = [vals.get(i, 0) & 0xFFFFFF for i in range(DD.STRIDE)]
        voice = [0x3B00, 0xF0, 0x400000, 0, 0, 0, 1, 0] + [0] * 10
        res, ran = run(P, d["dctl"], mem=common + [('x', DD.DB, blk), ('x', 0xA3, [0, 0x10000, 0, 0, 0]), ('x', 0x9F, [0]), ('x', VOICE_R3, voice)],
                       dumps=[('x', DD.DB, DD.STRIDE), ('x', VOICE_R3, 18), ('x', 0xA3, 5)],
                       regs_code=G.T("move #>$9f,r1", "move #>$a3,r2", "move #>$%x,r3" % VOICE_R3))
        assert 'pc=00' in ran, ran
        return res
    bad = []
    for envs in range(-64, 64):
        for eph, env in ((0, 0x7FFFFF), (1, 0x200000)):
            v = {DD.ENVS: envs, DD.EPH: eph, DD.ENV: env, DD.MB: 0, DD.MBL: 0}
            a, b = dctl(P0, dl, v), dctl(PR, dr, v)
            if a != b: bad.append((envs, eph))
    check(not bad, f"drums: ENVS -64..63 in the attack / decay phase, the same drum block in both ({bad[:4]})")
    gc.collect()

    # ---------------------------------------------------------------- VCA-VCF: vpre
    def vpre(P, d, st, ring):
        blk, osb, os2 = st
        mem = [('x', 0x3A, [N]), ('x', V.VB0, blk), ('x', V.FLAGS, [0]), ('y', V.RING_PTR, [RING]), ('y', RING, ring), ('x', OSB, osb), ('x', OS2, os2)]
        res, ran = run(P, d["vpre"], mem=mem, dumps=[('x', V.VB0, 2 * V.VBS), ('y', RING, 2 * N), ('x', OSB, 96), ('x', OS2, 96)], regs_code=[])
        assert 'pc=00' in ran, ran
        return (res[('x', V.VB0)], res[('x', OSB)], res[('x', OS2)]), res[('y', RING)]
    rnd = random.Random(36)
    def same(st, blocks, gates=None):
        sa = sb = st
        for k in range(blocks):
            if gates and k in gates:
                for s in (sa, sb):
                    for t_, g in gates[k]: s[0][V.VBS * t_ + V.GATE] = g
            ring = [u24(rnd.randrange(-0x300000, 0x300000)) for _ in range(2 * N)]
            sa, oa = vpre(P0, dl, tuple(list(x) for x in sa), ring)
            sb, ob = vpre(PR, dr, tuple(list(x) for x in sb), ring)
            if sa != sb or oa != ob: return False
        return True
    def state(voices):
        blk, osb, os2 = [0] * (2 * V.VBS), [0] * 96, [0] * 96
        for t_, kw in enumerate(voices):
            for off, v in kw.get("p", {}).items(): blk[V.VBS * t_ + off] = v & 0xFFFFFF
            blk[V.VBS * t_ + V.ACT], blk[V.VBS * t_ + V.NOTE] = kw.get("act", 0), kw.get("note", 60)
            blk[V.VBS * t_ + V.VEL], blk[V.VBS * t_ + V.GATE], blk[V.VBS * t_ + V.GNEW] = kw.get("vel", 100), kw.get("gate", 0), kw.get("gnew", 0)
            osb[48 * t_ + V.DFLAGS_OFF], osb[48 * t_ + V.NOTE2_OFF] = kw.get("df", 0), kw.get("note2", 64)
        return blk, osb, os2
    neutral = {o: 64 for o in range(2, 18)}
    for name, act, df in (("line input", 1, 0), ("oscillator", 2, 0), ("VA-drum", 2, 4), ("VA-drum + velocity", 2, 12)):
        bad = []
        for v in range(0, 128, 3):
            p = dict(neutral); p.update({V.P_ATK: v, V.P_DEC: 127 - v, V.P_SUS: v, V.P_REL: (v * 5) % 128})
            st = state([dict(p=p, act=act, df=df, gate=1, gnew=1), dict(p=dict(neutral), act=act, df=df, gate=1, gnew=1)])
            if not same(st, 3, {2: [(0, 0)]}): bad.append(v)
        check(not bad, f"{name}: ATK / DEC / SUS / REL swept, gate on then off: identical ({bad[:4]})")
        gc.collect()
    bad = []
    for k in range(40):
        voices = [dict(p={o: rnd.randrange(128) for o in range(2, 18)}, act=rnd.choice((0, 1, 2)), df=rnd.randrange(16), gate=rnd.randrange(2),
                       gnew=rnd.randrange(2), note=rnd.randrange(24, 100), note2=rnd.randrange(24, 100), vel=rnd.randrange(128)) for _ in range(2)]
        if not same(state(voices), 4, {1: [(0, rnd.randrange(2)), (1, 1)], 3: [(0, 0), (1, 0)]}): bad.append(k)
    check(not bad, f"40 random voice states, 4 blocks with gate changes: identical ({bad[:4]})")
    print("COMPACT RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
