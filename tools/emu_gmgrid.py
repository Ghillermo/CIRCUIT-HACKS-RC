"""Alpha 7.48 (tools/gmgrid.py): the global macro view's page-2 grid saved with the project and loaded back.
    python tools/emu_gmgrid.py firmware/a7.48"""
import gc, json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_LR, UC_ARM_REG_SP
import emu_sc48_8 as S
import gmview as G, gmgrid as GG
from emu_sc05 import STOP


def main(d):
    img = next(Path(d).glob("*.bin")).read_bytes(); man = json.loads((Path(d) / "manifest.json").read_text()); R = man["report"]
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in R["gmgrid"]["labels"].items()}; P = {k: int(v, 16) for k, v in R["gmgrid"]["prev"].items()}
    G.use_rows(); G.use_page2col()
    e = S.ET(img, man); uc = e.uc
    rec = e.r32(0x2003D71C + 0x14)
    if not rec: print("skip: no session record"); return 0
    for adr in P.values(): uc.hook_add(UC_HOOK_CODE, lambda u, a_, s_, ud: u.emu_stop(), begin=adr, end=adr)
    def run(lab):
        uc.reg_write(UC_ARM_REG_SP, 0x20047C00); uc.reg_write(UC_ARM_REG_LR, STOP | 1); uc.emu_start(L[lab] | 1, STOP, count=2_000_000)
    run("c_ggload")                                                                    # gmview's state set up, the grid from a zero record
    check(e.r32(G.GM) == GG.SIG4 and e.r32(G.GM + G.O_MX) == 0, f"load from a clean project: state signed, grid empty ({e.r32(G.GM + G.O_MX):#x})")
    e.w32(G.GM + G.O_MX, 0x80030912)
    run("c_ggsave")
    b1, b2 = bytes(uc.mem_read(rec + GG.OFF1, 4)), bytes(uc.mem_read(rec + GG.OFF2 - 2, 4))
    check(b1[:3] == bytes([0x12, 0x09, 0x03]) and b2[2] == 0x80 and b1[3] == 0 and b2[:2] == bytes(2) and b2[3] == 0,
          f"save: rows 1-3 in MIDI 1's pattern 8 settings 4..6, row 4 in MIDI 2's settings 6, neighbours untouched ({b1.hex()}, {b2.hex()})")
    e.w32(G.GM + G.O_MX, 0)
    run("c_ggload")
    check(e.r32(G.GM + G.O_MX) == 0x80030912, f"load: the grid back ({e.r32(G.GM + G.O_MX):#x})")
    e.w32(G.GM, 0); e.w32(G.GM + G.O_MX, 0x01010101); run("c_ggsave")
    check(bytes(uc.mem_read(rec + GG.OFF1, 3)) == bytes([0x12, 0x09, 0x03]), "save with gmview's state unsigned: nothing written")
    uc.mem_write(rec + GG.OFF1, bytes(3)); uc.mem_write(rec + GG.OFF2, bytes(1)); run("c_ggload")
    check(e.r32(G.GM + G.O_MX) == 0 and e.r32(G.GM) == GG.SIG4, "load of a project without a grid: empty")
    del e; gc.collect()
    print(f"{man.get('marker')} GMGRID RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1]) else 0)
