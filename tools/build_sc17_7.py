"""Circuit Tracks 4486 — SC17.7 = SC17.6 + song pointer (Master FX view) + louder delay / reverb sources + mode view on Shift + Scales.

  * Pads 9-24 of the Master FX view (rows 2 and 3) = the 16 steps; the playhead follows the sequencer position (the general beat).
    Hold a step: when the playhead reaches the end (default step 16) the song resumes at that step instead of step 1.  Hold two
    steps: the first is the start, the second the end.  Shift + step: that step becomes the start (same step again: off; Shift +
    another step: moves it); while a start is set, touching another step (no Shift) places the end there.
  * Synth source modes 5 / 6 (delay / reverb returns): the captured signal is now x16 of the average (was x2: the returns live in
    the mixer's -24 dB domain, so they were inaudible).  linein3.FX_GAIN_SHIFT = 3.
  * The synth source mode pads move from "Shift in the synth Preset view" to the Shift + Scales view (modeview.py).
Everything up to SC17.6 is unchanged (tools/verify_builds.py).  See build_sc17.songptr_code and modeview.py.
"""
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ct_fw  # noqa: E402
import build_sc17_6 as b6  # noqa: E402  (use_slots, fxkeys.CLEAR_RESET, linein3.install ...)
import build_sc17 as s17  # noqa: E402
import build_sc15 as s15  # noqa: E402
import build_shared_channels as sc  # noqa: E402
import linein3  # noqa: E402
import modeview  # noqa: E402
from thumb import b_w  # noqa: E402

BASE = ct_fw.APP_BASE
NAME = "SC17.7"
s17.use_songptr()
linein3.FX_GAIN_SHIFT = 3


def build(stock: bytes, listing: Path):
    img6, report = b6.b5.build(stock, listing)
    img = bytearray(img6)
    def vt(addr, slot): return struct.unpack_from("<I", img, addr + 4 * slot - BASE)[0]
    assert vt(modeview.VIEW7_VT, 0) == modeview.VIEW7_PRESS | 1 and vt(modeview.VIEW7_VT, 7) == modeview.VIEW7_LEDS | 1
    c_spad = int(report["sc15"]["labels"]["c_spad"], 16); c_sleds = int(report["sc15"]["labels"]["c_sleds"], 16)
    assert vt(s15.SP_VT, 0) == c_spad | 1 and vt(s15.SP_VT, 7) == c_sleds | 1
    c_gst = int(report["sc14"]["labels"]["c_gst"], 16)
    ext = (len(img) + BASE + 3) & ~3
    code, labels = modeview.arm_code(ext, c_gst)
    img += bytes([0xFF]) * (ext - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    struct.pack_into("<I", img, modeview.VIEW7_VT - BASE, labels["c_mpad"] | 1)
    struct.pack_into("<I", img, modeview.VIEW7_VT + 28 - BASE, labels["c_mleds"] | 1)
    struct.pack_into("<I", img, s15.SP_VT - BASE, s15.SP_PRESS | 1)                  # synth Preset view: stock again
    struct.pack_into("<I", img, s15.SP_VT + 28 - BASE, s15.SP_LEDS | 1)
    report["modeview"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()}, listing=sc.disasm(bytes(code), ext),
                              pads=list(modeview.PADS), view=hex(modeview.VIEW7_VT))
    return bytes(img), report


if __name__ == "__main__":
    linein3.main(NAME, build, s15, sys.argv[1:])
