"""Circuit Tracks 4486 - A7PROT (marker "A7PROT", a prototype; the user, 2026-11-19) = Alpha 7.07 + tools/mixsolo3.py: the Mixer's pad 16 flips the
held tracks' mutes (its solo as before), pad 15 = the solo group (tapped) and the solo flip (held)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import outline
    outline.use()
    import build_a7_06 as A6
    src = Path(A6.__file__).read_text(encoding="utf-8")
    src = src.replace("""replace('NAME = "A7.03"', 'NAME = "A7.06"')""", """replace('NAME = "A7.03"', 'NAME = "A7PROT"')""")
    k = r'dspz.add(img, report, \"dbtoggle\", dbtoggle)"'
    assert k in src, "dbtoggle line"
    src = src.replace(k, k + "\n" + r'                      "\n            import mixsolo3; dspz.add(img, report, \"mixsolo3\", mixsolo3)"'
                      + "\n" + r'                      "\n            import outline; dspz.add(img, report, \"outline\", outline)"')
    src = src.replace("""assert "xlwin" in src and '"A7.06"' in src""", """assert "xlwin" in src and '"A7PROT"' in src""")
    sys.argv = [A6.__file__] + sys.argv[1:]
    exec(compile(src, A6.__file__, "exec"), {"__name__": "__main__", "__file__": A6.__file__})
