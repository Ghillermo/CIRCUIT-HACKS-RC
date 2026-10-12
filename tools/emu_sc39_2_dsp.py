"""SC39.2 DSP tests: the captured sample at the start of the Master FX chain (sampler_dsp.PRE), on the dsp56kEmu interpreter.

    python tools/emu_sc39_2_dsp.py [SC39.2.bin SC39.2_manifest.json SC39.1.bin SC39.1_manifest.json]
Logic (sampler_dsp.code with pre_ret, in front of a stand-in chain that halves every frame and ends as fx_out does: `move #>$2e10,r1` + `rts`):
  * a recording holds the master as it came in, (L + R) / 2 of each frame, not what the chain made of it (the effects are not recorded);
  * a playing sample is added before the chain: the block that goes out is (the master + the sample) / 2 (the effects process the sample);
  * the capture never records the sample that plays in the same block;
  * M4 comes back, r1 = $2E10 (the chain's own ending), x0 = X:FX_ON at the chain's second instruction (the instruction the hook replaced).
With the images: fx_hook = `jmp smp_post` (SC39.1: `move x:>FX_ON,x0`), fx_out = `move #>$2e10,r1` + `rts` (SC39.1: `jmp smp_post` + nop), smp_post ends with
the replaced instruction and `jmp fx_hook + 2`; the program still ends below $4000.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
import masterfx_dsp as G  # noqa: E402
import sampler_dsp as S  # noqa: E402
import dsp56 as D  # noqa: E402

FXH, AT, DRV = 0x0800, 0x1000, 0x2000
TB, TMAX = 0x40000, 0x400
NF = 58
T_ = G.T


def chain():
    """the stand-in for fx_hook: [jmp smp_post] then, from FXH + 2: x0 kept in X:$3C02, every frame halved, the ending of fx_out"""
    a = D.Asm(FXH)
    a.emit(D.jmp(AT))
    a.emit(T_("move x0,x:>$3c02", "move #>$%x,r0" % G.BUF)); a.emit(D.NOP)
    a.emit(D.do_x, S.FRAMES, "ch_e")
    a.emit(T_("move x:(r0),a", "asr a", "move a,x:(r0)+", "move x:(r0),a", "asr a"))
    a.label("ch_e"); a.emit(T_("move a,x:(r0)+"))
    a.emit(T_("move #>$%x,r1" % G.BUF)); a.emit(D.RTS)
    return a.assemble()


def main(img=None, man=None, prev=None, prev_man=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    if img is not None:
        from dsp_session import dsp_program
        def prog(i): sp = dsp_program(i); return [int.from_bytes(sp[k:k + 3], 'big') for k in range(0, len(sp), 3)]
        dl = {k: int(v, 16) for k, v in man["report"]["sc16"]["dsp_labels"].items()}
        P0 = prog(img)
        first = T_("move x:>$%x,x0" % G.FX_ON)
        check(P0[dl["fx_hook"]:dl["fx_hook"] + 2] == D.jmp(dl["smp_post"]), "fx_hook = jmp smp_post")
        check(P0[dl["fx_out"]:dl["fx_out"] + 3] == [0x61F400, G.BUF, 0x00000C], "fx_out = move #>$2e10,r1 + rts (its own ending)")
        tail = first + D.jmp(dl["fx_hook"] + 2)
        hit = [k for k in range(dl["smp_post"], len(P0) - 3) if P0[k:k + 4] == tail]
        check(len(hit) == 1 and len(P0) <= 0x4000, f"smp_post ends with the replaced instruction + jmp fx_hook + 2 (at P:${hit[0] if hit else 0:x}); the program ends at P:${len(P0):x}")
        if prev is not None:
            pl = {k: int(v, 16) for k, v in prev_man["report"]["sc16"]["dsp_labels"].items()}; P1 = prog(prev)
            check(P1[pl["fx_hook"]:pl["fx_hook"] + 2] == first and P1[pl["fx_out"]:pl["fx_out"] + 3] == D.jmp(pl["smp_post"]) + [0]
                  and P1[:pl["fx_hook"]] == P0[:dl["fx_hook"]] and P1[pl["fx_hook"] + 2:pl["fx_out"]] == P0[dl["fx_hook"] + 2:dl["fx_out"]],
                  "the previous build: the hook at fx_out; everything before the chain and the chain itself are the same words")
    cw, _ = chain()
    w, lab = S.code(AT, TB, TMAX, pre_ret=FXH + 2)
    P = [0] * 0x4000
    P[FXH:FXH + len(cw)] = cw; P[AT:AT + len(w)] = w

    def setx(addr, v): return T_("move #>$%x,x0" % (v & 0xFFFFFF), "move x0,x:>$%x" % addr)
    def frames(f): return [x & 0xFFFFFF for i in range(NF) for x in f(i)]
    def go(steps, mem=(), dumps=()):
        drv = T_("move #>$123456,m4")
        for s in steps: drv += D.jsr(FXH) if s == "call" else s
        drv += T_("move m4,x:>$3c00", "move r1,x:>$3c01") + [0x00000C]
        P2 = list(P); P2[DRV:DRV + len(drv)] = drv
        return run(P2, DRV, mem=[('x', 0x3A, [NF]), ('x', G.FX_ON, [0x2A])] + list(mem), maxins=3_000_000,
                   dumps=[('x', S.SMB, 0x20), ('x', G.BUF, 2 * NF), ('y', TB, TMAX), ('x', 0x3C00, 3)] + list(dumps))
    st = lambda r, k: r[('x', S.SMB)][k - S.SMB]
    src = lambda i: (0x1000 * (i + 1), 0x0800 * (i + 1))
    magic = [('x', S.MAGIC_AT, [S.MAGIC])]
    # ---- record: the master as it came in
    r, ran = go([setx(S.STATE, 1), "call"], mem=[('x', G.BUF, frames(src))] + magic)
    y = r[('y', TB)]; out = r[('x', G.BUF)]
    check(st(r, S.LEN) == NF and y[:NF] == [(0x1800 * (i + 1)) // 2 for i in range(NF)], f"the capture = the master before the chain, (L + R) / 2 ({ran})")
    check(out[0::2] == [0x1000 * (i + 1) // 2 for i in range(NF)] and out[1::2] == [0x0800 * (i + 1) // 2 for i in range(NF)], "the block that goes out went through the chain (halved)")
    check(r[('x', 0x3C00)] == [0x123456, G.BUF, 0x2A], f"M4 back, r1 = $2E10, x0 = X:FX_ON at the chain's second instruction ({[hex(v) for v in r[('x', 0x3C00)]]})")
    # ---- play: the sample goes through the chain
    LENP = 300
    ramp = [(i + 1) * 0x100 for i in range(LENP)]
    base = [('y', TB, ramp), ('x', S.LEN, [LENP]), ('x', S.PREV, [0])] + magic
    pre = setx(S.SF, 0) + setx(S.EF, 0x7FFFFF) + setx(S.INCI, 1) + setx(S.INCF, 0) + setx(S.MODE, 0) + setx(S.CMD, 1)
    r, _ = go([pre, "call"], mem=base + [('x', G.BUF, [0] * 2 * NF)])
    out = r[('x', G.BUF)]
    check(out[0::2] == [v // 2 for v in ramp[:NF]] and out[1::2] == [v // 2 for v in ramp[:NF]] and st(r, S.PLAY) == 1, "CMD 1 on a silent master: the sample halved by the chain on L and R")
    r, _ = go([pre, "call"], mem=base + [('x', G.BUF, frames(src))])
    out = r[('x', G.BUF)]
    check(out[0::2] == [(0x1000 * (i + 1) + ramp[i]) // 2 for i in range(NF)], "on a master with signal: (the master + the sample) / 2")
    # ---- a recording started while a sample plays never holds the sample (the record comes first; a new recording stops the playback)
    r, _ = go([pre, "call", setx(S.STATE, 1), "call"], mem=base + [('x', G.BUF, [0] * 2 * NF)])
    y = r[('y', TB)]
    first_blk = [v // 2 for v in ramp[:NF]]                                   # what the first call left in the buffer: the master of the second call
    check(y[:NF] == first_blk and st(r, S.PLAY) == 0 and st(r, S.LEN) == NF, "recording while playing: the capture = the master only, the playback stopped")
    print("SC39.2 DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    if len(a) > 4: sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
    sys.exit(1 if main() else 0)
