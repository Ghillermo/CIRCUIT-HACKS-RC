"""SC17D / SC173D diagnostic LEDs: python tools/emu_sc17d.py IMG.bin manifest.json"""
import json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc08 import MGR  # noqa: E402
import emu_sc17 as T  # noqa: E402
import emu_sc15 as T15  # noqa: E402
import build_sc17 as B  # noqa: E402

def main(img, man):
    m14 = man["marker"] == "SC173D"
    if m14: B.use_mixer14()
    else: B.ENTRY = "shift"
    L = {k: int(v, 16) for k, v in man["report"]["sc17"]["labels"].items()}
    e = T.E17(img, L); e.state = int(man["report"]["sc17"]["state"], 16)
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    V = T15.VIEWS[0]
    def diag():
        e.set_p0(e.r32(MGR + 0xC), 1)
        e.call(e.r32(e.r32(V) + 0x1C), V, maxins=900000); p = e.uc.reg_read(T.UC_ARM_REG_R0)
        e.set_p0(e.r32(MGR + 0xC), 0)
        l = struct.unpack("<32H", bytes(e.uc.mem_read(p, 64)))
        assert all(x in (B.DIAG_ON, B.DIAG_DIM) for x in l[8:24]), l
        free = sum(1 << (7 - i) for i in range(8) if l[8 + i] == B.DIAG_ON)
        bits = [int(l[16 + i] == B.DIAG_ON) for i in range(8)]
        return free, bits
    free_exp = (B.HEAP_TOP - e.r32(0x20002B48)) // 16
    f, b = diag()
    check(f == free_exp and b == [1, 0, 0, 0, 0, 0, 0, 1], f"power-up: free/16 = {f} (exp {free_exp}), block ok + limit ours {b}")
    mb = 14 if m14 else 13
    e.btn(mb); f, b = diag(); check(b == [1, 0, 0, 1, 0, 0, 0, 1], f"Mixer: pad 20 {b}")
    if m14: e.btn(14)
    else: e.btn(13, shift=True)
    f, b = diag(); check(b == [1, 1, 1, 1, 0, 0, 0, 1], f"Master FX entry: pads 18, 19 {b}")
    e.vcall(0, 0, 100); e.vcall(1, 0); e.leds()
    f, b = diag(); check(b == [1, 1, 1, 1, 1, 1, 1, 1], f"Master FX pad + LEDs: pads 21-23 {b}")
    print("SC17D RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails

if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
