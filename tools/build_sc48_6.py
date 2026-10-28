"""Circuit Tracks 4486 - SC48.6 = SC48.5 + vguard.use_hold() (the user, 2026-10-28, on SC48.5 / S485D: «stock synths sometimes cease to sound
when 5 notes are held», «synth1/2 sometimes stop playing, they come back when i let go of the chord», «save was amber/yellow/orange», only with
poly and 4 notes or more): the stock's own voice steal on the DSP's time (Synth 1 / 2 only: below half a voice of room the DSP kills one of
that synth's voices every 12 blocks) held while two or more own voices sound; a real overload is vguard's (our voices freed)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc48_5 as B  # noqa: E402
import vguard  # noqa: E402
vguard.use_hold()                                   # the stock's Synth 1 / 2 steal held while our voices sound
import linein3  # noqa: E402

NAME = "SC48.6"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
