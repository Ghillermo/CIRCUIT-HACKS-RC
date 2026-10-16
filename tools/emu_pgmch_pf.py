"""SC41.6 ARM tests: the patch flip stays on the MIDI track's channel with the PGM channels (pgmch.use_pf).

    python tools/emu_pgmch_pf.py NEW.bin NEW_manifest.json PREVIOUS.bin PREVIOUS_manifest.json
  * MIDI 1 in patch flip on channel 1, shared with Synth 1; the PGM listen channel = 1, the output channel = 10; a note of MIDI 1 through the
    transmitter's note-on method (the vtable 0x08059FC4): its program change goes out on channel 1 only and into Synth 1 (the previous build, SC41.5:
    also out on channel 10);
  * PGM Tx off: nothing out, still into Synth 1;
  * an external program change on the listen channel is still sent again on the output channel.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_PC
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc08 import E8  # noqa: E402
import pgmch as PG  # noqa: E402

B = 0x08010000
VT_NOTE_ON = 0x08059FC4
PC_TARGET, PC_AFTER = 0x080518EE, 0x080518F0
MSG = 0x2006E100
PF_MIDI1 = 0x20                                               # the transmitter's + 0x18: patch flip of MIDI 1 (bit 5), PGM Tx (bit 2)


def run(img, man):
    e = E8(img)
    L = {k: int(v, 16) for k, v in man["report"]["pgmch"]["labels"].items()}
    A = e.r32(PG.CTX); X = e.r32(e.r32(A) + 0x1C)
    hits = []
    def tgt(uc, a, s_, d):
        hits.append((uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2) & 0xFF)); uc.reg_write(UC_ARM_REG_PC, PC_AFTER | 1)
    e.uc.hook_add(UC_HOOK_CODE, tgt, begin=PC_TARGET, end=PC_TARGET)
    e.call(L["c_pgset"], PG.B_RX, 0); e.call(L["c_pgset"], PG.B_TX, 9)
    e.uc.mem_write(e.r32(X + 0xC) + 2, b"\0")                  # MIDI 1 on channel 1
    s1 = e.r8(A + 9)
    fl_rx, fl_tx = e.r8(A + 0x14), e.r8(X + 0x18)
    note_on = e.r32(VT_NOTE_ON) & ~1
    def flip(tx_on):
        e.uc.mem_write(A + 0x14, bytes([fl_rx | 0x04])); e.uc.mem_write(X + 0x18, bytes([(fl_tx | PF_MIDI1 | 0x04) if tx_on else (fl_tx | PF_MIDI1) & ~0x04]))
        hits.clear(); e.ev.clear()
        e.call(note_on, X, 2, 5, 100, maxins=8_000_000)
        return (list(hits), [x[1][:4] for x in e.ev if x[0] == "ext"])
    out = dict(s1=s1, flip=flip(True), notx=flip(False))
    e.uc.mem_write(A + 0x14, bytes([fl_rx | 0x04])); e.uc.mem_write(X + 0x18, bytes([fl_tx | 0x04]))
    hits.clear(); e.ev.clear(); e.uc.mem_write(MSG, bytes([0xC0, 7, 0, 0]))
    e.call(0x08051720, A, MSG, maxins=8_000_000)
    out["ext_in"] = (list(hits), [x[1][:4] for x in e.ev if x[0] == "ext"])
    del e; gc.collect()
    return out


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    o = run(img, man)
    check(o["s1"] == 0, f"Synth 1 listens on channel 1 ({o['s1']})")
    check(o["flip"] == ([(0, 5)], ["c005"]), f"a note of MIDI 1 in patch flip: out on its channel 1 only, into Synth 1 ({o['flip']})")
    check(o["notx"] == ([(0, 5)], []), f"PGM Tx off: nothing out, into Synth 1 ({o['notx']})")
    check(o["ext_in"] == ([(0, 7)], ["c907"]), f"an external program change on the listen channel 1: to Synth 1 (its channel), sent again on 10 ({o['ext_in']})")
    gc.collect(); p = run(prev, prev_man)
    check(p["flip"] == ([(0, 5)], ["c005", "c905"]), f"the previous build: the patch flip also out on the general channel 10 ({p['flip']})")
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
