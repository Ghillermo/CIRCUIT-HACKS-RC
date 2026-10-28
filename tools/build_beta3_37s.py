"""Circuit Tracks 4486 - Beta 3.37S (marker "B3.37S") = Beta 3.37 + rodisk.use_allpacks(): the safer build of the beta (the user, 2026-10-27:
«Does the last published Beta have an S version? If not, make it»; like Beta 3.36S, an exception to the 2026-10-18 rule of no S builds for
betas): every write and delete the mod starts is refused on every pack (the red Save LED), the stock's own saves pass; nothing of the mod writes
files to the SD card or to the internal memory.  The features that write (captured sample saved with the project, exchanges and copies between
packs, own-synth patches, synth patch save, copy of projects, deleting a pack) fail."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import rodisk  # noqa: E402
rodisk.use_allpacks()
import build_sc48 as B  # noqa: E402
import linein3  # noqa: E402

NAME = "B3.37S"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
