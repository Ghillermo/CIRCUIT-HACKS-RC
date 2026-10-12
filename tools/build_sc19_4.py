"""Circuit Tracks 4486 — SC19.4 = SC19.3 + the saved settings are restored from the session record.

SC19.3 booted, but nothing that was saved came back (also when switching between projects).  The stock apply (0x0802EEFE) copies the project and drum
blobs whole into the live stores, but a synth blob only when the patch of the record differs from the patch that is loaded (the flag bytes at [sp] /
[sp + 1], set at 0x0802F172 / 0x0802F19E; with the same patch only 6 parameters are restored): 44 of the 65 reserved bytes live in the synth blobs, among
them the signature, so the whole zone was judged empty and cleared.  Verified on the real stock code in emulation (tools/emu_sc19_4.py): same patch id ->
0 of 22 bytes of each synth restored.  persist19.REC_RESTORE copies the 65 bytes from the session record ([0x2003D71C + 0x14] + REC_BASE[store] + offset,
the buffer the stock load filled from the file and the stock save fills before writing it) into the live stores before the signature is checked.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import persist19  # noqa: E402
persist19.FIX_LOCK = True            # the SC19.3 fix (before persist19.install builds the code)
persist19.REC_RESTORE = True
persist19.BLOB_KEEP = True           # the synth patch changes keep our bytes of the synth stores
import build_sc19_1 as b191  # noqa: E402
import linein3  # noqa: E402

NAME = "SC19.4"
b182 = b191.b182

if __name__ == "__main__":
    linein3.main(NAME, b182.b18.b6.b5.build, b182.b18.b6.b5.s15, sys.argv[1:], extra=b191.extra)
