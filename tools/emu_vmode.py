"""SC47.5 ARM test (vmode, poly.use_v4): the voice modes of the own synth of MIDI 1 / 2 on pad 32 (emu_poly's harness: the real controller, the
template view, the note vtable, the whole DSP service chain with vmode's tick at its head, the DSP's writes into a dict).

    python tools/emu_vmode.py NEW.bin NEW_manifest.json

  * pad 32 opens the row: pads 17-21 = the five modes (the current bright, the others dim), pads 9-16 / 22-24 dark; pad 32 in the mode's colour;
  * pad 19 = portamento: the byte 0xC0 | modes, retrig's c_rtoff = 1 (no new gate over a held note), c_pyflag = 0; K1 / K2 while open = the time /
    the detune (clamped, their LEDs); the tick writes GK[time] to OSC2 + 44; closed, K1 goes to the engine again; the row closes by itself;
  * Shift + pad 29 = the next mode (poly: c_pyflag = 1, GK 0 written);
  * unison: a note = every voice on it, its offset word spread over +-detune x 258 and the target x 1/2; another note: every voice moves, no target 0
    between; let go while another is held: still held; the last one: let go;
  * the old byte (0xA0 | legato t | poly 2 + t) is read;
  * saved with the patch: projsyn's gather writes padding + 126..129 = 0xB6, 0x50 | mode, the time, the detune; its apply brings them back.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_LR, UC_ARM_REG_PC
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
import emu_poly as EP  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import poly as P  # noqa: E402
import vmode as VM  # noqa: E402
import modmx as MX  # noqa: E402
import vcf21_dsp as VD  # noqa: E402
import modesel as MS  # noqa: E402
import projsyn as PS  # noqa: E402
MGR = T.MGR


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    R = man["report"]
    if P.adopt(R): VM.use_v2()                                                        # (SC47.6: the six-record layout, seven modes)
    if R["vmode"].get("prev", {}).get("v3"): VM.use_v3()                              # (SC47.7: the pads in the user's order)
    pad_of = lambda m: 16 + (VM.ORDER.index(m) if VM.V3 else m)
    col_at = lambda k: VM.COLS[VM.ORDER[k] if VM.V3 else k]
    e = T.EL(img)
    vl = {k: int(v, 16) for k, v in R["vcf20"]["labels"].items()}
    sl = {k: int(v, 16) for k, v in R["sc06"]["labels"].items()}
    pl = {k: int(v, 16) for k, v in R["poly"]["labels"].items()}
    ml = {k: int(v, 16) for k, v in R["vmode"]["labels"].items()}
    rl = {k: int(v, 16) for k, v in R["retrig"]["labels"].items()}
    yl = {k: int(v, 16) for k, v in R["projsyn"]["labels"].items()}
    def skip(uc): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    for ad in (sl["c_non"], sl["c_noff"], EP.STOCK_TX_ON, EP.STOCK_TX_OFF, EP.REC_GATE):
        e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: skip(uc), begin=ad, end=ad)
    dsp, log = {}, []
    def w(uc, a, s, d):
        v, ad = uc.reg_read(UC_ARM_REG_R1) >> 8, uc.reg_read(UC_ARM_REG_R2); dsp[ad] = v; log.append((ad, v)); skip(uc)
    e.uc.hook_add(UC_HOOK_CODE, w, begin=P.DSP_WRITE, end=P.DSP_WRITE)
    def rd(uc, a, s, d): uc.reg_write(UC_ARM_REG_R0, 0); skip(uc)
    e.uc.hook_add(UC_HOOK_CODE, rd, begin=0x08029344, end=0x08029344)
    e.at(100000); e.transport(0)
    for _ in range(30): e.at(e.t + 40); e.call(vl["c_vtick"], maxins=3_000_000)
    rec = lambda t, v, f: VD.PV_REC0 + VD.PV_RS * (VD.PV_N * t + v) + f
    def tick(n=1):
        for _ in range(n): e.at(e.t + 1); e.call(ml["c_vmtick"], maxins=8_000_000)
    non, noff = e.r32(MX.NOTE_VT) & ~1, e.r32(MX.NOTE_VT + 4) & ~1
    def on(n, v=100, t=0): e.call(non, EP.TXOBJ, 2 + t, n, v, maxins=8_000_000)
    def off(n, t=0): e.call(noff, EP.TXOBJ, 2 + t, n, 0, maxins=8_000_000)
    def mode(k): e.uc.mem_write(MS.RAM, bytes(8)); e.pad(26); e.pad(MS.ROW + k); e.pad(26)
    def r0(fn, *a): e.call(fn, *a, maxins=4_000_000); return e.uc.reg_read(UC_ARM_REG_R0)
    vm = lambda t: r0(pl["c_vmget"], t)
    def knob(k, d): e.call(0x08033848, MGR, k, d & 0xFFFFFFFF, maxins=8_000_000)
    def shift(o): e.set_p0(e.r32(MGR + 0xC), 1 if o else 0)
    def frame(): e.at(e.t + 20); return X.frame(e)
    tailb = lambda: e.r8(r0(rl["c_rtb"]))
    s16 = lambda v: v - (1 << 24) if v & 0x800000 else v

    e.btn(2); e.btn(8); mode(2)
    e.call(pl["c_vmset"], 0, 0, maxins=1_000_000); e.call(pl["c_vmset"], 1, 0, maxins=1_000_000)
    tick(2)
    f = frame()
    check(f[31] & 0xFF == VM.COLS[0][0] and tailb() == 0xC0, f"retrigger: pad 32 green ({f[31]:#x}), the byte {tailb():#x}")
    # ---- the row
    e.pad(31); f = frame()
    row = [f[16 + k] & 0xFF for k in range(VM.N)]
    dark = all(f[i] == 0 for i in list(range(8, 16)) + list(range(16 + VM.N, 24)))
    check(row == [col_at(0)[0]] + [col_at(k)[1] for k in range(1, VM.N)] and dark, f"pad 32: the row on pads 17-{16 + VM.N} ({[hex(x) for x in row]}), the rest of 9-24 dark ({dark})")
    e.pad(pad_of(2)); f = frame()
    check(vm(0) == 2 and tailb() == 0xC2 and r0(rl["c_rtoff"], 0) == 1 and r0(pl["c_pyflag"], 0) == 0 and f[pad_of(2)] & 0xFF == VM.COLS[2][0] and f[31] & 0xFF == VM.COLS[2][0],
          f"pad 19 = portamento: the byte {tailb():#x}, no retrigger over a held note, not poly; pad 19 / 32 cyan")
    knob(0, 10); knob(1, -50); f = frame()
    ram = VM.RAM
    g, d = e.r8(ram + 8), e.r8(ram + 10)
    kl = (f[60], f[61])
    want_kl = (((16 + (58 * 7 >> 3)) << 8) | VM.KCOL[0], (16 << 8) | VM.KCOL[1])
    check(g == 58 and d == 0 and kl == want_kl, f"K1 / K2 while open: the time {g}, the detune {d} (clamped); their LEDs {[hex(x) for x in kl]}")
    log.clear(); tick(2)
    gw = [v for a, v in log if a == VD.OS2B0 + VD.GK_OFF]
    check(gw == [VM.gk(58)], f"the tick writes GK[58] = {VM.gk(58):#x} to OSC2 + 44 once ({[hex(x) for x in gw]})")
    e.pad(31); knob(0, 5); f = frame()
    check(e.r8(ram + 8) == 58 and f[16] & 0xFF != VM.COLS[0][0], "pad 32 again: closed (K1 back to the engine)")
    e.pad(31); frame(); e.at(e.t + 400); f = frame()
    check(e.r8(ram) == 0, "the row closes by itself when its LEDs were not asked for (another view)")
    # ---- Shift + pad 29
    if VM.V3: e.call(pl["c_vmset"], 0, VM.ORDER[-2], maxins=1_000_000)               # (SC47.7: poly comes last)
    shift(True); e.pad(28); f = frame(); shift(False)
    log.clear(); tick(2)
    gw = [v for a, v in log if a == VD.OS2B0 + VD.GK_OFF]
    check(vm(0) == 3 and r0(pl["c_pyflag"], 0) == 1 and f[28] & 0xFF == VM.COLS[3][0] and gw == [0], f"Shift + pad 29: poly (pad 29 magenta with Shift, GK 0 written {gw})")
    # ---- unison
    e.pad(31); frame(); e.pad(pad_of(4)); knob(1, 40); frame(); e.pad(31)
    tick(3)
    check(vm(0) == 4 and dsp.get(VD.OS2B0 + VD.PV_OFF) == VD.PV_REC0, f"pad 21 = unison: the records on ({vm(0)})")
    log.clear(); on(60, 100); tick(3)
    h = 40 * P.DT_K
    dts = [s16(dsp.get(rec(0, v, P.O_DTW), 0)) for v in range(4)]
    notes = [dsp.get(rec(0, v, VD.PV_NOTE)) for v in range(4)]
    tg = [dsp.get(rec(0, v, VD.PV_TGT)) for v in range(4)]
    check(notes == [60] * 4 and dts == [-h, -h // 3, h // 3, h] and tg == [(100 << 16) >> 1] * 4,
          f"a note: every voice on it ({notes}), the offsets {dts}, the targets {[hex(x) for x in tg]}")
    log.clear(); on(64, 90); tick(3)
    notes = [dsp.get(rec(0, v, VD.PV_NOTE)) for v in range(4)]
    zero = [a for a, v in log if a in [rec(0, v_, VD.PV_TGT) for v_ in range(4)] and v == 0]
    check(notes == [64] * 4 and not zero, f"another note: every voice moves ({notes}), no target 0 between ({len(zero)})")
    vs = lambda v: e.r8(P.PY + 4 + 4 + P.VS_ * v + P.VS)
    off(64); tick(2)
    held = [vs(v) & P.HELD for v in range(4)]
    off(60); tick(2)
    rel = [vs(v) & P.HELD for v in range(4)]
    check(all(held) and not any(rel), f"let go with 60 held: still held ({held}); the last one: let go ({rel})")
    # ---- the old byte
    b = r0(rl["c_rtb"])
    e.uc.mem_write(b, bytes([0xA1])); m1 = (vm(0), vm(1))
    e.uc.mem_write(b, bytes([0xA6])); m2 = (vm(0), vm(1))
    check(m1 == (1, 0) and m2 == (3, 1), f"the old byte: 0xA1 = legato / retrigger {m1}, 0xA6 = poly / legato {m2}")
    # ---- the patch: projsyn's gather / apply (mpatch's IO on RAM)
    e.call(pl["c_vmset"], 0, 4, maxins=1_000_000); e.uc.mem_write(ram + 8, bytes([70])); e.uc.mem_write(ram + 10, bytes([90]))
    e.call(yl["c_ysrun"], 0, 0, maxins=20_000_000)
    got = list(e.uc.mem_read(PS.IMG0 + VM.POFS, 4))
    e.call(pl["c_vmset"], 0, 1, maxins=1_000_000); e.uc.mem_write(ram + 8, bytes([10])); e.uc.mem_write(ram + 10, bytes([5]))
    e.call(yl["c_ysrun"], 0, 1, maxins=20_000_000)
    back = (vm(0), e.r8(ram + 8), e.r8(ram + 10))
    check(got == [VM.PTAG, 0x54, 70, 90] and back == (4, 70, 90), f"with the patch: padding + 126 = {[hex(x) for x in got]}, applied back {back}")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} VMODE ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
