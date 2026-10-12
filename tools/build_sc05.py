"""Circuit Tracks 4486 — SC05 = SC04 + internal MIDI loopback for shared channels.

When MIDI 1/2 share a channel with an internal track, what the MIDI track sends
is ALSO delivered internally (no cable needed):
  * notes (from the tx vtable 0x08059FC4/0x08059FC8, track ids 2/3) are injected
    only if the MIDI track channel equals Synth 1 or Synth 2 channel (never the
    Drums channel: the note router would hand them back to the MIDI track
    itself -> feedback loop);
  * template CC/NRPN messages (helper 0x0804A356, used only by MIDI-track
    templates) are injected if the channel equals the Synth 1 / Synth 2 / Drums
    CC-receive channel.
Injection = call the MIDI-in dispatcher 0x08051720(ctx=[0x200069E4], msg) while
bit 5 of the receiver flags byte [ctx+0x14] is set ("internal").  The three
recorder gates (note on 0x0802E56A, note off 0x0802E5CC, parameter automation
0x0802E62C) return without recording while that bit is set, so injected
messages make sound / move parameters but are never recorded into the target
track.  What the user plays or turns on the MIDI track is recorded there as in
stock.  Injection is skipped while the stock MIDI-in enable flag (0x20000A6C
bit 2) blocks input, and respects the stock Rx Note/CC toggles.
"""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ct_fw  # noqa: E402
import build_shared_channels as sc  # noqa: E402
import build_sc04 as s4  # noqa: E402
from thumb import (Asm, b, b_cond, b_w, bl, bx_lr, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, ldrb_reg,  # noqa: E402
                   lsls_imm, lsrs_imm, mov_reg, movs_imm, movt, movw, orrs_reg, bics_reg, pop_list,
                   push_list, raw, strb_imm, subs_imm3, add_sp_imm, sub_sp_imm)

BASE = ct_fw.APP_BASE
MARKER = b"SC05"
CTX_PTR = 0x200069E4            # MIDI-in callback context (receiver object A)
MIDI_IN_FLAG = 0x20000A6C       # bit 2 set -> MIDI input disabled (stock check 0x080223FA)
DISPATCH = 0x08051720
SEND = 0x0803BEDA
NOTE_ON = 0x08029EFE
NOTE_OFF = 0x08029F2A
VT_NOTE_ON = 0x08059FC4
VT_NOTE_OFF = 0x08059FC8
CC_HELPER = 0x0804A356
GATES = {0x0802E56A: "push {r3, r4, r5, r6, r7, lr}|mov r6, r0",
         0x0802E5CC: "push {r4, r5, r6, lr}|mov r5, r0",
         0x0802E62C: "push {r4, r5, r6, lr}|mov r4, r0"}
INTERNAL_BIT = 0x20


def ext_code(base: int, stock: bytes):
    a = Asm(base)
    # ---- c_inject(r0 = msg ptr): dispatch internally with the "internal" bit set
    a.label("c_inject")
    a.emit(push_list, [4, 5], lr=True)
    a.emit(mov_reg, 5, 0)
    a.emit(movw, 1, MIDI_IN_FLAG & 0xFFFF)
    a.emit(movt, 1, MIDI_IN_FLAG >> 16)
    a.emit(ldr_imm, 1, 1, 0)
    a.emit(lsls_imm, 1, 1, 29)                 # bit2 -> N : input disabled
    a.emit(b_cond, "inj_out", "mi")
    a.emit(movw, 4, CTX_PTR & 0xFFFF)
    a.emit(movt, 4, CTX_PTR >> 16)
    a.emit(ldr_imm, 4, 4, 0)                   # r4 = ctx A
    a.emit(cmp_imm, 4, 0)
    a.emit(b_cond, "inj_out", "eq")
    a.emit(ldrb_imm, 1, 4, 0x14)
    a.emit(movs_imm, 2, INTERNAL_BIT)
    a.emit(orrs_reg, 1, 2)
    a.emit(strb_imm, 1, 4, 0x14)
    a.emit(mov_reg, 1, 5)
    a.emit(mov_reg, 0, 4)
    a.emit(bl, DISPATCH)
    a.emit(ldrb_imm, 1, 4, 0x14)
    a.emit(movs_imm, 2, INTERNAL_BIT)
    a.emit(bics_reg, 1, 2)
    a.emit(strb_imm, 1, 4, 0x14)
    a.label("inj_out")
    a.emit(pop_list, [4, 5], pc=True)

    # ---- note wrappers (vtable targets): r0 tx iface, r1 track, r2 note, r3 vel
    for name, orig, status in (("c_non", NOTE_ON, 0x90), ("c_noff", NOTE_OFF, 0x80)):
        a.label(name)
        a.emit(push_list, [4, 5, 6, 7], lr=True)
        a.emit(sub_sp_imm, 12)                 # keep 8-byte alignment, 4-byte msg buffer
        a.emit(mov_reg, 4, 0)
        a.emit(mov_reg, 5, 1)
        a.emit(mov_reg, 6, 2)
        a.emit(mov_reg, 7, 3)
        a.emit(bl, orig)                       # stock behaviour first (external send)
        a.emit(subs_imm3, 0, 5, 2)
        a.emit(cmp_imm, 0, 1)
        a.emit(b_cond, f"{name}_done", "hi")    # only MIDI 1 / MIDI 2
        a.emit(ldr_imm, 0, 4, 0x0C)            # tx channel table
        a.emit(ldrb_reg, 1, 0, 5)              # MIDI track channel
        a.emit(ldrb_imm, 2, 0, 0)              # Synth 1 channel
        a.emit(cmp_reg, 1, 2)
        a.emit(b_cond, f"{name}_go", "eq")
        a.emit(ldrb_imm, 2, 0, 1)              # Synth 2 channel
        a.emit(cmp_reg, 1, 2)
        a.emit(b_cond, f"{name}_done", "ne")
        a.label(f"{name}_go")
        a.emit(mov_reg, 3, 13)                 # r3 = sp
        a.emit(movs_imm, 0, status)
        a.emit(orrs_reg, 0, 1)
        a.emit(strb_imm, 0, 3, 0)
        a.emit(strb_imm, 6, 3, 1)
        a.emit(strb_imm, 7, 3, 2)
        a.emit(mov_reg, 0, 3)
        a.emit(bl, "c_inject")
        a.label(f"{name}_done")
        a.emit(raw, bytes.fromhex("03b0"))     # add sp,#12
        a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # ---- template CC helper replacement: (r0 ch, r1 status, r2 d1, r3 d2)
    a.label("c_cc")
    a.emit(push_list, [4], lr=True)
    a.emit(sub_sp_imm, 8)
    a.emit(orrs_reg, 0, 1)
    a.emit(mov_reg, 4, 13)
    a.emit(strb_imm, 0, 4, 0)
    a.emit(strb_imm, 2, 4, 1)
    a.emit(strb_imm, 3, 4, 2)
    a.emit(mov_reg, 1, 4)
    a.emit(movs_imm, 0, 7)
    a.emit(bl, SEND)                           # stock send
    a.emit(ldrb_imm, 0, 4, 0)
    a.emit(lsls_imm, 0, 0, 28)
    a.emit(lsrs_imm, 0, 0, 28)                 # channel
    a.emit(movw, 1, CTX_PTR & 0xFFFF)
    a.emit(movt, 1, CTX_PTR >> 16)
    a.emit(ldr_imm, 1, 1, 0)
    a.emit(cmp_imm, 1, 0)
    a.emit(b_cond, "cc_done", "eq")
    for off in (9, 10):
        a.emit(ldrb_imm, 2, 1, off)            # Synth 1 / Synth 2 CC-rx channel
        a.emit(cmp_reg, 0, 2)
        a.emit(b_cond, "cc_go", "eq")
    a.emit(ldrb_imm, 2, 1, 11)                 # Drums CC-rx channel
    a.emit(cmp_reg, 0, 2)
    a.emit(b_cond, "cc_done", "ne")
    a.label("cc_go")
    a.emit(mov_reg, 0, 4)
    a.emit(bl, "c_inject")
    a.label("cc_done")
    a.emit(add_sp_imm, 8)
    a.emit(pop_list, [4], pc=True)

    # ---- recorder gates: skip recording while the internal bit is set
    for addr in GATES:
        name = f"c_gate_{addr:x}"
        a.label(name)
        a.emit(push_list, [0, 1])
        a.emit(movw, 0, CTX_PTR & 0xFFFF)
        a.emit(movt, 0, CTX_PTR >> 16)
        a.emit(ldr_imm, 0, 0, 0)
        a.emit(cmp_imm, 0, 0)
        a.emit(b_cond, f"{name}_rec", "eq")
        a.emit(ldrb_imm, 0, 0, 0x14)
        a.emit(lsls_imm, 0, 0, 26)             # bit5 -> N
        a.emit(b_cond, f"{name}_rec", "pl")
        a.emit(pop_list, [0, 1])
        a.emit(movs_imm, 0, 1)                 # (gate 3 returns 1 in stock; harmless for void gates)
        a.emit(bx_lr)
        a.label(f"{name}_rec")
        a.emit(pop_list, [0, 1])
        a.emit(raw, stock[addr - BASE:addr - BASE + 4])   # relocated stock prologue (push + mov)
        a.emit(b_w, addr + 4)
    return a.assemble()


def build(stock: bytes, listing: Path):
    img4, report = s4.build(stock, listing)
    img = bytearray(img4)
    img[sc.MARK_OFF:sc.MARK_OFF + 4] = MARKER
    ext_base = (len(img4) + BASE + 3) & ~3
    # first assemble to learn size; base must be fixed
    code, labels = ext_code(ext_base, stock)
    # verify stock bytes at patch sites
    def text(addr, n):
        return "|".join(sc.disasm(stock[addr - BASE:addr - BASE + n], addr))
    for addr, want in GATES.items():
        got = text(addr, 4)
        if got != want:
            raise SystemExit(f"gate {addr:#x}: '{got}' != '{want}'")
    if text(CC_HELPER, 4) != "push {r7, lr}|orrs r0, r1":
        raise SystemExit("cc helper mismatch: " + text(CC_HELPER, 4))
    for vt, fn in ((VT_NOTE_ON, NOTE_ON), (VT_NOTE_OFF, NOTE_OFF)):
        if struct.unpack_from("<I", stock, vt - BASE)[0] != fn | 1:
            raise SystemExit(f"vtable {vt:#x} mismatch")
    targets = s4.branch_targets(listing)
    for addr in list(GATES) + [CC_HELPER]:
        for x in range(addr + 1, addr + 4):
            if x in targets:
                raise SystemExit(f"branch into patched bytes at {x:#x}")
    # apply
    for addr in GATES:
        img[addr - BASE:addr - BASE + 4] = b_w(addr, labels[f"c_gate_{addr:x}"])
    img[CC_HELPER - BASE:CC_HELPER - BASE + 4] = b_w(CC_HELPER, labels["c_cc"])
    struct.pack_into("<I", img, VT_NOTE_ON - BASE, labels["c_non"] | 1)
    struct.pack_into("<I", img, VT_NOTE_OFF - BASE, labels["c_noff"] | 1)
    img += b"\xFF" * (ext_base - BASE - len(img)) + code
    while len(img) % 4:
        img += b"\xFF"
    assert len(img) <= 0x70000
    report["D"]["marker"] = MARKER.decode()
    report["sc05"] = dict(start=hex(ext_base), size=len(code), labels={k: hex(v) for k, v in labels.items()},
                          listing=sc.disasm(code, ext_base),
                          patches={hex(a): sc.disasm(bytes(img[a - BASE:a - BASE + 4]), a)
                                   for a in list(GATES) + [CC_HELPER]},
                          vtable={hex(VT_NOTE_ON): hex(labels["c_non"] | 1), hex(VT_NOTE_OFF): hex(labels["c_noff"] | 1)})
    return bytes(img), report


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("stock_bin", type=Path)
    ap.add_argument("--listing", type=Path, default=Path(__file__).resolve().parents[1] / "re/app.asm")
    ap.add_argument("-o", "--outdir", type=Path, default=Path("build/sc05"))
    args = ap.parse_args()
    stock = args.stock_bin.read_bytes()
    img, report = build(stock, args.listing)
    syx = ct_fw.encode(img)
    info = ct_fw.decode(syx)
    assert info["image"] == img
    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / "circuittracks-4486-SC05.bin").write_bytes(img)
    (args.outdir / "circuittracks-4486-SC05.syx").write_bytes(syx)
    manifest = dict(base="circuittracks-firmware-4486 (1.2.1)", marker=MARKER.decode(), image_size=hex(len(img)),
                    image_sha256=ct_fw.sha256(img), syx_sha256=ct_fw.sha256(syx), crc32=hex(info["crc"]), report=report)
    (args.outdir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    r = report["sc05"]
    print("patches", r["patches"]); print("vtable", r["vtable"])
    print("ext", r["start"], r["size"], "bytes")
    for l in r["listing"]:
        print("   ", l)
    print("image size", hex(len(img)), "syx sha", manifest["syx_sha256"], "crc", manifest["crc32"])
