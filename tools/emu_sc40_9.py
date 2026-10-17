"""SC40.9 ARM tests (live RAM dump, the real routes).

    python tools/emu_sc40_9.py SC40.9.bin SC40.9_manifest.json SC40.8.bin SC40.8_manifest.json
  * the chain mode of the whole project (patchain.use_v3): a project without anything of ours starts in the normal mode; Shift + Octave up / down
    in the Patterns view = every track on / off the rules, the tail made ours, Octave up green; a view button keeps the mode; a scene saved in
    the mode carries it, one saved out of it does not; a scene that starts (the track advance) puts its mode back, and so does the LED task when
    the current scene changes while stopped (not while playing); the mode off with a track on its B pattern: back to A; Clear + pattern: out of
    the mode the rule and the play order go, in the mode a rule goes alone and a pattern without one is cleared by the stock (order too);
  * the drum tracks (playmode.use_drums): pads 26-28 of their Pattern Settings view lit, the order in byte 7, Nudge = the four step arrays and
    the eight lanes rotated, the rest of the pattern untouched;
  * Master FX per session (fxsess): the save writes the block (mark, sum, 20 knobs, the compressor) into the tail; after a load the LED task puts
    it back (the knobs, «send again», the compressor through the listener); a block with a wrong sum, or none: nothing; a save before the
    project's block was applied leaves it;
  * the Sidechain view: K7 / K8 = the compressor's attack / release, limited, their LEDs; K5 / K6 nothing; compkn's hooks out of the Setup view;
  * the Setup view (the controller's mode 8, [ctrl + 0x68]): Record toggles the byte, its LED yellow / dark; not in the Advanced page; the three
    recorder gates: an internal message is recorded only with the toggle on, an external one always;
  * the engine's address (use_engfix): the step-drummer / FX sequencer read the step of MIDI 1 (the previous build: of Drum 2);
  * the FX sequencer's selector knob: one unit of its position every three events, the rest kept, both ways.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc35 import MGR, PK  # noqa: E402
from emu_sc05 import STOP  # noqa: E402
from emu_sc08 import CONT  # noqa: E402
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
import emu_sc40_5 as T5  # noqa: E402
import emu_sc40_8 as T8  # noqa: E402
import fxsess as FS  # noqa: E402
import mutate39 as MU  # noqa: E402
import patchain as PC  # noqa: E402
import playmode as PM  # noqa: E402
import sckn as SK  # noqa: E402

B = 0x08010000
ENG = PC.ENG


def seq_part(img, man, presses=5):
    """the FX sequencer of MIDI 1: which track's step it reads, the selector knob -> (the step read, the positions after the knob events);
    `presses` = pad 27 from off to the FX sequencer (6 from SC44: the sample state before it)"""
    import emu_sc36_1 as T361
    V = T361.V
    V.use_fxseq3()
    e = T361.E20(img, man)
    for _ in range(30): e.vtick()
    pad = lambda p: (e.padr(p), e.rel(p))
    def r0(fn, *a): e.call(fn, *a); return e.uc.reg_read(UC_ARM_REG_R0)
    e.btn(2); e.track(2); e.btn(8)
    for _ in range(presses): pad(V.PAD_OSC)
    fsq = r0(e.vl["c_fsq"], 0)
    pad(V.PAD_SD)
    for t, s in ((2, 7), (5, 3), (0, 11), (3, 13)):
        e.uc.mem_write(r0(0x0803542C, e.r32(ENG + 0x30 + 4 * t), 1), bytes([s]))
    step = r0(e.vl["c_sdpos"], 0)
    pat = r0(e.vl["c_sdpat"], 0)
    lane = lambda st: e.r8(r0(e.vl["c_sdlna"], pat, st))
    h0 = r0(e.vl["c_sdhalf"], 0)
    e.knob_raw(0, -127); e.knob_raw(0, -127)
    a_ = V.TAIL + V.O_ED + 1; e.uc.mem_write(a_, bytes([e.r8(a_) & 0x0F]))            # (nothing left over from those turns)
    seq = [lane(h0)]
    for d in (1, 1, 1, 1, 1, 1, -1, 1, 1, 9, -30, -30):
        e.knob_raw(0, d); seq.append(lane(h0))
    del e; gc.collect()
    return fsq, step, seq


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    lab = lambda sec, m_=man: {k: int(v, 16) for k, v in m_["report"][sec]["labels"].items()}
    L, LP, LM, L17 = lab("fxsess"), lab("patchain"), lab("playmode"), lab("sc17")
    from thumb import bl as tbl, b_w
    w = lambda a, i=img: struct.unpack_from("<I", i, a - B)[0]
    at = lambda a, n: bytes(img[a - B:a - B + n])
    stub = int(man["report"]["compkn"]["prev"]["knob"], 16)
    check(at(FS.SAVE_CALL, 4) == tbl(FS.SAVE_CALL, L["c_fssave"]) and w(SK.CT_VT + 16) == L["c_fsknob"] | 1 and w(FS.SETUP_VT + 8) == L["c_fssbtn"] | 1
          and all(at(g, 4) == b_w(g, L[f"c_fsgate_{g:x}"]) for g in FS.GATES) and all(at(c, 4) == tbl(c, L["c_fsledtask"]) for c in PK.LED_CALLS)
          and w(FS.SETUP_VT + 16) == stub | 1 and w(FS.SETUP_VT + 16, prev) != stub | 1,
          "the hooks: the save call, slot 4 of the container, slot 2 of the Setup view, the three gates, the LED task calls; the Setup view's knob slot = the stock's stub again")

    # ================================================================ the chain mode, Master FX per session, the views (one instance)
    e = T8.E8(img, man, LP)
    def frame():
        e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR); e.call(0x08033B3E, maxins=40_000_000)
        return list(struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138))))
    press = lambda i: e.call(0x08033320, MGR, i, maxins=8_000_000)
    release = lambda i: e.call(0x0803381A, MGR, i, maxins=8_000_000)
    btn = lambda i: (press(i), release(i))
    pad = lambda q: (e.call(PRESS, MGR, q, 100, maxins=8_000_000), e.call(RELEASE, MGR, q, maxins=8_000_000))
    shift = lambda v: e.set_p0(e.r32(MGR + 0xC), v)
    held = lambda v: e.uc.mem_write(e.ptr(e.r32(e.r32(MGR + 0x20) + 0xC), 0), bytes([v]))
    tail = lambda: bytes(e.uc.mem_read(e.tail, 48))
    scr = lambda o: e.r8(e.scr + o)
    mode = lambda: (scr(PC.S_EDIT), scr(PC.S_LIVE))
    transport = lambda on: e.uc.mem_write(e.ptr(MU.PLAY_STORE, 0), bytes([on]))
    def scene(n): e.put(e.r32(ENG + 0x2C), 0, bytes([n]))
    e.uc.mem_write(e.tail, bytes(1000)); e.uc.mem_write(e.gst + PC.ST_INIT, b"\0"); e.st()
    transport(0); scene(0)
    check(mode() == (0, 0), "a project without anything of ours: the normal mode")
    e.set_p0(e.r32(CONT + 0x188), 0); btn(0); btn(13)
    shift(1); f_y = frame(); btn(20); shift(0); m1 = mode(); t1 = tail(); f1 = frame()
    check(m1 == (1, 0xFF) and t1[:4] == b"CTC1" and t1[PC.P_SUM] == PC.checksum(t1) and t1[PC.P_LIVE] == 0xFF and t1[PC.P_FLAGS:PC.P_FLAGS + 16] == bytes(16)
          and f_y[PC.LED_UP] == PC.COL_SHIFT and f1[PC.LED_UP] == PC.COL_MODE,
          f"Patterns view, Shift (Octave up yellow) + Octave up: the mode on for every track, the tail ours with every scene normal, Octave up green ({m1}, {t1[:8].hex()})")
    btn(14); m2 = mode(); MIXV = e.r32(MGR + 0x6C)
    def scene_pad(q): e.call(0x08050EE8, MIXV + 0xC, q - 16, maxins=8_000_000)   # (the Mixer's scene pads, as emu_sc40_5)
    shift(1); scene_pad(16 + 2); shift(0); fl_on = tail()[PC.P_FLAGS + 2]
    btn(13); shift(1); f_d = frame(); btn(19); shift(0); m3 = mode(); t3 = tail()
    btn(14); shift(1); scene_pad(16 + 5); shift(0); t5 = tail()
    check(m2 == (1, 0xFF) and fl_on == 0xFF and f_d[PC.LED_DOWN] == PC.COL_SHIFT and m3 == (0, 0) and t3[PC.P_LIVE] == 0 and t5[PC.P_FLAGS + 5] == 0 and t5[PC.P_FLAGS + 2] == 0xFF
          and t5[PC.P_SUM] == PC.checksum(t5),
          f"another view keeps the mode; a scene saved in it carries it; Shift (Octave down yellow) + Octave down: off; a scene saved then is normal ({m2}, {m3})")
    for t in range(8): e.chain(t, e.playing(t), e.playing(t))
    e.advance(0, scene_start=1, scene=2); a1 = mode()
    for t in range(1, 8): e.advance(t, scene_start=1, scene=2)
    a2 = mode()
    for t in range(8): e.advance(t, scene_start=1, scene=5)
    a3 = mode()
    check(a1 == (1, 1) and a2 == (1, 0xFF) and a3 == (0, 0), f"a scene that starts (the track advance): its tracks take its mode, the indicator too ({a1}, {a2}, {a3})")
    frame(); scene(2); frame(); s1 = mode()
    transport(1); scene(5); frame(); s2 = mode(); transport(0); frame(); s3 = mode()
    scene(2); frame(); scene(5); frame(); s4 = mode()
    check(s1 == (1, 0xFF) and s2 == (1, 0xFF) and s3 == (1, 0xFF) and s4 == (0, 0),
          f"stopped, another scene chosen: the LED task puts its mode ({s1}); while playing it does not ({s2}, {s3}); stopped again, a normal scene: off ({s4})")
    # the mode off with a track on its B pattern
    btn(13); shift(1); btn(20); shift(0)
    e.rule(0, 0, 1, 1); e.rule(0, 1); e.chain(0, 0, 0); e.set_playing(0, 0); e.clear_state()
    e.advance(0); p1 = e.playing(0)
    shift(1); btn(19); shift(0)
    e.advance(0, look=1); pl = (e.ahead(0), e.playing(0)); e.advance(0); p2 = e.playing(0); e.advance(0); p3 = e.playing(0)
    check((p1, pl, p2, p3) == (1, (0, 1), 0, 0), f"the mode off with a track on its B pattern: it goes back to its A, then the stock chain ({p1}, {pl}, {p2}, {p3})")
    # Clear + pattern
    ra = lambda t, p: e.rec + PC.rule_offset(t, p)
    def setp(t, p, n, b_, order):
        e.uc.mem_write(ra(t, p), bytes([n, b_, 0, order]))
    getp = lambda t, p: tuple(e.uc.mem_read(ra(t, p), 4))
    stock = []
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s_, d: stock.append(a), begin=PC.PV_PAD, end=PC.PV_PAD)
    setp(0, 0, 2, 2, 2); setp(0, 1, 2, 1, 1)
    stock.clear(); held(1); pad(0); held(0); c1 = (getp(0, 0), len(stock))
    shift(1); btn(20); shift(0)
    stock.clear(); held(1); pad(8); held(0); c2 = (getp(0, 1), len(stock))
    stock.clear(); held(1); pad(8); held(0); c3 = (getp(0, 1), len(stock))
    shift(1); btn(19); shift(0)
    check(c1[0] == (0, 0, 0, 0) and c1[1] >= 1 and c2 == ((0, 0, 0, 1), 0) and c3[0] == (0, 0, 0, 0) and c3[1] >= 1,
          f"Clear + pattern: out of the mode the rule and the play order go with the stock's clear; in the mode a rule goes alone, then the stock's clear and the order ({c1}, {c2}, {c3})")

    # ---- Master FX per session; the Sidechain view
    def r0(fn, *a): e.call(fn, *a, maxins=8_000_000); return e.uc.reg_read(UC_ARM_REG_R0)
    comp = lambda: [r0(FS.GETTER, FS.TYPE, i) & 0xFF for i in range(8)]
    psets = []
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s_, d: psets.append((uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R3))), begin=FS.PARAM_SET, end=FS.PARAM_SET)
    saves = []
    def sv(uc, a, s_, d): saves.append(uc.reg_read(UC_ARM_REG_R0)); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, sv, begin=int(man["report"]["fxsess"]["prev"]["save"], 16), end=int(man["report"]["fxsess"]["prev"]["save"], 16))
    fxb = r0(L17["c_gfst"]); blk = e.tail + FS.BLK
    knobs = lambda: bytes(e.uc.mem_read(fxb + FS.S_KNOB, 20))
    block = lambda: bytes(e.uc.mem_read(blk, FS.B_END))
    def knob(k, d): e.call(0x08033848, MGR, k, d & 0xFFFFFFFF, maxins=3_000_000)
    shift(1); btn(15); shift(0)
    cont = e.r32(MGR + 0x2C); in_sc = e.r8(cont + SK.MODE_OFF)
    c0 = comp(); knob(6, 20); knob(7, 9); knob(4, 5); knob(5, -5); cA = comp(); fk = frame()[60:68]
    knob(6, 127); knob(6, 127); knob(7, -127); cB = comp(); knob(6, -127); knob(6, 20); knob(7, 9); cC = comp()
    check(in_sc == SK.MODE_SC and cA[3] == c0[3] + 20 and cA[4] == c0[4] + 9 and cA[:3] + cA[5:] == c0[:3] + c0[5:] and cB[3] == 127 and cB[4] == 0 and cC[3:5] == [20, 9]
          and fk[6] == FS.COL_COMP | (cA[3] + 2) << 8 and fk[7] == FS.COL_COMP | (cA[4] + 2) << 8 and fk[4] == fk[5] == 0,
          f"the Sidechain view: K7 = the compressor's attack, K8 = its release, limited to 0..127, white with their value; K5 / K6 nothing ({c0[3:5]} -> {cA[3:5]} -> {cB[3:5]})")
    KA = bytes((7 * i + 3) & 0x7F for i in range(20)); KB = bytes((5 * i + 60) & 0x7F for i in range(20))
    frame()
    e.uc.mem_write(fxb + FS.S_KNOB, KA); appl = scr(40)
    e.call(L["c_fssave"], PC.SESSION_OBJ, maxins=8_000_000); b1 = block()
    want = bytearray(FS.B_END); want[0:4] = b"MFX1"; want[FS.B_KNOB:FS.B_KNOB + 20] = KA; want[FS.B_COMP:FS.B_COMP + 2] = bytes([20, 9])
    want[FS.B_SUM] = (sum(want[FS.B_KNOB:FS.B_END]) ^ FS.SUM_XOR) & 0xFF
    check(appl == FS.APPL and b1 == bytes(want) and saves == [PC.SESSION_OBJ], f"the save: the block in the tail (the mark, the sum, the 20 knobs, the attack and the release), then the chain ({b1[:8].hex()})")
    def load(): e.uc.mem_write(e.gst + PC.ST_INIT, b"\0")                           # (what c_pcload does at the end of the stock's apply)
    e.uc.mem_write(fxb + FS.S_KNOB, bytes(b | 0x80 if i == 3 else b for i, b in enumerate(KB))); knob(6, 30); knob(7, 30); e.uc.mem_write(fxb + FS.S_DIRTY, b"\0")
    load(); e.call(L["c_fssave"], PC.SESSION_OBJ, maxins=8_000_000); kept = block() == b1
    psets.clear(); frame(); k1 = knobs(); d1 = e.r8(fxb + FS.S_DIRTY); c1_ = comp()[3:5]; p1_ = [x for x in psets if x[0] == FS.TYPE]
    psets.clear(); frame(); p2_ = list(psets)
    check(kept and k1 == bytes(b | 0x80 if i == 3 else b for i, b in enumerate(KA)) and d1 == 1 and c1_ == [20, 9] and sorted(p1_) == [(FS.TYPE, 3, 20), (FS.TYPE, 4, 9)] and p2_ == [],
          f"after a load: a save before the project's block is applied leaves it; the LED task puts the knobs back (bit 7 of the unit's byte kept), marks them for the DSP and sets the compressor, once ({p1_})")
    bad = bytearray(b1); bad[FS.B_SUM] ^= 1; e.uc.mem_write(blk, bytes(bad)); e.uc.mem_write(fxb + FS.S_KNOB, KB); e.uc.mem_write(fxb + FS.S_DIRTY, b"\0")
    load(); psets.clear(); frame(); n1 = (knobs() == KB, e.r8(fxb + FS.S_DIRTY), list(psets))
    e.uc.mem_write(blk, bytes(FS.B_END)); load(); frame(); n2 = knobs() == KB
    check(n1 == (True, 0, []) and n2, "a block with a wrong sum, or no block: the unit keeps what it has")

    # ---- the Setup view: Record
    SETUP = FS.SETUP_OBJ
    ptr68 = e.r32(MGR + FS.SETUP_PTR); raw = bytes(e.uc.mem_read(SETUP + 0x24, 4))
    ms = e.r32(MGR + FS.MODE_STORE); old_mode = e.r8(e.ptr(ms, 0)); old_view = e.r32(MGR + 0x6C)
    e.uc.mem_write(SETUP + FS.ADV_OFF, b"\0")
    f_out = frame()[FS.LED_REC]
    e.set_p0(ms, FS.MODE_SETUP); e.w32(MGR + 0x6C, 0)
    byte = lambda: struct.unpack("<H", bytes(e.uc.mem_read(SETUP + FS.REC_OFF, 2)))[0]
    r = [(byte(), frame()[FS.LED_REC])]
    for _ in range(3): press(16); release(16); r.append((byte(), frame()[FS.LED_REC]))
    press(23); release(23); press(24); release(24); r.append((byte(), frame()[FS.LED_REC]))
    e.uc.mem_write(SETUP + FS.ADV_OFF, b"\1"); press(16); release(16); adv = byte(); e.uc.mem_write(SETUP + FS.ADV_OFF, b"\0")
    check(ptr68 == SETUP and r[0][1] == 0 and r[0][0] != FS.REC_ON and r[1:] == [(FS.REC_ON, FS.COL_REC), (0, 0), (FS.REC_ON, FS.COL_REC), (FS.REC_ON, FS.COL_REC)] and adv == FS.REC_ON,
          f"the Setup view ([ctrl + 0x68], mode 8; the bytes after its Advanced flag: {raw.hex()}): Record toggles, its LED yellow / dark; other buttons and the Advanced page leave it ({r})")
    e.set_p0(ms, old_mode); e.w32(MGR + 0x6C, old_view)
    # the gates
    ctx = e.r32(0x200069E4); fl = e.r8(ctx + 0x14)
    hits = []
    def gh(uc, a, s_, d): hits.append(a); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    for g in FS.GATES: e.uc.hook_add(UC_HOOK_CODE, gh, begin=g + 4, end=g + 4)
    res = {}
    for internal in (0, 1):
        for on in (0, 1):
            e.uc.mem_write(ctx + 0x14, bytes([fl & ~0x20 | (0x20 if internal else 0)])); e.uc.mem_write(SETUP + FS.REC_OFF, struct.pack("<H", FS.REC_ON if on else 0x36EE))
            hits.clear()
            for g in FS.GATES: e.call(g, 0x2003C168, 60, 100, maxins=20000)
            res[(internal, on)] = [h_ - 4 for h_ in hits]
    e.uc.mem_write(ctx + 0x14, bytes([fl])); e.uc.mem_write(SETUP + FS.REC_OFF, b"\0\0")
    G = list(FS.GATES)
    check(res == {(0, 0): G, (0, 1): G, (1, 0): [], (1, 1): G}, f"the recorder gates: an external message is recorded, an internal one only with the toggle on ({ {k: len(v) for k, v in res.items()} })")

    del e; gc.collect()

    # ---- a drum track: the Pattern Settings view
    e = T8.E8(img, man, LP)
    for t in range(8): e.chain(t, e.playing(t), e.playing(t))
    e.set_p0(e.r32(CONT + 0x188), 4); btn(4); btn(12)
    dp = e.playing(4); DS = e.settings(4, dp); base = DS - PM.D_SET_OFF
    e.setpat(4, dp, 0, 15, 0, 0); e.call(0x08034196, MGR, 0x2006E000, maxins=8_000_000); fd = list(struct.unpack("<32H", bytes(e.uc.mem_read(0x2006E000, 64))))
    U, C = PM.COL_UNSEL, PM.COL_SEL
    pad(PM.PAD_DEC); m_d = (e.r8(DS + 7), e.r8(DS + 3)); pad(PM.PAD_DIR + 1); m_r = (e.r8(DS + 7), e.r8(DS + 3)); pad(PM.PAD_DIR)
    def fill():
        arr = b"".join(bytes((40 * a_ + s + 1) & 0xFF for s in range(32)) for a_ in range(4))
        lanes = b"".join(bytes((l * 37 + s * 5 + i) & 0xFF for s in range(32) for i in range(6)) for l in range(8))
        e.uc.mem_write(base, arr); e.uc.mem_write(base + PM.D_AUTO_OFF, lanes); return arr, lanes
    rot = lambda data, size, n, k: b"".join(data[size * ((i + k) % n):size * ((i + k) % n) + size] for i in range(n)) + data[size * n:]
    res = []
    for first, last, n in ((5, 12, 16), (20, 27, 32), (3, 2, 16)):
        e.setpat(4, dp, first, last, 0, 0); arr, lanes = fill(); whole0 = bytes(e.uc.mem_read(base, 0x6A8))
        pad(PM.PAD_NUDGE); whole = bytes(e.uc.mem_read(base, 0x6A8))
        wa = b"".join(rot(arr[32 * a_:32 * a_ + 32], 1, n, first) for a_ in range(4))
        wl = b"".join(rot(lanes[192 * l:192 * l + 192], 6, n, first) for l in range(8))
        res.append((whole[:128] == wa, whole[PM.D_AUTO_OFF:] == wl, (e.r8(DS), e.r8(DS + 1)) == ((last - first) % n, 0), whole[130:PM.D_AUTO_OFF] == whole0[130:PM.D_AUTO_OFF]))
    check(fd[25:28] == [PM.COL_NUDGE, U, U] and m_d == (PM.M_DEC, 0) and m_r == (0, 1) and all(all(x) for x in res),
          f"a drum track: pads 26-28 lit, the order in byte 7 ({m_d}, {m_r}); Nudge: its four step arrays and eight lanes rotated over 16 / 32, first = 1, the rest untouched ({res}, {[hex(x) for x in fd[24:]]}, sub {e.r8(MGR + 0x152)})")
    del e; gc.collect()

    # ================================================================ the FX sequencer: its track, its knob
    fsq, step, seq = seq_part(img, man)
    gc.collect(); pfsq, pstep, pseq = seq_part(prev, prev_man)
    check(fsq == 1 and step == 7 and pstep == 3, f"the step-drummer / FX sequencer of MIDI 1 reads the step of MIDI 1 ({step}); the previous build read Drum 2's ({pstep})")
    check(seq == [0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 5, 0, 0] and pseq[:4] == [0, 1, 2, 3], f"the selector knob: one unit of the position every three events, the rest kept, both ways ({seq}); the previous build: one an event ({pseq[:7]})")
    print("SC40.9 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
