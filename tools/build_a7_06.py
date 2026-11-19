"""Circuit Tracks 4486 - Alpha 7.06 (marker "A7.06") = Alpha 7.05 + tools/xlwin.py (the bug hunt's XL-9; the user, 2026-11-18: «Do xlanes»): the
extra lanes' LED-task transfers (fill, write back, save, load, reload) use their own DSP window (Y:$3B80), so a Components write, a sample swap
or a WAV save on the main loop can no longer read or write the same window between the copy and the read.  + tools/dbtoggle.py (the user:
«Pages (shift+tracks 1-4) exit wrong …» -> «Toggle: exit»): Shift + a track with its own page open = back to its Note view."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import poly  # noqa: E402

if __name__ == "__main__":
    poly.use_quarter()
    import dspz
    dspz.use_move("jumprnd", 1)                            # (as Alpha 7.05)
    import fixes704
    import xlwin
    import dbtoggle
    fixes704.alpha()
    import build_a7_03 as A3
    src = Path(A3.__file__).read_text(encoding="utf-8").replace('NAME = "A7.03"', 'NAME = "A7.06"')
    ic = '            dspz.add(img, report, "icache", icache)'
    src = src.replace(ic, ic + "\n            fixes704.extra_alpha(img, report)\n            dspz.add(img, report, \"xlwin\", xlwin)"
                      "\n            dspz.add(img, report, \"dbtoggle\", dbtoggle)")
    assert "xlwin" in src and '"A7.06"' in src
    import sampler_dsp
    sampler_dsp.use_overdub()
    sys.argv = [A3.__file__] + sys.argv[1:]
    exec(compile(src, A3.__file__, "exec"), {"__name__": "__main__", "__file__": A3.__file__, "fixes704": fixes704, "xlwin": xlwin, "dbtoggle": dbtoggle, "dspz": dspz})
