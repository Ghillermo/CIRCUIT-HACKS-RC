"""The patch editor of the own synth of MIDI 1 / 2 (the user, 2026-11-10: «Crea un editor de patches con interfaz gráfica y sliders agrupados por
secciones que pueda enviar los parámetros en tiempo real a los sintes custom para probarlos»).

    python tools/make_patch_editor.py          tools/patch_editor_src.html -> tools/patch_editor.html

One page (Chrome / Edge, Web MIDI): 33 sliders in six sections (amplifier, filter, LFO, effect, oscillator 1, oscillator 2), each sent as the
engine's own CC / NRPN on the track's channel while it moves (vcf21.CC_TAB: what the device reads through c_vin when CC Rx is on and the engine
is on; bipolar values go out + 64, as c_vfromu takes them back).  The device's knobs (CC Tx) move the sliders.  A test keyboard (notes on the
same channel), .ctm open / save (tools/patchtool.py's padding layout; whatever the page does not edit is kept from the opened file) and the
example patches of docs/patches (tools/make_examples.py) built in.  The engine, the LFO shape and page 4 / 8's destinations have no MIDI: they
only go into the saved file.  Run again whenever CC_TAB, the defaults or the examples change.
"""
from __future__ import annotations
import base64, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import vcf21  # noqa: E402
import make_examples as MX  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "tools" / "patch_editor_src.html", ROOT / "tools" / "patch_editor.html"


def data():
    params, by_cc, by_nrpn = {}, {}, {}
    for code in range(1, 35):
        t, n = vcf21.CC_TAB[code]
        if t == 0xFF:
            continue                                                    # code 14 (the second note): no knob, no message
        bip = code in MX.BIPOLAR
        lo, hi = (-64, 63) if bip else (0, 100 if code in MX.HI100 else 127)
        params[code] = dict(name=MX.NAMES_ES[code], min=lo, max=hi, def_=MX.DEFAULTS[code - 1], kind="bip" if bip else "uni", msg=[t, n])
        if t == 0:
            by_cc[n] = code
        else:
            by_nrpn[((t & 0x7F) << 7) | n] = code
    for p in params.values():
        p["def"] = p.pop("def_")
        assert p["min"] <= p["def"] <= p["max"], p
    ex = []
    for f in sorted((ROOT / "docs" / "patches").glob("*.ctm")):
        b = f.read_bytes()
        assert b[:4] == b"CTM1", f
        nm = b[44:60].decode("ascii", "replace").rstrip() if b[44] != 0xFF else f.stem.split("_", 1)[-1].replace("_", " ")
        ex.append(dict(name=f.stem[:2] + " " + nm, b64=base64.b64encode(b).decode()))
    return dict(params=params, byCc=by_cc, byNrpn=by_nrpn, examples=ex)


def main():
    src = SRC.read_text(encoding="utf-8")
    assert src.count("/*DATA*/null") == 1
    d = data()
    OUT.write_text(src.replace("/*DATA*/null", json.dumps(d, separators=(",", ":"))), encoding="utf-8", newline="\n")
    print(f"{OUT.relative_to(ROOT)}: {len(d['params'])} parameters, {len(d['examples'])} example patches, {OUT.stat().st_size} B")


if __name__ == "__main__":
    main()
