"""SC41.5 ARM tests: the PGM listen / output channels (tools/pgmch.py).

    python tools/emu_pgmch.py NEW.bin NEW_manifest.json PREVIOUS.bin PREVIOUS_manifest.json
  * the objects: [0x200069E4] = the receiver, [[[0x200069E4]] + 0x1C] = the transmitter (its project entries on channel 16), [L + 0x54] = the
    settings record's store;
  * the Setup view through the controller (mode 8): pad 29 shows the listen channel on pads 1-16 (16 by default, white; the rest dim), again = the
    stock's PGM Rx on / off; a channel pad sets it (byte 1 of parameter 3, index XOR 15; byte 0 untouched); pad 30 the same for the output channel;
    a track button or another pad = the stock's pads again; not in the Advanced page; out of the Setup view the state goes;
  * the settings' «changed?» (0x0802D300) sees the two bytes (the previous build does not);
  * receive (the dispatcher 0x08051720, PGM Rx on): a program change on the listen channel goes to the project and is sent again on the output
    channel when PGM Tx is on; channel 16 no longer; a track's channel still to its track; the previous build: channel 16 = the project;
  * send (0x0802A018, id 0x20): on the output channel; a track's id on its channel.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R4, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc35 import MGR, PK  # noqa: E402
from emu_sc05 import STOP  # noqa: E402
from emu_sc08 import E8  # noqa: E402
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
import pgmch as PG  # noqa: E402
from thumb import bl as tbl  # noqa: E402

B = 0x08010000
MSG = 0x2006E100
PC_TARGET, PC_AFTER = 0x080518EE, 0x080518F0                  # the dispatcher's blx to the program change's target (r1 = target, r2 = program)
SAVE_FN, FILE_WRITE = 0x0802D2AC, 0x0803C920                  # the settings' save (store -> record, then the file: skipped here)


def run(img, new):
    e = E8(img)
    o = {}
    def r0(fn, *a, maxins=8_000_000): e.call(fn, *a, maxins=maxins); return e.uc.reg_read(UC_ARM_REG_R0)
    A = e.r32(PG.CTX); L = e.r32(A); X = e.r32(L + 0x1C); ST = e.r32(L + 0x54)
    tbl_tx = e.r32(X + 0xC)
    o["objs"] = (hex(A), hex(X), ST == e.r32(PG.SETOBJ + 0x9C), bytes(e.uc.mem_read(tbl_tx + 5, 5)).hex(), bytes(e.uc.mem_read(A + 9, 5)).hex())
    p3 = lambda: bytes(e.uc.mem_read(r0(PG.PARAM_GET, ST, 3), 4))
    p2 = lambda: struct.unpack("<I", bytes(e.uc.mem_read(r0(PG.PARAM_GET, ST, 2), 4)))[0]
    def frame():
        e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR); e.call(0x08033B3E, maxins=40_000_000)
        return list(struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138))))
    pad = lambda q: (e.call(PRESS, MGR, q, 100, maxins=8_000_000), e.call(RELEASE, MGR, q, maxins=8_000_000))
    btn = lambda i: (e.call(0x08033320, MGR, i, maxins=8_000_000), e.call(0x0803381A, MGR, i, maxins=8_000_000))
    st = lambda: e.r8(PG.SETUP_OBJ + PG.ST_OFF)
    o["p3_0"] = p3()
    writes = []
    def fw(uc, a, s_, d): writes.append(a); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, fw, begin=FILE_WRITE, end=FILE_WRITE)
    e.call(SAVE_FN, PG.SETOBJ, maxins=8_000_000)                # (the record as the store: nothing changed)
    o["cmp0"] = r0(0x0802D300, PG.SETOBJ)
    # ---- the Setup view
    ms = e.r32(MGR + PG.MODE_STORE); old_mode = e.store_p0(ms); old_view = e.r32(MGR + 0x6C)
    e.uc.mem_write(PG.SETUP_OBJ + PG.ADV_OFF, b"\0\0")
    e.set_p0(ms, PG.MODE_SETUP); e.w32(MGR + 0x6C, 0)
    f0 = frame()[:16]
    seq = []
    def snap(tag): seq.append((tag, st(), p3().hex(), (p2() >> 8) & 3, frame()[:16]))
    pad(PG.PAD_RX); snap("rx")
    pad(PG.PAD_RX); snap("rx2")
    pad(PG.PAD_RX); snap("rx3")
    if not new:
        pad(PG.PAD_RX)                                          # (the previous build: the stock's on / off back as it was)
    if new:                                                     # (the previous build: the channel pads are the tracks')
        pad(4); snap("ch5")
        pad(PG.PAD_TX); snap("tx")
        pad(9); snap("ch10")
        btn(0); snap("track")
        pad(PG.PAD_TX); pad(0x18); snap("other"); pad(0x18)
        e.uc.mem_write(PG.SETUP_OBJ + PG.ADV_OFF, b"\1"); pad(PG.PAD_RX); o["adv"] = st(); e.uc.mem_write(PG.SETUP_OBJ + PG.ADV_OFF, b"\0")
        pad(PG.PAD_RX); o["s_in"] = st()
    e.set_p0(ms, old_mode); e.w32(MGR + 0x6C, old_view); frame(); o["s_out"] = st()
    o.update(seq=seq, f0=f0)
    if not new:                                                 # (the previous build: the same bytes written by hand)
        a_ = r0(PG.PARAM_WPTR, ST, 3); e.uc.mem_write(a_ + 1, bytes([4 ^ 15, 9 ^ 15])); e.call(PG.PARAM_COMMIT, ST)
    # ---- «changed?», the save
    o["cmp1"] = r0(0x0802D300, PG.SETOBJ)
    e.call(SAVE_FN, PG.SETOBJ, maxins=8_000_000)
    o["cmp2"] = r0(0x0802D300, PG.SETOBJ); o["rec3"] = bytes(e.uc.mem_read(PG.SETOBJ + 0x14, 4)).hex(); o["writes"] = len(writes)
    # ---- receive
    hits = []
    def tgt(uc, a, s_, d):
        hits.append((uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2) & 0xFF)); uc.reg_write(UC_ARM_REG_PC, PC_AFTER | 1)
    e.uc.hook_add(UC_HOOK_CODE, tgt, begin=PC_TARGET, end=PC_TARGET)
    fl_rx = e.r8(A + 0x14); fl_tx = e.r8(X + 0x18)
    s1 = e.r8(A + 9)
    def rx(ch, prog, tx_on=True):
        e.uc.mem_write(A + 0x14, bytes([fl_rx | 0x04])); e.uc.mem_write(X + 0x18, bytes([fl_tx | 0x04 if tx_on else fl_tx & ~0x04]))
        hits.clear(); e.ev.clear(); e.uc.mem_write(MSG, bytes([0xC0 | ch, prog, 0, 0]))
        e.call(0x08051720, A, MSG, maxins=8_000_000)
        return (list(hits), [x[1][:4] for x in e.ev if x[0] == "ext"])
    o["rx"] = dict(listen=rx(4, 7), ch16=rx(15, 3), synth1=rx(s1, 2), notx=rx(4, 8, False))
    # ---- send
    def tx(ident, prog):
        e.uc.mem_write(X + 0x18, bytes([fl_tx | 0x04])); e.ev.clear()
        e.call(PG.PC_SEND, X, PG.PC_PORT, ident, prog, maxins=2_000_000)
        return [x[1][:4] for x in e.ev if x[0] == "ext"]
    o["tx"] = dict(project=tx(0x20, 5), synth1=tx(0, 6))
    o["s1"] = s1; o["s1tx"] = e.r8(tbl_tx + 5)
    del e; gc.collect()
    return o


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["pgmch"]["labels"].items()}
    w = lambda a: struct.unpack_from("<I", img, a - B)[0]
    at = lambda a: bytes(img[a - B:a - B + 4])
    check(at(PG.RX_HOOK) == tbl(PG.RX_HOOK, L["c_pgrx"]) and at(PG.TX_HOOK) == tbl(PG.TX_HOOK, L["c_pgtx"]) and at(PG.CMP_HOOK) == tbl(PG.CMP_HOOK, L["c_pgcmp"])
          and w(PG.SETUP_VT) == L["c_pgpad"] | 1 and w(PG.SETUP_VT + 8) == L["c_pgbtn"] | 1 and all(at(c) == tbl(c, L["c_pgledtask"]) for c in PK.LED_CALLS),
          "the hooks: the receive's test, the send's channel, the settings' compare, slots 0 / 2 of the Setup view, the LED task calls")
    o = run(img, True)
    A, X, same, ttx, trx = o["objs"]
    check(same and ttx[6:10] == "0f0f" and trx[6:10] == "0f0f", f"the objects: receiver {A}, transmitter {X} (its table {ttx}, the receiver's {trx}: the project on channel 16), the store = the record's")
    check(o["p3_0"][1:3] == b"\0\0", f"the RAM dump's parameter 3: {o['p3_0'].hex()} (bytes 1 / 2 at 0 = channel 16)")
    d = {s[0]: s for s in o["seq"]}
    pat = lambda sel: [PG.COL_SEL if i == sel else PG.COL_DIM for i in range(16)]
    b0 = o["p3_0"][0]
    check(d["rx"][1] == PG.ST_RX and d["rx"][4] == pat(15) and d["rx"][3] == ((d["rx"][3]) & 3) and d["rx2"][1] == PG.ST_RX and d["rx2"][3] != d["rx"][3]
          and d["rx3"][3] == d["rx"][3],
          f"pad 29: the listen channel 16 shown (white, the rest dim), the stock's on / off untouched; again: the stock's on / off ({[s[:4] for s in o['seq'][:3]]})")
    check(d["ch5"][2] == bytes([b0, 4 ^ 15, 0, o["p3_0"][3]]).hex() and d["ch5"][4] == pat(4), f"pad 5 then: the listen channel 5 (byte 1 = {4 ^ 15}), byte 0 kept ({d['ch5'][2]})")
    check(d["tx"][1] == PG.ST_TX and d["tx"][4] == pat(15) and d["ch10"][2] == bytes([b0, 4 ^ 15, 9 ^ 15, o["p3_0"][3]]).hex() and d["ch10"][4] == pat(9),
          f"pad 30: the output channel 16 shown; pad 10: channel 10 ({d['ch10'][2]})")
    check(d["track"][1] == 0 and d["track"][4] == o["f0"] and d["other"][1] == 0 and o["adv"] == 0 and o["s_in"] == PG.ST_RX and o["s_out"] == 0,
          f"a track button, another pad: the stock's pads; the Advanced page: nothing; out of the Setup view the state goes "
          f"({d['track'][1]}, {d['track'][4]}, {o['f0']}, {d['other'][1]}, {o['adv']}, {o['s_in']:#x}, {o['s_out']})")
    check(o["cmp0"] == 0 and o["cmp1"] == 1 and o["cmp2"] == 0 and o["rec3"][2:6] == "0b06" and o["writes"] == 2,
          f"the settings' «changed?»: {o['cmp0']} after a save, {o['cmp1']} after a channel; the stock's save takes them into the record ({o['rec3']}), {o['cmp2']} then")
    rx = o["rx"]
    check(rx["listen"] == ([(0x20, 7)], ["c907"]) and rx["ch16"] == ([], []) and rx["synth1"] == ([(0, 2)], []) and rx["notx"] == ([(0x20, 8)], []),
          f"receive: channel 5 = the project, sent again on channel 10; channel 16 nothing; Synth 1's channel to Synth 1; PGM Tx off: not sent ({rx})")
    check(o["tx"]["project"] == ["c905"] and o["tx"]["synth1"] == [f"{0xC0 | o['s1tx']:02x}06"], f"send: the project on channel 10, Synth 1 on its channel ({o['tx']})")
    gc.collect(); p = run(prev, False)
    check(p["cmp0"] == 0 and p["cmp1"] == 0 and p["rx"]["ch16"] == ([(0x20, 3)], []) and p["rx"]["listen"] == ([], []) and p["tx"]["project"] == ["cf05"]
          and p["seq"][0][1] != PG.ST_RX and p["seq"][0][3] != p["seq"][1][3],
          f"the previous build: the bytes not seen by «changed?», channel 16 = the project, sent on 16, pad 29 the stock's "
          f"({p['cmp0']}, {p['cmp1']}, {[s[:4] for s in p['seq']]}, {p['rx']}, {p['tx']})")
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
