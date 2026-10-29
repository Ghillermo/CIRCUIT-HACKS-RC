"""Circuit Tracks 4486 - SC49.3 = SC49.2 with more of the mod's dead code left out (the user, 2026-10-29: «dead code pass»), for the drums' extra
lane's phase 2.  Found on SC49.2's image (nothing reaches them): SC15's c_spad / c_sleds (srcview took both slots), arp's sorted insert
(c_arins_old: PRESSORD), compkn (fxsess undid it), build_sc17's c_spengine / c_sppos / c_jmpled (SPCACHE, SP2), fxkeys' c_pgbtn / c_res (fxres put
id 21 back), mfbyp's c_mfset (HOLD), mutate39's c_mutbuf / c_mutled (stepmod took the slots).  Nothing changes in use."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc49_2 as B  # noqa: E402
import build_sc15  # noqa: E402
import arp  # noqa: E402
import compkn  # noqa: E402
import build_sc17  # noqa: E402
import fxkeys  # noqa: E402
import mfbyp  # noqa: E402
import mutate39  # noqa: E402
build_sc15.use_trim()                                # c_spad / c_sleds
arp.use_trimins()                                    # the sorted insert
compkn.use_trim()                                    # compkn
build_sc17.use_trimsp()                              # c_spengine / c_sppos / c_jmpled
fxkeys.use_trimpg()                                  # c_pgbtn / c_res
mfbyp.use_trimset()                                  # c_mfset
mutate39.use_trimsl()                                # c_mutbuf / c_mutled
import linein3  # noqa: E402

NAME = "SC49.3"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
