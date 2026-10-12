"""Circuit Tracks 4486 — SC19 = SC18.3 + the settings made with our patches are saved in the project (tools/persist19.py).

  * Drum controls (envelope, pitch envelope, ring mod, LFO + speed, env -> cutoff, filter mode, resonance, start point, bitcrush),
    the Master FX slot assignments and the synth source modes (noise / inputs / returns) go into the reserved bytes of the project:
    they are saved with the project, follow "save as copy" and come back when the project is loaded; a new project starts clean.
  * Loading a project, creating one and powering up switch every Master FX effect and the song pointer off.
  * Fixes found on the hardware: the master resonance step and its green LED were on the Record button (id 16 / LED 48); they move to
    the real "1-16 / 17-32" button (id 21 / LED 53) and Record / Play (ids 16 / 17) are stock again.  The chromatic drum view shows all
    four rows again.  The synth source modes are 0..4 (the delay / reverb return modes are dropped).
  * DSP: the drum mailbox takes absolute values (drums2_dsp.ABS); everything else is SC18.3.
Everything up to SC18.3 is unchanged (tools/verify_builds.py).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import drums2_dsp  # noqa: E402
drums2_dsp.ABS = True                # absolute mailbox values (must be set before the DSP code is generated)
import linein3  # noqa: E402
linein3.N_MODES = 5                  # synth source modes 0..4 only: the delay / reverb return modes are dropped (the Preset view pads 30 / 31 are stock again)
import fxkeys  # noqa: E402
fxkeys.PAGE_BTN = True               # the master resonance step on the real "1-16 / 17-32" button (id 21); 16 / 17 = Record / Play stay stock
import build_sc18_3 as b183  # noqa: E402  (applies the SC18.3 options)
import leds18  # noqa: E402
leds18.LED_PAIR = 53                 # ... and its LED (source 8, element 0) is the one that lights up, not Record's (48)
import persist19  # noqa: E402

NAME = "SC19"
b182 = b183.b182


def extra(img, report):
    b182.extra(img, report)
    st = (Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    def text(addr, n): return "|".join(b182.b18.sc.disasm(bytes(st[addr - b182.b18.BASE:addr - b182.b18.BASE + n]), addr))
    ext = (len(img) + b182.b18.BASE + 3) & ~3
    labels, code, info = persist19.install(img, report, ext, text)
    report["persist19"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()},
                               listing=b182.b18.sc.disasm(bytes(code), ext + len(persist19.table())), xmem=info["flat"],
                               flat=[(hex(c), o) for c, o in persist19.FLAT], sig=persist19.SIG, modes=persist19.N_MODES,
                               **({"fix_lock": True} if persist19.FIX_LOCK else {}), **({"rec_restore": True} if persist19.REC_RESTORE else {}), **({"blob_keep": True} if persist19.BLOB_KEEP else {}), **({"knob_levels": True} if persist19.KNOB_LEVELS else {}), **({"remap": True} if persist19.REMAP else {}), **({"extras": True} if persist19.EXTRAS else {}), **({"extras_slope": True} if persist19.EXTRAS_SLOPE else {}), **({"guard": [persist19.BOOT_A, persist19.BOOT_B]} if persist19.GUARD else {}), **({"save_mask": True} if persist19.SAVE_MASK else {}), **({"gfx_global": True} if persist19.GFX_GLOBAL else {}))


if __name__ == "__main__":
    linein3.main(NAME, b182.b18.b6.b5.build, b182.b18.b6.b5.s15, sys.argv[1:], extra=extra)
