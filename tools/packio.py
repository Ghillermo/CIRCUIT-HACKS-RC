"""SC35: the pack's samples on the SD card (the user's design, 2026-10-09), through the stock content API of the storage task (proven with SC35D4..SC35DA).

1. Save the captured sample into the pack.  The drum replacement of SC34 (Shift + pad twice in the drum Preset view) points the sample table entry
   X:$1D8D + 4 N at one of the 8 capture slots (Y:HIGH_SLOT0 + k * MAXLEN).  When the project is saved (the bl at 0x0802FE5E, after persist19's c_pl_save
   was put there), c_svs first writes every replaced sample N whose slot k is not marked saved (bit k of X:SAVED = X:SMB + 0x1E, cleared by the tick when
   the slot gets a new capture: build_sc17.SMP_SAVEBIT) into the pack as PCM/NN_PCM.wav (delete the old file, write a 44-byte WAV header + the 16-bit samples,
   mono 48 kHz), if the pack's sample memory can hold it (sum over the 64 PCM items of (size - 44) / 2 + 0x100 words <= $E80000 - $580000).
2. Swap two samples (drum Preset view): Duplicate held + pad A, then pad B: file A gets B's audio and file B gets A's (read back from the DSP's memory, where
   the pack is loaded), and the two table entries are swapped so it sounds swapped at once.  A blinks blue while waiting for B; A again = cancel.
3. Delete a whole pack (packs view, vtable 0x0805A6A4; the user, 2026-10-09): Clear held (no Shift: Shift + Clear is the metronome) + a pad = that pack
   asked (its pad and Clear blink red); Clear pressed again within ~5 s = deleted (op 5, kind 1, the stock pack number = the pad), then the current pack is
   re-selected in the storage task (op 0 on its PCM 0).  Never the current pack.  In the packs view Clear is dim white.  The emptied slot stays lit until the
   next power-up (the stock re-creates an empty folder; the pack list is rebuilt at boot).  Clear presses reach the held-buttons object (controller + 0x20,
   vtable 0x0805A91C) slot 2; its slot 8 draws the Clear / Duplicate LEDs: both are wrapped (the stock runs first).

4. (CROSS, SC37; the user, 2026-10-10) Swap samples between packs.  Duplicate + pad A "copies" sample A of the current pack: the clip
   (pack, A) lives in the DSP word X:CLIPW (sampler_dsp.CLIP clears it at power-up; MAGIC in bits 16-23) and survives releasing Duplicate, other views and
   loading another pack.  Duplicate + pad B: same pack = the swap of 2. (A again = cancel); another pack = c_xswap: the file of pack X sample A is copied
   to sample B of the current pack (read / write in 4 KB pieces), sample B's audio (still in the DSP's memory) is written as pack X's sample A, then
   the new B is read back from the card into the free external memory IMP_LO..IMP_HI (X:IMPW = the next address; host writes to Y:WIN + the sampler's
   block copy) and table entry B points there, so it sounds at once; both packs must still fit their sample memory, else nothing changes.  The
   clip is cleared by every swap and by a cancel.  LEDs (drum Preset view, Duplicate held): the copied pad blinks blue in its own pack, magenta in
   another one (a mirror of the clip in the view bytes +0x52 / +0x53, cosmetic only).

5. (PATCHX, SC37.1; the user, 2026-10-10) Swap synth patches between packs, the same way in the synth Preset view: Duplicate + pad A copies patch A
   (page x 32 + pad, 128 per pack; the clip in X:PCLIPW), Duplicate + pad B swaps A of the copied pack and B of the current one (the same pack too;
   A again = cancel).  A pack keeps its patches in 16 files Patches/NN_PATCHBANK.cpb of 8 patches each (340 bytes every 512; seen on the SD card copy),
   and the device keeps only the patches in use in RAM: c_pswap reads both 340-byte patches (op 6, kind 3, bank P / 8, offset 512 * (P % 8)) and writes
   each into the other bank in place (op 7 does not truncate), then B is chosen again through the stock pad handler so the new patch is loaded.
   Not in the source / step-drummer views of SC19.1 / SC27 (c_sdscr).  LEDs while Duplicate is held: the copied patch blinks blue in its pack, yellow
   in another one (read from the DSP only then).  CROSS_COL: the colour of a sample copied in another pack (SC37 magenta, SC37.1 yellow: Synth 1 is magenta).

6. (FIX2, SC37.2; SC37.1 on the device: swaps between packs deleted or mixed up samples) An item of another pack makes the storage task switch
   ITS current pack ([[0x20006914]], the one 0xFF means) to that pack (0x0803676C): after the first read of pack X, every 0xFF item meant pack X.
   With FIX2 the loaded pack comes from the packs view ([0x20044128 + 0x10] p0, the stock's own "current pack"; [[0x20006914]] only if that object
   is not there), c_xswap / c_pswap name it explicitly in every item, the storage task is put back on it at the end (c_resel), and so is it before a
   swap inside the pack; if copying the file of X:A into B fails after B was deleted, B is written back from the DSP's memory.
   Deleting a pack (3.) did nothing on the device: in the packs view the LED task never calls the held-buttons LEDs (slot 8: Clear never dim white)
   and the "Clear held" bit is not kept there, so the question was never asked.  With FIX2 it needs presses only: Clear (a tap, no Shift) arms it
   for ~5 s (every other lit pack blinks red), a pack pad = that pack asked (only it blinks; the pack is not loaded), Clear again = deleted.  A pad
   with Clear held still asks at once.  PQ_ARMED in the asked byte = armed, no pack yet.

7. (EXACT, SC37.3; the user, 2026-10-10: «se produce un click al final del sample») The samples written back from the DSP's memory were not the
   files: the stock loader keeps only whole 512-byte blocks of a file (0x08049AFA: size & ~511, + 0x100 padding words) and the table entry starts
   2 samples in, so a rebuilt WAV lost its first 2 samples and ended in an abrupt cut to zeros (a click; seen on the SD card: 29_PACK/09_PCM.wav vs
   00_.../09_HousePercB3.wav).  With EXACT the swaps move the files byte for byte, the DSP's free external memory being the temporary store:
   c_f2d (file -> DSP words, 16 bits each, the header too), c_f2f (file -> file in 4 KB pieces), c_d2f (DSP words -> file).  Between packs
   (c_xswap2): X:A -> DSP, B's file -> X:A, the DSP copy -> B; the copy stays as the live sample of B (entry = its data, 256 zero words after it).
   Inside the pack (c_swap2): A -> DSP (temporary, IMPW not moved), B -> A, the DSP copy -> B, the table entries exchanged; a replaced drum (entry in
   a capture slot) keeps the SC35 way.  A failed step puts the files back from the copies.

8. (COPYX, SC37.4; the user, 2026-10-10: «al duplicar un sample ENTRE PACKS, copia el primer sample al segundo, no lo intercambies con el
   primero») Between packs Duplicate copies: c_xcopy2 = X:A -> the DSP, B's own file -> the DSP after it (the backup), the copy of X:A -> B (B's
   backup put back if that fails), the copy stays as B's live sample; pack X is never written.  Only this pack must still fit its sample memory.
   Patches the same way: between packs c_pswap writes only B.  Inside a pack Duplicate still swaps.

9. (DUPMASK, SC37.4; SC37.3 on the device: «duplicate no se enciende con parches de sinte, ni parece hacer nada pulsarlo») The stock accepts
   held buttons per view: the controller reads the active view's slot 8 (0x08033B52) into [held-buttons object + 0x1C] when the view changes,
   and the press (0x08041530) sets the held bit only if the mask has it.  The track views' container (vtable 0x0805A62C) gives 1 (Clear only)
   for every Preset view, so Duplicate was never lit nor held there and c_spp / c_pdp never saw it (the tests had set the bit by hand).
   c_hmask (the container's slot 8) adds Duplicate when [MGR + 0x152] is the Preset view of Synth 1 / 2 or Drum 1..4.

10. (PKLED, SC37.5; SC37.4 on the device: «Clear no se ilumina en ningún momento durante el borrado de pack. El borrado funciona») c_mbl never runs
   in the packs view (the LED task does not call the held-buttons LEDs there), so the Clear LED stayed dark.  c_pkled takes the two LED task calls
   (in front of vcf21's c_vledtask) and, with the packs view on the screen, writes panel LED 55 of the frame: dim white, blinking red while a delete
   is armed or asked (the question is fresh).

11. (SRCGUARD, SC37.6; found in a review, 2026-10-10) SC19.1's source view (Synth 1 / 2 pressed again with its track view on the screen) is the
   same Preset view object with flag F_SRC, and c_spp only stepped aside for the step-drummer view (c_sdscr).  Pressing Duplicate there closes
   the source view (any button does) and Duplicate + pad is then the patch list, as it should; but with Duplicate already held when the source
   view opens (held in the track view, then Synth 1), a pad of the source view copied patch page x 32 + pad and a second one swapped / copied it.
   c_srcv = the synth Preset view shows the source view or a step-drummer view; then c_spp / c_spl hand everything to the stock.  The Duplicate
   LED stays as it is there (dim = available: pressing it goes back to the patch list).

12. (IMPGUARD, SC37.6; found in a review, 2026-10-10) Imported samples (a copy between packs, the temporary copy of a swap) go one after another into the
   free external memory IMP_LO..IMP_HI (≈ 2.1 M words, ≈ 44 s); when the next one does not fit, c_impdst went back to IMP_LO, over the first imports,
   which the sample table may still play (a drum would sound wrong until the pack is loaded again; the files are right).  c_impfree checks the 64
   table entries: when one starts inside the place, c_impdst returns 0 and nothing changes (as with a sample that does not fit).  Once the pack is
   loaded again its samples come from the stock area and the free memory can be reused.

13. (INPLACE, SC37.7; the user, 2026-10-10: «¿es posible que el búfer de 44 s se limpie al consolidar los pads a la SD?» — the copy is on the card at once;
   the free memory only makes it sound at once) The stock loader (0x08049A1C / 0x08049A80) puts the 64 samples one after another from $580000, each in
   (data bytes & ~511) / 2 words + 0x100 zero words, the table entry 2 words after the start of its place.  c_inplace: when the copied sample (its data
   words + PADW zeros) fits between B's entry and the next entry start - 2 (c_nextstart: the nearest start above B among the 64 entries inside the pack's
   sample memory; none above: B's own length + PADW), the DSP's block copy moves it there from the free memory (where c_xcopy2 put it, as a temporary),
   the zeros follow, B's entry keeps its start with the new length, and X:IMPW does not move: most replacements of similar drums use no free memory at
   all.  c_impdst: when no entry of the table starts inside the free memory (after the pack was loaded again, or every import was replaced in place),
   the next import starts at IMP_LO again.  Nothing hooks the stock loader (it runs in the storage task; the DSP service semaphore must not be taken there).

14. (PKLED2, SC37.8; SC37.7 on the device: «el botón Clear parpadea blanco. Mejor, blanco fijo. Al pulsar clear, se apagan todos los pads menos el
   seleccionado; los pads siguen apagados al soltar clear») c_ppl wrote the red / dark blink into the packs view's own LED buffer: a dark phase left
   zeros there, which the next pass took for empty slots, so the packs stayed dark until the stock drew the view again (the tests accepted red or dark
   and never looked again later).  Now c_ppl leaves the buffer alone and c_pkled (each pass of the LED task, after the stock copied the buffer into
   the frame; frame entry k = pad k) blinks the frame's pads: armed, every lit pack but the loaded one; asked, only that one; otherwise the stock's
   colours show again.  Clear: dim white, steady white (CLR_ON) while the question is fresh (the panel buttons are white: the red blink was a white one).

15. (PKLED3, SC38.4; SC37.8 on the device: «Clear sigue parpadeando al abrir. Clear debe estar blanco fijo al abrir el view, y mantener los colores y
   parpadeos anteriores al hacer una selección y confirmar») Clear is CLR_ON (steady white) in the packs view from the start, not CLR_DIM; the question
   (the pads blinking on the frame, Clear steady white) is as in SC37.8.

16. (EMPTY, SC38.4; SC37.4 on the device: «duplicate patch entre packs funciona sólo si el hueco del patch no está vacío») a copy between packs read B
   first and gave up when it was empty: a sample needed B's file (size > 44), a patch needed B's 340 bytes.  The card copy shows how the stock keeps
   them: a patch bank Patches/NN_PATCHBANK.cpb holds its patches one after another (16 bytes of name, the data, 0xFF to 512; the last one without the
   padding: 3924 = 7 x 512 + 340 for 8, 1876 for 4, 340 for 1) and an empty slot is past the end of the file (a bank without patches has no file).
   Now, between packs: a sample B that is empty is not read or backed up, the copy goes to the free memory (not in place: an empty entry has no place)
   and its file is created (op 7); a patch B is not read: the bank's size gives the patches it holds (n = (size + 511) / 512) and A is written at B's
   slot and at every empty slot before it (the bank cannot keep a hole: those become copies of A too).  Inside one pack Duplicate still swaps
   (both must exist).

17. (INITGAP, SC38.5; the user, 2026-10-11: «¿es posible que se rellene con el parche por defecto (el que suena cuando no hay nada asignado al
   hueco)?») the stock keeps a default patch in the flash, "Initial Patch" at 0x080584F0 (16 bytes of name and the data, as in a bank; 0x0802998E loads
   it into the synths): the empty slots between the bank's end and B are written from it (the write takes the flash address as its buffer); B gets A.

18. (FFGAP, SC38.6; the user, 2026-10-11: «déjalos vacíos como hasta ahora») the stock, saving a patch past the end of its bank (0x0802FBCC),
   fills from the old end to the slot with 0xFF (memset 0x0801A9BC) and then writes the 340 bytes: the slots between are 0xFF records, which it takes
   for empty.  The same here: one write of 0xFF (the shared buffer from + 512: at most 7 x 512 bytes) from the bank's size to B's offset, then A at B.
19. (PMODE, SC38.8; the user, 2026-10-11: «en la vista del selector de patch de synth stock se muestra el pad en color azul oscuro si el patch es mono,
   purple si es glide e inalterado si es poly») The synth Preset view colours each patch pad by its voice mode, byte 32 of the patch (0 Mono, 1 Mono AG =
   glide, 2 Poly; checked on the factory pack): mono dark blue, glide purple (brighter on the selected patch), poly as the stock draws it.  The modes live
   only on the SD card (the stock reads a patch when it is chosen), so c_pmode (in c_spl, the view's slot 7, every LED pass) keeps the 32 modes of the
   page shown, 2 bits each, with a tag (magic, pack, page, selected patch, time) in the Master FX block's idle LED buffer (S_SCR: the CC editor's scratch,
   used only while the MIDI Preset view shows it; Master FX repaints the buffer whenever it is shown): no new RAM.  A new tag (another pack / page / patch
   chosen, or 4 s gone) reads the page's four banks again (size, then up to 4 KB into the shared buffer under its lock, as c_pswap).  Only pads still in a
   stock colour (dim / bright of the synth) or in ours are recoloured, so other stock drawings show through; a pad that becomes poly gets the stock
   colour back.  Not over the source / step-drummer views.

The DSP's external memory is read through the sampler's own block copy (CPSRC / CPDST / CPLEN into the Y window WIN; rdiag.DSPX), with the DSP service
semaphore taken around every host-port access (never from the DSP tick: everything here runs in the UI task); the WAV goes out in 4 KB pieces from the
stock's shared buffer 0x20003D04 (lock 0x08026D06 / 0x08026D34, owner 5 as Components' SysEx).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, lsls_imm, lsrs_imm, mov_reg, movs_imm, movt, movw, adds_imm8, subs_imm8,  # noqa: E402
                   pop_list, push_list, raw, h, tst_reg, ands_reg, orrs_reg, bics_reg, adds_reg, subs_reg, str_imm, strb_imm, strh_imm, strh_reg,
                   add_sp_imm, sub_sp_imm, ldrb_w, strb_w, ldrh_reg)
import sampler_dsp as SD  # noqa: E402
import build_sc14 as s14  # noqa: E402

MGR = 0x20040B10                                 # the controller; [MGR + 0x20] = the held-buttons object, its +0xC store: p0 bit 0 Clear, bit 1 Duplicate
PARAM_GET = 0x0803542C
DSP_READ, DSP_WRITE = 0x08029344, 0x080292F8
SEM_PTR, SEM_TAKE, SEM_GIVE = 0x2000030C, 0x08021064, 0x08029028
SLEEP = 0x0801BE78
EXISTS, SIZE, WRITE, DEL_FN = 0x0803CB50, 0x0803CB6A, 0x0803CC16, 0x0803CC34
BUF_LOCK, BUF_UNLOCK, BUF, BUFSZ = 0x08026D06, 0x08026D34, 0x20003D04, 4096
SAVE_CALL = 0x0802FE5E                           # persist19 put `bl c_pl_save` here
DP_VT = 0x0805ABBC                               # drum Preset view (slot 0 pad, slot 7 LEDs; drumrep wraps them first)
PV_VT = 0x0805A6A4                               # packs view (slot 0 pad, slot 7 = the LED buffer [[view + 4]])
PV_PAD = 0x08044007
TAB = SD.SAMPLE_TAB                              # X:$1D8D + 4 N: start, length, base increment
SAVED = SD.SMB + 0x1E
WIN, NW = 0x3B40, 64                             # the Y window and the words per copy
KIND_PCM = 4
LIMIT = 0xE80000 - 0x580000                      # words of the pack's sample memory
PAD_W = 0x100                                    # the loader's padding per sample (0x08049B06)
SWAP_OFF, SWAP_MAGIC = 0x52, 0xA5                # drum Preset view bytes +0x52 = magic when A is chosen, +0x53 = A (padding: never trusted without the magic)
PQ_MAGIC, PQ_OFF = 0xA5, 0x25                    # packs view bytes +0x25 = magic, +0x26 = the asked pad, +0x27 = when ((ms >> 8) & 0xFF) (+0x25..+0x27 = padding)
PQ_LIFE = 19                                     # a question lives 19 x 256 ms ~ 5 s
PQ_ARMED = 0xFE                                  # FIX2: Clear tapped, no pack asked yet
MB_VT = 0x0805A91C                               # the held-buttons object (controller + 0x20): slot 2 = Clear / Duplicate pressed (id), slot 8 = its LEDs
MB_PRESS, MB_LEDS = 0x08041531, 0x08041649
CLR_DIM = 0x03                                   # dim white
BLUE, RED, DARK = 0x09, 0x53, 0x00
HAL_TICK = s14.TICK
CROSS = False                                    # SC37: swap samples between packs (see 4.)
READ = 0x0803CBF0                                # op 6 (item, offset, buf, len, cb, ctx, &done)
CUR_PACK_PTR = 0x20006914                        # [[CUR_PACK_PTR]] = the current pack, numbered as the API
CLIP_MAGIC = 0xA5
MIR_P, MIR_I = 0xC0, 0x40                        # the mirror: +0x52 = MIR_P | pack, +0x53 = MIR_I | sample (cosmetic: LEDs only)
IMP_LO, IMP_HI = 0x380000, 0x57F000              # free external memory (SC35D3), after the Glitch's ring ($340000-$37FFFF)
MAGENTA = 0x32
YELLOW = 0x2D
FIX2 = False                                     # SC37.2 (see 6.)
EXACT = False                                    # SC37.3 (see 7.)
COPYX = False                                    # SC37.4 (see 8.)
PADW = 0x100                                     # zero words after a live sample (as the stock loader)
DUPMASK = False                                  # SC37.4: Duplicate accepted as a held button in the synth / drum Preset views (see 9.)
PKLED = False                                    # SC37.5: the Clear LED in the packs view (see 10.)
SRCGUARD = False                                 # SC37.6: Duplicate out of the synth Preset view while it shows the source / step-drummer view (see 11.)
IMPGUARD = False                                 # SC37.6: the free memory never overwrites a sample the table still plays (see 12.)
INPLACE = False                                  # SC37.7: a copy in the replaced sample's own place when it fits; the free memory starts again when unused (see 13.)
PKLED2 = False                                   # SC37.8: the packs view's pads drawn on the frame, Clear steady white while asking (see 14.)
PKLED3 = False                                   # SC38.4: Clear steady white from the moment the packs view opens (see 15.)
EMPTY = False                                    # SC38.4: a copy between packs into an empty sample / patch slot (see 16.)
INITGAP = False                                  # SC38.5: the empty patch slots before B filled with the stock's Initial Patch (see 17.)
FFGAP = False                                    # SC38.6: ... left empty as the stock does (0xFF from the bank's end to B; see 18.)
PMODE = False                                    # SC38.8: patch pads coloured by voice mode in the synth Preset view (see 19.)
PLAYHOLD = False                                 # SC42.1: the ~4 s rereads of c_pmode (and mpatch) wait for the transport stopped (see use_playhold)
TRANSPORT = 0x20011034                           # the transport store: p0 = playing
PM_MAGIC, PM_LIFE = 0xA5C3, 16                   # the cache's tag word; it is read again after PM_LIFE x 256 ms (~4 s)
PM_CACHE = 40 + 64                               # c_gst() + GFX_OFF + S_SCR: the Master FX block's idle LED buffer (vcf21.S_SCR)
PM_MONO = (0x0E, 0x09)                           # dark blue / blue (the selected patch)
PM_GLIDE = (0x4C, 0x49)                          # purple / light purple
PM_VOICE = 32                                    # the patch's byte: voice mode (0 Mono, 1 Mono AG, 2 Poly)
TRACK_COLS = 0x08056464                          # the stock's colour table (u16): pads = [idx + 1], the selected patch = [idx], idx = view + 0x26
MEMSET = 0x0801A9BC                              # __aeabi_memset(dst, n, c), as the stock's patch save uses it (0x0802FBDA)
INIT_PATCH = 0x080584F0                          # the stock's "Initial Patch" (340 bytes in the flash; 0x0802998E loads it into the synths)
CLR_ON = 0x01                                    # white (the panel buttons are white: a "red" blink showed as a white one)
STOCK_LO, STOCK_HI = 0x580000, 0xE80000          # the pack's sample memory (the stock loader 0x08049A1C)
N_SAMPLES = 64                                   # entries of the sample table (X:TAB, 4 words each: start, length, increment, -)
S_PAINT, F_SRC = 20, 4                           # SC19.1: the SC14 state byte with the "source view open" flag (vcf21.S_PAINT / F_SRC)
LED_CALLS = (0x08033B46, 0x0803415A)             # the two calls of the LED task (vcf21's c_vledtask there)
LED_CLEAR = 55                                   # panel LED of Clear
CT_VT, CT_MASK = 0x0805A62C, 0x08059F19          # the track views' container: slot 8 = the held buttons it accepts (bit 0 Clear, 1 Duplicate)
DUP_SUBS = (0, 9, 36, 45, 54, 63)                # [MGR + 0x152] = 9 x track + sub-view: the Preset views of Synth 1 / 2 and Drum 1..4
PV_OBJ = 0x20044128                              # the packs view object (heap, fixed for this firmware): vtable PV_VT, [+0x10] p0 = the loaded pack
CROSS_COL = MAGENTA                              # SC37.1: YELLOW
PATCHX = False                                   # SC37.1: swap synth patches between packs (see 5.)
SP_VT = 0x0805AC9C                               # the synth Preset view: slot 0 pad, slot 7 LEDs
KIND_PATCH, PATCH_SZ, PATCH_STRIDE, PER_BANK = 3, 340, 512, 8
PCLIP_MAGIC = 0xA6


def use_dupmask():
    """SC37.4: Duplicate is a held button in the synth / drum Preset views too (see 9.)."""
    global DUPMASK
    DUPMASK = True


def use_pkled():
    """SC37.5: the Clear LED in the packs view (see 10.)."""
    global PKLED
    PKLED = True


def use_srcguard():
    """SC37.6: Duplicate does nothing (and stays dark) in the synth Preset view while it shows SC19.1's source view or the step-drummer (see 11.)."""
    global SRCGUARD
    assert DUPMASK and PATCHX
    SRCGUARD = True


def use_impguard():
    """SC37.6: c_impdst refuses a place where a sample of the table still starts (see 12.)."""
    global IMPGUARD
    assert EXACT
    IMPGUARD = True


def use_inplace():
    """SC37.7: copies between packs go into the replaced sample's place when they fit, and the free memory starts again once nothing uses it (see 13.)."""
    global INPLACE
    assert IMPGUARD and COPYX
    INPLACE = True


def use_pkled2():
    """SC37.8: the delete question of the packs view drawn on each LED frame (see 14.)."""
    global PKLED2
    assert PKLED and FIX2
    PKLED2 = True


def use_pkled3():
    """SC38.4: Clear steady white in the packs view from the start (see 15.)."""
    global PKLED3
    assert PKLED2
    PKLED3 = True


def use_empty():
    """SC38.4: Duplicate between packs copies into an empty slot too (see 16.)."""
    global EMPTY
    assert COPYX and INPLACE
    EMPTY = True


def use_initgap():
    """SC38.5: the empty patch slots before B get the Initial Patch, not copies of A (see 17.)."""
    global INITGAP
    assert EMPTY
    INITGAP = True


def use_pmode():
    """SC38.8: the synth Preset view colours each patch by its voice mode (see 19.)."""
    global PMODE
    assert PATCHX and SRCGUARD
    PMODE = True


def use_playhold():
    """SC42.1 (the stutter of the delay, Beta only; the user, 2026-10-16): in emulation the Beta reads the card synchronously every ~4 s while playing in
    the Preset views (c_pmode: the 4 banks of the page in the synth Preset view; mpatch: 2 banks in the Preset view of MIDI 1 / 2), the RC never.  With
    this the periodic reread waits for the transport stopped; the rereads on a change (pack, page, patch) stay."""
    global PLAYHOLD
    assert PMODE
    PLAYHOLD = True


def use_pmode2():
    """SC39 (the user, 2026-10-12: «el color purple se muestra parpadeando en vez de fijo»): 0x4C is one of the board's animated colour codes (its
    entry of the RGB table in RAM, 0x20003804, pulses; 0x4B blinks), so the glide patches pulsed.  Steady codes of the same family: 0x49 (lavender) for a
    glide patch, 0x5C (pale violet) for the selected one."""
    global PM_GLIDE
    assert PMODE
    PM_GLIDE = (0x49, 0x5C)


def use_ffgap():
    """SC38.6: the empty patch slots before B stay empty, 0xFF as the stock writes them (see 18.)."""
    global FFGAP
    assert EMPTY and not INITGAP
    FFGAP = True


def use_copyx():
    """SC37.4: use_exact + Duplicate between packs copies instead of swapping (see 8.)."""
    global COPYX
    use_exact()
    COPYX = True


def use_exact():
    """SC37.3: use_fix2 + swaps that move the files byte for byte (see 7.)."""
    global EXACT
    use_fix2()
    EXACT = True


def use_fix2():
    """SC37.2: use_cross2 + the loaded pack named explicitly (see 6.)."""
    global FIX2
    use_cross2()
    FIX2 = True


def use_cross2():
    """SC37.1: use_cross + synth patches between packs (sampler_dsp.CLIP2) + yellow for a clip of another pack."""
    global PATCHX, CROSS_COL
    use_cross()
    SD.CLIP2 = True
    PATCHX, CROSS_COL = True, YELLOW


def use_cross():
    """SC37: swap samples between packs (needs sampler_dsp.CLIP for the clip word)."""
    global CROSS
    SD.CLIP = True
    CROSS = True
INV = {"eq": "ne", "ne": "eq", "lo": "hs", "hs": "lo", "hi": "ls", "ls": "hi", "lt": "ge", "ge": "lt"}


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    zc = [0]
    udiv = s14.udiv

    def bc(target, cond):
        zc[0] += 1; n = f"_p{zc[0]}"
        a.emit(b_cond, n, INV[cond]); a.emit(b, target); a.label(n)

    def imm32(rd, v): a.emit(movw, rd, v & 0xFFFF); a.emit(movt, rd, (v >> 16) & 0xFFFF)

    # ---- DSP host port, all with the semaphore taken by the caller (c_take / c_give: r0 = the holder word's address)
    a.label("c_take")                                # (r0 = &holder)
    a.emit(push_list, [4], lr=True); a.emit(mov_reg, 4, 0)
    imm32(1, SEM_PTR); a.emit(ldr_imm, 1, 1, 0); a.emit(adds_imm8, 1, 0xC); a.emit(str_imm, 1, 4, 0)
    a.emit(mov_reg, 0, 1); a.emit(bl, SEM_TAKE); a.emit(pop_list, [4], pc=True)
    a.label("c_give")                                # (r0 = &holder)
    a.emit(b_w, SEM_GIVE)
    a.label("c_xr")                                  # r0 = X:r0 (24 bits)
    a.emit(push_list, [4], lr=True)
    a.emit(mov_reg, 1, 0); a.emit(movs_imm, 0, 0); a.emit(bl, DSP_READ); a.emit(lsrs_imm, 0, 0, 8)
    a.emit(pop_list, [4], pc=True)
    a.label("c_xw")                                  # X:r0 = r1
    a.emit(mov_reg, 2, 0); a.emit(lsls_imm, 1, 1, 8); a.emit(movs_imm, 0, 0); a.emit(b_w, DSP_WRITE)

    # ---- c_copy (r0 = external Y source, r1 = n <= NW): the sampler copies n words to Y:WIN in its next block -> r0 = 0, or 4 = no copy
    a.label("c_copy")
    if CROSS:                                        # = c_copy2(r0, WIN, r1)
        a.emit(mov_reg, 2, 1); imm32(1, WIN)
        a.label("c_copy2")                           # (r0 = Y source, r1 = Y destination, r2 = n <= NW)
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(sub_sp_imm, 8); a.emit(mov_reg, 7, 13); a.emit(mov_reg, 4, 0)
    if CROSS: a.emit(str_imm, 1, 7, 4); a.emit(mov_reg, 5, 2)
    else: a.emit(mov_reg, 5, 1)
    a.emit(movs_imm, 6, 200)
    a.label("cp_free")                               # wait until no copy runs (a drum replacement may)
    a.emit(mov_reg, 0, 7); a.emit(bl, "c_take"); imm32(0, SD.CPLEN); a.emit(bl, "c_xr")
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "cp_go", "eq")
    a.emit(mov_reg, 0, 7); a.emit(bl, "c_give"); a.emit(movs_imm, 0, 1); a.emit(bl, SLEEP)
    a.emit(subs_imm8, 6, 1); bc("cp_free", "ne"); a.emit(movs_imm, 0, 4); a.emit(b, "cp_x")
    a.label("cp_go")
    imm32(0, SD.CPSRC); a.emit(mov_reg, 1, 4); a.emit(bl, "c_xw")
    imm32(0, SD.CPDST)
    if CROSS: a.emit(ldr_imm, 1, 7, 4)
    else: imm32(1, WIN)
    a.emit(bl, "c_xw")
    imm32(0, SD.CPLEN); a.emit(mov_reg, 1, 5); a.emit(bl, "c_xw")
    a.emit(mov_reg, 0, 7); a.emit(bl, "c_give")
    a.emit(movs_imm, 6, 100)
    a.label("cp_w")
    a.emit(movs_imm, 0, 1); a.emit(bl, SLEEP)
    a.emit(mov_reg, 0, 7); a.emit(bl, "c_take"); imm32(0, SD.CPLEN); a.emit(bl, "c_xr"); a.emit(mov_reg, 4, 0)
    a.emit(mov_reg, 0, 7); a.emit(bl, "c_give")
    a.emit(cmp_imm, 4, 0); a.emit(b_cond, "cp_ok", "eq")
    a.emit(subs_imm8, 6, 1); bc("cp_w", "ne"); a.emit(movs_imm, 0, 4); a.emit(b, "cp_x")
    a.label("cp_ok"); a.emit(movs_imm, 0, 0)
    a.label("cp_x"); a.emit(add_sp_imm, 8); a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_wav (r0 = N, r1 = Y source, r2 = n samples) -> r0 = status: PCM N of the current pack := a WAV of those samples
    # frame r7: [0] cb [4] ctx [8] holder [12] spare [16..27] item [28] src [32] remaining [36] file offset [40] pos [44] status
    a.label("c_wav")
    if CROSS:
        a.emit(movs_imm, 3, 0xFF)
        a.label("c_wavp")                            # (r0 = N, r1 = Y source, r2 = n, r3 = pack)
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(sub_sp_imm, 48); a.emit(mov_reg, 7, 13)
    if CROSS: a.emit(mov_reg, 4, 3)
    a.emit(movs_imm, 3, 0)
    for o in range(0, 48, 4): a.emit(str_imm, 3, 7, o)
    a.emit(movs_imm, 3, KIND_PCM); a.emit(str_imm, 3, 7, 16); a.emit(str_imm, 0, 7, 20)
    if CROSS: a.emit(strb_imm, 4, 7, 24)
    else: a.emit(movs_imm, 3, 0xFF); a.emit(strb_imm, 3, 7, 24)
    a.emit(str_imm, 1, 7, 28); a.emit(str_imm, 2, 7, 32)
    a.emit(movs_imm, 0, 5); a.emit(bl, BUF_LOCK)
    a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, 16); a.emit(movs_imm, 1, 0); a.emit(movs_imm, 2, 0); a.emit(bl, DEL_FN)     # the old file (if any)
    imm32(4, BUF)                                    # r4 = the buffer: the 44-byte header
    a.emit(ldr_imm, 5, 7, 32); a.emit(lsls_imm, 5, 5, 1)                      # r5 = data bytes
    for off, v in ((0, 0x46464952), (8, 0x45564157), (12, 0x20746D66), (16, 16), (20, 0x00010001), (24, 48000), (28, 96000), (32, 0x00100002), (36, 0x61746164)):
        imm32(0, v); a.emit(str_imm, 0, 4, off)
    a.emit(str_imm, 5, 4, 40); a.emit(mov_reg, 0, 5); a.emit(adds_imm8, 0, 36); a.emit(str_imm, 0, 4, 4)
    a.emit(movs_imm, 0, 44); a.emit(str_imm, 0, 7, 40)
    a.label("wv_l")
    a.emit(ldr_imm, 5, 7, 32); a.emit(cmp_imm, 5, 0); bc("wv_flush", "eq")
    a.emit(cmp_imm, 5, NW); a.emit(b_cond, "wv_n", "ls"); a.emit(movs_imm, 5, NW)
    a.label("wv_n")                                  # r5 = n of this copy
    a.emit(ldr_imm, 0, 7, 28); a.emit(mov_reg, 1, 5); a.emit(bl, "c_copy"); a.emit(cmp_imm, 0, 0); bc("wv_fail", "ne")
    a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, 8); a.emit(bl, "c_take")
    a.emit(movs_imm, 6, 0)
    a.label("wv_r")                                  # r6 = i: halfword i of the window -> buf[pos + 2 i]
    imm32(1, 0x8000 | WIN); a.emit(adds_reg, 1, 1, 6); a.emit(movs_imm, 0, 0); a.emit(bl, DSP_READ); a.emit(lsrs_imm, 0, 0, 16)
    a.emit(ldr_imm, 1, 7, 40); a.emit(adds_reg, 1, 1, 6); a.emit(adds_reg, 1, 1, 6); a.emit(strh_reg, 0, 4, 1)
    a.emit(adds_imm8, 6, 1); a.emit(cmp_reg, 6, 5); a.emit(b_cond, "wv_r", "lo")
    a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, 8); a.emit(bl, "c_give")
    a.emit(ldr_imm, 0, 7, 40); a.emit(adds_reg, 0, 0, 5); a.emit(adds_reg, 0, 0, 5); a.emit(str_imm, 0, 7, 40)
    a.emit(ldr_imm, 0, 7, 28); a.emit(adds_reg, 0, 0, 5); a.emit(str_imm, 0, 7, 28)
    a.emit(ldr_imm, 0, 7, 32); a.emit(subs_reg, 0, 0, 5); a.emit(str_imm, 0, 7, 32)
    a.emit(ldr_imm, 0, 7, 40); imm32(1, BUFSZ - 2 * NW); a.emit(cmp_reg, 0, 1); a.emit(b_cond, "wv_l", "ls")
    a.label("wv_flush")                              # write buf[0 .. pos) at the file offset
    a.emit(ldr_imm, 3, 7, 40); a.emit(cmp_imm, 3, 0); bc("wv_done", "eq")
    a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, 16); a.emit(ldr_imm, 1, 7, 36); a.emit(mov_reg, 2, 4); a.emit(bl, WRITE)
    a.emit(cmp_imm, 0, 0); bc("wv_fail", "ne")
    a.emit(ldr_imm, 0, 7, 36); a.emit(ldr_imm, 1, 7, 40); a.emit(adds_reg, 0, 0, 1); a.emit(str_imm, 0, 7, 36)
    a.emit(movs_imm, 0, 0); a.emit(str_imm, 0, 7, 40)
    a.emit(ldr_imm, 0, 7, 32); a.emit(cmp_imm, 0, 0); bc("wv_l", "ne")
    a.label("wv_done"); a.emit(movs_imm, 0, 0); a.emit(str_imm, 0, 7, 44); a.emit(b, "wv_x")
    a.label("wv_fail"); a.emit(str_imm, 0, 7, 44); a.emit(cmp_imm, 0, 0); bc("wv_x", "ne"); a.emit(movs_imm, 0, 9); a.emit(str_imm, 0, 7, 44)
    a.label("wv_x")
    a.emit(bl, BUF_UNLOCK)
    a.emit(ldr_imm, 0, 7, 44); a.emit(add_sp_imm, 48); a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_entry (r0 = N, r1 = dst[3]): the table entry N (start, length, increment), the semaphore taken here
    a.label("c_entry")
    a.emit(push_list, [4, 5, 6, 7], lr=True); a.emit(sub_sp_imm, 8); a.emit(mov_reg, 7, 13)
    a.emit(lsls_imm, 4, 0, 2); imm32(0, TAB); a.emit(adds_reg, 4, 4, 0); a.emit(mov_reg, 5, 1)
    a.emit(mov_reg, 0, 7); a.emit(bl, "c_take")
    for k in range(3):
        a.emit(mov_reg, 0, 4); a.emit(adds_imm8, 0, k); a.emit(bl, "c_xr"); a.emit(str_imm, 0, 5, 4 * k)
    a.emit(mov_reg, 0, 7); a.emit(bl, "c_give")
    a.emit(add_sp_imm, 8); a.emit(pop_list, [4, 5, 6, 7], pc=True)
    a.label("c_setentry")                            # (r0 = N, r1 = src[3])
    a.emit(push_list, [4, 5, 6, 7], lr=True); a.emit(sub_sp_imm, 8); a.emit(mov_reg, 7, 13)
    a.emit(lsls_imm, 4, 0, 2); imm32(0, TAB); a.emit(adds_reg, 4, 4, 0); a.emit(mov_reg, 5, 1)
    a.emit(mov_reg, 0, 7); a.emit(bl, "c_take")
    for k in range(3):
        a.emit(mov_reg, 0, 4); a.emit(adds_imm8, 0, k); a.emit(ldr_imm, 1, 5, 4 * k); a.emit(bl, "c_xw")
    a.emit(mov_reg, 0, 7); a.emit(bl, "c_give")
    a.emit(add_sp_imm, 8); a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_isize (r0 = N) -> r0 = the size of PCM N of the current pack (0: none)
    a.label("c_isize")
    if CROSS:
        a.emit(movs_imm, 1, 0xFF)
        a.label("c_isizep")                          # (r0 = N, r1 = pack) -> the size of PCM N of that pack
        a.emit(push_list, [4], lr=True); a.emit(sub_sp_imm, 16)
        a.emit(raw, h(0x9102)); a.emit(movs_imm, 1, KIND_PCM); a.emit(raw, h(0x9100)); a.emit(raw, h(0x9001))   # [8] = pack, [0] = kind, [4] = N
    else:
        a.emit(push_list, [4], lr=True); a.emit(sub_sp_imm, 16)
        a.emit(movs_imm, 1, KIND_PCM); a.emit(raw, h(0x9100)); a.emit(raw, h(0x9001))          # str r1,[sp] ; str r0,[sp,#4]
        a.emit(movs_imm, 1, 0xFF); a.emit(raw, h(0x9102))                                       # str r1,[sp,#8] (pack 0xFF, 3 zero bytes)
    a.emit(mov_reg, 0, 13); a.emit(bl, SIZE)
    a.emit(add_sp_imm, 16); a.emit(pop_list, [4], pc=True)

    # ---- c_fits (r0 = N, r1 = new length in samples) -> r0 = 1 if the pack's samples still fit with PCM N of that length
    a.label("c_fits")
    if CROSS:
        a.emit(movs_imm, 2, 0xFF)
        a.label("c_fitsp")                           # (r0 = N, r1 = n, r2 = pack)
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    if CROSS: a.emit(mov_reg, 7, 2)
    a.emit(mov_reg, 6, 0); a.emit(mov_reg, 5, 1); imm32(0, PAD_W); a.emit(adds_reg, 5, 5, 0)           # r5 = total
    a.emit(movs_imm, 4, 0)
    a.label("fi_l")
    a.emit(cmp_reg, 4, 6); a.emit(b_cond, "fi_n", "eq")
    a.emit(mov_reg, 0, 4)
    if CROSS: a.emit(mov_reg, 1, 7); a.emit(bl, "c_isizep")
    else: a.emit(bl, "c_isize")
    a.emit(cmp_imm, 0, 44); a.emit(b_cond, "fi_n", "ls")
    a.emit(subs_imm8, 0, 44); a.emit(lsrs_imm, 0, 0, 1); a.emit(adds_reg, 5, 5, 0); imm32(0, PAD_W); a.emit(adds_reg, 5, 5, 0)
    a.label("fi_n")
    a.emit(adds_imm8, 4, 1); a.emit(cmp_imm, 4, 64); a.emit(b_cond, "fi_l", "lo")
    a.emit(movs_imm, 0, 1); imm32(1, LIMIT); a.emit(cmp_reg, 5, 1); a.emit(b_cond, "fi_x", "ls"); a.emit(movs_imm, 0, 0)
    a.label("fi_x"); a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_svs: the project save (r0 = the session manager): first the unsaved captures, then persist19's c_pl_save
    # frame r7: [0] holder [4] saved [8] count [12..43] pending (N | k << 8, up to 8) [44..55] entry
    a.label("c_svs")
    a.emit(push_list, [0, 4, 5, 6, 7], lr=True)
    a.emit(sub_sp_imm, 56); a.emit(mov_reg, 7, 13)
    a.emit(movs_imm, 0, 0); a.emit(str_imm, 0, 7, 8)
    a.emit(mov_reg, 0, 7); a.emit(bl, "c_take")
    imm32(0, SAVED); a.emit(bl, "c_xr"); a.emit(str_imm, 0, 7, 4)
    a.emit(movs_imm, 4, 0)
    a.label("sv_scan")                               # N = r4: start in a slot, at its base, not saved -> pending
    a.emit(lsls_imm, 0, 4, 2); imm32(1, TAB); a.emit(adds_reg, 0, 0, 1); a.emit(bl, "c_xr"); a.emit(mov_reg, 5, 0)
    imm32(1, SD.HIGH_SLOT0); a.emit(subs_reg, 0, 5, 1); a.emit(b_cond, "sv_next", "lo")         # (unsigned: below the slots -> next)
    imm32(1, SD.MAXLEN); a.emit(raw, udiv(2, 0, 1))                                          # r2 = k
    a.emit(cmp_imm, 2, SD.SLOTN); a.emit(b_cond, "sv_next", "hs")
    a.emit(raw, h(0xFB01) + h(0xF302))                                                       # mul r3, r1, r2
    a.emit(cmp_reg, 3, 0); a.emit(b_cond, "sv_next", "ne")                                   # not at the slot's start
    a.emit(ldr_imm, 0, 7, 4)
    a.emit(movs_imm, 1, 1); a.emit(raw, h(0x4091))                                           # lsls r1, r2 -> bit k
    a.emit(tst_reg, 0, 1); a.emit(b_cond, "sv_next", "ne")                                   # saved
    a.emit(ldr_imm, 0, 7, 8); a.emit(cmp_imm, 0, 8); a.emit(b_cond, "sv_next", "hs")
    a.emit(lsls_imm, 1, 0, 2); a.emit(adds_reg, 1, 1, 7)
    a.emit(lsls_imm, 3, 2, 8); a.emit(orrs_reg, 3, 4); a.emit(str_imm, 3, 1, 12)            # pending[count] = N | k << 8
    a.emit(adds_imm8, 0, 1); a.emit(str_imm, 0, 7, 8)
    a.label("sv_next")
    a.emit(adds_imm8, 4, 1); a.emit(cmp_imm, 4, 64); bc("sv_scan", "lo")
    a.emit(mov_reg, 0, 7); a.emit(bl, "c_give")
    a.emit(movs_imm, 6, 0)
    a.label("sv_l")                                  # r6 = index in the pending list
    a.emit(ldr_imm, 0, 7, 8); a.emit(cmp_reg, 6, 0); bc("sv_out", "hs")
    a.emit(lsls_imm, 1, 6, 2); a.emit(adds_reg, 1, 1, 7); a.emit(ldr_imm, 4, 1, 12)          # r4 = N | k << 8
    a.emit(lsls_imm, 0, 4, 24); a.emit(lsrs_imm, 0, 0, 24); a.emit(mov_reg, 1, 7); a.emit(adds_imm8, 1, 44); a.emit(bl, "c_entry")
    a.emit(lsls_imm, 0, 4, 24); a.emit(lsrs_imm, 0, 0, 24); a.emit(ldr_imm, 1, 7, 48); a.emit(bl, "c_fits")
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "sv_skip", "eq")
    a.emit(lsls_imm, 0, 4, 24); a.emit(lsrs_imm, 0, 0, 24); a.emit(ldr_imm, 1, 7, 44); a.emit(ldr_imm, 2, 7, 48); a.emit(bl, "c_wav")
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "sv_skip", "ne")
    a.emit(mov_reg, 0, 7); a.emit(bl, "c_take")                                              # saved: bit k
    imm32(0, SAVED); a.emit(bl, "c_xr"); a.emit(lsrs_imm, 2, 4, 8); a.emit(movs_imm, 1, 1); a.emit(raw, h(0x4091)); a.emit(orrs_reg, 1, 0)
    imm32(0, SAVED); a.emit(bl, "c_xw")
    a.emit(mov_reg, 0, 7); a.emit(bl, "c_give")
    a.label("sv_skip")
    a.emit(adds_imm8, 6, 1); a.emit(b, "sv_l")
    a.label("sv_out")
    a.emit(add_sp_imm, 56); a.emit(raw, popw([0, 4, 5, 6, 7], lr=True))
    a.emit(b_w, L["c_pl_save"])

    # ---- c_swap (r0 = A, r1 = B): files and table entries of PCM A and B exchanged -> r0 = status
    # frame r7: [0..11] entry A [12..23] entry B [24] nA [28] nB [32] A [36] B
    a.label("c_swap")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(sub_sp_imm, 40); a.emit(mov_reg, 7, 13); a.emit(str_imm, 0, 7, 32); a.emit(str_imm, 1, 7, 36)
    a.emit(mov_reg, 1, 7); a.emit(bl, "c_entry")
    a.emit(ldr_imm, 0, 7, 36); a.emit(mov_reg, 1, 7); a.emit(adds_imm8, 1, 12); a.emit(bl, "c_entry")
    for i, (ent, nslot) in enumerate(((0, 24), (12, 28))):                                 # n = file samples (pack sample) or the table length (a capture slot)
        a.emit(ldr_imm, 0, 7, ent + 4); a.emit(str_imm, 0, 7, nslot)
        a.emit(ldr_imm, 0, 7, ent); imm32(1, SD.HIGH_BASE); a.emit(cmp_reg, 0, 1); a.emit(b_cond, f"sw_t{i}", "hs")
        a.emit(ldr_imm, 0, 7, 32 + 4 * i); a.emit(bl, "c_isize"); a.emit(cmp_imm, 0, 44); bc("sw_bad", "ls")
        a.emit(subs_imm8, 0, 44); a.emit(lsrs_imm, 0, 0, 1); a.emit(str_imm, 0, 7, nslot)
        a.label(f"sw_t{i}")
    a.emit(ldr_imm, 0, 7, 32); a.emit(ldr_imm, 1, 7, 12); a.emit(ldr_imm, 2, 7, 28); a.emit(bl, "c_wav")     # A := B's audio
    a.emit(cmp_imm, 0, 0); bc("sw_x", "ne")
    a.emit(ldr_imm, 0, 7, 36); a.emit(ldr_imm, 1, 7, 0); a.emit(ldr_imm, 2, 7, 24); a.emit(bl, "c_wav")      # B := A's audio
    a.emit(cmp_imm, 0, 0); bc("sw_x", "ne")
    a.emit(ldr_imm, 0, 7, 32); a.emit(mov_reg, 1, 7); a.emit(adds_imm8, 1, 12); a.emit(bl, "c_setentry")
    a.emit(ldr_imm, 0, 7, 36); a.emit(mov_reg, 1, 7); a.emit(bl, "c_setentry")
    a.emit(movs_imm, 0, 0); a.emit(b, "sw_x")
    a.label("sw_bad"); a.emit(movs_imm, 0, 8)
    a.label("sw_x"); a.emit(add_sp_imm, 40); a.emit(pop_list, [4, 5, 6, 7], pc=True)

    if CROSS:
        cross_code(a, L, imm32, bc)
    if EXACT:
        exact_code(a, imm32, bc)
    if PATCHX:
        patch_code(a, L, prev, imm32, bc)
    if DUPMASK:                                  # ---- c_hmask (the container's slot 8: view) -> the held buttons it accepts; + Duplicate in a synth / drum Preset view
        a.label("c_hmask")
        a.emit(push_list, [4], lr=True)
        a.emit(bl, CT_MASK & ~1); a.emit(mov_reg, 4, 0)
        imm32(1, MGR); a.emit(ldrb_w, 1, 1, 0x152)
        for v in DUP_SUBS:
            a.emit(cmp_imm, 1, v); a.emit(b_cond, "hm_d", "eq")
        a.emit(b, "hm_x")
        a.label("hm_d"); a.emit(movs_imm, 0, 2); a.emit(orrs_reg, 4, 0)
        a.label("hm_x"); a.emit(mov_reg, 0, 4); a.emit(pop_list, [4], pc=True)

    def held(rd):                                    # rd = the held buttons (bit 0 Clear, bit 1 Duplicate); clobbers r0-r3
        imm32(0, MGR); a.emit(ldr_imm, 0, 0, 0x20); a.emit(ldr_imm, 0, 0, 0xC); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET)
        a.emit(ldrb_imm, rd, 0, 0)

    # ---- c_pdp (drum Preset view slot 0: view, pad, vel), in front of drumrep's c_drp: Duplicate + A, B = swap
    a.label("c_pdp")
    a.emit(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1)
    a.emit(ldrb_w, 0, 4, 0x51); a.emit(movs_imm, 1, 1); a.emit(tst_reg, 0, 1); bc("dp_fwd", "ne")       # chromatic keyboard: not samples
    held(6); a.emit(movs_imm, 0, 2); a.emit(tst_reg, 6, 0); bc("dp_nod", "eq")
    a.emit(ldr_imm, 0, 4, 0x20); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 0, 0, 0)
    a.emit(lsls_imm, 0, 0, 5); a.emit(adds_reg, 5, 0, 5)                                       # r5 = N
    if CROSS:                                    # the clip: none -> copy (pack, N); same pack -> swap / cancel; another pack -> c_xswap
        a.emit(bl, "c_clip"); a.emit(mov_reg, 6, 0); a.emit(cmp_imm, 6, 0); bc("dx_has", "ne")
        a.emit(bl, "c_curpack"); a.emit(lsls_imm, 0, 0, 8); a.emit(orrs_reg, 0, 5); a.emit(movs_imm, 1, CLIP_MAGIC); a.emit(lsls_imm, 1, 1, 16); a.emit(orrs_reg, 0, 1)
        a.emit(bl, "c_setclip")
        a.emit(bl, "c_curpack"); a.emit(movs_imm, 1, MIR_P); a.emit(orrs_reg, 0, 1); a.emit(strb_w, 0, 4, SWAP_OFF)
        a.emit(movs_imm, 0, MIR_I); a.emit(orrs_reg, 0, 5); a.emit(strb_w, 0, 4, SWAP_OFF + 1); a.emit(b, "dp_eat")
        a.label("dx_has")                        # r6 = the clip: forget it first (a failed swap must not stay armed)
        a.emit(movs_imm, 0, 0); a.emit(bl, "c_setclip"); a.emit(movs_imm, 0, 0); a.emit(strb_w, 0, 4, SWAP_OFF)
        a.emit(bl, "c_curpack"); a.emit(lsrs_imm, 1, 6, 8); a.emit(movs_imm, 2, 0xFF); a.emit(ands_reg, 1, 2)          # r1 = its pack
        a.emit(lsls_imm, 6, 6, 24); a.emit(lsrs_imm, 6, 6, 24)                                                         # r6 = its sample
        a.emit(cmp_imm, 6, 64); bc("dp_eat", "hs")
        a.emit(cmp_reg, 1, 0); bc("dx_other", "ne")
        a.emit(cmp_reg, 6, 5); bc("dp_eat", "eq")                                                                     # A again: cancel
        if FIX2 and not EXACT: a.emit(bl, "c_resel")                                                                  # (r0 = the loaded pack)
        a.emit(mov_reg, 0, 6); a.emit(mov_reg, 1, 5); a.emit(bl, "c_swap2" if EXACT else "c_swap"); a.emit(b, "dp_eat")
        a.label("dx_other")
        a.emit(mov_reg, 0, 6); a.emit(mov_reg, 2, 5); a.emit(bl, "c_xcopy2" if COPYX else "c_xswap2" if EXACT else "c_xswap"); a.emit(b, "dp_eat")
    a.emit(ldrb_w, 6, 4, SWAP_OFF); a.emit(cmp_imm, 6, SWAP_MAGIC); a.emit(b_cond, "dp_has", "eq")
    a.emit(movs_imm, 0, SWAP_MAGIC); a.emit(strb_w, 0, 4, SWAP_OFF); a.emit(strb_w, 5, 4, SWAP_OFF + 1); a.emit(b, "dp_eat")   # A chosen
    a.label("dp_has")
    a.emit(movs_imm, 0, 0); a.emit(strb_w, 0, 4, SWAP_OFF)
    a.emit(ldrb_w, 6, 4, SWAP_OFF + 1); a.emit(cmp_imm, 6, 64); a.emit(b_cond, "dp_eat", "hs")   # (never out of range)
    a.emit(cmp_reg, 6, 5); a.emit(b_cond, "dp_eat", "eq")                                      # A again: cancel
    a.emit(mov_reg, 0, 6); a.emit(mov_reg, 1, 5); a.emit(bl, "c_swap")
    a.label("dp_eat")
    a.emit(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); a.emit(raw, h(0x4770))
    a.label("dp_nod")                                # Duplicate not held: a pending A is dropped (CROSS: the clip stays)
    if not CROSS: a.emit(movs_imm, 0, 0); a.emit(strb_w, 0, 4, SWAP_OFF)
    a.label("dp_fwd")
    a.emit(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); a.emit(b_w, prev["dp_pad"])

    def blink(on, off):                              # r0 = the colour of a blinking pad (4 Hz)
        imm32(0, HAL_TICK); a.emit(ldr_imm, 0, 0, 0); a.emit(lsrs_imm, 0, 0, 7); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 0, 1)
        zc[0] += 1; n = f"_bk{zc[0]}"
        a.emit(movs_imm, 1, off); a.emit(cmp_imm, 0, 0); a.emit(b_cond, n, "eq"); a.emit(movs_imm, 1, on); a.label(n); a.emit(mov_reg, 0, 1)

    # ---- c_pdl (drum Preset view slot 7): drumrep's LEDs, then A blinks blue (on its page) while Duplicate is held
    a.label("c_pdl")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(bl, prev["dp_leds"]); a.emit(mov_reg, 5, 0)                 # r5 = LED buffer
    if CROSS:                                    # the mirror of the clip, while Duplicate is held: blue in its pack, magenta in another one
        a.emit(ldrb_w, 6, 4, SWAP_OFF); a.emit(movs_imm, 0, MIR_P); a.emit(ands_reg, 0, 6); a.emit(cmp_imm, 0, MIR_P); bc("dl_x", "ne")
        a.emit(ldrb_w, 7, 4, SWAP_OFF + 1); a.emit(movs_imm, 0, 0xC0); a.emit(ands_reg, 0, 7); a.emit(cmp_imm, 0, MIR_I); bc("dl_x", "ne")
        held(0); a.emit(movs_imm, 1, 2); a.emit(tst_reg, 0, 1); bc("dl_x", "eq")
        a.emit(ldr_imm, 0, 4, 0x20); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 0, 0, 0)
        a.emit(lsls_imm, 1, 7, 26); a.emit(lsrs_imm, 1, 1, 31); a.emit(cmp_reg, 1, 0); bc("dl_x", "ne")              # bit 5 = the page
        a.emit(bl, "c_curpack"); a.emit(lsls_imm, 6, 6, 26); a.emit(lsrs_imm, 6, 6, 26)
        a.emit(movs_imm, 1, BLUE); a.emit(cmp_reg, 6, 0); a.emit(b_cond, "dl_c", "eq"); a.emit(movs_imm, 1, CROSS_COL)
        a.label("dl_c"); a.emit(mov_reg, 6, 1)
        imm32(0, HAL_TICK); a.emit(ldr_imm, 0, 0, 0); a.emit(lsrs_imm, 0, 0, 7); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 0, 1)
        a.emit(cmp_imm, 0, 0); a.emit(b_cond, "dl_d", "ne"); a.emit(movs_imm, 6, DARK)
        a.label("dl_d")
        a.emit(lsls_imm, 7, 7, 27); a.emit(lsrs_imm, 7, 7, 26); a.emit(strh_reg, 6, 5, 7)                              # 2 x (A % 32)
        a.emit(b, "dl_x")
    a.emit(ldrb_w, 6, 4, SWAP_OFF); a.emit(cmp_imm, 6, SWAP_MAGIC); bc("dl_x", "ne")
    held(7); a.emit(movs_imm, 0, 2); a.emit(tst_reg, 7, 0); a.emit(b_cond, "dl_held", "ne")
    a.emit(movs_imm, 0, 0); a.emit(strb_w, 0, 4, SWAP_OFF); a.emit(b, "dl_x")
    a.label("dl_held")
    a.emit(ldr_imm, 0, 4, 0x20); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 0, 0, 0)
    a.emit(ldrb_w, 6, 4, SWAP_OFF + 1); a.emit(lsrs_imm, 1, 6, 5); a.emit(cmp_reg, 1, 0); bc("dl_x", "ne")    # another page
    a.emit(lsls_imm, 6, 6, 27); a.emit(lsrs_imm, 6, 6, 26)                                      # 2 x (A % 32)
    blink(BLUE, DARK); a.emit(strh_reg, 0, 5, 6)
    a.label("dl_x"); a.emit(mov_reg, 0, 5); a.emit(pop_list, [4, 5, 6, 7], pc=True)

    def pv_active(fail):                         # r4 = the active view when it is the packs view, else -> fail
        imm32(0, MGR); a.emit(ldr_imm, 4, 0, 0x6C); a.emit(ldr_imm, 0, 4, 0); imm32(1, PV_VT); a.emit(cmp_reg, 0, 1); bc(fail, "ne")

    def fresh(fail):                             # the question of the packs view r4: magic and asked less than PQ_LIFE ago, else -> fail (clobbers r0-r2)
        a.emit(ldrb_w, 0, 4, PQ_OFF); a.emit(cmp_imm, 0, PQ_MAGIC); bc(fail, "ne")
        imm32(0, HAL_TICK); a.emit(ldr_imm, 0, 0, 0); a.emit(lsrs_imm, 0, 0, 8); a.emit(ldrb_w, 1, 4, PQ_OFF + 2)
        a.emit(subs_reg, 0, 0, 1); a.emit(lsls_imm, 0, 0, 24); a.emit(lsrs_imm, 0, 0, 24); a.emit(cmp_imm, 0, PQ_LIFE); bc(fail, "hi")

    # ---- c_ppk (packs view slot 0: view, pad, vel): Clear held (no Shift: Shift + Clear = the metronome) + a pad = that pack asked
    a.label("c_ppk")
    a.emit(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1)
    held(6); a.emit(movs_imm, 0, 1); a.emit(tst_reg, 6, 0); bc("pk_clr", "eq")
    a.emit(bl, L["c_shift"]); a.emit(cmp_imm, 0, 0); bc("pk_clr", "ne")
    a.emit(ldr_imm, 0, 4, 0x10); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 6, 0, 0)   # the current pack: never
    a.emit(cmp_reg, 5, 6); bc("pk_eat", "eq")
    a.emit(movs_imm, 0, PQ_MAGIC); a.emit(strb_w, 0, 4, PQ_OFF); a.emit(strb_w, 5, 4, PQ_OFF + 1)
    imm32(0, HAL_TICK); a.emit(ldr_imm, 0, 0, 0); a.emit(lsrs_imm, 0, 0, 8); a.emit(strb_w, 0, 4, PQ_OFF + 2)   # asked at (ms >> 8)
    a.label("pk_eat")
    a.emit(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); a.emit(raw, h(0x4770))
    a.label("pk_clr")                                # a pad without Clear: no question, stock
    if FIX2:                                     # armed / asked and fresh: this pad becomes the asked pack (never the loaded one); not loaded
        a.emit(bl, L["c_shift"]); a.emit(cmp_imm, 0, 0); bc("pk_stk", "ne")                    # (Shift + pad: the stock's)
        fresh("pk_stk")
        a.emit(ldr_imm, 0, 4, 0x10); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 6, 0, 0)
        a.emit(cmp_reg, 5, 6); bc("pk_eat", "eq")
        a.emit(strb_w, 5, 4, PQ_OFF + 1)
        imm32(0, HAL_TICK); a.emit(ldr_imm, 0, 0, 0); a.emit(lsrs_imm, 0, 0, 8); a.emit(strb_w, 0, 4, PQ_OFF + 2)
        a.emit(b, "pk_eat")
        a.label("pk_stk")
    a.emit(movs_imm, 0, 0); a.emit(strb_w, 0, 4, PQ_OFF)
    a.emit(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); a.emit(b_w, PV_PAD & ~1)

    # ---- c_mbp (held-buttons object slot 2: obj, id = 23 Clear / 24 Duplicate pressed): the stock first, then Clear confirms a fresh question
    a.label("c_mbp")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 5, 1); a.emit(bl, MB_PRESS & ~1)
    a.emit(cmp_imm, 5, 23); bc("mp_x", "ne")
    a.emit(bl, L["c_shift"]); a.emit(cmp_imm, 0, 0); bc("mp_x", "ne")
    if FIX2:
        pv_active("mp_x"); fresh("mp_arm")
        a.emit(ldrb_w, 5, 4, PQ_OFF + 1); a.emit(cmp_imm, 5, 32); a.emit(b_cond, "mp_ask", "lo")
        a.label("mp_arm")                            # Clear: armed for ~5 s
        a.emit(movs_imm, 0, PQ_MAGIC); a.emit(strb_w, 0, 4, PQ_OFF); a.emit(movs_imm, 0, PQ_ARMED); a.emit(strb_w, 0, 4, PQ_OFF + 1)
        imm32(0, HAL_TICK); a.emit(ldr_imm, 0, 0, 0); a.emit(lsrs_imm, 0, 0, 8); a.emit(strb_w, 0, 4, PQ_OFF + 2)
        a.emit(b, "mp_x")
        a.label("mp_ask")
        a.emit(movs_imm, 0, 0); a.emit(strb_w, 0, 4, PQ_OFF)
    else:
        pv_active("mp_x"); fresh("mp_x")
        a.emit(ldrb_w, 5, 4, PQ_OFF + 1); a.emit(movs_imm, 0, 0); a.emit(strb_w, 0, 4, PQ_OFF)     # r5 = the pack; the question is used
    a.emit(ldr_imm, 0, 4, 0x10); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 6, 0, 0)   # r6 = the current pack
    a.emit(cmp_reg, 5, 6); bc("mp_x", "eq")
    a.emit(sub_sp_imm, 16)
    a.emit(movs_imm, 0, 1); a.emit(raw, h(0x9000)); a.emit(movs_imm, 0, 0); a.emit(subs_imm8, 0, 1); a.emit(raw, h(0x9001))   # {1, -1,
    a.emit(raw, h(0x9502))                                                                       #  pack r5}
    a.emit(mov_reg, 0, 13); a.emit(movs_imm, 1, 0); a.emit(movs_imm, 2, 0); a.emit(bl, DEL_FN)
    a.emit(movs_imm, 0, KIND_PCM); a.emit(raw, h(0x9000)); a.emit(movs_imm, 0, 0); a.emit(raw, h(0x9001)); a.emit(raw, h(0x9602))   # re-select the current pack
    a.emit(mov_reg, 0, 13); a.emit(bl, EXISTS)
    a.emit(add_sp_imm, 16)
    a.label("mp_x"); a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_mbl (held-buttons object slot 8: its LEDs): the stock first; in the packs view Clear is dim white, blinking red with a fresh question
    a.label("c_mbl")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 5, 0); a.emit(bl, MB_LEDS & ~1)
    pv_active("ml_x")
    a.emit(ldr_imm, 0, 5, 4); a.emit(ldr_imm, 6, 0, 0)                                         # r6 = [[obj + 4]]: entry 0 = Clear
    a.emit(movs_imm, 7, CLR_DIM); fresh("ml_put")
    blink(RED, DARK); a.emit(mov_reg, 7, 0)
    a.label("ml_put"); a.emit(strh_imm, 7, 6, 0)
    a.label("ml_x"); a.emit(pop_list, [4, 5, 6, 7], pc=True)

    if PKLED:                                    # ---- c_pkled (the LED task calls: ctrl, frame): c_vledtask, then the Clear LED in the packs view
        a.label("c_pkled")
        a.emit(push_list, [4, 5, 6, 7], lr=True)
        a.emit(mov_reg, 5, 1); a.emit(bl, L["c_vledtask"])
        pv_active("pkl_x")
        a.emit(movs_imm, 7, CLR_ON if PKLED3 else CLR_DIM); fresh("pkl_put")
        if PKLED3: a.label("pk3_l")
        if PKLED2:                               # the question: Clear steady white; the pads blink on the frame (the view's buffer stays the stock's)
            blink(RED, DARK); a.emit(mov_reg, 6, 0)                                                # r6 = the blink colour
            a.emit(ldrb_w, 7, 4, PQ_OFF + 1); a.emit(cmp_imm, 7, PQ_ARMED); a.emit(b_cond, "pk2_one", "ne")
            a.emit(ldr_imm, 0, 4, 0x10); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 7, 0, 0)    # r7 = the loaded pack
            a.emit(movs_imm, 3, 0)
            a.label("pk2_l")
            a.emit(cmp_reg, 3, 7); a.emit(b_cond, "pk2_n", "eq")
            a.emit(lsls_imm, 1, 3, 1); a.emit(ldrh_reg, 2, 5, 1); a.emit(cmp_imm, 2, 0); a.emit(b_cond, "pk2_n", "eq")   # an empty slot stays dark
            a.emit(strh_reg, 6, 5, 1)
            a.label("pk2_n")
            a.emit(adds_imm8, 3, 1); a.emit(cmp_imm, 3, 32); a.emit(b_cond, "pk2_l", "lo")
            a.emit(b, "pk2_c")
            a.label("pk2_one")
            a.emit(cmp_imm, 7, 32); a.emit(b_cond, "pk2_c", "hs"); a.emit(lsls_imm, 1, 7, 1); a.emit(strh_reg, 6, 5, 1)
            a.label("pk2_c")
            a.emit(movs_imm, 7, CLR_ON)
        else:
            blink(RED, DARK); a.emit(mov_reg, 7, 0)
        a.label("pkl_put"); a.emit(movw, 1, 2 * LED_CLEAR); a.emit(strh_reg, 7, 5, 1)
        a.label("pkl_x"); a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_ppl (packs view slot 7): the LED buffer; the asked pad blinks red while the question is fresh
    a.label("c_ppl")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(ldr_imm, 0, 0, 4); a.emit(ldr_imm, 5, 0, 0)                 # r5 = [[view + 4]]
    if PKLED2: a.emit(b, "pl_x")                 # (drawn on the frame by c_pkled)
    fresh("pl_x")
    if FIX2:
        a.emit(ldrb_w, 6, 4, PQ_OFF + 1); a.emit(cmp_imm, 6, PQ_ARMED); bc("pl_one", "ne")
        a.emit(ldr_imm, 0, 4, 0x10); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 7, 0, 0)    # r7 = the loaded pack
        blink(RED, DARK); a.emit(mov_reg, 6, 0); a.emit(movs_imm, 3, 0)                       # r6 = the colour, r3 = pad
        a.label("pl_al")
        a.emit(cmp_reg, 3, 7); a.emit(b_cond, "pl_an", "eq")
        a.emit(lsls_imm, 1, 3, 1); a.emit(ldrh_reg, 2, 5, 1); a.emit(cmp_imm, 2, 0); a.emit(b_cond, "pl_an", "eq")   # an empty slot stays dark
        a.emit(strh_reg, 6, 5, 1)
        a.label("pl_an")
        a.emit(adds_imm8, 3, 1); a.emit(cmp_imm, 3, 32); a.emit(b_cond, "pl_al", "lo")
        a.emit(b, "pl_x")
        a.label("pl_one")
    a.emit(ldrb_w, 6, 4, PQ_OFF + 1); a.emit(cmp_imm, 6, 32); bc("pl_x", "hs"); a.emit(lsls_imm, 6, 6, 1)
    blink(RED, DARK); a.emit(strh_reg, 0, 5, 6)
    a.label("pl_x"); a.emit(mov_reg, 0, 5); a.emit(pop_list, [4, 5, 6, 7], pc=True)
    return a.assemble()


def cross_code(a, L, imm32, bc):
    """c_curpack, c_clip / c_setclip (the clip word X:CLIPW), c_ywin (host writes to Y:WIN), c_xswap."""
    a.label("c_curpack")                         # r0 = the current pack (API numbering)
    if FIX2:                                     # the loaded pack: the packs view's p0 of [+0x10] (clobbers r1-r3)
        a.emit(push_list, [4], lr=True)
        imm32(4, PV_OBJ); a.emit(ldr_imm, 0, 4, 0); imm32(1, PV_VT); a.emit(cmp_reg, 0, 1); a.emit(b_cond, "cp_ff", "ne")
        a.emit(ldr_imm, 0, 4, 0x10); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 0, 0, 0); a.emit(pop_list, [4], pc=True)
        a.label("cp_ff")
        imm32(0, CUR_PACK_PTR); a.emit(ldr_imm, 0, 0, 0); a.emit(ldrb_imm, 0, 0, 0); a.emit(pop_list, [4], pc=True)
        a.label("c_resel")                       # (r0 = pack): the storage task's current pack := that one (op 0 on its PCM 0)
        a.emit(push_list, [4], lr=True); a.emit(sub_sp_imm, 16)
        a.emit(raw, h(0x9002)); a.emit(movs_imm, 0, KIND_PCM); a.emit(raw, h(0x9000)); a.emit(movs_imm, 0, 0); a.emit(raw, h(0x9001))
        a.emit(mov_reg, 0, 13); a.emit(bl, EXISTS); a.emit(add_sp_imm, 16); a.emit(pop_list, [4], pc=True)
    else:
        imm32(0, CUR_PACK_PTR); a.emit(ldr_imm, 0, 0, 0); a.emit(ldrb_imm, 0, 0, 0); a.emit(raw, h(0x4770))
    a.label("c_clip")                            # r0 = the clip word (MAGIC << 16 | pack << 8 | sample), 0 = none
    a.emit(push_list, [4], lr=True); a.emit(sub_sp_imm, 8)
    a.emit(mov_reg, 0, 13); a.emit(bl, "c_take"); imm32(0, SD.CLIPW); a.emit(bl, "c_xr"); a.emit(mov_reg, 4, 0)
    a.emit(mov_reg, 0, 13); a.emit(bl, "c_give")
    a.emit(lsrs_imm, 0, 4, 16); a.emit(cmp_imm, 0, CLIP_MAGIC); a.emit(b_cond, "cl_ok", "eq"); a.emit(movs_imm, 4, 0)
    a.label("cl_ok"); a.emit(mov_reg, 0, 4); a.emit(add_sp_imm, 8); a.emit(pop_list, [4], pc=True)
    a.label("c_setclip")                         # X:CLIPW = r0
    a.emit(push_list, [4], lr=True); a.emit(sub_sp_imm, 8); a.emit(mov_reg, 4, 0)
    a.emit(mov_reg, 0, 13); a.emit(bl, "c_take"); imm32(0, SD.CLIPW); a.emit(mov_reg, 1, 4); a.emit(bl, "c_xw")
    a.emit(mov_reg, 0, 13); a.emit(bl, "c_give"); a.emit(add_sp_imm, 8); a.emit(pop_list, [4], pc=True)
    a.label("c_ywin")                            # (r0 = 16-bit samples, r1 = n <= NW): Y:WIN + k = sample k << 8; the semaphore taken by the caller
    a.emit(push_list, [4, 5, 6], lr=True); a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); a.emit(movs_imm, 6, 0)
    a.label("yw_l")
    a.emit(cmp_reg, 6, 5); a.emit(b_cond, "yw_x", "hs")
    a.emit(lsls_imm, 2, 6, 1); a.emit(ldrh_reg, 1, 4, 2); a.emit(lsls_imm, 1, 1, 16)
    imm32(2, 0x8000 | WIN); a.emit(adds_reg, 2, 2, 6); a.emit(movs_imm, 0, 0); a.emit(bl, DSP_WRITE)
    a.emit(adds_imm8, 6, 1); a.emit(b, "yw_l")
    a.label("yw_x"); a.emit(pop_list, [4, 5, 6], pc=True)

    # ---- c_xswap (r0 = A, r1 = pack X, r2 = B): A of pack X <-> B of the current pack -> r0 = status (0 = done)
    # frame r7: [0] cb [4] ctx [8] &done [12] done [16..27] item X:A [28..39] item B [40] size X:A [44] offset [48] piece [52] status
    #           [56..67] entry B [68] n of B [72] destination [76] k [80] n of X:A [84] holder [88] pos
    F = 96 if FIX2 else 92
    a.label("c_xswap")
    a.emit(push_list, [4, 5, 6, 7], lr=True); a.emit(sub_sp_imm, F); a.emit(mov_reg, 7, 13)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 6, 2)
    a.emit(movs_imm, 3, 0)
    for o in range(0, F, 4): a.emit(str_imm, 3, 7, o)
    if FIX2: a.emit(bl, "c_curpack"); a.emit(str_imm, 0, 7, 92)                                 # [92] = the loaded pack
    a.emit(movs_imm, 3, KIND_PCM); a.emit(str_imm, 3, 7, 16); a.emit(str_imm, 4, 7, 20); a.emit(strb_imm, 5, 7, 24)
    a.emit(str_imm, 3, 7, 28); a.emit(str_imm, 6, 7, 32)
    if FIX2: a.emit(ldr_imm, 3, 7, 92); a.emit(strb_w, 3, 7, 36)                                # B: the loaded pack by its number
    else: a.emit(movs_imm, 3, 0xFF); a.emit(strb_w, 3, 7, 36)
    a.emit(movs_imm, 0, 8); a.emit(str_imm, 0, 7, 52)                                       # status 8 until it works
    a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, 16); a.emit(bl, SIZE); a.emit(str_imm, 0, 7, 40)
    a.emit(cmp_imm, 0, 44); bc("xs_x", "ls")
    a.emit(subs_imm8, 0, 44); a.emit(lsrs_imm, 0, 0, 1); a.emit(str_imm, 0, 7, 80)
    a.emit(mov_reg, 0, 6); a.emit(mov_reg, 1, 7); a.emit(adds_imm8, 1, 56); a.emit(bl, "c_entry")   # B: its entry and its length
    a.emit(ldr_imm, 0, 7, 60); a.emit(str_imm, 0, 7, 68)
    a.emit(ldr_imm, 0, 7, 56); imm32(1, SD.HIGH_BASE); a.emit(cmp_reg, 0, 1); a.emit(b_cond, "xs_nb", "hs")
    a.emit(mov_reg, 0, 6)
    if FIX2: a.emit(ldr_imm, 1, 7, 92); a.emit(bl, "c_isizep")
    else: a.emit(bl, "c_isize")
    a.emit(cmp_imm, 0, 44); bc("xs_x", "ls")
    a.emit(subs_imm8, 0, 44); a.emit(lsrs_imm, 0, 0, 1); a.emit(str_imm, 0, 7, 68)
    a.label("xs_nb")
    a.emit(movs_imm, 0, 10); a.emit(str_imm, 0, 7, 52)                                      # 10: does not fit
    a.emit(mov_reg, 0, 6); a.emit(ldr_imm, 1, 7, 80)
    if FIX2: a.emit(ldr_imm, 2, 7, 92); a.emit(bl, "c_fitsp")
    else: a.emit(bl, "c_fits")
    a.emit(cmp_imm, 0, 0); bc("xs_x", "eq")
    a.emit(mov_reg, 0, 4); a.emit(ldr_imm, 1, 7, 68); a.emit(mov_reg, 2, 5); a.emit(bl, "c_fitsp"); a.emit(cmp_imm, 0, 0); bc("xs_x", "eq")
    # 1. the file X:A -> B of the current pack, in 4 KB pieces
    a.emit(movs_imm, 0, 5); a.emit(bl, BUF_LOCK)
    a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, 28); a.emit(movs_imm, 1, 0); a.emit(movs_imm, 2, 0); a.emit(bl, DEL_FN)
    a.label("xs_cp")
    a.emit(ldr_imm, 0, 7, 40); a.emit(ldr_imm, 1, 7, 44); a.emit(subs_reg, 0, 0, 1); bc("xs_cpd", "eq")
    imm32(1, BUFSZ); a.emit(cmp_reg, 0, 1); a.emit(b_cond, "xs_pc", "ls"); a.emit(mov_reg, 0, 1)
    a.label("xs_pc"); a.emit(str_imm, 0, 7, 48)
    a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, 12); a.emit(str_imm, 0, 7, 8)              # &done
    a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, 16); a.emit(ldr_imm, 1, 7, 44); imm32(2, BUF); a.emit(ldr_imm, 3, 7, 48); a.emit(bl, READ)
    a.emit(movs_imm, 1, 0); a.emit(str_imm, 1, 7, 8)
    a.emit(cmp_imm, 0, 0); bc("xs_fail", "ne")
    a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, 28); a.emit(ldr_imm, 1, 7, 44); imm32(2, BUF); a.emit(ldr_imm, 3, 7, 48); a.emit(bl, WRITE)
    a.emit(cmp_imm, 0, 0); bc("xs_fail", "ne")
    a.emit(ldr_imm, 0, 7, 44); a.emit(ldr_imm, 1, 7, 48); a.emit(adds_reg, 0, 0, 1); a.emit(str_imm, 0, 7, 44); a.emit(b, "xs_cp")
    a.label("xs_fail"); a.emit(str_imm, 0, 7, 52); a.emit(bl, BUF_UNLOCK)
    if FIX2:                                     # B was deleted: written back from the DSP's memory, then the storage task back on the loaded pack
        a.emit(ldr_imm, 0, 7, 32); a.emit(ldr_imm, 1, 7, 56); a.emit(ldr_imm, 2, 7, 68); a.emit(ldr_imm, 3, 7, 92); a.emit(bl, "c_wavp")
        a.emit(b, "xs_sel")
    else: a.emit(b, "xs_x")
    a.label("xs_cpd"); a.emit(bl, BUF_UNLOCK)
    # 2. B's audio (still in the DSP's memory) -> sample A of pack X
    a.emit(mov_reg, 0, 4); a.emit(ldr_imm, 1, 7, 56); a.emit(ldr_imm, 2, 7, 68); a.emit(mov_reg, 3, 5); a.emit(bl, "c_wavp")
    a.emit(str_imm, 0, 7, 52); a.emit(cmp_imm, 0, 0); bc("xs_x", "ne")
    # 3. the new B into the free external memory, and its table entry -> there (a header that is not a plain 44-byte mono 16-bit WAV: skipped)
    a.emit(movs_imm, 0, 0); a.emit(str_imm, 0, 7, 44)
    a.emit(movs_imm, 0, 5); a.emit(bl, BUF_LOCK)
    a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, 12); a.emit(str_imm, 0, 7, 8)
    a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, 28); a.emit(movs_imm, 1, 0); imm32(2, BUF); a.emit(movs_imm, 3, 44); a.emit(bl, READ)
    a.emit(movs_imm, 1, 0); a.emit(str_imm, 1, 7, 8)
    a.emit(cmp_imm, 0, 0); bc("xs_nolive", "ne")
    imm32(2, BUF)
    for off, v in ((0, 0x46464952), (8, 0x45564157), (36, 0x61746164)):                      # RIFF, WAVE, data
        a.emit(ldr_imm, 0, 2, off); imm32(1, v); a.emit(cmp_reg, 0, 1); bc("xs_nolive", "ne")
    a.emit(ldr_imm, 0, 2, 20); imm32(1, 0x00010001); a.emit(cmp_reg, 0, 1); bc("xs_nolive", "ne")    # PCM, mono
    a.emit(ldr_imm, 0, 2, 32); a.emit(lsrs_imm, 0, 0, 16); a.emit(cmp_imm, 0, 16); bc("xs_nolive", "ne")   # 16 bits
    a.emit(ldr_imm, 0, 7, 80); imm32(1, IMP_HI - IMP_LO); a.emit(cmp_reg, 0, 1); bc("xs_nolive", "hs")
    a.emit(cmp_imm, 0, 4); bc("xs_nolive", "lo")
    a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, 84); a.emit(bl, "c_take"); imm32(0, SD.IMPW); a.emit(bl, "c_xr"); a.emit(mov_reg, 3, 0)
    a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, 84); a.emit(bl, "c_give")
    imm32(1, IMP_LO); a.emit(cmp_reg, 3, 1); a.emit(b_cond, "xs_lo", "hs"); a.emit(mov_reg, 3, 1)
    a.label("xs_lo")
    a.emit(ldr_imm, 0, 7, 80); a.emit(adds_reg, 0, 0, 3); imm32(2, IMP_HI); a.emit(cmp_reg, 0, 2); a.emit(b_cond, "xs_fit", "ls"); a.emit(mov_reg, 3, 1)
    a.label("xs_fit"); a.emit(str_imm, 3, 7, 72)                                             # destination
    a.emit(movs_imm, 0, 44); a.emit(str_imm, 0, 7, 44); a.emit(movs_imm, 0, 0); a.emit(str_imm, 0, 7, 76)
    a.label("xs_ld")                             # read up to 4 KB of B's samples (from offset 44), then 64 at a time to the DSP
    a.emit(ldr_imm, 0, 7, 80); a.emit(ldr_imm, 1, 7, 76); a.emit(subs_reg, 0, 0, 1); bc("xs_ldd", "eq")
    a.emit(lsls_imm, 0, 0, 1); imm32(1, BUFSZ); a.emit(cmp_reg, 0, 1); a.emit(b_cond, "xs_lp", "ls"); a.emit(mov_reg, 0, 1)
    a.label("xs_lp"); a.emit(str_imm, 0, 7, 48)
    a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, 12); a.emit(str_imm, 0, 7, 8)
    a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, 28); a.emit(ldr_imm, 1, 7, 44); imm32(2, BUF); a.emit(ldr_imm, 3, 7, 48); a.emit(bl, READ)
    a.emit(movs_imm, 1, 0); a.emit(str_imm, 1, 7, 8)
    a.emit(cmp_imm, 0, 0); bc("xs_nolive", "ne")
    a.emit(movs_imm, 0, 0); a.emit(str_imm, 0, 7, 88)                                       # pos = bytes of the piece sent
    a.label("xs_w")
    a.emit(ldr_imm, 0, 7, 48); a.emit(ldr_imm, 1, 7, 88); a.emit(subs_reg, 0, 0, 1); bc("xs_wd", "eq")
    a.emit(lsrs_imm, 0, 0, 1); a.emit(cmp_imm, 0, NW); a.emit(b_cond, "xs_wn", "ls"); a.emit(movs_imm, 0, NW)
    a.label("xs_wn"); a.emit(mov_reg, 6, 0)                                                 # r6 = n of this copy (B's index lives in the frame from now on)
    a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, 84); a.emit(bl, "c_take")
    imm32(0, BUF); a.emit(ldr_imm, 1, 7, 88); a.emit(adds_reg, 0, 0, 1); a.emit(mov_reg, 1, 6); a.emit(bl, "c_ywin")
    a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, 84); a.emit(bl, "c_give")
    imm32(0, WIN); a.emit(ldr_imm, 1, 7, 72); a.emit(ldr_imm, 2, 7, 76); a.emit(adds_reg, 1, 1, 2); a.emit(mov_reg, 2, 6); a.emit(bl, "c_copy2")
    a.emit(cmp_imm, 0, 0); bc("xs_nolive", "ne")
    a.emit(ldr_imm, 0, 7, 76); a.emit(adds_reg, 0, 0, 6); a.emit(str_imm, 0, 7, 76)
    a.emit(ldr_imm, 0, 7, 88); a.emit(adds_reg, 0, 0, 6); a.emit(adds_reg, 0, 0, 6); a.emit(str_imm, 0, 7, 88)
    a.emit(b, "xs_w")
    a.label("xs_wd")
    a.emit(ldr_imm, 0, 7, 44); a.emit(ldr_imm, 1, 7, 48); a.emit(adds_reg, 0, 0, 1); a.emit(str_imm, 0, 7, 44); a.emit(b, "xs_ld")
    a.label("xs_ldd")                            # loaded: entry B = (destination, n - 2, its increment); X:IMPW = after it
    a.emit(bl, BUF_UNLOCK)
    a.emit(ldr_imm, 0, 7, 72); a.emit(str_imm, 0, 7, 56); a.emit(ldr_imm, 1, 7, 80); a.emit(subs_imm8, 1, 2); a.emit(str_imm, 1, 7, 60)
    a.emit(ldr_imm, 0, 7, 32); a.emit(mov_reg, 1, 7); a.emit(adds_imm8, 1, 56); a.emit(bl, "c_setentry")
    a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, 84); a.emit(bl, "c_take")
    imm32(0, SD.IMPW); a.emit(ldr_imm, 1, 7, 72); a.emit(ldr_imm, 2, 7, 80); a.emit(adds_reg, 1, 1, 2); a.emit(bl, "c_xw")
    a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, 84); a.emit(bl, "c_give")
    a.emit(movs_imm, 0, 0); a.emit(str_imm, 0, 7, 52); a.emit(b, "xs_sel")
    a.label("xs_nolive")                         # swapped on the card; the new B sounds after the pack is loaded again
    a.emit(bl, BUF_UNLOCK); a.emit(movs_imm, 0, 1); a.emit(str_imm, 0, 7, 52)
    a.label("xs_sel")                            # the current pack selected again in the storage task (op 0 on its PCM 0)
    if FIX2:
        a.emit(ldr_imm, 0, 7, 92); a.emit(bl, "c_resel")
    else:
        a.emit(bl, "c_curpack"); a.emit(sub_sp_imm, 16)
        a.emit(raw, h(0x9002)); a.emit(movs_imm, 0, KIND_PCM); a.emit(raw, h(0x9000)); a.emit(movs_imm, 0, 0); a.emit(raw, h(0x9001))   # [8] pack, [0] kind, [4] 0
        a.emit(mov_reg, 0, 13); a.emit(bl, EXISTS); a.emit(add_sp_imm, 16)
    a.label("xs_x")
    if FIX2:                                     # (any early exit after reading pack X: the storage task back on the loaded pack)
        a.emit(ldr_imm, 0, 7, 92); a.emit(bl, "c_resel")
    a.emit(ldr_imm, 0, 7, 52); a.emit(add_sp_imm, F); a.emit(pop_list, [4, 5, 6, 7], pc=True)


def exact_code(a, imm32, bc):
    """c_f2d, c_d2f, c_f2f, c_zpad, c_impdst, c_xswap2, c_swap2 (see 7.)."""
    def zero_frame(F):
        a.emit(movs_imm, 3, 0)
        for o in range(0, F, 4): a.emit(str_imm, 3, 7, o)
    def take(o): a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, o); a.emit(bl, "c_take")
    def give(o): a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, o); a.emit(bl, "c_give")
    def piece(size_o, off_o, piece_o, done_label):           # [piece] = min(4 KB, size - off); -> done_label when nothing is left
        a.emit(ldr_imm, 0, 7, size_o); a.emit(ldr_imm, 1, 7, off_o); a.emit(cmp_reg, 1, 0); bc(done_label, "hs"); a.emit(subs_reg, 0, 0, 1)
        imm32(1, BUFSZ); a.emit(cmp_reg, 0, 1); zl = f"_pc{piece.n}"; piece.n += 1
        a.emit(b_cond, zl, "ls"); a.emit(mov_reg, 0, 1); a.label(zl); a.emit(str_imm, 0, 7, piece_o)
    piece.n = 0
    def rd(item_o, off_o, piece_o, fail):                    # READ(frame[item_o] item ptr, off, BUF, piece) with &done = frame + 12
        a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, 12); a.emit(str_imm, 0, 7, 8)
        a.emit(ldr_imm, 0, 7, item_o); a.emit(ldr_imm, 1, 7, off_o); imm32(2, BUF); a.emit(ldr_imm, 3, 7, piece_o); a.emit(bl, READ)
        a.emit(movs_imm, 1, 0); a.emit(str_imm, 1, 7, 8); a.emit(cmp_imm, 0, 0); bc(fail, "ne")
    def wr(item_o, off_o, piece_o, fail):
        a.emit(ldr_imm, 0, 7, item_o); a.emit(ldr_imm, 1, 7, off_o); imm32(2, BUF); a.emit(ldr_imm, 3, 7, piece_o); a.emit(bl, WRITE)
        a.emit(cmp_imm, 0, 0); bc(fail, "ne")
    def ret_status(F, regs_extra=False):
        a.emit(add_sp_imm, F); a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_f2d (r0 = item ptr, r1 = size, r2 = Y destination) -> r0 = status, r1 = 1 if a plain 44-byte mono 16-bit WAV
    # frame: [0] cb [4] ctx [8] &done [12] done [16] item [20] size [24] dst [28] off [32] piece [36] pos [40] holder [44] plain [48] status
    F = 52
    a.label("c_f2d")
    a.emit(push_list, [4, 5, 6, 7], lr=True); a.emit(sub_sp_imm, F); a.emit(mov_reg, 7, 13)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 6, 2); zero_frame(F)
    a.emit(str_imm, 4, 7, 16); a.emit(str_imm, 5, 7, 20); a.emit(str_imm, 6, 7, 24); a.emit(movs_imm, 0, 9); a.emit(str_imm, 0, 7, 48)
    a.emit(movs_imm, 0, 5); a.emit(bl, BUF_LOCK)
    a.label("fd_l")
    piece(20, 28, 32, "fd_ok")
    rd(16, 28, 32, "fd_fail")
    a.emit(ldr_imm, 0, 7, 28); a.emit(cmp_imm, 0, 0); bc("fd_nh", "ne")                       # the header, on the first piece
    imm32(2, BUF)
    for off, v in ((0, 0x46464952), (8, 0x45564157), (36, 0x61746164), (20, 0x00010001)):
        a.emit(ldr_imm, 0, 2, off); imm32(1, v); a.emit(cmp_reg, 0, 1); bc("fd_nh", "ne")
    a.emit(ldr_imm, 0, 2, 32); a.emit(lsrs_imm, 0, 0, 16); a.emit(cmp_imm, 0, 16); bc("fd_nh", "ne")
    a.emit(movs_imm, 0, 1); a.emit(str_imm, 0, 7, 44)
    a.label("fd_nh")
    a.emit(movs_imm, 0, 0); a.emit(str_imm, 0, 7, 36)
    a.label("fd_w")
    a.emit(ldr_imm, 0, 7, 32); a.emit(ldr_imm, 1, 7, 36); a.emit(cmp_reg, 1, 0); bc("fd_wd", "hs")
    a.emit(subs_reg, 0, 0, 1); a.emit(adds_imm8, 0, 1); a.emit(lsrs_imm, 0, 0, 1); a.emit(cmp_imm, 0, NW); a.emit(b_cond, "fd_n", "ls"); a.emit(movs_imm, 0, NW)
    a.label("fd_n"); a.emit(mov_reg, 6, 0)
    take(40); imm32(0, BUF); a.emit(ldr_imm, 1, 7, 36); a.emit(adds_reg, 0, 0, 1); a.emit(mov_reg, 1, 6); a.emit(bl, "c_ywin"); give(40)
    imm32(0, WIN); a.emit(ldr_imm, 1, 7, 24); a.emit(ldr_imm, 2, 7, 28); a.emit(ldr_imm, 3, 7, 36); a.emit(adds_reg, 2, 2, 3); a.emit(lsrs_imm, 2, 2, 1)
    a.emit(adds_reg, 1, 1, 2); a.emit(mov_reg, 2, 6); a.emit(bl, "c_copy2"); a.emit(cmp_imm, 0, 0); bc("fd_fail", "ne")
    a.emit(ldr_imm, 0, 7, 36); a.emit(adds_reg, 0, 0, 6); a.emit(adds_reg, 0, 0, 6); a.emit(str_imm, 0, 7, 36); a.emit(b, "fd_w")
    a.label("fd_wd")
    a.emit(ldr_imm, 0, 7, 28); a.emit(ldr_imm, 1, 7, 32); a.emit(adds_reg, 0, 0, 1); a.emit(str_imm, 0, 7, 28); a.emit(b, "fd_l")
    a.label("fd_ok"); a.emit(movs_imm, 0, 0)
    a.label("fd_fail"); a.emit(str_imm, 0, 7, 48)
    a.emit(bl, BUF_UNLOCK); a.emit(ldr_imm, 0, 7, 48); a.emit(ldr_imm, 1, 7, 44); ret_status(F)

    # ---- c_d2f (r0 = item ptr, r1 = Y source, r2 = size) -> r0 = status: the item := size bytes from the DSP's words (deleted first)
    # frame: [16] item [20] size [24] src [28] off [32] piece [36] pos [40] holder [48] status
    a.label("c_d2f")
    a.emit(push_list, [4, 5, 6, 7], lr=True); a.emit(sub_sp_imm, F); a.emit(mov_reg, 7, 13)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 6, 2); zero_frame(F)
    a.emit(str_imm, 4, 7, 16); a.emit(str_imm, 6, 7, 20); a.emit(str_imm, 5, 7, 24); a.emit(movs_imm, 0, 9); a.emit(str_imm, 0, 7, 48)
    a.emit(movs_imm, 0, 5); a.emit(bl, BUF_LOCK)
    a.emit(ldr_imm, 0, 7, 16); a.emit(movs_imm, 1, 0); a.emit(movs_imm, 2, 0); a.emit(bl, DEL_FN)
    a.label("df_l")
    piece(20, 28, 32, "df_ok")
    a.emit(movs_imm, 0, 0); a.emit(str_imm, 0, 7, 36)
    a.label("df_r")
    a.emit(ldr_imm, 0, 7, 32); a.emit(ldr_imm, 1, 7, 36); a.emit(cmp_reg, 1, 0); bc("df_wr", "hs")
    a.emit(subs_reg, 0, 0, 1); a.emit(adds_imm8, 0, 1); a.emit(lsrs_imm, 0, 0, 1); a.emit(cmp_imm, 0, NW); a.emit(b_cond, "df_n", "ls"); a.emit(movs_imm, 0, NW)
    a.label("df_n"); a.emit(mov_reg, 5, 0)                                                   # r5 = n words
    a.emit(ldr_imm, 0, 7, 24); a.emit(ldr_imm, 1, 7, 28); a.emit(ldr_imm, 2, 7, 36); a.emit(adds_reg, 1, 1, 2); a.emit(lsrs_imm, 1, 1, 1)
    a.emit(adds_reg, 0, 0, 1); a.emit(mov_reg, 1, 5); a.emit(bl, "c_copy"); a.emit(cmp_imm, 0, 0); bc("df_fail", "ne")
    take(40)
    imm32(4, BUF); a.emit(ldr_imm, 0, 7, 36); a.emit(adds_reg, 4, 4, 0); a.emit(movs_imm, 6, 0)     # r4 = BUF + pos, r6 = k
    a.label("df_k")
    imm32(1, 0x8000 | WIN); a.emit(adds_reg, 1, 1, 6); a.emit(movs_imm, 0, 0); a.emit(bl, DSP_READ); a.emit(lsrs_imm, 0, 0, 16)
    a.emit(lsls_imm, 1, 6, 1); a.emit(strh_reg, 0, 4, 1)
    a.emit(adds_imm8, 6, 1); a.emit(cmp_reg, 6, 5); a.emit(b_cond, "df_k", "lo")
    give(40)
    a.emit(ldr_imm, 0, 7, 36); a.emit(adds_reg, 0, 0, 5); a.emit(adds_reg, 0, 0, 5); a.emit(str_imm, 0, 7, 36); a.emit(b, "df_r")
    a.label("df_wr")
    wr(16, 28, 32, "df_fail")
    a.emit(ldr_imm, 0, 7, 28); a.emit(ldr_imm, 1, 7, 32); a.emit(adds_reg, 0, 0, 1); a.emit(str_imm, 0, 7, 28); a.emit(b, "df_l")
    a.label("df_ok"); a.emit(movs_imm, 0, 0)
    a.label("df_fail"); a.emit(str_imm, 0, 7, 48)
    a.emit(bl, BUF_UNLOCK); a.emit(ldr_imm, 0, 7, 48); ret_status(F)

    # ---- c_f2f (r0 = source item ptr, r1 = destination item ptr, r2 = size) -> r0 = status (the destination deleted first)
    # frame: [16] src [20] size [24] dst [28] off [32] piece [48] status
    a.label("c_f2f")
    a.emit(push_list, [4, 5, 6, 7], lr=True); a.emit(sub_sp_imm, F); a.emit(mov_reg, 7, 13)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 6, 2); zero_frame(F)
    a.emit(str_imm, 4, 7, 16); a.emit(str_imm, 6, 7, 20); a.emit(str_imm, 5, 7, 24); a.emit(movs_imm, 0, 9); a.emit(str_imm, 0, 7, 48)
    a.emit(movs_imm, 0, 5); a.emit(bl, BUF_LOCK)
    a.emit(ldr_imm, 0, 7, 24); a.emit(movs_imm, 1, 0); a.emit(movs_imm, 2, 0); a.emit(bl, DEL_FN)
    a.label("ff_l")
    piece(20, 28, 32, "ff_ok")
    rd(16, 28, 32, "ff_fail")
    wr(24, 28, 32, "ff_fail")
    a.emit(ldr_imm, 0, 7, 28); a.emit(ldr_imm, 1, 7, 32); a.emit(adds_reg, 0, 0, 1); a.emit(str_imm, 0, 7, 28); a.emit(b, "ff_l")
    a.label("ff_ok"); a.emit(movs_imm, 0, 0)
    a.label("ff_fail"); a.emit(str_imm, 0, 7, 48)
    a.emit(bl, BUF_UNLOCK); a.emit(ldr_imm, 0, 7, 48); ret_status(F)

    # ---- c_zpad (r0 = Y address): PADW zero words there
    a.label("c_zpad")
    a.emit(push_list, [4, 5, 6, 7], lr=True); a.emit(sub_sp_imm, 8); a.emit(mov_reg, 7, 13); a.emit(mov_reg, 5, 0)
    a.emit(movs_imm, 0, 5); a.emit(bl, BUF_LOCK)
    imm32(4, BUF); a.emit(movs_imm, 0, 0)
    for o in range(0, 2 * NW, 4): a.emit(str_imm, 0, 4, o)
    a.emit(mov_reg, 0, 7); a.emit(bl, "c_take"); a.emit(mov_reg, 0, 4); a.emit(movs_imm, 1, NW); a.emit(bl, "c_ywin"); a.emit(mov_reg, 0, 7); a.emit(bl, "c_give")
    a.emit(movs_imm, 6, 0)
    a.label("zp_l")
    imm32(0, WIN); a.emit(adds_reg, 1, 5, 6); a.emit(movs_imm, 2, NW); a.emit(bl, "c_copy2")
    a.emit(adds_imm8, 6, NW); imm32(0, PADW); a.emit(cmp_reg, 6, 0); a.emit(b_cond, "zp_l", "lo")
    a.emit(bl, BUF_UNLOCK); a.emit(add_sp_imm, 8); a.emit(pop_list, [4, 5, 6, 7], pc=True)

    if IMPGUARD:                                 # ---- c_impfree (r0 = place, r1 = words) -> r0 = 1 when no entry of the sample table starts inside
        a.label("c_impfree")
        a.emit(push_list, [4, 5, 6, 7], lr=True); a.emit(sub_sp_imm, 8)
        a.emit(mov_reg, 4, 0); a.emit(adds_reg, 5, 0, 1)
        a.emit(mov_reg, 0, 13); a.emit(bl, "c_take")
        a.emit(movs_imm, 6, 0); a.emit(movs_imm, 7, 0)
        a.label("if_l")
        a.emit(lsls_imm, 0, 6, 2); imm32(1, TAB); a.emit(adds_reg, 0, 0, 1); a.emit(bl, "c_xr")
        a.emit(cmp_reg, 0, 4); a.emit(b_cond, "if_n", "lo"); a.emit(cmp_reg, 0, 5); a.emit(b_cond, "if_x", "lo")      # inside: busy (r7 = 0)
        a.label("if_n")
        a.emit(adds_imm8, 6, 1); a.emit(cmp_imm, 6, N_SAMPLES); a.emit(b_cond, "if_l", "lo")
        a.emit(movs_imm, 7, 1)
        a.label("if_x")
        a.emit(mov_reg, 0, 13); a.emit(bl, "c_give")
        a.emit(mov_reg, 0, 7); a.emit(add_sp_imm, 8); a.emit(pop_list, [4, 5, 6, 7], pc=True)

    if INPLACE:                                  # ---- c_nextstart (r0 = a start) -> r0 = the nearest entry start above it inside the pack's sample memory, -1 = none
        a.label("c_nextstart")
        a.emit(push_list, [4, 5, 6, 7], lr=True); a.emit(sub_sp_imm, 8)
        a.emit(mov_reg, 4, 0); a.emit(movs_imm, 5, 0); a.emit(subs_imm8, 5, 1)
        a.emit(mov_reg, 0, 13); a.emit(bl, "c_take")
        a.emit(movs_imm, 6, 0)
        a.label("ns_l")
        a.emit(lsls_imm, 0, 6, 2); imm32(1, TAB); a.emit(adds_reg, 0, 0, 1); a.emit(bl, "c_xr")
        a.emit(cmp_reg, 0, 4); a.emit(b_cond, "ns_n", "ls")
        imm32(1, STOCK_HI); a.emit(cmp_reg, 0, 1); a.emit(b_cond, "ns_n", "hs")
        a.emit(cmp_reg, 0, 5); a.emit(b_cond, "ns_n", "hs"); a.emit(mov_reg, 5, 0)
        a.label("ns_n")
        a.emit(adds_imm8, 6, 1); a.emit(cmp_imm, 6, N_SAMPLES); a.emit(b_cond, "ns_l", "lo")
        a.emit(mov_reg, 0, 13); a.emit(bl, "c_give")
        a.emit(mov_reg, 0, 5); a.emit(add_sp_imm, 8); a.emit(pop_list, [4, 5, 6, 7], pc=True)
        # ---- c_inplace (r0 = c_xcopy2's frame: [40] size of X:A, [48] where X:A lies in the free memory, [56] / [60] B's entry) -> r0 = 1 when the copy
        #      went into B's own place (then [56] / [60] = the new entry), 0 = not there (it does not fit, or B is not in the pack's sample memory)
        a.label("c_inplace")
        a.emit(push_list, [4, 5, 6, 7], lr=True); a.emit(mov_reg, 7, 0)
        a.emit(ldr_imm, 4, 7, 56)                                                                   # r4 = B's start
        imm32(1, STOCK_LO); a.emit(cmp_reg, 4, 1); bc("ip_no", "lo"); imm32(1, STOCK_HI); a.emit(cmp_reg, 4, 1); bc("ip_no", "hs")
        a.emit(ldr_imm, 5, 7, 40); a.emit(subs_imm8, 5, 43); a.emit(lsrs_imm, 5, 5, 1)             # r5 = data words of X:A
        a.emit(mov_reg, 0, 4); a.emit(bl, "c_nextstart"); a.emit(mov_reg, 6, 0)
        a.emit(adds_imm8, 0, 1); a.emit(b_cond, "ip_nn", "eq")
        a.emit(subs_imm8, 6, 2); a.emit(b, "ip_end")                                               # r6 = the end of B's place
        a.label("ip_nn")
        a.emit(ldr_imm, 6, 7, 60); a.emit(adds_reg, 6, 6, 4); imm32(1, PADW); a.emit(adds_reg, 6, 6, 1)
        a.label("ip_end")
        imm32(1, PADW); a.emit(adds_reg, 0, 4, 5); a.emit(adds_reg, 0, 0, 1); a.emit(cmp_reg, 0, 6); bc("ip_no", "hi")
        a.emit(movs_imm, 6, 0)                                                                      # r6 = words moved
        a.label("ip_l")
        a.emit(subs_reg, 2, 5, 6); a.emit(b_cond, "ip_z", "eq"); imm32(1, 0x10000); a.emit(cmp_reg, 2, 1); a.emit(b_cond, "ip_c", "ls"); a.emit(mov_reg, 2, 1)
        a.label("ip_c")
        a.emit(ldr_imm, 0, 7, 48); a.emit(adds_imm8, 0, 22); a.emit(adds_reg, 0, 0, 6); a.emit(adds_reg, 1, 4, 6)
        a.emit(adds_reg, 6, 6, 2); a.emit(bl, "c_copy2"); a.emit(cmp_imm, 0, 0); bc("ip_no", "ne")
        a.emit(b, "ip_l")
        a.label("ip_z")
        a.emit(adds_reg, 0, 4, 5); a.emit(bl, "c_zpad")
        a.emit(subs_imm8, 5, 2); a.emit(str_imm, 5, 7, 60)                                          # the new entry: B's start, the new length
        a.emit(movs_imm, 0, 1); a.emit(pop_list, [4, 5, 6, 7], pc=True)
        a.label("ip_no"); a.emit(movs_imm, 0, 0); a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_impdst (r0 = words) -> r0 = where they go in the free memory (X:IMPW, back to IMP_LO when they do not fit), 0 = too big
    a.label("c_impdst")
    a.emit(push_list, [4, 5], lr=True); a.emit(sub_sp_imm, 8); a.emit(mov_reg, 4, 0)
    imm32(1, IMP_HI - IMP_LO); a.emit(cmp_reg, 4, 1); a.emit(b_cond, "id_ok", "ls"); a.emit(movs_imm, 0, 0); a.emit(b, "id_x")
    a.label("id_ok")
    a.emit(mov_reg, 0, 13); a.emit(bl, "c_take"); imm32(0, SD.IMPW); a.emit(bl, "c_xr"); a.emit(mov_reg, 5, 0); a.emit(mov_reg, 0, 13); a.emit(bl, "c_give")
    if INPLACE:                                  # nothing of the table in the free memory any more: start again at its beginning
        imm32(0, IMP_LO); imm32(1, IMP_HI - IMP_LO); a.emit(bl, "c_impfree"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "id_used", "eq"); a.emit(movs_imm, 5, 0)
        a.label("id_used")
    imm32(1, IMP_LO); a.emit(cmp_reg, 5, 1); a.emit(b_cond, "id_lo", "hs"); a.emit(mov_reg, 5, 1)
    a.label("id_lo")
    a.emit(adds_reg, 0, 5, 4); imm32(2, IMP_HI); a.emit(cmp_reg, 0, 2); a.emit(b_cond, "id_f", "ls"); a.emit(mov_reg, 5, 1)
    a.label("id_f"); a.emit(mov_reg, 0, 5)
    if IMPGUARD:                                 # a sample of the table still starts there: 0
        a.emit(mov_reg, 1, 4); a.emit(bl, "c_impfree"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "id_x", "eq"); a.emit(mov_reg, 0, 5)
    a.label("id_x"); a.emit(add_sp_imm, 8); a.emit(pop_list, [4, 5], pc=True)

    def item(o, kind, idx_reg, pack_reg):        # frame[o] = {kind, idx, pack}
        a.emit(movs_imm, 0, kind); a.emit(str_imm, 0, 7, o); a.emit(str_imm, idx_reg, 7, o + 4); a.emit(strb_w, pack_reg, 7, o + 8)
    def iptr(rd, o): a.emit(mov_reg, rd, 7); a.emit(adds_imm8, rd, o)

    # ---- c_xswap2 (r0 = A, r1 = pack X, r2 = B of the loaded pack) -> r0 = status
    # frame: [16..27] X:A [28..39] B [40] size X:A [44] size B [48] dst [52] status [56..67] entry B [68] plain [72] the loaded pack [76] holder [80] words
    F2 = 84
    a.label("c_xswap2")
    a.emit(push_list, [4, 5, 6, 7], lr=True); a.emit(sub_sp_imm, F2); a.emit(mov_reg, 7, 13)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 6, 2); zero_frame(F2)
    a.emit(bl, "c_curpack"); a.emit(str_imm, 0, 7, 72)
    item(16, KIND_PCM, 4, 5); a.emit(ldr_imm, 1, 7, 72); item(28, KIND_PCM, 6, 1)
    a.emit(movs_imm, 0, 8); a.emit(str_imm, 0, 7, 52)
    iptr(0, 16); a.emit(bl, SIZE); a.emit(str_imm, 0, 7, 40); a.emit(cmp_imm, 0, 44); bc("x2_sel", "ls")
    iptr(0, 28); a.emit(bl, SIZE); a.emit(str_imm, 0, 7, 44); a.emit(cmp_imm, 0, 44); bc("x2_sel", "ls")
    a.emit(movs_imm, 0, 10); a.emit(str_imm, 0, 7, 52)
    a.emit(mov_reg, 0, 6); a.emit(ldr_imm, 1, 7, 40); a.emit(subs_imm8, 1, 44); a.emit(lsrs_imm, 1, 1, 1); a.emit(ldr_imm, 2, 7, 72); a.emit(bl, "c_fitsp")
    a.emit(cmp_imm, 0, 0); bc("x2_sel", "eq")
    a.emit(mov_reg, 0, 4); a.emit(ldr_imm, 1, 7, 44); a.emit(subs_imm8, 1, 44); a.emit(lsrs_imm, 1, 1, 1); a.emit(mov_reg, 2, 5); a.emit(bl, "c_fitsp")
    a.emit(cmp_imm, 0, 0); bc("x2_sel", "eq")
    a.emit(ldr_imm, 0, 7, 40); a.emit(adds_imm8, 0, 1); a.emit(lsrs_imm, 0, 0, 1); imm32(1, PADW); a.emit(adds_reg, 0, 0, 1); a.emit(str_imm, 0, 7, 80)
    a.emit(bl, "c_impdst"); a.emit(str_imm, 0, 7, 48); a.emit(cmp_imm, 0, 0); bc("x2_sel", "eq")
    a.emit(mov_reg, 0, 6); a.emit(mov_reg, 1, 7); a.emit(adds_imm8, 1, 56); a.emit(bl, "c_entry")
    # 1. X:A -> the DSP
    iptr(0, 16); a.emit(ldr_imm, 1, 7, 40); a.emit(ldr_imm, 2, 7, 48); a.emit(bl, "c_f2d"); a.emit(str_imm, 1, 7, 68)
    a.emit(str_imm, 0, 7, 52); a.emit(cmp_imm, 0, 0); bc("x2_sel", "ne")
    # 2. B's file -> X:A (failed: X:A back from the DSP)
    iptr(0, 28); iptr(1, 16); a.emit(ldr_imm, 2, 7, 44); a.emit(bl, "c_f2f"); a.emit(cmp_imm, 0, 0); bc("x2_ok2", "eq")
    a.emit(str_imm, 0, 7, 52); iptr(0, 16); a.emit(ldr_imm, 1, 7, 48); a.emit(ldr_imm, 2, 7, 40); a.emit(bl, "c_d2f"); a.emit(b, "x2_sel")
    a.label("x2_ok2")
    # 3. the DSP copy -> B (failed: B back from X:A, X:A back from the DSP)
    iptr(0, 28); a.emit(ldr_imm, 1, 7, 48); a.emit(ldr_imm, 2, 7, 40); a.emit(bl, "c_d2f"); a.emit(cmp_imm, 0, 0); bc("x2_ok3", "eq")
    a.emit(str_imm, 0, 7, 52)
    iptr(0, 16); iptr(1, 28); a.emit(ldr_imm, 2, 7, 44); a.emit(bl, "c_f2f")
    iptr(0, 16); a.emit(ldr_imm, 1, 7, 48); a.emit(ldr_imm, 2, 7, 40); a.emit(bl, "c_d2f"); a.emit(b, "x2_sel")
    a.label("x2_ok3")
    # 4. the copy is B's live sample: entry = (its data, n - 2, B's increment), zeros after it, X:IMPW after them
    a.emit(movs_imm, 0, 1); a.emit(str_imm, 0, 7, 52)
    a.emit(ldr_imm, 0, 7, 68); a.emit(cmp_imm, 0, 0); bc("x2_sel", "eq")
    a.emit(ldr_imm, 0, 7, 40); a.emit(adds_imm8, 0, 1); a.emit(lsrs_imm, 0, 0, 1); a.emit(ldr_imm, 1, 7, 48); a.emit(adds_reg, 0, 0, 1); a.emit(bl, "c_zpad")
    a.emit(ldr_imm, 0, 7, 48); a.emit(adds_imm8, 0, 22); a.emit(str_imm, 0, 7, 56)
    a.emit(ldr_imm, 0, 7, 40); a.emit(subs_imm8, 0, 44); a.emit(lsrs_imm, 0, 0, 1); a.emit(subs_imm8, 0, 2); a.emit(str_imm, 0, 7, 60)
    a.emit(mov_reg, 0, 6); a.emit(mov_reg, 1, 7); a.emit(adds_imm8, 1, 56); a.emit(bl, "c_setentry")
    take(76); imm32(0, SD.IMPW); a.emit(ldr_imm, 1, 7, 48); a.emit(ldr_imm, 2, 7, 80); a.emit(adds_reg, 1, 1, 2); a.emit(bl, "c_xw"); give(76)
    a.emit(movs_imm, 0, 0); a.emit(str_imm, 0, 7, 52)
    a.label("x2_sel")
    a.emit(ldr_imm, 0, 7, 72); a.emit(bl, "c_resel")
    a.emit(ldr_imm, 0, 7, 52); a.emit(add_sp_imm, F2); a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_swap2 (r0 = A, r1 = B, both of the loaded pack) -> r0 = status
    # frame: [16..27] A [28..39] B [40] size A [44] size B [48] tmp [52] status [56..67] entry A [68..79] entry B [80] the loaded pack
    F3 = 84
    a.label("c_swap2")
    a.emit(push_list, [4, 5, 6, 7], lr=True); a.emit(sub_sp_imm, F3); a.emit(mov_reg, 7, 13)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); zero_frame(F3)
    a.emit(bl, "c_curpack"); a.emit(str_imm, 0, 7, 80); a.emit(bl, "c_resel")
    a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 7); a.emit(adds_imm8, 1, 56); a.emit(bl, "c_entry")
    a.emit(mov_reg, 0, 5); a.emit(mov_reg, 1, 7); a.emit(adds_imm8, 1, 68); a.emit(bl, "c_entry")
    imm32(1, SD.HIGH_BASE); a.emit(ldr_imm, 0, 7, 56); a.emit(cmp_reg, 0, 1); bc("s2_old", "hs")
    a.emit(ldr_imm, 0, 7, 68); a.emit(cmp_reg, 0, 1); bc("s2_old", "hs")
    a.emit(ldr_imm, 6, 7, 80); item(16, KIND_PCM, 4, 6); item(28, KIND_PCM, 5, 6)
    a.emit(movs_imm, 0, 8); a.emit(str_imm, 0, 7, 52)
    iptr(0, 16); a.emit(bl, SIZE); a.emit(str_imm, 0, 7, 40); a.emit(cmp_imm, 0, 44); bc("s2_x", "ls")
    iptr(0, 28); a.emit(bl, SIZE); a.emit(str_imm, 0, 7, 44); a.emit(cmp_imm, 0, 44); bc("s2_x", "ls")
    a.emit(ldr_imm, 0, 7, 40); a.emit(adds_imm8, 0, 1); a.emit(lsrs_imm, 0, 0, 1); a.emit(bl, "c_impdst"); a.emit(str_imm, 0, 7, 48)
    a.emit(movs_imm, 1, 10); a.emit(str_imm, 1, 7, 52); a.emit(cmp_imm, 0, 0); bc("s2_x", "eq")
    iptr(0, 16); a.emit(ldr_imm, 1, 7, 40); a.emit(ldr_imm, 2, 7, 48); a.emit(bl, "c_f2d"); a.emit(str_imm, 0, 7, 52); a.emit(cmp_imm, 0, 0); bc("s2_x", "ne")
    iptr(0, 28); iptr(1, 16); a.emit(ldr_imm, 2, 7, 44); a.emit(bl, "c_f2f"); a.emit(cmp_imm, 0, 0); bc("s2_ok2", "eq")
    a.emit(str_imm, 0, 7, 52); iptr(0, 16); a.emit(ldr_imm, 1, 7, 48); a.emit(ldr_imm, 2, 7, 40); a.emit(bl, "c_d2f"); a.emit(b, "s2_x")
    a.label("s2_ok2")
    iptr(0, 28); a.emit(ldr_imm, 1, 7, 48); a.emit(ldr_imm, 2, 7, 40); a.emit(bl, "c_d2f"); a.emit(cmp_imm, 0, 0); bc("s2_ok3", "eq")
    a.emit(str_imm, 0, 7, 52)
    iptr(0, 16); iptr(1, 28); a.emit(ldr_imm, 2, 7, 44); a.emit(bl, "c_f2f")
    iptr(0, 16); a.emit(ldr_imm, 1, 7, 48); a.emit(ldr_imm, 2, 7, 40); a.emit(bl, "c_d2f"); a.emit(b, "s2_x")
    a.label("s2_ok3")
    a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 7); a.emit(adds_imm8, 1, 68); a.emit(bl, "c_setentry")
    a.emit(mov_reg, 0, 5); a.emit(mov_reg, 1, 7); a.emit(adds_imm8, 1, 56); a.emit(bl, "c_setentry")
    a.emit(movs_imm, 0, 0); a.emit(str_imm, 0, 7, 52)
    a.label("s2_x")
    a.emit(ldr_imm, 0, 7, 80); a.emit(bl, "c_resel")
    a.emit(ldr_imm, 0, 7, 52); a.emit(add_sp_imm, F3); a.emit(pop_list, [4, 5, 6, 7], pc=True)
    a.label("s2_old")                            # a replaced drum: the SC35 swap from the DSP's memory
    a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(bl, "c_swap"); a.emit(str_imm, 0, 7, 52); a.emit(b, "s2_x")
    if COPYX:
        xcopy_code(a, imm32, bc, item, iptr, zero_frame, take, give)


def xcopy_code(a, imm32, bc, item, iptr, zero_frame, take, give):
    """c_xcopy2 (r0 = A, r1 = pack X, r2 = B of the loaded pack) -> r0 = status: B := X:A (see 8.)."""
    # frame: [16..27] X:A [28..39] B [40] size X:A [44] size B [48] dst [52] status [56..67] entry B [68] plain [72] the loaded pack [76] holder
    #        [80] words of X:A + padding [84] B's backup
    F = 88
    a.label("c_xcopy2")
    a.emit(push_list, [4, 5, 6, 7], lr=True); a.emit(sub_sp_imm, F); a.emit(mov_reg, 7, 13)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 6, 2); zero_frame(F)
    a.emit(bl, "c_curpack"); a.emit(str_imm, 0, 7, 72)
    item(16, KIND_PCM, 4, 5); a.emit(ldr_imm, 1, 7, 72); item(28, KIND_PCM, 6, 1)
    a.emit(movs_imm, 0, 8); a.emit(str_imm, 0, 7, 52)
    iptr(0, 16); a.emit(bl, SIZE); a.emit(str_imm, 0, 7, 40); a.emit(cmp_imm, 0, 44); bc("xc_sel", "ls")
    iptr(0, 28); a.emit(bl, SIZE); a.emit(str_imm, 0, 7, 44)
    if EMPTY:                                    # SC38.4: an empty B (no file / header only) is not backed up
        a.emit(cmp_imm, 0, 44); a.emit(b_cond, "xc_e0", "hi"); a.emit(movs_imm, 0, 0); a.emit(str_imm, 0, 7, 44)
        a.label("xc_e0")
    else:
        a.emit(cmp_imm, 0, 44); bc("xc_sel", "ls")
    a.emit(movs_imm, 0, 10); a.emit(str_imm, 0, 7, 52)
    a.emit(mov_reg, 0, 6); a.emit(ldr_imm, 1, 7, 40); a.emit(subs_imm8, 1, 44); a.emit(lsrs_imm, 1, 1, 1); a.emit(ldr_imm, 2, 7, 72); a.emit(bl, "c_fitsp")
    a.emit(cmp_imm, 0, 0); bc("xc_sel", "eq")
    a.emit(ldr_imm, 0, 7, 40); a.emit(adds_imm8, 0, 1); a.emit(lsrs_imm, 0, 0, 1); imm32(1, PADW); a.emit(adds_reg, 0, 0, 1); a.emit(str_imm, 0, 7, 80)
    a.emit(ldr_imm, 1, 7, 44); a.emit(adds_imm8, 1, 1); a.emit(lsrs_imm, 1, 1, 1); a.emit(adds_reg, 0, 0, 1)            # + B's backup
    a.emit(bl, "c_impdst"); a.emit(str_imm, 0, 7, 48); a.emit(cmp_imm, 0, 0); bc("xc_sel", "eq")
    a.emit(ldr_imm, 1, 7, 80); a.emit(adds_reg, 0, 0, 1); a.emit(str_imm, 0, 7, 84)
    a.emit(mov_reg, 0, 6); a.emit(mov_reg, 1, 7); a.emit(adds_imm8, 1, 56); a.emit(bl, "c_entry")
    iptr(0, 16); a.emit(ldr_imm, 1, 7, 40); a.emit(ldr_imm, 2, 7, 48); a.emit(bl, "c_f2d"); a.emit(str_imm, 1, 7, 68)          # X:A -> the DSP
    a.emit(str_imm, 0, 7, 52); a.emit(cmp_imm, 0, 0); bc("xc_sel", "ne")
    if EMPTY: a.emit(ldr_imm, 0, 7, 44); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "xc_nb", "eq")                                    # an empty B: no backup
    iptr(0, 28); a.emit(ldr_imm, 1, 7, 44); a.emit(ldr_imm, 2, 7, 84); a.emit(bl, "c_f2d")                                     # B -> its backup
    a.emit(str_imm, 0, 7, 52); a.emit(cmp_imm, 0, 0); bc("xc_sel", "ne")
    if EMPTY: a.label("xc_nb")
    iptr(0, 28); a.emit(ldr_imm, 1, 7, 48); a.emit(ldr_imm, 2, 7, 40); a.emit(bl, "c_d2f"); a.emit(cmp_imm, 0, 0); bc("xc_ok", "eq")   # B := X:A
    a.emit(str_imm, 0, 7, 52)
    if EMPTY: a.emit(ldr_imm, 0, 7, 44); a.emit(cmp_imm, 0, 0); bc("xc_sel", "eq")                                                # nothing to put back
    iptr(0, 28); a.emit(ldr_imm, 1, 7, 84); a.emit(ldr_imm, 2, 7, 44); a.emit(bl, "c_d2f"); a.emit(b, "xc_sel")
    a.label("xc_ok")
    a.emit(movs_imm, 0, 1); a.emit(str_imm, 0, 7, 52)
    a.emit(ldr_imm, 0, 7, 68); a.emit(cmp_imm, 0, 0); bc("xc_sel", "eq")
    if INPLACE:                                  # into B's own place when it fits: the free memory was only a temporary
        if EMPTY: a.emit(ldr_imm, 0, 7, 44); a.emit(cmp_imm, 0, 0); bc("xc_imp", "eq")                                            # an empty B has no place
        a.emit(mov_reg, 0, 7); a.emit(bl, "c_inplace"); a.emit(cmp_imm, 0, 0); bc("xc_imp", "eq")
        a.emit(mov_reg, 0, 6); a.emit(mov_reg, 1, 7); a.emit(adds_imm8, 1, 56); a.emit(bl, "c_setentry")
        a.emit(movs_imm, 0, 0); a.emit(str_imm, 0, 7, 52); a.emit(b, "xc_sel")
        a.label("xc_imp")
    a.emit(ldr_imm, 0, 7, 40); a.emit(adds_imm8, 0, 1); a.emit(lsrs_imm, 0, 0, 1); a.emit(ldr_imm, 1, 7, 48); a.emit(adds_reg, 0, 0, 1); a.emit(bl, "c_zpad")
    a.emit(ldr_imm, 0, 7, 48); a.emit(adds_imm8, 0, 22); a.emit(str_imm, 0, 7, 56)
    a.emit(ldr_imm, 0, 7, 40); a.emit(subs_imm8, 0, 44); a.emit(lsrs_imm, 0, 0, 1); a.emit(subs_imm8, 0, 2); a.emit(str_imm, 0, 7, 60)
    a.emit(mov_reg, 0, 6); a.emit(mov_reg, 1, 7); a.emit(adds_imm8, 1, 56); a.emit(bl, "c_setentry")
    take(76); imm32(0, SD.IMPW); a.emit(ldr_imm, 1, 7, 48); a.emit(ldr_imm, 2, 7, 80); a.emit(adds_reg, 1, 1, 2); a.emit(bl, "c_xw"); give(76)
    a.emit(movs_imm, 0, 0); a.emit(str_imm, 0, 7, 52)
    a.label("xc_sel")
    a.emit(ldr_imm, 0, 7, 72); a.emit(bl, "c_resel")
    a.emit(ldr_imm, 0, 7, 52); a.emit(add_sp_imm, F); a.emit(pop_list, [4, 5, 6, 7], pc=True)


def patch_code(a, L, prev, imm32, bc):
    """c_pclip / c_psetclip (X:PCLIPW), c_pswap, the synth Preset view's pad (c_spp) and LEDs (c_spl)."""
    def held(rd):
        imm32(0, MGR); a.emit(ldr_imm, 0, 0, 0x20); a.emit(ldr_imm, 0, 0, 0xC); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET)
        a.emit(ldrb_imm, rd, 0, 0)
    a.label("c_pclip")                           # r0 = the patch clip (PMAGIC << 16 | pack << 8 | patch), 0 = none
    a.emit(push_list, [4], lr=True); a.emit(sub_sp_imm, 8)
    a.emit(mov_reg, 0, 13); a.emit(bl, "c_take"); imm32(0, SD.PCLIPW); a.emit(bl, "c_xr"); a.emit(mov_reg, 4, 0)
    a.emit(mov_reg, 0, 13); a.emit(bl, "c_give")
    a.emit(lsrs_imm, 0, 4, 16); a.emit(cmp_imm, 0, PCLIP_MAGIC); a.emit(b_cond, "pc_ok", "eq"); a.emit(movs_imm, 4, 0)
    a.label("pc_ok"); a.emit(mov_reg, 0, 4); a.emit(add_sp_imm, 8); a.emit(pop_list, [4], pc=True)
    a.label("c_psetclip")                        # X:PCLIPW = r0
    a.emit(push_list, [4], lr=True); a.emit(sub_sp_imm, 8); a.emit(mov_reg, 4, 0)
    a.emit(mov_reg, 0, 13); a.emit(bl, "c_take"); imm32(0, SD.PCLIPW); a.emit(mov_reg, 1, 4); a.emit(bl, "c_xw")
    a.emit(mov_reg, 0, 13); a.emit(bl, "c_give"); a.emit(add_sp_imm, 8); a.emit(pop_list, [4], pc=True)

    # ---- c_pswap (r0 = A, r1 = pack of A, r2 = B of the current pack) -> r0 = status (0 = done): the two 340-byte patches exchanged in their banks
    # frame r7: [0] cb [4] ctx [8] &done [12] done [16..27] item of A's bank [28..39] item of B's bank [40] offset of A [44] offset of B [48] status
    F = 64 if FFGAP else 60 if EMPTY else 56 if FIX2 else 52
    def item_at(o, idx_reg, pack_reg_or_ff):     # frame[o] = {KIND_PATCH, idx >> 3, pack}; clobbers r0
        a.emit(movs_imm, 0, KIND_PATCH); a.emit(str_imm, 0, 7, o)
        a.emit(lsrs_imm, 0, idx_reg, 3); a.emit(str_imm, 0, 7, o + 4)
        if pack_reg_or_ff is None: a.emit(movs_imm, 0, 0xFF); a.emit(strb_w, 0, 7, o + 8)
        else: a.emit(strb_w, pack_reg_or_ff, 7, o + 8)
    def rw_patch(fn, item_off, off_slot, buf_off, fail, abs_buf=None, len_slot=None):
        a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, 12); a.emit(str_imm, 0, 7, 8)
        a.emit(movs_imm, 0, 0); a.emit(str_imm, 0, 7, 12)
        a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, item_off); a.emit(ldr_imm, 1, 7, off_slot); imm32(2, BUF + buf_off if abs_buf is None else abs_buf)
        if len_slot is None: imm32(3, PATCH_SZ)
        else: a.emit(ldr_imm, 3, 7, len_slot)
        a.emit(bl, fn)
        a.emit(movs_imm, 1, 0); a.emit(str_imm, 1, 7, 8)
        a.emit(cmp_imm, 0, 0); bc(fail, "ne")
    a.label("c_pswap")
    a.emit(push_list, [4, 5, 6, 7], lr=True); a.emit(sub_sp_imm, F); a.emit(mov_reg, 7, 13)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 6, 2)
    a.emit(movs_imm, 3, 0)
    for o in range(0, F, 4): a.emit(str_imm, 3, 7, o)
    if FIX2:
        a.emit(bl, "c_curpack"); a.emit(str_imm, 0, 7, 52); a.emit(mov_reg, 3, 0)
        item_at(16, 4, 5); item_at(28, 6, 3)                                                    # B: the loaded pack by its number
    else:
        item_at(16, 4, 5); item_at(28, 6, None)
    a.emit(lsls_imm, 0, 4, 29); a.emit(lsrs_imm, 0, 0, 20); a.emit(str_imm, 0, 7, 40)           # 512 * (A % 8)
    a.emit(lsls_imm, 0, 6, 29); a.emit(lsrs_imm, 0, 0, 20); a.emit(str_imm, 0, 7, 44)
    a.emit(movs_imm, 0, 8); a.emit(str_imm, 0, 7, 48)
    a.emit(movs_imm, 0, 5); a.emit(bl, BUF_LOCK)
    rw_patch(READ, 16, 40, 0, "ps_fail")
    a.emit(ldr_imm, 0, 7, 12); imm32(1, PATCH_SZ); a.emit(cmp_reg, 0, 1); bc("ps_fail8", "ne")
    if EMPTY:                                    # SC38.4: between packs B is not read; A goes to B's slot and to every empty slot before it
        a.emit(ldr_imm, 0, 7, 52); a.emit(cmp_reg, 0, 5); bc("ps_rb", "eq")
        a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, 28); a.emit(bl, SIZE)                                  # the bank's size (0: no file)
    if EMPTY and FFGAP:                          # SC38.6: from the bank's end to B: 0xFF, as the stock (the slots between stay empty); then A at B
        a.emit(str_imm, 0, 7, 56); a.emit(ldr_imm, 1, 7, 44); a.emit(cmp_reg, 0, 1); bc("ps_fa", "hs")
        a.emit(subs_reg, 1, 1, 0); a.emit(str_imm, 1, 7, 60)                                                # the gap's length
        imm32(0, BUF + PATCH_STRIDE); a.emit(movs_imm, 2, 0xFF); a.emit(bl, MEMSET)
        a.label("ps_ff"); rw_patch(WRITE, 28, 56, 0, "ps_fail", abs_buf=BUF + PATCH_STRIDE, len_slot=60)
        a.label("ps_fa")
        rw_patch(WRITE, 28, 44, 0, "ps_fail")
        a.emit(movs_imm, 0, 0); a.emit(str_imm, 0, 7, 48); a.emit(b, "ps_un")
    if EMPTY and not FFGAP:
        imm32(1, 511); a.emit(adds_reg, 0, 0, 1); a.emit(lsrs_imm, 0, 0, 9)                                 # n = the patches it holds
        a.emit(lsls_imm, 1, 6, 29); a.emit(lsrs_imm, 1, 1, 29); a.emit(cmp_reg, 0, 1); a.emit(b_cond, "ps_e1", "ls"); a.emit(mov_reg, 0, 1)   # i = min(n, B % 8)
        a.label("ps_e1"); a.emit(str_imm, 0, 7, 56)
        a.label("ps_el")
        a.emit(ldr_imm, 0, 7, 56); a.emit(lsls_imm, 0, 0, 9); a.emit(str_imm, 0, 7, 44)                    # the offset 512 i
        if INITGAP:                                                                                            # SC38.5: before B, the Initial Patch
            a.emit(ldr_imm, 0, 7, 56); a.emit(lsls_imm, 1, 6, 29); a.emit(lsrs_imm, 1, 1, 29); a.emit(cmp_reg, 0, 1); bc("ps_ia", "hs")
            a.label("ps_ig"); rw_patch(WRITE, 28, 44, 0, "ps_fail", abs_buf=INIT_PATCH); a.emit(b, "ps_in")
            a.label("ps_ia")
        rw_patch(WRITE, 28, 44, 0, "ps_fail")
        if INITGAP: a.label("ps_in")
        a.emit(ldr_imm, 0, 7, 56); a.emit(adds_imm8, 0, 1); a.emit(str_imm, 0, 7, 56)
        a.emit(lsls_imm, 1, 6, 29); a.emit(lsrs_imm, 1, 1, 29); a.emit(cmp_reg, 0, 1); bc("ps_el", "ls")
        a.emit(movs_imm, 0, 0); a.emit(str_imm, 0, 7, 48); a.emit(b, "ps_un")
    if EMPTY:
        a.label("ps_rb")
    rw_patch(READ, 28, 44, PATCH_STRIDE, "ps_fail")
    a.emit(ldr_imm, 0, 7, 12); imm32(1, PATCH_SZ); a.emit(cmp_reg, 0, 1); bc("ps_fail8", "ne")
    if COPYX:                                    # between packs: a copy, A's bank is left alone
        a.emit(ldr_imm, 0, 7, 52); a.emit(cmp_reg, 0, 5); a.emit(b_cond, "ps_cp", "ne")
    rw_patch(WRITE, 16, 40, PATCH_STRIDE, "ps_fail")                                         # A's bank <- B
    if COPYX: a.label("ps_cp")
    rw_patch(WRITE, 28, 44, 0, "ps_fail")                                                    # B's bank <- A
    a.emit(movs_imm, 0, 0); a.emit(str_imm, 0, 7, 48); a.emit(b, "ps_un")
    a.label("ps_fail8"); a.emit(movs_imm, 0, 8)
    a.label("ps_fail"); a.emit(str_imm, 0, 7, 48)
    a.label("ps_un"); a.emit(bl, BUF_UNLOCK)
    if FIX2:
        a.emit(ldr_imm, 0, 7, 52); a.emit(bl, "c_resel")
    else:
        a.emit(bl, "c_curpack"); a.emit(sub_sp_imm, 16)                                           # the current pack selected again in the storage task
        a.emit(raw, h(0x9002)); a.emit(movs_imm, 0, KIND_PATCH); a.emit(raw, h(0x9000)); a.emit(movs_imm, 0, 0); a.emit(raw, h(0x9001))
        a.emit(mov_reg, 0, 13); a.emit(bl, EXISTS); a.emit(add_sp_imm, 16)
    a.emit(ldr_imm, 0, 7, 48); a.emit(add_sp_imm, F); a.emit(pop_list, [4, 5, 6, 7], pc=True)

    if SRCGUARD:
        a.label("c_srcv")                        # -> r0 = 1 when the synth Preset view shows SC19.1's source view or a step-drummer view
        a.emit(push_list, [], lr=True)
        a.emit(bl, L["c_sdscr"]); a.emit(cmp_imm, 0, 0xFF); a.emit(b_cond, "sv_1", "ne")
        a.emit(bl, L["c_gst"]); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "sv_x", "eq")
        a.emit(ldrb_imm, 0, 0, S_PAINT); a.emit(lsrs_imm, 0, 0, 2); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 0, 1); a.emit(pop_list, [], pc=True)
        a.label("sv_1"); a.emit(movs_imm, 0, 1)
        a.label("sv_x"); a.emit(pop_list, [], pc=True)

    # ---- c_spp (synth Preset view slot 0: view, pad, vel): Duplicate held, the patch list (not the source / step-drummer views) -> copy / swap
    a.label("c_spp")
    a.emit(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1)
    held(6); a.emit(movs_imm, 0, 2); a.emit(tst_reg, 6, 0); bc("sp_fwd", "eq")
    a.emit(bl, L["c_sdscr"]); a.emit(cmp_imm, 0, 0xFF); bc("sp_fwd", "ne")
    if SRCGUARD: a.emit(bl, "c_srcv"); a.emit(cmp_imm, 0, 0); bc("sp_fwd", "ne")
    a.emit(ldr_imm, 0, 4, 0x20); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 0, 0, 0)
    a.emit(lsls_imm, 0, 0, 5); a.emit(adds_reg, 5, 0, 5); a.emit(cmp_imm, 5, 128); bc("sp_eat", "hs")    # r5 = the patch
    a.emit(bl, "c_pclip"); a.emit(mov_reg, 6, 0); a.emit(cmp_imm, 6, 0); bc("sp_has", "ne")
    a.emit(bl, "c_curpack"); a.emit(lsls_imm, 0, 0, 8); a.emit(orrs_reg, 0, 5); a.emit(movs_imm, 1, PCLIP_MAGIC); a.emit(lsls_imm, 1, 1, 16); a.emit(orrs_reg, 0, 1)
    a.emit(bl, "c_psetclip"); a.emit(b, "sp_eat")
    a.label("sp_has")
    a.emit(movs_imm, 0, 0); a.emit(bl, "c_psetclip")
    a.emit(bl, "c_curpack"); a.emit(lsrs_imm, 1, 6, 8); a.emit(movs_imm, 2, 0xFF); a.emit(ands_reg, 1, 2)          # r1 = its pack
    a.emit(lsls_imm, 6, 6, 24); a.emit(lsrs_imm, 6, 6, 24); a.emit(cmp_imm, 6, 128); bc("sp_eat", "hs")          # r6 = its patch
    a.emit(cmp_reg, 1, 0); a.emit(b_cond, "sp_go", "ne")
    a.emit(cmp_reg, 6, 5); bc("sp_eat", "eq")                                                                     # A again: cancel
    a.label("sp_go")
    a.emit(mov_reg, 0, 6); a.emit(mov_reg, 2, 5); a.emit(bl, "c_pswap"); a.emit(cmp_imm, 0, 0); bc("sp_eat", "ne")
    a.emit(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); a.emit(b_w, prev["sp_pad"])               # done: B chosen again (loads the new patch)
    a.label("sp_eat")
    a.emit(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); a.emit(raw, h(0x4770))
    a.label("sp_fwd")
    a.emit(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); a.emit(b_w, prev["sp_pad"])

    # ---- c_spl (synth Preset view slot 7): the LEDs; with Duplicate held, the copied patch blinks (blue: this pack, yellow: another one)
    a.label("c_spl")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(bl, prev["sp_leds"]); a.emit(mov_reg, 5, 0)
    if PMODE: a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(bl, "c_pmode")
    held(0); a.emit(movs_imm, 1, 2); a.emit(tst_reg, 0, 1); bc("sl_x", "eq")
    a.emit(bl, L["c_sdscr"]); a.emit(cmp_imm, 0, 0xFF); bc("sl_x", "ne")
    if SRCGUARD: a.emit(bl, "c_srcv"); a.emit(cmp_imm, 0, 0); bc("sl_x", "ne")
    a.emit(bl, "c_pclip"); a.emit(mov_reg, 6, 0); a.emit(cmp_imm, 6, 0); bc("sl_x", "eq")
    a.emit(ldr_imm, 0, 4, 0x20); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 0, 0, 0)
    a.emit(lsls_imm, 7, 6, 24); a.emit(lsrs_imm, 7, 7, 24); a.emit(lsrs_imm, 1, 7, 5); a.emit(cmp_reg, 1, 0); bc("sl_x", "ne")   # its page
    a.emit(bl, "c_curpack"); a.emit(lsrs_imm, 6, 6, 8); a.emit(movs_imm, 1, 0xFF); a.emit(ands_reg, 6, 1)
    a.emit(movs_imm, 1, BLUE); a.emit(cmp_reg, 6, 0); a.emit(b_cond, "sl_c", "eq"); a.emit(movs_imm, 1, YELLOW)
    a.label("sl_c"); a.emit(mov_reg, 6, 1)
    imm32(0, HAL_TICK); a.emit(ldr_imm, 0, 0, 0); a.emit(lsrs_imm, 0, 0, 7); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 0, 1)
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "sl_d", "ne"); a.emit(movs_imm, 6, DARK)
    a.label("sl_d")
    a.emit(lsls_imm, 7, 7, 27); a.emit(lsrs_imm, 7, 7, 26); a.emit(strh_reg, 6, 5, 7)
    a.label("sl_x"); a.emit(mov_reg, 0, 5); a.emit(pop_list, [4, 5, 6, 7], pc=True)

    if PMODE:
        # ---- c_pmode (r0 = the synth Preset view, r1 = its LED buffer): the patch pads coloured by voice mode (see 19.)
        # frame r7: [0] cb [4] ctx [8] &done [12] done [16..27] item / colours [28] page [32] selected patch [36] pack [40] bank [44] size
        a.label("c_pmode")
        a.emit(push_list, [4, 5, 6, 7], lr=True); a.emit(sub_sp_imm, 48); a.emit(mov_reg, 7, 13)
        a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1)
        a.emit(bl, "c_srcv"); a.emit(cmp_imm, 0, 0); bc("pm_x", "ne")                                   # the source / step-drummer views
        a.emit(ldr_imm, 0, 4, 0x28); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 0, 0, 0)
        a.emit(movs_imm, 1, 2); a.emit(tst_reg, 0, 1); bc("pm_x", "eq")                                                   # the view not shown (the stock clears it)
        a.emit(bl, L["c_gst"]); a.emit(cmp_imm, 0, 0); bc("pm_x", "eq")
        a.emit(adds_imm8, 0, PM_CACHE); a.emit(mov_reg, 6, 0)                                          # r6 = the cache
        a.emit(ldr_imm, 0, 4, 0x20); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 0, 0, 0)
        a.emit(movs_imm, 1, 3); a.emit(ands_reg, 0, 1); a.emit(str_imm, 0, 7, 28)                      # the page
        a.emit(ldr_imm, 0, 4, 0x14); a.emit(movs_imm, 1, 10); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 0, 0, 0); a.emit(str_imm, 0, 7, 32)   # the patch
        a.emit(bl, "c_curpack"); a.emit(str_imm, 0, 7, 36)
        from thumb import ldrh_imm
        a.emit(ldrh_imm, 0, 6, 0); a.emit(movw, 1, PM_MAGIC); a.emit(cmp_reg, 0, 1); bc("pm_ref", "ne")
        a.emit(ldrb_imm, 0, 6, 2); a.emit(ldr_imm, 1, 7, 36); a.emit(cmp_reg, 0, 1); bc("pm_ref", "ne")
        a.emit(ldrb_imm, 0, 6, 3); a.emit(ldr_imm, 1, 7, 28); a.emit(cmp_reg, 0, 1); bc("pm_ref", "ne")
        a.emit(ldrb_imm, 0, 6, 14); a.emit(ldr_imm, 1, 7, 32); a.emit(cmp_reg, 0, 1); bc("pm_ref", "ne")
        imm32(0, HAL_TICK); a.emit(ldr_imm, 0, 0, 0); a.emit(lsrs_imm, 0, 0, 8); a.emit(ldrh_imm, 1, 6, 12)
        a.emit(subs_reg, 0, 0, 1); a.emit(lsls_imm, 0, 0, 16); a.emit(lsrs_imm, 0, 0, 16); a.emit(cmp_imm, 0, PM_LIFE); bc("pm_paint", "lo")
        if PLAYHOLD:                                                                                   # older, but playing: kept (no card access)
            imm32(0, TRANSPORT); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 0, 0, 0); a.emit(cmp_imm, 0, 0); bc("pm_paint", "ne")
        # -- read the page's four banks again: size, then the bank (<= 4 KB) into the shared buffer; byte PM_VOICE of each record
        a.label("pm_ref")
        a.emit(movs_imm, 0, 0); a.emit(str_imm, 0, 6, 4); a.emit(str_imm, 0, 6, 8)                   # the modes: unknown (stock colours)
        a.emit(movs_imm, 0, 5); a.emit(bl, BUF_LOCK)
        a.emit(movs_imm, 0, 0); a.emit(str_imm, 0, 7, 40)
        a.label("pm_bl")
        a.emit(movs_imm, 0, KIND_PATCH); a.emit(str_imm, 0, 7, 16)
        a.emit(ldr_imm, 0, 7, 28); a.emit(lsls_imm, 0, 0, 2); a.emit(ldr_imm, 1, 7, 40); a.emit(adds_reg, 0, 0, 1); a.emit(str_imm, 0, 7, 20)
        a.emit(ldr_imm, 0, 7, 36); a.emit(str_imm, 0, 7, 24)                                          # u8 pack (the loaded one, by its number)
        a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, 16); a.emit(bl, SIZE); a.emit(str_imm, 0, 7, 44)
        a.emit(cmp_imm, 0, 0); bc("pm_nb", "eq")
        a.emit(movs_imm, 1, 1); a.emit(lsls_imm, 1, 1, 12); a.emit(cmp_reg, 0, 1); a.emit(b_cond, "pm_c", "ls"); a.emit(str_imm, 1, 7, 44)
        a.label("pm_c")
        a.emit(movs_imm, 0, 0); a.emit(str_imm, 0, 7, 0); a.emit(str_imm, 0, 7, 4); a.emit(str_imm, 0, 7, 12)
        a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, 12); a.emit(str_imm, 0, 7, 8)
        a.emit(mov_reg, 0, 7); a.emit(adds_imm8, 0, 16); a.emit(movs_imm, 1, 0); imm32(2, BUF); a.emit(ldr_imm, 3, 7, 44); a.emit(bl, READ)
        a.emit(movs_imm, 1, 0); a.emit(str_imm, 1, 7, 8)
        a.emit(cmp_imm, 0, 0); bc("pm_nb", "ne")
        a.emit(movs_imm, 3, 0)                                                                         # r3 = the record k
        a.label("pm_kl")
        a.emit(lsls_imm, 0, 3, 9); a.emit(adds_imm8, 0, PM_VOICE); a.emit(ldr_imm, 1, 7, 12); a.emit(cmp_reg, 0, 1); bc("pm_nb", "hs")
        imm32(1, BUF); a.emit(raw, h(0x5C08))                                                          # ldrb r0,[r1,r0]
        a.emit(movs_imm, 2, 1); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "pm_set", "eq")
        a.emit(movs_imm, 2, 2); a.emit(cmp_imm, 0, 1); a.emit(b_cond, "pm_kn", "ne")
        a.label("pm_set")                                                                              # mode r2 (1 mono, 2 glide) of pad 8 b + k
        a.emit(ldr_imm, 0, 7, 40); a.emit(lsls_imm, 0, 0, 3); a.emit(adds_reg, 0, 0, 3)
        a.emit(lsrs_imm, 1, 0, 2); a.emit(adds_reg, 1, 1, 6)
        a.emit(lsls_imm, 0, 0, 30); a.emit(lsrs_imm, 0, 0, 29); a.emit(raw, h(0x4082))                # lsls r2,r0  (2 x (pad & 3))
        a.emit(ldrb_imm, 0, 1, 4); a.emit(orrs_reg, 0, 2); a.emit(strb_imm, 0, 1, 4)
        a.label("pm_kn")
        a.emit(adds_imm8, 3, 1); a.emit(cmp_imm, 3, 8); a.emit(b_cond, "pm_kl", "lo")
        a.label("pm_nb")
        a.emit(ldr_imm, 0, 7, 40); a.emit(adds_imm8, 0, 1); a.emit(str_imm, 0, 7, 40); a.emit(cmp_imm, 0, 4); bc("pm_bl", "lo")
        a.emit(bl, BUF_UNLOCK)
        a.emit(movw, 0, PM_MAGIC); a.emit(strh_imm, 0, 6, 0)
        a.emit(ldr_imm, 0, 7, 36); a.emit(strb_imm, 0, 6, 2); a.emit(ldr_imm, 0, 7, 28); a.emit(strb_imm, 0, 6, 3)
        a.emit(ldr_imm, 0, 7, 32); a.emit(strb_imm, 0, 6, 14)
        imm32(0, HAL_TICK); a.emit(ldr_imm, 0, 0, 0); a.emit(lsrs_imm, 0, 0, 8); a.emit(strh_imm, 0, 6, 12)
        # -- paint: [16] the stock's bright (selected) colour, [20] its dim colour, [24] the selected pad (or 32)
        a.label("pm_paint")
        a.emit(ldrh_imm, 0, 4, 0x26); a.emit(lsls_imm, 0, 0, 1); imm32(1, TRACK_COLS)
        a.emit(ldrh_reg, 2, 1, 0); a.emit(str_imm, 2, 7, 16); a.emit(adds_imm8, 0, 2); a.emit(ldrh_reg, 2, 1, 0); a.emit(str_imm, 2, 7, 20)
        a.emit(ldr_imm, 0, 7, 32); a.emit(lsrs_imm, 1, 0, 5); a.emit(ldr_imm, 2, 7, 28); a.emit(movs_imm, 3, 31); a.emit(ands_reg, 0, 3)
        a.emit(cmp_reg, 1, 2); a.emit(b_cond, "pm_sp", "eq"); a.emit(movs_imm, 0, 32)
        a.label("pm_sp"); a.emit(str_imm, 0, 7, 24)
        a.emit(movs_imm, 3, 0)                                                                         # r3 = the pad
        a.label("pm_pl")
        a.emit(lsrs_imm, 0, 3, 2); a.emit(adds_reg, 0, 0, 6); a.emit(ldrb_imm, 0, 0, 4)
        a.emit(lsls_imm, 1, 3, 30); a.emit(lsrs_imm, 1, 1, 29); a.emit(raw, h(0x40C8))                # lsrs r0,r1
        a.emit(movs_imm, 1, 3); a.emit(ands_reg, 0, 1)                                                 # r0 = its mode
        a.emit(lsls_imm, 1, 3, 1); a.emit(ldrh_reg, 2, 5, 1)                                           # r2 = its colour now
        for c in PM_MONO + PM_GLIDE: a.emit(cmp_imm, 2, c); a.emit(b_cond, "pm_ours", "eq")
        a.emit(cmp_imm, 0, 0); a.emit(b_cond, "pm_pn", "eq")                                           # poly / unknown: a stock colour stays
        a.emit(ldr_imm, 1, 7, 16); a.emit(cmp_reg, 2, 1); a.emit(b_cond, "pm_ours", "eq")
        a.emit(ldr_imm, 1, 7, 20); a.emit(cmp_reg, 2, 1); a.emit(b_cond, "pm_pn", "ne")                # another stock drawing: left alone
        a.label("pm_ours")                                                                             # r0 = mode, pad r3
        a.emit(ldr_imm, 1, 7, 24); a.emit(cmp_reg, 1, 3); a.emit(b_cond, "pm_hi", "eq")
        a.emit(ldr_imm, 2, 7, 20); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "pm_w", "eq")
        a.emit(movs_imm, 2, PM_MONO[0]); a.emit(cmp_imm, 0, 1); a.emit(b_cond, "pm_w", "eq"); a.emit(movs_imm, 2, PM_GLIDE[0]); a.emit(b, "pm_w")
        a.label("pm_hi")
        a.emit(ldr_imm, 2, 7, 16); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "pm_w", "eq")
        a.emit(movs_imm, 2, PM_MONO[1]); a.emit(cmp_imm, 0, 1); a.emit(b_cond, "pm_w", "eq"); a.emit(movs_imm, 2, PM_GLIDE[1])
        a.label("pm_w"); a.emit(lsls_imm, 1, 3, 1); a.emit(strh_reg, 2, 5, 1)
        a.label("pm_pn")
        a.emit(adds_imm8, 3, 1); a.emit(cmp_imm, 3, 32); bc("pm_pl", "lo")
        a.label("pm_x"); a.emit(add_sp_imm, 48); a.emit(pop_list, [4, 5, 6, 7], pc=True)


def install(img, report, base_addr):
    """Append the code; the save call -> c_svs (then persist19's c_pl_save); drum Preset view slots 0 / 7 -> c_pdp / c_pdl (in front of drumrep);
    packs view slots 0 / 7 -> c_ppk / c_ppl; held-buttons object slots 2 / 8 -> c_mbp / c_mbl."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    p19 = {k: int(v, 16) for k, v in report["persist19"]["labels"].items()}
    L = dict(c_pl_save=p19["c_pl_save"], c_shift=int(report["sc15"]["labels"]["c_shift"], 16))
    if PATCHX: L["c_sdscr"] = int(report["vcf20"]["labels"]["c_sdscr"], 16)
    if PKLED: L["c_vledtask"] = int(report["vcf20"]["labels"]["c_vledtask"], 16)
    if SRCGUARD: L["c_gst"] = int(report["sc14"]["labels"]["c_gst"], 16)
    assert bytes(img[SAVE_CALL - BASE:SAVE_CALL - BASE + 4]) == bl(SAVE_CALL, L["c_pl_save"])
    u = lambda ad: struct.unpack_from("<I", img, ad - BASE)[0]
    prev = dict(dp_pad=u(DP_VT) & ~1, dp_leds=u(DP_VT + 28) & ~1)
    if PATCHX: prev.update(sp_pad=u(SP_VT) & ~1, sp_leds=u(SP_VT + 28) & ~1)
    assert u(PV_VT) == PV_PAD and u(PV_VT + 28) == 0x08047593 and u(MB_VT + 8) == MB_PRESS and u(MB_VT + 32) == MB_LEDS
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    img[SAVE_CALL - BASE:SAVE_CALL - BASE + 4] = bl(SAVE_CALL, labels["c_svs"])
    struct.pack_into("<I", img, DP_VT - BASE, labels["c_pdp"] | 1)
    struct.pack_into("<I", img, DP_VT + 28 - BASE, labels["c_pdl"] | 1)
    struct.pack_into("<I", img, PV_VT - BASE, labels["c_ppk"] | 1)
    struct.pack_into("<I", img, PV_VT + 28 - BASE, labels["c_ppl"] | 1)
    struct.pack_into("<I", img, MB_VT + 8 - BASE, labels["c_mbp"] | 1)
    struct.pack_into("<I", img, MB_VT + 32 - BASE, labels["c_mbl"] | 1)
    if PKLED:
        for c in LED_CALLS:
            assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, L["c_vledtask"]), hex(c)
            img[c - BASE:c - BASE + 4] = bl(c, labels["c_pkled"])
    if DUPMASK:
        assert u(CT_VT + 0x20) == CT_MASK
        struct.pack_into("<I", img, CT_VT + 0x20 - BASE, labels["c_hmask"] | 1)
    if PATCHX:
        struct.pack_into("<I", img, SP_VT - BASE, labels["c_spp"] | 1)
        struct.pack_into("<I", img, SP_VT + 28 - BASE, labels["c_spl"] | 1)
    return labels, code, prev
