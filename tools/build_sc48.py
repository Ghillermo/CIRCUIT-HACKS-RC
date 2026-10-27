"""Circuit Tracks 4486 - SC48 = SC47.9 + fmeng.use_starters() + velcurve («SC47.10» would be cut to «SC47.1»).
  * fmeng.use_starters (the user, 2026-10-27: «los parches de FM de la fila superior suenan todos muy parecidos … añade sonidos más de tipo
    "instrumento" como starters (piano, pluck, cuerdas, vientos)» · «añade los parches nuevos en otra página (pad 8) y deja en 7 algos por
    defecto»): with FM on, pad 8 held = 16 instrument starters on pads 9-24 (every FM parameter); pad 7 held = the algorithms as before.
  * velcurve (the user, 2026-10-27: «añade un atajo en advanced setup en K1 para cambiar la curva de respuesta de los pads (con centro por
    defecto) al moverlo se muestra número y se ilumina velocity»): Advanced Setup K1 = the pads' velocity curve -8 .. +8, saved in the settings.
  * midipre (the user, 2026-10-27: «doble pulsación abre la misma vista que preset … su pad 27 desactivado se ve gris»): MIDI 1 / 2 pressed
    twice = their Preset view; pad 27 dim white there with the engine off.
  * smnote.use_v2 (the user, on SC47.9: the auto-added note only showed in the Note view at the next Play, in the plain note colour): the
    note told to the stock at once; note + flip steps peach in the Note view.
  * notearp (the user: «queremos note (midi al arpeggiator) en setup normal»): the external keyboard through the arpeggiator on the
    normal Setup's Note button (Advanced Setup's pad 22 off).
  * build_sc17.use_fsqdef (the user: «y fx step seq, cuando no hay efectos asignados al bottom row, usa los efectos por defecto»): an empty
    bottom-row slot plays the top pad of its column in the MIDI tracks' FX step sequencer.
  * notecyc (the user: «cuando el step sequencer está activo, note togglea entre notas, notas expandidas y step seq»).
  * poly.use_v7 (the user: the FM crackle with 4+ notes; «1.B»): in poly a voice's level x 1 / sqrt(the voices sounding).
  * cue.use_preview + cueprev (the user: «only when a cue listen is active, synth patch selection goes to the Cue Channel only.  Sample patch
    with shift (silent selection) now goes to the Cue»): in the cue mode the Preset views' previews go to the cue only.
See tools/fmeng.py, tools/velcurve.py, tools/midipre.py, tools/smnote.py and tools/notearp.py."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc47_9 as B  # noqa: E402
import fmeng  # noqa: E402
import velcurve  # noqa: E402
import midipre  # noqa: E402
import smnote  # noqa: E402
import notearp  # noqa: E402
import build_sc17  # noqa: E402
import notecyc  # noqa: E402
import poly  # noqa: E402
import cue  # noqa: E402
import cueprev  # noqa: E402
import hole  # noqa: E402
import linein3  # noqa: E402
fmeng.use_starters()
smnote.use_v2()
build_sc17.use_fsqdef()
poly.use_v7()
cue.use_preview()

NAME = "SC48"


def extra(img, report):
    B.extra(img, report)
    hole.add(img, report, "velcurve", velcurve)
    hole.add(img, report, "midipre", midipre)
    hole.add(img, report, "notearp", notearp)
    hole.add(img, report, "notecyc", notecyc)
    hole.add(img, report, "cueprev", cueprev)
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
