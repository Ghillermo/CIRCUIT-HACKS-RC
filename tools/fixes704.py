"""The pending fixes of the 2026-11-14 bug hunt / 2026-11-15 review done on 2026-11-18 (the user: «Implement the other pending fixes»), as options:
  * alpha(): jumpseq.use_sig2 (a stronger check of the one-byte signature), patchain.use_lrram (nothing on the LED task's stack while the chain
    below runs), patchain.use_ccmap (a scene's chain mask only with its map bit); extra_alpha(): sclear2 (Clear + scene also resets the chain
    mode / repeats and pattern mutate's bytes) in a dspz gap;
  * rc(): patchain.use_lrram; extra_rc(): sclear2 appended at the image's end."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))


def alpha():
    import jumpseq, patchain
    jumpseq.use_sig2(); patchain.use_lrram(); patchain.use_ccmap()
    import dspz
    dspz.use_move("jsaflip", 1)          # (room: gap 1 is full, so with dspz.use_spill it goes to the image's end; patrev then fits in gap 0)


def rc():
    import patchain
    patchain.use_lrram()


def extra_alpha(img, report):
    import dspz, sclear2
    dspz.add(img, report, "sclear2", sclear2)


def extra_rc(img, report):
    import ct_fw, sclear2
    labels, code, prev = sclear2.install(img, report, (ct_fw.APP_BASE + len(img) + 3) & ~3)
    import build_shared_channels as sc
    report["sclear2"] = dict(arm_start=hex(int(labels["c_sc2"])), labels={k: hex(v) for k, v in labels.items()}, prev={k: hex(v) for k, v in prev.items()},
                             listing=sc.disasm(bytes(code), int(labels["c_sc2"])))
