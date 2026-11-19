"""Circuit Tracks 4486 - Alpha 7.08 (marker "A7.08") = Alpha 7.07 + tools/fxstep.py (the user, 2026-11-19: the FX sequencer discarded, a step
sequencer on the Master FX view: an FX pad held + a song pointer step = that FX on that step every cycle; Clear + step = mute / empty).
Alpha 7.07 = Alpha 7.06 + tools/outline.py (the user, 2026-11-18: «Make more flash room»): with
thumb.OUTLINE the assembler folds the common parameter reads (movs r1, #k; bl PARAM_GET; ldrb r0, [r0]) and the getter-and-test calls (bl
c_shift / c_von / ...; cmp r0, #0) of every module into one bl to a shared helper; the helpers are the build's last module."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import outline
    outline.use()
    import vcf21
    vcf21.use_nofsq()                                     # the old FX sequencer's code out (vcf21, sdpv, modesel, build_sc17)
    import build_a7_06 as A6
    src = Path(A6.__file__).read_text(encoding="utf-8")
    src = src.replace("""replace('NAME = "A7.03"', 'NAME = "A7.06"')""", """replace('NAME = "A7.03"', 'NAME = "A7.08"')""")
    k = r'dspz.add(img, report, \"dbtoggle\", dbtoggle)"'
    assert k in src, "dbtoggle line"
    src = src.replace(k, k + "\n" + r'                      "\n            import fxstep; dspz.add(img, report, \"fxstep\", fxstep)"'
                      + "\n" + r'                      "\n            import outline; dspz.add(img, report, \"outline\", outline)"')
    src = src.replace("""assert "xlwin" in src and '"A7.06"' in src""", """assert "xlwin" in src and '"A7.08"' in src""")
    sys.argv = [A6.__file__] + sys.argv[1:]
    exec(compile(src, A6.__file__, "exec"), {"__name__": "__main__", "__file__": A6.__file__})
