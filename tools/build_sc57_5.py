"""Circuit Tracks 4486 - SC57.5 = SC57.4 + tools/patrev.py + xlanes.use_reload() (the user, 2026-11-13: «On per-track views ... clear+mutate
restores current pattern to the one saved in the card»; «Ask first», «All track views»): Clear + Duplicate twice in a track view = the pattern edited
there read again from the card (Duplicate blinks white while it asks; Save red when refused); MIDI 1 / 2's extra lanes' block too.

SC57.4 = SC57.3 + tools/scrules.py + patchain.use_groups() (chains of pattern groups, per track and per scene)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc57_2 as S2  # noqa: E402
import build_sc57_1 as S  # noqa: E402
import linein3  # noqa: E402
import morphz  # noqa: E402
import tabpack  # noqa: E402

NAME = "SC57.5"
B = S.B


def extra(img, report):
    import dspz
    import xlanes
    S2.extra(img, report)
    dspz.add(img, report, "xlanes", xlanes)                                         # the outermost head of the save / load / LED task
    import scrules
    dspz.add(img, report, "scrules", scrules)                                       # chain rules per scene: the outermost heads now
    scrules.IO.install(img, report)                                                 # ... and its card work in the LED task, at the end
    import patrev
    patrev.install_end(img, report)                                                 # Clear + Duplicate in a track view: the outermost heads (image end)


if __name__ == "__main__":
    tabpack.use()
    import xlanes
    xlanes.use_reload()                                                             # (patrev: one block of the extra lanes read again)
    import patchain
    patchain.use_groups()                                                           # chains of pattern groups (scrules keeps them)
    import vcf21
    vcf21.use_trimpad()                                                             # (flash: the pad handlers nothing reaches)
    # SC57.5: unreached code not emitted (tools/fullwalk.py on Beta 5.59), room for patrev at the end of the image
    vcf21.use_trimsd()                                                              # (the step-drummer's old fx / base, sdpv's since V2 / V3)
    patchain.use_trimcc()                                                           # (c_pcchained's old body)
    import packio, build_sc17, persist19, stepgate, arp, retrig, sdpv
    packio.use_trim2()                                                              # (the tails CROSS / PKLED2 branch around)
    build_sc17.use_trimsp2()                                                        # (the old song pointer press, the Clear-pad latch test)
    persist19.use_trimkl()                                                          # (c_mhleds19's knob loop before REMAP)
    stepgate.use_trim()                                                             # (pad 31's long press, dead since V3)
    arp.use_trimzr()                                                                # (c_arzero's tail-state clear)
    retrig.use_trimoff()                                                            # (c_rtoff: poly's b.w)
    sdpv.use_trimbs()                                                               # (c_pvbase2's macro read)
    import patmut
    patmut.use_v2()
    S.S.S.S.S.S.S.S.S.S.S.S.room()
    S.S.S.S.S.S.S.S.S.S.S.cpu()
    morphz.use_four()
    morphz.use_slow()
    morphz.use_rrfix()
    morphz.use_newstop()
    morphz.use_fastatk()
    import fmmap
    fmmap.use_lrram()
    patmut.use_lrram()
    import knobhold
    knobhold.use_freeze()
    import fm8ui
    import build_sc55_7
    fm8ui.use_noinst()
    build_sc55_7.FM8DEST = False
    import p4dest
    p4dest.use_dup()
    import blackbox
    blackbox.use_v2()
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
