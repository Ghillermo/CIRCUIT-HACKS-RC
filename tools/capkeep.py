"""RC4.12 / Beta 5.61 (a fix; the user, 2026-11-14: «When a sample capture is running and a new project is loaded, the capture stops automatically …
Can we not stop it?» → «fix and beta»): a latched or armed capture of Master FX's sample goes on through a project load.

Why it stopped: every project load (a new pack, a new project too) ends in persist19's RESYNC (c_rs, the DSP service tick), whose c_clrall (pad 8's
«everything off») also clears the sample: S_JF's REC bit off, S_SMT = 0 (not latched, not armed), the stop command.  It was never a design choice:
c_clrall served pad 8 first (SC33) and the load reused it.

c_ckeep, in place of c_rs's call (of c_clrall, or of loopcarry's c_lcclr in the betas): S_JF and S_SMT read, the call, then, when S_SMT was latched or
armed (bits 30 / 31), S_SMT back (the press time, the request bits) and S_JF's REC bit back as it was: the DSP's STATE never drops, the recording goes on
where it was (the stop command only ends a playback, which a recording has already stopped).  A held capture (pad 32 held) ends when its view is left,
before any load: unchanged.  Pad 8 still stops everything (its own call).  The capture records what the master plays while the project loads.
RC4.12: at the end of the image; Beta 5.61: in the dspz gap (dspz.add)."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import Asm, b_cond, bics_reg, bl, ldr_imm, lsrs_imm, mov_reg, movs_imm, ands_reg, orrs_reg, pop_list, push_list, raw, str_imm, h  # noqa: E402
from thumb import bl as bl_enc  # noqa: E402
import build_sc17 as B17  # noqa: E402

S_JF, S_SMT, REC = B17.S_JF, B17.S_SMT, B17.SMB_REC
assert S_SMT % 4 == 0 and S_SMT < 128 and REC == 1


RESEND = False                                            # RC4.14 / Beta 5.63 (use_resend)


def use_resend():
    """RC4.14 / Beta 5.63 (a fix, the 2026-11-14 bug hunt, CK-1): a restart that keeps the RAM (an install, the black box's reset, a fault, a short
    power cut) keeps the Master FX block, so the boot's load went through c_ckeep with a latched capture: S_JF's REC bit kept, and its bits 6-7
    (the last STATE sent = 1) too, while the DSP was reloaded (its init zeroes X $0-$5FFF: the sampler's STATE 0).  c_smtick sends STATE only
    when (S_JF & 3) != S_JF >> 6: never again; pad 32 showed a capture that recorded nothing.  Now the keep path clears bits 6-7 too, so the next
    tick sends STATE = REC: after a normal load the DSP is at 1 already (a recording goes on: no edge), after a restart it starts again (+ 4 B)."""
    global RESEND
    RESEND = True


def ldrb_w(rt, rn, off): return h(0xF890 | rn) + h(rt << 12 | off)
def strb_w(rt, rn, off): return h(0xF880 | rn) + h(rt << 12 | off)


def arm_code(base, orig):
    a = Asm(base); E = a.emit
    # ---- c_ckeep (r0 = the Master FX block): the reset of the load, the capture kept
    a.label("c_ckeep")
    E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0)
    E(raw, ldrb_w(5, 4, S_JF)); E(ldr_imm, 6, 4, S_SMT)
    E(bl, orig)
    E(lsrs_imm, 0, 6, 30); E(b_cond, "ck_x", "eq")                                   # neither latched nor armed: as before
    E(str_imm, 6, 4, S_SMT)
    E(raw, ldrb_w(0, 4, S_JF)); E(movs_imm, 1, REC); E(ands_reg, 1, 5); E(orrs_reg, 0, 1)
    if RESEND: E(movs_imm, 1, 0xC0); E(bics_reg, 0, 1)                               # (RESEND) the last STATE sent forgotten: the next tick resends it
    E(raw, strb_w(0, 4, S_JF))
    a.label("ck_x"); E(pop_list, [4, 5, 6], pc=True)
    return a.assemble()


def install(img, report, base=None):
    """c_rs's call of c_clrall (or of loopcarry's c_lcclr) -> c_ckeep, which calls it.  Appends its code at the end of the image (base = its address
    there, or where dspz.add will move it: -> labels, code, prev); without base the end of the image and the report written here (RC4.12)."""
    import ct_fw
    import hole
    BASE = ct_fw.APP_BASE
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    targets = [lab("sc17", "c_clrall")] + ([lab("loopcarry", "c_lcclr")] if "loopcarry" in report else [])
    rs, rx = lab("persist19", "c_rs"), lab("persist19", "rs_x")
    sites = [(x, t) for x in range(rs, rx, 2) for t in targets if bytes(img[x - BASE:x - BASE + 4]) == bl_enc(x, t)]
    assert len(sites) == 1, sites
    site, orig = sites[0]
    end = base is None
    if end:
        while len(img) % 4:
            img += bytes([0xFF])
        base = BASE + len(img)
    code, labels = arm_code(base, orig)
    img += code
    img[site - BASE:site - BASE + 4] = bl_enc(site, labels["c_ckeep"])
    hole.rehash(img, report, site)
    prev = dict(site=site, orig=orig)
    if end:
        report["capkeep"] = dict(arm_start=hex(base), site=hex(site), orig=hex(orig), labels={k: hex(v) for k, v in labels.items()})
        return labels
    return labels, code, prev
