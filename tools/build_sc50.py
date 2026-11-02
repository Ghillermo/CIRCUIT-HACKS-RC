"""Circuit Tracks 4486 - SC50 = SC49.9 + mutate39.use_mut2 (the user, 2026-11-01: «Rediseña el modo Random mutate»; on the drums too: stepmod, arp, drumpat
follow it) + mutfac (Octave in that view = a factor on every chance) + autorel.use_sweep (a yellow step held + another = the automation interpolated between
them) + playmode.use_nudge3 (the same fix as RC4.04) + jumpseq (the user: «Incluye un nuevo modo de secuenciador en midi 1/2»: MIDI 1 / 2 pointing at another track,
their notes make its pattern jump).  «SC49.10» would be cut to «SC49.1»."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import mutate39  # noqa: E402
mutate39.use_mut2()
import autorel  # noqa: E402
autorel.use_sweep()
import playmode  # noqa: E402
playmode.use_nudge3()
import stepmod  # noqa: E402
stepmod.use_rectrack()
import janko  # noqa: E402
janko.use_v3()
janko.use_jump()
import build_sc49_9 as B  # noqa: E402
import mutfac  # noqa: E402
import jumpseq  # noqa: E402
import centab  # noqa: E402
import hole  # noqa: E402
import linein3  # noqa: E402

NAME = "SC50"


def extra(img, report):
    B.extra(img, report)
    import build_sc41_5
    centab.shrink(img, report)
    centab.add(img, report, "mutfac", mutfac)
    if jumpseq.V2:
        import jumpx
        centab.add(img, report, "jumpx", jumpx)
    build_sc41_5.add(img, report, "jumpseq", jumpseq)
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
