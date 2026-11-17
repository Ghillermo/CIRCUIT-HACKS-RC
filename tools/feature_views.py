"""Where every feature lives in the manual by views (the user, 2026-11-15: «merge both manuals. Now, all the features belong in Manual per views,
with their pictures. New sections are per view. An hyper linked index lists all features inside each view chapter. An hyper linked glossary lists
features with the old sections»).

FEATURE_VIEW = {section id of the feature list (make_manual.S): the guide's view (make_guide.V) whose chapter holds it}.  Each chapter of the guide
(make_guide.write) shows, after its title block, an index of its features, then the view's own text, then its features as subsections (anchor
«f-<sid>»: view ids and section ids overlap, e.g. setup, guardado, instalar, step-drummer).  ALSO = {sid: other views where the feature is used}:
those chapters list it under «also here» (a link to its chapter).  The glossary (the end of the guide, and the old feature-list pages
index.html / en.html, MANUAL*.md, CARACTERISTICAS.md / FEATURES.md) lists every feature under the old groups A-E, linking to its subsection.

    python tools/feature_views.py       (checks: every feature mapped once to an existing view, ALSO views exist; prints the chapters)
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

FEATURE_VIEW = {
    # A. Accesos directos y usabilidad
    "atajos": "botones", "master-fx-acceso": "master-fx", "vista-fx": "vista-fx", "clear-knob": "botones", "pad8": "master-fx",
    "fuente-sinte": "synth-fuente", "cromatica": "drum-cromatica", "pack": "drum-preset", "sustituir": "drum-preset", "editor-cc": "midi-cc",
    "mixer-shift": "mixer", "mixer-cue": "mixer", "lfo-sync": "botones", "teclado-partido": "synth-nota", "colores-patch": "synth-preset",
    "morph": "synth-preset", "patches-midi": "midi-preset", "guardar-patch": "synth-preset", "destinos-macro": "synth-fuente",
    "copiar-proyectos": "projects", "patches-entre-packs": "midi-preset", "luces-disparo": "botones", "proyecto-init": "botones",
    # B. Controles expuestos
    "knobs-drums": "drum-pista", "rev-delay": "vista-fx", "sidechain-comp": "sidechain", "grabar-interno": "setup", "midi-io": "midi",
    "automatizacion": "midi-knobs", "setup": "setup",
    # C. Nuevos modos de control
    "patch-flip": "midi-preset", "motor-midi": "midi-preset", "step-drummer": "step-drummer", "fx-seq": "step-drummer",
    "song-pointer": "master-fx", "sample": "master-fx", "glitch-pad": "master-fx", "fila-inferior": "master-fx",
    "random-mutate": "probabilidad", "frecuencia-dinamicas": "probabilidad", "cadenas": "patterns", "mutate-patrones": "patterns",
    "nudge-ordenes": "pattern-settings", "arpegiador": "pattern-settings", "rollers": "drum-cromatica", "escala-propia": "escalas",
    "acordes": "synth-nota", "pareja-estereo": "drum-pista", "carril-extra": "drum-pista", "modo-muestra": "midi-muestra",
    "matriz-mod": "midi-matriz", "saltos": "midi-preset", "fm4": "midi-fm", "fm8": "midi-fm8", "wavetable": "midi-preset",
    "master-fx-beta": "master-fx",
    # D. DSP
    "efectos-master-fx": "master-fx", "vca-vcf": "midi-knobs", "osciladores": "midi-knobs", "va-drum": "midi-knobs",
    "granular": "midi-knobs", "glitch-dsp": "master-fx", "drums-dsp": "drum-pista", "entradas": "synth-fuente",
    # E. Miscelánea
    "guardado": "guardado", "pack-interno": "packs", "instalar": "instalar", "herramientas": "instalar", "tablas-midi": "midi",
}

ALSO = {
    "atajos": ["convenciones"], "master-fx-acceso": ["mixer", "botones"], "vista-fx": ["master-fx"],
    "clear-knob": ["drum-pista", "midi-knobs", "master-fx"], "fuente-sinte": ["synth-nota"],
    "cromatica": ["drum-preset", "drum-pista", "escalas"], "pack": ["synth-preset", "packs", "guardado"], "sustituir": ["master-fx"],
    "editor-cc": ["midi-preset"], "mixer-cue": ["botones"], "lfo-sync": ["midi-knobs", "midi-matriz", "drum-pista", "master-fx"],
    "teclado-partido": ["botones"], "morph": ["midi-preset", "midi-knobs"], "patches-midi": ["guardado"], "destinos-macro": ["destinos"],
    "patches-entre-packs": ["packs"], "proyecto-init": ["synth-preset", "midi-preset"], "knobs-drums": ["botones", "midi"],
    "sidechain-comp": ["advanced-setup"], "grabar-interno": ["midi"], "midi-io": ["midi-knobs", "drum-pista", "master-fx"],
    "automatizacion": ["synth-nota", "datos-patron"], "setup": ["advanced-setup", "midi"], "patch-flip": ["setup", "midi"],
    "motor-midi": ["midi-knobs"], "step-drummer": ["synth-fuente", "midi-preset"], "fx-seq": ["midi-preset", "master-fx"],
    "sample": ["vista-fx", "drum-preset"], "fila-inferior": ["vista-fx"], "random-mutate": ["pattern-settings"],
    "frecuencia-dinamicas": ["pattern-settings"], "cadenas": ["mixer"], "mutate-patrones": ["mixer"],
    "arpegiador": ["synth-nota", "setup", "drum-preset"], "rollers": ["drum-pista", "datos-patron"], "escala-propia": ["synth-nota"],
    "acordes": ["midi-preset"], "carril-extra": ["drum-cromatica", "datos-patron", "guardado"], "modo-muestra": ["midi-preset"],
    "matriz-mod": ["destinos"], "saltos": ["probabilidad"], "fm4": ["midi-preset"], "fm8": ["midi-preset"], "wavetable": ["midi-knobs"],
    "master-fx-beta": ["guardado"], "vca-vcf": ["midi-preset"], "osciladores": ["midi-voces"], "va-drum": ["midi-preset"],
    "granular": ["midi-preset"], "drums-dsp": ["sidechain"], "entradas": ["setup", "vista-fx", "midi-preset"],
    "guardado": ["datos-patron", "datos-perdido"], "pack-interno": ["guardado"], "herramientas": ["app-sd"], "tablas-midi": ["destinos"],
}


def check():
    """-> problems: a feature of make_manual not mapped (or mapped and not a feature), a view that is not a view of the guide"""
    import make_manual as M
    import make_guide as G
    sids = [s_["id"] for s_ in M.S]
    views = {v["id"] for v in G.V}
    bad = [f"{s}: not mapped" for s in sids if s not in FEATURE_VIEW]
    bad += [f"{s}: mapped but not a feature" for s in FEATURE_VIEW if s not in sids]
    bad += [f"{s}: view {v} is not in the guide" for s, v in FEATURE_VIEW.items() if v not in views]
    bad += [f"{s}: also-view {v} is not in the guide" for s, vs in ALSO.items() for v in vs if v not in views]
    bad += [f"{s}: also-entry for an unknown feature" for s in ALSO if s not in FEATURE_VIEW]
    bad += [f"{s}: also-view {v} is its own view" for s, vs in ALSO.items() for v in vs if v == FEATURE_VIEW.get(s)]
    return bad


def by_view():
    """view id -> its features (section ids), in the feature list's order"""
    import make_manual as M
    out = {}
    for s_ in M.S: out.setdefault(FEATURE_VIEW[s_["id"]], []).append(s_["id"])
    return out


def also_in(vid):
    """the features of other chapters that are used in the view vid too, in the feature list's order"""
    import make_manual as M
    return [s_["id"] for s_ in M.S if vid in ALSO.get(s_["id"], ())]


_probs = check()
assert not _probs, _probs


if __name__ == "__main__":
    import make_guide as G
    bv = by_view()
    for v in G.V: print(f'{v["id"]:16} {", ".join(bv.get(v["id"], [])) or "-"}')
    print(len(FEATURE_VIEW), "features in", len(bv), "chapters")
