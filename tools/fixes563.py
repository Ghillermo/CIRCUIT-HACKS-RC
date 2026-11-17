"""The options of SC57.8 / Beta 5.63 (and RC4.14 / RC4.14S): the fixes of the 2026-11-14 bug hunt, in one place so the beta, the SC build and the
tests turn on the same set.  Each is an option of its module: the builds before stay byte-identical.

Room (the flash was full: Beta 5.62 had 28 B free in dspz's first gap, 19 in the second, 51 in the hole and 24 at the image's end; a first plan
reused two «dead» stock functions, which are not dead: the storage task reaches 0x08022E08 with a pc-relative addw, and 0x0804D2CA computes a
thunk into 0x0804D438 the same way; fullwalk.py did not follow those: never reuse stock code): tabpack.use_fm2() packs three more FM tables
(exp, inc, bexp: second differences, rebuilt in the ITCM at power-up like the rest): 1 152 B freed in the first gap, where every module of the
fixes lives (fm8's data is in that gap too), while their 620 B of records go to tabpack's blob at the image's end, so patrev (736 B) moves from
the end into the gap (patrev.use_gap).  The jump sequencer's companion goes into the gap as well; the arpeggio's tempo stub into the hole.

  beta()  the options of the beta / SC build (called before the chain is built: the main sequence's options and the wrappers must be set first)
  rc()    the options of RC4.14 / RC4.14S (the fixes also in the RC: ARP-1, CK-1)
  extra_beta(img, report) / extra_rc(img, report)  after the chain's extra: the modules the fixes add"""


def beta():
    import tabpack
    import xlanes
    import scrules
    import vcf21
    import recinst
    import arp
    import capkeep
    import jumprnd
    import jsaflip
    import jumpseq
    import patrev
    tabpack.use_fm2()                                         # room: the FM's exp / inc / bexp tables packed (+1 152 B in dspz's first gap, 620 B of records at the end)
    patrev.use_gap()                                          # room: patrev (736 B) from the image's end into the first gap (the end is where the records go)
    xlanes.use_memfix()                                       # XL-2 / XL-3: the unaligned memsets (the crash recording VA knobs); a stale block untouched
    xlanes.use_svfix()                                        # XL-1 / SCR-2 / XC-1: the lanes' tail to the project just saved (pack / slot were swapped); none in pack 0
    xlanes.use_fillfix()                                      # XL-5: the ITCM block's «cached» only once filled; failed DSP copies retried
    xlanes.use_editcache()                                    # XL-4: stopped, the edited pattern's block is the cached one (edits were dropped)
    xlanes.use_atomic()                                       # XL-6: the header written last (a failed save leaves no half tail); codes > 34 not played
    scrules.use_svfix()                                       # SCR-1 / XC-1: the chains' section to the project just saved; none in pack 0
    scrules.use_sclear()                                      # SCR-3: Clear + a scene pad clears the scene's chains too
    vcf21.use_freeslot()                                      # JR-1: a freed sequenceable slot (code 0) plays and sends nothing
    recinst.use_code0()                                       # JR-2: the Record + step snapshot never writes into a freed slot
    arp.use_tmext()                                           # ARP-1: the armed arpeggio notes timed with the external clock's tempo when slaved
    capkeep.use_resend()                                      # CK-1: a kept capture's STATE sent again (a restart that kept the RAM)
    jumprnd.use_v2()                                          # JR-7 / XC-3: one key and count per pointing track; one jump per pointing step; counts reset at Play
    jsaflip.use_sel()                                         # JR-6: a stopped press on a step without a flip sets the drum's selected sample
    jumpseq.use_stopclr()                                     # JR-4: a jump left pending at Stop does not run on the next Play
    jumpseq.use_audrel()                                      # JR-5: a pad pressed stopped gets its release once Play has started (the hung note)


def rc():
    import arp
    import capkeep
    arp.use_tmext()                                           # ARP-1
    capkeep.use_resend()                                      # CK-1


def vtguard():
    """SC57.9 / Beta 5.64 / RC4.15 (a fix in both; the black box record of 2026-11-15 on Beta 5.63, «pattern chain is broken», stopped, in the
    Patterns view, 1.4 s after the last gesture): the stopped tick's store commit (0x080353C0) of Drum 4's step store 0x2003bd90 called its
    entry 2 (the velocity bar's listener sub-object 0x20043610 = C3 + 8) whose vtable word had been overwritten (0x0805ADA8 -> 0x0805AD60,
    the low byte 0xA8 -> 0x60 = the address of slot 7 of the drum Note view class 0x0805AD44), so it ran rollers.c_rlleds with that sub-object
    as `this`; drumnote.c_nvl took [[this + 4]] (the header of store 0x2003bbf4, 0x1f020520) as the LED buffer and read 0x1f02055e: BusFault.
    In the stock that slot is the LED getter (harmless with any object).  Now both return at once when [this] != 0x0805AD44 (16 B each, no
    stack before the check): rollers.use_vtguard(), drumnote.use_vtguard().  Not called by beta() / rc(): the 5.63 / RC4.14 images stay as
    built; the next build calls it after them.  The writer of that byte is not found (the hunt: docs/NOTAS.md, «Beta 5.63: BusFault»)."""
    import rollers
    import drumnote
    rollers.use_vtguard()
    drumnote.use_vtguard()


def extra_beta(img, report):
    """after the chain's extra (capkeep, the last of Beta 5.62's, is in the first gap already): the jump sequencer's companion (dspz's first gap:
    after jumprnd and after every other head of SET_TICKS), then the arpeggio's tempo stub (the hole)"""
    import dspz
    import jumpseq
    dspz.add(img, report, "jsfix", jumpseq.FIX)
    extra_rc(img, report)


def extra_rc(img, report):
    """the arpeggio's tempo read as a pure read when not slaved (the hole: it writes nothing); c_artm's site re-pointed from c_cibpm to it"""
    import arp
    arp.tmext_stub(img, report)
    assert "tmext" in report["arp"] and "stub" in report["arp"]["tmext"], "ARP-1: the tempo site is not patched"
