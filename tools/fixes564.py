"""Beta 5.64 / SC57.9 and RC4.15 / RC4.15S (2026-11-15): the options of the fixes after the 5.63 chain crash (see docs/NOTAS.md, «Beta 5.64»).
Called before the chain is built: build_beta5_64 / build_sc57_9 call beta(), build_r415 / build_r415s call rc().

The crash (the black box record of 2026-11-15, Beta 5.63, «pattern chain is broken»): the stopped sequencer tick's store commit (0x080353C0) of
Drum 4's step store 0x2003bd90 reached its listener entry 2, the velocity bar's listener sub-object 0x20043610 (= C3 + 8, class C, vtable
0x0805AD7C, listener vtable 0x0805ADA8), whose vtable word had been overwritten with 0x0805AD60 (one byte, 0xA8 -> 0x60) = the address of slot 7
of the drum Note view class 0x0805AD44 = rollers.c_rlleds | 1: the commit ran c_rlleds with that sub-object as `this`, drumnote.c_nvl took
[[this + 4]] (the header of store 0x2003bbf4, 0x1f020520) as the LED buffer and read 0x1f02055e: BusFault.  In the stock that slot holds the LED
getter (`ldr r0, [r0, #4]; ldr r0, [r0]`), harmless with any object.  The writer of that byte is not found (the hunt: NOTAS); the fix makes the
slot-7 code inert with a foreign `this`: rollers.use_vtguard() (c_rlleds returns at once, nothing written, when [this] != 0x0805AD44; the check
runs before its push; 16 B).  c_nvl (drumnote) is reached only through c_rlleds in every build with rollers (RC2 and later, every beta): the beta
chain, with 12 B of flash left, guards c_rlleds only; the RC chain, where the SC49 / SC49.3 dead-code trims free about 2 KB, guards both."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))


def beta():
    """every 5.64 option for the beta chain (set before the chain is built)"""
    import rollers
    import jumpseq
    rollers.use_vtguard()                                     # the crash: slot 7 of the drum Note view class with a foreign `this`
    jumpseq.use_tgchk()                                       # the review: a pointing target from a garbage record tail wrote a byte in our RAM


def rc():
    """the RC chain: the SC49 / SC49.3 dead-code trims it never got (fullwalk on RC4.14: packio.c_xswap / c_xswap2 646 + 400 B, sc18.c_dk18
    430 B, vcf20.c_edknob 240 B, playmode.c_pmnudge 218 B, sc15.c_spad 212 B: unreachable there too), then both slot-7 guards."""
    import packio
    import drums18
    import vcf21
    import playmode
    import build_sc15
    import fixes563
    packio.use_trimx()
    drums18.use_trim()
    vcf21.use_trimed()
    playmode.use_trimnu()
    build_sc15.use_trim()
    fixes563.vtguard()                                        # rollers.use_vtguard() + drumnote.use_vtguard()
