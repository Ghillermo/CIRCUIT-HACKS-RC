"""SC403D ARM test (live RAM dump; the LED task from its caller): the marks in the settings of the 64 patterns (tools/patdiag.py).

    python tools/emu_sc403d.py SC403D.bin SC403D_manifest.json
  * the settings addresses = those of the stock getter 0x0803C6D6 (first / last step) for the 8 tracks x 8 patterns; bytes 4..39 zero in the dump;
  * the first save of a project: the stock's save still runs with its r0; bytes 4..39 of the 64 settings blocks = the marks, bytes 0..3 and the rest
    of the record (but the tail marks of SC402D) unchanged; the Octave-down LED green;
  * a second save does not write them again (a pattern zeroed stays zeroed: red); none left: as the stock.
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc39_6 as T6  # noqa: E402
from emu_sc35 import MGR, PK  # noqa: E402
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R4
from emu_sc05 import STOP  # noqa: E402
import taildiag as TD  # noqa: E402
import patdiag as PD  # noqa: E402

B = 0x08010000
SIZE = 0x2740C


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["patdiag"]["labels"].items()}
    LT = {k: int(v, 16) for k, v in man["report"]["taildiag"]["labels"].items()}
    from thumb import bl
    check(bytes(img[TD.SAVE_CALL - B:TD.SAVE_CALL - B + 4]) == bl(TD.SAVE_CALL, L["c_pdsave"]) and all(bytes(img[c - B:c - B + 4]) == bl(c, L["c_pdledtask"]) for c in PK.LED_CALLS),
          "the hooks: the bl to the save, the two LED task calls")
    e = T6.E6(img, man); e.setup(man)
    def led():
        e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR)
        e.call(0x08033B3E, maxins=20_000_000)
        return struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138)))[PD.LED_OCT]
    rec = e.r32(TD.SESSION_OBJ + 0x14); rd = lambda: bytes(e.uc.mem_read(rec, SIZE))
    r0 = rd(); idle = led()
    # the stock getter of first / last step: (object with the record pointer, track, pattern) -> the halfword at settings + 0
    e.uc.mem_write(0x2006F100, struct.pack("<I", rec)); same = True
    for i in range(PD.N_PAT):
        o = PD.settings_offset(i); e.uc.mem_write(rec + o, struct.pack("<H", 0x4000 + i))
        e.call(0x0803C6D6, 0x2006F100, i // 8, i % 8); same &= (e.uc.reg_read(UC_ARM_REG_R0) & 0xFFFF) == 0x4000 + i
        e.uc.mem_write(rec + o, r0[o:o + 2])
    S = [PD.settings_offset(i) for i in range(PD.N_PAT)]
    check(same and all(not any(r0[o + 4:o + 40]) for o in S), f"the 64 settings blocks = where the stock getter 0x0803C6D6 reads; bytes 4..39 zero in the dump; the Octave-down LED as the stock's ({idle:#x})")
    want = lambda i: bytes([PD.ID | i, PD.TAG]) + bytes(range(6, 40))
    e.saves.clear(); e.call(L["c_pdsave"], 0x1234, maxins=3_000_000); r1 = rd()
    clean = bytearray(r1)
    for o in S: clean[o + 4:o + 40] = bytes(36)
    check(e.saves == [0x1234] and all(r1[o + 4:o + 40] == want(i) for i, o in enumerate(S)) and bytes(clean[:TD.TAIL]) == r0[:TD.TAIL] and r1[TD.TAIL:TD.TAIL + 5] == b"TAIL" and led() == PD.COL_OK,
          "the first save: the stock's save runs; the marks in bytes 4..39 of the 64 settings blocks, nothing else changed but the tail marks; the LED green")
    e.uc.mem_write(rec + S[5] + 4, bytes(36)); e.uc.mem_write(rec + S[40] + 4, want(33))
    e.call(L["c_pdsave"], 0x55, maxins=3_000_000); r2 = rd()
    check(not any(r2[S[5] + 4:S[5] + 40]) and r2[S[40] + 4:S[40] + 40] == want(33) and r2[TD.TAIL + 4] == 2 and led() == PD.COL_BAD,
          "a second save does not write them again (a zeroed pattern and a copied one stay as they are); the LED red")
    for o in S: e.uc.mem_write(rec + o + 4, bytes(36))
    check(led() == idle, "no marks: the LED as the stock's")
    import tempfile, subprocess
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "00_SESSION.ncs").write_bytes(r2)
        out = subprocess.run([sys.executable, str(Path(__file__).with_name("patchtool.py")), "patdiag", td], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    check("62 de 64" in out and "Synth 1 patr" in out and "(borrado)" in out and "Drum 1 patr" in out and "(copiado)" in out, "patchtool.py patdiag on that record: 62 of 64, the zeroed and the copied pattern named")
    print("SC403D ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
