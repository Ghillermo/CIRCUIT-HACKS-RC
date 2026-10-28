"""Circuit Tracks 4486 - SC48.3 = SC48.2 + the fix of RC2.11: vcf21.use_edscratch (the user, on the device: «knobs 4 and 5 update fine, but all the other knobs turned leds off and stopped working»): the CC editor's undo copy moved out of the Master FX block's old LED buffer, which mpatch / psave / sesscopy / patchain / stepmod / sckn use for their state; a discard (pad 25 or a view button with a change pending) wrote their bytes into the template's records and killed those knobs; + vcf21.use_saveexit (the user: «after hitting save, the view must go back to default (exit to preset view)»); and mpatch.use_slots128 (a new feature, the beta only: 128 own-synth patch slots, 8 pages; the user: «128»); and the non-sequenceable knob page (vcf21.use_nspage, p4dest / p4ovl use_ns: Shift + pad 4, 8 knobs with assignable destinations, saved with the patches at padding + 130; the user: «rename page4 to sequenceable knobs, add another (saved) page with non-sequenceble knobs, with the same assign logic»); and the arpeggiator's modifiers (arp.use_ramst / use_mods: octave spread and position, groove, reset; Shift + pads 1-16 of Pattern Settings with the arpeggiator on); and the new Nudge (playmode.use_nudge2: pad 26 = the first-to-last range one step back, Shift + pad 26 forward); and the latch without the Shift colours (arpx.use_nolatchled); and Clear + a note track's button lets go of its latched notes (latchclr); and double presses that match the Shift shortcuts (cscale.use_dbl: Scales twice = the editor; dblpress: Velocity twice = fixed velocity, Shift + Synth / MIDI = pressing them twice); and the knob pages of MIDI 1 / 2 held 1/2 s or more shown only while held (pghold)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import vcf21  # noqa: E402
vcf21.use_edscratch()
vcf21.use_saveexit()
import mpatch  # noqa: E402
mpatch.use_slots128()
import build_sc48_2 as B  # noqa: E402
import modmx  # noqa: E402
import p4dest  # noqa: E402
import p4ovl  # noqa: E402
import psave  # noqa: E402
import xpatch  # noqa: E402
vcf21.use_nspage(modmx.MXR + 0x1B60)                # the non-sequenceable page (Shift + pad 4): its rows at 0x20046B60 (20 B)
p4dest.use_ns(); p4ovl.use_ns()
psave.XLEN = xpatch.XLEN = 142                      # the exchange / the copy between packs carry its destinations (padding + 130..141)
import arp  # noqa: E402
arp.use_ramst(modmx.MXR + 0x1C00)                   # the arpeggiator's running states in RAM (584 B): the tail's + 320.. for the modifiers
arp.use_mods(modmx.MXR + 0x1E50)                    # the arpeggiator's modifiers (Shift + pads 1-16 of Pattern Settings, the arpeggiator on)
import playmode  # noqa: E402
playmode.use_nudge2()                               # Nudge: the range one step back (Shift: forward), notes and drums
import arpx  # noqa: E402
arpx.use_nolatchled()                               # Shift: the keys keep their colours (no yellow / green for the latch)
import cscale  # noqa: E402
cscale.use_dbl()                                    # Scales pressed in the Scales view = Shift + Scales (the editor)
import linein3  # noqa: E402

NAME = "SC48.3"


def extra(img, report):
    import hole
    import latchclr
    import dblpress
    import pghold
    B.extra(img, report)
    hole.add(img, report, "latchclr", latchclr)          # Clear + a note track's button also lets go of its latched notes
    hole.add(img, report, "dblpress", dblpress)          # Velocity twice = fixed velocity; Shift + Synth / MIDI = pressing them twice
    hole.add(img, report, "pghold", pghold)              # a knob page pad of MIDI 1 / 2 held 1/2 s or more: that page only until it is let go
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
